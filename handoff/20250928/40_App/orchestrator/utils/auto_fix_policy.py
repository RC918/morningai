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
    if not actor_names:
        return set()
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

            dimensions = [
                ('pr', f"auto_fix:rate:pr:{pr_id}", self.settings.auto_fix_per_pr_per_hour),
                ('repo', f"auto_fix:rate:repo:{repo}", self.settings.auto_fix_per_repo_per_hour),
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

    def check_and_increment(self, pr_id: str) -> Tuple[bool, int]:
        """
        Check if auto-fix attempts for a PR have exceeded the max retry limit.
        If allowed, increments the attempt counter.

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
            key = f"auto_fix:attempts:{pr_id}"
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

            new_count = r.incr(key)
            r.expire(key, 86400 * 7)

            logger.debug(
                "[AutoFixLoopProtection] Attempt recorded",
                extra={
                    "operation": "auto_fix_attempt_recorded",
                    "pr_id": pr_id,
                    "attempt_number": new_count,
                    "max_retries": max_retries,
                }
            )
            return True, new_count

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
            key = f"auto_fix:attempts:{pr_id}"
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
            key = f"auto_fix:attempts:{pr_id}"
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
