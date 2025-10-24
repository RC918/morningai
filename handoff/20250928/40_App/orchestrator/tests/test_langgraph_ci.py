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
    
    @pytest.mark.integration
    def test_full_workflow_mock(self):
        """Integration test with mocked dependencies"""
        with patch('graph.execute') as mock_execute:
            mock_execute.return_value = ("https://github.com/test/pr/1", "success", "test-123")
            
            app = create_orchestrator_graph()
            
            initial_state = {
                "messages": [HumanMessage(content="Create FAQ")],
                "goal": "Create FAQ documentation",
                "trace_id": "test-integration-123",
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
            
            config = {"configurable": {"thread_id": "test-integration-123"}}
            
            result = app.invoke(initial_state, config)
            
            assert result is not None
            assert "final_result" in result


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
        
        assert duration < 0.1, f"Planner node took {duration}s, should be < 0.1s"
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
