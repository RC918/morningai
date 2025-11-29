#!/usr/bin/env python3
"""
Experiment Manager Module - Phase 5 PR-5

A/B Testing Infrastructure for LLM provider experiments.

Features:
- ExperimentManager for trace_id -> variant assignment
- Deterministic hash-based routing (consistent assignment per trace_id)
- Experiment configurations (gemini_planner_10pct_staging, gemini_reviewer_staging_only)
- Metrics labels: experiment_name, variant
- Staging only - production is no-op

Dependencies:
- PR-1: FailureRecord for tracking experiment failures
- PR-3: agent_eval integration for measuring experiment outcomes
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Environment types
EnvironmentType = Literal["staging", "production", "development", "test"]

# Variant types
VariantType = Literal["control", "treatment"]


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment"""
    name: str
    description: str
    treatment_percent: int  # 0-100, percentage of traffic to treatment
    enabled_environments: List[EnvironmentType]
    treatment_provider: str  # LLM provider for treatment group (e.g., "gemini")
    control_provider: str  # LLM provider for control group (e.g., "openai")
    target_component: str  # Component to experiment on (e.g., "planner", "reviewer")
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    enabled: bool = True


# Pre-defined experiment configurations
EXPERIMENT_CONFIGS: Dict[str, ExperimentConfig] = {
    "gemini_planner_10pct_staging": ExperimentConfig(
        name="gemini_planner_10pct_staging",
        description="Test Gemini as planner LLM on 10% of staging traffic",
        treatment_percent=10,
        enabled_environments=["staging"],
        treatment_provider="gemini",
        control_provider="openai",
        target_component="planner",
        enabled=True
    ),
    "gemini_reviewer_staging_only": ExperimentConfig(
        name="gemini_reviewer_staging_only",
        description="Test Gemini as reviewer LLM on all staging traffic",
        treatment_percent=100,
        enabled_environments=["staging"],
        treatment_provider="gemini",
        control_provider="openai",
        target_component="reviewer",
        enabled=True
    ),
}


class ExperimentManager:
    """
    Manages A/B testing experiments for LLM providers.

    Features:
    - Deterministic hash-based variant assignment
    - Environment-aware experiment activation
    - Metrics integration for experiment tracking
    - Graceful degradation (production is no-op)

    Usage:
        from experiment_manager import ExperimentManager

        manager = ExperimentManager(environment="staging")

        # Get variant for a trace
        variant = manager.get_variant("gemini_planner_10pct_staging", trace_id)

        # Get provider based on experiment
        provider = manager.get_provider_for_experiment(
            "gemini_planner_10pct_staging",
            trace_id
        )
    """

    def __init__(
        self,
        environment: EnvironmentType = "production",
        experiments: Optional[Dict[str, ExperimentConfig]] = None
    ):
        """
        Initialize ExperimentManager

        Args:
            environment: Current environment (staging, production, etc.)
            experiments: Optional custom experiment configs (defaults to EXPERIMENT_CONFIGS)
        """
        self.environment = environment
        self.experiments = experiments or EXPERIMENT_CONFIGS.copy()
        self._assignment_cache: Dict[str, VariantType] = {}

        logger.info(
            f"[ExperimentManager] Initialized with environment={environment}, "
            f"experiments={list(self.experiments.keys())}"
        )

    def is_experiment_active(self, experiment_name: str) -> bool:
        """
        Check if an experiment is active in the current environment

        Args:
            experiment_name: Name of the experiment

        Returns:
            True if experiment is active, False otherwise
        """
        if experiment_name not in self.experiments:
            logger.debug(f"[ExperimentManager] Unknown experiment: {experiment_name}")
            return False

        config = self.experiments[experiment_name]

        if not config.enabled:
            logger.debug(f"[ExperimentManager] Experiment {experiment_name} is disabled")
            return False

        if self.environment not in config.enabled_environments:
            logger.debug(
                f"[ExperimentManager] Experiment {experiment_name} not enabled "
                f"for environment {self.environment}"
            )
            return False

        return True

    def get_variant(
        self,
        experiment_name: str,
        trace_id: str
    ) -> VariantType:
        """
        Get variant assignment for a trace_id

        Uses deterministic hash-based routing for consistent assignment.
        Same trace_id always gets the same variant.

        Args:
            experiment_name: Name of the experiment
            trace_id: Unique trace identifier

        Returns:
            "treatment" or "control"
        """
        if not self.is_experiment_active(experiment_name):
            return "control"

        cache_key = f"{experiment_name}:{trace_id}"
        if cache_key in self._assignment_cache:
            return self._assignment_cache[cache_key]

        config = self.experiments[experiment_name]

        if config.treatment_percent <= 0:
            variant: VariantType = "control"
        elif config.treatment_percent >= 100:
            variant = "treatment"
        else:
            hash_input = f"{experiment_name}:{trace_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            bucket = hash_value % 100
            variant = "treatment" if bucket < config.treatment_percent else "control"

        self._assignment_cache[cache_key] = variant

        logger.info(
            f"[ExperimentManager] Assigned variant={variant} for "
            f"experiment={experiment_name}, trace_id={trace_id}",
            extra={
                "operation": "experiment_assignment",
                "experiment_name": experiment_name,
                "trace_id": trace_id,
                "variant": variant,
                "environment": self.environment
            }
        )

        return variant

    def get_provider_for_experiment(
        self,
        experiment_name: str,
        trace_id: str
    ) -> str:
        """
        Get LLM provider based on experiment variant assignment

        Args:
            experiment_name: Name of the experiment
            trace_id: Unique trace identifier

        Returns:
            Provider name ("openai", "gemini", etc.)
        """
        if not self.is_experiment_active(experiment_name):
            config = self.experiments.get(experiment_name)
            return config.control_provider if config else "openai"

        config = self.experiments[experiment_name]
        variant = self.get_variant(experiment_name, trace_id)

        provider = config.treatment_provider if variant == "treatment" else config.control_provider

        logger.debug(
            f"[ExperimentManager] Provider={provider} for "
            f"experiment={experiment_name}, variant={variant}"
        )

        return provider

    def get_experiment_for_component(
        self,
        component: str,
        trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get active experiment for a component

        Note: Returns the first matching active experiment for the component.
        If multiple experiments target the same component, iteration order determines
        which is returned.

        Args:
            component: Component name (e.g., "planner", "reviewer")
            trace_id: Unique trace identifier

        Returns:
            Dict with experiment_name, variant, provider or None if no active experiment
        """
        for name, config in self.experiments.items():
            if config.target_component == component and self.is_experiment_active(name):
                variant = self.get_variant(name, trace_id)
                provider = config.treatment_provider if variant == "treatment" else config.control_provider

                logger.debug(
                    f"[ExperimentManager] Component={component} assigned to "
                    f"experiment={name}, variant={variant}, provider={provider}"
                )

                return {
                    "experiment_name": name,
                    "variant": variant,
                    "provider": provider,
                    "component": component
                }

        return None

    def get_metrics_labels(
        self,
        experiment_name: str,
        trace_id: str
    ) -> Dict[str, str]:
        """
        Get metrics labels for experiment tracking

        Args:
            experiment_name: Name of the experiment
            trace_id: Unique trace identifier

        Returns:
            Dict with experiment_name, variant labels
        """
        variant = self.get_variant(experiment_name, trace_id)

        return {
            "experiment_name": experiment_name,
            "variant": variant,
            "environment": self.environment
        }

    def register_experiment(self, config: ExperimentConfig) -> None:
        """
        Register a new experiment configuration

        Args:
            config: ExperimentConfig to register
        """
        self.experiments[config.name] = config
        logger.info(f"[ExperimentManager] Registered experiment: {config.name}")

    def list_active_experiments(self) -> List[str]:
        """
        List all active experiments for current environment

        Returns:
            List of active experiment names
        """
        return [
            name for name in self.experiments
            if self.is_experiment_active(name)
        ]

    def get_experiment_summary(self) -> Dict[str, Any]:
        """
        Get summary of all experiments

        Returns:
            Dict with experiment summaries
        """
        summary = {
            "environment": self.environment,
            "total_experiments": len(self.experiments),
            "active_experiments": self.list_active_experiments(),
            "experiments": {}
        }

        for name, config in self.experiments.items():
            summary["experiments"][name] = {
                "enabled": config.enabled,
                "active_in_current_env": self.is_experiment_active(name),
                "treatment_percent": config.treatment_percent,
                "target_component": config.target_component,
                "treatment_provider": config.treatment_provider,
                "control_provider": config.control_provider,
                "enabled_environments": config.enabled_environments
            }

        return summary


# Global experiment manager instance (lazy initialization)
_experiment_manager: Optional[ExperimentManager] = None


def get_experiment_manager(
    environment: Optional[EnvironmentType] = None
) -> ExperimentManager:
    """
    Get or create the global ExperimentManager instance

    Args:
        environment: Environment to use (defaults to settings.environment)

    Returns:
        ExperimentManager instance
    """
    global _experiment_manager

    if _experiment_manager is None:
        if environment is None:
            try:
                from common.config.settings import settings
                environment = getattr(settings, "environment", "production")
            except ImportError:
                environment = "production"

        _experiment_manager = ExperimentManager(environment=environment)

    return _experiment_manager


def reset_experiment_manager() -> None:
    """Reset the global experiment manager (useful for testing)"""
    global _experiment_manager
    _experiment_manager = None


def get_provider_for_component(
    component: str,
    trace_id: str,
    default_provider: str = "openai"
) -> str:
    """
    Convenience function to get provider for a component based on active experiments

    Args:
        component: Component name (e.g., "planner", "reviewer")
        trace_id: Unique trace identifier
        default_provider: Default provider if no experiment is active

    Returns:
        Provider name
    """
    manager = get_experiment_manager()
    experiment_info = manager.get_experiment_for_component(component, trace_id)

    if experiment_info:
        return experiment_info["provider"]

    return default_provider
