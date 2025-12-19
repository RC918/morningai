import os
import logging
import sys
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

logger = logging.getLogger(__name__)

GITHUB_TOKEN = settings.agent_github_token or settings.github_token
GITHUB_REPO = settings.github_repo or "RC918/morningai"

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

def commit_file(repo, branch, path, content, message):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return
        file = repo.get_contents(path, ref=branch)
        repo.update_file(path, message, content, file.sha, branch=branch)
    except Exception as e:
        if repo is None:
            print("[GitHub] Repository not available")
        else:
            try:
                repo.create_file(path, message, content, branch=branch)
            except Exception as create_error:
                print(f"[GitHub] Failed to commit file: {create_error}")

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
    max_size_bytes: int = DIFF_MAX_SIZE_BYTES
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

    Returns:
        dict with keys:
            - diff: str - The truncated unified diff
            - files: list[dict] - List of changed files with metadata
            - truncated: bool - Whether truncation was applied
            - truncation_info: dict - Details about what was truncated
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
        "error": None
    }

    try:
        if repo is None:
            result["error"] = "Repository not available"
            logger.warning("[GitHub] Repository not available for get_pr_diff")
            return result

        pr = repo.get_pull(pr_number)

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


def post_pr_review(
    repo,
    pr_number: int,
    comments: list,
    summary: str = "MorningAI Review"
) -> dict:
    """
    Post review comments to a GitHub PR as inline review comments.

    EPIC B Phase B-3: GitHub Inline Comment Posting
    Issue #2595: Diff-Aware Review Plumbing

    This function posts review comments to GitHub using the Pull Request Review API.
    It supports both single-line and multi-line comments.

    Args:
        repo: GitHub repository object
        pr_number: Pull request number
        comments: List of ReviewComment dicts with keys:
            - file: File path (required)
            - end_line: End line number (required)
            - start_line: Start line number (optional, for multi-line)
            - message: Comment text (required)
        summary: Review summary text (default: "MorningAI Review")

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

    if not comments:
        logger.info("[GitHub] No comments to post")
        result["success"] = True
        return result

    try:
        if repo is None:
            result["error"] = "Repository not available"
            logger.warning("[GitHub] Repository not available for post_pr_review")
            return result

        pr = repo.get_pull(pr_number)

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

        if not gh_comments:
            logger.info("[GitHub] No valid comments to post after filtering")
            result["success"] = True
            return result

        # Check dry-run mode
        if settings.github_review_posting_dry_run:
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
            return result

        # Post the review
        pr.create_review(
            body=summary,
            event="COMMENT",
            comments=gh_comments
        )

        result["success"] = True
        result["posted_count"] = len(gh_comments)

        logger.info(
            f"[GitHub] Posted review to PR #{pr_number} with {len(gh_comments)} comments",
            extra={
                "operation": "post_pr_review",
                "pr_number": pr_number,
                "comment_count": len(gh_comments),
                "skipped_count": result["skipped_count"],
                "truncated_count": result["truncated_count"]
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

                # Post review with body only (no inline comments)
                pr.create_review(
                    body=fallback_body,
                    event="COMMENT"
                )

                result["success"] = True
                result["posted_count"] = len(gh_comments)
                result["downgraded"] = True

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
