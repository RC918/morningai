"""
Tests for Dev_Agent V2 OODA Loop implementation
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from dev_agent_v2 import (
    OODAPhase,
    ActionType,
    SessionState,
    SessionStore,
    DevAgentV2,
    create_dev_agent_v2
)


class TestOODAPhase:
    """Test OODA phase enum"""
    
    def test_ooda_phases_defined(self):
        """Test that all OODA phases are defined"""
        assert OODAPhase.OBSERVE.value == "observe"
        assert OODAPhase.ORIENT.value == "orient"
        assert OODAPhase.DECIDE.value == "decide"
        assert OODAPhase.ACT.value == "act"


class TestActionType:
    """Test ActionType enum"""
    
    def test_action_types_defined(self):
        """Test that all action types are defined"""
        assert ActionType.ANALYZE_CODE.value == "analyze_code"
        assert ActionType.FIX_ERROR.value == "fix_error"
        assert ActionType.RUN_TESTS.value == "run_tests"
        assert ActionType.CREATE_PR.value == "create_pr"
        assert ActionType.WAIT_CI.value == "wait_ci"
        assert ActionType.COMPLETE.value == "complete"
        assert ActionType.ESCALATE.value == "escalate"


class TestSessionState:
    """Test SessionState dataclass"""
    
    def test_session_state_initialization(self):
        """Test SessionState creates with defaults"""
        state = SessionState(
            session_id="test-session-1",
            task_id="task-123",
            goal="Test goal"
        )
        
        assert state.session_id == "test-session-1"
        assert state.task_id == "task-123"
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
    
    def test_add_observation(self):
        """Test adding observations to session state"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test"
        )
        
        state.add_observation("Test observation", {"key": "value"})
        
        assert len(state.observations) == 1
        assert state.observations[0]["observation"] == "Test observation"
        assert state.observations[0]["data"]["key"] == "value"
        assert "timestamp" in state.observations[0]
    
    def test_add_decision(self):
        """Test adding decisions to session state"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test"
        )
        
        state.add_decision(
            decision="Run tests",
            reasoning="Need to verify changes",
            action_type=ActionType.RUN_TESTS
        )
        
        assert len(state.decisions) == 1
        assert state.decisions[0]["decision"] == "Run tests"
        assert state.decisions[0]["reasoning"] == "Need to verify changes"
        assert state.decisions[0]["action_type"] == "run_tests"
    
    def test_add_action(self):
        """Test adding actions to session state"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test"
        )
        
        state.add_action(
            action_type=ActionType.FIX_ERROR,
            result={"fixed": True},
            success=True
        )
        
        assert len(state.actions) == 1
        assert state.actions[0]["action_type"] == "fix_error"
        assert state.actions[0]["result"]["fixed"] is True
        assert state.actions[0]["success"] is True
    
    def test_mark_solution_attempted(self):
        """Test marking solutions as attempted"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test"
        )
        
        state.mark_solution_attempted("solution_a")
        state.mark_solution_attempted("solution_b")
        state.mark_solution_attempted("solution_a")  # Duplicate
        
        assert len(state.attempted_solutions) == 2
        assert "solution_a" in state.attempted_solutions
        assert "solution_b" in state.attempted_solutions
    
    def test_to_dict(self):
        """Test converting session state to dictionary"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test"
        )
        state.add_observation("Test observation")
        
        data = state.to_dict()
        
        assert isinstance(data, dict)
        assert data["session_id"] == "test-session"
        assert data["task_id"] == "task-1"
        assert data["current_phase"] == "observe"
        assert len(data["observations"]) == 1
    
    def test_from_dict(self):
        """Test creating session state from dictionary"""
        data = {
            "session_id": "test-session",
            "task_id": "task-1",
            "goal": "Test goal",
            "current_phase": "decide",
            "iteration": 3,
            "max_iterations": 10,
            "observations": [],
            "decisions": [],
            "actions": [],
            "attempted_solutions": [],
            "context": {},
            "conversation_history": [],
            "status": "active",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
        
        state = SessionState.from_dict(data)
        
        assert state.session_id == "test-session"
        assert state.current_phase == OODAPhase.DECIDE
        assert state.iteration == 3


class TestSessionStore:
    """Test SessionStore Redis integration"""
    
    def test_session_store_save(self):
        """Test saving session state to Redis"""
        mock_redis = Mock()
        store = SessionStore(mock_redis)
        
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test"
        )
        
        store.save(state)
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "dev_agent:session:test-session"
        assert call_args[0][1] == 86400  # TTL
        saved_data = json.loads(call_args[0][2])
        assert saved_data["session_id"] == "test-session"
    
    def test_session_store_load(self):
        """Test loading session state from Redis"""
        mock_redis = Mock()
        state_data = {
            "session_id": "test-session",
            "task_id": "task-1",
            "goal": "Test",
            "current_phase": "observe",
            "iteration": 0,
            "max_iterations": 10,
            "observations": [],
            "decisions": [],
            "actions": [],
            "attempted_solutions": [],
            "context": {},
            "conversation_history": [],
            "status": "active",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(state_data)
        
        store = SessionStore(mock_redis)
        state = store.load("test-session")
        
        assert state is not None
        assert state.session_id == "test-session"
        assert state.task_id == "task-1"
        mock_redis.get.assert_called_once_with("dev_agent:session:test-session")
    
    def test_session_store_load_not_found(self):
        """Test loading non-existent session returns None"""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        
        store = SessionStore(mock_redis)
        state = store.load("nonexistent")
        
        assert state is None
    
    def test_session_store_delete(self):
        """Test deleting session from Redis"""
        mock_redis = Mock()
        store = SessionStore(mock_redis)
        
        store.delete("test-session")
        
        mock_redis.delete.assert_called_once_with("dev_agent:session:test-session")


class TestDevAgentV2:
    """Test DevAgentV2 OODA loop"""
    
    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client"""
        mock = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test analysis"))]
        mock.chat.completions.create.return_value = mock_response
        return mock
    
    @pytest.fixture
    def mock_session_store(self):
        """Mock session store"""
        return Mock()
    
    @pytest.fixture
    def dev_agent(self, mock_openai, mock_session_store):
        """Create DevAgentV2 instance with mocks"""
        return DevAgentV2(
            openai_client=mock_openai,
            session_store=mock_session_store
        )
    
    def test_observe_phase(self, dev_agent, mock_session_store):
        """Test observe phase adds observation and transitions"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal"
        )
        
        result = dev_agent.observe(state)
        
        assert len(result.observations) == 1
        assert result.current_phase == OODAPhase.ORIENT
        mock_session_store.save.assert_called_once()
    
    def test_orient_phase(self, dev_agent, mock_session_store, mock_openai):
        """Test orient phase calls GPT-4 and transitions"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.ORIENT
        )
        
        result = dev_agent.orient(state)
        
        assert result.current_phase == OODAPhase.DECIDE
        assert "orientation_analysis" in result.context
        mock_openai.chat.completions.create.assert_called_once()
        mock_session_store.save.assert_called_once()
    
    def test_orient_phase_handles_errors(self, dev_agent, mock_session_store, mock_openai):
        """Test orient phase handles GPT-4 errors gracefully"""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.ORIENT
        )
        
        result = dev_agent.orient(state)
        
        assert result.current_phase == OODAPhase.DECIDE
        assert "failed" in result.context["orientation_analysis"].lower()
    
    def test_decide_phase_first_iteration(self, dev_agent, mock_session_store):
        """Test decide phase chooses analyze on first iteration"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.DECIDE
        )
        
        result = dev_agent.decide(state)
        
        assert len(result.decisions) == 1
        assert result.decisions[0]["action_type"] == "analyze_code"
        assert result.current_phase == OODAPhase.ACT
    
    def test_decide_phase_escalates_at_max_iterations(self, dev_agent, mock_session_store):
        """Test decide phase escalates when max iterations reached"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.DECIDE,
            iteration=10,
            max_iterations=10
        )
        
        result = dev_agent.decide(state)
        
        assert len(result.decisions) == 1
        assert result.decisions[0]["action_type"] == "escalate"
    
    def test_decide_phase_creates_pr_after_success(self, dev_agent, mock_session_store):
        """Test decide phase creates PR after successful action"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.DECIDE
        )
        state.actions = [{"success": True, "action_type": "fix_error"}]
        
        result = dev_agent.decide(state)
        
        assert result.decisions[0]["action_type"] == "create_pr"
    
    def test_act_phase_escalate(self, dev_agent, mock_session_store):
        """Test act phase handles escalation"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.ACT
        )
        state.decisions = [{
            "action_type": "escalate",
            "decision": "Escalate",
            "reasoning": "Max iterations"
        }]
        
        result = dev_agent.act(state)
        
        assert result.status == "escalated"
        assert len(result.actions) == 1
        assert result.iteration == 1
        assert result.current_phase == OODAPhase.OBSERVE
    
    def test_act_phase_complete(self, dev_agent, mock_session_store):
        """Test act phase handles completion"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal",
            current_phase=OODAPhase.ACT
        )
        state.decisions = [{
            "action_type": "complete",
            "decision": "Complete",
            "reasoning": "All done"
        }]
        
        result = dev_agent.act(state)
        
        assert result.status == "completed"
        assert result.actions[0]["success"] is True
    
    def test_run_ooda_loop_creates_new_session(self, dev_agent, mock_session_store):
        """Test run_ooda_loop creates new session when not found"""
        mock_session_store.load.return_value = None
        
        def save_side_effect(state):
            if state.iteration > 0:
                state.status = "escalated"
        
        mock_session_store.save.side_effect = save_side_effect
        
        result = dev_agent.run_ooda_loop(
            session_id="new-session",
            task_id="task-1",
            goal="Test goal",
            max_iterations=1
        )
        
        assert result.session_id == "new-session"
        assert result.task_id == "task-1"
    
    def test_run_ooda_loop_stops_on_completion(self, dev_agent, mock_session_store):
        """Test run_ooda_loop stops when status is completed"""
        state = SessionState(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal"
        )
        mock_session_store.load.return_value = state
        
        original_act = dev_agent.act
        def mock_act(s):
            s.status = "completed"
            return s
        dev_agent.act = mock_act
        
        result = dev_agent.run_ooda_loop(
            session_id="test-session",
            task_id="task-1",
            goal="Test goal"
        )
        
        assert result.status == "completed"


def test_create_dev_agent_v2():
    """Test factory function creates agent correctly"""
    with patch('dev_agent_v2.OpenAI') as mock_openai_class:
        mock_redis = Mock()
        
        agent = create_dev_agent_v2(mock_redis)
        
        assert isinstance(agent, DevAgentV2)
        mock_openai_class.assert_called_once()
