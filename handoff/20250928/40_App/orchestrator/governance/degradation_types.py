"""
Degradation Types - Data structures for EPIC I-4 Auto-Degradation

EPIC I-4 Phase A: Immune Decision Engine (Observe-Only)

This module defines the data structures used by the degradation advisory system.
These types are designed to be reusable in Phase B when actual routing changes
are implemented.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DegradationSeverity(Enum):
    """
    Severity levels for provider degradation

    Each severity level maps to a recommended score multiplier:
    - HEALTHY: Provider is operating normally (multiplier = 1.0)
    - DEGRADED: Provider has reduced reliability (multiplier = 0.5)
    - CRITICAL: Provider has significant issues (multiplier = 0.25)
    - AVOID: Provider should not be used (multiplier = 0.0)
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    AVOID = "avoid"


# Score multipliers for each severity level
SEVERITY_MULTIPLIERS = {
    DegradationSeverity.HEALTHY: 1.0,
    DegradationSeverity.DEGRADED: 0.5,
    DegradationSeverity.CRITICAL: 0.25,
    DegradationSeverity.AVOID: 0.0,
}


@dataclass
class DegradationRecommendation:
    """
    Recommendation for provider degradation

    EPIC I-4 Phase A: Observe-Only

    This dataclass represents a degradation recommendation that can be:
    - Logged for observability (Phase A)
    - Applied to routing (Phase B)

    Attributes:
        provider: Canonical provider name (e.g., "alicloud", "openai")
        severity: Current severity level
        score_multiplier: Recommended routing score multiplier (0.0-1.0)
        health_score: Raw health score (0-100 scale)
        health_score_normalized: Normalized health score (0.0-1.0 scale)
        reason: Human-readable reason for the recommendation
        dry_run: Whether this is a dry-run (always True in Phase A)
        floor_protected: Whether floor protection was applied
        previous_severity: Previous severity level (for state change detection)
        timestamp: ISO 8601 timestamp of the recommendation
    """
    provider: str
    severity: DegradationSeverity
    score_multiplier: float
    health_score: float
    health_score_normalized: float
    reason: str
    dry_run: bool = True
    floor_protected: bool = False
    previous_severity: Optional[DegradationSeverity] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_state_change(self) -> bool:
        """Check if this recommendation represents a state change"""
        return (
            self.previous_severity is not None and
            self.previous_severity != self.severity
        )

    @property
    def display_name(self) -> str:
        """Get display-friendly provider name"""
        display_names = {
            "alicloud": "AliCloud",
            "openai": "OpenAI",
            "gemini": "Gemini",
            "siliconflow": "SiliconFlow",
        }
        return display_names.get(self.provider, self.provider.title())

    def format_log(self) -> str:
        """
        Format recommendation for logging

        Returns a human-readable log message suitable for [I-4-ADVISORY] prefix.
        """
        weight_reduction = int((1 - self.score_multiplier) * 100)

        base_msg = (
            f"Health score {self.health_score:.1f} "
            f"(normalized={self.health_score_normalized:.2f}) "
            f"detected for {self.display_name}. "
            f"Severity: {self.severity.value.upper()}. "
        )

        if self.severity == DegradationSeverity.HEALTHY:
            recommendation = "No action needed."
        elif self.severity == DegradationSeverity.AVOID:
            recommendation = "Recommendation: Avoid using this provider."
        else:
            recommendation = (
                f"Recommendation: Lower routing score by {weight_reduction}% "
                f"(multiplier={self.score_multiplier:.2f})."
            )

        suffix = " (Dry-run mode)" if self.dry_run else ""
        floor_note = " [Floor protected]" if self.floor_protected else ""

        return f"{base_msg}{recommendation}{floor_note}{suffix}"

    def format_state_change_log(self) -> str:
        """
        Format state change for logging

        Returns a human-readable log message for state transitions.
        """
        if not self.is_state_change:
            return self.format_log()

        prev_name = self.previous_severity.value.upper() if self.previous_severity else "UNKNOWN"
        curr_name = self.severity.value.upper()

        return (
            f"Provider {self.display_name} state changed: "
            f"{prev_name} -> {curr_name}. "
            f"Health score: {self.health_score:.1f} "
            f"(normalized={self.health_score_normalized:.2f}). "
            f"Reason: {self.reason}."
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "provider": self.provider,
            "display_name": self.display_name,
            "severity": self.severity.value,
            "score_multiplier": self.score_multiplier,
            "health_score": self.health_score,
            "health_score_normalized": self.health_score_normalized,
            "reason": self.reason,
            "dry_run": self.dry_run,
            "floor_protected": self.floor_protected,
            "is_state_change": self.is_state_change,
            "previous_severity": (
                self.previous_severity.value if self.previous_severity else None
            ),
            "timestamp": self.timestamp,
        }
