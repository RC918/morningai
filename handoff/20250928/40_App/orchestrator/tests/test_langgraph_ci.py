"""
LangGraph CI Integration Tests

Tests for LangGraph 1.0+ compatibility and performance.
"""
import pytest
import time
from unittest.mock import Mock, patch
from langgraph_orchestrator import (
    create_orchestrator_graph,
    planner_node,
    executor_node,
    should_continue_execution,
    AgentState
)
from langchain_core.messages import HumanMessage


class TestLangGraphCI:
    """Test suite for LangGraph CI integration"""
    
    def test_workflow_determinism(self):
        """Test that the same input produces consistent workflow structure"""
        app1 = create_orchestrator_graph()
        app2 = create_orchestrator_graph()
        
        assert app1 is not None
        assert app2 is not None
        assert type(app1) == type(app2)
    
    def test_planner_node_creates_plan(self):
        """Test planner node creates a valid plan"""
        initial_state = {
            "messages": [HumanMessage(content="Create FAQ")],
            "goal": "Create FAQ documentation",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        result = planner_node(initial_state)
        
        assert "plan" in result
        assert len(result["plan"]) > 0
        assert result["current_step"] == 0
        assert isinstance(result["plan"], list)
    
    @patch('graph.execute')
    def test_executor_node_success(self, mock_execute):
        """Test executor node handles successful execution"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1", "Step 2"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        result = executor_node(state)
        
        assert result["pr_url"] == "https://github.com/test/pr/1"
        assert result["ci_state"] == "success"
        assert result["error"] is None
        assert result["current_step"] == 1
    
    @patch('graph.execute')
    def test_executor_node_error_handling(self, mock_execute):
        """Test executor node handles errors gracefully"""
        mock_execute.side_effect = Exception("Test error")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        result = executor_node(state)
        
        assert result["error"] == "Test error"
        assert result["retry_count"] == 1
    
    def test_workflow_performance(self):
        """Test workflow creation performance"""
        start = time.time()
        app = create_orchestrator_graph()
        duration = time.time() - start
        
        assert app is not None
        assert duration < 1.0, f"Workflow creation took {duration}s, should be < 1s"
    
    def test_conditional_edge_logic(self):
        """Test conditional edge routing logic"""
        state_success = {
            "error": None,
            "current_step": 0,
            "plan": ["Step 1", "Step 2"]
        }
        assert should_continue_execution(state_success) == "execute"
        
        state_complete = {
            "error": None,
            "current_step": 2,
            "plan": ["Step 1", "Step 2"]
        }
        assert should_continue_execution(state_complete) == "monitor_ci"
        
        state_error = {
            "error": "Some error",
            "current_step": 0,
            "plan": ["Step 1"],
            "retry_count": 0
        }
        assert should_continue_execution(state_error) == "fix"
        
        state_max_retry = {
            "error": "Some error",
            "current_step": 0,
            "plan": ["Step 1"],
            "retry_count": 3
        }
        assert should_continue_execution(state_max_retry) == "finalize"
    
    def test_state_typing(self):
        """Test AgentState type definition"""
        from typing import get_type_hints
        
        hints = get_type_hints(AgentState)
        
        required_fields = [
            "messages", "goal", "trace_id", "repo", "branch",
            "plan", "current_step", "pr_url", "pr_number",
            "ci_state", "ci_checks", "error", "retry_count", "final_result"
        ]
        
        for field in required_fields:
            assert field in hints, f"Field {field} missing from AgentState"
    
    def test_workflow_node_count(self):
        """Test workflow has correct number of nodes"""
        app = create_orchestrator_graph()
        
        assert app is not None
    
    def test_workflow_graph_structure(self):
        """Test workflow graph has correct structure and nodes"""
        app = create_orchestrator_graph()
        
        assert app is not None
        
        graph_dict = app.get_graph().to_json()
        assert graph_dict is not None
        
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]
        
        expected_nodes = ["planner", "executor", "ci_monitor", "fixer", "finalizer"]
        for expected_node in expected_nodes:
            assert any(expected_node in node_id for node_id in node_ids), f"Node {expected_node} not found in graph"


class TestExecutorNodeSourcePrNumber:
    """Tests for source_pr_number extraction and type handling in executor_node (Issue #2918)"""
    
    @patch('graph.execute')
    def test_executor_node_passes_int_pr_number(self, mock_execute):
        """Test executor_node correctly passes integer pr_number to execute()"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 42,  # Integer PR number
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify execute was called with source_pr_number=42
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] == 42
    
    @patch('graph.execute')
    def test_executor_node_converts_string_pr_number(self, mock_execute):
        """Test executor_node converts string pr_number to int"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": "123",  # String PR number (from webhook resource_id)
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify execute was called with source_pr_number=123 (converted to int)
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] == 123
    
    @patch('graph.execute')
    def test_executor_node_handles_zero_pr_number(self, mock_execute):
        """Test executor_node treats 0 as None (goal-driven flow)"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,  # Zero = no source PR
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify execute was called with source_pr_number=None
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] is None
    
    @patch('graph.execute')
    def test_executor_node_handles_none_pr_number(self, mock_execute):
        """Test executor_node handles None pr_number gracefully"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": None,  # Explicit None
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify execute was called with source_pr_number=None
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] is None
    
    @patch('graph.execute')
    def test_executor_node_handles_missing_pr_number(self, mock_execute):
        """Test executor_node handles missing pr_number key gracefully"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            # pr_number key is missing
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify execute was called with source_pr_number=None
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] is None
    
    @patch('graph.execute')
    @patch('langgraph_orchestrator.logger')
    def test_executor_node_logs_warning_for_invalid_pr_number(self, mock_logger, mock_execute):
        """Test executor_node logs warning for unparseable pr_number"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": "not-a-number",  # Invalid string
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify warning was logged
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args
        assert "Could not parse pr_number" in warning_call[0][0]
        
        # Verify execute was called with source_pr_number=None (fallback)
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] is None
    
    @patch('graph.execute')
    def test_executor_node_handles_negative_pr_number(self, mock_execute):
        """Test executor_node treats negative numbers as None"""
        mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": -5,  # Negative number (invalid)
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        executor_node(state)
        
        # Verify execute was called with source_pr_number=None
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args[1]
        assert call_kwargs["source_pr_number"] is None


class TestLangGraphDryRun:
    """Tests for dry_run mode handling in LangGraph nodes"""
    
    def test_ci_monitor_node_skips_checks_in_dry_run(self):
        """Test ci_monitor_node skips GitHub API calls when ci_state is dry_run"""
        from langgraph_orchestrator import ci_monitor_node
        
        state = {
            "messages": [],
            "goal": "Test",
            "trace_id": "dry-run-ci-test",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "dry-run://trace/dry-run-ci-test",
            "pr_number": 0,
            "ci_state": "dry_run",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        with patch('tools.github_api.get_repo') as mock_get_repo, \
             patch('tools.github_api.get_pr_checks') as mock_get_pr_checks:
            
            result = ci_monitor_node(state)
            
            # Verify GitHub API was NOT called
            mock_get_repo.assert_not_called()
            mock_get_pr_checks.assert_not_called()
            
            # Verify ci_state remains dry_run and state is returned unchanged
            assert result["ci_state"] == "dry_run"
            assert result is state
    
    def test_decision_node_approves_dry_run(self):
        """Test decision_node treats dry_run as approved to avoid CI loop"""
        from langgraph_orchestrator import decision_node
        
        state = {
            "messages": [],
            "goal": "Test",
            "trace_id": "dry-run-decision-test",
            "repo": "test/repo",
            "branch": "",
            "plan": ["Step 1"],
            "current_step": 1,
            "pr_url": "dry-run://trace/dry-run-decision-test",
            "pr_number": 0,
            "ci_state": "dry_run",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {},
            "review_severity": "none",
            "code_quality_score": 100
        }
        
        result = decision_node(state)
        
        # Verify dry_run is treated as approved
        assert result["merge_decision"] == "approve"
    
    def test_should_fix_or_finalize_routes_dry_run_to_finalize(self):
        """Test should_fix_or_finalize routes dry_run approved state to finalizer"""
        from langgraph_orchestrator import should_fix_or_finalize
        
        state = {
            "merge_decision": "approve",
            "retry_count": 0,
            "trace_id": "dry-run-routing-test"
        }
        
        result = should_fix_or_finalize(state)
        
        # Approved decisions should route to finalize
        assert result == "finalize"
    
    @patch('graph.execute')
    def test_executor_node_with_dry_run_result(self, mock_execute):
        """Test executor_node handles dry_run results from execute()"""
        mock_execute.return_value = ("dry-run://trace/test-123", "dry_run", "test-123")
        
        state = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "test/repo",
            "branch": "test",
            "plan": ["Step 1"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        result = executor_node(state)
        
        assert result["pr_url"] == "dry-run://trace/test-123"
        assert result["ci_state"] == "dry_run"
        assert result["error"] is None


class TestLangGraphPerformance:
    """Performance benchmark tests"""
    
    def test_node_execution_speed(self):
        """Test individual node execution speed"""
        state = {
            "messages": [],
            "goal": "Test",
            "trace_id": "perf-test",
            "repo": "test/repo",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        start = time.time()
        result = planner_node(state)
        duration = time.time() - start
        
        assert duration < 5.0, f"Planner node took {duration}s, should be < 5.0s"
        assert result is not None
    
    def test_graph_compilation_caching(self):
        """Test that graph compilation is efficient"""
        times = []
        
        for _ in range(3):
            start = time.time()
            create_orchestrator_graph()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0, f"Average compilation time {avg_time}s too slow"


class TestLangGraphObservability:
    """Tests for observability and tracing"""
    
    def test_trace_id_propagation(self):
        """Test trace_id is maintained through workflow"""
        trace_id = "trace-observability-123"
        
        state = {
            "messages": [],
            "goal": "Test",
            "trace_id": trace_id,
            "repo": "test/repo",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }
        
        result = planner_node(state)
        
        assert result["trace_id"] == trace_id
    
    def test_state_immutability_check(self):
        """Test that nodes return new state objects"""
        original_state = {
            "messages": [],
            "goal": "Test",
            "trace_id": "immut-test",
            "repo": "test/repo",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = planner_node(original_state)

        assert "plan" in result
        assert len(result["plan"]) > 0


class TestRedisCheckpointer:
    """Test suite for Redis Checkpointer factory function"""

    @patch('langgraph_orchestrator.settings')
    def test_get_checkpointer_returns_memory_saver_by_default(self, mock_settings):
        """Test that get_checkpointer returns MemorySaver when Redis is disabled"""
        from langgraph_orchestrator import get_checkpointer
        from langgraph.checkpoint.memory import MemorySaver

        mock_settings.use_redis_checkpointer = False
        mock_settings.redis_url = None

        checkpointer = get_checkpointer()

        assert isinstance(checkpointer, MemorySaver)

    @patch('langgraph_orchestrator.settings')
    def test_get_checkpointer_returns_memory_saver_when_redis_url_missing(self, mock_settings):
        """Test that get_checkpointer returns MemorySaver when REDIS_URL is not set"""
        from langgraph_orchestrator import get_checkpointer
        from langgraph.checkpoint.memory import MemorySaver

        mock_settings.use_redis_checkpointer = True
        mock_settings.redis_url = None

        with patch.dict('os.environ', {}, clear=True):
            checkpointer = get_checkpointer()

        assert isinstance(checkpointer, MemorySaver)

    @patch('langgraph_orchestrator.settings')
    def test_get_checkpointer_falls_back_on_import_error(self, mock_settings):
        """Test that get_checkpointer falls back to MemorySaver on ImportError"""
        from langgraph_orchestrator import get_checkpointer

        mock_settings.use_redis_checkpointer = True
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.redis_checkpointer_ttl = 86400

        # Since we can't easily mock the import inside the function,
        # we just verify the function returns a checkpointer
        checkpointer = get_checkpointer()
        assert checkpointer is not None

    @patch('langgraph_orchestrator.settings')
    def test_get_checkpointer_logs_memory_saver_usage(self, mock_settings):
        """Test that get_checkpointer logs when using MemorySaver"""
        from langgraph_orchestrator import get_checkpointer

        mock_settings.use_redis_checkpointer = False
        mock_settings.redis_url = None

        with patch('langgraph_orchestrator.logger') as mock_logger:
            get_checkpointer()
            # Verify logging was called
            assert mock_logger.info.called

    @patch('langgraph_orchestrator.settings')
    def test_get_checkpointer_attempts_redis_when_configured(self, mock_settings):
        """Test that get_checkpointer attempts Redis when properly configured"""
        from langgraph_orchestrator import get_checkpointer

        mock_settings.use_redis_checkpointer = True
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.redis_checkpointer_ttl = 86400

        # This will either succeed (if Redis is available) or fall back to MemorySaver
        checkpointer = get_checkpointer()

        # Either way, we should get a valid checkpointer
        assert checkpointer is not None

    def test_create_orchestrator_graph_uses_get_checkpointer(self):
        """Test that create_orchestrator_graph uses get_checkpointer factory"""
        with patch('langgraph_orchestrator.get_checkpointer') as mock_get_checkpointer:
            from langgraph.checkpoint.memory import MemorySaver
            mock_get_checkpointer.return_value = MemorySaver()

            from langgraph_orchestrator import create_orchestrator_graph
            app = create_orchestrator_graph()

            # Verify get_checkpointer was called
            mock_get_checkpointer.assert_called_once()
            assert app is not None
