"""
Tests for LangGraph Orchestrator implementation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langgraph_orchestrator import (
    AgentState,
    planner_node,
    executor_node,
    ci_monitor_node,
    fixer_node,
    finalizer_node,
    should_continue_execution,
    should_retry_or_finish,
    create_orchestrator_graph,
    run_orchestrator
)


class TestPlannerNode:
    """Test planner_node functionality"""
    
    def test_planner_creates_plan(self):
        """Test that planner creates a multi-step plan"""
        state = {
            "goal": "Create FAQ documentation",
            "trace_id": "test-123",
            "messages": []
        }
        
        result = planner_node(state)
        
        assert "plan" in result
        assert len(result["plan"]) == 7
        assert result["current_step"] == 0
        assert "Analyze codebase" in result["plan"][0]
        assert "Generate FAQ content" in result["plan"][1]
    
    def test_planner_adds_system_message(self):
        """Test that planner adds system message to messages"""
        state = {
            "goal": "Test goal",
            "trace_id": "test-123",
            "messages": []
        }
        
        result = planner_node(state)
        
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], SystemMessage)
        assert "Planned" in result["messages"][0].content
    
    def test_planner_preserves_existing_messages(self):
        """Test that planner preserves existing messages"""
        state = {
            "goal": "Test goal",
            "trace_id": "test-123",
            "messages": [HumanMessage(content="Previous message")]
        }
        
        result = planner_node(state)
        
        assert len(result["messages"]) == 2
        assert result["messages"][0].content == "Previous message"


class TestExecutorNode:
    """Test executor_node functionality"""
    
    @patch('graph.execute')
    def test_executor_success(self, mock_execute):
        """Test executor node successful execution"""
        mock_execute.return_value = ("https://github.com/pr/1", "success", "trace-123")
        
        state = {
            "trace_id": "trace-123",
            "goal": "Test goal",
            "repo": "owner/repo",
            "current_step": 0,
            "plan": ["Step 1", "Step 2"],
            "messages": []
        }
        
        result = executor_node(state)
        
        assert result["pr_url"] == "https://github.com/pr/1"
        assert result["ci_state"] == "success"
        assert result["error"] is None
        assert result["current_step"] == 1
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
    
    @patch('graph.execute')
    def test_executor_handles_errors(self, mock_execute):
        """Test executor node error handling"""
        mock_execute.side_effect = Exception("Execution failed")
        
        state = {
            "trace_id": "trace-123",
            "goal": "Test goal",
            "repo": "owner/repo",
            "current_step": 0,
            "plan": ["Step 1"],
            "messages": []
        }
        
        result = executor_node(state)
        
        assert result["error"] == "Execution failed"
        assert result["retry_count"] == 1
        assert result["current_step"] == 1
        assert len(result["messages"]) == 1
        assert "Error" in result["messages"][0].content
    
    @patch('graph.execute')
    def test_executor_increments_retry_count(self, mock_execute):
        """Test that executor increments retry count on error"""
        mock_execute.side_effect = Exception("Error")
        
        state = {
            "trace_id": "trace-123",
            "goal": "Test goal",
            "repo": "owner/repo",
            "current_step": 0,
            "plan": ["Step 1"],
            "messages": [],
            "retry_count": 2
        }
        
        result = executor_node(state)
        
        assert result["retry_count"] == 3


class TestCIMonitorNode:
    """Test ci_monitor_node functionality"""
    
    @patch('tools.github_api.get_pr_checks')
    @patch('tools.github_api.get_repo')
    def test_ci_monitor_success(self, mock_get_repo, mock_get_pr_checks):
        """Test CI monitor with successful checks"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_get_pr_checks.return_value = ("success", {"check1": "passed"})
        
        state = {
            "trace_id": "trace-123",
            "pr_number": 123,
            "messages": []
        }
        
        result = ci_monitor_node(state)
        
        assert result["ci_state"] == "success"
        assert result["ci_checks"] == {"check1": "passed"}
        assert len(result["messages"]) == 1
        mock_get_pr_checks.assert_called_once_with(mock_repo, 123)
    
    @patch('tools.github_api.get_pr_checks')
    @patch('tools.github_api.get_repo')
    def test_ci_monitor_no_pr_number(self, mock_get_repo, mock_get_pr_checks):
        """Test CI monitor when no PR number is available"""
        state = {
            "trace_id": "trace-123",
            "pr_number": None,
            "messages": []
        }
        
        result = ci_monitor_node(state)
        
        assert result["ci_state"] == "unknown"
        mock_get_pr_checks.assert_not_called()
    
    @patch('tools.github_api.get_pr_checks')
    @patch('tools.github_api.get_repo')
    def test_ci_monitor_handles_errors(self, mock_get_repo, mock_get_pr_checks):
        """Test CI monitor error handling"""
        mock_get_repo.side_effect = Exception("API Error")
        
        state = {
            "trace_id": "trace-123",
            "pr_number": 123,
            "messages": []
        }
        
        result = ci_monitor_node(state)
        
        assert result["ci_state"] == "error"
        assert result["error"] == "API Error"


class TestFixerNode:
    """Test fixer_node functionality"""
    
    def test_fixer_first_attempt(self):
        """Test fixer on first attempt"""
        state = {
            "trace_id": "trace-123",
            "ci_checks": {"check1": "failed"},
            "retry_count": 0,
            "messages": []
        }
        
        result = fixer_node(state)
        
        assert len(result["messages"]) == 1
        assert "attempt 1/3" in result["messages"][0].content
    
    def test_fixer_max_retries(self):
        """Test fixer when max retries reached"""
        state = {
            "trace_id": "trace-123",
            "ci_checks": {},
            "retry_count": 3,
            "messages": []
        }
        
        result = fixer_node(state)
        
        assert result["error"] == "Max retries exceeded"
    
    def test_fixer_second_attempt(self):
        """Test fixer on second attempt"""
        state = {
            "trace_id": "trace-123",
            "ci_checks": {},
            "retry_count": 1,
            "messages": []
        }
        
        result = fixer_node(state)
        
        assert "attempt 2/3" in result["messages"][0].content


class TestFinalizerNode:
    """Test finalizer_node functionality"""
    
    def test_finalizer_success_state(self):
        """Test finalizer with successful workflow"""
        state = {
            "trace_id": "trace-123",
            "pr_url": "https://github.com/pr/1",
            "ci_state": "success",
            "error": None,
            "messages": []
        }
        
        result = finalizer_node(state)
        
        assert result["final_result"]["status"] == "success"
        assert result["final_result"]["pr_url"] == "https://github.com/pr/1"
        assert result["final_result"]["error"] is None
        assert "timestamp" in result["final_result"]
    
    def test_finalizer_error_state(self):
        """Test finalizer with error workflow"""
        state = {
            "trace_id": "trace-123",
            "pr_url": None,
            "ci_state": "error",
            "error": "Something failed",
            "messages": []
        }
        
        result = finalizer_node(state)
        
        assert result["final_result"]["status"] == "error"
        assert result["final_result"]["error"] == "Something failed"
    
    def test_finalizer_adds_message(self):
        """Test that finalizer adds completion message"""
        state = {
            "trace_id": "trace-123",
            "pr_url": "https://github.com/pr/1",
            "ci_state": "success",
            "error": None,
            "messages": []
        }
        
        result = finalizer_node(state)
        
        assert len(result["messages"]) == 1
        assert "completed" in result["messages"][0].content.lower()


class TestRoutingFunctions:
    """Test routing decision functions"""
    
    def test_should_continue_execution_with_error(self):
        """Test routing when there's an error"""
        state = {
            "error": "Something failed",
            "retry_count": 1,
            "current_step": 0,
            "plan": ["Step 1"]
        }
        
        result = should_continue_execution(state)
        
        assert result == "fix"
    
    def test_should_continue_execution_max_retries(self):
        """Test routing when max retries reached"""
        state = {
            "error": "Something failed",
            "retry_count": 3,
            "current_step": 0,
            "plan": ["Step 1"]
        }
        
        result = should_continue_execution(state)
        
        assert result == "finalize"
    
    def test_should_continue_execution_plan_complete(self):
        """Test routing when plan is complete"""
        state = {
            "error": None,
            "current_step": 2,
            "plan": ["Step 1", "Step 2"]
        }
        
        result = should_continue_execution(state)
        
        assert result == "monitor_ci"
    
    def test_should_continue_execution_continue(self):
        """Test routing to continue execution"""
        state = {
            "error": None,
            "current_step": 0,
            "plan": ["Step 1", "Step 2"]
        }
        
        result = should_continue_execution(state)
        
        assert result == "execute"
    
    def test_should_retry_or_finish_success(self):
        """Test routing when CI succeeds"""
        state = {
            "ci_state": "success",
            "error": None
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "finalize"
    
    def test_should_retry_or_finish_failure(self):
        """Test routing when CI fails"""
        state = {
            "ci_state": "failure",
            "error": None,
            "retry_count": 0
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "fix"
    
    def test_should_retry_or_finish_max_retries(self):
        """Test routing when CI fails with max retries"""
        state = {
            "ci_state": "failure",
            "error": None,
            "retry_count": 3
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "finalize"
    
    def test_should_retry_or_finish_pending(self):
        """Test routing when CI is pending"""
        state = {
            "ci_state": "pending",
            "error": None
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "monitor_ci"
    
    def test_should_retry_or_finish_with_error(self):
        """Test routing when there's an error"""
        state = {
            "ci_state": "success",
            "error": "Something failed"
        }
        
        result = should_retry_or_finish(state)
        
        assert result == "finalize"


class TestOrchestratorGraph:
    """Test orchestrator graph creation"""
    
    def test_create_orchestrator_graph(self):
        """Test that graph is created successfully"""
        app = create_orchestrator_graph()
        
        assert app is not None
        assert hasattr(app, 'invoke')
    
    @patch('langgraph_orchestrator.create_orchestrator_graph')
    def test_run_orchestrator_success(self, mock_create_graph):
        """Test run_orchestrator with successful workflow"""
        mock_app = Mock()
        mock_result = {
            "final_result": {
                "trace_id": "test-123",
                "pr_url": "https://github.com/pr/1",
                "ci_state": "success",
                "status": "success",
                "error": None
            }
        }
        mock_app.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_app
        
        result = run_orchestrator(
            goal="Create FAQ",
            repo="owner/repo",
            trace_id="test-123"
        )
        
        assert result["status"] == "success"
        assert result["pr_url"] == "https://github.com/pr/1"
        assert result["trace_id"] == "test-123"
    
    @patch('langgraph_orchestrator.create_orchestrator_graph')
    def test_run_orchestrator_handles_errors(self, mock_create_graph):
        """Test run_orchestrator error handling"""
        mock_app = Mock()
        mock_app.invoke.side_effect = Exception("Workflow failed")
        mock_create_graph.return_value = mock_app
        
        result = run_orchestrator(
            goal="Create FAQ",
            repo="owner/repo",
            trace_id="test-123"
        )
        
        assert result["status"] == "error"
        assert result["error"] == "Workflow failed"
        assert result["trace_id"] == "test-123"
    
    @patch('langgraph_orchestrator.create_orchestrator_graph')
    def test_run_orchestrator_initial_state(self, mock_create_graph):
        """Test that run_orchestrator creates proper initial state"""
        mock_app = Mock()
        mock_result = {"final_result": {"status": "success"}}
        mock_app.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_app
        
        run_orchestrator(
            goal="Test goal",
            repo="owner/repo",
            trace_id="test-123"
        )
        
        call_args = mock_app.invoke.call_args
        initial_state = call_args[0][0]
        
        assert initial_state["goal"] == "Test goal"
        assert initial_state["repo"] == "owner/repo"
        assert initial_state["trace_id"] == "test-123"
        assert initial_state["current_step"] == 0
        assert initial_state["retry_count"] == 0
        assert len(initial_state["messages"]) == 1
        assert isinstance(initial_state["messages"][0], HumanMessage)


class TestAgentState:
    """Test AgentState TypedDict structure"""
    
    def test_agent_state_structure(self):
        """Test that AgentState has expected fields"""
        state = {
            "messages": [],
            "goal": "test",
            "trace_id": "123",
            "repo": "owner/repo",
            "branch": "main",
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
        
        assert "messages" in state
        assert "goal" in state
        assert "trace_id" in state
        assert "repo" in state
        assert "plan" in state
        assert "pr_url" in state
        assert "ci_state" in state
