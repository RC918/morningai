import os
import logging
import random
import sys
import time
from typing import Optional
from github import Github, GithubException, RateLimitExceededException, UnknownObjectException, BadCredentialsException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions import (
    GitHubException as CustomGitHubException,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
    GitHubPermissionError
)
from utils.retry import retry_with_backoff, API_RETRY_CONFIG
from common.config.settings import settings
from resource_telemetry import log_diff_fetch_bytes

logger = logging.getLogger(__name__)

# Import shared constants to prevent drift between github_api.py and normalizer.py
# Issue: Self-Trigger Loop Prevention
from utils.constants import (
    MORNINGAI_REVIEW_MARKER,
    REVIEW_DEDUP_TTL_SECONDS,
    REVIEWER_VERSION,
)

GITHUB_TOKEN = settings.agent_github_token or settings.github_token
GITHUB_REPO = settings.github_repo or "RC918/morningai"


REVIEW_CLAIM_TTL_SECONDS = 300  # 5 minutes - short TTL for inflight claim


def _check_review_already_posted(
    repo: str,
    pr_number: int,
    head_sha: Optional[str],
) -> tuple[bool, Optional[str]]:
    """
    P2: Artifact Idempotency - Atomic claim to prevent duplicate reviews.

    Issue: Self-Trigger Loop Prevention + Race Condition Fix
    This provides platform-level protection against duplicate reviews using
    atomic SET NX (claim) instead of check-then-act pattern.

    The atomic claim pattern prevents race conditions where multiple workers
    could simultaneously check "not posted" and then all post reviews.

    Flow:
    1. Try to SET key with NX (only if not exists) and short TTL (5 min)
    2. If SET succeeds: we have the claim, proceed to post review
    3. If SET fails: another worker has the claim or review was posted, skip
    4. After successful post: _mark_review_posted() extends TTL to 24h

    Args:
        repo: Repository in owner/repo format
        pr_number: Pull request number
        head_sha: Head commit SHA (if None, skips dedup check)

    Returns:
        Tuple of (already_claimed_or_posted: bool, dedup_key: str | None)
        - already_claimed_or_posted: True if review was already posted or claimed
        - dedup_key: The Redis key used for deduplication (for logging)
    """
    if not head_sha:
        # Can't deduplicate without SHA, allow posting (fail-open)
        # Issue #3260: Add observability for skipped dedup
        logger.warning(
            "[GitHub] Dedup skipped: no valid commit_id (head_sha is None)",
            extra={
                "operation": "review_dedup_skipped_no_commit_id",
                "repo": repo,
                "pr_number": pr_number,
                "reason": "head_sha_none",
                "fail_open": True,
            }
        )
        return False, None

    try:
        import redis
        redis_url = getattr(settings, 'redis_url', None)
        if not redis_url:
            # Redis not configured, allow posting (fail-open)
            logger.warning(
                "[GitHub] Redis URL not configured, skipping dedup check (fail-open)",
                extra={
                    "operation": "review_dedup_no_redis",
                    "repo": repo,
                    "pr_number": pr_number,
                }
            )
            return False, None

        r = redis.Redis.from_url(redis_url, decode_responses=True)

        # Key format: review_posted:{repo}:{pr}:{head_sha}:{reviewer_version}
        # This ensures we only post one review per PR+SHA+version combination
        dedup_key = f"review_posted:{repo}:{pr_number}:{head_sha[:12]}:{REVIEWER_VERSION}"

        # Atomic claim: SET NX EX (only set if not exists, with TTL)
        # This prevents race conditions where multiple workers check simultaneously
        # Value "claiming" indicates inflight, "posted" indicates completed
        claimed = r.set(dedup_key, "claiming", nx=True, ex=REVIEW_CLAIM_TTL_SECONDS)

        if claimed:
            # Successfully claimed - we have exclusive right to post
            logger.info(
                f"[GitHub] Acquired review claim (dedup_key={dedup_key}, ttl={REVIEW_CLAIM_TTL_SECONDS}s)",
                extra={
                    "operation": "review_dedup_claimed",
                    "repo": repo,
                    "pr_number": pr_number,
                    "head_sha": head_sha[:12],
                    "dedup_key": dedup_key,
                }
            )
            return False, dedup_key
        else:
            # Key already exists - either claimed by another worker or already posted
            # Check the value to provide better logging
            existing_value = r.get(dedup_key)
            # Handle edge case: key may have expired between SET NX and GET
            status = {None: "expired", "posted": "posted"}.get(existing_value, "claimed_by_other")
            logger.info(
                f"[GitHub] Review already {status} for this SHA, skipping (dedup_key={dedup_key})",
                extra={
                    "operation": "review_dedup_hit",
                    "repo": repo,
                    "pr_number": pr_number,
                    "head_sha": head_sha[:12],
                    "dedup_key": dedup_key,
                    "existing_status": status,
                }
            )
            return True, dedup_key

    except redis.exceptions.RedisError as e:
        # Redis error, allow posting (graceful degradation / fail-open)
        # Issue #3260: Add observability for Redis dedup failures
        logger.warning(
            f"[GitHub] Dedup skipped: Redis error during dedup check (fail-open): {e}",
            extra={
                "operation": "review_dedup_skipped_redis_error",
                "repo": repo,
                "pr_number": pr_number,
                "error": str(e),
                "error_type": type(e).__name__,
                "reason": "redis_error",
                "fail_open": True,
            }
        )
        return False, None


def _mark_review_posted(dedup_key: Optional[str]) -> None:
    """
    P2: Artifact Idempotency - Mark that a review has been successfully posted.

    Issue: Self-Trigger Loop Prevention + Race Condition Fix
    After successfully posting a review, we update the Redis key from "claiming"
    to "posted" and extend the TTL to 24 hours.

    This completes the atomic claim pattern:
    1. _check_review_already_posted() sets key to "claiming" with 5 min TTL
    2. Review is posted to GitHub
    3. This function updates key to "posted" with 24 hour TTL

    If this function fails (Redis error), the "claiming" key will expire after
    5 minutes, allowing a retry. This is acceptable because the review was
    already posted to GitHub.

    Args:
        dedup_key: The Redis key to set (from _check_review_already_posted)
    """
    if not dedup_key:
        return

    try:
        import redis
        redis_url = getattr(settings, 'redis_url', None)
        if not redis_url:
            return

        r = redis.Redis.from_url(redis_url, decode_responses=True)
        # Update value from "claiming" to "posted" and extend TTL to 24 hours
        r.setex(dedup_key, REVIEW_DEDUP_TTL_SECONDS, "posted")

        logger.info(
            f"[GitHub] Marked review as posted (dedup_key={dedup_key}, ttl={REVIEW_DEDUP_TTL_SECONDS}s)",
            extra={
                "operation": "review_dedup_posted",
                "dedup_key": dedup_key,
                "ttl_seconds": REVIEW_DEDUP_TTL_SECONDS,
            }
        )

    except redis.exceptions.RedisError as e:
        # Redis error, log but don't fail the review
        # The review was already posted to GitHub, so this is not critical
        # The "claiming" key will expire after 5 minutes if not updated
        logger.warning(
            f"[GitHub] Failed to mark review as posted (review was still sent): {e}",
            extra={
                "operation": "review_dedup_posted_write_failed",
                "dedup_key": dedup_key,
                "error": str(e),
            }
        )

@retry_with_backoff(
    max_retries=API_RETRY_CONFIG.max_retries,
    initial_delay=API_RETRY_CONFIG.initial_delay,
    backoff_factor=API_RETRY_CONFIG.backoff_factor,
    exceptions=(RateLimitExceededException, ConnectionError, TimeoutError)
)
def get_repo():
    """
    Get GitHub repository object with retry logic

    Returns:
        Repository object or None if unavailable

    Raises:
        GitHubAuthenticationError: If token is invalid
        GitHubResourceNotFoundError: If repository not found
        GitHubRateLimitError: If rate limit exceeded (after retries)
    """
    try:
        if not GITHUB_TOKEN:
            error_msg = "GITHUB_TOKEN not set in environment"
            logger.error(f"[GitHub] {error_msg}")
            raise GitHubAuthenticationError(error_msg)

        gh = Github(GITHUB_TOKEN)
        repo = gh.get_repo(GITHUB_REPO)
        logger.info(f"[GitHub] Successfully connected to {GITHUB_REPO}")
        return repo

    except BadCredentialsException as e:
        error_msg = f"Invalid GitHub token: {e}"
        logger.error(f"[GitHub] {error_msg}")
        raise GitHubAuthenticationError(error_msg) from e

    except UnknownObjectException as e:
        error_msg = f"Repository {GITHUB_REPO} not found: {e}"
        logger.error(f"[GitHub] {error_msg}")
        raise GitHubResourceNotFoundError(error_msg) from e

    except RateLimitExceededException as e:
        error_msg = f"GitHub API rate limit exceeded: {e}"
        logger.error(f"[GitHub] {error_msg}")
        raise GitHubRateLimitError(error_msg) from e

    except Exception as e:
        error_msg = f"Failed to get repo {GITHUB_REPO}: {e}"
        logger.error(f"[GitHub] {error_msg}")
        raise CustomGitHubException(error_msg) from e

def create_branch(repo, base="main", new_branch="orchestrator/demo-branch"):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return "demo-branch"
        base_ref = repo.get_git_ref(f"heads/{base}")
        try:
            repo.get_git_ref(f"heads/{new_branch}")
            return new_branch
        except:
            repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=base_ref.object.sha)
            return new_branch
    except Exception as e:
        print(f"[GitHub] Failed to create branch: {e}")
        return "demo-branch"

class CommitResult:
    """Result of a commit_file operation with detailed status information."""

    SUCCESS = "success"
    CONFLICT = "conflict"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    TRANSIENT_ERROR = "transient_error"
    UNKNOWN_ERROR = "unknown_error"

    def __init__(self, status: str, message: str = "", sha: str = ""):
        self.status = status
        self.message = message
        self.sha = sha

    @property
    def success(self) -> bool:
        return self.status == self.SUCCESS

    def __repr__(self):
        return f"CommitResult(status={self.status}, message={self.message})"


def _is_transient_error(status_code: int) -> bool:
    """Check if HTTP status code indicates a transient error worth retrying.

    Transient errors (Issue #3230):
    - 408: Request Timeout - server took too long, worth retrying
    - 429: Too Many Requests - rate limited, retry with backoff
    - 5xx: Server errors - temporary server issues
    """
    return status_code >= 500 or status_code == 429 or status_code == 408


def _extract_commit_sha(result) -> str:
    """Safely extract commit SHA from GitHub API response.

    Handles both PyGithub Commit objects (with .sha attribute) and
    dict responses (with ['sha'] key) for robustness.

    Args:
        result: Response from update_file() or create_file()

    Returns:
        str: Commit SHA or empty string if not found
    """
    if not result or not isinstance(result, dict):
        return ""

    commit_obj = result.get("commit")
    if commit_obj is None:
        return ""

    sha = getattr(commit_obj, "sha", None)
    if sha:
        return sha

    if isinstance(commit_obj, dict):
        return commit_obj.get("sha", "")

    return ""


def _is_rate_limit_error(error_msg: str, headers: dict | None) -> bool:
    """Check if a 403 error is actually a rate limit error (Issue #3230).

    GitHub rate limiting can manifest as 403 with specific messages or headers.
    See: https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api

    Args:
        error_msg: Error message from the exception
        headers: Response headers from the exception (can be None)

    Returns:
        bool: True if this is a rate limit error that should be retried
    """
    error_lower = str(error_msg).lower()
    if "rate limit" in error_lower or "secondary rate limit" in error_lower:
        return True
    if headers and headers.get("x-ratelimit-remaining") == "0":
        return True
    return False


def _classify_github_error(e: Exception) -> tuple[str, str]:
    """Classify a GitHub exception into error type and message.

    Status code classification (Issue #3230):
    - 401: Unauthorized - bad credentials, fail fast
    - 403: Permission denied OR rate limit (check message/headers)
    - 404: Not found - resource doesn't exist
    - 408: Request timeout - transient, retry
    - 409: Conflict - SHA mismatch, fail fast
    - 422: Unprocessable entity - validation error, fail fast
    - 429: Too many requests - rate limited, retry
    - 5xx: Server errors - transient, retry

    Returns:
        tuple: (error_type, error_message)
    """
    if isinstance(e, GithubException):
        status = getattr(e, 'status', 0)
        data = getattr(e, 'data', {}) or {}
        headers = getattr(e, 'headers', {}) or {}
        error_msg = data.get('message', str(e)) if isinstance(data, dict) else str(e)

        if status == 409:
            return CommitResult.CONFLICT, f"SHA conflict - file was modified externally: {error_msg}"
        elif status == 401:
            return CommitResult.PERMISSION_DENIED, f"Unauthorized - invalid credentials: {error_msg}"
        elif status == 403:
            if "protected branch" in str(error_msg).lower():
                return CommitResult.PERMISSION_DENIED, f"Branch protection prevents commit: {error_msg}"
            if _is_rate_limit_error(error_msg, headers):
                return CommitResult.TRANSIENT_ERROR, f"Rate limited (HTTP 403): {error_msg}"
            return CommitResult.PERMISSION_DENIED, f"Permission denied: {error_msg}"
        elif status == 404:
            return CommitResult.NOT_FOUND, f"Resource not found: {error_msg}"
        elif status == 422:
            return CommitResult.UNKNOWN_ERROR, f"Validation error (HTTP 422): {error_msg}"
        elif _is_transient_error(status):
            return CommitResult.TRANSIENT_ERROR, f"Transient error (HTTP {status}): {error_msg}"

    return CommitResult.UNKNOWN_ERROR, str(e)


def commit_file(repo, branch, path, content, message, max_retries: int = None) -> CommitResult:
    """Commit a file to a GitHub repository branch.

    This function handles file updates with SHA-based concurrency protection.
    If the file doesn't exist, it creates a new file.

    Error handling:
    - 409 Conflict: File was modified externally (SHA mismatch). Fails fast, no retry.
    - 403 Forbidden: Permission denied or branch protection. Fails fast, no retry.
    - 5xx/429: Transient errors. Retries with exponential backoff + jitter.

    Retry Policy (Issue #3229):
    - Configurable via settings: COMMIT_FILE_MAX_RETRIES, COMMIT_FILE_INITIAL_DELAY,
      COMMIT_FILE_BACKOFF_FACTOR, COMMIT_FILE_MAX_TOTAL_TIME, COMMIT_FILE_JITTER_FACTOR
    - Jitter: Random ±jitter_factor applied to delay to avoid thundering herd
    - Total budget: Retries stop if cumulative time exceeds max_total_time
    - Defaults: max_retries=3, initial_delay=2s, backoff=2x, max_total_time=30s, jitter=0.25

    Protected Branch Behavior (D-1.5):
    - SimpleCoder is designed to only operate on PR branches, not main/protected branches
    - If a commit is attempted on a protected branch, GitHub returns 403 with
      "protected branch" in the error message
    - This function detects protected branch errors via substring matching on the
      GitHub error message (case-insensitive). If GitHub changes their error wording,
      the detection may need to be updated in _classify_github_error()
    - Returns PERMISSION_DENIED status for protected branch errors
    - The caller (SimpleCoder wiring in fixer_node) handles this gracefully by
      falling back to AutoFixer when commit_file returns a non-success status
    - Log event: [COMMIT_FILE_PERMISSION_DENIED] with branch protection context

    Args:
        repo: GitHub repository object
        branch: Target branch name
        path: File path within the repository
        content: New file content
        message: Commit message
        max_retries: Maximum retries for transient errors (default: from settings)

    Returns:
        CommitResult: Object with status, message, and optional SHA
    """
    if repo is None:
        logger.warning("[COMMIT_FILE_SKIP] Repository not available")
        return CommitResult(CommitResult.NOT_FOUND, "Repository not available")

    # Load retry configuration from settings (Issue #3229)
    cfg_max_retries = getattr(settings, 'commit_file_max_retries', 3)
    cfg_initial_delay = getattr(settings, 'commit_file_initial_delay', 2.0)
    cfg_backoff_factor = getattr(settings, 'commit_file_backoff_factor', 2.0)
    cfg_max_total_time = getattr(settings, 'commit_file_max_total_time', 30.0)
    cfg_jitter_factor = getattr(settings, 'commit_file_jitter_factor', 0.25)

    # Allow override via parameter for backward compatibility
    effective_max_retries = max_retries if max_retries is not None else cfg_max_retries

    repo_name = getattr(repo, 'full_name', 'unknown')
    log_context = {
        "repo": repo_name,
        "branch": branch,
        "path": path,
        "max_retries": effective_max_retries,
        "max_total_time": cfg_max_total_time,
    }

    delay = cfg_initial_delay
    last_error = None
    start_time = time.time()
    total_elapsed = 0.0

    for attempt in range(effective_max_retries + 1):
        try:
            try:
                file = repo.get_contents(path, ref=branch)
                result = repo.update_file(path, message, content, file.sha, branch=branch)
                new_sha = _extract_commit_sha(result)
                logger.info(
                    f"[COMMIT_FILE_SUCCESS] Updated {path} on {branch}",
                    extra={**log_context, "sha": new_sha, "attempt": attempt + 1}
                )
                return CommitResult(CommitResult.SUCCESS, f"Updated {path}", new_sha)
            except GithubException as e:
                if getattr(e, 'status', 0) == 404:
                    result = repo.create_file(path, message, content, branch=branch)
                    new_sha = _extract_commit_sha(result)
                    logger.info(
                        f"[COMMIT_FILE_SUCCESS] Created {path} on {branch}",
                        extra={**log_context, "sha": new_sha, "attempt": attempt + 1}
                    )
                    return CommitResult(CommitResult.SUCCESS, f"Created {path}", new_sha)
                raise

        except GithubException as e:
            error_type, error_msg = _classify_github_error(e)
            last_error = e

            if error_type == CommitResult.CONFLICT:
                logger.error(
                    f"[COMMIT_FILE_CONFLICT] SHA conflict for {path} on {branch} - "
                    "file was modified externally. Not retrying.",
                    extra={**log_context, "error": error_msg, "status": 409}
                )
                return CommitResult(CommitResult.CONFLICT, error_msg)

            elif error_type == CommitResult.PERMISSION_DENIED:
                logger.error(
                    f"[COMMIT_FILE_PERMISSION_DENIED] Cannot commit to {path} on {branch}. "
                    "Check branch protection rules and token permissions. Not retrying.",
                    extra={**log_context, "error": error_msg, "status": 403}
                )
                return CommitResult(CommitResult.PERMISSION_DENIED, error_msg)

            elif error_type == CommitResult.TRANSIENT_ERROR:
                if attempt < effective_max_retries:
                    # Apply jitter to delay first (Issue #3229: avoid thundering herd)
                    jitter = delay * cfg_jitter_factor * (2 * random.random() - 1)
                    jittered_delay = max(0.1, delay + jitter)  # Ensure minimum 0.1s delay

                    # Check total time budget before retrying (Issue #3229)
                    # Use jittered_delay (actual sleep time) for accurate budget check
                    total_elapsed = time.time() - start_time
                    if total_elapsed + jittered_delay > cfg_max_total_time:
                        logger.error(
                            f"[COMMIT_FILE_BUDGET_EXCEEDED] Total retry budget exceeded for {path} on {branch}. "
                            f"Elapsed: {total_elapsed:.1f}s, next delay: {jittered_delay:.1f}s, budget: {cfg_max_total_time}s",
                            extra={
                                **log_context,
                                "error": error_msg,
                                "elapsed": total_elapsed,
                                "next_delay": jittered_delay,
                                "budget": cfg_max_total_time,
                                "attempt": attempt + 1,
                            }
                        )
                        return CommitResult(
                            CommitResult.TRANSIENT_ERROR,
                            f"Retry budget exceeded ({total_elapsed:.1f}s/{cfg_max_total_time}s): {error_msg}"
                        )

                    logger.warning(
                        f"[COMMIT_FILE_RETRY] Transient error for {path} on {branch}, "
                        f"attempt {attempt + 1}/{effective_max_retries + 1}, retrying in {jittered_delay:.2f}s",
                        extra={
                            **log_context,
                            "error": error_msg,
                            "attempt": attempt + 1,
                            "delay": jittered_delay,
                            "base_delay": delay,
                            "elapsed": total_elapsed,
                        }
                    )
                    time.sleep(jittered_delay)
                    delay *= cfg_backoff_factor
                    continue
                else:
                    logger.error(
                        f"[COMMIT_FILE_FAILED] Transient error for {path} on {branch} "
                        f"after {effective_max_retries + 1} attempts",
                        extra={**log_context, "error": error_msg, "attempts": effective_max_retries + 1}
                    )
                    return CommitResult(CommitResult.TRANSIENT_ERROR, error_msg)

            else:
                logger.error(
                    f"[COMMIT_FILE_ERROR] Unexpected error committing {path} on {branch}",
                    extra={**log_context, "error": error_msg, "exception_type": type(e).__name__}
                )
                return CommitResult(CommitResult.UNKNOWN_ERROR, error_msg)

        except Exception as e:
            logger.error(
                f"[COMMIT_FILE_ERROR] Unexpected exception committing {path} on {branch}: {e}",
                extra={**log_context, "error": str(e), "exception_type": type(e).__name__}
            )
            return CommitResult(CommitResult.UNKNOWN_ERROR, str(e))

    return CommitResult(CommitResult.UNKNOWN_ERROR, f"Failed after {effective_max_retries + 1} attempts: {last_error}")


def commit_files(
    repo,
    branch: str,
    files: list[dict],
    message: str,
    max_retries: int = None
) -> CommitResult:
    """Commit multiple files atomically to a GitHub repository branch.

    This function uses the GitHub Git Data API to create a single commit
    affecting multiple files. This is atomic - either all files are committed
    or none are (no partial state).

    Issue #2760: D-1b Multi-file GeneralCoder support

    API Flow:
    1. Get current branch ref to find base commit SHA
    2. Get base tree SHA from base commit
    3. Create new tree with all file changes
    4. Create new commit pointing to new tree
    5. Update branch ref to point to new commit

    Args:
        repo: GitHub repository object
        branch: Target branch name
        files: List of file changes, each dict has:
            - path: str - File path within the repository
            - content: str - New file content
        message: Commit message
        max_retries: Maximum retries for transient errors (default: from settings)

    Returns:
        CommitResult: Object with status, message, and optional SHA

    Event Codes (greppable):
        [COMMIT_FILES_SUCCESS] - All files committed successfully
        [COMMIT_FILES_CONFLICT] - SHA conflict during commit
        [COMMIT_FILES_PERMISSION_DENIED] - Permission denied
        [COMMIT_FILES_TRANSIENT_ERROR] - Transient error, retrying
        [COMMIT_FILES_FAILED] - Commit failed after retries
        [COMMIT_FILES_VALIDATION_ERROR] - Invalid input (e.g., >5 files)
    """
    if repo is None:
        logger.warning("[COMMIT_FILES_SKIP] Repository not available")
        return CommitResult(CommitResult.NOT_FOUND, "Repository not available")

    if not files:
        logger.warning("[COMMIT_FILES_VALIDATION_ERROR] No files provided")
        return CommitResult(CommitResult.UNKNOWN_ERROR, "No files provided")

    # D-1b guardrail: max 5 files
    if len(files) > 5:
        logger.warning(
            f"[COMMIT_FILES_VALIDATION_ERROR] Too many files: {len(files)} > 5"
        )
        return CommitResult(
            CommitResult.UNKNOWN_ERROR,
            f"Too many files: {len(files)} > 5 (D-1b limit)"
        )

    # Validate file paths (no path traversal)
    # Use os.path.normpath to handle edge cases like foo/../bar
    for f in files:
        path = f.get("path", "")
        if not path:
            logger.warning(
                "[COMMIT_FILES_VALIDATION_ERROR] Empty path"
            )
            return CommitResult(
                CommitResult.UNKNOWN_ERROR,
                "Invalid file path: empty"
            )
        # Normalize path and check for traversal
        normalized_path = os.path.normpath(path)
        if ".." in normalized_path or normalized_path.startswith("/"):
            logger.warning(
                f"[COMMIT_FILES_VALIDATION_ERROR] Invalid path: {path} (normalized: {normalized_path})"
            )
            return CommitResult(
                CommitResult.UNKNOWN_ERROR,
                f"Invalid file path: {path}"
            )

    # Load retry configuration from settings
    cfg_max_retries = getattr(settings, 'commit_file_max_retries', 3)
    cfg_initial_delay = getattr(settings, 'commit_file_initial_delay', 2.0)
    cfg_backoff_factor = getattr(settings, 'commit_file_backoff_factor', 2.0)
    cfg_max_total_time = getattr(settings, 'commit_file_max_total_time', 30.0)
    cfg_jitter_factor = getattr(settings, 'commit_file_jitter_factor', 0.25)

    effective_max_retries = max_retries if max_retries is not None else cfg_max_retries

    repo_name = getattr(repo, 'full_name', 'unknown')
    file_paths = [f.get("path", "") for f in files]
    log_context = {
        "repo": repo_name,
        "branch": branch,
        "file_count": len(files),
        "file_paths": file_paths,
        "max_retries": effective_max_retries,
    }

    delay = cfg_initial_delay
    last_error = None
    start_time = time.time()

    for attempt in range(effective_max_retries + 1):
        try:
            # Step 1: Get current branch ref
            ref = repo.get_git_ref(f"heads/{branch}")
            base_commit_sha = ref.object.sha

            # Step 2: Get base tree SHA
            base_commit = repo.get_git_commit(base_commit_sha)
            base_tree_sha = base_commit.tree.sha

            # Step 3: Create tree elements for all files
            tree_elements = []
            for f in files:
                tree_elements.append({
                    "path": f["path"],
                    "mode": "100644",  # Regular file
                    "type": "blob",
                    "content": f["content"]
                })

            # Step 4: Create new tree
            new_tree = repo.create_git_tree(tree_elements, base_tree=base_tree_sha)

            # Step 5: Create new commit
            new_commit = repo.create_git_commit(
                message=message,
                tree=new_tree,
                parents=[base_commit]
            )

            # Step 6: Update branch ref
            ref.edit(sha=new_commit.sha)

            logger.info(
                f"[COMMIT_FILES_SUCCESS] Committed {len(files)} files on {branch}",
                extra={
                    **log_context,
                    "sha": new_commit.sha,
                    "attempt": attempt + 1
                }
            )
            return CommitResult(
                CommitResult.SUCCESS,
                f"Committed {len(files)} files",
                new_commit.sha
            )

        except GithubException as e:
            error_type, error_msg = _classify_github_error(e)
            last_error = e

            if error_type == CommitResult.CONFLICT:
                logger.error(
                    f"[COMMIT_FILES_CONFLICT] SHA conflict on {branch}. Not retrying.",
                    extra={**log_context, "error": error_msg}
                )
                return CommitResult(CommitResult.CONFLICT, error_msg)

            elif error_type == CommitResult.PERMISSION_DENIED:
                logger.error(
                    f"[COMMIT_FILES_PERMISSION_DENIED] Cannot commit to {branch}. Not retrying.",
                    extra={**log_context, "error": error_msg}
                )
                return CommitResult(CommitResult.PERMISSION_DENIED, error_msg)

            elif error_type == CommitResult.TRANSIENT_ERROR:
                if attempt < effective_max_retries:
                    jitter = delay * cfg_jitter_factor * (2 * random.random() - 1)
                    jittered_delay = max(0.1, delay + jitter)

                    total_elapsed = time.time() - start_time
                    if total_elapsed + jittered_delay > cfg_max_total_time:
                        logger.error(
                            f"[COMMIT_FILES_BUDGET_EXCEEDED] Retry budget exceeded on {branch}.",
                            extra={
                                **log_context,
                                "error": error_msg,
                                "elapsed": total_elapsed,
                                "budget": cfg_max_total_time,
                            }
                        )
                        return CommitResult(
                            CommitResult.TRANSIENT_ERROR,
                            f"Retry budget exceeded: {error_msg}"
                        )

                    logger.warning(
                        f"[COMMIT_FILES_TRANSIENT_ERROR] Retrying in {jittered_delay:.2f}s",
                        extra={
                            **log_context,
                            "error": error_msg,
                            "attempt": attempt + 1,
                            "delay": jittered_delay,
                        }
                    )
                    time.sleep(jittered_delay)
                    delay *= cfg_backoff_factor
                    continue
                else:
                    logger.error(
                        f"[COMMIT_FILES_FAILED] Failed after {effective_max_retries + 1} attempts",
                        extra={**log_context, "error": error_msg}
                    )
                    return CommitResult(CommitResult.TRANSIENT_ERROR, error_msg)

            else:
                logger.error(
                    f"[COMMIT_FILES_ERROR] Unexpected error on {branch}",
                    extra={**log_context, "error": error_msg}
                )
                return CommitResult(CommitResult.UNKNOWN_ERROR, error_msg)

        except Exception as e:
            logger.error(
                f"[COMMIT_FILES_ERROR] Unexpected exception on {branch}: {e}",
                extra={**log_context, "error": str(e)}
            )
            return CommitResult(CommitResult.UNKNOWN_ERROR, str(e))

    return CommitResult(
        CommitResult.UNKNOWN_ERROR,
        f"Failed after {effective_max_retries + 1} attempts: {last_error}"
    )


def open_pr(repo, branch, title, body="", base="main", draft=False, labels=None):
    """
    Create a pull request

    Args:
        repo: GitHub repository object
        branch: Source branch name
        title: PR title
        body: PR description
        base: Target branch (default: main)
        draft: Create as draft PR (default: False)
        labels: List of label names to add (default: None)

    Returns:
        tuple: (pr_url, pr_number)
    """
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return "demo-pr-url", 0

        pr = repo.create_pull(title=title, body=body, head=branch, base=base, draft=draft)

        if labels:
            try:
                pr.add_to_labels(*labels)
                print(f"[GitHub] Added labels: {labels}")
            except Exception as e:
                print(f"[GitHub] Failed to add labels: {e}")

        return pr.html_url, pr.number
    except Exception as e:
        print(f"[GitHub] Failed to open PR: {e}")
        return "demo-pr-url", 0

def get_pr_checks(repo, pr_number:int):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return "demo", []
        pr = repo.get_pull(pr_number)
        combined = repo.get_commit(pr.head.sha).get_combined_status()
        return combined.state, [s.context + ":" + s.state for s in combined.statuses]
    except Exception as e:
        print(f"[GitHub] Failed to get PR checks: {e}")
        return "demo", []


# Diff truncation configuration (Phase B-2)
DIFF_MAX_FILES = 20
DIFF_MAX_LINES = 1000
DIFF_MAX_SIZE_BYTES = 100 * 1024  # 100KB
DIFF_PRIORITY_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.jsx'}
DIFF_MIN_REMAINING_LINES_FOR_PARTIAL = 10  # Minimum lines to include partial patch

# Phase B-2.5: Ignore list for lockfiles and generated assets (#2702)
# These files waste LLM tokens and provide no review value
DIFF_IGNORE_FILENAMES = {
    # Package manager lockfiles
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    'go.sum',
    'Cargo.lock',
    'Gemfile.lock',
    'poetry.lock',
    'composer.lock',
    'Pipfile.lock',
}

DIFF_IGNORE_EXTENSIONS = {
    # Minified/compiled assets
    '.min.js',
    '.min.css',
    '.map',
    # Binary/generated
    '.pyc',
    '.pyo',
    '.class',
    '.o',
    '.so',
    '.dll',
}

# Root-only ignore patterns: only match when directory is at the root level
# These are typically project-level build outputs, not source directories
DIFF_IGNORE_ROOT_DIRS = {
    'dist',
    'build',
    '.next',
    'out',
}

# Anywhere ignore patterns: match at any depth in the path
# These are always generated/cached content regardless of location
DIFF_IGNORE_ANYWHERE_DIRS = {
    '__pycache__',
    'node_modules',
    'vendor',
    '.tox',
    '.pytest_cache',
    'generated',
    'auto_generated',
}


def _should_ignore_file(filename: str) -> bool:
    """
    Check if a file should be ignored based on Phase B-2.5 ignore list.

    Uses path-segment matching to avoid false positives like src/build/main.py.
    - Root-only patterns (dist, build, .next, out): only match at path root
    - Anywhere patterns (node_modules, __pycache__): match at any depth

    Args:
        filename: File path to check

    Returns:
        True if file should be ignored, False otherwise
    """
    from pathlib import PurePosixPath

    # Normalize path to POSIX format
    normalized = filename.replace('\\', '/')
    # Strip leading ./ but preserve dotfiles like .next
    if normalized.startswith('./'):
        normalized = normalized[2:]
    parts = PurePosixPath(normalized).parts

    if not parts:
        return False

    basename = parts[-1]

    # Check exact filename match (lockfiles)
    if basename in DIFF_IGNORE_FILENAMES:
        return True

    # Check extension match (minified/compiled)
    for ext in DIFF_IGNORE_EXTENSIONS:
        if filename.endswith(ext):
            return True

    # Check root-only directory patterns (first segment only)
    # This avoids false positives like src/build/main.py
    if parts[0] in DIFF_IGNORE_ROOT_DIRS:
        return True

    # Check anywhere directory patterns (any segment)
    # These are always generated content regardless of depth
    for part in parts[:-1]:  # Exclude filename itself
        if part in DIFF_IGNORE_ANYWHERE_DIRS:
            return True

    return False


def get_pr_diff(
    repo,
    pr_number: int,
    max_files: int = DIFF_MAX_FILES,
    max_lines: int = DIFF_MAX_LINES,
    max_size_bytes: int = DIFF_MAX_SIZE_BYTES,
    *,
    trace_id: Optional[str] = None
) -> dict:
    """
    Get PR diff with intelligent truncation strategy.

    EPIC B Phase B-1: PR Diff Retrieval
    Issue #2595: Diff-Aware Review Plumbing

    This function fetches the PR diff from GitHub API and applies
    intelligent truncation to ensure the diff fits within LLM context limits.

    Truncation Strategy (Phase B-2):
    1. File count limit: Only include up to max_files files
    2. Line count limit: Truncate total lines to max_lines
    3. Size limit: Truncate total size to max_size_bytes
    4. Priority ordering: Prioritize important files (.py, .ts, .tsx, .js, .jsx)

    Args:
        repo: GitHub repository object
        pr_number: Pull request number
        max_files: Maximum number of files to include (default: 20)
        max_lines: Maximum total lines in diff (default: 1000)
        max_size_bytes: Maximum total size in bytes (default: 100KB)
        trace_id: Optional trace ID for telemetry correlation (keyword-only)

    Returns:
        dict with keys:
            - diff: str - The truncated unified diff
            - files: list[dict] - List of changed files with metadata
            - truncated: bool - Whether truncation was applied
            - truncation_info: dict - Details about what was truncated
            - head_sha: str | None - PR head commit SHA for line drift protection
            - error: str | None - Error message if fetch failed
    """
    result = {
        "diff": "",
        "files": [],
        "truncated": False,
        "truncation_info": {
            "original_file_count": 0,
            "included_file_count": 0,
            "original_line_count": 0,
            "included_line_count": 0,
            "original_size_bytes": 0,
            "included_size_bytes": 0,
            "truncation_reasons": [],
            # Phase B-2.5: Track ignored files (#2702)
            "ignored_file_count": 0,
            "ignored_filenames": []
        },
        # Phase 2: Capture head_sha for line drift protection
        "head_sha": None,
        "error": None
    }

    try:
        if repo is None:
            result["error"] = "Repository not available"
            logger.warning("[GitHub] Repository not available for get_pr_diff")
            return result

        pr = repo.get_pull(pr_number)

        # Phase 2: Capture head_sha for line drift protection
        # This allows publisher_node to detect if new commits were pushed
        # between reviewer_node and publisher_node execution
        result["head_sha"] = pr.head.sha

        # Get list of changed files
        all_files = list(pr.get_files())
        result["truncation_info"]["original_file_count"] = len(all_files)

        if not all_files:
            logger.info(f"[GitHub] PR #{pr_number} has no changed files")
            return result

        # Phase B-2.5: Filter out lockfiles and generated assets (#2702)
        ignored_files = []
        files = []
        for f in all_files:
            if _should_ignore_file(f.filename):
                ignored_files.append(f.filename)
            else:
                files.append(f)

        # Track ignored files in truncation_info
        result["truncation_info"]["ignored_file_count"] = len(ignored_files)
        # Only store first 5 filenames to avoid bloating the response
        result["truncation_info"]["ignored_filenames"] = ignored_files[:5]

        # Log ignored files at DEBUG level with aggregated summary
        if ignored_files:
            logger.debug(
                f"[GitHub] Skipped {len(ignored_files)} generated/lockfiles: "
                f"{ignored_files[:5]}{'...' if len(ignored_files) > 5 else ''}",
                extra={
                    "operation": "get_pr_diff",
                    "pr_number": pr_number,
                    "ignored_count": len(ignored_files),
                    "ignored_sample": ignored_files[:5]
                }
            )

        if not files:
            # All files were ignored - return empty diff (metadata-only review)
            logger.info(
                f"[GitHub] PR #{pr_number} has only lockfiles/generated assets, "
                f"returning empty diff for metadata-only review",
                extra={
                    "operation": "get_pr_diff",
                    "pr_number": pr_number,
                    "ignored_count": len(ignored_files)
                }
            )
            return result

        # Sort files by priority (important extensions first)
        def file_priority(f):
            ext = '.' + f.filename.split('.')[-1] if '.' in f.filename else ''
            is_priority = ext.lower() in DIFF_PRIORITY_EXTENSIONS
            return (0 if is_priority else 1, f.filename)

        sorted_files = sorted(files, key=file_priority)

        # Pre-calculate original totals for all files (before truncation)
        # This ensures original_* values are always the true totals
        original_total_lines = 0
        original_total_size = 0
        for file in sorted_files:
            patch = file.patch or ""
            original_total_lines += patch.count('\n') + 1 if patch else 0
            original_total_size += len(patch.encode('utf-8'))

        result["truncation_info"]["original_line_count"] = original_total_lines
        result["truncation_info"]["original_size_bytes"] = original_total_size

        # Build diff with truncation
        diff_parts = []
        included_files = []
        total_lines = 0
        total_size = 0

        for file in sorted_files:
            # Check file count limit
            if len(included_files) >= max_files:
                result["truncated"] = True
                if "file_count_exceeded" not in result["truncation_info"]["truncation_reasons"]:
                    result["truncation_info"]["truncation_reasons"].append("file_count_exceeded")
                break

            # Get file patch (diff)
            patch = file.patch or ""
            patch_lines = patch.count('\n') + 1 if patch else 0
            patch_size = len(patch.encode('utf-8'))

            # Check line count limit
            if total_lines + patch_lines > max_lines:
                result["truncated"] = True
                if "line_count_exceeded" not in result["truncation_info"]["truncation_reasons"]:
                    result["truncation_info"]["truncation_reasons"].append("line_count_exceeded")
                # Include partial patch if possible
                remaining_lines = max_lines - total_lines
                if remaining_lines > DIFF_MIN_REMAINING_LINES_FOR_PARTIAL:
                    patch_lines_list = patch.split('\n')
                    patch = '\n'.join(patch_lines_list[:remaining_lines])
                    patch += f"\n... (truncated {len(patch_lines_list) - remaining_lines} more lines)"
                    patch_lines = remaining_lines
                    patch_size = len(patch.encode('utf-8'))
                else:
                    break

            # Check size limit
            if total_size + patch_size > max_size_bytes:
                result["truncated"] = True
                if "size_exceeded" not in result["truncation_info"]["truncation_reasons"]:
                    result["truncation_info"]["truncation_reasons"].append("size_exceeded")
                break

            # Include this file
            file_header = f"--- a/{file.filename}\n+++ b/{file.filename}\n"
            diff_parts.append(file_header + patch)

            included_files.append({
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes
            })

            total_lines += patch_lines
            total_size += patch_size

        # Combine diff parts
        result["diff"] = '\n'.join(diff_parts)
        result["files"] = included_files
        result["truncation_info"]["included_file_count"] = len(included_files)
        result["truncation_info"]["included_line_count"] = total_lines
        result["truncation_info"]["included_size_bytes"] = total_size

        logger.info(
            f"[GitHub] Retrieved diff for PR #{pr_number}",
            extra={
                "operation": "get_pr_diff",
                "pr_number": pr_number,
                "file_count": len(included_files),
                "total_files": len(files),
                "line_count": total_lines,
                "size_bytes": total_size,
                "truncated": result["truncated"]
            }
        )

        # P1 瘦身計畫 (#3197): Log diff fetch bytes for resource profiling
        if trace_id:
            log_diff_fetch_bytes(
                trace_id=trace_id,
                diff_bytes=total_size,
                file_count=len(included_files),
                truncated=result["truncated"],
                pr_number=pr_number
            )

        return result

    except UnknownObjectException as e:
        error_msg = f"PR #{pr_number} not found: {e}"
        logger.error(f"[GitHub] {error_msg}")
        result["error"] = error_msg
        return result

    except RateLimitExceededException as e:
        error_msg = f"GitHub API rate limit exceeded: {e}"
        logger.error(f"[GitHub] {error_msg}")
        result["error"] = error_msg
        return result

    except Exception as e:
        error_msg = f"Failed to get PR diff: {e}"
        logger.error(f"[GitHub] {error_msg}", exc_info=True)
        result["error"] = error_msg
        return result

def close_pr(repo, pr_number: int, comment: str = None):
    """
    Close a pull request

    Args:
        repo: GitHub repository object
        pr_number: PR number to close
        comment: Optional comment to add before closing

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return False

        pr = repo.get_pull(pr_number)

        if comment:
            pr.create_issue_comment(comment)
            print(f"[GitHub] Added comment to PR #{pr_number}")

        pr.edit(state="closed")
        print(f"[GitHub] Closed PR #{pr_number}")

        return True
    except Exception as e:
        print(f"[GitHub] Failed to close PR: {e}")
        return False

def delete_branch(repo, branch: str):
    """
    Delete a branch

    Args:
        repo: GitHub repository object
        branch: Branch name to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return False

        ref = repo.get_git_ref(f"heads/{branch}")
        ref.delete()
        print(f"[GitHub] Deleted branch: {branch}")

        return True
    except Exception as e:
        print(f"[GitHub] Failed to delete branch: {e}")
        return False


def _is_repo_in_internal_whitelist(settings, repo_full_name: str) -> bool:
    """
    Check if a repository is in the internal repos whitelist.

    This is a helper function for fault injection to limit injection
    to internal repos only, preventing interference with other staging flows.

    Args:
        settings: Application settings object
        repo_full_name: Repository in owner/repo format (e.g., 'RC918/morningai')

    Returns:
        True if repo is in the internal whitelist, False otherwise
    """
    if not repo_full_name:
        return False

    whitelist_str = getattr(settings, 'internal_repos_whitelist', '')
    if not whitelist_str:
        return False

    whitelist = {r.strip() for r in whitelist_str.split(',') if r.strip()}
    return repo_full_name in whitelist


def _should_inject_422_fault(settings, repo_full_name: str = None) -> bool:
    """
    Check if 422 fault injection should be triggered.

    Phase B-B: Fault Injection for 422 Fallback Verification

    This is a safety-gated function that only allows fault injection when:
    1. settings.enable_fault_injection is True
    2. settings.is_staging is True (NEVER in production)
    3. repo is in internal_repos_whitelist (prevents interference with other staging flows)
    4. Random check passes based on fault_injection_422_rate

    Args:
        settings: Application settings object
        repo_full_name: Repository in owner/repo format (e.g., 'RC918/morningai')

    Returns:
        True if fault should be injected, False otherwise
    """
    import random

    # Safety gate 1: Must have fault injection enabled
    if not getattr(settings, 'enable_fault_injection', False):
        return False

    # Safety gate 2: Must be in staging environment (NEVER production)
    if not getattr(settings, 'is_staging', False):
        return False

    # Safety gate 3: Must be an internal repo (prevents interference with other staging flows)
    if not _is_repo_in_internal_whitelist(settings, repo_full_name):
        return False

    # Safety gate 4: Check injection rate (default 1.0 = always inject when enabled)
    injection_rate = getattr(settings, 'fault_injection_422_rate', 1.0)
    if random.random() > injection_rate:
        return False

    return True


def post_pr_review(
    repo,
    pr_number: int,
    comments: list,
    summary: str = "MorningAI Review",
    commit_id: str | None = None
) -> dict:
    """
    Post review comments to a GitHub PR as inline review comments.

    EPIC B Phase B-3: GitHub Inline Comment Posting
    Issue #2595: Diff-Aware Review Plumbing

    This function posts review comments to GitHub using the Pull Request Review API.
    It supports both single-line and multi-line comments.

    EPIC B Phase 3 P2: commit_id validation
    When commit_id is provided, the review is pinned to that specific commit.
    This prevents 422 errors caused by race conditions where new commits are
    pushed between diff generation and review posting.

    Args:
        repo: GitHub repository object
        pr_number: Pull request number
        comments: List of ReviewComment dicts with keys:
            - file: File path (required)
            - end_line: End line number (required)
            - start_line: Start line number (optional, for multi-line)
            - message: Comment text (required)
        summary: Review summary text (default: "MorningAI Review")
        commit_id: SHA of the commit to review (optional). When provided,
            the review is pinned to this commit, preventing 422 errors
            from race conditions. Should be the diff_head_sha captured
            when the diff was fetched.

    Returns:
        dict with keys:
            - success: bool - Whether the review was posted
            - posted_count: int - Number of comments posted
            - skipped_count: int - Number of comments skipped (invalid)
            - truncated_count: int - Number of comments truncated (over limit)
            - dry_run: bool - Whether this was a dry-run
            - error: str | None - Error message if failed
    """
    from common.config.settings import settings

    result = {
        "success": False,
        "posted_count": 0,
        "skipped_count": 0,
        "truncated_count": 0,
        "dry_run": False,
        "error": None
    }

    # Check feature flag
    if not settings.enable_github_review_posting:
        logger.info("[GitHub] Review posting disabled by feature flag")
        result["error"] = "Feature disabled"
        return result

    # Issue #3220: Allow posting summary-only reviews (no inline comments)
    # When comments is empty but summary is provided, we still want to post
    # the review body to provide visibility (e.g., Summary Report feature)
    summary_only_mode = not comments

    try:
        if repo is None:
            result["error"] = "Repository not available"
            logger.warning("[GitHub] Repository not available for post_pr_review")
            return result

        pr = repo.get_pull(pr_number)

        # P4: PR State Guard - Only post to open, unmerged PRs (allowlist approach)
        # Issue: Self-Trigger Loop Prevention
        # Reviews on merged PRs can still trigger PR_REVIEWED webhooks,
        # causing unnecessary resource consumption and potential loops.
        #
        # We use an allowlist approach (state must be "open") rather than a blocklist
        # (state != "closed") to be more defensive against unknown/unexpected values.
        # This ensures we only post reviews when we're certain the PR is in a valid state.
        #
        # Note: We use explicit `is True` check for merged to avoid MagicMock truthiness
        # issues in unit tests where pr.merged would be a truthy MagicMock object.
        pr_state = getattr(pr, 'state', None)
        pr_merged = getattr(pr, 'merged', None)
        if pr_state != "open" or pr_merged is True:
            logger.info(
                f"[GitHub] Skipping review for non-open/merged PR #{pr_number} "
                f"(state={pr_state}, merged={pr_merged})",
                extra={
                    "operation": "post_pr_review_skipped",
                    "pr_number": pr_number,
                    "pr_state": pr_state,
                    "pr_merged": pr_merged,
                    "reason": "pr_not_open_or_merged"
                }
            )
            result["success"] = True
            result["skipped_reason"] = "pr_closed_or_merged"
            return result

        # P2: Artifact Idempotency - Check if review already posted for this SHA
        # Issue: Self-Trigger Loop Prevention
        # This provides platform-level protection against duplicate reviews.
        repo_full_name = f"{repo.owner.login}/{repo.name}"
        already_posted, dedup_key = _check_review_already_posted(
            repo=repo_full_name,
            pr_number=pr_number,
            head_sha=commit_id,
        )
        if already_posted:
            result["success"] = True
            result["skipped_reason"] = "review_already_posted"
            result["dedup_key"] = dedup_key
            return result

        # Truncate if over limit
        max_comments = settings.github_review_posting_max_comments
        if len(comments) > max_comments:
            logger.warning(
                f"[GitHub] Too many comments ({len(comments)}), "
                f"truncating to {max_comments}"
            )
            result["truncated_count"] = len(comments) - max_comments
            comments = comments[:max_comments]

        # Build GitHub API payload
        gh_comments = []
        for c in comments:
            # Validate required fields
            file_path = c.get("file")
            end_line = c.get("end_line")
            message = c.get("message")

            if not file_path or not end_line or not message:
                logger.warning(
                    f"[GitHub] Skipping invalid comment: "
                    f"file={file_path}, end_line={end_line}, has_message={bool(message)}"
                )
                result["skipped_count"] += 1
                continue

            # Build comment payload for PyGithub
            item = {
                "path": file_path,
                "body": message,
                "line": int(end_line),
                "side": "RIGHT"
            }

            # Add start_line for multi-line comments
            start_line = c.get("start_line")
            if start_line is not None and int(start_line) < int(end_line):
                item["start_line"] = int(start_line)
                item["start_side"] = "RIGHT"

            gh_comments.append(item)

        # Issue #3220: Allow summary-only reviews (no inline comments)
        # When summary_only_mode is True, we still want to post the review body
        if not gh_comments and not summary_only_mode:
            logger.info("[GitHub] No valid comments to post after filtering")
            result["success"] = True
            return result

        # DIAGNOSTIC: Log final GitHub payload structure for 422 debugging
        # Extract only structural fields (path, line, start_line, side, start_side) - no body content
        # Uses diagnostic_helper for consistent formatting, fallback, and size limits
        from diagnostic_helper import format_diagnostic
        payload_structures = [
            {
                "path": c.get("path"),
                "line": c.get("line"),
                "start_line": c.get("start_line"),
                "side": c.get("side"),
                "start_side": c.get("start_side"),
                "body_length": len(c.get("body", "")) if c.get("body") else 0
            }
            for c in gh_comments
        ]
        payload_diagnostic = {
            "pr_number": pr_number,
            "comment_count": len(gh_comments),
            "commit_id": commit_id[:8] if commit_id else None,
            "payload_structures": payload_structures
        }
        logger.info(
            f"[GitHub] DIAGNOSTIC: Final payload for PR #{pr_number}{format_diagnostic(payload_diagnostic)}",
            extra={"operation": "github_diagnostic"}
        )

        # Check dry-run mode
        if settings.github_review_posting_dry_run:
            if summary_only_mode:
                logger.info(
                    f"[GitHub][DRY-RUN] Would post summary-only review to PR #{pr_number}"
                )
            else:
                logger.info(
                    f"[GitHub][DRY-RUN] Would post review to PR #{pr_number} "
                    f"with {len(gh_comments)} comments"
                )
                for i, c in enumerate(gh_comments):
                    logger.info(
                        f"[GitHub][DRY-RUN] Comment {i + 1}: "
                        f"{c['path']}:{c.get('start_line', c['line'])}-{c['line']}"
                    )
            result["success"] = True
            result["posted_count"] = len(gh_comments)
            result["dry_run"] = True
            result["summary_only"] = summary_only_mode
            return result

        # Phase B-B: Fault injection for 422 fallback verification (Staging only)
        # This allows controlled testing of the fallback mechanism
        # P2: Now limited to internal repos only to prevent interference with other staging flows
        repo_full_name = getattr(repo, 'full_name', None)
        if _should_inject_422_fault(settings, repo_full_name):
            logger.warning(
                "[GitHub][FAULT_INJECTION] Injecting 422 error for fallback testing",
                extra={
                    "operation": "fault_injection_422",
                    "pr_number": pr_number,
                    "comment_count": len(gh_comments),
                    "repo": repo_full_name,
                }
            )
            raise GithubException(
                422,
                {"message": "Validation Failed (FAULT_INJECTION)"},
                None
            )

        # Post the review
        # Phase 3 P2: Pass commit_id to pin review to specific commit
        # This prevents 422 errors from race conditions where new commits
        # are pushed between diff generation and review posting
        commit_obj = None
        commit_pinning_attempted = False
        commit_pinning_success = False
        if commit_id:
            commit_pinning_attempted = True
            try:
                commit_obj = repo.get_commit(commit_id)
                commit_pinning_success = True
                logger.info(
                    f"[GitHub] Using commit_id for review: {commit_id[:8]} "
                    f"(commit_pinning_attempted={commit_pinning_attempted}, "
                    f"commit_pinning_success={commit_pinning_success})",
                    extra={
                        "operation": "post_pr_review",
                        "pr_number": pr_number,
                        "commit_id": commit_id[:8],
                        "commit_pinning_attempted": commit_pinning_attempted,
                        "commit_pinning_success": commit_pinning_success
                    }
                )
            except (GithubException, UnknownObjectException) as commit_error:
                logger.warning(
                    f"[GitHub] Failed to get commit {commit_id[:8]}, "
                    f"proceeding without commit_id: {commit_error} "
                    f"(commit_pinning_attempted={commit_pinning_attempted}, "
                    f"commit_pinning_success={commit_pinning_success})",
                    extra={
                        "operation": "post_pr_review",
                        "pr_number": pr_number,
                        "commit_id": commit_id[:8],
                        "commit_pinning_attempted": commit_pinning_attempted,
                        "commit_pinning_success": commit_pinning_success,
                        "error": str(commit_error)
                    }
                )

        # P1: Add self-review marker to prevent feedback loop
        # Issue: Self-Trigger Loop Prevention
        # The marker is added at the end of the review body so the webhook
        # normalizer can detect and skip PR_REVIEWED events from our own reviews.
        review_body_with_marker = f"{summary}\n\n{MORNINGAI_REVIEW_MARKER}"

        if commit_obj:
            pr.create_review(
                commit=commit_obj,
                body=review_body_with_marker,
                event="COMMENT",
                comments=gh_comments
            )
        else:
            pr.create_review(
                body=review_body_with_marker,
                event="COMMENT",
                comments=gh_comments
            )

        result["success"] = True
        result["posted_count"] = len(gh_comments)
        result["commit_pinning_attempted"] = commit_pinning_attempted
        result["commit_pinning_success"] = commit_pinning_success
        result["summary_only"] = summary_only_mode

        # P2: Mark review as posted for artifact idempotency
        _mark_review_posted(dedup_key)

        # Issue #3220: Log summary-only mode for visibility
        if summary_only_mode:
            logger.info(
                f"[GitHub] Posted summary-only review to PR #{pr_number} "
                f"(commit_pinning_attempted={commit_pinning_attempted}, "
                f"commit_pinning_success={commit_pinning_success})",
                extra={
                    "operation": "post_pr_review",
                    "pr_number": pr_number,
                    "comment_count": 0,
                    "summary_only": True,
                    "commit_id": commit_id[:8] if commit_id else None,
                    "commit_pinning_attempted": commit_pinning_attempted,
                    "commit_pinning_success": commit_pinning_success
                }
            )
        else:
            logger.info(
                f"[GitHub] Posted review to PR #{pr_number} with {len(gh_comments)} comments "
                f"(commit_pinning_attempted={commit_pinning_attempted}, "
                f"commit_pinning_success={commit_pinning_success})",
                extra={
                    "operation": "post_pr_review",
                    "pr_number": pr_number,
                    "comment_count": len(gh_comments),
                    "skipped_count": result["skipped_count"],
                    "truncated_count": result["truncated_count"],
                    "commit_id": commit_id[:8] if commit_id else None,
                    "commit_pinning_attempted": commit_pinning_attempted,
                    "commit_pinning_success": commit_pinning_success
                }
            )

        return result

    except UnknownObjectException as e:
        error_msg = f"PR #{pr_number} not found: {e}"
        logger.error(f"[GitHub] {error_msg}")
        result["error"] = error_msg
        return result

    except GithubException as e:
        # Handle 422/404 errors with fallback to Review Body Appendix
        # EPIC B Phase B-3: Atomic batch failure protection
        # If any comment falls outside diff hunk, GitHub returns 422 and ALL fail
        # Fallback: Convert comments to markdown and append to review body
        if e.status in (422, 404) and gh_comments:
            logger.warning(
                f"[GitHub] Batch review failed (status={e.status}), "
                f"falling back to Review Body Appendix. Error: {e}",
                extra={
                    "operation": "post_pr_review_fallback",
                    "pr_number": pr_number,
                    "original_comment_count": len(gh_comments),
                    "error_status": e.status
                }
            )

            try:
                # Build fallback body with comments as markdown
                fallback_body = summary + "\n\n## Comments (Fallback Mode)\n"
                fallback_body += (
                    "> *GitHub API rejected inline comments due to line drift. "
                    "Showing below:*\n\n"
                )

                for c in gh_comments:
                    line_info = c.get("start_line", c["line"])
                    if c.get("start_line") and c["start_line"] != c["line"]:
                        line_info = f"{c['start_line']}-{c['line']}"
                    fallback_body += f"- **{c['path']}** (Line {line_info}):\n"
                    fallback_body += f"  {c['body']}\n\n"

                # P1: Add self-review marker to fallback body as well
                fallback_body += f"\n{MORNINGAI_REVIEW_MARKER}"

                # Post review with body only (no inline comments)
                pr.create_review(
                    body=fallback_body,
                    event="COMMENT"
                )

                result["success"] = True
                result["posted_count"] = len(gh_comments)
                result["downgraded"] = True

                # P2: Mark review as posted for artifact idempotency (fallback path)
                _mark_review_posted(dedup_key)

                logger.info(
                    f"[GitHub] Posted fallback review to PR #{pr_number} "
                    f"with {len(gh_comments)} comments in body",
                    extra={
                        "operation": "post_pr_review_fallback_success",
                        "pr_number": pr_number,
                        "comment_count": len(gh_comments)
                    }
                )

                return result

            except Exception as fallback_error:
                # Fallback also failed - log and return error
                error_msg = (
                    f"Both inline and fallback review failed. "
                    f"Original: {e}, Fallback: {fallback_error}"
                )
                logger.error(f"[GitHub] {error_msg}")
                result["error"] = error_msg
                return result

        # Other GitHub errors (401, 403, etc.) - don't fallback
        error_msg = f"GitHub API error: {e}"
        logger.error(f"[GitHub] {error_msg}")
        result["error"] = error_msg
        return result

    except Exception as e:
        error_msg = f"Failed to post review: {e}"
        logger.error(f"[GitHub] {error_msg}", exc_info=True)
        result["error"] = error_msg
        return result


def cleanup_stale_orchestrator_branches(max_age_days: int = 7, dry_run: bool = True):
    """
    Clean up stale orchestrator branches that were not properly cleaned up.

    This function addresses the branch accumulation issue where orchestrator/*
    branches are created but not deleted when:
    - CI never completes
    - PR is closed without merge
    - Test mode cleanup fails

    Args:
        max_age_days: Delete branches older than this many days (default: 7)
        dry_run: If True, only log what would be deleted (default: True)

    Returns:
        dict: Summary of cleanup results
    """
    from datetime import datetime, timezone, timedelta

    results = {
        'scanned': 0,
        'deleted': 0,
        'failed': 0,
        'skipped': 0,
        'branches': []
    }

    try:
        repo = get_repo()
        if repo is None:
            print("[GitHub] Repository not available for cleanup")
            return results

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        # Get all branches matching orchestrator/* pattern
        branches = repo.get_branches()

        for branch in branches:
            if not branch.name.startswith('orchestrator/'):
                continue

            results['scanned'] += 1

            # Get the last commit date
            try:
                commit = repo.get_commit(branch.commit.sha)
                commit_date = commit.commit.author.date

                if commit_date < cutoff_date:
                    age_days = (datetime.now(timezone.utc) - commit_date).days
                    results['branches'].append({
                        'name': branch.name,
                        'age_days': age_days,
                        'last_commit': commit_date.isoformat()
                    })

                    if dry_run:
                        print(f"[Cleanup][DRY_RUN] Would delete: {branch.name} (age: {age_days} days)")
                        results['skipped'] += 1
                    else:
                        if delete_branch(repo, branch.name):
                            print(f"[Cleanup] Deleted: {branch.name}")
                            results['deleted'] += 1
                        else:
                            print(f"[Cleanup] Failed to delete: {branch.name}")
                            results['failed'] += 1
                else:
                    results['skipped'] += 1

            except Exception as e:
                print(f"[Cleanup] Error processing branch {branch.name}: {e}")
                results['failed'] += 1

        print(f"[Cleanup] Summary: scanned={results['scanned']}, deleted={results['deleted']}, failed={results['failed']}, skipped={results['skipped']}")

    except Exception as e:
        print(f"[Cleanup] Error during cleanup: {e}")

    return results


def get_ci_test_logs(
    repo,
    pr_number: int,
    head_sha: Optional[str] = None,
    trace_id: str = "unknown"
) -> dict:
    """
    Fetch CI test collection logs from GitHub Actions for a PR.

    Issue #3369: Wire DiscoveryAuditor into Reviewer Agent workflow
    This function fetches the test job logs from the latest workflow run
    for the PR's head commit, enabling DiscoveryAuditor to cross-reference
    PR diff with CI logs to detect silent test failures.

    Args:
        repo: GitHub repository object
        pr_number: Pull request number
        head_sha: Head commit SHA (optional, will fetch from PR if not provided)
        trace_id: Trace ID for logging

    Returns:
        dict with keys:
        - logs: str - The CI test logs content
        - success: bool - Whether logs were successfully fetched
        - error: str - Error message if failed
        - workflow_run_id: int - The workflow run ID (if found)
        - job_name: str - The job name that was fetched
        - ci_status: str - The CI status (success, failure, pending, etc.)
    """
    result = {
        "logs": "",
        "success": False,
        "error": "",
        "workflow_run_id": None,
        "job_name": "",
        "ci_status": "unknown"
    }

    if repo is None:
        result["error"] = "Repository not available"
        logger.warning(
            "[GitHub] get_ci_test_logs: Repository not available",
            extra={"operation": "get_ci_test_logs", "trace_id": trace_id}
        )
        return result

    try:
        # Get PR to find head SHA if not provided
        if not head_sha:
            try:
                pr = repo.get_pull(pr_number)
                head_sha = pr.head.sha
            except Exception as pr_error:
                result["error"] = f"Failed to get PR: {pr_error}"
                logger.warning(
                    f"[GitHub] get_ci_test_logs: Failed to get PR #{pr_number}",
                    extra={
                        "operation": "get_ci_test_logs",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "error": str(pr_error)
                    }
                )
                return result

        # Get workflow runs for the head SHA
        # Look for the test workflow (test-apps.yml)
        # Filter by event='pull_request' to ensure we get PR-triggered workflows
        # (not push-triggered ones that may have different test coverage)
        try:
            workflow_runs = repo.get_workflow_runs(
                head_sha=head_sha,
                event='pull_request'
            )

            # Find the most recent completed test workflow run
            # Single-pass optimization: capture fallback while searching for preferred match
            test_run = None
            fallback_run = None
            for run in workflow_runs:
                if fallback_run is None:
                    fallback_run = run  # Capture the first (most recent) run as fallback

                # Look for test-apps workflow or any workflow with "test" in the name
                workflow_name = run.name.lower() if run.name else ""
                if "test" in workflow_name or "ci" in workflow_name:
                    test_run = run
                    break  # Found preferred test run, stop searching

            if not test_run:
                test_run = fallback_run  # Use fallback if no preferred match found

            if not test_run:
                result["error"] = "No workflow runs found for this commit"
                result["ci_status"] = "pending"
                logger.info(
                    "[GitHub] get_ci_test_logs: No workflow runs found",
                    extra={
                        "operation": "get_ci_test_logs",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "head_sha": head_sha[:12] if head_sha else None
                    }
                )
                return result

            result["workflow_run_id"] = test_run.id
            result["ci_status"] = test_run.conclusion or test_run.status

            # Check if workflow is still running
            if test_run.status != "completed":
                result["error"] = f"Workflow still {test_run.status}"
                result["ci_status"] = test_run.status
                logger.info(
                    f"[GitHub] get_ci_test_logs: Workflow still {test_run.status}",
                    extra={
                        "operation": "get_ci_test_logs",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "workflow_run_id": test_run.id,
                        "workflow_status": test_run.status
                    }
                )
                return result

            # Get jobs from the workflow run
            jobs = test_run.jobs()

            # Single-pass optimization: find best job match with fallbacks
            test_job = None
            generic_test_job = None
            first_job = None

            # Find the test job (look for "Orchestrator Tests" or similar)
            for job in jobs:
                if first_job is None:
                    first_job = job  # Capture first job as ultimate fallback

                job_name_lower = job.name.lower() if job.name else ""
                if "orchestrator" in job_name_lower and "test" in job_name_lower:
                    test_job = job
                    break  # Most specific match found, exit loop
                elif "test" in job_name_lower:
                    generic_test_job = job  # Store generic test job, keep searching

            # Use best available match
            if test_job is None:
                test_job = generic_test_job or first_job

            if not test_job:
                result["error"] = "No jobs found in workflow run"
                logger.warning(
                    "[GitHub] get_ci_test_logs: No jobs found in workflow run",
                    extra={
                        "operation": "get_ci_test_logs",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "workflow_run_id": test_run.id
                    }
                )
                return result

            result["job_name"] = test_job.name

            # Get logs URL and download
            # PyGithub provides logs_url as a property (not a method)
            # The URL points to the GitHub API endpoint for downloading job logs
            import requests

            logs_url = test_job.logs_url
            if logs_url:
                # Download logs using GitHub token
                headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                response = requests.get(logs_url, headers=headers, timeout=30)

                if response.status_code == 200:
                    # Issue #3369: Handle both plaintext and zip responses
                    # GitHub Actions logs_url may return zip files in some cases
                    # Check Content-Type header and signature bytes to detect format
                    content_type = response.headers.get("Content-Type", "")
                    is_zip = False
                    logs_text = None

                    # Check for zip signature (PK\x03\x04) in first 4 bytes
                    if response.content[:4] == b'PK\x03\x04':
                        is_zip = True
                    elif "application/zip" in content_type.lower():
                        is_zip = True

                    if is_zip:
                        # Extract text from zip file
                        try:
                            import zipfile
                            import io
                            zip_buffer = io.BytesIO(response.content)
                            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                                # Concatenate all text files in stable order
                                text_parts = []
                                for name in sorted(zf.namelist()):
                                    try:
                                        content = zf.read(name).decode('utf-8', errors='replace')
                                        text_parts.append(content)
                                    except Exception:
                                        pass  # Skip non-text files
                                logs_text = "\n".join(text_parts)
                            logger.info(
                                "[GitHub] get_ci_test_logs: Extracted logs from zip",
                                extra={
                                    "operation": "get_ci_test_logs",
                                    "trace_id": trace_id,
                                    "pr_number": pr_number,
                                    "format": "zip",
                                    "logs_length": len(logs_text) if logs_text else 0
                                }
                            )
                        except Exception as zip_error:
                            # Fail-open: if zip extraction fails, skip audit
                            result["error"] = f"Failed to extract zip logs: {zip_error}"
                            result["format"] = "zip_extraction_failed"
                            logger.warning(
                                "[GitHub] get_ci_test_logs: Zip extraction failed",
                                extra={
                                    "operation": "get_ci_test_logs",
                                    "trace_id": trace_id,
                                    "pr_number": pr_number,
                                    "error": str(zip_error)
                                }
                            )
                    else:
                        # Plaintext response
                        logs_text = response.text

                    if logs_text:
                        result["logs"] = logs_text
                        result["success"] = True
                        result["format"] = "zip" if is_zip else "plaintext"
                        logger.info(
                            "[GitHub] get_ci_test_logs: Successfully fetched CI logs",
                            extra={
                                "operation": "get_ci_test_logs",
                                "trace_id": trace_id,
                                "pr_number": pr_number,
                                "workflow_run_id": test_run.id,
                                "job_name": test_job.name,
                                "logs_length": len(logs_text),
                                "format": result["format"]
                            }
                        )
                else:
                    result["error"] = f"Failed to download logs: HTTP {response.status_code}"
                    logger.warning(
                        "[GitHub] get_ci_test_logs: Failed to download logs",
                        extra={
                            "operation": "get_ci_test_logs",
                            "trace_id": trace_id,
                            "pr_number": pr_number,
                            "http_status": response.status_code
                        }
                    )
            else:
                result["error"] = "No logs URL available"
                logger.warning(
                    "[GitHub] get_ci_test_logs: No logs URL available",
                    extra={
                        "operation": "get_ci_test_logs",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "job_name": test_job.name
                    }
                )

        except Exception as workflow_error:
            result["error"] = f"Failed to get workflow runs: {workflow_error}"
            logger.warning(
                "[GitHub] get_ci_test_logs: Failed to get workflow runs",
                extra={
                    "operation": "get_ci_test_logs",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "error": str(workflow_error)
                }
            )

    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(
            "[GitHub] get_ci_test_logs: Unexpected error",
            extra={
                "operation": "get_ci_test_logs",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "error": str(e)
            },
            exc_info=True
        )

    return result
