"""
Auto-Fix Policy Module - Safety Mechanisms for Auto-Fix Execution

This module provides safety mechanisms for auto-fix execution from AI reviewer comments,
including feature flags, rate limiting, and loop protection.

Issue #2251: Implement safety mechanisms for auto-fix executor

Components:
1. AutoFixPolicy - Feature flags and category/repo allowlist checks
2. AutoFixRateLimiter - Redis-based rate limiting (per-repo, per-PR, global)
3. AutoFixLoopProtection - Commit marking and max retry tracking
"""
import logging
import re
import redis
import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Set, Tuple

if TYPE_CHECKING:
    from common.config.settings import Settings
    from webhooks.comment_triage import CommentTriageResult

logger = logging.getLogger(__name__)

AUTO_FIX_COMMIT_MARKER = "[auto-fix]"
AUTO_FIX_RATE_LIMIT_WINDOW = 3600

# Issue #3794: Pre-compiled regex for Redis key sanitization
# Allows alphanumeric, underscore, forward slash, hash, and hyphen
_REDIS_KEY_SANITIZE_PATTERN = re.compile(r'[^a-zA-Z0-9_/#-]')

# Issue #3806: Pre-compiled regex patterns for timestamp sanitization in error messages
# These patterns match common timestamp formats that cause deduplication to fail
# Note: Using {0,30} limit on character classes to prevent ReDoS (catastrophic backtracking)
_TIMESTAMP_PATTERNS = [
    re.compile(r'\[\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\]]{0,30}\]'),  # [2024-01-11T10:00:00Z] or [2024-01-11 10:00:00]
    re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?'),  # ISO 8601 timestamps
    re.compile(r'\[\d{2}:\d{2}:\d{2}\]'),  # [10:00:00] time only
    re.compile(r'\d{2}:\d{2}:\d{2}\.\d+'),  # 10:00:00.123 with milliseconds
]

# Issue #3810: Keywords that indicate important error content for signature extraction
# These patterns help identify the most relevant parts of error messages
_ERROR_KEYWORDS = [
    'Error:', 'Exception:', 'FAILED', 'FAILURE', 'error:', 'exception:',
    'AssertionError', 'TypeError', 'ValueError', 'KeyError', 'AttributeError',
    'ImportError', 'ModuleNotFoundError', 'NameError', 'RuntimeError',
    'SyntaxError', 'IndentationError', 'FileNotFoundError', 'PermissionError',
    'FATAL', 'CRITICAL', 'Traceback', 'panic:', 'undefined', 'null pointer',
]

# Issue #3810: Regex patterns for line numbers and file paths in error messages
_LINE_NUMBER_PATTERN = re.compile(r'(?:line\s+\d+|:\d+:|\[\d+\])')
_FILE_PATH_PATTERN = re.compile(r'(?:/[\w./\-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|rb|cpp|c|h)|[\w./\-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|rb|cpp|c|h):\d+)')


def _sanitize_pr_id(pr_id: str) -> str:
    """
    Sanitize pr_id for use in Redis keys.

    Issue #3794: Defense-in-depth sanitization to prevent Redis key manipulation.
    Although pr_id components (repo, pr_number, trace_id) come from trusted sources
    (GitHub API, internal UUID generation), this sanitization provides an additional
    safety layer against potential injection attacks.

    Args:
        pr_id: Pull request identifier (e.g., "owner/repo#123" or trace_id UUID)

    Returns:
        Sanitized string safe for use in Redis keys
    """
    if not pr_id:
        return pr_id
    return _REDIS_KEY_SANITIZE_PATTERN.sub('_', pr_id)


def _extract_important_lines(error_text: str) -> list:
    """
    Extract lines containing important error indicators.

    Issue #3810: Intelligent keyword extraction to identify the most relevant
    parts of error messages for signature computation.

    Args:
        error_text: Error text to analyze

    Returns:
        List of lines containing important error indicators
    """
    if not error_text:
        return []

    lines = error_text.split('\n')
    important_lines = []

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for error keywords
        has_keyword = any(keyword in line for keyword in _ERROR_KEYWORDS)

        # Check for line numbers (e.g., "line 42", ":42:", "[42]")
        has_line_number = bool(_LINE_NUMBER_PATTERN.search(line))

        # Check for file paths with error context
        has_file_path = bool(_FILE_PATH_PATTERN.search(line))

        if has_keyword or has_line_number or has_file_path:
            important_lines.append(line_stripped)

    return important_lines


def _sanitize_error_for_signature(error_summary: str) -> str:
    """
    Sanitize error summary for CI signature computation.

    Issue #3806: Removes timestamps and extracts meaningful error content
    to prevent deduplication failures due to:
    1. Timestamp sensitivity - timestamps cause unique hashes every run
    2. Truncation blindness - important error details may be after char 500

    Issue #3810: Uses intelligent keyword extraction to identify the most
    relevant parts of error messages instead of simple head+tail truncation.

    Args:
        error_summary: Raw error summary text from CI logs

    Returns:
        Sanitized error digest suitable for signature computation
    """
    if not error_summary:
        return ""

    clean_error = error_summary

    # Strip timestamps that would cause unique hashes every run
    for pattern in _TIMESTAMP_PATTERNS:
        clean_error = pattern.sub('', clean_error)

    # Issue #3810: Try intelligent keyword extraction first
    important_lines = _extract_important_lines(clean_error)

    if important_lines:
        # Join important lines and use as digest if sufficient content
        extracted = '\n'.join(important_lines)
        # If extracted content is meaningful (at least 50 chars), use it
        if len(extracted) >= 50:
            # Still apply truncation if extracted content is too long
            if len(extracted) > 1500:
                error_digest = extracted[:1000] + "..." + extracted[-500:]
            else:
                error_digest = extracted
            return error_digest

    # Fallback: Take head + tail to capture both context and specific error
    # Stack traces often have generic framework calls first, real error at end
    if len(clean_error) > 1500:
        error_digest = clean_error[:1000] + "..." + clean_error[-500:]
    else:
        error_digest = clean_error

    return error_digest


@dataclass
class AutoFixPolicyResult:
    """Result of auto-fix policy check"""
    allowed: bool
    reason: str
    blocked_by: Optional[str] = None


@dataclass
class AutoFixRateLimitResult:
    """Result of auto-fix rate limit check"""
    allowed: bool
    exceeded_dimension: Optional[str] = None
    current_count: int = 0
    limit: int = 0
    repo: Optional[str] = None
    pr_id: Optional[str] = None


def get_allowed_categories(settings: "Settings") -> Set[str]:
    """
    Get the set of categories allowed for auto-fix from settings.

    Args:
        settings: Application settings

    Returns:
        Set of allowed category values (lowercase)
    """
    categories_str = settings.auto_fix_categories
    if not categories_str:
        return set()
    return {c.strip().lower() for c in categories_str.split(",") if c.strip()}


def get_allowed_repos(settings: "Settings") -> Set[str]:
    """
    Get the set of repos allowed for auto-fix from settings.

    Args:
        settings: Application settings

    Returns:
        Set of allowed repo names (empty set means all repos allowed)
    """
    repos_str = settings.auto_fix_repos_allowlist
    if not repos_str:
        return set()
    return {r.strip() for r in repos_str.split(",") if r.strip()}


def is_auto_fix_enabled(settings: "Settings") -> bool:
    """
    Check if auto-fix is globally enabled.

    Args:
        settings: Application settings

    Returns:
        True if auto-fix is enabled
    """
    return settings.auto_fix_enabled


def is_auto_fix_commit(commit_message: str) -> bool:
    """
    Check if a commit message indicates it was created by auto-fix.

    Args:
        commit_message: The commit message to check

    Returns:
        True if this is an auto-fix commit
    """
    if not commit_message:
        return False
    lower_msg = commit_message.lower()
    return AUTO_FIX_COMMIT_MARKER in lower_msg or lower_msg.startswith("auto-fix:")


def get_auto_fix_actors(settings: "Settings" = None) -> set:
    """
    Get the set of auto-fix actor names from settings.

    Args:
        settings: Application settings. If None, uses global settings.

    Returns:
        Set of actor names (lowercase)
    """
    if settings is None:
        from common.config.settings import settings as global_settings
        settings = global_settings
    actor_names = settings.auto_fix_actor_names
    return {name.strip().lower() for name in actor_names.split(",") if name.strip()}


def is_auto_fix_actor(actor_name: str, settings: "Settings" = None) -> bool:
    """
    Check if an actor name indicates it's the auto-fix bot.

    Args:
        actor_name: The actor/author name to check
        settings: Application settings. If None, uses global settings.

    Returns:
        True if this is the auto-fix bot
    """
    if not actor_name:
        return False
    auto_fix_actors = get_auto_fix_actors(settings)
    return actor_name.lower() in auto_fix_actors


class AutoFixPolicy:
    """
    Policy engine for auto-fix execution decisions.

    This class checks feature flags, category allowlists, and repo allowlists
    to determine if auto-fix should be allowed for a given triage result.
    """

    def __init__(self, settings: "Settings" = None):
        """
        Initialize AutoFixPolicy with settings.

        Args:
            settings: Application settings. If None, uses global settings.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            settings = global_settings
        self.settings = settings

    def check(
        self,
        triage_result: "CommentTriageResult",
        repo: str,
        pr_id: str,
        actor_name: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> AutoFixPolicyResult:
        """
        Check if auto-fix is allowed for a given triage result.

        Args:
            triage_result: Result from CommentTriageAgent
            repo: Repository name (e.g., "owner/repo")
            pr_id: Pull request identifier
            actor_name: Optional actor name to check for loop protection
            commit_message: Optional commit message to check for loop protection

        Returns:
            AutoFixPolicyResult with allowed status and reason
        """
        if not is_auto_fix_enabled(self.settings):
            logger.debug(
                "[AutoFixPolicy] Auto-fix disabled by AUTO_FIX_ENABLED=false",
                extra={
                    "operation": "auto_fix_policy_check",
                    "policy_result": "disabled",
                    "blocked_by": "feature_flag",
                }
            )
            return AutoFixPolicyResult(
                allowed=False,
                reason="Auto-fix is disabled (AUTO_FIX_ENABLED=false)",
                blocked_by="feature_flag",
            )

        if not triage_result.should_auto_fix:
            logger.debug(
                "[AutoFixPolicy] Triage result does not recommend auto-fix",
                extra={
                    "operation": "auto_fix_policy_check",
                    "policy_result": "triage_not_recommended",
                    "blocked_by": "triage_result",
                }
            )
            return AutoFixPolicyResult(
                allowed=False,
                reason="Triage result does not recommend auto-fix",
                blocked_by="triage_result",
            )

        if actor_name and is_auto_fix_actor(actor_name):
            logger.info(
                "[AutoFixPolicy] Blocking auto-fix for auto-fix-generated change",
                extra={
                    "operation": "auto_fix_policy_check",
                    "policy_result": "loop_protection",
                    "blocked_by": "actor_name",
                    "actor_name": actor_name,
                }
            )
            return AutoFixPolicyResult(
                allowed=False,
                reason=f"Blocking auto-fix for auto-fix-generated change (actor: {actor_name})",
                blocked_by="loop_protection_actor",
            )

        if commit_message and is_auto_fix_commit(commit_message):
            logger.info(
                "[AutoFixPolicy] Blocking auto-fix for auto-fix commit",
                extra={
                    "operation": "auto_fix_policy_check",
                    "policy_result": "loop_protection",
                    "blocked_by": "commit_message",
                }
            )
            return AutoFixPolicyResult(
                allowed=False,
                reason="Blocking auto-fix for auto-fix commit",
                blocked_by="loop_protection_commit",
            )

        category_value = triage_result.category.value
        allowed_categories = get_allowed_categories(self.settings)
        if category_value not in allowed_categories:
            logger.debug(
                "[AutoFixPolicy] Category not in allowlist",
                extra={
                    "operation": "auto_fix_policy_check",
                    "policy_result": "category_not_allowed",
                    "blocked_by": "category_allowlist",
                    "category": category_value,
                    "allowed_categories": list(allowed_categories),
                }
            )
            return AutoFixPolicyResult(
                allowed=False,
                reason=f"Category '{category_value}' not in allowlist: {allowed_categories}",
                blocked_by="category_allowlist",
            )

        allowed_repos = get_allowed_repos(self.settings)
        if allowed_repos and repo not in allowed_repos:
            logger.debug(
                "[AutoFixPolicy] Repo not in allowlist",
                extra={
                    "operation": "auto_fix_policy_check",
                    "policy_result": "repo_not_allowed",
                    "blocked_by": "repo_allowlist",
                    "repo": repo,
                    "allowed_repos": list(allowed_repos),
                }
            )
            return AutoFixPolicyResult(
                allowed=False,
                reason=f"Repo '{repo}' not in allowlist",
                blocked_by="repo_allowlist",
            )

        logger.info(
            "[AutoFixPolicy] Auto-fix allowed",
            extra={
                "operation": "auto_fix_policy_check",
                "policy_result": "allowed",
                "repo": repo,
                "pr_id": pr_id,
                "category": category_value,
            }
        )
        return AutoFixPolicyResult(
            allowed=True,
            reason="Auto-fix allowed by policy",
        )


class AutoFixRateLimiter:
    """
    Redis-based rate limiter for auto-fix execution.

    Implements three dimensions of rate limiting:
    - Per-repo per hour
    - Per-PR per hour
    - Global per hour
    """

    def __init__(self, settings: "Settings" = None, redis_url: Optional[str] = None):
        """
        Initialize AutoFixRateLimiter.

        Args:
            settings: Application settings. If None, uses global settings.
            redis_url: Redis connection URL. If None, uses settings.redis_url.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            settings = global_settings
        self.settings = settings
        self.redis_url = redis_url or settings.redis_url

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client, returning None if unavailable."""
        try:
            if self.redis_url:
                return redis.Redis.from_url(self.redis_url, decode_responses=True)
            return redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                decode_responses=True
            )
        except Exception as e:
            logger.error(
                "[AutoFixRateLimiter] ALERT: Failed to connect to Redis: %s",
                str(e),
                extra={
                    "operation": "auto_fix_rate_limit_redis_error",
                    "alert_type": "redis_connection_failure",
                    "component": "AutoFixRateLimiter",
                    "severity": "high",
                    "fail_open": True,
                }
            )
            return None

    def check(self, repo: str, pr_id: str) -> AutoFixRateLimitResult:
        """
        Check if auto-fix is rate limited.

        Args:
            repo: Repository name (e.g., "owner/repo")
            pr_id: Pull request identifier (e.g., "owner/repo#123")

        Returns:
            AutoFixRateLimitResult with allowed status and details
        """
        r = self._get_redis_client()
        if r is None:
            logger.error(
                "[AutoFixRateLimiter] ALERT: Redis unavailable, allowing request (fail-open)",
                extra={
                    "operation": "auto_fix_rate_limit_redis_unavailable",
                    "alert_type": "redis_unavailable",
                    "component": "AutoFixRateLimiter",
                    "severity": "high",
                    "fail_open": True,
                    "repo": repo,
                    "pr_id": pr_id,
                }
            )
            return AutoFixRateLimitResult(allowed=True, repo=repo, pr_id=pr_id)

        try:
            current_time = time.time()
            window_start = current_time - AUTO_FIX_RATE_LIMIT_WINDOW

            # Issue #3794: Sanitize pr_id and repo for Redis key safety
            safe_pr_id = _sanitize_pr_id(pr_id)
            safe_repo = _sanitize_pr_id(repo)  # repo has same format constraints

            dimensions = [
                ('pr', f"auto_fix:rate:pr:{safe_pr_id}", self.settings.auto_fix_per_pr_per_hour),
                ('repo', f"auto_fix:rate:repo:{safe_repo}", self.settings.auto_fix_per_repo_per_hour),
                ('global', "auto_fix:rate:global", self.settings.auto_fix_global_per_hour),
            ]

            for dimension, key, limit in dimensions:
                pipe = r.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                results = pipe.execute()
                current_count = results[1]

                if current_count >= limit:
                    logger.warning(
                        "[AutoFixRateLimiter] Rate limit exceeded",
                        extra={
                            "operation": "auto_fix_rate_limit_exceeded",
                            "dimension": dimension,
                            "current_count": current_count,
                            "limit": limit,
                            "repo": repo,
                            "pr_id": pr_id,
                        }
                    )
                    return AutoFixRateLimitResult(
                        allowed=False,
                        exceeded_dimension=dimension,
                        current_count=current_count,
                        limit=limit,
                        repo=repo,
                        pr_id=pr_id,
                    )

            unique_member = f"{time.time_ns()}-{uuid.uuid4()}"
            pipe = r.pipeline()
            for _, key, _ in dimensions:
                pipe.zadd(key, {unique_member: current_time})
                pipe.expire(key, AUTO_FIX_RATE_LIMIT_WINDOW + 60)
            pipe.execute()

            logger.debug(
                "[AutoFixRateLimiter] Rate limit check passed",
                extra={
                    "operation": "auto_fix_rate_limit_passed",
                    "repo": repo,
                    "pr_id": pr_id,
                }
            )
            return AutoFixRateLimitResult(allowed=True, repo=repo, pr_id=pr_id)

        except redis.ConnectionError as e:
            logger.warning(
                "[AutoFixRateLimiter] Redis connection error, allowing request: %s",
                str(e),
                extra={"operation": "auto_fix_rate_limit_redis_error"}
            )
            return AutoFixRateLimitResult(allowed=True, repo=repo, pr_id=pr_id)
        except Exception as e:
            logger.warning(
                "[AutoFixRateLimiter] Unexpected error, allowing request: %s",
                str(e),
                extra={"operation": "auto_fix_rate_limit_error"}
            )
            return AutoFixRateLimitResult(allowed=True, repo=repo, pr_id=pr_id)


class AutoFixLoopProtection:
    """
    Loop protection for auto-fix execution.

    Tracks the number of auto-fix attempts per PR and enforces max retry limits.
    """

    def __init__(self, settings: "Settings" = None, redis_url: Optional[str] = None):
        """
        Initialize AutoFixLoopProtection.

        Args:
            settings: Application settings. If None, uses global settings.
            redis_url: Redis connection URL. If None, uses settings.redis_url.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            settings = global_settings
        self.settings = settings
        self.redis_url = redis_url or settings.redis_url

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client, returning None if unavailable."""
        try:
            if self.redis_url:
                return redis.Redis.from_url(self.redis_url, decode_responses=True)
            return redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                decode_responses=True
            )
        except Exception as e:
            logger.error(
                "[AutoFixLoopProtection] ALERT: Failed to connect to Redis: %s",
                str(e),
                extra={
                    "operation": "auto_fix_loop_protection_redis_error",
                    "alert_type": "redis_connection_failure",
                    "component": "AutoFixLoopProtection",
                    "severity": "high",
                    "fail_open": True,
                }
            )
            return None

    def check_only(self, pr_id: str) -> Tuple[bool, int]:
        """
        Check if auto-fix attempts for a PR have exceeded the max retry limit.
        Does NOT increment the counter - use increment() after actual fix attempt.

        Issue #3792: Separating check and increment prevents race condition where
        PR_OPENED webhook exhausts the counter before CI_FAILURE webhook arrives.

        Args:
            pr_id: Pull request identifier (e.g., "owner/repo#123")

        Returns:
            Tuple of (allowed: bool, current_attempts: int)
        """
        r = self._get_redis_client()
        if r is None:
            logger.error(
                "[AutoFixLoopProtection] ALERT: Redis unavailable, allowing request (fail-open)",
                extra={
                    "operation": "auto_fix_loop_protection_redis_unavailable",
                    "alert_type": "redis_unavailable",
                    "component": "AutoFixLoopProtection",
                    "severity": "high",
                    "fail_open": True,
                    "pr_id": pr_id,
                }
            )
            return True, 0

        try:
            # Issue #3794: Sanitize pr_id for Redis key safety
            safe_pr_id = _sanitize_pr_id(pr_id)
            key = f"auto_fix:attempts:{safe_pr_id}"
            max_retries = self.settings.auto_fix_max_retries

            current_attempts = r.get(key)
            current_attempts = int(current_attempts) if current_attempts else 0

            if current_attempts >= max_retries:
                logger.warning(
                    "[AutoFixLoopProtection] Max retries exceeded",
                    extra={
                        "operation": "auto_fix_max_retries_exceeded",
                        "pr_id": pr_id,
                        "current_attempts": current_attempts,
                        "max_retries": max_retries,
                    }
                )
                return False, current_attempts

            return True, current_attempts

        except redis.ConnectionError as e:
            logger.warning(
                "[AutoFixLoopProtection] Redis connection error, allowing request: %s",
                str(e),
                extra={"operation": "auto_fix_loop_protection_redis_error"}
            )
            return True, 0
        except Exception as e:
            logger.warning(
                "[AutoFixLoopProtection] Unexpected error, allowing request: %s",
                str(e),
                extra={"operation": "auto_fix_loop_protection_error"}
            )
            return True, 0

    def increment(self, pr_id: str) -> int:
        """
        Increment the auto-fix attempt counter for a PR.
        Should be called AFTER an actual fix attempt is made.

        Issue #3792: Only increment after actual fix attempt to prevent
        race condition where early returns exhaust the counter.

        Args:
            pr_id: Pull request identifier (e.g., "owner/repo#123")

        Returns:
            New attempt count, or 0 if increment failed
        """
        r = self._get_redis_client()
        if r is None:
            return 0

        try:
            key = f"auto_fix:attempts:{pr_id}"
            max_retries = self.settings.auto_fix_max_retries

            new_count = r.incr(key)
            r.expire(key, 86400 * 7)

            logger.info(
                "[AutoFixLoopProtection] Attempt recorded after fix",
                extra={
                    "operation": "auto_fix_attempt_recorded",
                    "pr_id": pr_id,
                    "attempt_number": new_count,
                    "max_retries": max_retries,
                }
            )
            return new_count

        except Exception as e:
            logger.warning(
                "[AutoFixLoopProtection] Failed to increment counter: %s",
                str(e),
                extra={"operation": "auto_fix_loop_protection_increment_error"}
            )
            return 0

    def check_and_increment(self, pr_id: str) -> Tuple[bool, int]:
        """
        Check if auto-fix attempts for a PR have exceeded the max retry limit.
        If allowed, increments the attempt counter.

        DEPRECATED: Use check_only() + increment() for better control.
        This method is kept for backward compatibility.

        Args:
            pr_id: Pull request identifier (e.g., "owner/repo#123")

        Returns:
            Tuple of (allowed: bool, current_attempts: int)
        """
        allowed, current_attempts = self.check_only(pr_id)
        if allowed:
            new_count = self.increment(pr_id)
            # Issue #3793: Return actual Redis state on increment failure
            # If increment fails (returns 0), return current_attempts to reflect
            # the actual state rather than an optimistic estimate
            return True, new_count if new_count > 0 else current_attempts
        return False, current_attempts

    def get_attempts(self, pr_id: str) -> int:
        """
        Get the current number of auto-fix attempts for a PR.

        Args:
            pr_id: Pull request identifier

        Returns:
            Number of attempts, or 0 if unavailable
        """
        r = self._get_redis_client()
        if r is None:
            return 0

        try:
            # Issue #3794: Sanitize pr_id for Redis key safety
            safe_pr_id = _sanitize_pr_id(pr_id)
            key = f"auto_fix:attempts:{safe_pr_id}"
            count = r.get(key)
            return int(count) if count else 0
        except Exception:
            return 0

    def reset_attempts(self, pr_id: str) -> bool:
        """
        Reset the auto-fix attempt counter for a PR.

        Args:
            pr_id: Pull request identifier

        Returns:
            True if reset was successful
        """
        r = self._get_redis_client()
        if r is None:
            return False

        try:
            # Issue #3794: Sanitize pr_id for Redis key safety
            safe_pr_id = _sanitize_pr_id(pr_id)
            key = f"auto_fix:attempts:{safe_pr_id}"
            r.delete(key)
            logger.info(
                "[AutoFixLoopProtection] Attempts reset",
                extra={
                    "operation": "auto_fix_attempts_reset",
                    "pr_id": pr_id,
                }
            )
            return True
        except Exception as e:
            logger.warning(
                "[AutoFixLoopProtection] Failed to reset attempts: %s",
                str(e),
                extra={"operation": "auto_fix_attempts_reset_error"}
            )
            return False


class CISignatureDeduplication:
    """
    CI signature deduplication to prevent re-processing identical failures.

    Cost Optimization: Tracks CI failure signatures (hash of check_name + error_digest)
    to avoid running the same fix attempt multiple times within a time window.

    This is different from AutoFixLoopProtection which counts attempts per PR.
    CISignatureDeduplication prevents re-processing the EXACT SAME failure.
    """

    # Default TTL: 24 hours (in seconds)
    DEFAULT_TTL = 86400

    def __init__(self, settings: "Settings" = None, redis_url: Optional[str] = None):
        """
        Initialize CISignatureDeduplication.

        Args:
            settings: Application settings. If None, uses global settings.
            redis_url: Redis connection URL. If None, uses settings.redis_url.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            settings = global_settings
        self.settings = settings
        self.redis_url = redis_url or settings.redis_url

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client, returning None if unavailable."""
        try:
            if self.redis_url:
                return redis.Redis.from_url(self.redis_url, decode_responses=True)
            return redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                decode_responses=True
            )
        except Exception as e:
            logger.error(
                "[CISignatureDeduplication] ALERT: Failed to connect to Redis: %s",
                str(e),
                extra={
                    "operation": "ci_signature_dedup_redis_error",
                    "alert_type": "redis_connection_failure",
                    "component": "CISignatureDeduplication",
                    "severity": "high",
                    "fail_open": True,
                }
            )
            return None

    def _compute_signature(
        self,
        pr_id: str,
        commit_sha: str,
        failed_check_name: str,
        error_digest: str,
    ) -> str:
        """
        Compute a unique signature for a CI failure.

        Issue #3806: Added commit_sha to signature to enable Self-Correction Loop.
        Without commit_sha, identical error messages after code changes would be
        treated as duplicates, blocking valid retry attempts.

        Args:
            pr_id: Pull request identifier
            commit_sha: Git commit SHA (new code = new retry opportunity)
            failed_check_name: Name of the failed CI check
            error_digest: Sanitized error message digest

        Returns:
            SHA256 hash of the combined signature (16 hex chars = 64 bits)
        """
        import hashlib
        # Issue #3794: Sanitize pr_id for Redis key safety
        safe_pr_id = _sanitize_pr_id(pr_id)
        # Issue #3806: Include commit_sha so new code gets new retry opportunity
        signature_input = f"{safe_pr_id}:{commit_sha}:{failed_check_name}:{error_digest}"
        return hashlib.sha256(signature_input.encode()).hexdigest()[:16]

    def check_and_mark(
        self,
        pr_id: str,
        failed_check_name: str,
        error_summary: str,
        ttl: int = None,
        commit_sha: str = "",
    ) -> tuple:
        """
        Check if this CI failure signature has been processed recently.
        If not, mark it as processed.

        Issue #3806: Added commit_sha parameter to enable Self-Correction Loop.
        New code (new commit) = new retry opportunity, even if error message is identical.

        Args:
            pr_id: Pull request identifier
            failed_check_name: Name of the failed CI check
            error_summary: Error summary text (will be sanitized and hashed)
            ttl: Time-to-live in seconds (default: 24 hours)
            commit_sha: Git commit SHA (required for proper deduplication)

        Returns:
            Tuple of (is_new: bool, signature: str)
            - is_new=True means this is a new failure, proceed with fix
            - is_new=False means this failure was already processed, skip
        """
        if ttl is None:
            ttl = self.DEFAULT_TTL

        # Issue #3806: Sanitize error summary (strip timestamps, take head+tail)
        error_digest = _sanitize_error_for_signature(error_summary)

        signature = self._compute_signature(pr_id, commit_sha, failed_check_name, error_digest)

        r = self._get_redis_client()
        if r is None:
            # Fail-open: if Redis unavailable, treat as new failure
            logger.warning(
                "[CISignatureDeduplication] Redis unavailable, treating as new failure (fail-open)",
                extra={
                    "operation": "ci_signature_dedup_redis_unavailable",
                    "pr_id": pr_id,
                    "signature": signature,
                    "fail_open": True,
                }
            )
            return True, signature

        try:
            key = f"ci_signature:{signature}"

            # Check if signature exists
            existing = r.get(key)
            if existing:
                logger.info(
                    "[CISignatureDeduplication] Duplicate CI failure detected, skipping",
                    extra={
                        "operation": "ci_signature_duplicate_detected",
                        "pr_id": pr_id,
                        "failed_check_name": failed_check_name,
                        "signature": signature,
                        "first_seen": existing,
                    }
                )
                return False, signature

            # Mark as processed
            r.setex(key, ttl, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

            logger.debug(
                "[CISignatureDeduplication] New CI failure signature recorded",
                extra={
                    "operation": "ci_signature_recorded",
                    "pr_id": pr_id,
                    "failed_check_name": failed_check_name,
                    "signature": signature,
                    "ttl": ttl,
                }
            )
            return True, signature

        except redis.ConnectionError as e:
            logger.warning(
                "[CISignatureDeduplication] Redis connection error, treating as new failure: %s",
                str(e),
                extra={"operation": "ci_signature_dedup_redis_error"}
            )
            return True, signature
        except Exception as e:
            logger.warning(
                "[CISignatureDeduplication] Unexpected error, treating as new failure: %s",
                str(e),
                extra={"operation": "ci_signature_dedup_error"}
            )
            return True, signature


@dataclass
class AutoFixSafetyCheckResult:
    """Combined result of all auto-fix safety checks"""
    allowed: bool
    reason: str
    policy_result: Optional[AutoFixPolicyResult] = None
    rate_limit_result: Optional[AutoFixRateLimitResult] = None
    loop_protection_allowed: bool = True
    current_attempts: int = 0


def check_auto_fix_safety(
    triage_result: "CommentTriageResult",
    repo: str,
    pr_id: str,
    actor_name: Optional[str] = None,
    commit_message: Optional[str] = None,
    settings: "Settings" = None,
    redis_url: Optional[str] = None,
) -> AutoFixSafetyCheckResult:
    """
    Perform all auto-fix safety checks in one call.

    This is the main entry point for checking if auto-fix should be allowed.
    It combines policy checks, rate limiting, and loop protection.

    Args:
        triage_result: Result from CommentTriageAgent
        repo: Repository name (e.g., "owner/repo")
        pr_id: Pull request identifier (e.g., "owner/repo#123")
        actor_name: Optional actor name for loop protection
        commit_message: Optional commit message for loop protection
        settings: Application settings. If None, uses global settings.
        redis_url: Redis connection URL. If None, uses settings.redis_url.

    Returns:
        AutoFixSafetyCheckResult with combined results
    """
    if settings is None:
        from common.config.settings import settings as global_settings
        settings = global_settings

    policy = AutoFixPolicy(settings)
    policy_result = policy.check(
        triage_result=triage_result,
        repo=repo,
        pr_id=pr_id,
        actor_name=actor_name,
        commit_message=commit_message,
    )

    if not policy_result.allowed:
        return AutoFixSafetyCheckResult(
            allowed=False,
            reason=policy_result.reason,
            policy_result=policy_result,
        )

    rate_limiter = AutoFixRateLimiter(settings, redis_url)
    rate_limit_result = rate_limiter.check(repo, pr_id)

    if not rate_limit_result.allowed:
        return AutoFixSafetyCheckResult(
            allowed=False,
            reason=f"Rate limit exceeded ({rate_limit_result.exceeded_dimension}): "
                   f"{rate_limit_result.current_count}/{rate_limit_result.limit}",
            policy_result=policy_result,
            rate_limit_result=rate_limit_result,
        )

    loop_protection = AutoFixLoopProtection(settings, redis_url)
    loop_allowed, current_attempts = loop_protection.check_and_increment(pr_id)

    if not loop_allowed:
        return AutoFixSafetyCheckResult(
            allowed=False,
            reason=f"Max retries exceeded: {current_attempts}/{settings.auto_fix_max_retries}",
            policy_result=policy_result,
            rate_limit_result=rate_limit_result,
            loop_protection_allowed=False,
            current_attempts=current_attempts,
        )

    logger.info(
        "[AutoFixSafety] All safety checks passed",
        extra={
            "operation": "auto_fix_safety_check_passed",
            "repo": repo,
            "pr_id": pr_id,
            "category": triage_result.category.value,
            "attempt_number": current_attempts,
        }
    )

    return AutoFixSafetyCheckResult(
        allowed=True,
        reason="All safety checks passed",
        policy_result=policy_result,
        rate_limit_result=rate_limit_result,
        loop_protection_allowed=True,
        current_attempts=current_attempts,
    )
