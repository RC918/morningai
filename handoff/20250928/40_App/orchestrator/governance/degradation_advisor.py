"""
Degradation Advisor - EPIC I-4 Auto-Degradation Decision Engine

EPIC I-4 Phase A: Immune Decision Engine (Observe-Only)

This module implements the degradation advisory system that monitors provider
health scores and generates recommendations for routing weight adjustments.

Phase A is observe-only: recommendations are logged but not applied to routing.
Phase B (future) will apply recommendations to the routing engine.

Key Features:
- Threshold-based severity calculation
- Hysteresis to prevent oscillation
- Floor provider protection
- Cooldown mechanism
- Minimum sample size guard

Safety Contract:
- Phase A MUST NOT modify any routing behavior
- All operations are wrapped in try/except
- Failures are logged but never block the main service
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from .degradation_types import (
    DegradationSeverity,
    DegradationRecommendation,
    SEVERITY_MULTIPLIERS,
)

logger = logging.getLogger(__name__)


class DegradationPolicy:
    """
    Pure decision logic for degradation recommendations

    EPIC I-4 Phase A: Immune Decision Engine

    This class is stateless and computes severity based on health scores.
    It implements hysteresis to prevent rapid oscillation between states.

    Thresholds (0-100 scale):
    - HEALTHY: health_score >= 75
    - DEGRADED: health_score >= 50
    - CRITICAL: health_score >= 25
    - AVOID: health_score < 25

    Hysteresis (recovery requires higher score):
    - DEGRADED -> HEALTHY: requires >= 85 (not just >= 75)
    - CRITICAL -> DEGRADED: requires >= 60 (not just >= 50)
    - AVOID -> CRITICAL: requires >= 35 (not just >= 25)
    """

    def __init__(
        self,
        healthy_threshold: float = 75.0,
        degraded_threshold: float = 50.0,
        critical_threshold: float = 25.0,
        recovery_buffer: float = 10.0,
    ):
        """
        Initialize degradation policy

        Args:
            healthy_threshold: Health score threshold for HEALTHY status
            degraded_threshold: Health score threshold for DEGRADED status
            critical_threshold: Health score threshold for CRITICAL status
            recovery_buffer: Additional score required for recovery (hysteresis)
        """
        self.healthy_threshold = healthy_threshold
        self.degraded_threshold = degraded_threshold
        self.critical_threshold = critical_threshold
        self.recovery_buffer = recovery_buffer

    def compute_severity(
        self,
        health_score: float,
        current_severity: Optional[DegradationSeverity] = None
    ) -> DegradationSeverity:
        """
        Compute severity level based on health score with hysteresis

        Args:
            health_score: Health score (0-100 scale)
            current_severity: Current severity level (for hysteresis)

        Returns:
            Computed severity level
        """
        # If no current severity, use simple threshold logic
        if current_severity is None:
            return self._compute_severity_simple(health_score)

        # Apply hysteresis: recovery requires higher score than degradation
        if current_severity == DegradationSeverity.AVOID:
            # AVOID -> CRITICAL requires score >= critical_threshold + buffer
            if health_score >= self.critical_threshold + self.recovery_buffer:
                return self._compute_severity_simple(health_score)
            return DegradationSeverity.AVOID

        elif current_severity == DegradationSeverity.CRITICAL:
            # CRITICAL -> DEGRADED requires score >= degraded_threshold + buffer
            if health_score >= self.degraded_threshold + self.recovery_buffer:
                return self._compute_severity_simple(health_score)
            # Can still degrade further to AVOID
            if health_score < self.critical_threshold:
                return DegradationSeverity.AVOID
            return DegradationSeverity.CRITICAL

        elif current_severity == DegradationSeverity.DEGRADED:
            # DEGRADED -> HEALTHY requires score >= healthy_threshold + buffer
            if health_score >= self.healthy_threshold + self.recovery_buffer:
                return DegradationSeverity.HEALTHY
            # Can still degrade further
            if health_score < self.critical_threshold:
                return DegradationSeverity.AVOID
            if health_score < self.degraded_threshold:
                return DegradationSeverity.CRITICAL
            return DegradationSeverity.DEGRADED

        else:  # HEALTHY
            # HEALTHY -> DEGRADED at threshold (no hysteresis for degradation)
            return self._compute_severity_simple(health_score)

    def _compute_severity_simple(self, health_score: float) -> DegradationSeverity:
        """Compute severity without hysteresis (simple threshold logic)"""
        if health_score >= self.healthy_threshold:
            return DegradationSeverity.HEALTHY
        elif health_score >= self.degraded_threshold:
            return DegradationSeverity.DEGRADED
        elif health_score >= self.critical_threshold:
            return DegradationSeverity.CRITICAL
        else:
            return DegradationSeverity.AVOID

    def get_multiplier(self, severity: DegradationSeverity) -> float:
        """Get score multiplier for a severity level"""
        return SEVERITY_MULTIPLIERS.get(severity, 1.0)

    def determine_reason(
        self,
        health_data: Dict[str, Any],
        severity: DegradationSeverity
    ) -> str:
        """
        Determine the primary reason for the severity level

        Args:
            health_data: Health data from CanaryMetrics
            severity: Computed severity level

        Returns:
            Human-readable reason string
        """
        if severity == DegradationSeverity.HEALTHY:
            return "all_metrics_normal"

        reasons = []

        # Check error rate (0-100 scale)
        error_rate = health_data.get("error_rate", 0)
        if error_rate >= 10.0:
            reasons.append(f"error_rate_spike ({error_rate:.1f}% >= 10.0%)")
        elif error_rate >= 5.0:
            reasons.append(f"elevated_error_rate ({error_rate:.1f}%)")

        # Check drift rate (0-100 scale)
        drift_rate = health_data.get("drift_rate", 0)
        if drift_rate >= 10.0:
            reasons.append(f"drift_rate_spike ({drift_rate:.1f}% >= 10.0%)")
        elif drift_rate >= 5.0:
            reasons.append(f"elevated_drift_rate ({drift_rate:.1f}%)")

        # Check latency
        latency = health_data.get("latency", {})
        p95_ms = latency.get("p95_ms")
        if p95_ms is not None and p95_ms > 5000:
            reasons.append(f"high_latency (p95={p95_ms:.0f}ms)")

        # Check health score directly
        health_score = health_data.get("health_score", 100)
        if not reasons:
            reasons.append(f"low_health_score ({health_score:.1f})")

        return "; ".join(reasons)


class DegradationAdvisor:
    """
    Service layer for degradation advisory

    EPIC I-4 Phase A: Immune Decision Engine (Observe-Only)

    This class manages state, cooldown, and floor provider protection.
    It integrates with CanaryMetrics for health data and outputs
    [I-4-ADVISORY] log messages.

    Floor Strategy (Hybrid):
    - fixed: Always use fixed_floor_provider
    - dynamic: Select healthiest provider as floor
    - hybrid: Dynamic with stickiness and fallback (recommended)

    Safety Contract:
    - Phase A: dry_run=True always, no routing modifications
    - Notification failures are logged but never block
    - All operations are wrapped in try/except
    """

    def __init__(
        self,
        enabled: bool = False,
        cooldown_minutes: int = 15,
        min_requests: int = 10,
        floor_provider_count: int = 1,
        healthy_threshold: float = 75.0,
        degraded_threshold: float = 50.0,
        critical_threshold: float = 25.0,
        recovery_buffer: float = 10.0,
        floor_strategy: str = "hybrid",
        fixed_floor_provider: str = "openai",
        floor_switch_margin: float = 10.0,
        floor_min_requests: int = 10,
    ):
        """
        Initialize Degradation Advisor

        Args:
            enabled: Whether advisory is enabled
            cooldown_minutes: Minimum time between advisories for same provider
            min_requests: Minimum requests in window before advisory
            floor_provider_count: Minimum providers to keep at non-AVOID status
            healthy_threshold: Health score threshold for HEALTHY
            degraded_threshold: Health score threshold for DEGRADED
            critical_threshold: Health score threshold for CRITICAL
            recovery_buffer: Additional score required for recovery (hysteresis)
            floor_strategy: Floor selection strategy ('fixed', 'dynamic', 'hybrid')
            fixed_floor_provider: Provider to use for 'fixed' strategy or fallback
            floor_switch_margin: Score margin required to switch floor in 'hybrid'
            floor_min_requests: Minimum requests for floor candidate eligibility
        """
        self.enabled = enabled
        self.cooldown_minutes = cooldown_minutes
        self.min_requests = min_requests
        self.floor_provider_count = floor_provider_count
        self.floor_strategy = floor_strategy
        self.fixed_floor_provider = fixed_floor_provider
        self.floor_switch_margin = floor_switch_margin
        self.floor_min_requests = floor_min_requests

        self._policy = DegradationPolicy(
            healthy_threshold=healthy_threshold,
            degraded_threshold=degraded_threshold,
            critical_threshold=critical_threshold,
            recovery_buffer=recovery_buffer,
        )

        # State tracking
        self._provider_states: Dict[str, DegradationSeverity] = {}
        self._last_advisory_time: Dict[str, datetime] = {}
        self._current_floor_provider: Optional[str] = None
        self._lock = threading.Lock()

        logger.info(
            f"[DegradationAdvisor] Initialized: enabled={enabled}, "
            f"cooldown={cooldown_minutes}min, min_requests={min_requests}, "
            f"floor_providers={floor_provider_count}, floor_strategy={floor_strategy}"
        )

    def compute_advisory(
        self,
        provider: str,
        health_data: Dict[str, Any]
    ) -> Optional[DegradationRecommendation]:
        """
        Compute degradation advisory for a provider

        EPIC I-4 Phase A: Observe-Only

        Args:
            provider: Provider name
            health_data: Health data from CanaryMetrics.get_provider_health()

        Returns:
            DegradationRecommendation if advisory should be logged, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Extract metrics
            health_score = health_data.get("health_score")
            total_requests = health_data.get("total_requests", 0)

            # Skip if no health score
            if health_score is None:
                logger.debug(f"[DegradationAdvisor] No health score for {provider}")
                return None

            # Skip if insufficient data
            if total_requests < self.min_requests:
                logger.debug(
                    f"[DegradationAdvisor] Insufficient requests for {provider}: "
                    f"{total_requests} < {self.min_requests}"
                )
                return None

            # Get current state
            with self._lock:
                current_severity = self._provider_states.get(provider)

            # Compute new severity with hysteresis
            new_severity = self._policy.compute_severity(health_score, current_severity)

            # Check if this is a state change
            is_state_change = current_severity != new_severity

            # Only log on state change or if in cooldown check
            if not is_state_change and self._is_in_cooldown(provider):
                return None

            # Determine reason
            reason = self._policy.determine_reason(health_data, new_severity)

            # Get multiplier
            multiplier = self._policy.get_multiplier(new_severity)

            # Create recommendation
            recommendation = DegradationRecommendation(
                provider=provider,
                severity=new_severity,
                score_multiplier=multiplier,
                health_score=health_score,
                health_score_normalized=health_score / 100.0,
                reason=reason,
                dry_run=True,  # Phase A: always dry-run
                floor_protected=False,
                previous_severity=current_severity,
            )

            # Update state
            with self._lock:
                self._provider_states[provider] = new_severity
                self._last_advisory_time[provider] = datetime.now(timezone.utc)

            return recommendation

        except Exception as e:
            logger.warning(f"[DegradationAdvisor] Error computing advisory for {provider}: {e}")
            return None

    def compute_all_advisories(
        self,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compute advisories for all providers with floor protection

        EPIC I-4 Phase A: Observe-Only

        This method checks all providers and applies floor protection to ensure
        at least floor_provider_count providers remain usable.

        Args:
            providers: List of provider names (default: all known providers)

        Returns:
            Dict with advisories and summary
        """
        if not self.enabled:
            return {"enabled": False}

        if providers is None:
            providers = ["openai", "gemini", "alicloud", "siliconflow"]

        try:
            from metrics import get_canary_metrics

            metrics = get_canary_metrics()
            if metrics is None:
                logger.debug("[DegradationAdvisor] CanaryMetrics not available")
                return {"enabled": True, "error": "metrics_unavailable"}

            # Get health data for all providers
            all_health = metrics.get_all_providers_health(providers=providers)
            if not all_health.get("enabled", False):
                return {"enabled": True, "error": "metrics_disabled"}

            providers_health = all_health.get("providers", {})

            # Compute initial advisories
            advisories: Dict[str, DegradationRecommendation] = {}
            for provider in providers:
                health_data = providers_health.get(provider, {})
                if isinstance(health_data, dict) and "health_score" in health_data:
                    # Flatten health_data for compute_advisory
                    flat_health = {
                        "health_score": health_data.get("health_score"),
                        "total_requests": health_data.get("metrics", {}).get("total_requests", 0),
                        "error_rate": health_data.get("metrics", {}).get("error_rate", 0),
                        "drift_rate": health_data.get("metrics", {}).get("drift_rate", 0),
                        "latency": health_data.get("metrics", {}).get("latency", {}),
                    }
                    advisory = self.compute_advisory(provider, flat_health)
                    if advisory:
                        advisories[provider] = advisory

            # Apply floor protection
            advisories = self._apply_floor_protection(advisories, providers_health)

            # Log advisories
            logged_count = 0
            for provider, advisory in advisories.items():
                if advisory.is_state_change:
                    logger.warning(
                        f"[I-4-ADVISORY] {advisory.format_state_change_log()}"
                    )
                    logged_count += 1
                elif advisory.severity != DegradationSeverity.HEALTHY:
                    logger.info(f"[I-4-ADVISORY] {advisory.format_log()}")
                    logged_count += 1

            return {
                "enabled": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "providers_checked": list(providers),
                "advisories": {p: a.to_dict() for p, a in advisories.items()},
                "advisories_logged": logged_count,
            }

        except Exception as e:
            logger.warning(f"[DegradationAdvisor] Error computing all advisories: {e}")
            return {"enabled": True, "error": str(e)}

    def _select_floor_provider(
        self,
        providers_health: Dict[str, Any],
        allowed_providers: Optional[List[str]] = None
    ) -> str:
        """
        Select floor provider based on configured strategy

        EPIC I-4 Phase A: Hybrid Floor Strategy

        Strategies:
        - fixed: Always return fixed_floor_provider
        - dynamic: Return healthiest provider with sufficient requests
        - hybrid: Dynamic with stickiness and fallback

        Args:
            providers_health: Health data for all providers
            allowed_providers: List of allowed providers (from ROUTING_ALLOWED_PROVIDERS)

        Returns:
            Selected floor provider name
        """
        # Fixed strategy: always use configured provider
        if self.floor_strategy == "fixed":
            logger.debug(
                f"[I-4-ADVISORY] Floor strategy=fixed, using {self.fixed_floor_provider}"
            )
            return self.fixed_floor_provider

        # Build list of eligible candidates
        candidates: List[tuple] = []  # (provider, health_score, total_requests)
        for provider, health_data in providers_health.items():
            if not isinstance(health_data, dict):
                continue

            # Filter by allowed providers if specified
            if allowed_providers and provider not in allowed_providers:
                continue

            health_score = health_data.get("health_score", 0)
            metrics = health_data.get("metrics", {})
            total_requests = metrics.get("total_requests", 0)

            # Filter by minimum requests
            if total_requests < self.floor_min_requests:
                logger.debug(
                    f"[I-4-ADVISORY] {provider} excluded from floor candidates: "
                    f"requests={total_requests} < min={self.floor_min_requests}"
                )
                continue

            candidates.append((provider, health_score, total_requests))

        # No valid candidates: fallback to fixed provider
        if not candidates:
            logger.info(
                f"[I-4-ADVISORY] No valid floor candidates, "
                f"falling back to {self.fixed_floor_provider}"
            )
            return self.fixed_floor_provider

        # Sort by health score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate, best_score, _ = candidates[0]

        # Dynamic strategy: always pick healthiest
        if self.floor_strategy == "dynamic":
            with self._lock:
                self._current_floor_provider = best_candidate
            logger.debug(
                f"[I-4-ADVISORY] Floor strategy=dynamic, "
                f"selected {best_candidate} (score={best_score:.1f})"
            )
            return best_candidate

        # Hybrid strategy: apply stickiness
        with self._lock:
            current_floor = self._current_floor_provider

        # If no current floor, use best candidate
        if current_floor is None:
            with self._lock:
                self._current_floor_provider = best_candidate
            logger.info(
                f"[I-4-ADVISORY] Floor strategy=hybrid, "
                f"initial floor={best_candidate} (score={best_score:.1f})"
            )
            return best_candidate

        # Find current floor's score
        current_score = 0.0
        for provider, score, _ in candidates:
            if provider == current_floor:
                current_score = score
                break

        # Check if current floor is still valid (in candidates)
        current_in_candidates = any(p == current_floor for p, _, _ in candidates)

        if not current_in_candidates:
            # Current floor no longer valid, switch to best
            with self._lock:
                self._current_floor_provider = best_candidate
            logger.info(
                f"[I-4-ADVISORY] Floor strategy=hybrid, "
                f"current floor {current_floor} no longer valid, "
                f"switching to {best_candidate} (score={best_score:.1f})"
            )
            return best_candidate

        # Apply stickiness: only switch if best exceeds current by margin
        if best_candidate != current_floor:
            if best_score > current_score + self.floor_switch_margin:
                with self._lock:
                    self._current_floor_provider = best_candidate
                logger.info(
                    f"[I-4-ADVISORY] Floor strategy=hybrid, "
                    f"switching floor from {current_floor} (score={current_score:.1f}) "
                    f"to {best_candidate} (score={best_score:.1f}, "
                    f"margin={best_score - current_score:.1f} > {self.floor_switch_margin})"
                )
                return best_candidate
            else:
                logger.debug(
                    f"[I-4-ADVISORY] Floor strategy=hybrid, "
                    f"keeping {current_floor} (score={current_score:.1f}), "
                    f"candidate {best_candidate} (score={best_score:.1f}) "
                    f"margin={best_score - current_score:.1f} <= {self.floor_switch_margin}"
                )
                return current_floor

        return current_floor

    def _apply_floor_protection(
        self,
        advisories: Dict[str, DegradationRecommendation],
        providers_health: Dict[str, Any]
    ) -> Dict[str, DegradationRecommendation]:
        """
        Apply floor protection to ensure minimum usable providers

        EPIC I-4 Phase A: Floor Provider Protection with Hybrid Strategy

        This ensures at least floor_provider_count providers are not set to AVOID.
        Uses the configured floor_strategy to select which providers to protect.

        Args:
            advisories: Computed advisories
            providers_health: Health data for all providers

        Returns:
            Advisories with floor protection applied
        """
        if self.floor_provider_count <= 0:
            return advisories

        # Get allowed providers from settings
        allowed_providers: Optional[List[str]] = None
        try:
            from common.config.settings import settings
            allowed_str = getattr(settings, "routing_allowed_providers", None)
            if allowed_str:
                allowed_providers = [p.strip() for p in allowed_str.split(",") if p.strip()]
        except Exception:
            pass

        # Select floor provider using configured strategy
        floor_provider = self._select_floor_provider(providers_health, allowed_providers)

        # Count providers that would be AVOID
        avoid_providers = [
            p for p, a in advisories.items()
            if a.severity == DegradationSeverity.AVOID
        ]

        # Check if we need floor protection
        non_avoid_count = len(advisories) - len(avoid_providers)
        if non_avoid_count >= self.floor_provider_count:
            return advisories

        # Need to protect some providers
        # Prioritize the selected floor provider, then sort by health score
        avoid_with_health = []
        for provider in avoid_providers:
            health_data = providers_health.get(provider, {})
            health_score = (
                health_data.get("health_score", 0)
                if isinstance(health_data, dict) else 0
            )
            # Give floor provider priority by adding a large bonus
            priority_score = health_score + (1000 if provider == floor_provider else 0)
            avoid_with_health.append((provider, health_score, priority_score))

        avoid_with_health.sort(key=lambda x: x[2], reverse=True)

        # Protect the prioritized AVOID providers
        protect_count = self.floor_provider_count - non_avoid_count
        for i, (provider, health_score, _) in enumerate(avoid_with_health):
            if i >= protect_count:
                break

            # Cap at CRITICAL instead of AVOID
            original = advisories[provider]
            advisories[provider] = DegradationRecommendation(
                provider=provider,
                severity=DegradationSeverity.CRITICAL,
                score_multiplier=SEVERITY_MULTIPLIERS[DegradationSeverity.CRITICAL],
                health_score=original.health_score,
                health_score_normalized=original.health_score_normalized,
                reason=original.reason,
                dry_run=True,
                floor_protected=True,
                previous_severity=original.previous_severity,
            )

            is_selected_floor = provider == floor_provider
            logger.info(
                f"[I-4-ADVISORY] Floor protection applied for {provider}. "
                f"Health score {health_score:.1f} would trigger AVOID, "
                f"but provider is protected as floor provider "
                f"(strategy={self.floor_strategy}, selected={is_selected_floor}). "
                f"Capped at CRITICAL (multiplier=0.25)."
            )

        return advisories

    def _is_in_cooldown(self, provider: str) -> bool:
        """Check if provider is in cooldown period"""
        with self._lock:
            last_advisory = self._last_advisory_time.get(provider)
            if last_advisory is None:
                return False

            cooldown_end = last_advisory + timedelta(minutes=self.cooldown_minutes)
            return datetime.now(timezone.utc) < cooldown_end

    def get_provider_state(self, provider: str) -> Optional[DegradationSeverity]:
        """Get current state for a provider"""
        with self._lock:
            return self._provider_states.get(provider)

    def get_all_states(self) -> Dict[str, str]:
        """Get current states for all tracked providers"""
        with self._lock:
            return {p: s.value for p, s in self._provider_states.items()}

    def clear_state(self, provider: Optional[str] = None) -> None:
        """Clear state for a provider or all providers (for testing)"""
        with self._lock:
            if provider:
                self._provider_states.pop(provider, None)
                self._last_advisory_time.pop(provider, None)
                if self._current_floor_provider == provider:
                    self._current_floor_provider = None
            else:
                self._provider_states.clear()
                self._last_advisory_time.clear()
                self._current_floor_provider = None

    def get_current_floor_provider(self) -> Optional[str]:
        """Get the current floor provider (for testing/debugging)"""
        with self._lock:
            return self._current_floor_provider


# Global singleton for degradation advisor (EPIC I-4)
_degradation_advisor: Optional[DegradationAdvisor] = None
_degradation_advisor_lock = threading.Lock()


def get_degradation_advisor() -> Optional[DegradationAdvisor]:
    """
    Get the global DegradationAdvisor singleton instance

    EPIC I-4 Phase A: Immune Decision Engine

    This function provides thread-safe access to the global advisor instance.
    Returns None if advisory is disabled or not configured.

    Returns:
        DegradationAdvisor instance or None if not available
    """
    global _degradation_advisor

    if _degradation_advisor is not None:
        return _degradation_advisor

    with _degradation_advisor_lock:
        if _degradation_advisor is not None:
            return _degradation_advisor

        try:
            from common.config.settings import settings

            if not getattr(settings, "degradation_advisory_enabled", False):
                logger.debug("[DegradationAdvisor] Advisory disabled")
                return None

            _degradation_advisor = DegradationAdvisor(
                enabled=True,
                cooldown_minutes=getattr(
                    settings, "degradation_cooldown_minutes", 15
                ),
                min_requests=getattr(
                    settings, "degradation_min_requests", 10
                ),
                floor_provider_count=getattr(
                    settings, "degradation_floor_provider_count", 1
                ),
                healthy_threshold=getattr(
                    settings, "degradation_healthy_threshold", 75.0
                ),
                degraded_threshold=getattr(
                    settings, "degradation_degraded_threshold", 50.0
                ),
                critical_threshold=getattr(
                    settings, "degradation_critical_threshold", 25.0
                ),
                recovery_buffer=getattr(
                    settings, "degradation_recovery_buffer", 10.0
                ),
                floor_strategy=getattr(
                    settings, "degradation_floor_strategy", "hybrid"
                ),
                fixed_floor_provider=getattr(
                    settings, "degradation_fixed_floor_provider", "openai"
                ),
                floor_switch_margin=getattr(
                    settings, "degradation_floor_switch_margin", 10.0
                ),
                floor_min_requests=getattr(
                    settings, "degradation_floor_min_requests", 10
                ),
            )

            logger.info("[DegradationAdvisor] Initialized global advisor instance")
            return _degradation_advisor

        except Exception as e:
            logger.warning(f"[DegradationAdvisor] Failed to initialize: {e}")
            return None


def reset_degradation_advisor() -> None:
    """
    Reset the global DegradationAdvisor singleton (useful for testing)

    EPIC I-4 Phase A: Immune Decision Engine
    """
    global _degradation_advisor
    with _degradation_advisor_lock:
        _degradation_advisor = None
