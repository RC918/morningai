"""
PR Deduplication (Memory v2 Short-term Memory) for Publisher Node

Blueprint Alignment:
- Memory v2 (Layer 1 - Short-term): Tracks recent PR creations
- Flow Controller v3: Called before PR creation in Publisher Node
- Safety Governor v2: Prevents duplicate/similar PRs

Purpose:
Before creating a PR, check if a similar PR was recently created.
This prevents the Orchestrator from creating duplicate PRs for:
1. Same changeset (exact duplicate)
2. Similar goal/task (semantic duplicate)
3. Same file paths (path-based duplicate)

Feature Flags:
- ENABLE_PR_DEDUPLICATION: Master switch (default: True)
- PR_DEDUP_WINDOW_SECONDS: Time window for dedup check (default: 3600 = 1 hour)
- PR_DEDUP_SIMILARITY_THRESHOLD: Similarity threshold (default: 0.8)
- PR_DEDUP_DRY_RUN: Log-only mode for testing (default: True)

Issue: Memory v2 Short-term Deduplication (垃圾PR Prevention)
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_DEDUP_WINDOW_SECONDS = 3600  # 1 hour
DEFAULT_SIMILARITY_THRESHOLD = 0.8
REDIS_KEY_PREFIX = "orchestrator:pr_dedup"


@dataclass
class PRRecord:
    """Record of a PR creation for deduplication"""
    trace_id: str
    goal: str
    changeset_hash: str
    file_paths: List[str]
    pr_url: Optional[str]
    pr_number: Optional[int]
    created_at: float
    repo: str
    branch: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "goal": self.goal,
            "changeset_hash": self.changeset_hash,
            "file_paths": self.file_paths,
            "pr_url": self.pr_url,
            "pr_number": self.pr_number,
            "created_at": self.created_at,
            "repo": self.repo,
            "branch": self.branch
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PRRecord":
        return cls(
            trace_id=data.get("trace_id", ""),
            goal=data.get("goal", ""),
            changeset_hash=data.get("changeset_hash", ""),
            file_paths=data.get("file_paths", []),
            pr_url=data.get("pr_url"),
            pr_number=data.get("pr_number"),
            created_at=data.get("created_at", 0),
            repo=data.get("repo", ""),
            branch=data.get("branch", "")
        )


@dataclass
class DeduplicationResult:
    """Result of PR deduplication check"""
    is_duplicate: bool
    should_create_pr: bool
    duplicate_type: Optional[str] = None  # "exact", "semantic", "path"
    matching_pr: Optional[PRRecord] = None
    similarity_score: float = 0.0
    reasoning: str = ""
    dry_run: bool = False


def _get_redis_client(redis_url: Optional[str] = None):
    """
    Get Redis client for deduplication storage.
    
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
            logger.warning("[PRDedup] No Redis URL configured")
            return None
    except Exception as e:
        logger.warning(f"[PRDedup] Failed to connect to Redis: {e}")
        return None


def _get_dedup_key(repo: str) -> str:
    """Get Redis key for PR deduplication records"""
    try:
        from common.config.settings import settings
        prefix = getattr(settings, 'redis_key_prefix', '') or ''
        prefix = prefix.rstrip(':')
    except ImportError:
        prefix = ''
    
    base_key = f"{REDIS_KEY_PREFIX}:{repo}"
    return f"{prefix}:{base_key}" if prefix else base_key


def _normalize_goal(goal: str) -> str:
    """
    Normalize a goal string for comparison.
    
    Args:
        goal: Original goal string
        
    Returns:
        Normalized goal string
    """
    # Lowercase
    normalized = goal.lower()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    # Remove common prefixes
    prefixes = ['fix:', 'feat:', 'docs:', 'refactor:', 'chore:', 'test:']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    return normalized


def _calculate_goal_similarity(goal1: str, goal2: str) -> float:
    """
    Calculate similarity between two goals using Jaccard similarity.
    
    Args:
        goal1: First goal string
        goal2: Second goal string
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize goals
    norm1 = _normalize_goal(goal1)
    norm2 = _normalize_goal(goal2)
    
    # Tokenize
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard similarity
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    return len(intersection) / len(union)


def _calculate_path_similarity(paths1: List[str], paths2: List[str]) -> float:
    """
    Calculate similarity between two sets of file paths.
    
    Args:
        paths1: First list of file paths
        paths2: Second list of file paths
        
    Returns:
        Similarity score between 0 and 1
    """
    if not paths1 or not paths2:
        return 0.0
    
    set1 = set(paths1)
    set2 = set(paths2)
    
    intersection = set1 & set2
    union = set1 | set2
    
    return len(intersection) / len(union)


def record_pr_creation(
    trace_id: str,
    goal: str,
    changeset_hash: str,
    file_paths: List[str],
    repo: str,
    branch: str,
    pr_url: Optional[str] = None,
    pr_number: Optional[int] = None,
    redis_url: Optional[str] = None
) -> bool:
    """
    Record a PR creation for future deduplication checks.
    
    Blueprint Alignment:
    - Memory v2 (Layer 1): Stores short-term PR creation records
    - Telemetry v2: Enables traceability of PR creation decisions
    
    Args:
        trace_id: Unique trace ID
        goal: Task goal/description
        changeset_hash: Hash of the changeset
        file_paths: List of files in the changeset
        repo: Repository (owner/repo format)
        branch: Branch name
        pr_url: Optional PR URL
        pr_number: Optional PR number
        redis_url: Optional Redis URL override
        
    Returns:
        True if recorded successfully, False otherwise
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False
        
        record = PRRecord(
            trace_id=trace_id,
            goal=goal,
            changeset_hash=changeset_hash,
            file_paths=file_paths,
            pr_url=pr_url,
            pr_number=pr_number,
            created_at=time.time(),
            repo=repo,
            branch=branch
        )
        
        key = _get_dedup_key(repo)
        
        # Store as sorted set with timestamp as score
        r.zadd(key, {json.dumps(record.to_dict()): record.created_at})
        
        # Set TTL on the key (2x the dedup window for safety)
        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS
        
        r.expire(key, window * 2)
        
        logger.info("[PRDedup] Recorded PR creation", extra={
            "operation": "pr_dedup_record",
            "trace_id": trace_id,
            "repo": repo,
            "changeset_hash": changeset_hash,
            "file_count": len(file_paths)
        })
        
        return True
        
    except Exception as e:
        logger.warning(f"[PRDedup] Failed to record PR creation: {e}", extra={
            "operation": "pr_dedup_record_error",
            "trace_id": trace_id,
            "error": str(e)
        })
        return False


def check_pr_deduplication(
    goal: str,
    changeset_hash: str,
    file_paths: List[str],
    repo: str,
    trace_id: Optional[str] = None,
    redis_url: Optional[str] = None
) -> DeduplicationResult:
    """
    Check if a similar PR was recently created.
    
    Blueprint Alignment:
    - Memory v2 (Layer 1): Queries short-term PR creation records
    - Flow Controller v3: Called before PR creation in Publisher Node
    - Safety Governor v2: Part of the governance layer
    
    Args:
        goal: Task goal/description
        changeset_hash: Hash of the changeset
        file_paths: List of files in the changeset
        repo: Repository (owner/repo format)
        trace_id: Optional trace ID for logging
        redis_url: Optional Redis URL override
        
    Returns:
        DeduplicationResult with decision
    """
    # Check if deduplication is enabled
    try:
        from common.config.settings import settings
        enabled = getattr(settings, 'enable_pr_deduplication', True)
        dry_run = getattr(settings, 'pr_dedup_dry_run', True)
        window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
        window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        threshold = getattr(settings, 'pr_dedup_similarity_threshold', DEFAULT_SIMILARITY_THRESHOLD)
        threshold = threshold or DEFAULT_SIMILARITY_THRESHOLD
    except ImportError:
        enabled = True
        dry_run = True
        window = DEFAULT_DEDUP_WINDOW_SECONDS
        threshold = DEFAULT_SIMILARITY_THRESHOLD
    
    if not enabled:
        logger.info("[PRDedup] Feature disabled, allowing PR creation", extra={
            "operation": "pr_dedup",
            "trace_id": trace_id,
            "enabled": False
        })
        return DeduplicationResult(
            is_duplicate=False,
            should_create_pr=True,
            reasoning="PR deduplication disabled"
        )
    
    try:
        r = _get_redis_client(redis_url)
        if not r:
            logger.warning("[PRDedup] Redis unavailable, allowing PR creation", extra={
                "operation": "pr_dedup",
                "trace_id": trace_id
            })
            return DeduplicationResult(
                is_duplicate=False,
                should_create_pr=True,
                reasoning="Redis unavailable, skipping dedup check"
            )
        
        key = _get_dedup_key(repo)
        
        # Get recent PR records within the time window
        min_time = time.time() - window
        records_json = r.zrangebyscore(key, min_time, '+inf')
        
        if not records_json:
            logger.info("[PRDedup] No recent PRs found, allowing creation", extra={
                "operation": "pr_dedup",
                "trace_id": trace_id,
                "repo": repo
            })
            return DeduplicationResult(
                is_duplicate=False,
                should_create_pr=True,
                reasoning="No recent PRs in dedup window"
            )
        
        # Check for duplicates
        for record_json in records_json:
            try:
                record = PRRecord.from_dict(json.loads(record_json))
            except (json.JSONDecodeError, KeyError):
                continue
            
            # Check 1: Exact changeset match
            if record.changeset_hash == changeset_hash:
                result = DeduplicationResult(
                    is_duplicate=True,
                    should_create_pr=dry_run,  # Allow in dry-run mode
                    duplicate_type="exact",
                    matching_pr=record,
                    similarity_score=1.0,
                    reasoning=f"Exact changeset match with PR #{record.pr_number} (trace: {record.trace_id})",
                    dry_run=dry_run
                )
                _log_dedup_result(result, trace_id)
                return result
            
            # Check 2: Semantic similarity (goal)
            goal_similarity = _calculate_goal_similarity(goal, record.goal)
            if goal_similarity >= threshold:
                pr_num = record.pr_number
                tr_id = record.trace_id
                result = DeduplicationResult(
                    is_duplicate=True,
                    should_create_pr=dry_run,
                    duplicate_type="semantic",
                    matching_pr=record,
                    similarity_score=goal_similarity,
                    reasoning=f"Semantic match ({goal_similarity:.2f}) with PR #{pr_num} (trace: {tr_id})",
                    dry_run=dry_run
                )
                _log_dedup_result(result, trace_id)
                return result

            # Check 3: Path similarity
            path_similarity = _calculate_path_similarity(file_paths, record.file_paths)
            if path_similarity >= threshold:
                pr_num = record.pr_number
                tr_id = record.trace_id
                result = DeduplicationResult(
                    is_duplicate=True,
                    should_create_pr=dry_run,
                    duplicate_type="path",
                    matching_pr=record,
                    similarity_score=path_similarity,
                    reasoning=f"Path match ({path_similarity:.2f}) with PR #{pr_num} (trace: {tr_id})",
                    dry_run=dry_run
                )
                _log_dedup_result(result, trace_id)
                return result
        
        # No duplicates found
        logger.info("[PRDedup] No duplicates found, allowing creation", extra={
            "operation": "pr_dedup",
            "trace_id": trace_id,
            "repo": repo,
            "records_checked": len(records_json)
        })
        return DeduplicationResult(
            is_duplicate=False,
            should_create_pr=True,
            reasoning=f"No duplicates found in {len(records_json)} recent PRs"
        )
        
    except Exception as e:
        logger.warning(f"[PRDedup] Error during dedup check: {e}", extra={
            "operation": "pr_dedup_error",
            "trace_id": trace_id,
            "error": str(e)
        })
        return DeduplicationResult(
            is_duplicate=False,
            should_create_pr=True,
            reasoning=f"Error during dedup check: {e}"
        )


def _log_dedup_result(result: DeduplicationResult, trace_id: Optional[str]) -> None:
    """Log deduplication result"""
    log_extra = {
        "operation": "pr_dedup",
        "trace_id": trace_id,
        "is_duplicate": result.is_duplicate,
        "duplicate_type": result.duplicate_type,
        "similarity_score": result.similarity_score,
        "should_create_pr": result.should_create_pr,
        "dry_run": result.dry_run
    }
    
    if result.matching_pr:
        log_extra["matching_trace_id"] = result.matching_pr.trace_id
        log_extra["matching_pr_number"] = result.matching_pr.pr_number
    
    if result.dry_run:
        logger.warning(
            f"[PRDedup][DRY-RUN] Would block duplicate PR: {result.reasoning}",
            extra=log_extra
        )
    else:
        logger.warning(
            f"[PRDedup] Blocking duplicate PR: {result.reasoning}",
            extra=log_extra
        )


def cleanup_old_records(
    repo: str,
    redis_url: Optional[str] = None
) -> int:
    """
    Clean up old PR records outside the dedup window.
    
    Args:
        repo: Repository (owner/repo format)
        redis_url: Optional Redis URL override
        
    Returns:
        Number of records removed
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return 0
        
        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS

        key = _get_dedup_key(repo)
        min_time = time.time() - window

        # Remove records older than the window
        removed = r.zremrangebyscore(key, 0, min_time)
        
        if removed:
            logger.info(f"[PRDedup] Cleaned up {removed} old records", extra={
                "operation": "pr_dedup_cleanup",
                "repo": repo,
                "removed_count": removed
            })
        
        return removed
        
    except Exception as e:
        logger.warning(f"[PRDedup] Failed to cleanup old records: {e}")
        return 0


def get_recent_pr_count(
    repo: str,
    redis_url: Optional[str] = None
) -> int:
    """
    Get count of recent PRs in the dedup window.
    
    Args:
        repo: Repository (owner/repo format)
        redis_url: Optional Redis URL override
        
    Returns:
        Number of recent PRs
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return 0
        
        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS

        key = _get_dedup_key(repo)
        min_time = time.time() - window

        return r.zcount(key, min_time, '+inf')
        
    except Exception:
        return 0
