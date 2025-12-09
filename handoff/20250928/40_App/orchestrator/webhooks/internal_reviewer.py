#!/usr/bin/env python3
"""
Internal Reviewer Agent - Phase 7 Issue #2212

This module implements the Internal Reviewer Agent re-review mechanism,
which validates AI reviewer assessments after fixes are applied.

The Internal Reviewer Agent:
1. Re-reviews AI reviewer comments after follow-up actions
2. Validates whether fixes correctly addressed the original comments
3. Compares initial AI reviewer assessment with current state
4. Determines if HITL approval is required for high-risk re-reviews

Usage:
    from webhooks.internal_reviewer import (
        InternalReviewerService,
        InternalReviewerTask,
        InternalReviewStatus,
        InternalReviewAction,
    )

    service = InternalReviewerService()
    task = InternalReviewerTask(
        task_id="task-123",
        trace_id="trace-456",
        original_pr_number=100,
        repo="owner/repo",
        initial_ai_review={"decision": "needs_changes", "severity": "medium"},
        follow_up_result={"status": "completed", "fix_applied": True},
    )
    result = service.perform_internal_review(task)
"""
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class InternalReviewStatus(Enum):
    """Status of an internal review task"""
    PENDING = "pending"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class InternalReviewAction(Enum):
    """Action determined by internal review"""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    ESCALATE = "escalate"


class AIReviewerAgreement(Enum):
    """Agreement level between internal review and initial AI review"""
    AGREE = "agree"
    PARTIAL = "partial"
    DISAGREE = "disagree"


@dataclass
class InternalReviewerTask:
    """
    Task data for internal re-review.

    Issue #2212: Defines the schema for internal reviewer tasks.
    """
    task_id: str
    trace_id: str
    original_pr_number: int
    repo: str
    initial_ai_review: Dict[str, Any] = field(default_factory=dict)
    follow_up_result: Dict[str, Any] = field(default_factory=dict)
    triage_result: Dict[str, Any] = field(default_factory=dict)
    comment_body: str = ""
    file_path: str = ""
    line_number: int = 0
    ci_state: str = "unknown"
    code_quality_score: int = 100
    status: InternalReviewStatus = InternalReviewStatus.PENDING
    action: Optional[InternalReviewAction] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class InternalReviewResult:
    """
    Result of internal re-review.

    Issue #2212: Contains the assessment from the internal reviewer.
    """
    task_id: str
    trace_id: str
    status: InternalReviewStatus
    action: InternalReviewAction
    agreement: AIReviewerAgreement
    comment_addressed: bool
    addressing_quality: str
    quality_score_delta: int
    severity_assessment: str
    regression_risk: str
    summary: str
    recommendations: List[str] = field(default_factory=list)
    requires_hitl: bool = False
    review_time_ms: float = 0.0


class InternalReviewerService:
    """
    Service for performing internal re-reviews of AI reviewer assessments.

    Issue #2212: Internal Reviewer Agent Re-review Mechanism

    This service:
    1. Validates initial AI reviewer assessments
    2. Compares with current state after follow-up actions
    3. Determines if the fix addressed the original comment
    4. Assesses code quality changes
    5. Identifies potential regressions
    6. Determines HITL approval requirements
    """

    SEVERITY_ORDER = {
        "none": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    QUALITY_THRESHOLDS = {
        "good": 80,
        "partial": 50,
        "poor": 0,
    }

    def __init__(self):
        """Initialize the Internal Reviewer Service"""
        self.logger = logging.getLogger(__name__)

    def perform_internal_review(
        self,
        task: InternalReviewerTask
    ) -> InternalReviewResult:
        """
        Perform internal re-review of an AI reviewer assessment.

        Args:
            task: InternalReviewerTask containing review context

        Returns:
            InternalReviewResult with re-review assessment
        """
        start_time = time.time()

        self.logger.info(
            "[InternalReviewer] Starting internal re-review",
            extra={
                "operation": "internal_review",
                "trace_id": task.trace_id,
                "task_id": task.task_id,
                "original_pr_number": task.original_pr_number,
            }
        )

        task.status = InternalReviewStatus.REVIEWING

        try:
            comment_addressed = self._check_comment_addressed(task)
            addressing_quality = self._assess_addressing_quality(task, comment_addressed)
            quality_delta = self._calculate_quality_delta(task)
            severity_assessment = self._assess_severity(task)
            regression_risk = self._assess_regression_risk(task)
            agreement = self._determine_agreement(task, comment_addressed, addressing_quality)
            action = self._determine_action(task, agreement, regression_risk)
            requires_hitl = self._determine_hitl_requirement(task, action, agreement)
            summary = self._generate_summary(
                task, comment_addressed, addressing_quality, agreement, action
            )
            recommendations = self._generate_recommendations(
                task, comment_addressed, addressing_quality, regression_risk
            )

            review_time_ms = (time.time() - start_time) * 1000

            result = InternalReviewResult(
                task_id=task.task_id,
                trace_id=task.trace_id,
                status=InternalReviewStatus.COMPLETED,
                action=action,
                agreement=agreement,
                comment_addressed=comment_addressed,
                addressing_quality=addressing_quality,
                quality_score_delta=quality_delta,
                severity_assessment=severity_assessment,
                regression_risk=regression_risk,
                summary=summary,
                recommendations=recommendations,
                requires_hitl=requires_hitl,
                review_time_ms=review_time_ms,
            )

            task.status = InternalReviewStatus.COMPLETED
            task.action = action

            self.logger.info(
                "[InternalReviewer] Internal re-review completed",
                extra={
                    "operation": "internal_review",
                    "trace_id": task.trace_id,
                    "task_id": task.task_id,
                    "action": action.value,
                    "agreement": agreement.value,
                    "comment_addressed": comment_addressed,
                    "requires_hitl": requires_hitl,
                    "review_time_ms": review_time_ms,
                }
            )

            return result

        except Exception as e:
            task.status = InternalReviewStatus.FAILED
            review_time_ms = (time.time() - start_time) * 1000

            self.logger.error(
                f"[InternalReviewer] Internal re-review failed: {e}",
                extra={
                    "operation": "internal_review",
                    "trace_id": task.trace_id,
                    "task_id": task.task_id,
                    "error": str(e),
                },
                exc_info=True
            )

            return InternalReviewResult(
                task_id=task.task_id,
                trace_id=task.trace_id,
                status=InternalReviewStatus.FAILED,
                action=InternalReviewAction.ESCALATE,
                agreement=AIReviewerAgreement.DISAGREE,
                comment_addressed=False,
                addressing_quality="unknown",
                quality_score_delta=0,
                severity_assessment="unknown",
                regression_risk="high",
                summary=f"Internal review failed: {str(e)}",
                recommendations=["Manual review required due to internal review failure"],
                requires_hitl=True,
                review_time_ms=review_time_ms,
            )

    def _check_comment_addressed(self, task: InternalReviewerTask) -> bool:
        """
        Check if the original AI reviewer comment was addressed.

        Args:
            task: InternalReviewerTask

        Returns:
            True if comment was addressed, False otherwise
        """
        follow_up = task.follow_up_result

        if not follow_up:
            return False

        if follow_up.get("status") == "completed":
            if follow_up.get("fix_applied", False):
                return True
            if follow_up.get("pr_created", False):
                return True

        if task.ci_state == "success":
            initial_ci = task.initial_ai_review.get("ci_state", "unknown")
            if initial_ci in ("failure", "pending"):
                return True

        return False

    def _assess_addressing_quality(
        self,
        task: InternalReviewerTask,
        comment_addressed: bool
    ) -> str:
        """
        Assess the quality of how the comment was addressed.

        Args:
            task: InternalReviewerTask
            comment_addressed: Whether comment was addressed

        Returns:
            Quality assessment: "good", "partial", or "poor"
        """
        if not comment_addressed:
            return "poor"

        score = task.code_quality_score
        initial_score = task.initial_ai_review.get("quality_score", 50)

        if score >= self.QUALITY_THRESHOLDS["good"]:
            if score >= initial_score:
                return "good"
            return "partial"

        if score >= self.QUALITY_THRESHOLDS["partial"]:
            return "partial"

        return "poor"

    def _calculate_quality_delta(self, task: InternalReviewerTask) -> int:
        """
        Calculate the change in code quality score.

        Args:
            task: InternalReviewerTask

        Returns:
            Delta between current and initial quality scores
        """
        current_score = task.code_quality_score
        initial_score = task.initial_ai_review.get("quality_score", 50)
        return current_score - initial_score

    def _assess_severity(self, task: InternalReviewerTask) -> str:
        """
        Assess the current severity level.

        Args:
            task: InternalReviewerTask

        Returns:
            Severity assessment
        """
        initial_severity = task.initial_ai_review.get("severity", "medium")
        triage_risk = task.triage_result.get("risk_level", "medium")

        initial_val = self.SEVERITY_ORDER.get(initial_severity, 2)
        triage_val = self.SEVERITY_ORDER.get(triage_risk, 2)

        if task.ci_state == "success":
            return "low" if initial_val <= 2 else "medium"

        if task.ci_state == "failure":
            return "high"

        return initial_severity if initial_val >= triage_val else triage_risk

    def _assess_regression_risk(self, task: InternalReviewerTask) -> str:
        """
        Assess the risk of regression from the fix.

        Args:
            task: InternalReviewerTask

        Returns:
            Regression risk: "low", "medium", or "high"
        """
        if task.ci_state == "failure":
            return "high"

        quality_delta = self._calculate_quality_delta(task)
        if quality_delta < -20:
            return "high"
        if quality_delta < -10:
            return "medium"

        triage_category = task.triage_result.get("category", "")
        if triage_category in ("security", "critical"):
            return "medium"

        return "low"

    def _determine_agreement(
        self,
        task: InternalReviewerTask,
        comment_addressed: bool,
        addressing_quality: str
    ) -> AIReviewerAgreement:
        """
        Determine agreement level with initial AI reviewer assessment.

        Args:
            task: InternalReviewerTask
            comment_addressed: Whether comment was addressed
            addressing_quality: Quality of addressing

        Returns:
            Agreement level
        """
        initial_decision = task.initial_ai_review.get("decision", "needs_changes")

        if comment_addressed and addressing_quality == "good":
            if initial_decision in ("needs_changes", "request_changes"):
                return AIReviewerAgreement.AGREE
            return AIReviewerAgreement.PARTIAL

        if comment_addressed and addressing_quality == "partial":
            return AIReviewerAgreement.PARTIAL

        if not comment_addressed:
            if initial_decision in ("needs_changes", "request_changes"):
                return AIReviewerAgreement.AGREE
            return AIReviewerAgreement.DISAGREE

        return AIReviewerAgreement.PARTIAL

    def _determine_action(
        self,
        task: InternalReviewerTask,
        agreement: AIReviewerAgreement,
        regression_risk: str
    ) -> InternalReviewAction:
        """
        Determine the action to take based on re-review.

        Args:
            task: InternalReviewerTask
            agreement: Agreement level with initial review
            regression_risk: Regression risk assessment

        Returns:
            Action to take
        """
        if regression_risk == "high":
            return InternalReviewAction.ESCALATE

        if agreement == AIReviewerAgreement.DISAGREE:
            return InternalReviewAction.ESCALATE

        if task.ci_state == "success" and agreement == AIReviewerAgreement.AGREE:
            return InternalReviewAction.APPROVE

        if agreement == AIReviewerAgreement.PARTIAL:
            if task.ci_state == "success":
                return InternalReviewAction.APPROVE
            return InternalReviewAction.REQUEST_CHANGES

        return InternalReviewAction.REQUEST_CHANGES

    def _determine_hitl_requirement(
        self,
        task: InternalReviewerTask,
        action: InternalReviewAction,
        agreement: AIReviewerAgreement
    ) -> bool:
        """
        Determine if HITL approval is required.

        Args:
            task: InternalReviewerTask
            action: Determined action
            agreement: Agreement level

        Returns:
            True if HITL approval is required
        """
        if action == InternalReviewAction.ESCALATE:
            return True

        if agreement == AIReviewerAgreement.DISAGREE:
            return True

        triage_category = task.triage_result.get("category", "")
        if triage_category in ("security", "critical"):
            return True

        triage_risk = task.triage_result.get("risk_level", "")
        if triage_risk == "high":
            return True

        initial_severity = task.initial_ai_review.get("severity", "")
        if initial_severity in ("high", "critical"):
            return True

        return False

    def _generate_summary(
        self,
        task: InternalReviewerTask,
        comment_addressed: bool,
        addressing_quality: str,
        agreement: AIReviewerAgreement,
        action: InternalReviewAction
    ) -> str:
        """
        Generate a summary of the internal re-review.

        Args:
            task: InternalReviewerTask
            comment_addressed: Whether comment was addressed
            addressing_quality: Quality of addressing
            agreement: Agreement level
            action: Determined action

        Returns:
            Summary string
        """
        parts = []

        if comment_addressed:
            parts.append(f"Comment addressed with {addressing_quality} quality.")
        else:
            parts.append("Comment not fully addressed.")

        parts.append(f"Internal review {agreement.value}s with initial AI assessment.")

        if action == InternalReviewAction.APPROVE:
            parts.append("Recommending approval.")
        elif action == InternalReviewAction.REQUEST_CHANGES:
            parts.append("Requesting additional changes.")
        else:
            parts.append("Escalating for human review.")

        if task.ci_state == "success":
            parts.append("CI checks passing.")
        elif task.ci_state == "failure":
            parts.append("CI checks failing.")

        return " ".join(parts)

    def _generate_recommendations(
        self,
        task: InternalReviewerTask,
        comment_addressed: bool,
        addressing_quality: str,
        regression_risk: str
    ) -> List[str]:
        """
        Generate recommendations based on re-review.

        Args:
            task: InternalReviewerTask
            comment_addressed: Whether comment was addressed
            addressing_quality: Quality of addressing
            regression_risk: Regression risk

        Returns:
            List of recommendations
        """
        recommendations = []

        if not comment_addressed:
            recommendations.append(
                f"Review original comment: {task.comment_body[:100]}..."
                if len(task.comment_body) > 100
                else f"Review original comment: {task.comment_body}"
            )

        if addressing_quality == "partial":
            recommendations.append("Consider additional improvements to fully address the comment.")

        if addressing_quality == "poor":
            recommendations.append("Significant rework may be needed to address the comment.")

        if regression_risk == "high":
            recommendations.append("High regression risk detected. Thorough testing recommended.")
        elif regression_risk == "medium":
            recommendations.append("Moderate regression risk. Additional review recommended.")

        if task.ci_state == "failure":
            recommendations.append("Fix CI failures before proceeding.")

        if not recommendations:
            recommendations.append("No additional actions required.")

        return recommendations


def create_internal_review_task(
    trace_id: str,
    original_pr_number: int,
    repo: str,
    initial_ai_review: Dict[str, Any],
    follow_up_result: Dict[str, Any],
    triage_result: Optional[Dict[str, Any]] = None,
    comment_body: str = "",
    file_path: str = "",
    line_number: int = 0,
    ci_state: str = "unknown",
    code_quality_score: int = 100,
) -> InternalReviewerTask:
    """
    Factory function to create an InternalReviewerTask.

    Args:
        trace_id: Trace ID for logging
        original_pr_number: Original PR number
        repo: Repository in owner/repo format
        initial_ai_review: Initial AI reviewer assessment
        follow_up_result: Result from follow-up execution
        triage_result: Result from comment triage
        comment_body: Original comment body
        file_path: File path from comment
        line_number: Line number from comment
        ci_state: Current CI state
        code_quality_score: Current code quality score

    Returns:
        InternalReviewerTask instance
    """
    import uuid

    task_id = f"internal-review-{uuid.uuid4().hex[:8]}"

    return InternalReviewerTask(
        task_id=task_id,
        trace_id=trace_id,
        original_pr_number=original_pr_number,
        repo=repo,
        initial_ai_review=initial_ai_review,
        follow_up_result=follow_up_result,
        triage_result=triage_result or {},
        comment_body=comment_body,
        file_path=file_path,
        line_number=line_number,
        ci_state=ci_state,
        code_quality_score=code_quality_score,
    )
