"""
Tests for Multi-Signal Trigger System - Issue #2213

This module provides comprehensive tests for the multi-signal trigger mechanism
that allows the system to automatically trigger fix tasks based on multiple signals.

Issue: #2213 - Phase 7.5: Multi-Signal Trigger System
"""

import pytest

from ..multi_signal_trigger import (
    SignalType,
    SignalPriority,
    TriggerAction,
    TriggerSignal,
    MultiSignalContext,
    TriggerEvaluationResult,
    MultiSignalTriggerService,
    SIGNAL_PRIORITY_MAP,
    PRIORITY_ORDER,
)


class TestSignalType:
    """Tests for SignalType enum"""

    def test_signal_types_exist(self):
        """Test that all expected signal types exist"""
        assert SignalType.AI_REVIEW.value == "ai_review"
        assert SignalType.CI_FAILURE.value == "ci_failure"
        assert SignalType.EVALUATION_REGRESSION.value == "evaluation_regression"
        assert SignalType.MENTION.value == "mention"
        assert SignalType.SCHEDULED_SCAN.value == "scheduled_scan"

    def test_signal_priority_mapping(self):
        """Test that signal types have correct priority mapping"""
        assert SIGNAL_PRIORITY_MAP[SignalType.AI_REVIEW] == SignalPriority.HIGH
        assert SIGNAL_PRIORITY_MAP[SignalType.CI_FAILURE] == SignalPriority.HIGH
        assert SIGNAL_PRIORITY_MAP[SignalType.EVALUATION_REGRESSION] == SignalPriority.MEDIUM
        assert SIGNAL_PRIORITY_MAP[SignalType.MENTION] == SignalPriority.MEDIUM
        assert SIGNAL_PRIORITY_MAP[SignalType.SCHEDULED_SCAN] == SignalPriority.LOW


class TestSignalPriority:
    """Tests for SignalPriority enum"""

    def test_priority_levels_exist(self):
        """Test that all priority levels exist"""
        assert SignalPriority.HIGH.value == "high"
        assert SignalPriority.MEDIUM.value == "medium"
        assert SignalPriority.LOW.value == "low"

    def test_priority_order(self):
        """Test that priority order is correct (lower = higher priority)"""
        assert PRIORITY_ORDER[SignalPriority.HIGH] < PRIORITY_ORDER[SignalPriority.MEDIUM]
        assert PRIORITY_ORDER[SignalPriority.MEDIUM] < PRIORITY_ORDER[SignalPriority.LOW]


class TestTriggerSignal:
    """Tests for TriggerSignal dataclass"""

    def test_create_signal_with_defaults(self):
        """Test creating a signal with default values"""
        signal = TriggerSignal(
            signal_type=SignalType.CI_FAILURE,
            source="ci",
        )
        assert signal.signal_type == SignalType.CI_FAILURE
        assert signal.source == "ci"
        assert signal.is_active is True
        assert signal.confidence == 1.0
        # Priority should be set based on signal type
        assert signal.priority == SignalPriority.HIGH

    def test_create_signal_with_custom_values(self):
        """Test creating a signal with custom values"""
        signal = TriggerSignal(
            signal_type=SignalType.MENTION,
            source="user123",
            priority=SignalPriority.HIGH,
            confidence=0.9,
            metadata={"mention_text": "please fix"},
        )
        assert signal.signal_type == SignalType.MENTION
        assert signal.source == "user123"
        assert signal.priority == SignalPriority.HIGH
        assert signal.confidence == 0.9
        assert signal.metadata["mention_text"] == "please fix"

    def test_signal_to_dict(self):
        """Test signal serialization"""
        signal = TriggerSignal(
            signal_type=SignalType.AI_REVIEW,
            source="codex",
            confidence=0.8,
        )
        result = signal.to_dict()
        assert result["signal_type"] == "ai_review"
        assert result["source"] == "codex"
        assert result["confidence"] == 0.8
        assert result["is_active"] is True
        assert "timestamp" in result


class TestMultiSignalContext:
    """Tests for MultiSignalContext dataclass"""

    def test_create_context(self):
        """Test creating a context"""
        context = MultiSignalContext(
            pr_number=123,
            repo="owner/repo",
        )
        assert context.pr_number == 123
        assert context.repo == "owner/repo"
        assert len(context.signals) == 0
        assert context.evaluation_count == 0

    def test_add_signal(self):
        """Test adding a signal to context"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        signal = TriggerSignal(
            signal_type=SignalType.CI_FAILURE,
            source="ci",
        )
        context.add_signal(signal)
        assert len(context.signals) == 1
        assert context.signals[0] == signal

    def test_get_active_signals(self):
        """Test getting active signals"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        active_signal = TriggerSignal(
            signal_type=SignalType.CI_FAILURE,
            source="ci",
            is_active=True,
        )
        inactive_signal = TriggerSignal(
            signal_type=SignalType.MENTION,
            source="user",
            is_active=False,
        )
        context.add_signal(active_signal)
        context.add_signal(inactive_signal)

        active = context.get_active_signals()
        assert len(active) == 1
        assert active[0] == active_signal

    def test_get_signals_by_type(self):
        """Test getting signals by type"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        ci_signal = TriggerSignal(signal_type=SignalType.CI_FAILURE, source="ci")
        mention_signal = TriggerSignal(signal_type=SignalType.MENTION, source="user")
        context.add_signal(ci_signal)
        context.add_signal(mention_signal)

        ci_signals = context.get_signals_by_type(SignalType.CI_FAILURE)
        assert len(ci_signals) == 1
        assert ci_signals[0] == ci_signal

    def test_get_highest_priority_signal(self):
        """Test getting highest priority signal"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        low_signal = TriggerSignal(
            signal_type=SignalType.SCHEDULED_SCAN,
            source="scheduler",
        )
        high_signal = TriggerSignal(
            signal_type=SignalType.CI_FAILURE,
            source="ci",
        )
        context.add_signal(low_signal)
        context.add_signal(high_signal)

        highest = context.get_highest_priority_signal()
        assert highest == high_signal

    def test_has_signal_type(self):
        """Test checking for signal type"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        signal = TriggerSignal(signal_type=SignalType.CI_FAILURE, source="ci")
        context.add_signal(signal)

        assert context.has_signal_type(SignalType.CI_FAILURE) is True
        assert context.has_signal_type(SignalType.MENTION) is False

    def test_context_to_dict(self):
        """Test context serialization"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        signal = TriggerSignal(signal_type=SignalType.CI_FAILURE, source="ci")
        context.add_signal(signal)

        result = context.to_dict()
        assert result["pr_number"] == 123
        assert result["repo"] == "owner/repo"
        assert len(result["signals"]) == 1
        assert result["active_signal_count"] == 1


class TestMultiSignalTriggerService:
    """Tests for MultiSignalTriggerService"""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance"""
        return MultiSignalTriggerService()

    def test_get_or_create_context(self, service):
        """Test getting or creating a context"""
        context1 = service.get_or_create_context("owner/repo", 123)
        context2 = service.get_or_create_context("owner/repo", 123)
        assert context1 is context2  # Same context returned

        context3 = service.get_or_create_context("owner/repo", 456)
        assert context3 is not context1  # Different PR, different context

    def test_create_ai_review_signal(self, service):
        """Test creating AI review signal"""
        signal = service.create_ai_review_signal(
            source="codex",
            comment_body="Consider refactoring this function",
            file_path="src/main.py",
            line_number=42,
            severity="high",
        )
        assert signal.signal_type == SignalType.AI_REVIEW
        assert signal.source == "codex"
        assert signal.priority == SignalPriority.HIGH
        assert signal.confidence == 0.9  # High severity
        assert signal.metadata["file_path"] == "src/main.py"
        assert signal.metadata["line_number"] == 42

    def test_create_ci_failure_signal_success(self, service):
        """Test creating CI failure signal when CI fails"""
        signal = service.create_ci_failure_signal(
            ci_state="failure",
            failed_checks=["lint", "test"],
            error_message="Tests failed",
        )
        assert signal is not None
        assert signal.signal_type == SignalType.CI_FAILURE
        assert signal.confidence == 1.0
        assert signal.metadata["failed_checks"] == ["lint", "test"]

    def test_create_ci_failure_signal_no_failure(self, service):
        """Test that no signal is created when CI passes"""
        signal = service.create_ci_failure_signal(ci_state="success")
        assert signal is None

        signal = service.create_ci_failure_signal(ci_state="pending")
        assert signal is None

    def test_create_evaluation_regression_signal(self, service):
        """Test creating evaluation regression signal"""
        signal = service.create_evaluation_regression_signal(
            current_score=60,
            previous_score=85,
        )
        assert signal is not None
        assert signal.signal_type == SignalType.EVALUATION_REGRESSION
        assert signal.metadata["score_drop"] == 25
        assert signal.confidence == 0.9  # 20+ drop

    def test_create_evaluation_regression_signal_no_regression(self, service):
        """Test that no signal is created when score improves"""
        signal = service.create_evaluation_regression_signal(
            current_score=85,
            previous_score=80,
        )
        assert signal is None

    def test_create_evaluation_regression_signal_small_drop(self, service):
        """Test that no signal is created for small drops"""
        signal = service.create_evaluation_regression_signal(
            current_score=85,
            previous_score=90,
        )
        assert signal is None  # 5 point drop < 10 threshold

    def test_create_mention_signal_valid(self, service):
        """Test creating mention signal with valid trigger phrase"""
        signal = service.create_mention_signal(
            mention_text="@meta-agent please fix this bug",
            mentioned_by="user123",
            mention_type="comment",
        )
        assert signal is not None
        assert signal.signal_type == SignalType.MENTION
        assert signal.source == "user123"

    def test_create_mention_signal_invalid(self, service):
        """Test that no signal is created without trigger phrase"""
        signal = service.create_mention_signal(
            mention_text="This looks good to me",
            mentioned_by="user123",
        )
        assert signal is None

    def test_create_scheduled_scan_signal_stale(self, service):
        """Test creating scheduled scan signal for stale PR"""
        signal = service.create_scheduled_scan_signal(
            pr_age_days=30,
            last_activity_days=14,
        )
        assert signal is not None
        assert signal.signal_type == SignalType.SCHEDULED_SCAN
        assert signal.confidence == 0.7  # 14 days

    def test_create_scheduled_scan_signal_active(self, service):
        """Test that no signal is created for active PR"""
        signal = service.create_scheduled_scan_signal(
            pr_age_days=10,
            last_activity_days=2,
        )
        assert signal is None  # Less than 7 days

    def test_evaluate_context_no_signals(self, service):
        """Test evaluating context with no signals"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        result = service.evaluate_context(context)

        assert result.should_trigger is False
        assert result.action == TriggerAction.SKIP
        assert "No active signals" in result.reason

    def test_evaluate_context_ci_failure_triggers(self, service):
        """Test that CI failure alone triggers auto-fix"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        signal = TriggerSignal(signal_type=SignalType.CI_FAILURE, source="ci")
        context.add_signal(signal)

        result = service.evaluate_context(context)

        assert result.should_trigger is True
        assert result.action == TriggerAction.AUTO_FIX
        assert result.priority == "high"

    def test_evaluate_context_ai_review_triggers(self, service):
        """Test that AI review alone triggers auto-fix"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        signal = TriggerSignal(signal_type=SignalType.AI_REVIEW, source="codex")
        context.add_signal(signal)

        result = service.evaluate_context(context)

        assert result.should_trigger is True
        assert result.action == TriggerAction.AUTO_FIX
        assert result.priority == "high"

    def test_evaluate_context_mention_requires_hitl(self, service):
        """Test that mention requires HITL approval"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        signal = TriggerSignal(signal_type=SignalType.MENTION, source="user")
        context.add_signal(signal)

        result = service.evaluate_context(context)

        assert result.should_trigger is True
        assert result.action == TriggerAction.MANUAL_REVIEW

    def test_evaluate_context_combined_signals(self, service):
        """Test evaluating context with combined signals"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        ci_signal = TriggerSignal(signal_type=SignalType.CI_FAILURE, source="ci")
        eval_signal = TriggerSignal(
            signal_type=SignalType.EVALUATION_REGRESSION,
            source="evaluation",
        )
        context.add_signal(ci_signal)
        context.add_signal(eval_signal)

        result = service.evaluate_context(context)

        assert result.should_trigger is True
        assert result.action == TriggerAction.AUTO_FIX
        assert len(result.contributing_signals) == 2

    def test_process_ci_state_failure(self, service):
        """Test processing CI failure state"""
        result = service.process_ci_state(
            repo="owner/repo",
            pr_number=123,
            ci_state="failure",
            failed_checks=["lint"],
        )

        assert result.should_trigger is True
        assert result.action == TriggerAction.AUTO_FIX

    def test_process_ci_state_success(self, service):
        """Test processing CI success state"""
        result = service.process_ci_state(
            repo="owner/repo",
            pr_number=123,
            ci_state="success",
        )

        assert result.should_trigger is False

    def test_process_evaluation_result_regression(self, service):
        """Test processing evaluation regression"""
        result = service.process_evaluation_result(
            repo="owner/repo",
            pr_number=123,
            current_score=50,
            previous_score=80,
        )

        assert result.should_trigger is True

    def test_process_mention(self, service):
        """Test processing mention"""
        result = service.process_mention(
            repo="owner/repo",
            pr_number=123,
            mention_text="@meta-agent please fix this",
            mentioned_by="user123",
        )

        assert result.should_trigger is True
        assert result.action == TriggerAction.MANUAL_REVIEW

    def test_process_ai_review(self, service):
        """Test processing AI review"""
        result = service.process_ai_review(
            repo="owner/repo",
            pr_number=123,
            source="gemini",
            comment_body="Consider using a more efficient algorithm",
            severity="medium",
        )

        assert result.should_trigger is True
        assert result.action == TriggerAction.AUTO_FIX

    def test_clear_context(self, service):
        """Test clearing context"""
        service.get_or_create_context("owner/repo", 123)
        assert service.clear_context("owner/repo", 123) is True
        assert service.clear_context("owner/repo", 123) is False  # Already cleared

    def test_get_stats(self, service):
        """Test getting service statistics"""
        service.process_ci_state("owner/repo", 123, "failure")
        service.process_ai_review("owner/repo", 456, "codex", "Fix this", severity="high")

        stats = service.get_stats()
        assert stats["context_count"] == 2
        assert stats["total_signals"] == 2
        assert "ci_failure" in stats["signal_type_counts"]
        assert "ai_review" in stats["signal_type_counts"]


class TestPriorityLogic:
    """Tests for priority logic: AI review > CI failure > Evaluation regression > Mention"""

    @pytest.fixture
    def service(self):
        return MultiSignalTriggerService()

    def test_ai_review_highest_priority(self, service):
        """Test that AI review has highest priority"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        context.add_signal(TriggerSignal(
            signal_type=SignalType.SCHEDULED_SCAN,
            source="scheduler",
        ))
        context.add_signal(TriggerSignal(
            signal_type=SignalType.AI_REVIEW,
            source="codex",
        ))

        highest = context.get_highest_priority_signal()
        assert highest.signal_type == SignalType.AI_REVIEW

    def test_ci_failure_over_evaluation(self, service):
        """Test that CI failure has higher priority than evaluation regression"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        context.add_signal(TriggerSignal(
            signal_type=SignalType.EVALUATION_REGRESSION,
            source="evaluation",
        ))
        context.add_signal(TriggerSignal(
            signal_type=SignalType.CI_FAILURE,
            source="ci",
        ))

        highest = context.get_highest_priority_signal()
        assert highest.signal_type == SignalType.CI_FAILURE

    def test_evaluation_over_mention(self, service):
        """Test that evaluation regression has same priority as mention"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        context.add_signal(TriggerSignal(
            signal_type=SignalType.MENTION,
            source="user",
        ))
        context.add_signal(TriggerSignal(
            signal_type=SignalType.EVALUATION_REGRESSION,
            source="evaluation",
        ))

        highest = context.get_highest_priority_signal()
        # Both are medium priority, first added wins
        assert highest.priority == SignalPriority.MEDIUM

    def test_mention_over_scheduled_scan(self, service):
        """Test that mention has higher priority than scheduled scan"""
        context = MultiSignalContext(pr_number=123, repo="owner/repo")
        context.add_signal(TriggerSignal(
            signal_type=SignalType.SCHEDULED_SCAN,
            source="scheduler",
        ))
        context.add_signal(TriggerSignal(
            signal_type=SignalType.MENTION,
            source="user",
        ))

        highest = context.get_highest_priority_signal()
        assert highest.signal_type == SignalType.MENTION


class TestTriggerEvaluationResult:
    """Tests for TriggerEvaluationResult dataclass"""

    def test_result_to_dict(self):
        """Test result serialization"""
        signal = TriggerSignal(signal_type=SignalType.CI_FAILURE, source="ci")
        result = TriggerEvaluationResult(
            should_trigger=True,
            action=TriggerAction.AUTO_FIX,
            priority="high",
            reason="CI failure detected",
            contributing_signals=[signal],
            confidence=0.95,
        )

        data = result.to_dict()
        assert data["should_trigger"] is True
        assert data["action"] == "auto_fix"
        assert data["priority"] == "high"
        assert data["confidence"] == 0.95
        assert len(data["contributing_signals"]) == 1
