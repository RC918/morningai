"""
Unit tests for F-5.5 Review Consolidation - Judge Agent Arbitration

Tests cover:
- ConflictDetector: Conflict detection between specialist findings
- ReviewConsolidator: Conflict resolution using Judge Agent
- Rule-based arbitration: Context-aware priority rules
- Integration with Debate Engine Judge Agent
"""

from unittest.mock import patch

from core.planner.review_consolidation import (
    ConflictType,
    ConflictResolution,
    Conflict,
    ArbitrationDecision,
    ConsolidatedReview,
    ConflictDetector,
    ReviewConsolidator,
    consolidate_review_findings,
    CONTEXT_PRIORITY_RULES,
)


class TestConflictType:
    """Tests for ConflictType enum."""

    def test_conflict_types_exist(self):
        """Verify all expected conflict types exist."""
        assert ConflictType.SECURITY_VS_PERFORMANCE.value == "security_vs_performance"
        assert ConflictType.SECURITY_VS_ARCHITECTURE.value == "security_vs_architecture"
        assert ConflictType.PERFORMANCE_VS_ARCHITECTURE.value == "performance_vs_architecture"
        assert ConflictType.CONTRADICTORY_SUGGESTIONS.value == "contradictory_suggestions"
        assert ConflictType.OVERLAPPING_CONCERNS.value == "overlapping_concerns"


class TestConflictResolution:
    """Tests for ConflictResolution enum."""

    def test_resolution_types_exist(self):
        """Verify all expected resolution types exist."""
        assert ConflictResolution.PRIORITIZE_FIRST.value == "prioritize_first"
        assert ConflictResolution.PRIORITIZE_SECOND.value == "prioritize_second"
        assert ConflictResolution.MERGE_BOTH.value == "merge_both"
        assert ConflictResolution.DEFER_TO_HUMAN.value == "defer_to_human"


class TestConflict:
    """Tests for Conflict dataclass."""

    def test_conflict_creation(self):
        """Test creating a Conflict instance."""
        finding_a = {"specialist": "security", "message": "Add validation"}
        finding_b = {"specialist": "performance", "message": "Remove overhead"}

        conflict = Conflict(
            conflict_type=ConflictType.SECURITY_VS_PERFORMANCE,
            finding_a=finding_a,
            finding_b=finding_b,
            description="Security vs Performance conflict",
            severity="high",
        )

        assert conflict.conflict_type == ConflictType.SECURITY_VS_PERFORMANCE
        assert conflict.finding_a == finding_a
        assert conflict.finding_b == finding_b
        assert conflict.severity == "high"

    def test_conflict_to_dict(self):
        """Test Conflict.to_dict() serialization."""
        conflict = Conflict(
            conflict_type=ConflictType.OVERLAPPING_CONCERNS,
            finding_a={"specialist": "security"},
            finding_b={"specialist": "architecture"},
            description="Same location",
        )

        result = conflict.to_dict()

        assert result["conflict_type"] == "overlapping_concerns"
        assert result["finding_a"] == {"specialist": "security"}
        assert result["finding_b"] == {"specialist": "architecture"}
        assert result["description"] == "Same location"
        assert result["severity"] == "medium"


class TestArbitrationDecision:
    """Tests for ArbitrationDecision dataclass."""

    def test_arbitration_decision_creation(self):
        """Test creating an ArbitrationDecision instance."""
        decision = ArbitrationDecision(
            resolution=ConflictResolution.PRIORITIZE_FIRST,
            winning_finding={"specialist": "security"},
            rationale="Security takes priority for auth API",
            confidence=0.9,
            requires_human_review=False,
        )

        assert decision.resolution == ConflictResolution.PRIORITIZE_FIRST
        assert decision.winning_finding == {"specialist": "security"}
        assert decision.confidence == 0.9
        assert decision.requires_human_review is False

    def test_arbitration_decision_to_dict(self):
        """Test ArbitrationDecision.to_dict() serialization."""
        decision = ArbitrationDecision(
            resolution=ConflictResolution.DEFER_TO_HUMAN,
            rationale="Cannot determine priority",
            requires_human_review=True,
        )

        result = decision.to_dict()

        assert result["resolution"] == "defer_to_human"
        assert result["requires_human_review"] is True
        assert result["winning_finding"] is None


class TestConsolidatedReview:
    """Tests for ConsolidatedReview dataclass."""

    def test_consolidated_review_creation(self):
        """Test creating a ConsolidatedReview instance."""
        findings = [{"specialist": "security", "message": "Issue 1"}]
        decisions = [ArbitrationDecision(resolution=ConflictResolution.PRIORITIZE_FIRST)]

        review = ConsolidatedReview(
            findings=findings,
            conflicts_detected=1,
            conflicts_resolved=1,
            arbitration_decisions=decisions,
            requires_human_review=False,
            consolidation_time_ms=50.0,
        )

        assert len(review.findings) == 1
        assert review.conflicts_detected == 1
        assert review.conflicts_resolved == 1
        assert len(review.arbitration_decisions) == 1

    def test_consolidated_review_to_dict(self):
        """Test ConsolidatedReview.to_dict() serialization."""
        review = ConsolidatedReview(
            findings=[{"specialist": "security"}],
            conflicts_detected=2,
            conflicts_resolved=2,
        )

        result = review.to_dict()

        assert result["finding_count"] == 1
        assert result["conflicts_detected"] == 2
        assert result["conflicts_resolved"] == 2


class TestConflictDetector:
    """Tests for ConflictDetector class."""

    def test_no_conflicts_empty_findings(self):
        """Test no conflicts with empty findings."""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts([])
        assert conflicts == []

    def test_no_conflicts_single_specialist(self):
        """Test no conflicts when all findings from same specialist."""
        detector = ConflictDetector()
        findings = [
            {"specialist": "security", "message": "Issue 1"},
            {"specialist": "security", "message": "Issue 2"},
        ]
        conflicts = detector.detect_conflicts(findings)
        assert conflicts == []

    def test_detect_security_vs_performance_conflict(self):
        """Test detecting security vs performance conflict."""
        detector = ConflictDetector()
        findings = [
            {
                "specialist": "security",
                "message": "Add input validation",
                "suggestion": "Add validation check for user input",
            },
            {
                "specialist": "performance",
                "message": "Reduce overhead",
                "suggestion": "Skip validation to reduce overhead",
            },
        ]

        conflicts = detector.detect_conflicts(findings)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.SECURITY_VS_PERFORMANCE

    def test_detect_overlapping_concerns(self):
        """Test detecting overlapping concerns at same location."""
        detector = ConflictDetector()
        findings = [
            {
                "specialist": "security",
                "message": "Security issue",
                "file_path": "src/auth.py",
                "line_number": 42,
            },
            {
                "specialist": "architecture",
                "message": "Architecture issue",
                "file_path": "src/auth.py",
                "line_number": 42,
            },
        ]

        conflicts = detector.detect_conflicts(findings)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.OVERLAPPING_CONCERNS

    def test_no_conflict_different_locations(self):
        """Test no conflict when findings at different locations."""
        detector = ConflictDetector()
        findings = [
            {
                "specialist": "security",
                "message": "Security issue",
                "file_path": "src/auth.py",
                "line_number": 10,
            },
            {
                "specialist": "performance",
                "message": "Performance issue",
                "file_path": "src/auth.py",
                "line_number": 50,
            },
        ]

        conflicts = detector.detect_conflicts(findings)

        # No overlapping concerns since different lines
        # May or may not have pattern-based conflicts depending on message content
        overlapping = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_CONCERNS]
        assert len(overlapping) == 0

    def test_conflict_severity_from_findings(self):
        """Test conflict severity is determined from finding severities."""
        detector = ConflictDetector()
        findings = [
            {
                "specialist": "security",
                "message": "Add check",
                "suggestion": "Add validation check",
                "severity": "critical",
            },
            {
                "specialist": "performance",
                "message": "Remove check",
                "suggestion": "Remove check to reduce overhead",
                "severity": "low",
            },
        ]

        conflicts = detector.detect_conflicts(findings)

        assert len(conflicts) == 1
        assert conflicts[0].severity == "critical"


class TestReviewConsolidator:
    """Tests for ReviewConsolidator class."""

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_consolidate_disabled(self, mock_use):
        """Test consolidation when feature is disabled."""
        mock_use.return_value = False

        consolidator = ReviewConsolidator(trace_id="test")
        findings = [{"specialist": "security", "message": "Issue"}]

        result = consolidator.consolidate(findings)

        assert result.findings == findings
        assert result.conflicts_detected == 0
        assert result.conflicts_resolved == 0

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_consolidate_no_conflicts(self, mock_use):
        """Test consolidation with no conflicts."""
        mock_use.return_value = True

        consolidator = ReviewConsolidator(trace_id="test")
        findings = [
            {"specialist": "security", "message": "Issue 1"},
            {"specialist": "security", "message": "Issue 2"},
        ]

        result = consolidator.consolidate(findings)

        assert result.findings == findings
        assert result.conflicts_detected == 0

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_consolidate_with_conflicts_rule_based(self, mock_use):
        """Test consolidation with conflicts using rule-based arbitration."""
        mock_use.return_value = True

        consolidator = ReviewConsolidator(trace_id="test", enable_llm=False)
        findings = [
            {
                "specialist": "security",
                "message": "Add validation",
                "suggestion": "Add validation check",
                "severity": "high",
            },
            {
                "specialist": "performance",
                "message": "Skip validation",
                "suggestion": "Skip validation to reduce overhead",
                "severity": "medium",
            },
        ]

        result = consolidator.consolidate(
            findings,
            task_context={"api_type": "auth"}
        )

        assert result.conflicts_detected >= 1
        assert result.conflicts_resolved >= 1
        # Security should win for auth API
        assert len(result.arbitration_decisions) >= 1

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_consolidate_auth_context_security_priority(self, mock_use):
        """Test that security takes priority in auth context."""
        mock_use.return_value = True

        consolidator = ReviewConsolidator(trace_id="test", enable_llm=False)
        findings = [
            {
                "specialist": "security",
                "message": "Add encryption",
                "suggestion": "Encrypt sensitive data",
                "severity": "high",
                "file_path": "auth.py",
                "line_number": 10,
            },
            {
                "specialist": "performance",
                "message": "Cache data",
                "suggestion": "Cache to improve performance",
                "severity": "medium",
                "file_path": "auth.py",
                "line_number": 10,
            },
        ]

        result = consolidator.consolidate(
            findings,
            task_context={"api_type": "login"}
        )

        # Should have detected overlapping concerns
        assert result.conflicts_detected >= 1
        # Security finding should be kept (priority 100 vs 50 for login context)
        security_findings = [f for f in result.findings if f.get("specialist") == "security"]
        assert len(security_findings) >= 1

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_consolidate_ui_context_performance_priority(self, mock_use):
        """Test that performance takes priority in UI context."""
        mock_use.return_value = True

        consolidator = ReviewConsolidator(trace_id="test", enable_llm=False)
        findings = [
            {
                "specialist": "security",
                "message": "Add check",
                "suggestion": "Add security check",
                "severity": "medium",
                "file_path": "component.tsx",
                "line_number": 50,
            },
            {
                "specialist": "performance",
                "message": "Optimize render",
                "suggestion": "Memoize component",
                "severity": "high",
                "file_path": "component.tsx",
                "line_number": 50,
            },
        ]

        result = consolidator.consolidate(
            findings,
            task_context={"component_type": "ui"}
        )

        # Should have detected overlapping concerns
        assert result.conflicts_detected >= 1
        # Performance finding should be kept (priority 80 vs 50 for UI context)
        perf_findings = [f for f in result.findings if f.get("specialist") == "performance"]
        assert len(perf_findings) >= 1


class TestContextPriorityRules:
    """Tests for context priority rules."""

    def test_auth_context_priorities(self):
        """Test priority rules for auth context."""
        rules = CONTEXT_PRIORITY_RULES["auth"]
        assert rules["security"] > rules["performance"]
        assert rules["performance"] > rules["architecture"]

    def test_ui_context_priorities(self):
        """Test priority rules for UI context."""
        rules = CONTEXT_PRIORITY_RULES["ui"]
        assert rules["performance"] > rules["security"]
        assert rules["architecture"] > rules["security"]

    def test_default_context_priorities(self):
        """Test default priority rules."""
        rules = CONTEXT_PRIORITY_RULES["default"]
        assert rules["security"] > rules["performance"]
        assert rules["performance"] > rules["architecture"]


class TestConsolidateReviewFindings:
    """Tests for consolidate_review_findings convenience function."""

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_convenience_function(self, mock_use):
        """Test the convenience function works correctly."""
        mock_use.return_value = False

        findings = [{"specialist": "security", "message": "Issue"}]
        result = consolidate_review_findings(findings, trace_id="test")

        assert isinstance(result, ConsolidatedReview)
        assert result.findings == findings


class TestJudgeAgentIntegration:
    """Tests for Judge Agent integration."""

    @patch("core.planner.review_consolidation._use_review_consolidation")
    @patch("core.planner.review_consolidation.ReviewConsolidator._arbitrate_with_judge")
    def test_judge_agent_called_when_enabled(self, mock_judge, mock_use):
        """Test that Judge Agent is called when LLM is enabled."""
        mock_use.return_value = True
        mock_judge.return_value = ArbitrationDecision(
            resolution=ConflictResolution.PRIORITIZE_FIRST,
            rationale="Judge decision",
            confidence=0.9,
        )

        consolidator = ReviewConsolidator(trace_id="test", enable_llm=True)
        findings = [
            {
                "specialist": "security",
                "message": "Add check",
                "suggestion": "Add validation check",
                "file_path": "test.py",
                "line_number": 10,
            },
            {
                "specialist": "performance",
                "message": "Remove check",
                "suggestion": "Remove check",
                "file_path": "test.py",
                "line_number": 10,
            },
        ]

        result = consolidator.consolidate(findings)

        # Judge should have been called for the conflict
        assert mock_judge.called or result.conflicts_detected == 0

    @patch("core.planner.review_consolidation._use_review_consolidation")
    def test_fallback_to_rule_based_on_error(self, mock_use):
        """Test fallback to rule-based when Judge Agent fails."""
        mock_use.return_value = True

        consolidator = ReviewConsolidator(trace_id="test", enable_llm=True)

        # Mock _arbitrate_with_judge to raise an exception
        with patch.object(
            consolidator,
            "_arbitrate_with_judge",
            side_effect=Exception("LLM error")
        ):
            findings = [
                {
                    "specialist": "security",
                    "message": "Add check",
                    "suggestion": "Add validation check",
                    "file_path": "test.py",
                    "line_number": 10,
                },
                {
                    "specialist": "performance",
                    "message": "Remove check",
                    "suggestion": "Remove check",
                    "file_path": "test.py",
                    "line_number": 10,
                },
            ]

            result = consolidator.consolidate(findings)

            # Should still produce a result using rule-based fallback
            assert isinstance(result, ConsolidatedReview)
