"""
Drift-Triggered Retry for LLM Responses

EPIC I-2b: Active Recovery (Blueprint 4.3 - Model Governance Framework v2)
Issue: #3342

This module implements intelligent retry logic that uses a higher-tier model
when drift is detected. It provides:
1. Policy-based retry decisions
2. Cost cap enforcement
3. Task type eligibility filtering
4. Model tier escalation

Design Principles:
- Disabled by default (DRIFT_RETRY_ENABLED=false)
- Cost-conscious (default 2x cost cap)
- Task-aware (only retry high-value tasks)
- Drift-type filtering (excludes unexpected_format)

Usage:
    from governance.drift_retry import get_drift_retry_decision, should_retry_on_drift

    # In LLMClient.generate() after drift detection:
    if drift_result.has_drift:
        decision = should_retry_on_drift(
            drift_result=drift_result,
            task_type="code_generation",
            attempt_count=0,
            original_cost=0.01
        )
        if decision.should_retry:
            # Retry with higher-tier model
            ...
"""

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class RetryModelTier(str, Enum):
    """Model tier selection for retry"""
    SAME = "same"
    HIGHER = "higher"
    HIGHEST = "highest"


@dataclass
class DriftRetryPolicy:
    """
    Policy configuration for drift-triggered retry.

    EPIC I-2b: Configurable via environment variables.
    """
    enabled: bool = False
    max_retries: int = 1
    eligible_drift_types: Set[str] = field(default_factory=lambda: {
        "json_parse_error",
        "schema_violation",
        "empty_response"
    })
    retry_model_tier: RetryModelTier = RetryModelTier.HIGHER
    cost_cap_multiplier: float = 2.0
    eligible_task_types: Set[str] = field(default_factory=lambda: {
        "code_generation",
        "code_review"
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "eligible_drift_types": list(self.eligible_drift_types),
            "retry_model_tier": self.retry_model_tier.value,
            "cost_cap_multiplier": self.cost_cap_multiplier,
            "eligible_task_types": list(self.eligible_task_types),
        }


@dataclass
class RetryDecision:
    """
    Result of retry decision evaluation.

    Contains whether to retry and the reason for the decision.
    """
    should_retry: bool
    reason: str
    retry_model: Optional[str] = None
    retry_provider: Optional[str] = None
    estimated_cost: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            "should_retry": self.should_retry,
            "reason": self.reason,
            "retry_model": self.retry_model,
            "retry_provider": self.retry_provider,
            "estimated_cost": self.estimated_cost,
            "metadata": self.metadata,
        }


MODEL_TIER_ESCALATION = {
    "qwen-14b": "qwen-72b",
    "qwen-turbo": "qwen-plus",
    "qwen-72b": "qwen-max",
    "qwen-plus": "qwen-max",
    "gpt-3.5-turbo": "gpt-4o",
    "gemini-1.5-flash": "gemini-1.5-pro",
    "qwen-max": "qwen-max",
    "gpt-4o": "gpt-4o",
    "gemini-1.5-pro": "gemini-1.5-pro",
}

HIGHEST_TIER_MODELS = {
    "alicloud": "qwen-max",
    "openai": "gpt-4o",
    "gemini": "gemini-1.5-pro",
    "siliconflow": "qwen-max",
}

# Issue #3933: Moved from _estimate_retry_cost() to module level for visibility
# Similar pattern to MODEL_TIER_ESCALATION above
TIER_COST_MULTIPLIERS = {
    "qwen-max": 1.5,
    "gpt-4o": 2.0,
    "gemini-1.5-pro": 1.5,
    "qwen-72b": 1.2,
    "qwen-plus": 1.2,
}


class DriftRetryDecision:
    """
    EPIC I-2b: Drift-Triggered Retry Decision Engine

    Decides whether to retry a request after drift detection.
    """

    def __init__(self, policy: DriftRetryPolicy):
        self.policy = policy
        logger.info(
            f"[DriftRetryDecision] Initialized with policy: {policy.to_dict()}"
        )

    def should_retry(
        self,
        drift_events: List[Any],
        task_type: Optional[str] = None,
        attempt_count: int = 0,
        original_cost: float = 0.0,
        current_model: Optional[str] = None,
        current_provider: Optional[str] = None,
        remaining_timeout: Optional[float] = None
    ) -> RetryDecision:
        """
        Determine if retry should be attempted.

        Safety Guards:
        1. Max retry limit (default: 1)
        2. Eligible drift types only (not unexpected_format)
        3. Cost cap enforcement
        4. Task type eligibility
        """
        if not self.policy.enabled:
            return RetryDecision(
                should_retry=False,
                reason="retry_disabled"
            )

        if attempt_count >= self.policy.max_retries:
            return RetryDecision(
                should_retry=False,
                reason="max_retries_exceeded",
                metadata={"attempt_count": attempt_count, "max_retries": self.policy.max_retries}
            )

        if not drift_events:
            return RetryDecision(
                should_retry=False,
                reason="no_drift_events"
            )

        eligible_events = [
            e for e in drift_events
            if self._get_drift_type(e) in self.policy.eligible_drift_types
        ]

        if not eligible_events:
            drift_types = [self._get_drift_type(e) for e in drift_events]
            return RetryDecision(
                should_retry=False,
                reason="drift_type_not_eligible",
                metadata={"drift_types": drift_types, "eligible_types": list(self.policy.eligible_drift_types)}
            )

        if task_type and task_type not in self.policy.eligible_task_types:
            return RetryDecision(
                should_retry=False,
                reason="task_type_not_eligible",
                metadata={"task_type": task_type, "eligible_types": list(self.policy.eligible_task_types)}
            )

        retry_model, retry_provider = self._select_retry_model(
            current_model, current_provider
        )

        estimated_cost = self._estimate_retry_cost(retry_model, original_cost)
        max_allowed_cost = original_cost * self.policy.cost_cap_multiplier

        if estimated_cost > max_allowed_cost and original_cost > 0:
            return RetryDecision(
                should_retry=False,
                reason="cost_cap_exceeded",
                metadata={
                    "estimated_cost": estimated_cost,
                    "max_allowed_cost": max_allowed_cost,
                    "cost_cap_multiplier": self.policy.cost_cap_multiplier
                }
            )

        logger.info(
            f"[DriftRetryDecision] Approving retry: "
            f"drift_types={[self._get_drift_type(e) for e in eligible_events]}, "
            f"task_type={task_type}, attempt={attempt_count + 1}, "
            f"retry_model={retry_model}"
        )

        return RetryDecision(
            should_retry=True,
            reason="drift_detected_eligible_for_retry",
            retry_model=retry_model,
            retry_provider=retry_provider,
            estimated_cost=estimated_cost,
            metadata={
                "drift_types": [self._get_drift_type(e) for e in eligible_events],
                "task_type": task_type,
                "attempt_count": attempt_count + 1,
                "original_model": current_model,
                "tier_escalation": self.policy.retry_model_tier.value
            }
        )

    def _get_drift_type(self, event: Any) -> str:
        """Extract drift type from event object"""
        if hasattr(event, 'drift_type'):
            drift_type = event.drift_type
            if hasattr(drift_type, 'value'):
                return drift_type.value
            return str(drift_type)
        return "unknown"

    def _select_retry_model(
        self,
        current_model: Optional[str],
        current_provider: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Select model for retry based on tier escalation policy."""
        if not current_model:
            return None, current_provider

        if self.policy.retry_model_tier == RetryModelTier.SAME:
            return current_model, current_provider

        if self.policy.retry_model_tier == RetryModelTier.HIGHEST:
            if current_provider and current_provider in HIGHEST_TIER_MODELS:
                return HIGHEST_TIER_MODELS[current_provider], current_provider
            return current_model, current_provider

        if current_model in MODEL_TIER_ESCALATION:
            return MODEL_TIER_ESCALATION[current_model], current_provider

        return current_model, current_provider

    def _estimate_retry_cost(
        self,
        retry_model: Optional[str],
        original_cost: float
    ) -> float:
        """Estimate cost of retry request."""
        if not retry_model or original_cost <= 0:
            return original_cost

        # Issue #3933: Use module-level constant for visibility
        multiplier = TIER_COST_MULTIPLIERS.get(retry_model, 1.0)
        return original_cost * multiplier


_drift_retry_policy: Optional[DriftRetryPolicy] = None
_drift_retry_decision: Optional[DriftRetryDecision] = None
_drift_retry_lock = threading.Lock()


def get_drift_retry_policy() -> DriftRetryPolicy:
    """Get or create the global DriftRetryPolicy instance (thread-safe)."""
    global _drift_retry_policy

    if _drift_retry_policy is None:
        with _drift_retry_lock:
            if _drift_retry_policy is None:
                try:
                    from common.config.settings import settings

                    drift_types_str = getattr(
                        settings, 'drift_retry_eligible_drift_types',
                        'json_parse_error,schema_violation,empty_response'
                    )
                    eligible_drift_types = {
                        t.strip().lower() for t in drift_types_str.split(',') if t.strip()
                    }

                    task_types_str = getattr(
                        settings, 'drift_retry_eligible_task_types',
                        'code_generation,code_review'
                    )
                    eligible_task_types = {
                        t.strip().lower() for t in task_types_str.split(',') if t.strip()
                    }

                    tier_str = getattr(settings, 'drift_retry_model_tier', 'higher')
                    try:
                        retry_model_tier = RetryModelTier(tier_str.lower())
                    except ValueError:
                        retry_model_tier = RetryModelTier.HIGHER

                    _drift_retry_policy = DriftRetryPolicy(
                        enabled=getattr(settings, 'drift_retry_enabled', False),
                        max_retries=getattr(settings, 'drift_retry_max_retries', 1),
                        eligible_drift_types=eligible_drift_types,
                        retry_model_tier=retry_model_tier,
                        cost_cap_multiplier=getattr(settings, 'drift_retry_cost_cap_multiplier', 2.0),
                        eligible_task_types=eligible_task_types,
                    )
                except ImportError:
                    logger.warning(
                        "[DriftRetryPolicy] Could not import settings, using defaults (disabled)"
                    )
                    _drift_retry_policy = DriftRetryPolicy(enabled=False)
                except Exception as e:
                    logger.warning(
                        f"[DriftRetryPolicy] Initialization error, using defaults (disabled): "
                        f"{type(e).__name__}"
                    )
                    _drift_retry_policy = DriftRetryPolicy(enabled=False)

    return _drift_retry_policy


def get_drift_retry_decision() -> DriftRetryDecision:
    """Get or create the global DriftRetryDecision instance (thread-safe)."""
    global _drift_retry_decision

    if _drift_retry_decision is None:
        with _drift_retry_lock:
            if _drift_retry_decision is None:
                policy = get_drift_retry_policy()
                _drift_retry_decision = DriftRetryDecision(policy)

    return _drift_retry_decision


def should_retry_on_drift(
    drift_events: List[Any],
    task_type: Optional[str] = None,
    attempt_count: int = 0,
    original_cost: float = 0.0,
    current_model: Optional[str] = None,
    current_provider: Optional[str] = None,
    remaining_timeout: Optional[float] = None
) -> RetryDecision:
    """
    Convenience function to check if retry should be attempted.

    This is the main entry point for drift retry decisions.
    """
    decision_engine = get_drift_retry_decision()
    return decision_engine.should_retry(
        drift_events=drift_events,
        task_type=task_type,
        attempt_count=attempt_count,
        original_cost=original_cost,
        current_model=current_model,
        current_provider=current_provider,
        remaining_timeout=remaining_timeout
    )


def reset_drift_retry() -> None:
    """Reset the global drift retry instances (useful for testing)"""
    global _drift_retry_policy, _drift_retry_decision
    with _drift_retry_lock:
        _drift_retry_policy = None
        _drift_retry_decision = None
