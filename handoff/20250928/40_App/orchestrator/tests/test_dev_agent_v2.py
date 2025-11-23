"""
Tests for Dev_Agent V2 with OODA Loop and Session State

Phase 0-Lite: Targeted tests for AI-critical orchestrator modules
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from redis import Redis

from orchestrator.dev_agent_v2 import (
    DevAgentV2,
    SessionState,
    SessionStore,
    OODAPhase,
    ActionType,
    create_dev_agent_v2
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    redis_mock = Mock(spec=Redis)
    redis_mock.setex = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.delete = Mock()
    return redis_mock


@pytest.fixture
def session_store(mock_redis):
    """Create SessionStore with mock Redis"""
    return SessionStore(mock_redis)


@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    openai_mock = Mock()
    
    # Mock chat completion response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Analysis: Task is progressing well. Recommend continuing with current approach."
    
    openai_mock.chat.completions.create = Mock(return_value=mock_response)
    
    return openai_mock


@pytest.fixture
def dev_agent(mock_openai, session_store):
    """Create DevAgentV2 instance with mocks"""
    return DevAgentV2(
        openai_client=mock_openai,
        session_store=session_store,
        model="gpt-4-turbo-preview"
    )


@pytest.fixture
def sample_session_state():
    """Create sample session state for testing"""
    return SessionState(
        session_id="test-session-123",
        task_id="task-456",
        goal="Fix bug in authentication module",
        max_iterations=5
    )


class TestSessionState:
    """Test SessionState data class"""
    
    def test_session_state_initialization(self):
        """Test SessionState initializes with correct defaults"""
        state = SessionState(
            session_id="test-123",
            task_id="task-456",
            goal="Test goal"
        )
        
        assert state.session_id == "test-123"
        assert state.task_id == "task-456"
        assert state.goal == "Test goal"
        assert state.current_phase == OODAPhase.OBSERVE
        assert state.iteration == 0
        assert state.max_iterations == 10
        assert state.observations == []
        assert state.decisions == []
        assert state.actions == []
        assert state.attempted_solutions == []
        assert state.context == {}
        assert state.conversation_history == []
        assert state.status == "active"
        assert state.created_at is not None
        assert state.updated_at is not None
    
    def test_add_observation(self, sample_session_state):
        """Test adding observation to session state"""
        sample_session_state.add_observation(
            observation="Found error in auth.py line 42",
            data={"file": "auth.py", "line": 42}
        )
        
        assert len(sample_session_state.observations) == 1
        obs = sample_session_state.observations[0]
        assert obs["observation"] == "Found error in auth.py line 42"
        assert obs["data"]["file"] == "auth.py"
        assert obs["iteration"] == 0
        assert obs["phase"] == "observe"
    
    def test_add_decision(self, sample_session_state):
        """Test adding decision to session state"""
        sample_session_state.add_decision(
            decision="Fix authentication error",
            reasoning="Error is in token validation logic",
            action_type=ActionType.FIX_ERROR
        )
        
        assert len(sample_session_state.decisions) == 1
        decision = sample_session_state.decisions[0]
        assert decision["decision"] == "Fix authentication error"
        assert decision["reasoning"] == "Error is in token validation logic"
        assert decision["action_type"] == "fix_error"
    
    def test_add_action(self, sample_session_state):
        """Test adding action to session state"""
        sample_session_state.add_action(
            action_type=ActionType.FIX_ERROR,
            result={"files_modified": ["auth.py"]},
            success=True
        )
        
        assert len(sample_session_state.actions) == 1
        action = sample_session_state.actions[0]
        assert action["action_type"] == "fix_error"
        assert action["success"] is True
        assert action["result"]["files_modified"] == ["auth.py"]
    
    def test_mark_solution_attempted(self, sample_session_state):
        """Test marking solution as attempted"""
        sample_session_state.mark_solution_attempted("approach_1")
        sample_session_state.mark_solution_attempted("approach_2")
        sample_session_state.mark_solution_attempted("approach_1")  # Duplicate
        
        assert len(sample_session_state.attempted_solutions) == 2
        assert "approach_1" in sample_session_state.attempted_solutions
        assert "approach_2" in sample_session_state.attempted_solutions
    
    def test_to_dict_serialization(self, sample_session_state):
        """Test session state serialization to dict"""
        state_dict = sample_session_state.to_dict()
        
        assert state_dict["session_id"] == "test-session-123"
        assert state_dict["task_id"] == "task-456"
        assert state_dict["goal"] == "Fix bug in authentication module"
        assert state_dict["current_phase"] == "observe"
        assert state_dict["iteration"] == 0
        assert isinstance(state_dict["observations"], list)
    
    def test_from_dict_deserialization(self):
        """Test session state deserialization from dict"""
        state_dict = {
            "session_id": "test-789",
            "task_id": "task-101",
            "goal": "Test deserialization",
            "current_phase": "orient",
            "iteration": 3,
            "max_iterations": 10,
            "observations": [{"test": "data"}],
            "decisions": [],
            "actions": [],
            "attempted_solutions": ["solution_1"],
            "context": {"key": "value"},
            "conversation_history": [],
            "created_at": "2025-11-23T12:00:00Z",
            "updated_at": "2025-11-23T12:05:00Z",
            "status": "active"
        }
        
        state = SessionState.from_dict(state_dict)
        
        assert state.session_id == "test-789"
        assert state.current_phase == OODAPhase.ORIENT
        assert state.iteration == 3
        assert state.attempted_solutions == ["solution_1"]


class TestSessionStore:
    """Test SessionStore Redis operations"""
    
    def test_save_session_state(self, session_store, mock_redis, sample_session_state):
        """Test saving session state to Redis"""
        session_store.save(sample_session_state)
        
        # Verify Redis setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        
        # Check key format
        assert call_args[0][0] == f"dev_agent:session:{sample_session_state.session_id}"
        
        # Check TTL
        assert call_args[0][1] == 86400
        
        # Check data is JSON serializable
        saved_data = call_args[0][2]
        parsed_data = json.loads(saved_data)
        assert parsed_data["session_id"] == sample_session_state.session_id
    
    def test_load_session_state(self, session_store, mock_redis):
        """Test loading session state from Redis"""
        # Mock Redis to return serialized session state
        test_state = SessionState(
            session_id="load-test-123",
            task_id="task-789",
            goal="Test load"
        )
        mock_redis.get.return_value = json.dumps(test_state.to_dict())
        
        loaded_state = session_store.load("load-test-123")
        
        assert loaded_state is not None
        assert loaded_state.session_id == "load-test-123"
        assert loaded_state.task_id == "task-789"
        assert loaded_state.goal == "Test load"
        
        # Verify Redis get was called with correct key
        mock_redis.get.assert_called_once_with("dev_agent:session:load-test-123")
    
    def test_load_nonexistent_session(self, session_store, mock_redis):
        """Test loading non-existent session returns None"""
        mock_redis.get.return_value = None
        
        loaded_state = session_store.load("nonexistent-session")
        
        assert loaded_state is None
    
    def test_delete_session_state(self, session_store, mock_redis):
        """Test deleting session state from Redis"""
        session_store.delete("delete-test-123")
        
        mock_redis.delete.assert_called_once_with("dev_agent:session:delete-test-123")


class TestDevAgentV2OODALoop:
    """Test DevAgentV2 OODA loop phases"""
    
    def test_observe_phase(self, dev_agent, session_store, sample_session_state):
        """Test observe phase transitions to orient"""
        result_state = dev_agent.observe(sample_session_state)
        
        assert result_state.current_phase == OODAPhase.ORIENT
        assert len(result_state.observations) == 1
        assert "Observing task" in result_state.observations[0]["observation"]
    
    def test_orient_phase_with_gpt4(self, dev_agent, mock_openai, session_store, sample_session_state):
        """Test orient phase calls GPT-4 and transitions to decide"""
        # Add some observations first
        sample_session_state.add_observation("Test observation", {"test": "data"})
        sample_session_state.current_phase = OODAPhase.ORIENT
        
        result_state = dev_agent.orient(sample_session_state)
        
        # Verify GPT-4 was called
        mock_openai.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4-turbo-preview"
        assert call_kwargs["temperature"] == 0.3
        
        # Verify phase transition
        assert result_state.current_phase == OODAPhase.DECIDE
        assert "orientation_analysis" in result_state.context
    
    def test_orient_phase_handles_gpt4_failure(self, dev_agent, mock_openai, session_store, sample_session_state):
        """Test orient phase handles GPT-4 API failure gracefully"""
        # Make GPT-4 call fail
        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        
        sample_session_state.current_phase = OODAPhase.ORIENT
        result_state = dev_agent.orient(sample_session_state)
        
        # Should still transition to decide with fallback analysis
        assert result_state.current_phase == OODAPhase.DECIDE
        assert "Analysis failed" in result_state.context["orientation_analysis"]
    
    def test_decide_phase_first_iteration(self, dev_agent, session_store, sample_session_state):
        """Test decide phase on first iteration chooses analyze"""
        sample_session_state.current_phase = OODAPhase.DECIDE
        
        result_state = dev_agent.decide(sample_session_state)
        
        assert result_state.current_phase == OODAPhase.ACT
        assert len(result_state.decisions) == 1
        
        decision = result_state.decisions[0]
        assert decision["action_type"] == "analyze_code"
        assert "analyzing codebase" in decision["decision"].lower()
    
    def test_decide_phase_max_iterations_reached(self, dev_agent, session_store, sample_session_state):
        """Test decide phase escalates when max iterations reached"""
        sample_session_state.iteration = 10
        sample_session_state.max_iterations = 10
        sample_session_state.current_phase = OODAPhase.DECIDE
        
        result_state = dev_agent.decide(sample_session_state)
        
        decision = result_state.decisions[0]
        assert decision["action_type"] == "escalate"
        assert "Max iterations" in decision["decision"]
    
    def test_decide_phase_after_success(self, dev_agent, session_store, sample_session_state):
        """Test decide phase creates PR after successful action"""
        # Add a successful action
        sample_session_state.add_action(
            action_type=ActionType.FIX_ERROR,
            result={"success": True},
            success=True
        )
        sample_session_state.current_phase = OODAPhase.DECIDE
        
        result_state = dev_agent.decide(sample_session_state)
        
        decision = result_state.decisions[0]
        assert decision["action_type"] == "create_pr"
    
    def test_act_phase_escalate(self, dev_agent, session_store, sample_session_state):
        """Test act phase handles escalation"""
        sample_session_state.add_decision(
            decision="Escalate to human",
            reasoning="Max iterations reached",
            action_type=ActionType.ESCALATE
        )
        sample_session_state.current_phase = OODAPhase.ACT
        
        result_state = dev_agent.act(sample_session_state)
        
        assert result_state.status == "escalated"
        assert len(result_state.actions) == 1
        assert result_state.actions[0]["action_type"] == "escalate"
        assert result_state.actions[0]["success"] is False
    
    def test_act_phase_complete(self, dev_agent, session_store, sample_session_state):
        """Test act phase handles completion"""
        sample_session_state.add_decision(
            decision="Task complete",
            reasoning="All tests passing",
            action_type=ActionType.COMPLETE
        )
        sample_session_state.current_phase = OODAPhase.ACT
        
        result_state = dev_agent.act(sample_session_state)
        
        assert result_state.status == "completed"
        assert result_state.actions[0]["success"] is True
    
    def test_act_phase_increments_iteration(self, dev_agent, session_store, sample_session_state):
        """Test act phase increments iteration counter"""
        initial_iteration = sample_session_state.iteration
        
        sample_session_state.add_decision(
            decision="Test decision",
            reasoning="Test reasoning",
            action_type=ActionType.ANALYZE_CODE
        )
        sample_session_state.current_phase = OODAPhase.ACT
        
        result_state = dev_agent.act(sample_session_state)
        
        assert result_state.iteration == initial_iteration + 1
        assert result_state.current_phase == OODAPhase.OBSERVE


class TestDevAgentV2Integration:
    """Integration tests for complete OODA loop"""
    
    def test_run_ooda_loop_creates_new_session(self, dev_agent, session_store, mock_redis):
        """Test run_ooda_loop creates new session if not exists"""
        mock_redis.get.return_value = None  # No existing session
        
        final_state = dev_agent.run_ooda_loop(
            session_id="integration-test-123",
            task_id="task-999",
            goal="Integration test goal",
            max_iterations=3
        )
        
        assert final_state.session_id == "integration-test-123"
        assert final_state.task_id == "task-999"
        assert final_state.goal == "Integration test goal"
        assert final_state.iteration > 0  # Should have run at least one iteration
    
    def test_run_ooda_loop_stops_at_max_iterations(self, dev_agent, session_store, mock_redis):
        """Test run_ooda_loop respects max_iterations limit"""
        mock_redis.get.return_value = None
        
        final_state = dev_agent.run_ooda_loop(
            session_id="max-iter-test",
            task_id="task-888",
            goal="Test max iterations",
            max_iterations=2
        )
        
        # Should stop at or before max_iterations
        assert final_state.iteration <= 2
        assert final_state.status in ["active", "escalated", "completed", "failed"]
    
    def test_run_ooda_loop_stops_on_completion(self, dev_agent, session_store, mock_redis, mock_openai):
        """Test run_ooda_loop stops when status changes to completed"""
        mock_redis.get.return_value = None
        
        # Mock to make it complete quickly
        original_decide = dev_agent.decide
        def mock_decide(state):
            state.add_decision(
                decision="Complete task",
                reasoning="Test completion",
                action_type=ActionType.COMPLETE
            )
            state.current_phase = OODAPhase.ACT
            return state
        
        dev_agent.decide = mock_decide
        
        final_state = dev_agent.run_ooda_loop(
            session_id="completion-test",
            task_id="task-777",
            goal="Test completion",
            max_iterations=10
        )
        
        assert final_state.status == "completed"
        assert final_state.iteration < 10  # Should complete before max


class TestCreateDevAgentV2Factory:
    """Test factory function for creating DevAgentV2"""
    
    @patch('orchestrator.dev_agent_v2.OpenAI')
    @patch('orchestrator.dev_agent_v2.settings')
    def test_create_dev_agent_v2(self, mock_settings, mock_openai_class, mock_redis):
        """Test factory function creates properly configured agent"""
        mock_settings.openai_api_key = "test-api-key"
        mock_settings.dev_agent_model = "gpt-4-turbo-preview"
        
        agent = create_dev_agent_v2(mock_redis)
        
        assert isinstance(agent, DevAgentV2)
        assert agent.model == "gpt-4-turbo-preview"
        
        # Verify OpenAI client was created with correct API key
        mock_openai_class.assert_called_once_with(api_key="test-api-key")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
