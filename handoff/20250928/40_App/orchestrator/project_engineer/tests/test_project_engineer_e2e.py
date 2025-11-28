#!/usr/bin/env python3
"""
E2E tests for ProjectEngineerAgent → CodeGenerationWorkflow integration
Phase 2 Step B-1: E2E Tests

Tests the complete flow from ProjectEngineerAgent through CodeGenerationWorkflow
with safe tasks (documentation_update, test_generation).
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use relative import to avoid syntax error with numeric path component
from project_engineer.agent import ProjectEngineerAgent  # noqa: E402


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")

    # Create basic repo structure
    docs_dir = Path(temp_dir) / "docs"
    docs_dir.mkdir()

    tests_dir = Path(temp_dir) / "tests"
    tests_dir.mkdir()

    src_dir = Path(temp_dir) / "src"
    src_dir.mkdir()

    # Create sample files
    (docs_dir / "README.md").write_text("# Test Project\n\nInitial content.")
    (tests_dir / "test_sample.py").write_text("def test_example():\n    assert True\n")
    (src_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_dev_agent():
    """Create a mock DevAgent for testing"""
    agent = Mock()

    # Mock LLM responses
    agent.llm = Mock()
    agent.llm.generate = AsyncMock(return_value="# Updated Documentation\n\nNew content here.")

    # Mock file system operations
    agent.fs_tool = Mock()
    agent.fs_tool.read_file = Mock(return_value="# Original content")
    agent.fs_tool.write_file = Mock(return_value=True)

    # Mock test runner
    agent.test_tool = Mock()
    agent.test_tool.run_tests = AsyncMock(return_value={
        'success': True,
        'passed': 1,
        'failed': 0
    })

    # Mock PR creation
    agent.github_tool = Mock()
    agent.github_tool.create_pr = AsyncMock(return_value={
        'number': 123,
        'url': 'https://github.com/test/repo/pull/123'
    })

    return agent


class TestProjectEngineerE2EDocumentation:
    """E2E tests for documentation_update safe task"""

    @pytest.mark.asyncio
    async def test_documentation_update_end_to_end_mocked(self, temp_repo, mock_dev_agent):
        """Test complete flow: agent → workflow → result for documentation update"""

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = temp_repo

            # Create agent with code generation enabled
            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock planner to return single step (avoid multi-step decomposition)
            with patch.object(agent.planner, 'generate_plan') as mock_planner:
                mock_planner.return_value = {
                    "plan": ["Update README.md with installation instructions"],
                    "planner_type": "test"
                }

                # Mock classifier to return documentation_update
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    mock_classify_result = Mock()
                    mock_classify_result.value = "documentation_update"
                    mock_classify.return_value = mock_classify_result

                    with patch.object(agent.classifier, 'get_task_metadata') as mock_metadata:
                        mock_metadata.return_value = {"complexity": "low"}

                        # Mock workflow execution to avoid real LangGraph execution
                        with patch.object(agent.workflow, 'execute') as mock_execute:
                            mock_execute.return_value = {
                                "task_id": 1,
                                "task_type": "documentation_update",
                                "error": None,
                                "pr_number": 123,
                                "pr_url": "https://github.com/test/repo/pull/123",
                                "security_validated": True,
                                "target_files": ["docs/README.md"]
                            }

                            # Execute task
                            results = await agent.run_task(
                                description="Update README.md with installation instructions",
                                repo="test/repo"
                            )

                            # Verify results
                            assert len(results) == 1
                            result = results[0]

                            assert result.task_type == "documentation_update"
                            assert result.status == "success"
                            assert result.is_safe is True
                            assert result.pr_number == 123
                            assert result.pr_url == "https://github.com/test/repo/pull/123"
                            assert result.error is None

                            # Verify workflow was called with correct parameters
                            mock_execute.assert_called_once()
                            call_args = mock_execute.call_args[0][0]
                            assert call_args["task_type"] == "documentation_update"
                            assert "README.md" in call_args["description"]
                            assert call_args["task_metadata"] is not None

    @pytest.mark.asyncio
    async def test_documentation_update_respects_safe_task_check(self, temp_repo, mock_dev_agent):
        """Test that only safe tasks trigger code generation"""

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = temp_repo

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock planner to return single step
            with patch.object(agent.planner, 'generate_plan') as mock_planner:
                mock_planner.return_value = {
                    "plan": ["Run database migration"],
                    "planner_type": "test"
                }

                # Mock classifier to return unsafe task type
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    mock_classify_result = Mock()
                    mock_classify_result.value = "database_migration"  # Not in safe whitelist
                    mock_classify.return_value = mock_classify_result

                    with patch.object(agent.classifier, 'get_task_metadata') as mock_metadata:
                        mock_metadata.return_value = {"complexity": "high"}

                        # Mock workflow execution (should NOT be called)
                        with patch.object(agent.workflow, 'execute') as mock_execute:
                            # Execute task
                            results = await agent.run_task(
                                description="Run database migration",
                                repo="test/repo"
                            )

                            # Verify results
                            assert len(results) == 1
                            result = results[0]

                            assert result.task_type == "database_migration"
                            assert result.status == "skipped"
                            assert result.is_safe is False
                            assert "not in safe whitelist" in result.details

                            # Verify workflow was NOT called
                            mock_execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_documentation_update_handles_workflow_error(self, temp_repo, mock_dev_agent):
        """Test error handling when workflow execution fails"""

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = temp_repo

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock planner to return single step
            with patch.object(agent.planner, 'generate_plan') as mock_planner:
                mock_planner.return_value = {
                    "plan": ["Update README.md"],
                    "planner_type": "test"
                }

                # Mock classifier to return documentation_update
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    mock_classify_result = Mock()
                    mock_classify_result.value = "documentation_update"
                    mock_classify.return_value = mock_classify_result

                    with patch.object(agent.classifier, 'get_task_metadata') as mock_metadata:
                        mock_metadata.return_value = {"complexity": "low"}

                        # Mock workflow execution to return error
                        with patch.object(agent.workflow, 'execute') as mock_execute:
                            mock_execute.return_value = {
                                "task_id": 1,
                                "task_type": "documentation_update",
                                "error": "Security validation failed: dangerous pattern detected",
                                "pr_number": None,
                                "pr_url": None,
                                "security_validated": False
                            }

                            # Execute task
                            results = await agent.run_task(
                                description="Update README.md",
                                repo="test/repo"
                            )

                            # Verify error handling
                            assert len(results) == 1
                            result = results[0]

                            assert result.task_type == "documentation_update"
                            assert result.status == "failed"
                            assert result.is_safe is True  # Task type is safe, but execution failed
                            assert result.error is not None
                            assert "Security validation failed" in result.error
                            assert result.pr_number is None


class TestProjectEngineerE2ETestGeneration:
    """E2E tests for test_generation safe task"""

    @pytest.mark.asyncio
    async def test_test_generation_end_to_end_mocked(self, temp_repo, mock_dev_agent):
        """Test complete flow for test generation task"""

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = temp_repo

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock planner to return single step
            with patch.object(agent.planner, 'generate_plan') as mock_planner:
                mock_planner.return_value = {
                    "plan": ["Generate unit tests for src/utils.py"],
                    "planner_type": "test"
                }

                # Mock classifier to return test_generation
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    mock_classify_result = Mock()
                    mock_classify_result.value = "test_generation"
                    mock_classify.return_value = mock_classify_result

                    with patch.object(agent.classifier, 'get_task_metadata') as mock_metadata:
                        mock_metadata.return_value = {"complexity": "low"}

                        # Mock workflow execution
                        with patch.object(agent.workflow, 'execute') as mock_execute:
                            mock_execute.return_value = {
                                "task_id": 2,
                                "task_type": "test_generation",
                                "error": None,
                                "pr_number": 124,
                                "pr_url": "https://github.com/test/repo/pull/124",
                                "security_validated": True,
                                "target_files": ["tests/test_utils.py"],
                                "generated_tests": "def test_add():\n    assert add(1, 2) == 3"
                            }

                            # Execute task
                            results = await agent.run_task(
                                description="Generate unit tests for src/utils.py",
                                repo="test/repo"
                            )

                            # Verify results
                            assert len(results) == 1
                            result = results[0]

                            assert result.task_type == "test_generation"
                            assert result.status == "success"
                            assert result.is_safe is True
                            assert result.pr_number == 124

                            # Verify workflow was called with correct task type
                            mock_execute.assert_called_once()
                            call_args = mock_execute.call_args[0][0]
                            assert call_args["task_type"] == "test_generation"


class TestProjectEngineerE2EFeatureFlag:
    """E2E tests for feature flag integration"""

    @pytest.mark.asyncio
    async def test_feature_flag_disabled_skips_execution(self, temp_repo, mock_dev_agent):
        """Test that code generation is skipped when feature flag is disabled"""

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = temp_repo

            # Create agent with code generation DISABLED
            agent = ProjectEngineerAgent(
                enable_code_generation=False,
                dev_agent=None  # No dev_agent needed when disabled
            )

            # Mock planner to return single step
            with patch.object(agent.planner, 'generate_plan') as mock_planner:
                mock_planner.return_value = {
                    "plan": ["Update README.md"],
                    "planner_type": "test"
                }

                # Mock classifier to return safe task
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    mock_classify_result = Mock()
                    mock_classify_result.value = "documentation_update"
                    mock_classify.return_value = mock_classify_result

                    with patch.object(agent.classifier, 'get_task_metadata') as mock_metadata:
                        mock_metadata.return_value = {"complexity": "low"}

                        # Execute task
                        results = await agent.run_task(
                            description="Update README.md",
                            repo="test/repo"
                        )

                        # Verify execution was skipped
                        assert len(results) == 1
                        result = results[0]

                        assert result.task_type == "documentation_update"
                        assert result.status == "skipped"
                        assert result.is_safe is True
                        assert "Code generation disabled" in result.details
                        assert result.pr_number is None


class TestProjectEngineerE2ETaskMetadata:
    """E2E tests for task metadata flow"""

    @pytest.mark.asyncio
    async def test_task_metadata_passed_to_workflow(self, temp_repo, mock_dev_agent):
        """Test that task metadata from safe_tasks is passed to workflow"""

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = temp_repo

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock planner to return single step
            with patch.object(agent.planner, 'generate_plan') as mock_planner:
                mock_planner.return_value = {
                    "plan": ["Update docs"],
                    "planner_type": "test"
                }

                # Mock classifier
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    mock_classify_result = Mock()
                    mock_classify_result.value = "documentation_update"
                    mock_classify.return_value = mock_classify_result

                    with patch.object(agent.classifier, 'get_task_metadata') as mock_metadata:
                        mock_metadata.return_value = {"complexity": "low"}

                        # Mock get_safe_task_metadata to return specific metadata
                        with patch('project_engineer.safe_tasks.get_safe_task_metadata') as mock_safe_metadata:
                            mock_safe_metadata.return_value = {
                                "risk_level": "low",
                                "max_files": 5,
                                "allowed_extensions": [".md", ".rst", ".txt"]
                            }

                            # Mock workflow execution
                            with patch.object(agent.workflow, 'execute') as mock_execute:
                                mock_execute.return_value = {
                                    "task_id": 3,
                                    "error": None,
                                    "pr_number": 125,
                                    "pr_url": "https://github.com/test/repo/pull/125"
                                }

                                # Execute task
                                await agent.run_task(
                                    description="Update docs",
                                    repo="test/repo"
                                )

                                # Verify metadata was passed to workflow
                                mock_execute.assert_called_once()
                                call_args = mock_execute.call_args[0][0]

                                assert "task_metadata" in call_args
                                metadata = call_args["task_metadata"]
                                assert metadata is not None
                                assert metadata["risk_level"] == "low"
                                assert metadata["max_files"] == 5
                                assert ".md" in metadata["allowed_extensions"]
