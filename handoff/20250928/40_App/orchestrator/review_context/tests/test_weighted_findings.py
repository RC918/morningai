"""
Tests for WeightedFinding and get_weighted_findings - EPIC I-X RuntimeTrustScore Integration

Issue #3925: RuntimeTrustScore Integration - Reviewer Weight Adjustment
"""

import pytest

from review_context.multi_specialist_reviewer import (
    ReviewSpecialist,
    SpecialistFinding,
    WeightedFinding,
    get_weighted_findings,
    SEVERITY_PRIORITY,
)
from governance.specialist_trust_score import (
    SpecialistType,
    FeedbackType,
    SpecialistTrustScoreTracker,
    get_specialist_trust_tracker,
    reset_specialist_trust_tracker,
)

# Get default trust score from the authoritative source
DEFAULT_TRUST_SCORE = SpecialistTrustScoreTracker.DEFAULT_TRUST_SCORE


class TestWeightedFinding:
    """Tests for WeightedFinding dataclass."""

    def test_create_weighted_finding(self):
        """Test creating a weighted finding."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.SECURITY,
            severity="high",
            category="injection",
            message="SQL injection vulnerability",
        )
        weighted = WeightedFinding(
            finding=finding,
            weight=0.8,
            effective_priority=2.4,  # 3.0 * 0.8
        )

        assert weighted.finding == finding
        assert weighted.weight == 0.8
        assert weighted.effective_priority == 2.4

    def test_weighted_finding_to_dict(self):
        """Test converting weighted finding to dictionary."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.PERFORMANCE,
            severity="medium",
            category="n+1",
            message="N+1 query detected",
        )
        weighted = WeightedFinding(
            finding=finding,
            weight=0.7,
            effective_priority=1.4,
        )

        result = weighted.to_dict()
        assert "finding" in result
        assert result["weight"] == 0.7
        assert result["effective_priority"] == 1.4
        assert result["finding"]["specialist"] == "performance"


class TestSeverityPriority:
    """Tests for severity priority mapping."""

    def test_severity_priority_values(self):
        """Test that severity priorities are correctly defined."""
        assert SEVERITY_PRIORITY["critical"] == 4.0
        assert SEVERITY_PRIORITY["high"] == 3.0
        assert SEVERITY_PRIORITY["medium"] == 2.0
        assert SEVERITY_PRIORITY["low"] == 1.0

    def test_default_trust_score(self):
        """Test default trust score is 0.7."""
        assert DEFAULT_TRUST_SCORE == 0.7


class TestGetWeightedFindings:
    """Tests for get_weighted_findings function."""

    def setup_method(self):
        """Reset global tracker before each test."""
        reset_specialist_trust_tracker()

    def test_empty_findings(self):
        """Test with empty findings list."""
        result = get_weighted_findings([])
        assert result == []

    def test_single_finding_default_score(self):
        """Test single finding with default trust score."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.SECURITY,
            severity="high",
            category="injection",
            message="SQL injection",
        )

        result = get_weighted_findings([finding])

        assert len(result) == 1
        assert result[0].finding == finding
        assert result[0].weight == 0.7  # Default
        # high = 3.0, weight = 0.7, effective = 2.1
        assert result[0].effective_priority == pytest.approx(2.1)

    def test_multiple_findings_sorted_by_priority(self):
        """Test multiple findings are sorted by effective priority."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="low",  # priority 1.0
                category="info",
                message="Low severity issue",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="critical",  # priority 4.0
                category="memory",
                message="Critical memory leak",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="medium",  # priority 2.0
                category="coupling",
                message="Tight coupling",
            ),
        ]

        result = get_weighted_findings(findings)

        assert len(result) == 3
        # Should be sorted by effective_priority (highest first)
        assert result[0].finding.severity == "critical"
        assert result[1].finding.severity == "medium"
        assert result[2].finding.severity == "low"

    def test_custom_trust_scores(self):
        """Test with custom trust scores."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",  # priority 3.0
                category="injection",
                message="SQL injection",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="high",  # priority 3.0
                category="memory",
                message="Memory leak",
            ),
        ]

        # Security has higher trust, performance has lower
        trust_scores = {
            "security": 0.9,
            "performance": 0.5,
        }

        result = get_weighted_findings(findings, trust_scores)

        assert len(result) == 2
        # Security should be first due to higher trust score
        assert result[0].finding.specialist == ReviewSpecialist.SECURITY
        assert result[0].weight == 0.9
        assert result[0].effective_priority == pytest.approx(2.7)  # 3.0 * 0.9

        assert result[1].finding.specialist == ReviewSpecialist.PERFORMANCE
        assert result[1].weight == 0.5
        assert result[1].effective_priority == pytest.approx(1.5)  # 3.0 * 0.5

    def test_trust_score_affects_ordering(self):
        """Test that trust score can change finding order."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="medium",  # priority 2.0
                category="info",
                message="Medium security issue",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="high",  # priority 3.0
                category="memory",
                message="High performance issue",
            ),
        ]

        # Give security very high trust, performance very low
        trust_scores = {
            "security": 1.0,  # 2.0 * 1.0 = 2.0
            "performance": 0.5,  # 3.0 * 0.5 = 1.5
        }

        result = get_weighted_findings(findings, trust_scores)

        # Security should be first despite lower base severity
        assert result[0].finding.specialist == ReviewSpecialist.SECURITY
        assert result[1].finding.specialist == ReviewSpecialist.PERFORMANCE

    def test_uses_global_tracker_when_no_scores_provided(self):
        """Test that global tracker is used when no scores provided."""
        # Record some feedback to change trust scores
        tracker = get_specialist_trust_tracker()
        for _ in range(5):
            tracker.record_feedback(
                specialist=SpecialistType.SECURITY,
                feedback_type=FeedbackType.ACCEPTED,
            )

        finding = SpecialistFinding(
            specialist=ReviewSpecialist.SECURITY,
            severity="high",
            category="injection",
            message="SQL injection",
        )

        result = get_weighted_findings([finding])

        # Trust score should be higher than default 0.7
        assert result[0].weight > 0.7

    def test_unknown_severity_uses_default(self):
        """Test that unknown severity uses default priority of 2.0."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.SECURITY,
            severity="unknown",  # Not in SEVERITY_PRIORITY
            category="misc",
            message="Unknown severity issue",
        )

        result = get_weighted_findings([finding], {"security": 1.0})

        # Should use default priority of 2.0
        assert result[0].effective_priority == 2.0

    def test_missing_specialist_uses_default_score(self):
        """Test that missing specialist uses default trust score."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.ARCHITECTURE,
            severity="high",
            category="coupling",
            message="Tight coupling",
        )

        # Only provide security score, not architecture
        trust_scores = {"security": 0.9}

        result = get_weighted_findings([finding], trust_scores)

        # Should use default trust score of 0.7
        assert result[0].weight == 0.7
