"""
Capability Score Manager - EPIC I Phase I-3 Autonomous Evolution

This module manages provider capability scores based on benchmark results.
It implements automatic score updates with safety guards.

Key Features:
- Provider capability score tracking with trend analysis
- Automatic score updates based on benchmark results
- Safety guards: no auto-upgrade without human review
- Alert generation for significant score changes

Blueprint Alignment:
- Section 4.4: Autonomous Provisioning v2
- EPIC I-3: Autonomous Evolution (Benchmark & Capability Scoring)

Issue: #3342
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Redis keys for capability scores
CAPABILITY_SCORES_KEY = "governance:capability_scores"
CAPABILITY_HISTORY_KEY = "governance:capability_history"
CAPABILITY_ALERTS_KEY = "governance:capability_alerts"
CAPABILITY_SCORES_TTL = 86400 * 90  # 90 days


class ScoreTrend(Enum):
    """Score trend over time"""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class ScoreChangeAction(Enum):
    """Actions to take on score changes"""
    NO_ACTION = "no_action"
    ALERT_ONLY = "alert_only"
    FLAG_FOR_REVIEW = "flag_for_review"
    AUTO_DOWNGRADE = "auto_downgrade"


# Auto-update rules from EPIC I-3 roadmap
AUTO_UPDATE_RULES = {
    "score_drop_10_percent": {
        "threshold": 0.10,
        "action": ScoreChangeAction.FLAG_FOR_REVIEW,
        "description": "Score drops >10%: Alert + flag for review",
    },
    "score_drop_20_percent": {
        "threshold": 0.20,
        "action": ScoreChangeAction.AUTO_DOWNGRADE,
        "description": "Score drops >20%: Auto-downgrade severity",
    },
    "score_improve_10_percent": {
        "threshold": 0.10,
        "action": ScoreChangeAction.FLAG_FOR_REVIEW,
        "description": "Score improves >10%: Flag for review (no auto-upgrade)",
    },
}


@dataclass
class ProviderCapabilityScore:
    """
    Capability score for a provider/model combination.

    EPIC I-3: Provider Capability Score Schema

    Attributes:
        provider: Canonical provider name (e.g., "openai", "gemini")
        model: Model identifier
        task_type: Type of task this score applies to
        score: Capability score (0-100 scale)
        sample_size: Number of benchmark runs contributing to score
        confidence: Statistical confidence in score (0.0-1.0)
        trend: Score trend over last 4 weeks
        last_updated: ISO 8601 timestamp of last update
        previous_score: Previous score for change detection
        flagged_for_review: Whether score change needs human review
    """
    provider: str
    model: str
    task_type: str
    score: float
    sample_size: int = 0
    confidence: float = 0.0
    trend: ScoreTrend = ScoreTrend.STABLE
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    previous_score: Optional[float] = None
    flagged_for_review: bool = False

    @property
    def score_change_percent(self) -> float:
        """Calculate percentage change from previous score.

        Returns 0.0 when there's no previous score to ensure consistent
        downstream handling without None checks.
        """
        if self.previous_score is None or self.previous_score == 0:
            return 0.0
        return (self.score - self.previous_score) / self.previous_score

    @property
    def is_significant_change(self) -> bool:
        """Check if score change is significant (>10%)"""
        change = self.score_change_percent
        if change is None:
            return False
        return abs(change) > 0.10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "provider": self.provider,
            "model": self.model,
            "task_type": self.task_type,
            "score": self.score,
            "sample_size": self.sample_size,
            "confidence": self.confidence,
            "trend": self.trend.value,
            "last_updated": self.last_updated,
            "previous_score": self.previous_score,
            "score_change_percent": self.score_change_percent,
            "flagged_for_review": self.flagged_for_review,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderCapabilityScore":
        """Create from dictionary"""
        return cls(
            provider=data["provider"],
            model=data["model"],
            task_type=data["task_type"],
            score=data["score"],
            sample_size=data.get("sample_size", 0),
            confidence=data.get("confidence", 0.0),
            trend=ScoreTrend(data.get("trend", "stable")),
            last_updated=data.get("last_updated", datetime.now(timezone.utc).isoformat()),
            previous_score=data.get("previous_score"),
            flagged_for_review=data.get("flagged_for_review", False),
        )


@dataclass
class ScoreChangeAlert:
    """
    Alert for significant score changes.

    Attributes:
        provider: Provider name
        model: Model name
        task_type: Task type
        previous_score: Previous capability score
        new_score: New capability score
        change_percent: Percentage change
        action: Recommended action
        reason: Human-readable reason
        timestamp: ISO 8601 timestamp
        acknowledged: Whether alert has been acknowledged
    """
    provider: str
    model: str
    task_type: str
    previous_score: float
    new_score: float
    change_percent: float
    action: ScoreChangeAction
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "provider": self.provider,
            "model": self.model,
            "task_type": self.task_type,
            "previous_score": self.previous_score,
            "new_score": self.new_score,
            "change_percent": self.change_percent,
            "action": self.action.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
        }


class CapabilityScoreManager:
    """
    Manages provider capability scores based on benchmark results.

    EPIC I-3: Autonomous Evolution

    This class tracks capability scores, detects trends, and generates
    alerts for significant changes. It enforces safety guards to prevent
    automatic upgrades without human review.

    Safety Contract:
    - Score drops >20% trigger auto-downgrade (with floor protection)
    - Score improvements NEVER trigger auto-upgrade (human review required)
    - All significant changes are logged and flagged for review

    Attributes:
        enabled: Whether capability score management is enabled
        redis_client: Redis client for score storage
        dry_run: Whether to run in dry-run mode (no actual changes)
    """

    def __init__(
        self,
        redis_client: Optional["Redis"] = None,
        enabled: bool = True,
        dry_run: bool = True,
    ):
        self.redis_client = redis_client
        self.enabled = enabled
        self.dry_run = dry_run
        self._scores_cache: Dict[str, ProviderCapabilityScore] = {}

    def _get_score_key(self, provider: str, model: str, task_type: str) -> str:
        """Generate unique key for a capability score"""
        return f"{provider}:{model}:{task_type}"

    def get_score(
        self,
        provider: str,
        model: str,
        task_type: str,
    ) -> Optional[ProviderCapabilityScore]:
        """
        Get capability score for a provider/model/task combination.

        Args:
            provider: Provider name
            model: Model name
            task_type: Task type

        Returns:
            ProviderCapabilityScore if found, None otherwise
        """
        key = self._get_score_key(provider, model, task_type)

        # Check cache first
        if key in self._scores_cache:
            return self._scores_cache[key]

        # Load from Redis
        if self.redis_client:
            try:
                data = self.redis_client.hget(CAPABILITY_SCORES_KEY, key)
                if data:
                    score = ProviderCapabilityScore.from_dict(json.loads(data))
                    self._scores_cache[key] = score
                    return score
            except Exception as e:
                logger.warning(
                    f"[CapabilityScore] Failed to load score: {e}",
                    extra={
                        "operation": "capability_score_load",
                        "key": key,
                        "error": str(e),
                    }
                )

        return None

    def update_score(
        self,
        provider: str,
        model: str,
        task_type: str,
        new_score: float,
        sample_size: int = 1,
    ) -> ProviderCapabilityScore:
        """
        Update capability score based on new benchmark results.

        Implements exponential moving average for score updates:
        new_score = alpha * benchmark_score + (1 - alpha) * previous_score

        Args:
            provider: Provider name
            model: Model name
            task_type: Task type
            new_score: New score from benchmark
            sample_size: Number of samples in this update

        Returns:
            Updated ProviderCapabilityScore
        """
        key = self._get_score_key(provider, model, task_type)
        existing = self.get_score(provider, model, task_type)

        if existing:
            # Calculate exponential moving average
            alpha = min(0.3, sample_size / (existing.sample_size + sample_size))
            updated_score = alpha * new_score + (1 - alpha) * existing.score

            # Determine trend
            trend = self._calculate_trend(existing.score, updated_score)

            # Calculate confidence based on sample size
            confidence = min(1.0, (existing.sample_size + sample_size) / 100)

            score = ProviderCapabilityScore(
                provider=provider,
                model=model,
                task_type=task_type,
                score=round(updated_score, 2),
                sample_size=existing.sample_size + sample_size,
                confidence=round(confidence, 2),
                trend=trend,
                previous_score=existing.score,
            )
        else:
            # First score for this combination
            score = ProviderCapabilityScore(
                provider=provider,
                model=model,
                task_type=task_type,
                score=round(new_score, 2),
                sample_size=sample_size,
                confidence=min(1.0, sample_size / 100),
                trend=ScoreTrend.STABLE,
            )

        # Check for significant changes and generate alerts
        action = self._evaluate_score_change(score)
        if action != ScoreChangeAction.NO_ACTION:
            score.flagged_for_review = True
            self._generate_alert(score, action)

        # Store updated score
        self._store_score(score)
        self._scores_cache[key] = score

        logger.info(
            f"[CapabilityScore] Updated: provider={provider}, model={model}, "
            f"task_type={task_type}, score={score.score:.2f}, trend={score.trend.value}",
            extra={
                "operation": "capability_score_update",
                "provider": provider,
                "model": model,
                "task_type": task_type,
                "score": score.score,
                "previous_score": score.previous_score,
                "trend": score.trend.value,
                "flagged_for_review": score.flagged_for_review,
            }
        )

        return score

    def _calculate_trend(self, previous_score: float, current_score: float) -> ScoreTrend:
        """Calculate score trend based on change"""
        if previous_score == 0:
            return ScoreTrend.STABLE

        change_percent = (current_score - previous_score) / previous_score

        if change_percent > 0.05:
            return ScoreTrend.IMPROVING
        elif change_percent < -0.05:
            return ScoreTrend.DEGRADING
        else:
            return ScoreTrend.STABLE

    def _evaluate_score_change(self, score: ProviderCapabilityScore) -> ScoreChangeAction:
        """
        Evaluate score change and determine action.

        Implements EPIC I-3 auto-update rules with safety guards.
        """
        change = score.score_change_percent
        if change is None:
            return ScoreChangeAction.NO_ACTION

        # Check for score drop
        if change < 0:
            if abs(change) >= AUTO_UPDATE_RULES["score_drop_20_percent"]["threshold"]:
                return ScoreChangeAction.AUTO_DOWNGRADE
            elif abs(change) >= AUTO_UPDATE_RULES["score_drop_10_percent"]["threshold"]:
                return ScoreChangeAction.FLAG_FOR_REVIEW

        # Check for score improvement (NEVER auto-upgrade)
        if change > 0:
            if change >= AUTO_UPDATE_RULES["score_improve_10_percent"]["threshold"]:
                return ScoreChangeAction.FLAG_FOR_REVIEW

        return ScoreChangeAction.NO_ACTION

    def _generate_alert(
        self,
        score: ProviderCapabilityScore,
        action: ScoreChangeAction,
    ) -> None:
        """Generate alert for significant score change"""
        change = score.score_change_percent or 0

        if change < 0:
            reason = f"Score dropped by {abs(change) * 100:.1f}%"
        else:
            reason = f"Score improved by {change * 100:.1f}% (requires human review)"

        alert = ScoreChangeAlert(
            provider=score.provider,
            model=score.model,
            task_type=score.task_type,
            previous_score=score.previous_score or 0,
            new_score=score.score,
            change_percent=change,
            action=action,
            reason=reason,
        )

        logger.warning(
            f"[CapabilityScore] Alert: {reason}",
            extra={
                "operation": "capability_score_alert",
                "provider": score.provider,
                "model": score.model,
                "task_type": score.task_type,
                "action": action.value,
                "change_percent": change,
            }
        )

        # Store alert in Redis
        if self.redis_client:
            try:
                alert_key = f"{CAPABILITY_ALERTS_KEY}:{int(datetime.now(timezone.utc).timestamp())}"
                self.redis_client.setex(
                    alert_key,
                    86400 * 7,  # 7 days TTL
                    json.dumps(alert.to_dict()),
                )
            except Exception as e:
                logger.warning(
                    f"[CapabilityScore] Failed to store alert: {e}",
                    extra={
                        "operation": "capability_score_alert_store",
                        "error": str(e),
                    }
                )

    def _extract_task_type(self, task_id: str) -> str:
        """
        Extract task_type from task_id with validation.

        Issue #3958: Robust task_id parsing with validation.

        Expected task_id format: {prefix}_{task_type}_{suffix}
        Examples:
        - "bench_code_gen_001" -> "code_gen"
        - "bench_code_review_002" -> "code_review"
        - "bench_bug_fix_003" -> "bug_fix"
        - "test_general_001" -> "general"

        Args:
            task_id: Task identifier string

        Returns:
            Extracted task_type, or "general" if format is unexpected
        """
        # Handle empty or None task_id
        if not task_id or not isinstance(task_id, str):
            logger.debug(
                "[CapabilityScore] Empty or invalid task_id, using 'general'",
                extra={"task_id": task_id}
            )
            return "general"

        # Handle task_id without underscores
        if "_" not in task_id:
            logger.debug(
                f"[CapabilityScore] task_id '{task_id}' has no underscores, "
                "using 'general'",
                extra={"task_id": task_id}
            )
            return "general"

        parts = task_id.split("_")

        # Validate minimum parts: prefix_type_suffix (at least 3 parts)
        if len(parts) < 2:
            logger.warning(
                f"[CapabilityScore] Unexpected task_id format: '{task_id}', "
                "expected at least 2 parts separated by '_'",
                extra={"task_id": task_id, "parts_count": len(parts)}
            )
            return "general"

        # Extract task_type: everything between prefix and suffix
        # For "bench_code_gen_001" -> parts = ["bench", "code", "gen", "001"]
        # task_type = "code_gen" (parts[1:-1] joined)
        if len(parts) > 2:
            task_type = "_".join(parts[1:-1])
        else:
            # For "bench_general" -> parts = ["bench", "general"]
            task_type = parts[1]

        # Validate task_type is not empty
        if not task_type:
            logger.warning(
                f"[CapabilityScore] Empty task_type extracted from '{task_id}'",
                extra={"task_id": task_id}
            )
            return "general"

        return task_type

    def _store_score(self, score: ProviderCapabilityScore) -> bool:
        """Store capability score in Redis"""
        if not self.redis_client:
            return False

        try:
            key = self._get_score_key(score.provider, score.model, score.task_type)
            self.redis_client.hset(
                CAPABILITY_SCORES_KEY,
                key,
                json.dumps(score.to_dict()),
            )

            # Also store in history for trend analysis
            history_key = f"{CAPABILITY_HISTORY_KEY}:{key}:{int(datetime.now(timezone.utc).timestamp())}"
            self.redis_client.setex(
                history_key,
                CAPABILITY_SCORES_TTL,
                json.dumps(score.to_dict()),
            )

            return True

        except Exception as e:
            logger.warning(
                f"[CapabilityScore] Failed to store score: {e}",
                extra={
                    "operation": "capability_score_store",
                    "error": str(e),
                }
            )
            return False

    def update_from_benchmark_results(
        self,
        benchmark_results: Dict[str, Any],
    ) -> Dict[str, ProviderCapabilityScore]:
        """
        Update capability scores from benchmark results.

        This method aggregates benchmark results by (provider, model, task_type)
        to avoid sample_size inflation and uses task-specific scores instead of
        provider-wide averages for more accurate capability tracking.

        Fixes:
        - #3955: Per-task-type scoring granularity
        - #3956: Sample size inflation bug

        Args:
            benchmark_results: Results from BenchmarkEvaluator.run_benchmark_suite()

        Returns:
            Dictionary of updated capability scores
        """
        if not self.enabled:
            return {}

        updated_scores: Dict[str, ProviderCapabilityScore] = {}
        results = benchmark_results.get("results", [])

        # Aggregate results by (provider, model, task_type) to avoid sample_size inflation
        # and use task-specific scores instead of provider-wide averages
        aggregated: Dict[str, Dict[str, Any]] = {}

        for result in results:
            provider = result.get("provider", "")
            model = result.get("model", "default")
            task_id = result.get("task_id", "")

            # Extract task_type from task_id with validation (Issue #3958)
            task_type = self._extract_task_type(task_id)

            # Create aggregation key
            agg_key = f"{provider}:{model}:{task_type}"

            if agg_key not in aggregated:
                aggregated[agg_key] = {
                    "provider": provider,
                    "model": model,
                    "task_type": task_type,
                    "scores": [],
                    "count": 0,
                }

            # Use the result's weighted_score if available, otherwise calculate from components
            weighted_score = result.get("weighted_score")
            if weighted_score is None:
                # Calculate from component scores if weighted_score not provided
                correctness = result.get("correctness_score", 0)
                format_score = result.get("format_compliance_score", 0)
                # Simple average of available scores
                weighted_score = (correctness + format_score) / 2 if correctness or format_score else 0

            if weighted_score > 0:
                aggregated[agg_key]["scores"].append(weighted_score)
                aggregated[agg_key]["count"] += 1

        # Update scores for each unique (provider, model, task_type) combination
        for agg_key, agg_data in aggregated.items():
            if agg_data["scores"]:
                # Calculate average score for this specific task_type
                avg_score = sum(agg_data["scores"]) / len(agg_data["scores"])

                # Use count of unique results as sample_size (not inflated)
                sample_size = agg_data["count"]

                score = self.update_score(
                    provider=agg_data["provider"],
                    model=agg_data["model"],
                    task_type=agg_data["task_type"],
                    new_score=avg_score,
                    sample_size=sample_size,
                )

                key = self._get_score_key(
                    agg_data["provider"],
                    agg_data["model"],
                    agg_data["task_type"]
                )
                updated_scores[key] = score

        logger.info(
            f"[CapabilityScore] Updated {len(updated_scores)} scores from benchmark results",
            extra={
                "operation": "capability_score_batch_update",
                "updated_count": len(updated_scores),
                "aggregated_groups": len(aggregated),
            }
        )

        return updated_scores

    def get_all_scores(self) -> List[ProviderCapabilityScore]:
        """Get all capability scores"""
        scores = []

        if self.redis_client:
            try:
                all_data = self.redis_client.hgetall(CAPABILITY_SCORES_KEY)
                for key, data in all_data.items():
                    score = ProviderCapabilityScore.from_dict(json.loads(data))
                    scores.append(score)
            except Exception as e:
                logger.warning(
                    f"[CapabilityScore] Failed to load all scores: {e}",
                    extra={
                        "operation": "capability_score_load_all",
                        "error": str(e),
                    }
                )

        return scores

    def get_degrading_providers(self) -> List[ProviderCapabilityScore]:
        """Get providers with degrading scores"""
        all_scores = self.get_all_scores()
        return [s for s in all_scores if s.trend == ScoreTrend.DEGRADING]

    def get_flagged_for_review(self) -> List[ProviderCapabilityScore]:
        """Get scores flagged for human review"""
        all_scores = self.get_all_scores()
        return [s for s in all_scores if s.flagged_for_review]


# Global instance
_capability_score_manager: Optional[CapabilityScoreManager] = None


def get_capability_score_manager(
    redis_client: Optional["Redis"] = None,
) -> CapabilityScoreManager:
    """Get or create global CapabilityScoreManager instance."""
    global _capability_score_manager
    if _capability_score_manager is None:
        enabled = os.getenv("CAPABILITY_SCORE_ENABLED", "false").lower() == "true"
        dry_run = os.getenv("CAPABILITY_SCORE_DRY_RUN", "true").lower() == "true"
        _capability_score_manager = CapabilityScoreManager(
            redis_client=redis_client,
            enabled=enabled,
            dry_run=dry_run,
        )
    return _capability_score_manager
