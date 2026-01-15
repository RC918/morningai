"""
Simulation Scenario Base Classes

Blueprint Section 5.3: Multi-Agent Simulation Suite v1

Provides base classes for defining simulation scenarios that test
multi-agent interactions, Flow v3 branches, routing, and more.
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ScenarioStatus(Enum):
    """Status of a simulation scenario execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ScenarioResult:
    """
    Result of a simulation scenario execution.

    Attributes:
        scenario_id: Unique identifier for the scenario
        scenario_name: Human-readable name
        status: Execution status
        duration_ms: Execution duration in milliseconds
        assertions_passed: Number of assertions that passed
        assertions_failed: Number of assertions that failed
        error_message: Error message if status is ERROR or FAILED
        error_traceback: Full traceback if available
        metadata: Additional metadata from the scenario
        timestamp: When the scenario was executed
    """
    scenario_id: str
    scenario_name: str
    status: ScenarioStatus
    duration_ms: float
    assertions_passed: int = 0
    assertions_failed: int = 0
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class SimulationScenario(ABC):
    """
    Base class for simulation scenarios.

    Blueprint Section 5.3 defines scenarios for:
    - Multi-agent E2E testing
    - Flow v3 branch testing
    - Routing testing
    - Safety/compliance testing
    - Drift testing
    - Provider fallback testing

    Subclasses must implement:
    - name: Human-readable scenario name
    - setup(): Prepare the scenario environment
    - execute(): Run the scenario logic
    - teardown(): Clean up after execution
    - validate(): Check assertions and return results

    Example:
        class FlowBranchScenario(SimulationScenario):
            name = "Flow v3 Branch Testing"

            def setup(self):
                self.flow_controller = FlowController()

            def execute(self):
                result = self.flow_controller.execute_branch("review")
                self.execution_result = result

            def validate(self) -> List[Tuple[str, bool]]:
                return [
                    ("Branch executed successfully", self.execution_result.success),
                    ("No errors in execution", len(self.execution_result.errors) == 0),
                ]
    """

    # Subclasses must define these
    name: str = "Unnamed Scenario"
    description: str = ""
    tags: List[str] = []
    timeout_seconds: float = 300.0  # 5 minutes default

    def __init__(self):
        self.scenario_id = str(uuid.uuid4())
        self._assertions: List[tuple] = []
        self._metadata: Dict[str, Any] = {}
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    @abstractmethod
    def setup(self) -> None:
        """
        Prepare the scenario environment.

        Called before execute(). Use this to:
        - Initialize dependencies
        - Set up mock data
        - Configure test fixtures
        """
        pass

    @abstractmethod
    def execute(self) -> None:
        """
        Run the scenario logic.

        This is where the main test logic goes.
        Store results in instance variables for validation.
        """
        pass

    @abstractmethod
    def validate(self) -> List[tuple]:
        """
        Check assertions and return results.

        Returns:
            List of tuples: (assertion_name, passed: bool)

        Example:
            return [
                ("Response status is 200", response.status == 200),
                ("Response has data", response.data is not None),
            ]
        """
        pass

    def teardown(self) -> None:
        """
        Clean up after execution.

        Called after validate(), even if execute() or validate() fails.
        Override to clean up resources.
        """
        pass

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the scenario result."""
        self._metadata[key] = value

    def run(self) -> ScenarioResult:
        """
        Execute the full scenario lifecycle.

        Returns:
            ScenarioResult with execution details
        """
        self._start_time = time.time()
        assertions_passed = 0
        assertions_failed = 0
        error_message = None
        error_traceback = None
        status = ScenarioStatus.PENDING

        try:
            # Setup phase
            logger.info(
                f"[Simulation] Setting up scenario: {self.name}",
                extra={"operation": "simulation.scenario", "scenario_id": self.scenario_id}
            )
            self.setup()

            # Execute phase
            status = ScenarioStatus.RUNNING
            logger.info(
                f"[Simulation] Executing scenario: {self.name}",
                extra={"operation": "simulation.scenario", "scenario_id": self.scenario_id}
            )
            self.execute()

            # Validate phase
            logger.info(
                f"[Simulation] Validating scenario: {self.name}",
                extra={"operation": "simulation.scenario", "scenario_id": self.scenario_id}
            )
            assertions = self.validate()

            for assertion_name, passed in assertions:
                if passed:
                    assertions_passed += 1
                    logger.debug(
                        f"[Simulation] Assertion PASSED: {assertion_name}",
                        extra={"operation": "simulation.scenario", "scenario_id": self.scenario_id}
                    )
                else:
                    assertions_failed += 1
                    logger.warning(
                        f"[Simulation] Assertion FAILED: {assertion_name}",
                        extra={"operation": "simulation.scenario", "scenario_id": self.scenario_id}
                    )

            # Determine final status
            if assertions_failed > 0:
                status = ScenarioStatus.FAILED
                error_message = f"{assertions_failed} assertion(s) failed"
            else:
                status = ScenarioStatus.PASSED

        except Exception as e:
            import traceback
            status = ScenarioStatus.ERROR
            error_message = str(e)
            error_traceback = traceback.format_exc()
            logger.error(
                f"[Simulation] Scenario error: {self.name} - {e}",
                extra={
                    "operation": "simulation.scenario",
                    "scenario_id": self.scenario_id,
                    "error": str(e),
                }
            )
        finally:
            # Teardown phase (always runs)
            try:
                self.teardown()
            except Exception as e:
                logger.warning(
                    f"[Simulation] Teardown error: {self.name} - {e}",
                    extra={"operation": "simulation.scenario", "scenario_id": self.scenario_id}
                )

            self._end_time = time.time()

        duration_ms = (self._end_time - self._start_time) * 1000

        result = ScenarioResult(
            scenario_id=self.scenario_id,
            scenario_name=self.name,
            status=status,
            duration_ms=duration_ms,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            error_message=error_message,
            error_traceback=error_traceback,
            metadata=self._metadata,
        )

        logger.info(
            f"[Simulation] Scenario completed: {self.name} - {status.value} "
            f"(passed={assertions_passed}, failed={assertions_failed}, duration={duration_ms:.2f}ms)",
            extra={
                "operation": "simulation.scenario",
                "scenario_id": self.scenario_id,
                "status": status.value,
                "duration_ms": duration_ms,
            }
        )

        return result


# Pre-built scenario types for common testing patterns

class FlowBranchScenario(SimulationScenario):
    """
    Base class for Flow v3 branch testing scenarios.

    Blueprint Section 5.3: Flow v3 branch testing
    """

    tags = ["flow", "branch"]

    def __init__(self, branch_name: str):
        super().__init__()
        self.branch_name = branch_name
        self.flow_result: Optional[Dict[str, Any]] = None

    def setup(self) -> None:
        """Initialize flow controller for testing."""
        self.add_metadata("branch_name", self.branch_name)

    def execute(self) -> None:
        """Execute the flow branch - override in subclass."""
        pass

    def validate(self) -> List[tuple]:
        """Validate flow execution - override in subclass."""
        return []


class RoutingScenario(SimulationScenario):
    """
    Base class for routing testing scenarios.

    Blueprint Section 5.3: Routing testing
    """

    tags = ["routing"]

    def __init__(self, task_type: str, expected_provider: Optional[str] = None):
        super().__init__()
        self.task_type = task_type
        self.expected_provider = expected_provider
        self.routing_result: Optional[Dict[str, Any]] = None

    def setup(self) -> None:
        """Initialize routing engine for testing."""
        self.add_metadata("task_type", self.task_type)
        if self.expected_provider:
            self.add_metadata("expected_provider", self.expected_provider)

    def execute(self) -> None:
        """Execute routing - override in subclass."""
        pass

    def validate(self) -> List[tuple]:
        """Validate routing result - override in subclass."""
        return []


class SafetyComplianceScenario(SimulationScenario):
    """
    Base class for safety/compliance testing scenarios.

    Blueprint Section 5.3: Safety/compliance testing
    """

    tags = ["safety", "compliance"]

    def __init__(self, test_input: str, expected_blocked: bool = False):
        super().__init__()
        self.test_input = test_input
        self.expected_blocked = expected_blocked
        self.safety_result: Optional[Dict[str, Any]] = None

    def setup(self) -> None:
        """Initialize safety scanner for testing."""
        self.add_metadata("expected_blocked", self.expected_blocked)

    def execute(self) -> None:
        """Execute safety check - override in subclass."""
        pass

    def validate(self) -> List[tuple]:
        """Validate safety result - override in subclass."""
        return []


class DriftScenario(SimulationScenario):
    """
    Base class for drift testing scenarios.

    Blueprint Section 5.3: Drift testing
    """

    tags = ["drift", "governance"]

    def __init__(self, provider: str, model: str):
        super().__init__()
        self.provider = provider
        self.model = model
        self.drift_metrics: Optional[Dict[str, Any]] = None

    def setup(self) -> None:
        """Initialize drift detector for testing."""
        self.add_metadata("provider", self.provider)
        self.add_metadata("model", self.model)

    def execute(self) -> None:
        """Execute drift detection - override in subclass."""
        pass

    def validate(self) -> List[tuple]:
        """Validate drift metrics - override in subclass."""
        return []


class ProviderFallbackScenario(SimulationScenario):
    """
    Base class for provider fallback testing scenarios.

    Blueprint Section 5.3: Provider fallback testing
    """

    tags = ["fallback", "provider"]

    def __init__(self, primary_provider: str, fallback_provider: str):
        super().__init__()
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.fallback_triggered: bool = False

    def setup(self) -> None:
        """Initialize providers for testing."""
        self.add_metadata("primary_provider", self.primary_provider)
        self.add_metadata("fallback_provider", self.fallback_provider)

    def execute(self) -> None:
        """Execute fallback scenario - override in subclass."""
        pass

    def validate(self) -> List[tuple]:
        """Validate fallback behavior - override in subclass."""
        return []


class MultiAgentScenario(SimulationScenario):
    """
    Base class for multi-agent E2E testing scenarios.

    Blueprint Section 5.3: Multi-agent E2E testing
    """

    tags = ["multi-agent", "e2e"]

    def __init__(self, agents: List[str]):
        super().__init__()
        self.agents = agents
        self.agent_results: Dict[str, Any] = {}

    def setup(self) -> None:
        """Initialize agents for testing."""
        self.add_metadata("agents", self.agents)

    def execute(self) -> None:
        """Execute multi-agent workflow - override in subclass."""
        pass

    def validate(self) -> List[tuple]:
        """Validate agent interactions - override in subclass."""
        return []
