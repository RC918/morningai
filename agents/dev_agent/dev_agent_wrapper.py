#!/usr/bin/env python3
"""
Dev Agent Wrapper - Provides unified interface for Bug Fix Workflow
Phase 1 Week 6: Bug Fix Workflow
"""
import os
import logging
import subprocess
from typing import Optional, Dict, Any

from agents.dev_agent.knowledge_graph.knowledge_graph_manager import (
    KnowledgeGraphManager
)
from agents.dev_agent.knowledge_graph.bug_fix_pattern_learner import (
    BugFixPatternLearner
)
from hitl_approval_system import HITLApprovalSystem

logger = logging.getLogger(__name__)


class SimpleGitTool:
    """Simple Git tool for local operations."""

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
            if files:
                subprocess.run(['git', 'add'] + files, cwd=os.getcwd())
            result = subprocess.run(
                ['git', 'commit', '-m', message],
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
    """Simple LLM wrapper for OpenAI."""

    def __init__(self, api_key: str):
        """Initialize LLM with API key."""
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"

    async def generate(self, prompt: str) -> str:
        """
        Generate response from LLM.

        Args:
            prompt: Input prompt

        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
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

        openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
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
