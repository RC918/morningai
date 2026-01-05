#!/usr/bin/env python3
"""
Dev Agent Wrapper - Provides unified interface for Bug Fix Workflow
Phase 1 Week 6: Bug Fix Workflow
"""
import os
import re
import logging
import subprocess
from typing import Optional, Dict, Any

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
    """

    # Default git author identity for automated commits
    # These are used when git user.name/user.email are not configured in the environment
    DEFAULT_GIT_AUTHOR_NAME = "MorningAI Bot"
    DEFAULT_GIT_AUTHOR_EMAIL = "bot@morningai.com"
    # Default remote name for git push operations
    DEFAULT_REMOTE_NAME = "origin"

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
        self, title: str, body: str = ""
    ) -> Dict[str, Any]:
        """
        Commit and push changes to the current branch.

        This is the preferred method name for new code. For interface
        compatibility with CodeGenerationWorkflow, use create_pr() which
        delegates to this method.

        Steps:
        1. Check for uncommitted changes
        2. Stage all modified files
        3. Commit with the provided title/body as commit message
        4. Push to the current branch

        Args:
            title: Commit message subject line
            body: Commit message body (optional)

        Returns:
            Dict with success status, commit_sha, and branch name.
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

            add_result = subprocess.run(
                ['git', 'add', '-A'],
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
            # This prevents "Author identity unknown" errors in CI/CD environments
            # where git user.name and user.email are not configured globally
            commit_cmd = [
                'git',
                '-c', f'user.name={self.DEFAULT_GIT_AUTHOR_NAME}',
                '-c', f'user.email={self.DEFAULT_GIT_AUTHOR_EMAIL}',
                'commit', '-m', title
            ]
            if body:
                commit_cmd.extend(['-m', body])

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
            logger.info(f"[SimpleGitTool] Committed {commit_sha_short}: {title}")

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

            push_result = subprocess.run(
                ['git', 'push', '-u', self.DEFAULT_REMOTE_NAME, 'HEAD'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
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
                'output': f'Committed and pushed {commit_sha_short} to {branch}'
            }

        except Exception as e:
            logger.error(f"[SimpleGitTool] commit_and_push failed: {e}")
            return {'success': False, 'error': str(e)}

    async def create_pr(
        self, title: str, body: str = ""
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

        Returns:
            Dict with success status, commit_sha, and branch name.
            Note: pr_number and pr_url are not returned since we're
            pushing to an existing PR branch, not creating a new PR.
        """
        logger.debug(
            "[SimpleGitTool] create_pr called - delegating to commit_and_push "
            "(create_pr is kept for interface compatibility)"
        )
        return await self.commit_and_push(title, body)


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
    """Simple LLM wrapper for OpenAI.

    Issue #3581: Added timeout configuration to prevent hanging LLM calls.
    The OpenAI v1 SDK uses httpx under the hood, which has a default timeout
    of 600 seconds. This was causing code generation to hang for 10+ minutes
    before the RQ worker was killed.

    Default timeout: 120 seconds (configurable via CODEGEN_LLM_TIMEOUT_SECONDS)
    """

    # Default timeout in seconds for LLM calls
    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(self, api_key: str, timeout: Optional[int] = None):
        """Initialize LLM with API key.

        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds (default: 120s from settings or DEFAULT_TIMEOUT_SECONDS)
        """
        from openai import OpenAI

        # Get timeout from settings, parameter, or default
        self.timeout = timeout or getattr(settings, 'codegen_llm_timeout_seconds', self.DEFAULT_TIMEOUT_SECONDS)

        # Initialize OpenAI client with explicit timeout
        # OpenAI v1 SDK accepts timeout parameter directly
        self.client = OpenAI(api_key=api_key, timeout=self.timeout)
        self.model = "gpt-4"

        logger.info(
            f"[SimpleLLM] Initialized with model={self.model}, timeout={self.timeout}s"
        )

    async def generate(self, prompt: str) -> str:
        """
        Generate response from LLM.

        Issue #3581: Added instrumentation to track LLM call duration and
        diagnose slow code generation (10+ minutes observed in staging).

        Args:
            prompt: Input prompt

        Returns:
            Generated text response
        """
        import time
        start_time = time.monotonic()
        prompt_length = len(prompt)

        logger.info(
            f"[SimpleLLM] Starting LLM call: model={self.model}, "
            f"prompt_length={prompt_length}, timeout={self.timeout}s"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )

            elapsed_ms = (time.monotonic() - start_time) * 1000
            content = response.choices[0].message.content or ""

            # Log success with timing and token usage
            usage_info = ""
            if hasattr(response, 'usage') and response.usage:
                usage_info = (
                    f", prompt_tokens={response.usage.prompt_tokens}, "
                    f"completion_tokens={response.usage.completion_tokens}, "
                    f"total_tokens={response.usage.total_tokens}"
                )

            logger.info(
                f"[SimpleLLM] LLM call completed: elapsed_ms={elapsed_ms:.2f}, "
                f"response_length={len(content)}{usage_info}"
            )

            return content

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            error_type = type(e).__name__

            # Log failure with timing and error classification
            logger.error(
                f"[SimpleLLM] LLM call failed: elapsed_ms={elapsed_ms:.2f}, "
                f"error_type={error_type}, error={e}"
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

        openai_key = openai_api_key or settings.openai_api_key
        self.llm = SimpleLLM(openai_key) if openai_key else None

        if not self.llm:
            logger.warning(
                "OpenAI API key not configured - LLM features disabled"
            )

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
