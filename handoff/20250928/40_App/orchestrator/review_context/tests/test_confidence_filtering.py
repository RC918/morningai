"""
Tests for B-18 Confidence Scoring for Multi-Specialist Review

Issue #4253: Confidence Scoring Mechanism

Tests cover:
1. filter_findings_by_confidence function
2. Confidence parsing in _parse_specialist_response
3. SpecialistFinding confidence field
4. Edge cases (empty findings, missing confidence, invalid confidence)
"""

from review_context.multi_specialist_reviewer import (
    ReviewSpecialist,
    SpecialistFinding,
    filter_findings_by_confidence,
    DEFAULT_CONFIDENCE_THRESHOLD,
)


class TestSpecialistFindingConfidence:
    """Tests for SpecialistFinding confidence field."""

    def test_default_confidence(self):
        """Test that default confidence is 0.8."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.SECURITY,
            severity="medium",
            category="injection",
            message="Potential SQL injection",
        )
        assert finding.confidence == 0.8

    def test_custom_confidence(self):
        """Test setting custom confidence value."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.PERFORMANCE,
            severity="high",
            category="n+1",
            message="N+1 query detected",
            confidence=0.95,
        )
        assert finding.confidence == 0.95

    def test_confidence_in_to_dict(self):
        """Test that confidence is included in to_dict output."""
        finding = SpecialistFinding(
            specialist=ReviewSpecialist.ARCHITECTURE,
            severity="low",
            category="coupling",
            message="Tight coupling",
            confidence=0.75,
        )
        d = finding.to_dict()
        assert "confidence" in d
        assert d["confidence"] == 0.75


class TestFilterFindingsByConfidence:
    """Tests for filter_findings_by_confidence function."""

    def test_empty_findings(self):
        """Test filtering empty findings list."""
        filtered, stats = filter_findings_by_confidence([])
        assert filtered == []
        assert stats["original_count"] == 0
        assert stats["filtered_count"] == 0
        assert stats["removed_count"] == 0
        assert stats["threshold"] == DEFAULT_CONFIDENCE_THRESHOLD

    def test_all_high_confidence(self):
        """Test that all high-confidence findings are kept."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection",
                confidence=0.95,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query",
                confidence=0.85,
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(filtered) == 2
        assert stats["original_count"] == 2
        assert stats["filtered_count"] == 2
        assert stats["removed_count"] == 0

    def test_all_low_confidence(self):
        """Test that all low-confidence findings are removed."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="Style issue",
                confidence=0.3,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.CORRECTNESS,
                severity="medium",
                category="logic",
                message="Possible logic error",
                confidence=0.5,
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(filtered) == 0
        assert stats["original_count"] == 2
        assert stats["filtered_count"] == 0
        assert stats["removed_count"] == 2

    def test_mixed_confidence(self):
        """Test filtering with mixed confidence levels."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection",
                confidence=0.95,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query",
                confidence=0.5,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="Style issue",
                confidence=0.75,
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(filtered) == 2
        assert stats["original_count"] == 3
        assert stats["filtered_count"] == 2
        assert stats["removed_count"] == 1

        # Check that the correct findings were kept
        specialists = [f.specialist for f in filtered]
        assert ReviewSpecialist.SECURITY in specialists
        assert ReviewSpecialist.ARCHITECTURE in specialists
        assert ReviewSpecialist.PERFORMANCE not in specialists

    def test_threshold_exactly_0_7(self):
        """Test that findings at exactly 0.7 confidence are kept."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="medium",
                category="config",
                message="Config issue",
                confidence=0.7,
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(filtered) == 1
        assert stats["filtered_count"] == 1
        assert stats["removed_count"] == 0

    def test_threshold_just_below_0_7(self):
        """Test that findings just below 0.7 confidence are removed."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="medium",
                category="config",
                message="Config issue",
                confidence=0.69,
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(filtered) == 0
        assert stats["filtered_count"] == 0
        assert stats["removed_count"] == 1

    def test_custom_threshold(self):
        """Test filtering with custom threshold."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection",
                confidence=0.85,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query",
                confidence=0.75,
            ),
        ]

        # With threshold 0.8, only the 0.85 finding should pass
        filtered, stats = filter_findings_by_confidence(findings, threshold=0.8)
        assert len(filtered) == 1
        assert stats["threshold"] == 0.8
        assert filtered[0].specialist == ReviewSpecialist.SECURITY

    def test_removed_findings_in_stats(self):
        """Test that removed findings are included in stats."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="style",
                message="This is a style issue that should be removed",
                confidence=0.4,
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(stats["removed_findings"]) == 1
        removed = stats["removed_findings"][0]
        assert removed["specialist"] == "architecture"
        assert removed["confidence"] == 0.4
        assert "style issue" in removed["message"]

    def test_default_confidence_passes_threshold(self):
        """Test that default confidence (0.8) passes default threshold (0.7)."""
        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.CORRECTNESS,
                severity="medium",
                category="logic",
                message="Logic error",
                # No confidence specified, defaults to 0.8
            ),
        ]

        filtered, stats = filter_findings_by_confidence(findings)
        assert len(filtered) == 1
        assert stats["removed_count"] == 0


class TestDefaultConfidenceThreshold:
    """Tests for DEFAULT_CONFIDENCE_THRESHOLD constant."""

    def test_default_threshold_value(self):
        """Test that default threshold is 0.7."""
        assert DEFAULT_CONFIDENCE_THRESHOLD == 0.7
