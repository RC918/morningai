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
