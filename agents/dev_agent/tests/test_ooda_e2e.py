#!/usr/bin/env python3
"""
E2E Tests for Dev_Agent OODA Loop
Week 3: Basic OODA functionality
Week 4: Session persistence, decision trace, error handling
"""
import pytest
import os

from agents.dev_agent.dev_agent_ooda import create_dev_agent_ooda

SANDBOX_ENDPOINT = os.getenv('DEV_AGENT_ENDPOINT', 'http://localhost:8080')
TEST_TIMEOUT = 60


class TestDevAgentOODA:
    """Test Dev_Agent OODA cycle"""

    @pytest.fixture
    def ooda_agent(self):
        """Create OODA agent instance without persistence"""
        return create_dev_agent_ooda(SANDBOX_ENDPOINT, enable_persistence=False)

    @pytest.fixture
    def ooda_agent_with_persistence(self):
        """Create OODA agent instance with persistence (Week 4)"""
        return create_dev_agent_ooda(SANDBOX_ENDPOINT, enable_persistence=True)

    @pytest.mark.asyncio
    async def test_ooda_simple_task(self, ooda_agent):
        """Test OODA cycle with simple task"""
        task = "Check git status and list files in workspace"

        result = await ooda_agent.execute_task(task, priority="low", max_iterations=1)

        assert result is not None
        assert 'observations' in result
        assert len(result['observations']) > 0
        assert result['iteration'] >= 1

        print("✓ Simple OODA task completed")
        print(f"  Observations: {len(result['observations'])}")
        print(f"  Iterations: {result['iteration']}")

    @pytest.mark.asyncio
    async def test_ooda_file_operation_task(self, ooda_agent):
        """Test OODA cycle with file operations"""
        task = "Create a test file named 'ooda_test.txt' with content 'OODA cycle test'"

        result = await ooda_agent.execute_task(task, priority="medium", max_iterations=2)

        assert result is not None
        assert 'action_results' in result

        print("✓ File operation OODA task completed")
        print(f"  Actions executed: {len(result.get('action_results', []))}")

    @pytest.mark.asyncio
    async def test_ooda_code_exploration_task(self, ooda_agent):
        """Test OODA cycle with code exploration"""
        task = "Search for Python files and analyze the codebase structure"

        result = await ooda_agent.execute_task(task, priority="medium", max_iterations=1)

        assert result is not None
        assert 'observations' in result
        assert 'orientation' in result

        print("✓ Code exploration OODA task completed")
        print(f"  Observations collected: {len(result['observations'])}")
        print(f"  Orientation: {result.get('orientation', {}).get('complexity', 'N/A')}")

    @pytest.mark.asyncio
    async def test_ooda_decision_trace(self, ooda_agent):
        """Test OODA cycle decision trace (Week 4)"""
        task = "Check git status"

        result = await ooda_agent.execute_task(task, priority="low", max_iterations=1)

        assert result is not None
        assert 'decision_trace' in result
        assert len(result['decision_trace']) > 0

        for trace_entry in result['decision_trace']:
            assert 'phase' in trace_entry
            assert 'timestamp' in trace_entry
            assert trace_entry['phase'] in ['observe', 'orient', 'decide', 'act']

        print("✓ Decision trace OODA task completed")
        print(f"  Decision trace entries: {len(result['decision_trace'])}")

    @pytest.mark.asyncio
    async def test_ooda_max_iterations(self, ooda_agent):
        """Test OODA cycle max iterations limit (Week 4)"""
        task = "Complex task that will hit max iterations"

        result = await ooda_agent.execute_task(task, priority="low", max_iterations=1)

        assert result is not None
        assert result['iteration'] <= 1

        print("✓ Max iterations limit enforced")
        print(f"  Iterations: {result['iteration']}")

    @pytest.mark.asyncio
    async def test_ooda_with_session_persistence(self, ooda_agent_with_persistence):
        """Test OODA cycle with session persistence (Week 4)"""
        if not ooda_agent_with_persistence.session_manager:
            pytest.skip("Session persistence not available (Redis not configured)")

        task = "Test session persistence"

        result = await ooda_agent_with_persistence.execute_task(
            task,
            priority="medium",
            max_iterations=1
        )

        assert result is not None
        assert 'session_id' in result

        if result.get('session_id'):
            session = ooda_agent_with_persistence.session_manager.get_session(result['session_id'])
            assert session is not None
            assert session['task'] == task

            print("✓ Session persistence OODA task completed")
            print(f"  Session ID: {result['session_id']}")
        else:
            print("⚠ Session not created (Redis may not be configured)")


class TestFileSystemPathValidation:
    """Test filesystem path whitelist validation (Week 4)"""

    @pytest.fixture
    def fs_tool(self):
        """Create filesystem tool"""
        from agents.dev_agent.tools.filesystem_tool import FileSystemTool
        return FileSystemTool(SANDBOX_ENDPOINT)

    @pytest.mark.asyncio
    async def test_forbidden_path_rejection(self, fs_tool):
        """Test that forbidden paths are rejected"""
        result = await fs_tool.read_file('/etc/passwd')

        assert result['success'] is False
        assert 'error' in result
        assert 'error_code' in result['error']

        print("✓ Forbidden path correctly rejected")

    @pytest.mark.asyncio
    async def test_whitelisted_path_accepted(self, fs_tool):
        """Test that whitelisted paths are accepted"""
        result = fs_tool._validate_path('/workspace/test.py')

        assert result['success'] is True

        print("✓ Whitelisted path correctly accepted")


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Dev_Agent OODA E2E Tests (Week 3-4)")
    print("=" * 50 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
