"""
Tests for agent_protocol module - Interface Definitions for Dev and Ops Agents

Issue: #1958 - Meta Agent: 新模組單元測試
"""

import pytest
from datetime import datetime

from meta_agent.agent_protocol import (
    AgentCapability,
    AgentTask,
    AgentResult,
    DevAgentProtocol,
    OpsAgentProtocol,
    BaseDevAgent,
    BaseOpsAgent,
    validate_dev_agent,
    validate_ops_agent,
)


class TestAgentCapability:
    """Tests for AgentCapability enum"""

    def test_all_capabilities_exist(self):
        """Verify all expected capabilities are defined"""
        expected_capabilities = {
            "CODE_ANALYSIS",
            "CODE_WRITING",
            "CODE_REVIEW",
            "TEST_WRITING",
            "TEST_EXECUTION",
            "DOCUMENTATION",
            "DEPLOYMENT",
            "MONITORING",
            "INCIDENT_RESPONSE",
            "DATABASE_OPERATIONS",
        }
        actual_capabilities = {member.name for member in AgentCapability}
        assert actual_capabilities == expected_capabilities

    def test_capability_values(self):
        """Verify capability values are lowercase strings"""
        assert AgentCapability.CODE_ANALYSIS.value == "code_analysis"
        assert AgentCapability.DEPLOYMENT.value == "deployment"
        assert AgentCapability.INCIDENT_RESPONSE.value == "incident_response"


class TestAgentTask:
    """Tests for AgentTask dataclass"""

    def test_agent_task_creation(self):
        """Test creating an AgentTask"""
        task = AgentTask(
            task_id="task-123",
            action="analyze_code",
        )

        assert task.task_id == "task-123"
        assert task.action == "analyze_code"
        assert task.inputs == {}
        assert task.context == {}
        assert task.timeout_seconds == 300
        assert task.requires_approval is False

    def test_agent_task_with_all_fields(self):
        """Test creating AgentTask with all fields"""
        task = AgentTask(
            task_id="task-123",
            action="deploy",
            inputs={"environment": "staging", "version": "1.0.0"},
            context={"repo": "my-repo", "branch": "main"},
            timeout_seconds=600,
            requires_approval=True,
        )

        assert task.task_id == "task-123"
        assert task.action == "deploy"
        assert task.inputs == {"environment": "staging", "version": "1.0.0"}
        assert task.context == {"repo": "my-repo", "branch": "main"}
        assert task.timeout_seconds == 600
        assert task.requires_approval is True


class TestAgentResult:
    """Tests for AgentResult dataclass"""

    def test_agent_result_creation(self):
        """Test creating an AgentResult"""
        result = AgentResult(
            task_id="task-123",
            success=True,
        )

        assert result.task_id == "task-123"
        assert result.success is True
        assert result.outputs == {}
        assert result.error is None
        assert result.duration_seconds == 0
        assert result.metadata == {}
        assert result.started_at is None
        assert result.completed_at is None

    def test_agent_result_with_all_fields(self):
        """Test creating AgentResult with all fields"""
        started = datetime(2025, 1, 1, 10, 0, 0)
        completed = datetime(2025, 1, 1, 10, 5, 0)

        result = AgentResult(
            task_id="task-123",
            success=True,
            outputs={"files_modified": ["src/main.py"]},
            error=None,
            duration_seconds=300.5,
            metadata={"model": "gpt-4"},
            started_at=started,
            completed_at=completed,
        )

        assert result.task_id == "task-123"
        assert result.success is True
        assert result.outputs == {"files_modified": ["src/main.py"]}
        assert result.duration_seconds == 300.5
        assert result.metadata == {"model": "gpt-4"}
        assert result.started_at == started
        assert result.completed_at == completed

    def test_agent_result_failure(self):
        """Test creating a failed AgentResult"""
        result = AgentResult(
            task_id="task-123",
            success=False,
            error="Connection timeout",
            duration_seconds=30.0,
        )

        assert result.success is False
        assert result.error == "Connection timeout"

    def test_agent_result_to_dict(self):
        """Test converting AgentResult to dictionary"""
        started = datetime(2025, 1, 1, 10, 0, 0)
        completed = datetime(2025, 1, 1, 10, 5, 0)

        result = AgentResult(
            task_id="task-123",
            success=True,
            outputs={"result": "success"},
            duration_seconds=300.0,
            started_at=started,
            completed_at=completed,
        )

        data = result.to_dict()

        assert data["task_id"] == "task-123"
        assert data["success"] is True
        assert data["outputs"] == {"result": "success"}
        assert data["error"] is None
        assert data["duration_seconds"] == 300.0
        assert data["started_at"] == "2025-01-01T10:00:00"
        assert data["completed_at"] == "2025-01-01T10:05:00"

    def test_agent_result_to_dict_without_timestamps(self):
        """Test converting AgentResult to dictionary without timestamps"""
        result = AgentResult(
            task_id="task-123",
            success=True,
        )

        data = result.to_dict()

        assert data["started_at"] is None
        assert data["completed_at"] is None


class TestBaseDevAgent:
    """Tests for BaseDevAgent class"""

    def test_base_dev_agent_initialization(self):
        """Test BaseDevAgent initialization"""
        agent = BaseDevAgent()

        assert agent.is_available is True
        assert len(agent.capabilities) == 5
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        assert AgentCapability.CODE_WRITING in agent.capabilities
        assert AgentCapability.CODE_REVIEW in agent.capabilities
        assert AgentCapability.TEST_WRITING in agent.capabilities
        assert AgentCapability.TEST_EXECUTION in agent.capabilities

    def test_base_dev_agent_capabilities_property(self):
        """Test capabilities property returns correct list"""
        agent = BaseDevAgent()
        caps = agent.capabilities

        assert isinstance(caps, list)
        assert all(isinstance(c, AgentCapability) for c in caps)

    def test_base_dev_agent_is_available_property(self):
        """Test is_available property"""
        agent = BaseDevAgent()
        assert agent.is_available is True

    @pytest.mark.asyncio
    async def test_base_dev_agent_analyze_code_not_implemented(self):
        """Test analyze_code raises NotImplementedError"""
        agent = BaseDevAgent()
        task = AgentTask(task_id="task-1", action="analyze")

        with pytest.raises(NotImplementedError, match="Subclass must implement analyze_code"):
            await agent.analyze_code(task)

    @pytest.mark.asyncio
    async def test_base_dev_agent_write_code_not_implemented(self):
        """Test write_code raises NotImplementedError"""
        agent = BaseDevAgent()
        task = AgentTask(task_id="task-1", action="write")

        with pytest.raises(NotImplementedError, match="Subclass must implement write_code"):
            await agent.write_code(task)

    @pytest.mark.asyncio
    async def test_base_dev_agent_write_test_not_implemented(self):
        """Test write_test raises NotImplementedError"""
        agent = BaseDevAgent()
        task = AgentTask(task_id="task-1", action="test")

        with pytest.raises(NotImplementedError, match="Subclass must implement write_test"):
            await agent.write_test(task)

    @pytest.mark.asyncio
    async def test_base_dev_agent_run_test_not_implemented(self):
        """Test run_test raises NotImplementedError"""
        agent = BaseDevAgent()
        task = AgentTask(task_id="task-1", action="run_test")

        with pytest.raises(NotImplementedError, match="Subclass must implement run_test"):
            await agent.run_test(task)

    @pytest.mark.asyncio
    async def test_base_dev_agent_review_code_not_implemented(self):
        """Test review_code raises NotImplementedError"""
        agent = BaseDevAgent()
        task = AgentTask(task_id="task-1", action="review")

        with pytest.raises(NotImplementedError, match="Subclass must implement review_code"):
            await agent.review_code(task)


class TestBaseOpsAgent:
    """Tests for BaseOpsAgent class"""

    def test_base_ops_agent_initialization(self):
        """Test BaseOpsAgent initialization"""
        agent = BaseOpsAgent()

        assert agent.is_available is True
        assert len(agent.capabilities) == 3
        assert AgentCapability.DEPLOYMENT in agent.capabilities
        assert AgentCapability.MONITORING in agent.capabilities
        assert AgentCapability.INCIDENT_RESPONSE in agent.capabilities

    def test_base_ops_agent_capabilities_property(self):
        """Test capabilities property returns correct list"""
        agent = BaseOpsAgent()
        caps = agent.capabilities

        assert isinstance(caps, list)
        assert all(isinstance(c, AgentCapability) for c in caps)

    def test_base_ops_agent_is_available_property(self):
        """Test is_available property"""
        agent = BaseOpsAgent()
        assert agent.is_available is True

    @pytest.mark.asyncio
    async def test_base_ops_agent_deploy_not_implemented(self):
        """Test deploy raises NotImplementedError"""
        agent = BaseOpsAgent()
        task = AgentTask(task_id="task-1", action="deploy")

        with pytest.raises(NotImplementedError, match="Subclass must implement deploy"):
            await agent.deploy(task)

    @pytest.mark.asyncio
    async def test_base_ops_agent_monitor_not_implemented(self):
        """Test monitor raises NotImplementedError"""
        agent = BaseOpsAgent()
        task = AgentTask(task_id="task-1", action="monitor")

        with pytest.raises(NotImplementedError, match="Subclass must implement monitor"):
            await agent.monitor(task)

    @pytest.mark.asyncio
    async def test_base_ops_agent_rollback_not_implemented(self):
        """Test rollback raises NotImplementedError"""
        agent = BaseOpsAgent()
        task = AgentTask(task_id="task-1", action="rollback")

        with pytest.raises(NotImplementedError, match="Subclass must implement rollback"):
            await agent.rollback(task)

    @pytest.mark.asyncio
    async def test_base_ops_agent_scale_not_implemented(self):
        """Test scale raises NotImplementedError"""
        agent = BaseOpsAgent()
        task = AgentTask(task_id="task-1", action="scale")

        with pytest.raises(NotImplementedError, match="Subclass must implement scale"):
            await agent.scale(task)


class TestDevAgentProtocol:
    """Tests for DevAgentProtocol"""

    def test_base_dev_agent_implements_protocol(self):
        """Test that BaseDevAgent implements DevAgentProtocol"""
        agent = BaseDevAgent()
        assert isinstance(agent, DevAgentProtocol)

    def test_custom_dev_agent_implements_protocol(self):
        """Test that a custom implementation satisfies the protocol"""
        class CustomDevAgent:
            @property
            def capabilities(self):
                return [AgentCapability.CODE_ANALYSIS]

            @property
            def is_available(self):
                return True

            async def analyze_code(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def write_code(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def write_test(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def run_test(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def review_code(self, task):
                return AgentResult(task_id=task.task_id, success=True)

        agent = CustomDevAgent()
        assert isinstance(agent, DevAgentProtocol)


class TestOpsAgentProtocol:
    """Tests for OpsAgentProtocol"""

    def test_base_ops_agent_implements_protocol(self):
        """Test that BaseOpsAgent implements OpsAgentProtocol"""
        agent = BaseOpsAgent()
        assert isinstance(agent, OpsAgentProtocol)

    def test_custom_ops_agent_implements_protocol(self):
        """Test that a custom implementation satisfies the protocol"""
        class CustomOpsAgent:
            @property
            def capabilities(self):
                return [AgentCapability.DEPLOYMENT]

            @property
            def is_available(self):
                return True

            async def deploy(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def monitor(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def rollback(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def scale(self, task):
                return AgentResult(task_id=task.task_id, success=True)

        agent = CustomOpsAgent()
        assert isinstance(agent, OpsAgentProtocol)


class TestValidateDevAgent:
    """Tests for validate_dev_agent function"""

    def test_validate_dev_agent_with_base_agent(self):
        """Test validate_dev_agent with BaseDevAgent"""
        agent = BaseDevAgent()
        assert validate_dev_agent(agent) is True

    def test_validate_dev_agent_with_valid_custom_agent(self):
        """Test validate_dev_agent with valid custom agent"""
        class ValidDevAgent:
            @property
            def capabilities(self):
                return []

            @property
            def is_available(self):
                return True

            async def analyze_code(self, task):
                pass

            async def write_code(self, task):
                pass

            async def write_test(self, task):
                pass

            async def run_test(self, task):
                pass

            async def review_code(self, task):
                pass

        agent = ValidDevAgent()
        assert validate_dev_agent(agent) is True

    def test_validate_dev_agent_with_invalid_object(self):
        """Test validate_dev_agent with invalid object"""
        assert validate_dev_agent("not an agent") is False
        assert validate_dev_agent(123) is False
        assert validate_dev_agent(None) is False
        assert validate_dev_agent({}) is False

    def test_validate_dev_agent_with_incomplete_agent(self):
        """Test validate_dev_agent with incomplete implementation"""
        class IncompleteAgent:
            @property
            def capabilities(self):
                return []

            # Missing other required methods

        agent = IncompleteAgent()
        assert validate_dev_agent(agent) is False


class TestValidateOpsAgent:
    """Tests for validate_ops_agent function"""

    def test_validate_ops_agent_with_base_agent(self):
        """Test validate_ops_agent with BaseOpsAgent"""
        agent = BaseOpsAgent()
        assert validate_ops_agent(agent) is True

    def test_validate_ops_agent_with_valid_custom_agent(self):
        """Test validate_ops_agent with valid custom agent"""
        class ValidOpsAgent:
            @property
            def capabilities(self):
                return []

            @property
            def is_available(self):
                return True

            async def deploy(self, task):
                pass

            async def monitor(self, task):
                pass

            async def rollback(self, task):
                pass

            async def scale(self, task):
                pass

        agent = ValidOpsAgent()
        assert validate_ops_agent(agent) is True

    def test_validate_ops_agent_with_invalid_object(self):
        """Test validate_ops_agent with invalid object"""
        assert validate_ops_agent("not an agent") is False
        assert validate_ops_agent(123) is False
        assert validate_ops_agent(None) is False
        assert validate_ops_agent([]) is False

    def test_validate_ops_agent_with_incomplete_agent(self):
        """Test validate_ops_agent with incomplete implementation"""
        class IncompleteAgent:
            @property
            def capabilities(self):
                return []

            # Missing other required methods

        agent = IncompleteAgent()
        assert validate_ops_agent(agent) is False


class TestProtocolCrossValidation:
    """Tests for cross-validation between protocols"""

    def test_dev_agent_is_not_ops_agent(self):
        """Test that DevAgent doesn't satisfy OpsAgentProtocol"""
        agent = BaseDevAgent()
        assert validate_dev_agent(agent) is True
        assert validate_ops_agent(agent) is False

    def test_ops_agent_is_not_dev_agent(self):
        """Test that OpsAgent doesn't satisfy DevAgentProtocol"""
        agent = BaseOpsAgent()
        assert validate_ops_agent(agent) is True
        assert validate_dev_agent(agent) is False

    def test_hybrid_agent_satisfies_both(self):
        """Test that a hybrid agent can satisfy both protocols"""
        class HybridAgent:
            @property
            def capabilities(self):
                return [
                    AgentCapability.CODE_ANALYSIS,
                    AgentCapability.DEPLOYMENT,
                ]

            @property
            def is_available(self):
                return True

            # DevAgent methods
            async def analyze_code(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def write_code(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def write_test(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def run_test(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def review_code(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            # OpsAgent methods
            async def deploy(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def monitor(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def rollback(self, task):
                return AgentResult(task_id=task.task_id, success=True)

            async def scale(self, task):
                return AgentResult(task_id=task.task_id, success=True)

        agent = HybridAgent()
        assert validate_dev_agent(agent) is True
        assert validate_ops_agent(agent) is True
