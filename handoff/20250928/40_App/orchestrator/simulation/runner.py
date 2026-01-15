"""
Scenario Runner for Simulation Suite

Blueprint Section 5.3: Multi-Agent Simulation Suite v1

Executes simulation scenarios and collects results.
Supports:
- Sequential and parallel execution
- Filtering by tags
- Result aggregation and reporting
- Replay capability
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from simulation.scenario import (
    ScenarioResult,
    ScenarioStatus,
    SimulationScenario,
)

logger = logging.getLogger(__name__)


@dataclass
class SimulationRunResult:
    """
    Aggregated result of a simulation run.

    Attributes:
        run_id: Unique identifier for this run
        total_scenarios: Total number of scenarios executed
        passed: Number of scenarios that passed
        failed: Number of scenarios that failed
        errors: Number of scenarios that errored
        skipped: Number of scenarios that were skipped
        total_duration_ms: Total execution time in milliseconds
        scenario_results: Individual scenario results
        timestamp: When the run started
    """
    run_id: str
    total_scenarios: int
    passed: int
    failed: int
    errors: int
    skipped: int
    total_duration_ms: float
    scenario_results: List[ScenarioResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_scenarios == 0:
            return 0.0
        return (self.passed / self.total_scenarios) * 100

    @property
    def all_passed(self) -> bool:
        """Check if all scenarios passed."""
        return self.failed == 0 and self.errors == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "total_scenarios": self.total_scenarios,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "success_rate": self.success_rate,
            "total_duration_ms": self.total_duration_ms,
            "scenario_results": [r.to_dict() for r in self.scenario_results],
            "timestamp": self.timestamp.isoformat(),
        }

    def get_failed_scenarios(self) -> List[ScenarioResult]:
        """Get list of failed scenario results."""
        return [
            r for r in self.scenario_results
            if r.status in (ScenarioStatus.FAILED, ScenarioStatus.ERROR)
        ]

    def summary(self) -> str:
        """Generate human-readable summary."""
        status = "PASSED" if self.all_passed else "FAILED"
        return (
            f"Simulation Run {self.run_id}: {status}\n"
            f"  Total: {self.total_scenarios}, Passed: {self.passed}, "
            f"Failed: {self.failed}, Errors: {self.errors}, Skipped: {self.skipped}\n"
            f"  Success Rate: {self.success_rate:.1f}%\n"
            f"  Duration: {self.total_duration_ms:.2f}ms"
        )


class ScenarioRunner:
    """
    Executes simulation scenarios and collects results.

    Blueprint Section 5.3: Multi-Agent Simulation Suite v1

    Features:
    - Register scenarios by class or instance
    - Filter scenarios by tags
    - Execute sequentially or in parallel
    - Aggregate results for reporting
    - Support replay of failed scenarios

    Example:
        runner = ScenarioRunner()
        runner.register(FlowBranchScenario("review"))
        runner.register(RoutingScenario("code_gen", "alicloud"))

        result = runner.run_all()
        print(result.summary())

        # Run only routing scenarios
        result = runner.run_by_tags(["routing"])
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize the scenario runner.

        Args:
            max_workers: Maximum number of parallel workers for parallel execution
        """
        self.max_workers = max_workers
        self._scenarios: List[SimulationScenario] = []
        self._run_history: List[SimulationRunResult] = []

    def register(self, scenario: SimulationScenario) -> None:
        """
        Register a scenario instance for execution.

        Args:
            scenario: SimulationScenario instance to register
        """
        self._scenarios.append(scenario)
        logger.debug(
            f"[Simulation] Registered scenario: {scenario.name}",
            extra={"operation": "simulation.runner", "scenario_name": scenario.name}
        )

    def register_class(
        self,
        scenario_class: Type[SimulationScenario],
        *args,
        **kwargs
    ) -> None:
        """
        Register a scenario class (will be instantiated).

        Args:
            scenario_class: SimulationScenario subclass
            *args, **kwargs: Arguments to pass to constructor
        """
        scenario = scenario_class(*args, **kwargs)
        self.register(scenario)

    def clear(self) -> None:
        """Clear all registered scenarios."""
        self._scenarios.clear()

    def get_scenarios_by_tags(self, tags: List[str]) -> List[SimulationScenario]:
        """
        Get scenarios that match any of the given tags.

        Args:
            tags: List of tags to filter by

        Returns:
            List of matching scenarios
        """
        return [
            s for s in self._scenarios
            if any(tag in s.tags for tag in tags)
        ]

    def run_all(self, parallel: bool = False) -> SimulationRunResult:
        """
        Run all registered scenarios.

        Args:
            parallel: If True, run scenarios in parallel

        Returns:
            SimulationRunResult with aggregated results
        """
        return self._run_scenarios(self._scenarios, parallel)

    def run_by_tags(
        self,
        tags: List[str],
        parallel: bool = False
    ) -> SimulationRunResult:
        """
        Run scenarios matching the given tags.

        Args:
            tags: List of tags to filter by
            parallel: If True, run scenarios in parallel

        Returns:
            SimulationRunResult with aggregated results
        """
        scenarios = self.get_scenarios_by_tags(tags)
        return self._run_scenarios(scenarios, parallel)

    def run_single(self, scenario: SimulationScenario) -> ScenarioResult:
        """
        Run a single scenario.

        Args:
            scenario: Scenario to run

        Returns:
            ScenarioResult for the scenario
        """
        return scenario.run()

    def replay_failed(
        self,
        run_result: SimulationRunResult,
        parallel: bool = False
    ) -> SimulationRunResult:
        """
        Replay failed scenarios from a previous run.

        Blueprint Section 5.3: Replayable scenarios

        Args:
            run_result: Previous run result
            parallel: If True, run scenarios in parallel

        Returns:
            SimulationRunResult with replay results
        """
        failed_ids = {r.scenario_id for r in run_result.get_failed_scenarios()}
        scenarios_to_replay = [
            s for s in self._scenarios
            if s.scenario_id in failed_ids
        ]

        if not scenarios_to_replay:
            logger.info(
                "[Simulation] No failed scenarios to replay",
                extra={"operation": "simulation.runner"}
            )
            return SimulationRunResult(
                run_id=f"replay-{run_result.run_id}",
                total_scenarios=0,
                passed=0,
                failed=0,
                errors=0,
                skipped=0,
                total_duration_ms=0,
            )

        return self._run_scenarios(scenarios_to_replay, parallel, prefix="replay-")

    def _run_scenarios(
        self,
        scenarios: List[SimulationScenario],
        parallel: bool = False,
        prefix: str = ""
    ) -> SimulationRunResult:
        """
        Internal method to run a list of scenarios.

        Args:
            scenarios: List of scenarios to run
            parallel: If True, run in parallel
            prefix: Prefix for run_id

        Returns:
            SimulationRunResult with aggregated results
        """
        import uuid

        run_id = f"{prefix}{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        logger.info(
            f"[Simulation] Starting run {run_id} with {len(scenarios)} scenarios "
            f"(parallel={parallel})",
            extra={
                "operation": "simulation.runner",
                "run_id": run_id,
                "scenario_count": len(scenarios),
                "parallel": parallel,
            }
        )

        results: List[ScenarioResult] = []

        if parallel and len(scenarios) > 1:
            results = self._run_parallel(scenarios)
        else:
            results = self._run_sequential(scenarios)

        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000

        # Aggregate results
        passed = sum(1 for r in results if r.status == ScenarioStatus.PASSED)
        failed = sum(1 for r in results if r.status == ScenarioStatus.FAILED)
        errors = sum(1 for r in results if r.status == ScenarioStatus.ERROR)
        skipped = sum(1 for r in results if r.status == ScenarioStatus.SKIPPED)

        run_result = SimulationRunResult(
            run_id=run_id,
            total_scenarios=len(scenarios),
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            total_duration_ms=total_duration_ms,
            scenario_results=results,
        )

        self._run_history.append(run_result)

        logger.info(
            f"[Simulation] Run {run_id} completed: {run_result.summary()}",
            extra={
                "operation": "simulation.runner",
                "run_id": run_id,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": run_result.success_rate,
            }
        )

        return run_result

    def _run_sequential(
        self,
        scenarios: List[SimulationScenario]
    ) -> List[ScenarioResult]:
        """Run scenarios sequentially."""
        results = []
        for scenario in scenarios:
            result = scenario.run()
            results.append(result)
        return results

    def _run_parallel(
        self,
        scenarios: List[SimulationScenario]
    ) -> List[ScenarioResult]:
        """Run scenarios in parallel using ThreadPoolExecutor."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_scenario = {
                executor.submit(scenario.run): scenario
                for scenario in scenarios
            }
            for future in as_completed(future_to_scenario):
                scenario = future_to_scenario[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"[Simulation] Parallel execution error for {scenario.name}: {e}",
                        extra={"operation": "simulation.runner", "error": str(e)}
                    )
                    # Create error result
                    results.append(ScenarioResult(
                        scenario_id=scenario.scenario_id,
                        scenario_name=scenario.name,
                        status=ScenarioStatus.ERROR,
                        duration_ms=0,
                        error_message=str(e),
                    ))
        return results

    def get_run_history(self) -> List[SimulationRunResult]:
        """Get history of all runs."""
        return self._run_history.copy()

    def get_last_run(self) -> Optional[SimulationRunResult]:
        """Get the most recent run result."""
        if self._run_history:
            return self._run_history[-1]
        return None


# Convenience function for quick scenario execution
def run_scenarios(
    scenarios: List[SimulationScenario],
    parallel: bool = False
) -> SimulationRunResult:
    """
    Convenience function to run a list of scenarios.

    Args:
        scenarios: List of scenarios to run
        parallel: If True, run in parallel

    Returns:
        SimulationRunResult with aggregated results
    """
    runner = ScenarioRunner()
    for scenario in scenarios:
        runner.register(scenario)
    return runner.run_all(parallel=parallel)
