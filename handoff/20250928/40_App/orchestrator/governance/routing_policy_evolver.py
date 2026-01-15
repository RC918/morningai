"""
Routing Policy Evolver - EPIC I-4 Self-Evolving Routing

EPIC I-4 Phase B: Self-Evolving Routing Policy

This module implements the routing policy evolution system that automatically
adjusts routing weights and tier assignments based on capability scores and
degradation recommendations.

Key Features:
- Auto-downgrade: Automatically reduce routing weight when score drops >20%
- Flag for review: Flag changes for human review when score changes >10%
- Never auto-upgrade: Improvements require human approval
- Audit trail: All changes are logged and stored for review
- Rollback support: Changes can be reverted if needed

Safety Contract:
- Auto-upgrades are NEVER applied without human approval
- Floor provider protection is always enforced
- All changes are logged with full audit trail
- Dry-run mode available for testing
"""

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis

from memory.memory_integration import save_routing_decision

logger = logging.getLogger(__name__)

# Redis keys for routing policy evolution
ROUTING_CHANGES_KEY = "morningai:routing:changes"
ROUTING_PENDING_KEY = "morningai:routing:pending"
ROUTING_APPLIED_KEY = "morningai:routing:applied"
ROUTING_CHANGES_TTL = 86400 * 30  # 30 days


class ChangeType(Enum):
    """Types of routing policy changes"""
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    TIER_CHANGE = "tier_change"
    PROVIDER_DISABLE = "provider_disable"
    PROVIDER_ENABLE = "provider_enable"


class ChangeStatus(Enum):
    """Status of a routing policy change"""
    PENDING = "pending"  # Awaiting human approval
    APPROVED = "approved"  # Approved by human
    AUTO_APPLIED = "auto_applied"  # Auto-applied (downgrade only)
    REJECTED = "rejected"  # Rejected by human
    ROLLED_BACK = "rolled_back"  # Reverted after application


class ChangeReason(Enum):
    """Reason for the routing policy change"""
    CAPABILITY_SCORE_DROP = "capability_score_drop"
    CAPABILITY_SCORE_IMPROVE = "capability_score_improve"
    DEGRADATION_ADVISORY = "degradation_advisory"
    BENCHMARK_RESULT = "benchmark_result"
    MANUAL_OVERRIDE = "manual_override"


@dataclass
class RoutingPolicyChange:
    """
    Represents a single routing policy change.

    Attributes:
        change_id: Unique identifier for this change
        change_type: Type of change (weight, tier, etc.)
        provider: Affected provider
        model: Affected model (optional)
        task_type: Affected task type (optional)
        old_value: Previous value
        new_value: New value
        reason: Reason for the change
        status: Current status of the change
        auto_applicable: Whether this change can be auto-applied
        score_change_percent: Percentage change in score that triggered this
        created_at: When the change was created
        applied_at: When the change was applied (if applicable)
        approved_by: Who approved the change (if applicable)
    """
    change_id: str
    change_type: ChangeType
    provider: str
    model: Optional[str] = None
    task_type: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    reason: ChangeReason = ChangeReason.CAPABILITY_SCORE_DROP
    status: ChangeStatus = ChangeStatus.PENDING
    auto_applicable: bool = False
    score_change_percent: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    applied_at: Optional[str] = None
    approved_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "provider": self.provider,
            "model": self.model,
            "task_type": self.task_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason.value,
            "status": self.status.value,
            "auto_applicable": self.auto_applicable,
            "score_change_percent": self.score_change_percent,
            "created_at": self.created_at,
            "applied_at": self.applied_at,
            "approved_by": self.approved_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoutingPolicyChange":
        """Create from dictionary"""
        return cls(
            change_id=data["change_id"],
            change_type=ChangeType(data["change_type"]),
            provider=data["provider"],
            model=data.get("model"),
            task_type=data.get("task_type"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            reason=ChangeReason(data.get("reason", "capability_score_drop")),
            status=ChangeStatus(data.get("status", "pending")),
            auto_applicable=data.get("auto_applicable", False),
            score_change_percent=data.get("score_change_percent"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            applied_at=data.get("applied_at"),
            approved_by=data.get("approved_by"),
        )


# Auto-apply thresholds (aligned with CapabilityScoreManager)
AUTO_APPLY_THRESHOLDS = {
    "score_drop_auto_downgrade": 0.20,  # >20% drop = auto-downgrade
    "score_drop_flag_review": 0.10,  # >10% drop = flag for review
    "score_improve_flag_review": 0.10,  # >10% improve = flag for review (never auto)
}

# Weight adjustment factors (aligned with SEVERITY_MULTIPLIERS in degradation_types.py)
# SSOT: These values MUST match SEVERITY_MULTIPLIERS for consistency
WEIGHT_ADJUSTMENTS = {
    "severe_drop": 0.3,  # >20% drop: reduce to CRITICAL (0.3 multiplier)
    "moderate_drop": 0.7,  # 10-20% drop: reduce to DEGRADED (0.7 multiplier)
}


class RoutingPolicyEvolver:
    """
    Evolves routing policy based on capability scores and degradation recommendations.

    EPIC I-4 Phase B: Self-Evolving Routing

    This class manages the evolution of routing policy by:
    1. Monitoring capability score changes
    2. Processing degradation recommendations
    3. Generating routing policy changes
    4. Auto-applying safe changes (downgrades only)
    5. Queuing changes that require human approval

    Safety Contract:
    - Auto-upgrades are NEVER applied without human approval
    - Floor provider protection is always enforced
    - All changes are logged with full audit trail
    - Dry-run mode available for testing

    Attributes:
        enabled: Whether policy evolution is enabled
        dry_run: Whether to run in dry-run mode (no actual changes)
        redis_client: Redis client for state storage
    """

    def __init__(
        self,
        redis_client: Optional["Redis"] = None,
        enabled: bool = True,
        dry_run: bool = True,
        floor_provider: str = "gemini",
    ):
        """
        Initialize Routing Policy Evolver

        Args:
            redis_client: Redis client for state storage
            enabled: Whether policy evolution is enabled
            dry_run: Whether to run in dry-run mode
            floor_provider: Provider that should never be fully disabled
        """
        self.redis_client = redis_client
        self.enabled = enabled
        self.dry_run = dry_run
        self.floor_provider = floor_provider

        self._pending_changes: Dict[str, RoutingPolicyChange] = {}
        self._applied_changes: Dict[str, RoutingPolicyChange] = {}
        self._lock = threading.Lock()

        logger.info(
            f"[RoutingPolicyEvolver] Initialized: enabled={enabled}, "
            f"dry_run={dry_run}, floor_provider={floor_provider}"
        )

    def _get_current_weight(self, provider: str) -> float:
        """
        Get the current routing weight for a provider from DegradationAdvisor.

        Args:
            provider: Provider name

        Returns:
            Current weight (multiplier) for the provider, defaults to 1.0 if unknown
        """
        try:
            from governance.degradation_advisor import get_degradation_advisor
            from governance.degradation_types import SEVERITY_MULTIPLIERS

            advisor = get_degradation_advisor()
            if advisor:
                severity = advisor.get_provider_state(provider)
                if severity is not None:
                    return SEVERITY_MULTIPLIERS.get(severity, 1.0)
        except ImportError:
            logger.debug(
                "[I-4-EVOLVE] DegradationAdvisor not available, "
                "using default weight 1.0"
            )
        except Exception as e:
            logger.warning(f"[I-4-EVOLVE] Error getting current weight: {e}")

        return 1.0  # Default to full weight if unknown

    def evolve_from_capability_scores(
        self,
        capability_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evolve routing policy based on capability score changes.

        EPIC I-4 Phase B: Self-Evolving Routing

        This method processes capability score updates and generates
        routing policy changes as needed.

        Args:
            capability_scores: List of capability score dictionaries with
                              provider, model, task_type, score, previous_score, trend

        Returns:
            Dictionary with evolution results
        """
        if not self.enabled:
            return {"enabled": False}

        changes_generated = 0
        changes_auto_applied = 0
        changes_pending = 0

        for score_data in capability_scores:
            change = self._evaluate_score_change(score_data)
            if change:
                changes_generated += 1

                if change.auto_applicable and not self.dry_run:
                    self._apply_change(change)
                    changes_auto_applied += 1
                else:
                    self._queue_pending_change(change)
                    changes_pending += 1

        result = {
            "enabled": True,
            "dry_run": self.dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scores_evaluated": len(capability_scores),
            "changes_generated": changes_generated,
            "changes_auto_applied": changes_auto_applied,
            "changes_pending": changes_pending,
        }

        logger.info(
            f"[RoutingPolicyEvolver] Evolution complete: "
            f"evaluated={len(capability_scores)}, generated={changes_generated}, "
            f"auto_applied={changes_auto_applied}, pending={changes_pending}",
            extra={
                "operation": "routing_policy_evolution",
                **result,
            }
        )

        return result

    def evolve_from_degradation_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evolve routing policy based on degradation recommendations.

        EPIC I-4 Phase B: Integration with DegradationAdvisor

        Args:
            recommendations: List of degradation recommendation dictionaries

        Returns:
            Dictionary with evolution results
        """
        if not self.enabled:
            return {"enabled": False}

        changes_generated = 0
        changes_auto_applied = 0

        for rec in recommendations:
            change = self._evaluate_degradation_recommendation(rec)
            if change:
                changes_generated += 1

                if change.auto_applicable and not self.dry_run:
                    self._apply_change(change)
                    changes_auto_applied += 1
                else:
                    self._queue_pending_change(change)

        return {
            "enabled": True,
            "dry_run": self.dry_run,
            "recommendations_evaluated": len(recommendations),
            "changes_generated": changes_generated,
            "changes_auto_applied": changes_auto_applied,
        }

    def _evaluate_score_change(
        self,
        score_data: Dict[str, Any],
    ) -> Optional[RoutingPolicyChange]:
        """
        Evaluate a capability score change and generate routing policy change if needed.

        Args:
            score_data: Capability score dictionary

        Returns:
            RoutingPolicyChange if change is needed, None otherwise
        """
        provider = score_data.get("provider", "")
        model = score_data.get("model", "default")
        task_type = score_data.get("task_type", "general")
        current_score = score_data.get("score", 0)
        previous_score = score_data.get("previous_score")
        # Note: trend is available in score_data but not used in current logic

        # Skip if no previous score (first measurement)
        if previous_score is None or previous_score == 0:
            return None

        # Calculate change percentage
        change_percent = (current_score - previous_score) / previous_score

        # Determine if change is needed
        if change_percent < 0:
            # Score dropped
            abs_change = abs(change_percent)

            if abs_change >= AUTO_APPLY_THRESHOLDS["score_drop_auto_downgrade"]:
                # Severe drop: auto-downgrade
                new_weight = WEIGHT_ADJUSTMENTS["severe_drop"]
                auto_applicable = True
                reason = ChangeReason.CAPABILITY_SCORE_DROP

                logger.warning(
                    f"[I-4-EVOLVE] Severe score drop detected: "
                    f"provider={provider}, model={model}, task_type={task_type}, "
                    f"change={change_percent * 100:.1f}%, auto_downgrade=True",
                    extra={
                        "operation": "routing_policy_evolution",
                        "event": "SEVERE_SCORE_DROP",
                        "provider": provider,
                        "model": model,
                        "task_type": task_type,
                        "change_percent": change_percent,
                        "auto_applicable": True,
                    }
                )

            elif abs_change >= AUTO_APPLY_THRESHOLDS["score_drop_flag_review"]:
                # Moderate drop: flag for review
                new_weight = WEIGHT_ADJUSTMENTS["moderate_drop"]
                auto_applicable = False
                reason = ChangeReason.CAPABILITY_SCORE_DROP

                logger.info(
                    f"[I-4-EVOLVE] Moderate score drop detected: "
                    f"provider={provider}, model={model}, task_type={task_type}, "
                    f"change={change_percent * 100:.1f}%, flagged_for_review=True"
                )

            else:
                # Minor drop: no action needed
                return None

        elif change_percent > 0:
            # Score improved
            if change_percent >= AUTO_APPLY_THRESHOLDS["score_improve_flag_review"]:
                # Significant improvement: flag for review (NEVER auto-upgrade)
                new_weight = 1.0  # Potential upgrade to full weight
                auto_applicable = False  # NEVER auto-upgrade
                reason = ChangeReason.CAPABILITY_SCORE_IMPROVE

                logger.info(
                    f"[I-4-EVOLVE] Score improvement detected: "
                    f"provider={provider}, model={model}, task_type={task_type}, "
                    f"change={change_percent * 100:.1f}%, requires_human_approval=True"
                )

            else:
                # Minor improvement: no action needed
                return None

        else:
            # No change
            return None

        # Check floor provider protection
        if provider == self.floor_provider and new_weight < 0.25:
            logger.info(
                f"[I-4-EVOLVE] Floor provider protection: "
                f"provider={provider} is floor provider, capping weight at 0.25"
            )
            new_weight = 0.25

        # Fetch actual current weight from DegradationAdvisor
        old_weight = self._get_current_weight(provider)

        # Generate change ID
        change_id = f"{provider}:{model}:{task_type}:{int(datetime.now(timezone.utc).timestamp())}"

        return RoutingPolicyChange(
            change_id=change_id,
            change_type=ChangeType.WEIGHT_ADJUSTMENT,
            provider=provider,
            model=model,
            task_type=task_type,
            old_value=old_weight,
            new_value=new_weight,
            reason=reason,
            status=ChangeStatus.PENDING if not auto_applicable else ChangeStatus.AUTO_APPLIED,
            auto_applicable=auto_applicable,
            score_change_percent=change_percent,
        )

    def _evaluate_degradation_recommendation(
        self,
        rec: Dict[str, Any],
    ) -> Optional[RoutingPolicyChange]:
        """
        Evaluate a degradation recommendation and generate routing policy change if needed.

        Args:
            rec: Degradation recommendation dictionary

        Returns:
            RoutingPolicyChange if change is needed, None otherwise
        """
        provider = rec.get("provider", "")
        severity = rec.get("severity", "healthy")
        score_multiplier = rec.get("score_multiplier", 1.0)
        is_state_change = rec.get("is_state_change", False)

        # Only process state changes
        if not is_state_change:
            return None

        # Skip healthy state (no change needed)
        if severity == "healthy":
            return None

        # Determine auto-applicability based on severity
        # Downgrades (degraded, critical, avoid) can be auto-applied
        auto_applicable = severity in ("degraded", "critical", "avoid")

        # Check floor provider protection
        if provider == self.floor_provider and score_multiplier < 0.25:
            logger.info(
                f"[I-4-EVOLVE] Floor provider protection: "
                f"provider={provider} is floor provider, capping multiplier at 0.25"
            )
            score_multiplier = 0.25

        # Fetch actual current weight from DegradationAdvisor
        old_weight = self._get_current_weight(provider)

        change_id = f"{provider}:degradation:{int(datetime.now(timezone.utc).timestamp())}"

        return RoutingPolicyChange(
            change_id=change_id,
            change_type=ChangeType.WEIGHT_ADJUSTMENT,
            provider=provider,
            old_value=old_weight,
            new_value=score_multiplier,
            reason=ChangeReason.DEGRADATION_ADVISORY,
            status=ChangeStatus.PENDING if not auto_applicable else ChangeStatus.AUTO_APPLIED,
            auto_applicable=auto_applicable,
        )

    def _apply_change(self, change: RoutingPolicyChange) -> bool:
        """
        Apply a routing policy change.

        Args:
            change: The change to apply

        Returns:
            True if change was applied successfully
        """
        if self.dry_run:
            logger.info(
                f"[I-4-EVOLVE] DRY-RUN: Would apply change {change.change_id}",
                extra={
                    "operation": "routing_policy_apply",
                    "dry_run": True,
                    "change": change.to_dict(),
                }
            )
            return True

        try:
            # Apply the change to routing engine
            self._apply_to_routing_engine(change)

            # Update applied_at timestamp (status is already set by caller)
            change.applied_at = datetime.now(timezone.utc).isoformat()

            # Store in applied changes
            with self._lock:
                self._applied_changes[change.change_id] = change

            # Store in Redis
            self._store_change(change)

            # EPIC G: Save routing decision to Governance Memory
            # This is controlled by ENABLE_MEMORY_V2_GOVERNANCE feature flag (checked internally)
            save_routing_decision(
                decision_id=change.change_id,
                trace_id=f"routing_evolution_{change.change_id}",
                task_type=change.task_type or "general",
                selected_provider=change.provider,
                selected_model=change.model or "default",
                selection_reason=f"{change.reason.value}: weight {change.old_value} -> {change.new_value}",
                candidates=[],
                latency_ms=0.0,
                success=True,
            )

            logger.warning(
                f"[I-4-EVOLVE] Change applied: {change.change_id}",
                extra={
                    "operation": "routing_policy_apply",
                    "change": change.to_dict(),
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"[I-4-EVOLVE] Failed to apply change {change.change_id}: {e}",
                extra={
                    "operation": "routing_policy_apply",
                    "error": str(e),
                    "change": change.to_dict(),
                }
            )
            return False

    def _apply_to_routing_engine(self, change: RoutingPolicyChange) -> None:
        """
        Apply change to the actual routing engine.

        This method updates the routing engine's internal state based on the change.

        Args:
            change: The change to apply
        """
        if change.change_type == ChangeType.WEIGHT_ADJUSTMENT:
            # Update provider weight in DegradationAdvisor state
            # This affects _get_degradation_multiplier() in RoutingEngine
            try:
                from governance.degradation_advisor import get_degradation_advisor
                from governance.degradation_types import DegradationSeverity

                advisor = get_degradation_advisor()
                if advisor:
                    # Map weight to severity
                    weight = change.new_value
                    if weight >= 1.0:
                        severity = DegradationSeverity.HEALTHY
                    elif weight >= 0.7:
                        severity = DegradationSeverity.DEGRADED
                    elif weight >= 0.25:
                        severity = DegradationSeverity.CRITICAL
                    else:
                        severity = DegradationSeverity.AVOID

                    # Update advisor state directly
                    with advisor._lock:
                        advisor._provider_states[change.provider] = severity

                    logger.info(
                        f"[I-4-EVOLVE] Updated DegradationAdvisor state: "
                        f"provider={change.provider}, severity={severity.value}, weight={weight}"
                    )

            except ImportError:
                logger.warning(
                    "[I-4-EVOLVE] DegradationAdvisor not available, "
                    "change applied to local state only"
                )

    def _queue_pending_change(self, change: RoutingPolicyChange) -> None:
        """
        Queue a change for human approval.

        Args:
            change: The change to queue
        """
        change.status = ChangeStatus.PENDING

        with self._lock:
            self._pending_changes[change.change_id] = change

        # Store in Redis
        self._store_pending_change(change)

        logger.info(
            f"[I-4-EVOLVE] Change queued for approval: {change.change_id}",
            extra={
                "operation": "routing_policy_queue",
                "change": change.to_dict(),
            }
        )

    def approve_change(
        self,
        change_id: str,
        approved_by: str = "human",
    ) -> bool:
        """
        Approve and apply a pending change.

        Args:
            change_id: ID of the change to approve
            approved_by: Who approved the change

        Returns:
            True if change was approved and applied successfully
        """
        with self._lock:
            change = self._pending_changes.get(change_id)

        if not change:
            logger.warning(f"[I-4-EVOLVE] Change not found: {change_id}")
            return False

        change.status = ChangeStatus.APPROVED
        change.approved_by = approved_by

        # Apply the change
        success = self._apply_change(change)

        if success:
            # Remove from pending
            with self._lock:
                self._pending_changes.pop(change_id, None)

        return success

    def reject_change(
        self,
        change_id: str,
        rejected_by: str = "human",
    ) -> bool:
        """
        Reject a pending change.

        Args:
            change_id: ID of the change to reject
            rejected_by: Who rejected the change

        Returns:
            True if change was rejected successfully
        """
        with self._lock:
            change = self._pending_changes.get(change_id)

        if not change:
            logger.warning(f"[I-4-EVOLVE] Change not found: {change_id}")
            return False

        change.status = ChangeStatus.REJECTED

        # Remove from pending
        with self._lock:
            self._pending_changes.pop(change_id, None)

        # Store rejection
        self._store_change(change)

        logger.info(
            f"[I-4-EVOLVE] Change rejected: {change_id} by {rejected_by}",
            extra={
                "operation": "routing_policy_reject",
                "change": change.to_dict(),
            }
        )

        return True

    def rollback_change(self, change_id: str) -> bool:
        """
        Rollback an applied change.

        Args:
            change_id: ID of the change to rollback

        Returns:
            True if change was rolled back successfully
        """
        with self._lock:
            change = self._applied_changes.get(change_id)

        if not change:
            logger.warning(f"[I-4-EVOLVE] Applied change not found: {change_id}")
            return False

        # Create reverse change
        reverse_change = RoutingPolicyChange(
            change_id=f"{change_id}:rollback",
            change_type=change.change_type,
            provider=change.provider,
            model=change.model,
            task_type=change.task_type,
            old_value=change.new_value,
            new_value=change.old_value,
            reason=ChangeReason.MANUAL_OVERRIDE,
            auto_applicable=True,
        )

        # Apply reverse change
        success = self._apply_change(reverse_change)

        if success:
            change.status = ChangeStatus.ROLLED_BACK
            self._store_change(change)

            logger.info(
                f"[I-4-EVOLVE] Change rolled back: {change_id}",
                extra={
                    "operation": "routing_policy_rollback",
                    "change": change.to_dict(),
                }
            )

        return success

    def get_pending_changes(self) -> List[RoutingPolicyChange]:
        """Get all pending changes awaiting approval"""
        with self._lock:
            return list(self._pending_changes.values())

    def get_applied_changes(self) -> List[RoutingPolicyChange]:
        """Get all applied changes"""
        with self._lock:
            return list(self._applied_changes.values())

    def _store_change(self, change: RoutingPolicyChange) -> bool:
        """Store change in Redis"""
        if not self.redis_client:
            return False

        try:
            key = f"{ROUTING_CHANGES_KEY}:{change.change_id}"
            self.redis_client.setex(
                key,
                ROUTING_CHANGES_TTL,
                json.dumps(change.to_dict()),
            )
            return True
        except Exception as e:
            logger.warning(f"[I-4-EVOLVE] Failed to store change: {e}")
            return False

    def _store_pending_change(self, change: RoutingPolicyChange) -> bool:
        """Store pending change in Redis"""
        if not self.redis_client:
            return False

        try:
            self.redis_client.hset(
                ROUTING_PENDING_KEY,
                change.change_id,
                json.dumps(change.to_dict()),
            )
            return True
        except Exception as e:
            logger.warning(f"[I-4-EVOLVE] Failed to store pending change: {e}")
            return False


# Global instance
_routing_policy_evolver: Optional[RoutingPolicyEvolver] = None
_evolver_lock = threading.Lock()


def get_routing_policy_evolver(
    redis_client: Optional["Redis"] = None,
) -> Optional[RoutingPolicyEvolver]:
    """
    Get or create global RoutingPolicyEvolver instance.

    EPIC I-4 Phase B: Self-Evolving Routing

    Returns:
        RoutingPolicyEvolver instance or None if not enabled
    """
    global _routing_policy_evolver

    if _routing_policy_evolver is not None:
        return _routing_policy_evolver

    with _evolver_lock:
        if _routing_policy_evolver is not None:
            return _routing_policy_evolver

        try:
            import os

            enabled = os.getenv("ROUTING_POLICY_EVOLUTION_ENABLED", "false").lower() == "true"
            dry_run = os.getenv("ROUTING_POLICY_EVOLUTION_DRY_RUN", "true").lower() == "true"
            floor_provider = os.getenv("ROUTING_FLOOR_PROVIDER", "openai")

            if not enabled:
                logger.debug("[RoutingPolicyEvolver] Policy evolution disabled")
                return None

            _routing_policy_evolver = RoutingPolicyEvolver(
                redis_client=redis_client,
                enabled=enabled,
                dry_run=dry_run,
                floor_provider=floor_provider,
            )

            logger.info("[RoutingPolicyEvolver] Initialized global instance")
            return _routing_policy_evolver

        except Exception as e:
            logger.warning(f"[RoutingPolicyEvolver] Failed to initialize: {e}")
            return None


def reset_routing_policy_evolver() -> None:
    """Reset the global RoutingPolicyEvolver singleton (for testing)"""
    global _routing_policy_evolver
    with _evolver_lock:
        _routing_policy_evolver = None
