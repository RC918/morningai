"""
Docs Digest Strategy (Layer 2 Value Gate) for Publisher Node

Blueprint Alignment:
- Flow Controller v3: Aggregates blocked changes for batch processing
- Safety Governor v2: Prevents garbage PR flooding while preserving changes
- Memory v2 (Layer 1): Uses Redis for short-term accumulation

Purpose:
When Value Gate blocks low-significance changes (e.g., DOCS with score < 30),
instead of discarding them, this module accumulates them and periodically
creates a single aggregated PR containing all blocked changes.

Trigger Conditions:
1. Count-based: When accumulated changes reach DOCS_DIGEST_COUNT_THRESHOLD
2. Time-based: When current time passes DOCS_DIGEST_FLUSH_HOUR_UTC (opportunistic)

Feature Flags:
- DOCS_DIGEST_ENABLED: Master switch (default: False)
- DOCS_DIGEST_COUNT_THRESHOLD: Items needed to trigger flush (default: 5)
- DOCS_DIGEST_FLUSH_HOUR_UTC: Hour (0-23) for daily flush (default: 0 = midnight)
- DOCS_DIGEST_LOCK_TTL_SECONDS: Lock TTL for flush operation (default: 600)
- DOCS_DIGEST_MAX_ITEMS: Maximum items to accumulate (default: 50)

Issue: #3087 - Implement Docs Digest Strategy
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Redis key prefixes
REDIS_KEY_PREFIX = "orchestrator:docs_digest"

# Default configuration values
DEFAULT_COUNT_THRESHOLD = 5
DEFAULT_FLUSH_HOUR_UTC = 0  # Midnight UTC
DEFAULT_LOCK_TTL_SECONDS = 600  # 10 minutes
DEFAULT_MAX_ITEMS = 50
DEFAULT_ITEM_TTL_SECONDS = 86400 * 7  # 7 days


@dataclass
class BlockedDocChange:
    """Record of a blocked documentation change for digest accumulation.
    
    Attributes:
        trace_id: Unique identifier for tracing this change
        repo: Repository in owner/repo format
        doc_file_path: Target file path for the documentation
        content: The documentation content to be committed
        goal: Task description/goal for this change
        score: Value Gate significance score
        downgrade_reason: Reason why this change was blocked
        created_at: Unix timestamp in seconds (float, from time.time())
        changeset_hash: Hash for deduplication
        branch: Optional branch name (empty if not yet created)
    """
    trace_id: str
    repo: str
    doc_file_path: str
    content: str
    goal: str
    score: int
    downgrade_reason: str
    created_at: float  # Unix epoch seconds (from time.time())
    changeset_hash: str
    branch: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "repo": self.repo,
            "doc_file_path": self.doc_file_path,
            "content": self.content,
            "goal": self.goal,
            "score": self.score,
            "downgrade_reason": self.downgrade_reason,
            "created_at": self.created_at,
            "changeset_hash": self.changeset_hash,
            "branch": self.branch,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockedDocChange":
        return cls(
            trace_id=data.get("trace_id", ""),
            repo=data.get("repo", ""),
            doc_file_path=data.get("doc_file_path", ""),
            content=data.get("content", ""),
            goal=data.get("goal", ""),
            score=data.get("score", 0),
            downgrade_reason=data.get("downgrade_reason", ""),
            created_at=data.get("created_at", 0),
            changeset_hash=data.get("changeset_hash", ""),
            branch=data.get("branch", ""),
        )


def _get_redis_client(redis_url: Optional[str] = None):
    """
    Get Redis client for digest storage.

    Args:
        redis_url: Optional Redis URL override

    Returns:
        Redis client instance or None if unavailable
    """
    try:
        import redis

        try:
            from common.config.settings import settings
            url = redis_url or getattr(settings, 'redis_url', None)
        except ImportError:
            url = redis_url

        if url:
            return redis.Redis.from_url(url, decode_responses=True)
        else:
            logger.warning("[DocsDigest] No Redis URL configured")
            return None
    except Exception as e:
        logger.warning(f"[DocsDigest] Failed to connect to Redis: {e}")
        return None


def _get_key(key_type: str, repo: str) -> str:
    """
    Get Redis key with proper prefix.

    Args:
        key_type: Type of key (pending, processing, lock, last_flush, seen)
        repo: Repository in owner/repo format

    Returns:
        Full Redis key
    """
    try:
        from common.config.settings import settings
        prefix = getattr(settings, 'redis_key_prefix', '') or ''
        prefix = prefix.rstrip(':')
    except ImportError:
        prefix = ''

    base_key = f"{REDIS_KEY_PREFIX}:{key_type}:{repo}"
    return f"{prefix}:{base_key}" if prefix else base_key


def _get_settings():
    """Get Docs Digest settings with defaults."""
    try:
        from common.config.settings import settings
        return {
            "enabled": getattr(settings, 'docs_digest_enabled', False),
            "count_threshold": getattr(settings, 'docs_digest_count_threshold', DEFAULT_COUNT_THRESHOLD) or DEFAULT_COUNT_THRESHOLD,
            "flush_hour_utc": getattr(settings, 'docs_digest_flush_hour_utc', DEFAULT_FLUSH_HOUR_UTC),
            "lock_ttl": getattr(settings, 'docs_digest_lock_ttl_seconds', DEFAULT_LOCK_TTL_SECONDS) or DEFAULT_LOCK_TTL_SECONDS,
            "max_items": getattr(settings, 'docs_digest_max_items', DEFAULT_MAX_ITEMS) or DEFAULT_MAX_ITEMS,
        }
    except ImportError:
        return {
            "enabled": False,
            "count_threshold": DEFAULT_COUNT_THRESHOLD,
            "flush_hour_utc": DEFAULT_FLUSH_HOUR_UTC,
            "lock_ttl": DEFAULT_LOCK_TTL_SECONDS,
            "max_items": DEFAULT_MAX_ITEMS,
        }


def record_blocked_doc_change(
    change: BlockedDocChange,
    redis_url: Optional[str] = None
) -> bool:
    """
    Record a blocked documentation change for future digest.

    This function is called when Value Gate blocks a low-significance change.
    Instead of discarding the change, we store it for later aggregation.

    Args:
        change: The blocked change to record
        redis_url: Optional Redis URL override

    Returns:
        True if recorded successfully, False otherwise
    """
    config = _get_settings()

    if not config["enabled"]:
        logger.debug("[DocsDigest] Feature disabled, skipping record")
        return False

    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        # Check for duplicate using changeset_hash
        seen_key = _get_key("seen", change.repo)
        if r.sismember(seen_key, change.changeset_hash):
            logger.info(
                "[DocsDigest] Duplicate change detected, skipping",
                extra={
                    "operation": "docs_digest_duplicate",
                    "trace_id": change.trace_id,
                    "changeset_hash": change.changeset_hash,
                }
            )
            return False

        # Check max items limit
        pending_key = _get_key("pending", change.repo)
        current_count = r.llen(pending_key)
        if current_count >= config["max_items"]:
            logger.warning(
                "[DocsDigest] Max items reached, skipping",
                extra={
                    "operation": "docs_digest_max_reached",
                    "trace_id": change.trace_id,
                    "current_count": current_count,
                    "max_items": config["max_items"],
                }
            )
            return False

        # Add to pending list
        r.lpush(pending_key, json.dumps(change.to_dict()))
        r.expire(pending_key, DEFAULT_ITEM_TTL_SECONDS)

        # Mark as seen
        r.sadd(seen_key, change.changeset_hash)
        r.expire(seen_key, DEFAULT_ITEM_TTL_SECONDS)

        logger.info(
            "[DocsDigest] Recorded blocked change",
            extra={
                "operation": "docs_digest_recorded",
                "trace_id": change.trace_id,
                "repo": change.repo,
                "doc_file_path": change.doc_file_path,
                "score": change.score,
                "pending_count": current_count + 1,
            }
        )

        return True

    except Exception as e:
        logger.warning(
            f"[DocsDigest] Failed to record blocked change: {e}",
            extra={
                "operation": "docs_digest_record_error",
                "trace_id": change.trace_id,
                "error": str(e),
            }
        )
        return False


def _should_flush(repo: str, redis_url: Optional[str] = None) -> tuple:
    """
    Check if digest should be flushed.

    Trigger conditions:
    1. Count-based: pending items >= threshold
    2. Time-based: current hour >= flush_hour_utc AND not flushed today

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        Tuple of (should_flush: bool, reason: str, pending_count: int)
    """
    config = _get_settings()

    if not config["enabled"]:
        return False, "disabled", 0

    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False, "no_redis", 0

        pending_key = _get_key("pending", repo)
        pending_count = r.llen(pending_key)

        if pending_count == 0:
            return False, "empty", 0

        # Check count-based trigger
        if pending_count >= config["count_threshold"]:
            return True, "count_threshold", pending_count

        # Check time-based trigger (opportunistic)
        now = datetime.now(timezone.utc)
        current_hour = now.hour

        if current_hour >= config["flush_hour_utc"]:
            # Check if already flushed today
            last_flush_key = _get_key("last_flush", repo)
            last_flush_str = r.get(last_flush_key)

            if last_flush_str:
                last_flush_date = datetime.fromisoformat(last_flush_str).date()
                if last_flush_date >= now.date():
                    return False, "already_flushed_today", pending_count

            return True, "time_trigger", pending_count

        return False, "not_triggered", pending_count

    except Exception as e:
        logger.warning(f"[DocsDigest] Error checking flush condition: {e}")
        return False, f"error: {e}", 0


def _acquire_flush_lock(repo: str, redis_url: Optional[str] = None) -> tuple:
    """
    Acquire distributed lock for flush operation.

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        Tuple of (acquired: bool, lock_token: str)
    """
    config = _get_settings()

    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False, ""

        lock_key = _get_key("lock", repo)
        lock_token = str(uuid.uuid4())

        # Atomic SET NX EX
        acquired = r.set(lock_key, lock_token, nx=True, ex=config["lock_ttl"])

        if acquired:
            logger.info(
                f"[DocsDigest] Acquired flush lock (token={lock_token[:8]}...)",
                extra={
                    "operation": "docs_digest_lock_acquired",
                    "repo": repo,
                    "lock_token": lock_token[:8],
                    "ttl": config["lock_ttl"],
                }
            )
            return True, lock_token
        else:
            logger.debug(
                "[DocsDigest] Failed to acquire flush lock (already held)",
                extra={
                    "operation": "docs_digest_lock_busy",
                    "repo": repo,
                }
            )
            return False, ""

    except Exception as e:
        logger.warning(f"[DocsDigest] Error acquiring flush lock: {e}")
        return False, ""


def _release_flush_lock(repo: str, lock_token: str, redis_url: Optional[str] = None) -> bool:
    """
    Release distributed lock for flush operation.

    Args:
        repo: Repository in owner/repo format
        lock_token: Token from _acquire_flush_lock
        redis_url: Optional Redis URL override

    Returns:
        True if released successfully
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        lock_key = _get_key("lock", repo)

        # Verify token before releasing (prevent releasing someone else's lock)
        current_token = r.get(lock_key)
        if current_token == lock_token:
            r.delete(lock_key)
            logger.info(
                f"[DocsDigest] Released flush lock (token={lock_token[:8]}...)",
                extra={
                    "operation": "docs_digest_lock_released",
                    "repo": repo,
                }
            )
            return True
        else:
            logger.warning(
                "[DocsDigest] Lock token mismatch, not releasing",
                extra={
                    "operation": "docs_digest_lock_mismatch",
                    "repo": repo,
                    "expected": lock_token[:8] if lock_token else "none",
                    "actual": current_token[:8] if current_token else "none",
                }
            )
            return False

    except Exception as e:
        logger.warning(f"[DocsDigest] Error releasing flush lock: {e}")
        return False


def _move_pending_to_processing(repo: str, redis_url: Optional[str] = None) -> List[BlockedDocChange]:
    """
    Atomically move items from pending to processing list.

    This two-stage pattern ensures data safety during flush:
    - If flush fails, items remain in processing for retry
    - If flush succeeds, processing is cleared

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        List of BlockedDocChange items to process
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return []

        pending_key = _get_key("pending", repo)
        processing_key = _get_key("processing", repo)

        items = []
        # Use RPOPLPUSH for atomic move (FIFO order)
        while True:
            item_json = r.rpoplpush(pending_key, processing_key)
            if not item_json:
                break
            try:
                item = BlockedDocChange.from_dict(json.loads(item_json))
                items.append(item)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"[DocsDigest] Invalid item in pending: {e}")
                continue

        if items:
            r.expire(processing_key, DEFAULT_ITEM_TTL_SECONDS)

        logger.info(
            f"[DocsDigest] Moved {len(items)} items to processing",
            extra={
                "operation": "docs_digest_move_to_processing",
                "repo": repo,
                "item_count": len(items),
            }
        )

        return items

    except Exception as e:
        logger.warning(f"[DocsDigest] Error moving items to processing: {e}")
        return []


def _clear_processing(repo: str, redis_url: Optional[str] = None) -> bool:
    """
    Clear processing list after successful flush.

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        True if cleared successfully
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        processing_key = _get_key("processing", repo)
        r.delete(processing_key)

        logger.info(
            "[DocsDigest] Cleared processing list",
            extra={
                "operation": "docs_digest_clear_processing",
                "repo": repo,
            }
        )
        return True

    except Exception as e:
        logger.warning(f"[DocsDigest] Error clearing processing: {e}")
        return False


def _restore_processing_to_pending(repo: str, redis_url: Optional[str] = None) -> bool:
    """
    Restore items from processing back to pending on flush failure.

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        True if restored successfully
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        pending_key = _get_key("pending", repo)
        processing_key = _get_key("processing", repo)

        count = 0
        while True:
            item_json = r.rpoplpush(processing_key, pending_key)
            if not item_json:
                break
            count += 1

        if count > 0:
            r.expire(pending_key, DEFAULT_ITEM_TTL_SECONDS)

        logger.info(
            f"[DocsDigest] Restored {count} items to pending",
            extra={
                "operation": "docs_digest_restore_to_pending",
                "repo": repo,
                "item_count": count,
            }
        )
        return True

    except Exception as e:
        logger.warning(f"[DocsDigest] Error restoring to pending: {e}")
        return False


def _merge_changes_by_path(changes: List[BlockedDocChange]) -> Dict[str, BlockedDocChange]:
    """
    Merge multiple changes to the same file path (latest wins).

    Args:
        changes: List of blocked changes

    Returns:
        Dict mapping doc_file_path to the latest change
    """
    merged = {}
    for change in changes:
        path = change.doc_file_path
        if path not in merged or change.created_at > merged[path].created_at:
            merged[path] = change

    return merged


def _update_last_flush_time(repo: str, redis_url: Optional[str] = None) -> bool:
    """
    Update the last flush timestamp.

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        True if updated successfully
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        last_flush_key = _get_key("last_flush", repo)
        now = datetime.now(timezone.utc).isoformat()
        r.set(last_flush_key, now)
        r.expire(last_flush_key, DEFAULT_ITEM_TTL_SECONDS)

        return True

    except Exception as e:
        logger.warning(f"[DocsDigest] Error updating last flush time: {e}")
        return False


def _create_digest_pr(
    repo: str,
    changes: Dict[str, BlockedDocChange],
    redis_url: Optional[str] = None
) -> Optional[str]:
    """
    Create a single aggregated PR for all blocked changes.

    Args:
        repo: Repository in owner/repo format
        changes: Dict mapping doc_file_path to BlockedDocChange
        redis_url: Optional Redis URL override

    Returns:
        PR URL if created successfully, None otherwise
    """
    if not changes:
        return None

    try:
        from tools.github_api import get_repo, create_branch, commit_file, open_pr
        from utils.constants import LABEL_ORCHESTRATOR_DOCS

        github_repo = get_repo()
        if not github_repo:
            logger.error("[DocsDigest] Failed to get GitHub repo")
            return None

        # Generate unique branch name
        timestamp = int(time.time())
        branch_name = f"orchestrator/docs-digest-{timestamp}"

        # Create branch
        branch = create_branch(github_repo, base="main", new_branch=branch_name)
        if not branch or branch == "demo-branch":
            logger.error("[DocsDigest] Failed to create branch")
            return None

        # Commit each file, tracking successes and failures
        successful_changes: dict = {}
        failed_commits: list = []
        for path, change in changes.items():
            commit_msg = f"docs: {change.goal[:50]} (digest trace: {change.trace_id[:8]})"
            result = commit_file(github_repo, branch, path, change.content, commit_msg)
            if result.success:
                successful_changes[path] = change
            else:
                logger.warning(
                    f"[DocsDigest] Failed to commit {path}: {result.status} - {result.message}",
                    extra={
                        "operation": "docs_digest_commit_failed",
                        "path": path,
                        "status": result.status,
                        "message": result.message,
                    }
                )
                failed_commits.append(path)

        # If all commits failed, abort PR creation
        if not successful_changes:
            logger.error("[DocsDigest] All commits failed, aborting PR creation")
            return None

        # Generate trace_ids from successful changes
        trace_ids = [c.trace_id[:8] for c in successful_changes.values()]

        # Build PR body using only successful changes
        pr_body = f"""## Automated Documentation Digest

This PR aggregates {len(successful_changes)} blocked documentation changes that were below the Value Gate threshold.

### Included Changes

| File | Goal | Score | Trace ID |
|------|------|-------|----------|
"""
        for path, change in successful_changes.items():
            pr_body += f"| `{path}` | {change.goal[:50]}... | {change.score} | `{change.trace_id[:8]}` |\n"

        # Add failed commits section if any
        if failed_commits:
            pr_body += f"""
### Failed Commits

The following {len(failed_commits)} file(s) could not be committed and are not included in this PR:
"""
            for path in failed_commits:
                pr_body += f"- `{path}`\n"

        pr_body += f"""
### Why This PR Exists

The Value Gate (Layer 1) blocks low-significance changes (score < 30) to prevent garbage PR flooding.
Instead of discarding these changes, the Docs Digest Strategy (Layer 2) accumulates them and creates
periodic summary PRs like this one.

**Trade-off:** Individual changes are batched together, reducing PR noise while preserving documentation updates.

---

**Digest Timestamp:** {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
**Successful Changes:** {len(successful_changes)}
**Trace IDs:** {', '.join(trace_ids)}

[Link to Devin run](https://app.devin.ai/sessions/199f2f07612d42fd88f6b030768a3247)
Requested by: @RC918
"""

        # Create PR with orchestrator-docs label to prevent self-trigger
        pr_url, pr_num = open_pr(
            github_repo,
            branch,
            f"docs: Digest update ({len(successful_changes)} changes)",
            body=pr_body,
            draft=False,
            labels=[LABEL_ORCHESTRATOR_DOCS, "orchestrator-digest"]
        )

        if pr_url and pr_url != "demo-pr-url":
            logger.info(
                f"[DocsDigest] Created digest PR: {pr_url}",
                extra={
                    "operation": "docs_digest_pr_created",
                    "repo": repo,
                    "pr_url": pr_url,
                    "pr_num": pr_num,
                    "change_count": len(changes),
                }
            )
            return pr_url
        else:
            logger.error("[DocsDigest] Failed to create PR")
            return None

    except Exception as e:
        logger.error(
            f"[DocsDigest] Error creating digest PR: {e}",
            extra={
                "operation": "docs_digest_pr_error",
                "repo": repo,
                "error": str(e),
            }
        )
        return None


def maybe_flush_docs_digest(
    repo: str,
    redis_url: Optional[str] = None
) -> Optional[str]:
    """
    Check if digest should be flushed and create PR if needed.

    This function is called after recording a blocked change.
    It checks trigger conditions and creates an aggregated PR if needed.

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        PR URL if created, None otherwise
    """
    config = _get_settings()

    if not config["enabled"]:
        return None

    # Check if flush is needed
    should_flush, reason, pending_count = _should_flush(repo, redis_url)

    if not should_flush:
        logger.debug(
            f"[DocsDigest] Flush not needed: {reason}",
            extra={
                "operation": "docs_digest_flush_check",
                "repo": repo,
                "reason": reason,
                "pending_count": pending_count,
            }
        )
        return None

    # Try to acquire lock
    acquired, lock_token = _acquire_flush_lock(repo, redis_url)
    if not acquired:
        logger.info(
            "[DocsDigest] Another worker is flushing, skipping",
            extra={
                "operation": "docs_digest_flush_skip",
                "repo": repo,
                "reason": "lock_busy",
            }
        )
        return None

    pr_url = None
    try:
        # Move items to processing (two-stage pattern for data safety)
        items = _move_pending_to_processing(repo, redis_url)

        if not items:
            logger.info(
                "[DocsDigest] No items to flush after move",
                extra={
                    "operation": "docs_digest_flush_empty",
                    "repo": repo,
                }
            )
            return None

        # Merge changes by path (latest wins)
        merged_changes = _merge_changes_by_path(items)

        logger.info(
            f"[DocsDigest] Flushing {len(items)} items ({len(merged_changes)} unique paths)",
            extra={
                "operation": "docs_digest_flush_start",
                "repo": repo,
                "reason": reason,
                "total_items": len(items),
                "unique_paths": len(merged_changes),
            }
        )

        # Create digest PR
        pr_url = _create_digest_pr(repo, merged_changes, redis_url)

        if pr_url:
            # Success: clear processing and update last flush time
            _clear_processing(repo, redis_url)
            _update_last_flush_time(repo, redis_url)

            # Clear seen set for flushed items
            try:
                r = _get_redis_client(redis_url)
                if r:
                    seen_key = _get_key("seen", repo)
                    for change in merged_changes.values():
                        r.srem(seen_key, change.changeset_hash)
            except Exception:
                pass  # Non-critical

            logger.info(
                f"[DocsDigest] Flush completed successfully: {pr_url}",
                extra={
                    "operation": "docs_digest_flush_success",
                    "repo": repo,
                    "pr_url": pr_url,
                    "change_count": len(merged_changes),
                }
            )
        else:
            # Failure: restore items to pending for retry
            _restore_processing_to_pending(repo, redis_url)
            logger.error(
                "[DocsDigest] Flush failed, items restored to pending",
                extra={
                    "operation": "docs_digest_flush_failed",
                    "repo": repo,
                    "item_count": len(items),
                }
            )

    except Exception as e:
        # Restore items on any error
        _restore_processing_to_pending(repo, redis_url)
        logger.error(
            f"[DocsDigest] Flush error: {e}",
            extra={
                "operation": "docs_digest_flush_error",
                "repo": repo,
                "error": str(e),
            }
        )

    finally:
        # Always release lock
        _release_flush_lock(repo, lock_token, redis_url)

    return pr_url


def get_pending_count(repo: str, redis_url: Optional[str] = None) -> int:
    """
    Get the number of pending blocked changes.

    Args:
        repo: Repository in owner/repo format
        redis_url: Optional Redis URL override

    Returns:
        Number of pending items
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return 0

        pending_key = _get_key("pending", repo)
        return r.llen(pending_key)

    except Exception:
        return 0
