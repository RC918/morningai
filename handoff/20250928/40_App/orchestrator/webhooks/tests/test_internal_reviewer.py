#!/usr/bin/env python3
"""
Tests for Internal Reviewer Agent - Phase 7 Issue #2212

This module tests the InternalReviewerService and related components
for the Internal Reviewer Agent re-review mechanism.
"""
from webhooks.internal_reviewer import (
    InternalReviewerService,
    InternalReviewerTask,
    InternalReviewResult,
    InternalReviewStatus,
    InternalReviewAction,
    AIReviewerAgreement,
    create_internal_review_task,
)


class TestInternalReviewerTask:
    """Tests for InternalReviewerTask dataclass"""

    def test_create_task_with_defaults(self):
        """Test creating a task with default values"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
        )

        assert task.task_id == "test-123"
        assert task.trace_id == "trace-456"
        assert task.original_pr_number == 100
        assert task.repo == "owner/repo"
        assert task.initial_ai_review == {}
        assert task.follow_up_result == {}
        assert task.triage_result == {}
        assert task.comment_body == ""
        assert task.file_path == ""
        assert task.line_number == 0
        assert task.ci_state == "unknown"
        assert task.code_quality_score == 100
        assert task.status == InternalReviewStatus.PENDING
        assert task.action is None

    def test_create_task_with_all_fields(self):
        """Test creating a task with all fields specified"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "severity": "medium"},
            follow_up_result={"status": "completed", "fix_applied": True},
            triage_result={"category": "bug", "risk_level": "medium"},
            comment_body="Fix the bug",
            file_path="src/main.py",
            line_number=42,
            ci_state="success",
            code_quality_score=85,
        )

        assert task.initial_ai_review == {"decision": "needs_changes", "severity": "medium"}
        assert task.follow_up_result == {"status": "completed", "fix_applied": True}
        assert task.triage_result == {"category": "bug", "risk_level": "medium"}
        assert task.comment_body == "Fix the bug"
        assert task.file_path == "src/main.py"
        assert task.line_number == 42
        assert task.ci_state == "success"
        assert task.code_quality_score == 85


class TestCreateInternalReviewTask:
    """Tests for create_internal_review_task factory function"""

    def test_creates_task_with_unique_id(self):
        """Test that factory creates task with unique ID"""
        task1 = create_internal_review_task(
            trace_id="trace-1",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={},
            follow_up_result={},
        )
        task2 = create_internal_review_task(
            trace_id="trace-2",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={},
            follow_up_result={},
        )

        assert task1.task_id != task2.task_id
        assert task1.task_id.startswith("internal-review-")
        assert task2.task_id.startswith("internal-review-")

    def test_creates_task_with_all_parameters(self):
        """Test factory creates task with all parameters"""
        task = create_internal_review_task(
            trace_id="trace-123",
            original_pr_number=200,
            repo="test/repo",
            initial_ai_review={"decision": "approve"},
            follow_up_result={"status": "completed"},
            triage_result={"category": "style"},
            comment_body="Style fix",
            file_path="src/style.css",
            line_number=10,
            ci_state="success",
            code_quality_score=90,
        )

        assert task.trace_id == "trace-123"
        assert task.original_pr_number == 200
        assert task.repo == "test/repo"
        assert task.initial_ai_review == {"decision": "approve"}
        assert task.follow_up_result == {"status": "completed"}
        assert task.triage_result == {"category": "style"}
        assert task.comment_body == "Style fix"
        assert task.file_path == "src/style.css"
        assert task.line_number == 10
        assert task.ci_state == "success"
        assert task.code_quality_score == 90


class TestInternalReviewerService:
    """Tests for InternalReviewerService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = InternalReviewerService()

    def test_perform_internal_review_basic(self):
        """Test basic internal review"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "severity": "medium"},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=85,
        )

        result = self.service.perform_internal_review(task)

        assert isinstance(result, InternalReviewResult)
        assert result.task_id == "test-123"
        assert result.trace_id == "trace-456"
        assert result.status == InternalReviewStatus.COMPLETED
        assert result.action in [
            InternalReviewAction.APPROVE,
            InternalReviewAction.REQUEST_CHANGES,
            InternalReviewAction.ESCALATE,
        ]
        assert result.agreement in [
            AIReviewerAgreement.AGREE,
            AIReviewerAgreement.PARTIAL,
            AIReviewerAgreement.DISAGREE,
        ]
        assert isinstance(result.comment_addressed, bool)
        assert result.addressing_quality in ["good", "partial", "poor"]
        assert isinstance(result.quality_score_delta, int)
        assert result.severity_assessment in ["none", "low", "medium", "high", "critical", "unknown"]
        assert result.regression_risk in ["low", "medium", "high"]
        assert isinstance(result.summary, str)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.requires_hitl, bool)
        assert result.review_time_ms > 0

    def test_comment_addressed_with_fix_applied(self):
        """Test that comment is marked as addressed when fix is applied"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
        )

        result = self.service.perform_internal_review(task)

        assert result.comment_addressed is True

    def test_comment_addressed_with_pr_created(self):
        """Test that comment is marked as addressed when PR is created"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "pr_created": True},
            ci_state="pending",
        )

        result = self.service.perform_internal_review(task)

        assert result.comment_addressed is True

    def test_comment_not_addressed_without_follow_up(self):
        """Test that comment is not addressed without follow-up result"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={},
            ci_state="pending",
        )

        result = self.service.perform_internal_review(task)

        assert result.comment_addressed is False

    def test_addressing_quality_good(self):
        """Test good addressing quality with high score"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"quality_score": 70},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=90,
        )

        result = self.service.perform_internal_review(task)

        assert result.addressing_quality == "good"

    def test_addressing_quality_partial(self):
        """Test partial addressing quality with medium score"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.addressing_quality == "partial"

    def test_addressing_quality_poor_not_addressed(self):
        """Test poor addressing quality when not addressed"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={},
            ci_state="pending",
            code_quality_score=30,
        )

        result = self.service.perform_internal_review(task)

        assert result.addressing_quality == "poor"

    def test_quality_score_delta_positive(self):
        """Test positive quality score delta"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"quality_score": 60},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=80,
        )

        result = self.service.perform_internal_review(task)

        assert result.quality_score_delta == 20

    def test_quality_score_delta_negative(self):
        """Test negative quality score delta"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"quality_score": 80},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=60,
        )

        result = self.service.perform_internal_review(task)

        assert result.quality_score_delta == -20

    def test_regression_risk_high_with_ci_failure(self):
        """Test high regression risk with CI failure"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="failure",
            code_quality_score=50,
        )

        result = self.service.perform_internal_review(task)

        assert result.regression_risk == "high"

    def test_regression_risk_high_with_large_quality_drop(self):
        """Test high regression risk with large quality score drop"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=60,
        )

        result = self.service.perform_internal_review(task)

        assert result.regression_risk == "high"

    def test_regression_risk_medium_with_security_category(self):
        """Test medium regression risk with security category"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            triage_result={"category": "security"},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=85,
        )

        result = self.service.perform_internal_review(task)

        assert result.regression_risk == "medium"

    def test_regression_risk_low_with_success(self):
        """Test low regression risk with successful CI and good quality"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"quality_score": 80},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=85,
        )

        result = self.service.perform_internal_review(task)

        assert result.regression_risk == "low"

    def test_agreement_agree_with_addressed_comment(self):
        """Test agreement when comment is addressed with good quality"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 70},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=90,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.AGREE

    def test_agreement_partial_with_partial_quality(self):
        """Test partial agreement with partial addressing quality"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL

    def test_action_approve_with_success(self):
        """Test approve action with successful CI and agreement"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 70},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=90,
        )

        result = self.service.perform_internal_review(task)

        assert result.action == InternalReviewAction.APPROVE

    def test_action_escalate_with_high_regression_risk(self):
        """Test escalate action with high regression risk"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="failure",
            code_quality_score=30,
        )

        result = self.service.perform_internal_review(task)

        assert result.action == InternalReviewAction.ESCALATE

    def test_hitl_required_for_escalate(self):
        """Test HITL required for escalate action"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="failure",
            code_quality_score=30,
        )

        result = self.service.perform_internal_review(task)

        assert result.requires_hitl is True

    def test_hitl_required_for_security_category(self):
        """Test HITL required for security category"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            triage_result={"category": "security"},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=85,
        )

        result = self.service.perform_internal_review(task)

        assert result.requires_hitl is True

    def test_hitl_required_for_high_risk(self):
        """Test HITL required for high risk level"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            triage_result={"risk_level": "high"},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=85,
        )

        result = self.service.perform_internal_review(task)

        assert result.requires_hitl is True

    def test_hitl_required_for_high_severity(self):
        """Test HITL required for high severity initial review"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"severity": "high"},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=85,
        )

        result = self.service.perform_internal_review(task)

        assert result.requires_hitl is True

    def test_hitl_not_required_for_low_risk_approve(self):
        """Test HITL not required for low risk approve"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "severity": "low", "quality_score": 70},
            triage_result={"category": "style", "risk_level": "low"},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=90,
        )

        result = self.service.perform_internal_review(task)

        assert result.requires_hitl is False

    def test_summary_generation(self):
        """Test summary generation"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 70},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=90,
        )

        result = self.service.perform_internal_review(task)

        assert "Comment addressed" in result.summary
        assert "CI checks passing" in result.summary

    def test_recommendations_for_ci_failure(self):
        """Test recommendations include CI fix for failure"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="failure",
            code_quality_score=50,
        )

        result = self.service.perform_internal_review(task)

        assert any("CI" in rec for rec in result.recommendations)

    def test_recommendations_for_not_addressed(self):
        """Test recommendations include review comment when not addressed"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            comment_body="Please fix the null pointer exception",
            follow_up_result={},
            ci_state="pending",
        )

        result = self.service.perform_internal_review(task)

        assert any("comment" in rec.lower() for rec in result.recommendations)

    def test_task_status_updated_to_completed(self):
        """Test task status is updated to completed after review"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
        )

        assert task.status == InternalReviewStatus.PENDING

        self.service.perform_internal_review(task)

        assert task.status == InternalReviewStatus.COMPLETED

    def test_task_action_updated_after_review(self):
        """Test task action is updated after review"""
        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
        )

        assert task.action is None

        self.service.perform_internal_review(task)

        assert task.action is not None


class TestInternalReviewEnums:
    """Tests for Internal Review enums"""

    def test_internal_review_status_values(self):
        """Test InternalReviewStatus enum values"""
        assert InternalReviewStatus.PENDING.value == "pending"
        assert InternalReviewStatus.REVIEWING.value == "reviewing"
        assert InternalReviewStatus.COMPLETED.value == "completed"
        assert InternalReviewStatus.FAILED.value == "failed"

    def test_internal_review_action_values(self):
        """Test InternalReviewAction enum values"""
        assert InternalReviewAction.APPROVE.value == "approve"
        assert InternalReviewAction.REQUEST_CHANGES.value == "request_changes"
        assert InternalReviewAction.ESCALATE.value == "escalate"

    def test_ai_reviewer_agreement_values(self):
        """Test AIReviewerAgreement enum values"""
        assert AIReviewerAgreement.AGREE.value == "agree"
        assert AIReviewerAgreement.PARTIAL.value == "partial"
        assert AIReviewerAgreement.DISAGREE.value == "disagree"


class TestInternalReviewResult:
    """Tests for InternalReviewResult dataclass"""

    def test_create_result_with_all_fields(self):
        """Test creating result with all fields"""
        result = InternalReviewResult(
            task_id="test-123",
            trace_id="trace-456",
            status=InternalReviewStatus.COMPLETED,
            action=InternalReviewAction.APPROVE,
            agreement=AIReviewerAgreement.AGREE,
            comment_addressed=True,
            addressing_quality="good",
            quality_score_delta=10,
            severity_assessment="low",
            regression_risk="low",
            summary="All good",
            recommendations=["No action needed"],
            requires_hitl=False,
            review_time_ms=100.5,
        )

        assert result.task_id == "test-123"
        assert result.trace_id == "trace-456"
        assert result.status == InternalReviewStatus.COMPLETED
        assert result.action == InternalReviewAction.APPROVE
        assert result.agreement == AIReviewerAgreement.AGREE
        assert result.comment_addressed is True
        assert result.addressing_quality == "good"
        assert result.quality_score_delta == 10
        assert result.severity_assessment == "low"
        assert result.regression_risk == "low"
        assert result.summary == "All good"
        assert result.recommendations == ["No action needed"]
        assert result.requires_hitl is False
        assert result.review_time_ms == 100.5


class TestPartialPolicyConfiguration:
    """
    Tests for Issue #2264: Configurable PARTIAL agreement policy.

    The INTERNAL_REVIEW_PARTIAL_POLICY environment variable controls
    how PARTIAL agreement is handled:
    - "optimistic" (default): PARTIAL + CI success → APPROVE
    - "conservative": PARTIAL → always REQUEST_CHANGES
    """

    def setup_method(self):
        """Set up test fixtures"""
        self.service = InternalReviewerService()

    def test_optimistic_policy_partial_ci_success_approves(self, monkeypatch):
        """Test optimistic policy: PARTIAL + CI success → APPROVE"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "optimistic")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL
        assert result.action == InternalReviewAction.APPROVE

    def test_optimistic_policy_partial_ci_failure_requests_changes(self, monkeypatch):
        """Test optimistic policy: PARTIAL + CI failure → REQUEST_CHANGES"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "optimistic")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="pending",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL
        assert result.action == InternalReviewAction.REQUEST_CHANGES

    def test_conservative_policy_partial_ci_success_requests_changes(self, monkeypatch):
        """Test conservative policy: PARTIAL + CI success → REQUEST_CHANGES"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "conservative")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL
        assert result.action == InternalReviewAction.REQUEST_CHANGES

    def test_conservative_policy_partial_ci_failure_requests_changes(self, monkeypatch):
        """Test conservative policy: PARTIAL + CI failure → REQUEST_CHANGES"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "conservative")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="pending",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL
        assert result.action == InternalReviewAction.REQUEST_CHANGES

    def test_policy_case_insensitive(self, monkeypatch):
        """Test that policy value is case insensitive"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "CONSERVATIVE")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL
        assert result.action == InternalReviewAction.REQUEST_CHANGES

    def test_unknown_policy_defaults_to_optimistic(self, monkeypatch):
        """Test that unknown policy value defaults to optimistic behavior"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "unknown_value")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 90},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=70,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.PARTIAL
        assert result.action == InternalReviewAction.APPROVE

    def test_agree_action_unaffected_by_policy(self, monkeypatch):
        """Test that AGREE action is not affected by PARTIAL policy"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "conservative")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "needs_changes", "quality_score": 70},
            follow_up_result={"status": "completed", "fix_applied": True},
            ci_state="success",
            code_quality_score=90,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.AGREE
        assert result.action == InternalReviewAction.APPROVE

    def test_disagree_action_unaffected_by_policy(self, monkeypatch):
        """Test that DISAGREE action is not affected by PARTIAL policy"""
        import webhooks.internal_reviewer as ir_module
        monkeypatch.setattr(ir_module, "INTERNAL_REVIEW_PARTIAL_POLICY", "optimistic")

        task = InternalReviewerTask(
            task_id="test-123",
            trace_id="trace-456",
            original_pr_number=100,
            repo="owner/repo",
            initial_ai_review={"decision": "approve"},
            follow_up_result={},
            ci_state="pending",
            code_quality_score=30,
        )

        result = self.service.perform_internal_review(task)

        assert result.agreement == AIReviewerAgreement.DISAGREE
        assert result.action == InternalReviewAction.ESCALATE
