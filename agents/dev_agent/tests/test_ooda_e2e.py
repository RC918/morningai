#!/usr/bin/env python3
"""
E2E Tests for Dev_Agent OODA Loop
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
        """Create OODA agent instance"""
        return create_dev_agent_ooda(SANDBOX_ENDPOINT)

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


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Dev_Agent OODA E2E Tests")
    print("=" * 50 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
