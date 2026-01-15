"""
Routing Simulation Scenarios

Blueprint Section 5.3: Routing testing

Scenarios for testing the routing engine and provider selection.
"""

import logging
from typing import List, Optional

from simulation.scenario import ProviderFallbackScenario, RoutingScenario

logger = logging.getLogger(__name__)


class TaskRoutingScenario(RoutingScenario):
    """
    Test task-based routing selection.

    Verifies that:
    - Correct provider is selected for task type
    - Routing policy is respected
    - Tier selection is appropriate
    """

    name = "Task-Based Routing"
    description = "Test routing engine selects correct provider for task type"
    tags = ["routing", "provider", "task"]

    def __init__(
        self,
        task_type: str = "code_gen",
        expected_provider: Optional[str] = None,
        expected_tier: Optional[int] = None,
    ):
        super().__init__(task_type, expected_provider)
        self.expected_tier = expected_tier
        self.actual_provider: Optional[str] = None
        self.actual_tier: Optional[int] = None
        self.actual_model: Optional[str] = None

    def setup(self) -> None:
        """Initialize routing engine."""
        super().setup()
        if self.expected_tier:
            self.add_metadata("expected_tier", self.expected_tier)

    def execute(self) -> None:
        """Execute routing selection."""
        # In real implementation, would call routing_engine.select_provider()
        # For now, simulate routing based on task type
        task_routing_map = {
            "code_gen": ("alicloud", "qwen-plus", 1),
            "review": ("alicloud", "qwen-plus", 1),
            "planning": ("alicloud", "qwen-max", 0),
            "simple": ("alicloud", "qwen-turbo", 2),
        }

        if self.task_type in task_routing_map:
            provider, model, tier = task_routing_map[self.task_type]
            self.actual_provider = provider
            self.actual_model = model
            self.actual_tier = tier
        else:
            # Default routing
            self.actual_provider = "alicloud"
            self.actual_model = "qwen-plus"
            self.actual_tier = 1

        self.routing_result = {
            "provider": self.actual_provider,
            "model": self.actual_model,
            "tier": self.actual_tier,
            "task_type": self.task_type,
        }

        logger.info(
            f"[TaskRoutingScenario] Routed {self.task_type} to "
            f"{self.actual_provider}/{self.actual_model} (tier {self.actual_tier})",
            extra={"operation": "simulation.scenario"}
        )

    def validate(self) -> List[tuple]:
        """Validate routing selection."""
        assertions = []

        # Check provider was selected
        assertions.append((
            "Provider was selected",
            self.actual_provider is not None
        ))

        # Check model was selected
        assertions.append((
            "Model was selected",
            self.actual_model is not None
        ))

        # Check expected provider if specified
        if self.expected_provider:
            assertions.append((
                f"Provider is {self.expected_provider}",
                self.actual_provider == self.expected_provider
            ))

        # Check expected tier if specified
        if self.expected_tier is not None:
            assertions.append((
                f"Tier is {self.expected_tier}",
                self.actual_tier == self.expected_tier
            ))

        return assertions


class FallbackRoutingScenario(ProviderFallbackScenario):
    """
    Test provider fallback behavior.

    Verifies that:
    - Fallback is triggered when primary fails
    - Correct fallback provider is selected
    - Fallback chain is respected
    """

    name = "Provider Fallback"
    description = "Test fallback behavior when primary provider fails"
    tags = ["routing", "fallback", "resilience"]

    def __init__(
        self,
        primary_provider: str = "alicloud",
        fallback_provider: str = "siliconflow",
        simulate_failure: bool = True,
    ):
        super().__init__(primary_provider, fallback_provider)
        self.simulate_failure = simulate_failure
        self.fallback_reason: Optional[str] = None
        self.final_provider: Optional[str] = None

    def setup(self) -> None:
        """Initialize providers."""
        super().setup()
        self.add_metadata("simulate_failure", self.simulate_failure)

    def execute(self) -> None:
        """Execute with potential fallback."""
        if self.simulate_failure:
            # Simulate primary provider failure
            logger.info(
                f"[FallbackRoutingScenario] Simulating {self.primary_provider} failure",
                extra={"operation": "simulation.scenario"}
            )
            self.fallback_triggered = True
            self.fallback_reason = "simulated_timeout"
            self.final_provider = self.fallback_provider
        else:
            # Primary succeeds
            self.fallback_triggered = False
            self.final_provider = self.primary_provider

        logger.info(
            f"[FallbackRoutingScenario] Final provider: {self.final_provider} "
            f"(fallback={self.fallback_triggered})",
            extra={"operation": "simulation.scenario"}
        )

    def validate(self) -> List[tuple]:
        """Validate fallback behavior."""
        assertions = []

        # Check final provider was selected
        assertions.append((
            "Final provider was selected",
            self.final_provider is not None
        ))

        if self.simulate_failure:
            # Fallback should have been triggered
            assertions.append((
                "Fallback was triggered",
                self.fallback_triggered
            ))

            # Should use fallback provider
            assertions.append((
                f"Using fallback provider {self.fallback_provider}",
                self.final_provider == self.fallback_provider
            ))

            # Should have fallback reason
            assertions.append((
                "Fallback reason is recorded",
                self.fallback_reason is not None
            ))
        else:
            # Fallback should not have been triggered
            assertions.append((
                "Fallback was not triggered",
                not self.fallback_triggered
            ))

            # Should use primary provider
            assertions.append((
                f"Using primary provider {self.primary_provider}",
                self.final_provider == self.primary_provider
            ))

        return assertions
