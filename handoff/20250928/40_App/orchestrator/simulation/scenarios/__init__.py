"""
Built-in Simulation Scenarios

Blueprint Section 5.3: Multi-Agent Simulation Suite v1

Pre-built scenarios for common testing patterns:
- Flow v3 branch testing
- Routing testing
- Safety/compliance testing
- Drift testing
- Provider fallback testing
- Multi-agent E2E testing
"""

from simulation.scenarios.flow_scenarios import (
    FlowExecutionScenario,
    FlowBranchCoverageScenario,
)
from simulation.scenarios.routing_scenarios import (
    TaskRoutingScenario,
    FallbackRoutingScenario,
)
from simulation.scenarios.safety_scenarios import (
    ContentSafetyScenario,
    PIIScannerScenario,
)
from simulation.scenarios.governance_scenarios import (
    DriftDetectionScenario,
    HealthCheckScenario,
)

__all__ = [
    "FlowExecutionScenario",
    "FlowBranchCoverageScenario",
    "TaskRoutingScenario",
    "FallbackRoutingScenario",
    "ContentSafetyScenario",
    "PIIScannerScenario",
    "DriftDetectionScenario",
    "HealthCheckScenario",
]
