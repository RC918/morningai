#!/usr/bin/env python3
"""
Dev Agent Wrapper - Provides unified interface for Bug Fix Workflow
Phase 1 Week 6: Bug Fix Workflow
"""
import os
import re
import logging
import subprocess
import tempfile
import stat
from typing import Optional, Dict, Any, List

from knowledge_graph.knowledge_graph_manager import (
    KnowledgeGraphManager
)
from knowledge_graph.bug_fix_pattern_learner import (
    BugFixPatternLearner
)
from common.config.settings import settings

logger = logging.getLogger(__name__)


class HITLApprovalSystem:
    """Stub for Human-in-the-Loop approval system."""

    def __init__(self, telegram_bot_token=None, admin_chat_id=None):
        """Initialize HITL approval system (stub)."""
        self.telegram_bot_token = telegram_bot_token
        self.admin_chat_id = admin_chat_id
        logger.warning("Using stub HITLApprovalSystem - real implementation not available")


class SimpleGitTool:
    """Simple Git tool for local operations.

    Issue #3584: Added default git author identity to prevent "Author identity unknown"
    errors in CI/CD environments where git user.name and user.email are not configured.
    The bot identity is used for automated commits from the AutoFixer workflow.

    Issue #3602: Added GITHUB_TOKEN authentication for git push operations.
    Uses GIT_ASKPASS mechanism to securely provide credentials without exposing
    the token in logs, git config, or remote URLs.
    """

    # Default git author identity for automated commits
    # These are used when git user.name/user.email are not configured in the environment
    DEFAULT_GIT_AUTHOR_NAME = "MorningAI Bot"
    DEFAULT_GIT_AUTHOR_EMAIL = "bot@morningai.com"
    # Default remote name for git push operations
    DEFAULT_REMOTE_NAME = "origin"

    # Issue #3540: Input validation constants for commit messages
    # Git commit title should follow conventional commit format (max 72 chars)
    MAX_COMMIT_TITLE_LENGTH = 72
    # Git commit body can be longer but should have a reasonable limit
    MAX_COMMIT_BODY_LENGTH = 4096

    @staticmethod
    def _sanitize_commit_message(
        text: str,
        max_length: int,
        field_name: str,
        allow_newlines: bool = False
    ) -> str:
        """
        Sanitize commit message input for git commit.

        Issue #3540: Add input validation for git commit message in SimpleGitTool

        This sanitizes the input by:
        - Stripping NUL characters and control characters (except newlines if allowed)
        - Truncating to max_length
        - Ensuring valid UTF-8 encoding

        Args:
            text: The input text to sanitize
            max_length: Maximum allowed length
            field_name: Name of the field for logging (e.g., "title", "body")
            allow_newlines: Whether to preserve newline characters (for body)

        Returns:
            Sanitized text string
        """
        if not text:
            return ""

        original_length = len(text)

        # Ensure valid UTF-8 by encoding and decoding with error handling
        try:
            text = text.encode('utf-8', errors='replace').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            logger.warning(
                f"[SimpleGitTool] Invalid encoding in commit {field_name}, "
                "replaced invalid characters"
            )

        # Strip NUL characters (always dangerous for C-based tools like git)
        text = text.replace('\x00', '')

        # Strip control characters (ASCII 0-31) except:
        # - \t (tab, 0x09) - sometimes used in commit messages
        # - \n (newline, 0x0a) - only if allow_newlines is True
        # - \r (carriage return, 0x0d) - convert to \n if allow_newlines
        sanitized_chars = []
        for char in text:
            code = ord(char)
            if code == 0x09:  # Tab - keep
                sanitized_chars.append(char)
            elif code == 0x0a:  # Newline
                if allow_newlines:
                    sanitized_chars.append(char)
                else:
                    sanitized_chars.append(' ')  # Replace with space in title
            elif code == 0x0d:  # Carriage return
                if allow_newlines:
                    sanitized_chars.append('\n')  # Convert to newline
                # else: skip entirely
            elif code < 0x20 or code == 0x7f:  # Other control chars or DEL
                pass  # Skip
            else:
                sanitized_chars.append(char)

        text = ''.join(sanitized_chars)

        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(
                f"[SimpleGitTool] Commit {field_name} truncated from "
                f"{original_length} to {max_length} characters"
            )

        # Strip leading/trailing whitespace
        text = text.strip()

        # Issue #3540: Prevent command argument injection (gemini-code-assist feedback)
        # If the sanitized string starts with a hyphen, it could be interpreted as a
        # git command-line option (e.g., --amend, --author). Prepend a safe character.
        if text.startswith('-'):
            text = '_' + text
            logger.warning(
                f"[SimpleGitTool] Commit {field_name} started with hyphen, "
                "prepended underscore to prevent argument injection"
            )

        return text

    def _get_git_auth_env(self) -> Dict[str, str]:
        """
        Get environment variables for git authentication using GITHUB_TOKEN.

        Issue #3602: Root Cause #27 - git push fails with "could not read Username"
        because GITHUB_TOKEN is not being used for authentication.

        This method creates a temporary askpass script that provides the token
        when git requests credentials. This approach:
        - Does NOT expose the token in remote URLs
        - Does NOT write the token to git config
        - Does NOT expose the token in process arguments
        - Works with HTTPS remotes

        Returns:
            Dict of environment variables to pass to subprocess.run()
        """
        github_token = os.environ.get('GITHUB_TOKEN')

        if not github_token:
            logger.warning(
                "[SimpleGitTool] GITHUB_TOKEN not found in environment. "
                "Git push may fail if authentication is required."
            )
            return {}

        # Log that we have a token (without exposing it)
        logger.info(
            f"[SimpleGitTool] GITHUB_TOKEN found (length={len(github_token)}), "
            "configuring git authentication"
        )

        # Create a temporary askpass script
        # This script will be called by git when it needs credentials
        # Security fix: Read token from environment at runtime to prevent
        # command injection if token contains shell metacharacters
        askpass_script = None
        try:
            askpass_script = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            )
            # The script reads GITHUB_TOKEN from environment at runtime
            # Using printf '%s' instead of echo to:
            # - Avoid shell metacharacter interpretation
            # - Avoid adding extra newline
            # - Avoid echo option parsing issues (-n, -e, etc.)
            # For username, we use 'x-access-token' which is the standard
            # for GitHub token authentication
            askpass_script.write('#!/bin/sh\n')
            askpass_script.write('case "$1" in\n')
            askpass_script.write("  *Username*) printf '%s' 'x-access-token' ;;\n")
            askpass_script.write("  *Password*) printf '%s' \"$GITHUB_TOKEN\" ;;\n")
            askpass_script.write('  *) exit 0 ;;\n')
            askpass_script.write('esac\n')
            askpass_script.close()

            # Make the script executable (owner only for security)
            os.chmod(askpass_script.name, stat.S_IRWXU)

            # Return environment variables for git
            # GITHUB_TOKEN is passed through so the askpass script can read it
            return {
                'GIT_ASKPASS': askpass_script.name,
                'GIT_TERMINAL_PROMPT': '0',  # Disable interactive prompts
                'GITHUB_TOKEN': github_token,  # Pass through for askpass script
            }
        except (IOError, OSError) as e:
            logger.error(f"[SimpleGitTool] Failed to create askpass script: {e}")
            # Clean up on error using existing cleanup method (DRY)
            if askpass_script and hasattr(askpass_script, 'name'):
                self._cleanup_askpass_script({'GIT_ASKPASS': askpass_script.name})
            return {}

    def _cleanup_askpass_script(self, env: Dict[str, str]) -> None:
        """Clean up the temporary askpass script after git operation."""
        askpass_path = env.get('GIT_ASKPASS')
        if askpass_path and os.path.exists(askpass_path):
            try:
                os.unlink(askpass_path)
                logger.debug(f"[SimpleGitTool] Cleaned up askpass script: {askpass_path}")
            except OSError as e:
                logger.warning(f"[SimpleGitTool] Failed to clean up askpass script: {e}")

    async def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create a new Git branch."""
        try:
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def commit(
        self, message: str, files: Optional[list] = None
    ) -> Dict[str, Any]:
        """Commit changes."""
        try:
            cwd = os.getcwd()
            if files:
                add_result = subprocess.run(
                    ['git', 'add'] + files,
                    capture_output=True,
                    text=True,
                    cwd=cwd
                )
                if add_result.returncode != 0:
                    logger.error(f"[SimpleGitTool] git add failed: {add_result.stderr}")
                    return {
                        'success': False,
                        'error': f'git add failed: {add_result.stderr}'
                    }

            # Issue #3584: Use git -c options to set author identity
            commit_cmd = [
                'git',
                '-c', f'user.name={self.DEFAULT_GIT_AUTHOR_NAME}',
                '-c', f'user.email={self.DEFAULT_GIT_AUTHOR_EMAIL}',
                'commit', '-m', message
            ]

            logger.info(
                f"[SimpleGitTool] Committing with author: "
                f"{self.DEFAULT_GIT_AUTHOR_NAME} <{self.DEFAULT_GIT_AUTHOR_EMAIL}>"
            )

            result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                cwd=cwd
            )

            if result.returncode != 0:
                logger.error(f"[SimpleGitTool] git commit failed: {result.stderr}")

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            logger.error(f"[SimpleGitTool] commit failed with exception: {e}")
            return {'success': False, 'error': str(e)}

    async def push(
        self, remote: str = 'origin', branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Push changes to remote."""
        try:
            cmd = ['git', 'push', remote]
            if branch:
                cmd.append(branch)
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=os.getcwd()
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def commit_and_push(
        self, title: str, body: str = "", target_branch: Optional[str] = None,
        target_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Commit and push changes to the current branch.

        This is the preferred method name for new code. For interface
        compatibility with CodeGenerationWorkflow, use create_pr() which
        delegates to this method.

        Steps:
        1. Check for uncommitted changes
        2. Stage files (scoped to target_files if provided, otherwise all)
        3. Commit with the provided title/body as commit message
        4. Push to the current branch

        Args:
            title: Commit message subject line
            body: Commit message body (optional)
            target_branch: Optional target branch name for push (Issue #3606).
                          Used when in detached HEAD state to specify which
                          remote branch to push to. If not provided, uses
                          the current branch name or GITHUB_HEAD_REF env var.
            target_files: Optional list of file paths to stage (Issue #3538).
                         When provided, only these files are staged instead of
                         using 'git add -A'. This prevents accidentally committing
                         unintended files in a dirty working tree.

        Returns:
            Dict with success status, commit_sha, branch name, and staged_files list.
        """
        try:
            cwd = os.getcwd()

            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if not status_result.stdout.strip():
                logger.info("[SimpleGitTool] No changes to commit (no-op)")
                return {
                    'success': True,
                    'commit_pushed': False,
                    'output': 'No changes to commit'
                }

            # Issue #3612: Capture base_sha before commit for multi-commit cherry-pick support
            # This allows us to identify exactly which commits were created by this invocation
            # in case we need to retry with cherry-pick after a non-fast-forward rejection
            base_sha_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            base_sha = base_sha_result.stdout.strip() if base_sha_result.returncode == 0 else None

            # Issue #3538: Scoped git add - only stage target_files if provided
            # This prevents accidentally committing unintended files in a dirty working tree
            if target_files:
                # Validate and filter target_files to only include existing files
                valid_files = []
                # MorningAI Reviewer: Use abspath to prevent directory traversal
                cwd_abs = os.path.abspath(cwd)
                for f in target_files:
                    # Security: Normalize and get absolute path to prevent directory traversal
                    normalized = os.path.normpath(f)
                    abs_path = os.path.abspath(os.path.join(cwd, normalized))

                    # Verify file is within repo root (prevent ../../../etc/passwd attacks)
                    if not abs_path.startswith(cwd_abs + os.sep) and abs_path != cwd_abs:
                        logger.warning(
                            f"[SimpleGitTool] target_file outside repo root, skipping: {f}"
                        )
                        continue

                    # Use relative path for git add
                    rel_path = os.path.relpath(abs_path, cwd)

                    # MorningAI Reviewer: Check both existence and read permission
                    if os.path.exists(abs_path) and os.access(abs_path, os.R_OK):
                        valid_files.append(rel_path)
                    else:
                        logger.warning(
                            f"[SimpleGitTool] target_file does not exist or not readable, "
                            f"skipping: {f}"
                        )

                if not valid_files:
                    logger.warning(
                        "[SimpleGitTool] No valid target_files found, "
                        "falling back to git add -A"
                    )
                    add_cmd = ['git', 'add', '-A']
                else:
                    add_cmd = ['git', 'add', '--'] + valid_files
                    logger.info(
                        f"[SimpleGitTool] Staging {len(valid_files)} target file(s): "
                        f"{valid_files}"
                    )
            else:
                # Fallback to git add -A when target_files is not provided
                logger.warning(
                    "[SimpleGitTool] target_files not provided, using git add -A. "
                    "Consider passing target_files for safer scoped staging."
                )
                add_cmd = ['git', 'add', '-A']

            add_result = subprocess.run(
                add_cmd,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if add_result.returncode != 0:
                logger.error(f"[SimpleGitTool] git add failed: {add_result.stderr}")
                return {
                    'success': False,
                    'error': f'git add failed: {add_result.stderr}'
                }

            # Issue #3538: Capture staged files for audit trail
            staged_files_result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            # MorningAI Reviewer: More robust parsing that handles empty lines
            # and different line endings (CRLF vs LF)
            staged_files = []
            if staged_files_result.returncode == 0 and staged_files_result.stdout.strip():
                staged_files = [
                    line.strip() for line in staged_files_result.stdout.splitlines()
                    if line.strip()
                ]
            logger.info(f"[SimpleGitTool] Staged files for commit: {staged_files}")

            # Issue #3540: Sanitize commit message inputs
            # This prevents issues with NUL characters, control characters, and long strings
            sanitized_title = self._sanitize_commit_message(
                title, self.MAX_COMMIT_TITLE_LENGTH, "title", allow_newlines=False
            )
            sanitized_body = self._sanitize_commit_message(
                body, self.MAX_COMMIT_BODY_LENGTH, "body", allow_newlines=True
            ) if body else ""

            if not sanitized_title:
                logger.error("[SimpleGitTool] Commit title is empty after sanitization")
                return {
                    'success': False,
                    'error': 'Commit title is empty or invalid'
                }

            # Issue #3584: Use git -c options to set author identity
            # This prevents "Author identity unknown" errors in CI/CD environments
            # where git user.name and user.email are not configured globally
            commit_cmd = [
                'git',
                '-c', f'user.name={self.DEFAULT_GIT_AUTHOR_NAME}',
                '-c', f'user.email={self.DEFAULT_GIT_AUTHOR_EMAIL}',
                'commit', '-m', sanitized_title
            ]
            if sanitized_body:
                commit_cmd.extend(['-m', sanitized_body])

            logger.info(
                f"[SimpleGitTool] Committing with author: "
                f"{self.DEFAULT_GIT_AUTHOR_NAME} <{self.DEFAULT_GIT_AUTHOR_EMAIL}>"
            )

            commit_result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if commit_result.returncode != 0:
                logger.error(f"[SimpleGitTool] git commit failed: {commit_result.stderr}")
                return {
                    'success': False,
                    'error': f'git commit failed: {commit_result.stderr}'
                }

            sha_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else "unknown"

            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            commit_sha_short = commit_sha[:8] if len(commit_sha) >= 8 else commit_sha
            logger.info(f"[SimpleGitTool] Committed {commit_sha_short}: {sanitized_title}")

            # Issue #3591: Root Cause #22 - Ensure remote exists before pushing
            # In staging, the workspace may not have 'origin' configured if it was
            # initialized differently (e.g., via init+fetch instead of clone)
            remote_check = subprocess.run(
                ['git', 'remote', 'get-url', self.DEFAULT_REMOTE_NAME],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if remote_check.returncode != 0:
                # Remote doesn't exist - try to get the repo URL from git config
                # or use a fallback based on the current directory structure
                logger.warning(
                    f"[SimpleGitTool] Remote '{self.DEFAULT_REMOTE_NAME}' not found, "
                    "attempting to configure from environment"
                )

                # Issue #3593: Root Cause #22 - Use multiple fallback sources for repo slug
                # Priority: 1) GITHUB_REPOSITORY env var, 2) settings.github_repo
                github_repo = os.environ.get('GITHUB_REPOSITORY')

                if not github_repo:
                    # Fallback to settings.github_repo (always available, defaults to RC918/morningai)
                    # Note: settings is already imported at module level
                    github_repo = settings.github_repo
                    if github_repo:
                        logger.info(
                            f"[SimpleGitTool] Using settings.github_repo as fallback: {github_repo}"
                        )

                if github_repo:
                    # Validate repo slug format (security: only allow safe characters)
                    if not re.match(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', github_repo):
                        logger.error(f"[SimpleGitTool] Invalid repo slug format: {github_repo}")
                        return {
                            'success': False,
                            'error': f'Invalid repo slug format: {github_repo}',
                            'commit_sha': commit_sha,
                            'branch': branch
                        }

                    remote_url = f"https://github.com/{github_repo}.git"
                    add_remote = subprocess.run(
                        ['git', 'remote', 'add', self.DEFAULT_REMOTE_NAME, remote_url],
                        capture_output=True,
                        text=True,
                        cwd=cwd
                    )
                    if add_remote.returncode == 0:
                        logger.info(f"[SimpleGitTool] Added remote '{self.DEFAULT_REMOTE_NAME}': {remote_url}")
                    else:
                        logger.error(f"[SimpleGitTool] Failed to add remote: {add_remote.stderr}")
                        return {
                            'success': False,
                            'error': f'Failed to configure git remote: {add_remote.stderr}',
                            'commit_sha': commit_sha,
                            'branch': branch
                        }
                else:
                    logger.error(
                        f"[SimpleGitTool] Remote '{self.DEFAULT_REMOTE_NAME}' not configured "
                        "and no fallback repo slug available"
                    )
                    return {
                        'success': False,
                        'error': (
                            f"git push failed: Remote '{self.DEFAULT_REMOTE_NAME}' not configured. "
                            "Set GITHUB_REPOSITORY env var or configure settings.github_repo."
                        ),
                        'commit_sha': commit_sha,
                        'branch': branch
                    }
            else:
                logger.debug(
                    f"[SimpleGitTool] Remote '{self.DEFAULT_REMOTE_NAME}' exists: "
                    f"{remote_check.stdout.strip()}"
                )

            # Issue #3602: Root Cause #27 - Use GITHUB_TOKEN for authentication
            # Get authentication environment variables (creates temporary askpass script)
            # Initialize auth_env before the call to prevent NameError in finally block
            # if _get_git_auth_env() raises an exception
            auth_env: Dict[str, str] = {}
            try:
                auth_env = self._get_git_auth_env()

                # Merge auth env with current environment
                push_env = os.environ.copy()
                push_env.update(auth_env)

                # Issue #3604: Root Cause #28 - Use explicit refspec for git push
                # When pushing to a newly added remote, 'git push -u origin HEAD' fails with
                # "The destination you provided is not a full refname" because git doesn't
                # know what branch name to create on the remote.
                # Solution: Use explicit refspec 'HEAD:refs/heads/<branch_name>'
                # This tells git exactly what remote branch to create/update.
                #
                # Issue #3605: Root Cause #29 - Handle detached HEAD properly
                # In detached HEAD state, we must NOT push to 'main' (it's protected).
                # Instead, try to get the branch name from environment variables.
                #
                # Issue #3606: Root Cause #30 - Pass head_branch from webhook context
                # The target_branch parameter allows callers to pass the PR branch name
                # from webhook context (CiFailureContext.head_branch), which is the most
                # reliable source of the branch name in AutoFixer workflows.
                #
                # Priority order for determining push target:
                # 1. target_branch parameter (from webhook context, if valid)
                # 2. Current git branch name (if on a named branch, not 'HEAD')
                # 3. GITHUB_HEAD_REF environment variable (GitHub Actions fallback)
                # 4. Fail gracefully (never push to protected 'main')
                #
                # Refactored per gemini-code-assist review for better readability.
                # Note: 'HEAD' is treated as invalid since it indicates detached HEAD state.
                if target_branch and target_branch != 'HEAD':
                    push_target = target_branch
                    branch_source = "target_branch parameter"
                elif branch and branch != 'HEAD':
                    push_target = branch
                    branch_source = "git branch"
                else:
                    # Detached HEAD case - try to get branch from environment
                    # GITHUB_HEAD_REF is set by GitHub Actions for PR events
                    push_target = os.environ.get('GITHUB_HEAD_REF', '')
                    branch_source = "GITHUB_HEAD_REF"

                # Log detached HEAD detection and validate push_target
                if branch_source == "GITHUB_HEAD_REF":
                    if push_target:
                        logger.info(
                            f"[SimpleGitTool] Detached HEAD detected, using GITHUB_HEAD_REF: "
                            f"{push_target}"
                        )
                    else:
                        # No branch name available - fail gracefully
                        # Do NOT push to 'main' as it's likely protected
                        logger.error(
                            "[SimpleGitTool] Detached HEAD detected and no target branch available. "
                            "Checked: target_branch param, git branch, GITHUB_HEAD_REF env var."
                        )
                        return {
                            'success': False,
                            'error': (
                                'git push failed: Detached HEAD state and no target branch '
                                'available. Please pass target_branch parameter or checkout '
                                'a named branch before committing.'
                            ),
                            'commit_sha': commit_sha,
                            'branch': branch
                        }

                push_cmd = [
                    'git', 'push', '-u', self.DEFAULT_REMOTE_NAME,
                    f'HEAD:refs/heads/{push_target}'
                ]
                logger.info(
                    f"[SimpleGitTool] Pushing to branch '{push_target}' "
                    f"(source: {branch_source})"
                )

                push_result = subprocess.run(
                    push_cmd,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=push_env
                )

                # Issue #3609: Root Cause #31 - Handle non-fast-forward rejection
                # Issue #3612: Root Cause #32 - Use cherry-pick instead of rebase
                #
                # Problem with rebase approach:
                # When the worker's workspace is based on a different commit chain
                # (e.g., an older main branch), 'git rebase origin/<branch>' tries to
                # replay ALL commits between the local base and HEAD, including commits
                # that are already in the remote branch. This causes conflicts.
                #
                # Solution: Cherry-pick only the newly created commit(s) onto the
                # remote branch tip. This avoids replaying unrelated commits.
                #
                # Per code review feedback:
                # - Support multiple commits using base_sha..HEAD range
                # - Add safety check for clean working directory before checkout -B
                # - Update commit_sha after cherry-pick to return actual pushed commit
                #
                # Steps:
                # 1. Fetch the latest remote branch
                # 2. Verify working directory is clean (safety check for -B)
                # 3. Checkout the remote branch tip (creates local branch at that point)
                # 4. Cherry-pick the commit(s) created by this invocation (base_sha..HEAD)
                # 5. Push again
                if push_result.returncode != 0:
                    stderr = push_result.stderr
                    is_non_fast_forward = (
                        'fetch first' in stderr or
                        'non-fast-forward' in stderr or
                        'Updates were rejected' in stderr
                    )

                    if is_non_fast_forward:
                        logger.warning(
                            f"[SimpleGitTool] Push rejected (non-fast-forward), "
                            f"attempting fetch+cherry-pick+retry for branch '{push_target}'"
                        )

                        # Step 1: Fetch the latest remote branch
                        fetch_cmd = [
                            'git', 'fetch', self.DEFAULT_REMOTE_NAME, push_target
                        ]
                        fetch_result = subprocess.run(
                            fetch_cmd,
                            capture_output=True,
                            text=True,
                            cwd=cwd,
                            env=push_env
                        )

                        if fetch_result.returncode != 0:
                            logger.error(
                                f"[SimpleGitTool] Fetch failed during retry: "
                                f"{fetch_result.stderr}"
                            )
                            # Fall through to return the original push error
                        else:
                            logger.info(
                                f"[SimpleGitTool] Fetched latest "
                                f"{self.DEFAULT_REMOTE_NAME}/{push_target}"
                            )

                            # Step 2: Safety check - verify working directory is clean
                            # Per code review: -B force checkout may discard changes
                            # This should always pass since we just committed, but
                            # adds safety if environment is reused or polluted
                            clean_check = subprocess.run(
                                ['git', 'status', '--porcelain'],
                                capture_output=True,
                                text=True,
                                cwd=cwd
                            )
                            if clean_check.stdout.strip():
                                logger.error(
                                    "[SimpleGitTool] Working directory not clean, "
                                    "cannot safely checkout remote branch for retry. "
                                    f"Uncommitted changes: {clean_check.stdout.strip()}"
                                )
                                # Fall through to return the original push error
                            else:
                                # Step 3: Checkout the remote branch tip
                                # Use -B to force create/reset local branch to remote tip
                                # This moves HEAD to the latest remote state
                                # Safety: We verified working directory is clean above
                                checkout_cmd = [
                                    'git', 'checkout', '-B', push_target,
                                    f'{self.DEFAULT_REMOTE_NAME}/{push_target}'
                                ]
                                checkout_result = subprocess.run(
                                    checkout_cmd,
                                    capture_output=True,
                                    text=True,
                                    cwd=cwd,
                                    env=push_env
                                )

                                if checkout_result.returncode != 0:
                                    logger.error(
                                        f"[SimpleGitTool] Checkout failed during retry: "
                                        f"{checkout_result.stderr}"
                                    )
                                    # Fall through to return the original push error
                                else:
                                    logger.info(
                                        f"[SimpleGitTool] Checked out "
                                        f"{self.DEFAULT_REMOTE_NAME}/{push_target}"
                                    )

                                    # Step 4: Cherry-pick the commit(s) we created
                                    # Per code review: support multiple commits using
                                    # base_sha..commit_sha range instead of single SHA
                                    # This handles cases where multiple commits were created
                                    # Issue #3614: Set git identity inline for cherry-pick
                                    # After checkout -B, the committer identity may not be
                                    # available in the new checkout context. Using -c options
                                    # ensures identity is always set regardless of git config.
                                    git_identity_args = [
                                        '-c', f'user.email={self.DEFAULT_GIT_AUTHOR_EMAIL}',
                                        '-c', f'user.name={self.DEFAULT_GIT_AUTHOR_NAME}',
                                    ]

                                    if base_sha and base_sha != commit_sha:
                                        # Use range to get all commits created by this invocation
                                        # Note: base_sha..commit_sha means "commits reachable from
                                        # commit_sha but not from base_sha" - this is correct.
                                        # Do NOT use base_sha^..commit_sha as that would include
                                        # base_sha itself, which we don't want to transplant.
                                        cherry_pick_range = f'{base_sha}..{commit_sha}'
                                        logger.info(
                                            f"[SimpleGitTool] Cherry-picking commits "
                                            f"in range {cherry_pick_range}"
                                        )
                                        cherry_pick_cmd = [
                                            'git', *git_identity_args,
                                            'cherry-pick', cherry_pick_range
                                        ]
                                    else:
                                        # Fallback: single commit if base_sha not available
                                        # or if base_sha == commit_sha (edge case)
                                        if not base_sha:
                                            logger.warning(
                                                "[SimpleGitTool] base_sha not available, "
                                                "multi-commit cherry-pick not supported. "
                                                "Falling back to single commit."
                                            )
                                        elif base_sha == commit_sha:
                                            logger.warning(
                                                "[SimpleGitTool] base_sha == commit_sha, "
                                                "range would be empty. "
                                                "Falling back to single commit."
                                            )
                                        logger.info(
                                            f"[SimpleGitTool] Cherry-picking single commit "
                                            f"{commit_sha[:8]}"
                                        )
                                        cherry_pick_cmd = [
                                            'git', *git_identity_args,
                                            'cherry-pick', commit_sha
                                        ]

                                    cherry_pick_result = subprocess.run(
                                        cherry_pick_cmd,
                                        capture_output=True,
                                        text=True,
                                        cwd=cwd,
                                        env=push_env
                                    )

                                    if cherry_pick_result.returncode != 0:
                                        # Cherry-pick failed (likely conflicts) - abort
                                        logger.error(
                                            f"[SimpleGitTool] Cherry-pick failed during retry: "
                                            f"{cherry_pick_result.stderr}"
                                        )
                                        # Abort the cherry-pick to restore clean state
                                        abort_result = subprocess.run(
                                            ['git', 'cherry-pick', '--abort'],
                                            capture_output=True,
                                            text=True,
                                            cwd=cwd,
                                            env=push_env
                                        )
                                        if abort_result.returncode == 0:
                                            logger.info(
                                                "[SimpleGitTool] Cherry-pick aborted, "
                                                "returning original push error"
                                            )
                                        else:
                                            # Note: "No cherry-pick in progress" is not critical
                                            logger.warning(
                                                f"[SimpleGitTool] 'git cherry-pick --abort' "
                                                f"returned non-zero: {abort_result.stderr.strip()}"
                                            )
                                        # Fall through to return the original push error
                                    else:
                                        # Per code review: update commit_sha to the actual
                                        # pushed commit (cherry-pick creates new SHA)
                                        new_sha_result = subprocess.run(
                                            ['git', 'rev-parse', 'HEAD'],
                                            capture_output=True,
                                            text=True,
                                            cwd=cwd
                                        )
                                        new_commit_sha = (
                                            new_sha_result.stdout.strip()
                                            if new_sha_result.returncode == 0
                                            else commit_sha
                                        )
                                        logger.info(
                                            f"[SimpleGitTool] Cherry-picked onto "
                                            f"{self.DEFAULT_REMOTE_NAME}/{push_target}, "
                                            f"new HEAD: {new_commit_sha[:8]}"
                                        )

                                        # Step 5: Retry push (now from the local branch)
                                        retry_push_cmd = [
                                            'git', 'push', '-u', self.DEFAULT_REMOTE_NAME,
                                            f'{push_target}:refs/heads/{push_target}'
                                        ]
                                        retry_push_result = subprocess.run(
                                            retry_push_cmd,
                                            capture_output=True,
                                            text=True,
                                            cwd=cwd,
                                            env=push_env
                                        )

                                        if retry_push_result.returncode == 0:
                                            logger.info(
                                                "[SimpleGitTool] Retry push succeeded "
                                                "after fetch+cherry-pick"
                                            )
                                            # Update for success path
                                            push_result = retry_push_result
                                            # Update commit_sha to actual pushed commit
                                            commit_sha = new_commit_sha
                                            commit_sha_short = commit_sha[:8]
                                            # Update branch to pushed branch
                                            branch = push_target
                                        else:
                                            logger.error(
                                                f"[SimpleGitTool] Retry push failed: "
                                                f"{retry_push_result.stderr}"
                                            )
                                            # Update push_result with retry error
                                            push_result = retry_push_result

            finally:
                # Always clean up the askpass script
                self._cleanup_askpass_script(auth_env)

            if push_result.returncode != 0:
                logger.error(f"[SimpleGitTool] git push failed: {push_result.stderr}")
                return {
                    'success': False,
                    'error': f'git push failed: {push_result.stderr}',
                    'commit_sha': commit_sha,
                    'branch': branch
                }

            logger.info(f"[SimpleGitTool] Pushed to branch '{branch}'")

            return {
                'success': True,
                'commit_pushed': True,
                'commit_sha': commit_sha,
                'branch': branch,
                'staged_files': staged_files,
                'output': f'Committed and pushed {commit_sha_short} to {branch}'
            }

        except Exception as e:
            logger.error(f"[SimpleGitTool] commit_and_push failed: {e}")
            return {'success': False, 'error': str(e)}

    async def create_pr(
        self, title: str, body: str = "", target_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Commit and push changes to the current branch.

        DEPRECATION NOTE: This method name is kept for interface compatibility
        with CodeGenerationWorkflow. It does NOT create a new GitHub PR.
        For new code, prefer using commit_and_push() directly.

        For AutoFixer scenarios, the PR already exists and this method
        commits and pushes fixes to the existing PR branch.

        Args:
            title: Commit message subject line
            body: Commit message body (optional)
            target_branch: Optional target branch name for push (Issue #3606).
                          Used when in detached HEAD state to specify which
                          remote branch to push to.

        Returns:
            Dict with success status, commit_sha, and branch name.
            Note: pr_number and pr_url are not returned since we're
            pushing to an existing PR branch, not creating a new PR.
        """
        logger.debug(
            "[SimpleGitTool] create_pr called - delegating to commit_and_push "
            "(create_pr is kept for interface compatibility)"
        )
        return await self.commit_and_push(title, body, target_branch=target_branch)


class SimpleFilesystemTool:
    """Simple filesystem tool for local operations."""

    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file contents."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {'success': True, 'content': content}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {'success': True, 'path': file_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def list_files(
        self, directory: str = '.', pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """List files in directory."""
        try:
            if pattern:
                result = subprocess.run(
                    ['find', directory, '-name', pattern],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ['ls', '-la', directory],
                    capture_output=True,
                    text=True
                )
            return {'success': True, 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class SimpleIDETool:
    """Simple IDE tool for local operations."""

    async def search_code(
        self, query: str, directory: str = '.'
    ) -> Dict[str, Any]:
        """Search for code in directory."""
        try:
            result = subprocess.run(
                ['grep', '-rn', query, directory],
                capture_output=True,
                text=True
            )
            return {'success': True, 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_file_tree(self, path: str = '.') -> Dict[str, Any]:
        """Get file tree structure."""
        try:
            result = subprocess.run(
                ['tree', '-L', '3', '-I',
                 'node_modules|__pycache__|.git', path],
                capture_output=True,
                text=True
            )
            return {'success': True, 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class TestTool:
    """Simple test tool for running tests."""

    async def run_tests(self, test_pattern=None):
        """
        Run tests and return results.

        Args:
            test_pattern: Optional list of test patterns to run

        Returns:
            Dict with success, error, and stack_trace
        """
        cmd = ['pytest', '-v', '--tb=short']
        if test_pattern:
            cmd.extend(test_pattern)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300, cwd=os.getcwd()
            )

            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None,
                'stack_trace': (
                    result.stderr if result.returncode != 0 else None
                ),
                'output': result.stdout
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out after 300 seconds',
                'stack_trace': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stack_trace': None
            }


class SimpleLLM:
    """Simple LLM wrapper using unified LLMClient.

    Issue #3581: Added timeout configuration to prevent hanging LLM calls.
    Default timeout: 120 seconds (configurable via CODEGEN_LLM_TIMEOUT_SECONDS)

    EPIC D Fix: Migrated from hardcoded OpenAI to LLMClient abstraction layer.
    This allows SimpleCoder to use the configured LLM provider (e.g., Qwen via
    alicloud) instead of always using OpenAI. The provider is determined by:
    1. LLM_PROVIDER environment variable (e.g., "alicloud", "siliconflow")
    2. ROUTING_ALLOWED_PROVIDERS for governance filtering
    3. Auto-selection based on available API keys (Qwen-first per EPIC #2594)
    """

    # Default timeout in seconds for LLM calls
    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(self, api_key: str = None, timeout: Optional[int] = None):
        """Initialize LLM using unified LLMClient.

        Args:
            api_key: Deprecated - kept for backward compatibility but ignored.
                     LLMClient uses provider-specific API keys from settings.
            timeout: Request timeout in seconds (default: 120s from settings or DEFAULT_TIMEOUT_SECONDS)
        """
        # Import LLMClient from orchestrator's llm module
        # This provides unified access to all LLM providers (OpenAI, Gemini, Qwen, etc.)
        try:
            from llm.client import LLMClient
        except ImportError:
            # Fallback import path for different execution contexts
            from handoff.orchestrator.llm.client import LLMClient

        # Get timeout from settings, parameter, or default
        self.timeout = timeout or getattr(settings, 'codegen_llm_timeout_seconds', self.DEFAULT_TIMEOUT_SECONDS)

        # Initialize unified LLMClient (respects LLM_PROVIDER setting)
        # Provider selection follows EPIC #2594: Qwen-first for cost optimization
        self._client = LLMClient()
        self.model = self._client.model

        logger.info(
            f"[SimpleLLM] Initialized with provider={self._client.provider_name}, "
            f"model={self.model}, timeout={self.timeout}s"
        )

    async def generate(self, prompt: str) -> str:
        """
        Generate response from LLM using unified LLMClient.

        Issue #3581: Added instrumentation to track LLM call duration and
        diagnose slow code generation (10+ minutes observed in staging).

        EPIC D Fix: Now uses LLMClient which respects LLM_PROVIDER setting,
        allowing SimpleCoder to use Qwen or other configured providers.

        Args:
            prompt: Input prompt

        Returns:
            Generated text response
        """
        import time
        start_time = time.monotonic()
        prompt_length = len(prompt)

        logger.info(
            f"[SimpleLLM] Starting LLM call: provider={self._client.provider_name}, "
            f"model={self.model}, prompt_length={prompt_length}, timeout={self.timeout}s"
        )

        try:
            # Use LLMClient's generate method which handles all provider-specific logic
            response = self._client.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )

            elapsed_ms = (time.monotonic() - start_time) * 1000
            content = response.content or ""

            # Log success with timing and token usage
            usage_info = ""
            if response.usage:
                usage_info = (
                    f", prompt_tokens={response.usage.get('prompt_tokens', 'N/A')}, "
                    f"completion_tokens={response.usage.get('completion_tokens', 'N/A')}, "
                    f"total_tokens={response.usage.get('total_tokens', 'N/A')}"
                )

            logger.info(
                f"[SimpleLLM] LLM call completed: provider={self._client.provider_name}, "
                f"elapsed_ms={elapsed_ms:.2f}, response_length={len(content)}{usage_info}"
            )

            return content

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            error_type = type(e).__name__

            # Log failure with timing and error classification
            logger.error(
                f"[SimpleLLM] LLM call failed: provider={self._client.provider_name}, "
                f"elapsed_ms={elapsed_ms:.2f}, error_type={error_type}, error={e}"
            )
            return f"Error: {str(e)}"


class DevAgent:
    """
    Dev Agent with all tools for Bug Fix Workflow.

    Provides unified interface to:
    - Git operations
    - Filesystem operations
    - IDE/LSP features
    - Test execution
    - Knowledge Graph
    - Pattern learning
    - HITL approval
    - LLM generation
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        admin_chat_id: Optional[str] = None
    ):
        """
        Initialize Dev Agent.

        Args:
            supabase_url: Supabase URL (default from env)
            supabase_password: Supabase password (default from env)
            openai_api_key: OpenAI API key (default from env)
            telegram_bot_token: Telegram bot token (default from env)
            admin_chat_id: Telegram admin chat ID (default from env)
        """
        self.git_tool = SimpleGitTool()
        self.fs_tool = SimpleFilesystemTool()
        self.ide_tool = SimpleIDETool()
        self.test_tool = TestTool()

        self.knowledge_graph = KnowledgeGraphManager(
            supabase_url=supabase_url,
            supabase_password=supabase_password,
            openai_api_key=openai_api_key
        )
        self.pattern_learner = BugFixPatternLearner(self.knowledge_graph)

        telegram_token = telegram_bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        admin_id = admin_chat_id or os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        self.hitl_client = HITLApprovalSystem(
            telegram_bot_token=telegram_token,
            admin_chat_id=admin_id
        )

        # SimpleLLM now uses LLMClient which auto-selects provider based on
        # LLM_PROVIDER setting and available API keys (Qwen-first per EPIC #2594)
        # The openai_api_key parameter is kept for backward compatibility but ignored
        try:
            self.llm = SimpleLLM()
        except ValueError as e:
            # LLMClient raises ValueError if no provider is available
            logger.warning(f"LLM features disabled: {e}")
            self.llm = None

        logger.info("DevAgent initialized with all tools")

    def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        health = {
            'git_tool': True,
            'fs_tool': True,
            'ide_tool': True,
            'test_tool': True,
            'llm': self.llm is not None,
            'hitl': self.hitl_client is not None
        }

        kg_health = self.knowledge_graph.health_check()
        health['knowledge_graph'] = kg_health.get('success', False)

        health['overall'] = all(health.values())

        return health
