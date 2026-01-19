"""
Tests for B-9.5 Priority-based Filtering + Approval Threshold

Issue #3918: Priority-based Filtering + Approval Threshold for MultiSpecialistReviewer

Tests cover:
1. Security findings (high/critical) always blocking
2. Performance findings require 3+ retries
3. Architecture/CORRECTNESS findings can be force-approved after 2 retries
4. Filtered findings based on retry count
5. Edge cases (empty findings, mixed specialists)
"""

from review_context.multi_specialist_reviewer import (
    ReviewSpecialist,
    SpecialistFinding,
    ForceApproveResult,
    should_force_approve,
    filter_findings_by_priority,
)


class TestForceApproveResult:
    """Tests for ForceApproveResult dataclass."""

    def test_create_force_approve_result(self):
        """Test creating a ForceApproveResult."""
        result = ForceApproveResult(
            should_approve=True,
            reason="Force-approved after 2 retries",
            blocked_by=[],
            filtered_findings=[],
        )
        assert result.should_approve is True
        assert result.reason == "Force-approved after 2 retries"
        assert result.blocked_by == []
        assert result.filtered_findings == []

    def test_to_dict(self):
        """Test converting ForceApproveResult to dictionary."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.ARCHITECTURE,
            severity="medium",
            category="coupling",
            message="Tight coupling",
        )
        result = ForceApproveResult(
            should_approve=False,
            reason="Blocked by PERFORMANCE",
            blocked_by=["PERFORMANCE"],
            filtered_findings=[finding],
        )
        d = result.to_dict()
        assert d["should_approve"] is False
        assert d["reason"] == "Blocked by PERFORMANCE"
        assert d["blocked_by"] == ["PERFORMANCE"]
        assert d["filtered_findings_count"] == 1


class TestShouldForceApprove:
    """Tests for should_force_approve function."""

    def test_empty_findings(self):
        """Test with empty findings list."""
        result = should_force_approve([], retry_count=0)
        assert result.should_approve is False
        assert result.reason == "No findings to evaluate"
        assert result.blocked_by == []
        assert result.filtered_findings == []

    def test_security_high_always_blocking(self):
        """Test that high severity security findings are always blocking."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection vulnerability",
            ),
        ]

        # Even with high retry count, security blockers should never be force-approved
        for retry_count in [0, 1, 2, 3, 5, 10]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is False
            assert "SECURITY" in result.blocked_by
            assert "Security blockers" in result.reason

    def test_security_critical_always_blocking(self):
        """Test that critical severity security findings are always blocking."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="critical",
                category="auth",
                message="Authentication bypass",
            ),
        ]

        result = should_force_approve(findings, retry_count=10)
        assert result.should_approve is False
        assert "SECURITY" in result.blocked_by

    def test_security_low_not_blocking(self):
        """Test that low severity security findings are not blocking after 2 retries."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="low",
                category="info",
                message="Informational security note",
            ),
        ]

        # Low severity security should be force-approved after 2 retries
        result = should_force_approve(findings, retry_count=2)
        assert result.should_approve is True

    def test_security_medium_not_blocking(self):
        """Test that medium severity security findings are not blocking after 2 retries."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="medium",
                category="config",
                message="Configuration issue",
            ),
        ]

        # Medium severity security should be force-approved after 2 retries
        result = should_force_approve(findings, retry_count=2)
        assert result.should_approve is True

    def test_performance_requires_3_retries(self):
        """Test that performance findings require 3+ retries to force-approve."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query detected",
            ),
        ]

        # retry_count < 3 should not force-approve
        for retry_count in [0, 1, 2]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is False
            assert "PERFORMANCE" in result.blocked_by

        # retry_count >= 3 should force-approve
        for retry_count in [3, 4, 5]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is True

    def test_architecture_requires_2_retries(self):
        """Test that architecture findings can be force-approved after 2 retries."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="medium",
                category="coupling",
                message="Tight coupling between modules",
            ),
        ]

        # retry_count < 2 should not force-approve
        for retry_count in [0, 1]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is False

        # retry_count >= 2 should force-approve
        for retry_count in [2, 3, 4]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is True

    def test_correctness_requires_2_retries(self):
        """Test that correctness findings can be force-approved after 2 retries."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.CORRECTNESS,
                severity="high",
                category="logic",
                message="Logic error in condition",
            ),
        ]

        # retry_count < 2 should not force-approve
        for retry_count in [0, 1]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is False

        # retry_count >= 2 should force-approve
        for retry_count in [2, 3, 4]:
            result = should_force_approve(findings, retry_count=retry_count)
            assert result.should_approve is True

    def test_mixed_specialists_security_blocks(self):
        """Test that security blockers override other specialists."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="Style issue",
            ),
        ]

        # Security blocker should prevent force-approve even with high retry count
        result = should_force_approve(findings, retry_count=10)
        assert result.should_approve is False
        assert "SECURITY" in result.blocked_by

    def test_mixed_specialists_performance_blocks_until_3(self):
        """Test that performance blocks until 3 retries even with architecture."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="memory",
                message="Memory leak",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="medium",
                category="coupling",
                message="Tight coupling",
            ),
        ]

        # At retry_count=2, architecture would be approved but performance blocks
        result = should_force_approve(findings, retry_count=2)
        assert result.should_approve is False
        assert "PERFORMANCE" in result.blocked_by

        # At retry_count=3, both can be force-approved
        result = should_force_approve(findings, retry_count=3)
        assert result.should_approve is True

    def test_filtered_findings_at_retry_0(self):
        """Test that all findings remain at retry_count=0."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="Style issue",
            ),
        ]

        result = should_force_approve(findings, retry_count=0)
        assert len(result.filtered_findings) == 2

    def test_filtered_findings_at_retry_2(self):
        """Test that architecture/correctness are filtered at retry_count=2."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="Style issue",
            ),
        ]

        result = should_force_approve(findings, retry_count=2)
        # Only performance should remain (architecture filtered at retry >= 2)
        assert len(result.filtered_findings) == 1
        assert result.filtered_findings[0].specialist == ReviewSpecialist.PERFORMANCE

    def test_filtered_findings_at_retry_3(self):
        """Test that performance is also filtered at retry_count=3."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="Style issue",
            ),
        ]

        result = should_force_approve(findings, retry_count=3)
        # Both should be filtered (force-approved)
        assert len(result.filtered_findings) == 0


class TestFilterFindingsByPriority:
    """Tests for filter_findings_by_priority convenience function."""

    def test_filter_empty_findings(self):
        """Test filtering empty findings list."""
        result = filter_findings_by_priority([], retry_count=0)
        assert result == []

    def test_filter_at_retry_0(self):
        """Test that all findings remain at retry_count=0."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="medium",
                category="coupling",
                message="Tight coupling",
            ),
        ]

        result = filter_findings_by_priority(findings, retry_count=0)
        assert len(result) == 1

    def test_filter_at_retry_2(self):
        """Test that architecture findings are filtered at retry_count=2."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="medium",
                category="coupling",
                message="Tight coupling",
            ),
        ]

        result = filter_findings_by_priority(findings, retry_count=2)
        assert len(result) == 0

    def test_filter_preserves_security_blockers(self):
        """Test that security blockers are never filtered."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection",
            ),
        ]

        # Security blockers should remain even at high retry count
        result = filter_findings_by_priority(findings, retry_count=10)
        assert len(result) == 1
