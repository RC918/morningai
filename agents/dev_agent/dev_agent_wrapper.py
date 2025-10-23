#!/usr/bin/env python3
"""
Dev Agent Wrapper - Provides unified interface for Bug Fix Workflow
Phase 1 Week 6: Bug Fix Workflow
"""
import os
import sys
import logging
import subprocess
from typing import Optional, Dict, Any

from knowledge_graph.knowledge_graph_manager import (
    KnowledgeGraphManager
)
from knowledge_graph.bug_fix_pattern_learner import (
    BugFixPatternLearner
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(project_root, 'handoff/20250928/40_App/orchestrator'))

from governance import (
    get_cost_tracker, CostBudgetExceeded,
    get_reputation_engine,
    get_permission_checker, PermissionDenied
)

logger = logging.getLogger(__name__)


class HITLApprovalSystem:
    """Stub for Human-in-the-Loop approval system."""
    
    def __init__(self, telegram_bot_token=None, admin_chat_id=None):
        """Initialize HITL approval system (stub)."""
        self.telegram_bot_token = telegram_bot_token
        self.admin_chat_id = admin_chat_id
        logger.warning("Using stub HITLApprovalSystem - real implementation not available")


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

        self.cost_tracker = get_cost_tracker()
        self.reputation_engine = get_reputation_engine()
        self.permission_checker = get_permission_checker()
        self.agent_id = self.reputation_engine.get_or_create_agent('dev_agent')
        
        if self.agent_id:
            score = self.reputation_engine.get_reputation_score(self.agent_id)
            level = self.reputation_engine.get_permission_level(self.agent_id)
            logger.info(f"DevAgent governance initialized: score={score}, level={level}")

        logger.info("DevAgent initialized with all tools")

    def check_budget(self, trace_id: str) -> bool:
        """Check if budget allows operation"""
        if not self.agent_id:
            return True
        
        try:
            self.cost_tracker.enforce_budget(trace_id, period='daily')
            self.cost_tracker.enforce_budget(trace_id, period='hourly')
            return True
        except CostBudgetExceeded as e:
            logger.error(f"Budget exceeded: {e}")
            self.reputation_engine.record_event(
                self.agent_id, 'cost_overrun',
                trace_id=trace_id, reason=str(e)
            )
            return False
    
    def check_permission(self, operation: str) -> bool:
        """Check if agent has permission for operation"""
        if not self.agent_id:
            return True
        
        try:
            self.permission_checker.check_permission(self.agent_id, operation)
            return True
        except PermissionDenied as e:
            logger.error(f"Permission denied: {e}")
            return False
    
    def track_success(self, trace_id: str, tokens_used: int = 1000):
        """Track successful operation"""
        if not self.agent_id:
            return
        
        self.reputation_engine.record_event(
            self.agent_id, 'test_passed',
            trace_id=trace_id, reason='Operation completed successfully'
        )
        
        cost = self.cost_tracker.estimate_cost(tokens_used, model='gpt-4')
        self.cost_tracker.track_usage(
            trace_id, tokens_used, cost,
            model='gpt-4', operation='dev_agent_task'
        )
    
    def track_failure(self, trace_id: str, error: str):
        """Track failed operation"""
        if not self.agent_id:
            return
        
        self.reputation_engine.record_event(
            self.agent_id, 'test_failed',
            trace_id=trace_id, reason=f'Operation failed: {error}'
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        health = {
            'git_tool': True,
            'fs_tool': True,
            'ide_tool': True,
            'test_tool': True,
            'llm': self.llm is not None,
            'hitl': self.hitl_client is not None,
            'governance': self.agent_id is not None
        }

        kg_health = self.knowledge_graph.health_check()
        health['knowledge_graph'] = kg_health.get('success', False)

        health['overall'] = all(health.values())
        
        if self.agent_id:
            health['reputation'] = {
                'agent_id': self.agent_id,
                'score': self.reputation_engine.get_reputation_score(self.agent_id),
                'level': self.reputation_engine.get_permission_level(self.agent_id)
            }

        return health
