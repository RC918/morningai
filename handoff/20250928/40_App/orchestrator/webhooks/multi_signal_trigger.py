"""
Multi-Signal Trigger System - Issue #2213

This module provides a multi-signal trigger mechanism that allows the system
to automatically trigger fix tasks based on multiple signals when there are
no Codex/Gemini reviews.

Design Concept:
The AI Review closed loop should not rely solely on external AI reviews.
When there are no reviews, the system should be able to trigger based on:
- CI failure
- Evaluation regression
- Human @mention
- Scheduled scanning

Signal Types and Priority:
| Signal Source       | Trigger Condition              | Priority |
|---------------------|--------------------------------|----------|
| Codex/Gemini review | Has concrete suggestion        | High     |
| CI failure          | ci_state == "failure"          | High     |
| Evaluation regression | code_quality_score drops     | Medium   |
| Human @mention      | @meta-agent please fix...      | Medium   |
| Scheduled scanning  | Cron job checks stale PRs      | Low      |

Issue: #2213 - Phase 7.5: Multi-Signal Trigger System
Milestone: Phase 7: AI Review Closed Loop
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """
    Types of signals that can trigger fix tasks.

    Priority order (highest to lowest):
    1. AI_REVIEW - External AI reviewer (Codex/Gemini) comment
    2. CI_FAILURE - CI checks failed
    3. EVALUATION_REGRESSION - Code quality score dropped
    4. MENTION - Human @mention requesting fix
    5. SCHEDULED_SCAN - Scheduled scan found stale PR
    """
    AI_REVIEW = "ai_review"
    CI_FAILURE = "ci_failure"
    EVALUATION_REGRESSION = "evaluation_regression"
    MENTION = "mention"
    SCHEDULED_SCAN = "scheduled_scan"


class SignalPriority(Enum):
    """Priority levels for signals"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TriggerAction(Enum):
    """Actions that can be triggered by signals"""
    AUTO_FIX = "auto_fix"
    MANUAL_REVIEW = "manual_review"
    ESCALATE = "escalate"
    SKIP = "skip"
    QUEUE = "queue"


# Signal type to priority mapping
SIGNAL_PRIORITY_MAP: Dict[SignalType, SignalPriority] = {
    SignalType.AI_REVIEW: SignalPriority.HIGH,
    SignalType.CI_FAILURE: SignalPriority.HIGH,
    SignalType.EVALUATION_REGRESSION: SignalPriority.MEDIUM,
    SignalType.MENTION: SignalPriority.MEDIUM,
    SignalType.SCHEDULED_SCAN: SignalPriority.LOW,
}

# Priority to numeric value for comparison (lower = higher priority)
PRIORITY_ORDER: Dict[SignalPriority, int] = {
    SignalPriority.HIGH: 0,
    SignalPriority.MEDIUM: 1,
    SignalPriority.LOW: 2,
}


@dataclass
class TriggerSignal:
    """
    Represents a single trigger signal.

    Attributes:
        signal_type: Type of the signal
        source: Source identifier (e.g., "codex", "gemini", "ci", "user")
        timestamp: When the signal was generated
        priority: Priority level of the signal
        metadata: Additional signal-specific data
        is_active: Whether the signal is currently active
        confidence: Confidence score for the signal (0.0 to 1.0)
    """
    signal_type: SignalType
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: SignalPriority = field(default=SignalPriority.MEDIUM)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    confidence: float = 1.0

    def __post_init__(self):
        # Set priority based on signal type if not explicitly set
        if self.priority == SignalPriority.MEDIUM:
            self.priority = SIGNAL_PRIORITY_MAP.get(
                self.signal_type, SignalPriority.MEDIUM
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "signal_type": self.signal_type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "confidence": self.confidence,
        }


@dataclass
class MultiSignalContext:
    """
    Aggregates multiple signals for a single PR/task.

    This context is used to evaluate whether to trigger a fix task
    based on the combination of signals present.

    Attributes:
        pr_number: PR number being evaluated
        repo: Repository in owner/repo format
        signals: List of active signals
        created_at: When the context was created
        last_updated: When the context was last updated
        evaluation_count: Number of times this context has been evaluated
    """
    pr_number: int
    repo: str
    signals: List[TriggerSignal] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation_count: int = 0

    def add_signal(self, signal: TriggerSignal) -> None:
        """Add a signal to the context"""
        self.signals.append(signal)
        self.last_updated = datetime.now(timezone.utc)
        logger.debug(
            "[MultiSignalContext] Added signal: type=%s, source=%s, pr=%d",
            signal.signal_type.value,
            signal.source,
            self.pr_number,
        )

    def get_active_signals(self) -> List[TriggerSignal]:
        """Get all active signals"""
        return [s for s in self.signals if s.is_active]

    def get_signals_by_type(self, signal_type: SignalType) -> List[TriggerSignal]:
        """Get all signals of a specific type"""
        return [s for s in self.signals if s.signal_type == signal_type]

    def get_highest_priority_signal(self) -> Optional[TriggerSignal]:
        """Get the highest priority active signal"""
        active = self.get_active_signals()
        if not active:
            return None
        return min(
            active,
            key=lambda s: PRIORITY_ORDER.get(s.priority, 999)
        )

    def has_signal_type(self, signal_type: SignalType) -> bool:
        """Check if context has an active signal of the given type"""
        return any(
            s.signal_type == signal_type and s.is_active
            for s in self.signals
        )

    def get_overall_priority(self) -> Optional[SignalPriority]:
        """Get the overall priority based on highest priority signal"""
        signal = self.get_highest_priority_signal()
        return signal.priority if signal else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "pr_number": self.pr_number,
            "repo": self.repo,
            "signals": [s.to_dict() for s in self.signals],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "evaluation_count": self.evaluation_count,
            "active_signal_count": len(self.get_active_signals()),
            "overall_priority": (
                self.get_overall_priority().value
                if self.get_overall_priority()
                else None
            ),
        }


@dataclass
class TriggerEvaluationResult:
    """
    Result of evaluating a multi-signal context.

    Attributes:
        should_trigger: Whether a fix task should be triggered
        action: Recommended action to take
        priority: Priority for the triggered task
        reason: Human-readable reason for the decision
        contributing_signals: Signals that contributed to the decision
        confidence: Overall confidence in the decision (0.0 to 1.0)
    """
    should_trigger: bool
    action: TriggerAction
    priority: str
    reason: str
    contributing_signals: List[TriggerSignal] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "should_trigger": self.should_trigger,
            "action": self.action.value,
            "priority": self.priority,
            "reason": self.reason,
            "contributing_signals": [s.to_dict() for s in self.contributing_signals],
            "confidence": self.confidence,
        }


class MultiSignalTriggerService:
    """
    Service for evaluating multi-signal contexts and triggering fix tasks.

    This service:
    1. Creates signal contexts from various sources
    2. Evaluates contexts to determine if fix tasks should be triggered
    3. Applies priority logic to determine task priority
    4. Integrates with TaskIntakeService for task creation

    Issue: #2213 - Multi-Signal Trigger System
    """

    # Minimum confidence threshold for triggering
    MIN_CONFIDENCE_THRESHOLD = 0.5

    # Signal combinations that always trigger
    ALWAYS_TRIGGER_COMBINATIONS = [
        {SignalType.AI_REVIEW},  # AI review alone triggers
        {SignalType.CI_FAILURE},  # CI failure alone triggers
        {SignalType.CI_FAILURE, SignalType.EVALUATION_REGRESSION},  # Combined
    ]

    # Signal combinations that require HITL approval
    HITL_REQUIRED_COMBINATIONS = [
        {SignalType.MENTION},  # Human mention needs confirmation
        {SignalType.SCHEDULED_SCAN},  # Scheduled scan needs review
    ]

    def __init__(self):
        """Initialize the MultiSignalTriggerService"""
        self._contexts: Dict[str, MultiSignalContext] = {}
        logger.info("[MultiSignalTriggerService] Initialized")

    def _get_context_key(self, repo: str, pr_number: int) -> str:
        """Generate a unique key for a context"""
        return f"{repo}#{pr_number}"

    def get_or_create_context(
        self, repo: str, pr_number: int
    ) -> MultiSignalContext:
        """
        Get existing context or create a new one.

        Args:
            repo: Repository in owner/repo format
            pr_number: PR number

        Returns:
            MultiSignalContext for the PR
        """
        key = self._get_context_key(repo, pr_number)
        if key not in self._contexts:
            self._contexts[key] = MultiSignalContext(
                pr_number=pr_number,
                repo=repo,
            )
            logger.info(
                "[MultiSignalTriggerService] Created new context: repo=%s, pr=%d",
                repo,
                pr_number,
            )
        return self._contexts[key]

    def create_ai_review_signal(
        self,
        source: str,
        comment_body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        severity: str = "medium",
    ) -> TriggerSignal:
        """
        Create a signal from an AI reviewer comment.

        Args:
            source: AI reviewer name (codex, gemini, coderabbit)
            comment_body: Body of the review comment
            file_path: File path mentioned in the comment
            line_number: Line number mentioned in the comment
            severity: Severity of the issue (low, medium, high, critical)

        Returns:
            TriggerSignal for the AI review
        """
        # Determine confidence based on severity
        severity_confidence = {
            "critical": 1.0,
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5,
        }
        confidence = severity_confidence.get(severity.lower(), 0.7)

        return TriggerSignal(
            signal_type=SignalType.AI_REVIEW,
            source=source,
            priority=SignalPriority.HIGH,
            confidence=confidence,
            metadata={
                "comment_body": comment_body,
                "file_path": file_path,
                "line_number": line_number,
                "severity": severity,
            },
        )

    def create_ci_failure_signal(
        self,
        ci_state: str,
        failed_checks: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[TriggerSignal]:
        """
        Create a signal from CI failure.

        Args:
            ci_state: CI state (success, failure, pending, unknown)
            failed_checks: List of failed check names
            error_message: Error message from CI

        Returns:
            TriggerSignal if CI failed, None otherwise
        """
        if ci_state != "failure":
            return None

        return TriggerSignal(
            signal_type=SignalType.CI_FAILURE,
            source="ci",
            priority=SignalPriority.HIGH,
            confidence=1.0,  # CI failure is definitive
            metadata={
                "ci_state": ci_state,
                "failed_checks": failed_checks or [],
                "error_message": error_message,
            },
        )

    def create_evaluation_regression_signal(
        self,
        current_score: int,
        previous_score: int,
        threshold: int = 10,
    ) -> Optional[TriggerSignal]:
        """
        Create a signal from evaluation regression.

        Args:
            current_score: Current code quality score (0-100)
            previous_score: Previous code quality score (0-100)
            threshold: Minimum score drop to trigger (default: 10)

        Returns:
            TriggerSignal if regression detected, None otherwise
        """
        score_drop = previous_score - current_score
        if score_drop < threshold:
            return None

        # Confidence based on severity of drop
        if score_drop >= 30:
            confidence = 1.0
        elif score_drop >= 20:
            confidence = 0.9
        else:
            confidence = 0.7

        return TriggerSignal(
            signal_type=SignalType.EVALUATION_REGRESSION,
            source="evaluation",
            priority=SignalPriority.MEDIUM,
            confidence=confidence,
            metadata={
                "current_score": current_score,
                "previous_score": previous_score,
                "score_drop": score_drop,
            },
        )

    def create_mention_signal(
        self,
        mention_text: str,
        mentioned_by: str,
        mention_type: str = "comment",
    ) -> Optional[TriggerSignal]:
        """
        Create a signal from human @mention.

        Args:
            mention_text: Text of the mention
            mentioned_by: Username who mentioned
            mention_type: Type of mention (comment, issue, pr)

        Returns:
            TriggerSignal if valid mention, None otherwise
        """
        # Check for valid trigger phrases
        trigger_phrases = [
            "@meta-agent",
            "@bot",
            "@agent",
            "please fix",
            "please review",
            "needs fix",
        ]

        text_lower = mention_text.lower()
        has_trigger = any(phrase in text_lower for phrase in trigger_phrases)

        if not has_trigger:
            return None

        return TriggerSignal(
            signal_type=SignalType.MENTION,
            source=mentioned_by,
            priority=SignalPriority.MEDIUM,
            confidence=0.8,  # Human mentions have high confidence
            metadata={
                "mention_text": mention_text,
                "mentioned_by": mentioned_by,
                "mention_type": mention_type,
            },
        )

    def create_scheduled_scan_signal(
        self,
        pr_age_days: int,
        last_activity_days: int,
        scan_reason: str = "stale_pr",
    ) -> Optional[TriggerSignal]:
        """
        Create a signal from scheduled scanning.

        Args:
            pr_age_days: Age of the PR in days
            last_activity_days: Days since last activity
            scan_reason: Reason for the scan

        Returns:
            TriggerSignal if PR is stale, None otherwise
        """
        # Only trigger for PRs that are stale (no activity for 7+ days)
        if last_activity_days < 7:
            return None

        # Confidence based on staleness
        if last_activity_days >= 30:
            confidence = 0.9
        elif last_activity_days >= 14:
            confidence = 0.7
        else:
            confidence = 0.5

        return TriggerSignal(
            signal_type=SignalType.SCHEDULED_SCAN,
            source="scheduler",
            priority=SignalPriority.LOW,
            confidence=confidence,
            metadata={
                "pr_age_days": pr_age_days,
                "last_activity_days": last_activity_days,
                "scan_reason": scan_reason,
            },
        )

    def evaluate_context(
        self, context: MultiSignalContext
    ) -> TriggerEvaluationResult:
        """
        Evaluate a multi-signal context and determine if a fix task should be triggered.

        Priority Logic:
        1. AI review > CI failure > Evaluation regression > Human mention > Scheduled scan
        2. Multiple signals of same priority increase confidence
        3. Conflicting signals may require HITL approval

        Args:
            context: MultiSignalContext to evaluate

        Returns:
            TriggerEvaluationResult with decision and reasoning
        """
        context.evaluation_count += 1
        active_signals = context.get_active_signals()

        if not active_signals:
            return TriggerEvaluationResult(
                should_trigger=False,
                action=TriggerAction.SKIP,
                priority="low",
                reason="No active signals",
                confidence=1.0,
            )

        # Get signal types present
        signal_types = {s.signal_type for s in active_signals}

        # Check for always-trigger combinations
        for combo in self.ALWAYS_TRIGGER_COMBINATIONS:
            if combo.issubset(signal_types):
                highest = context.get_highest_priority_signal()
                avg_confidence = sum(s.confidence for s in active_signals) / len(active_signals)

                return TriggerEvaluationResult(
                    should_trigger=True,
                    action=TriggerAction.AUTO_FIX,
                    priority=highest.priority.value if highest else "medium",
                    reason=f"Trigger combination matched: {[t.value for t in combo]}",
                    contributing_signals=active_signals,
                    confidence=avg_confidence,
                )

        # Check for HITL-required combinations
        for combo in self.HITL_REQUIRED_COMBINATIONS:
            if combo.issubset(signal_types):
                highest = context.get_highest_priority_signal()

                return TriggerEvaluationResult(
                    should_trigger=True,
                    action=TriggerAction.MANUAL_REVIEW,
                    priority=highest.priority.value if highest else "medium",
                    reason=f"HITL approval required for: {[t.value for t in combo]}",
                    contributing_signals=active_signals,
                    confidence=0.7,
                )

        # Default: evaluate based on highest priority signal
        highest = context.get_highest_priority_signal()
        if highest and highest.confidence >= self.MIN_CONFIDENCE_THRESHOLD:
            return TriggerEvaluationResult(
                should_trigger=True,
                action=TriggerAction.QUEUE,
                priority=highest.priority.value,
                reason=f"Single signal trigger: {highest.signal_type.value}",
                contributing_signals=[highest],
                confidence=highest.confidence,
            )

        return TriggerEvaluationResult(
            should_trigger=False,
            action=TriggerAction.SKIP,
            priority="low",
            reason="No signals met confidence threshold",
            confidence=0.0,
        )

    def process_ci_state(
        self,
        repo: str,
        pr_number: int,
        ci_state: str,
        failed_checks: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ) -> TriggerEvaluationResult:
        """
        Process CI state and evaluate for triggering.

        This is the main integration point with ci_monitor_node.

        Args:
            repo: Repository in owner/repo format
            pr_number: PR number
            ci_state: CI state from ci_monitor_node
            failed_checks: List of failed check names
            error_message: Error message from CI

        Returns:
            TriggerEvaluationResult with decision
        """
        context = self.get_or_create_context(repo, pr_number)

        signal = self.create_ci_failure_signal(
            ci_state=ci_state,
            failed_checks=failed_checks,
            error_message=error_message,
        )

        if signal:
            context.add_signal(signal)
            logger.info(
                "[MultiSignalTriggerService] CI failure signal added: repo=%s, pr=%d",
                repo,
                pr_number,
            )

        return self.evaluate_context(context)

    def process_evaluation_result(
        self,
        repo: str,
        pr_number: int,
        current_score: int,
        previous_score: int,
    ) -> TriggerEvaluationResult:
        """
        Process evaluation result and evaluate for triggering.

        This is the main integration point with evaluation_node.

        Args:
            repo: Repository in owner/repo format
            pr_number: PR number
            current_score: Current code quality score
            previous_score: Previous code quality score

        Returns:
            TriggerEvaluationResult with decision
        """
        context = self.get_or_create_context(repo, pr_number)

        signal = self.create_evaluation_regression_signal(
            current_score=current_score,
            previous_score=previous_score,
        )

        if signal:
            context.add_signal(signal)
            logger.info(
                "[MultiSignalTriggerService] Evaluation regression signal added: "
                "repo=%s, pr=%d, drop=%d",
                repo,
                pr_number,
                previous_score - current_score,
            )

        return self.evaluate_context(context)

    def process_mention(
        self,
        repo: str,
        pr_number: int,
        mention_text: str,
        mentioned_by: str,
        mention_type: str = "comment",
    ) -> TriggerEvaluationResult:
        """
        Process @mention and evaluate for triggering.

        This is the main integration point with MENTION_RECEIVED webhook.

        Args:
            repo: Repository in owner/repo format
            pr_number: PR number
            mention_text: Text of the mention
            mentioned_by: Username who mentioned
            mention_type: Type of mention

        Returns:
            TriggerEvaluationResult with decision
        """
        context = self.get_or_create_context(repo, pr_number)

        signal = self.create_mention_signal(
            mention_text=mention_text,
            mentioned_by=mentioned_by,
            mention_type=mention_type,
        )

        if signal:
            context.add_signal(signal)
            logger.info(
                "[MultiSignalTriggerService] Mention signal added: "
                "repo=%s, pr=%d, by=%s",
                repo,
                pr_number,
                mentioned_by,
            )

        return self.evaluate_context(context)

    def process_ai_review(
        self,
        repo: str,
        pr_number: int,
        source: str,
        comment_body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        severity: str = "medium",
    ) -> TriggerEvaluationResult:
        """
        Process AI reviewer comment and evaluate for triggering.

        This is the main integration point with AI reviewer webhook events.

        Args:
            repo: Repository in owner/repo format
            pr_number: PR number
            source: AI reviewer name
            comment_body: Body of the review comment
            file_path: File path mentioned
            line_number: Line number mentioned
            severity: Severity of the issue

        Returns:
            TriggerEvaluationResult with decision
        """
        context = self.get_or_create_context(repo, pr_number)

        signal = self.create_ai_review_signal(
            source=source,
            comment_body=comment_body,
            file_path=file_path,
            line_number=line_number,
            severity=severity,
        )

        context.add_signal(signal)
        logger.info(
            "[MultiSignalTriggerService] AI review signal added: "
            "repo=%s, pr=%d, source=%s, severity=%s",
            repo,
            pr_number,
            source,
            severity,
        )

        return self.evaluate_context(context)

    def clear_context(self, repo: str, pr_number: int) -> bool:
        """
        Clear the context for a PR.

        Args:
            repo: Repository in owner/repo format
            pr_number: PR number

        Returns:
            True if context was cleared, False if not found
        """
        key = self._get_context_key(repo, pr_number)
        if key in self._contexts:
            del self._contexts[key]
            logger.info(
                "[MultiSignalTriggerService] Context cleared: repo=%s, pr=%d",
                repo,
                pr_number,
            )
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        total_signals = sum(
            len(ctx.signals) for ctx in self._contexts.values()
        )
        active_signals = sum(
            len(ctx.get_active_signals()) for ctx in self._contexts.values()
        )

        signal_type_counts: Dict[str, int] = {}
        for ctx in self._contexts.values():
            for signal in ctx.signals:
                signal_type = signal.signal_type.value
                signal_type_counts[signal_type] = (
                    signal_type_counts.get(signal_type, 0) + 1
                )

        return {
            "context_count": len(self._contexts),
            "total_signals": total_signals,
            "active_signals": active_signals,
            "signal_type_counts": signal_type_counts,
        }
