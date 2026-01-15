"""
EPIC H: Multi-Agent Simulation Suite v1

Blueprint Section 5.3: Multi-Agent Simulation Suite v1
Blueprint Section 5.4: Regression Pipeline v1

This module provides:
- SimulationScenario: Base class for defining test scenarios
- ScenarioRunner: Executes scenarios and collects results
- RegressionCandidate: Schema for regression test candidates
- RegressionPipeline: Automated regression test generation

The Simulation Suite is MorningAI's QA system for:
- Multi-agent E2E testing
- Flow v3 branch testing
- Routing testing
- Safety/compliance testing
- Drift testing
- Provider fallback testing
"""

from simulation.scenario import (
    SimulationScenario,
    ScenarioResult,
    ScenarioStatus,
)
from simulation.runner import ScenarioRunner
from simulation.regression import (
    RegressionCandidate,
    RegressionPriority,
    RegressionCandidateCollector,
    RegressionTestGenerator,
)

__all__ = [
    "SimulationScenario",
    "ScenarioResult",
    "ScenarioStatus",
    "ScenarioRunner",
    "RegressionCandidate",
    "RegressionPriority",
    "RegressionCandidateCollector",
    "RegressionTestGenerator",
]
