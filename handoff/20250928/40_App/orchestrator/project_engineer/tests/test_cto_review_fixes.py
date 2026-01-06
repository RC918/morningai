#!/usr/bin/env python3
"""
Tests for CTO Review Fixes (Phase 2 Step B)

Tests the high-priority security fixes:
1. Hash stability (deterministic task IDs)
2. File write sandbox hardening (forbidden patterns)
3. PR creation failure handling
"""
import pytest
import sys
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "handoff" / "20250928" / "40_App" / "orchestrator"))

from project_engineer.agent import ProjectEngineerAgent  # noqa: E402


class TestHashStability:
    """Test hash stability fix (CTO review high priority)"""

    def test_hash_deterministic(self):
        """Test that hash function produces deterministic results"""
        task_id = "test-task-12345"

        # Generate hash twice
        hash1 = int(hashlib.sha256(task_id.encode('utf-8')).hexdigest(), 16) & 0x7FFFFFFF
        hash2 = int(hashlib.sha256(task_id.encode('utf-8')).hexdigest(), 16) & 0x7FFFFFFF

        assert hash1 == hash2, "Hash should be deterministic"
        assert 0 <= hash1 < 2**31, "Hash should be in 31-bit range"

    def test_hash_different_inputs(self):
        """Test that different inputs produce different hashes"""
        task_id1 = "test-task-1"
        task_id2 = "test-task-2"

        hash1 = int(hashlib.sha256(task_id1.encode('utf-8')).hexdigest(), 16) & 0x7FFFFFFF
        hash2 = int(hashlib.sha256(task_id2.encode('utf-8')).hexdigest(), 16) & 0x7FFFFFFF

        assert hash1 != hash2, "Different inputs should produce different hashes"

    @pytest.mark.asyncio
    async def test_agent_uses_deterministic_hash(self):
        """Test that ProjectEngineerAgent uses deterministic hash"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow') as MockWorkflow:
            mock_workflow = MagicMock()
            mock_workflow.execute = AsyncMock(return_value={
                "error": None,
                "pr_number": 1234,
                "pr_url": "https://github.com/test/repo/pull/1234"
            })
            MockWorkflow.return_value = mock_workflow

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Execute code generation twice with same task_id
            task_id = "test-task-stable"

            result1 = await agent._execute_code_generation(
                step_text="Add unit tests",
                task_type="test_generation",
                task_id=task_id,
                trace_id="trace-1"
            )

            result2 = await agent._execute_code_generation(
                step_text="Add unit tests",
                task_type="test_generation",
                task_id=task_id,
                trace_id="trace-2"
            )

            # Both should succeed
            assert result1.status == "success"
            assert result2.status == "success"

            # Verify workflow was called with same task_id both times
            calls = mock_workflow.execute.call_args_list
            assert len(calls) == 2

            task_dict1 = calls[0][0][0]
            task_dict2 = calls[1][0][0]

            assert task_dict1["id"] == task_dict2["id"], "Task ID should be deterministic"


class TestSandboxHardening:
    """Test file write sandbox hardening (CTO review high priority)"""

    def test_forbidden_patterns_blocked(self):
        """Test that forbidden patterns are blocked"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Test forbidden patterns
        forbidden_paths = [
            "migrations/001_create_users.py",
            "handoff/migrations/002_add_column.sql",
            "common/config/settings.py",
            ".env",
            "config/.env",
            "policies.yaml",
            "infra/terraform/main.tf",
            "credentials.json",
        ]

        for path in forbidden_paths:
            is_safe = workflow._is_safe_file_path(path)
            assert not is_safe, f"Path '{path}' should be blocked by forbidden patterns"

    def test_allowed_paths_permitted(self):
        """Test that allowed paths are still permitted"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Test allowed paths
        allowed_paths = [
            "README.md",
            "docs/api.md",
            "tests/test_user.py",
            "handoff/20250928/40_App/orchestrator/tests/test_agent.py",
            "tools/monitoring/view_stats.py",
        ]

        for path in allowed_paths:
            is_safe = workflow._is_safe_file_path(path)
            assert is_safe, f"Path '{path}' should be allowed"

    def test_migrations_directory_blocked(self):
        """Test that migrations directory is completely blocked"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Various migration paths
        migration_paths = [
            "migrations/001_init.sql",
            "migrations/tests/test_migration.py",
            "handoff/migrations/002_add_table.py",
            "backend/migrations/003_alter.sql",
        ]

        for path in migration_paths:
            is_safe = workflow._is_safe_file_path(path)
            assert not is_safe, f"Migration path '{path}' should be blocked"

    def test_settings_file_blocked(self):
        """Test that settings.py is blocked regardless of location"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Various settings.py locations
        settings_paths = [
            "settings.py",
            "common/config/settings.py",
            "backend/settings.py",
            "handoff/20250928/40_App/orchestrator/settings.py",
        ]

        for path in settings_paths:
            is_safe = workflow._is_safe_file_path(path)
            assert not is_safe, f"Settings file '{path}' should be blocked"

    def test_env_files_blocked(self):
        """Test that .env files are blocked"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Various .env locations
        env_paths = [
            ".env",
            "backend/.env",
            "config/.env",
            ".env.local",
        ]

        for path in env_paths:
            is_safe = workflow._is_safe_file_path(path)
            assert not is_safe, f"Env file '{path}' should be blocked"


class TestPRCreationFailureHandling:
    """Test PR creation failure handling (CTO review medium priority)"""

    @pytest.mark.asyncio
    async def test_pr_creation_failure_sets_error(self):
        """Test that PR creation failure sets state error"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"
        mock_dev_agent.git_tool = MagicMock()
        mock_dev_agent.git_tool.create_pr = AsyncMock(side_effect=Exception("GitHub API error"))

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        state = {
            "task_id": 123,
            "task_title": "Test task",
            "task_type": "test_generation",
            "generated_code": "print('test')",
            "code_diff": "diff",
            "test_results": {"summary": "passed"},
            "error": None,
            "security_validated": True,  # Required for create_pr to proceed
        }

        result_state = await workflow.create_pr(state)

        # Error should be set
        assert result_state.get("error") is not None
        assert "PR creation failed" in result_state["error"]
        assert "GitHub API error" in result_state["error"]

    @pytest.mark.asyncio
    async def test_pr_creation_success_no_error(self):
        """Test that successful PR creation doesn't set error"""
        from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow

        mock_dev_agent = MagicMock()
        mock_dev_agent.repo_root = "/home/ubuntu/repos/morningai"
        mock_dev_agent.git_tool = MagicMock()
        mock_dev_agent.git_tool.create_pr = AsyncMock(return_value={
            "success": True,
            "pr_number": 1234,
            "pr_url": "https://github.com/test/repo/pull/1234"
        })

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        state = {
            "task_id": 123,
            "task_title": "Test task",
            "task_type": "test_generation",
            "generated_code": "print('test')",
            "code_diff": "diff",
            "test_results": {"summary": "passed"},
            "error": None,
            "security_validated": True,  # Required for create_pr to proceed
        }

        result_state = await workflow.create_pr(state)

        # Error should not be set
        assert result_state.get("error") is None
        assert result_state.get("pr_number") == 1234
        assert result_state.get("pr_url") == "https://github.com/test/repo/pull/1234"
