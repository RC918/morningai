"""
Tests for B-16 Self-Critique Specialist - Multi-Specialist Review Enhancement

Issue #4066: Self-Critique Specialist for Multi-Specialist Review (B-9 Enhancement)

This module tests the self-critique functionality that filters false positives
from the multi-specialist review pipeline.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from review_context.multi_specialist_reviewer import (
    ReviewSpecialist,
    SpecialistFinding,
    MultiSpecialistReviewer,
    SPECIALIST_PROMPTS,
)


class TestSelfCritiquePrompt:
    """Tests for Self-Critique specialist prompt."""

    def test_self_critique_prompt_exists(self):
        """Test that SELF_CRITIQUE prompt is defined."""
        assert ReviewSpecialist.SELF_CRITIQUE in SPECIALIST_PROMPTS

    def test_self_critique_prompt_content(self):
        """Test that SELF_CRITIQUE prompt has required elements."""
        prompt = SPECIALIST_PROMPTS[ReviewSpecialist.SELF_CRITIQUE]

        # Should mention false positives
        assert "false positive" in prompt.lower()

        # Should mention verification
        assert "verify" in prompt.lower()

        # Should mention output format
        assert "false_positive_indices" in prompt
        assert "verification_notes" in prompt

        # Should mention being conservative
        assert "conservative" in prompt.lower()


class TestSelfCritiqueFindings:
    """Tests for _self_critique_findings method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reviewer = MultiSpecialistReviewer(trace_id="test-trace")
        self.sample_findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection vulnerability",
                file_path="src/db.py",
                line_number=42,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query detected",
                file_path="src/api.py",
                line_number=100,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="coupling",
                message="Tight coupling between modules",
                file_path="src/service.py",
                line_number=25,
            ),
        ]
        self.sample_diff = """
diff --git a/src/db.py b/src/db.py
--- a/src/db.py
+++ b/src/db.py
@@ -40,6 +40,8 @@ def query_user(user_id):
     # Some code
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return execute(query)
"""

    def test_empty_findings_returns_empty(self):
        """Test that empty findings list returns empty with stats."""
        result, stats = self.reviewer._self_critique_findings(
            findings=[],
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert result == []
        assert stats["original_count"] == 0
        assert stats["removed_count"] == 0
        assert stats["verified_count"] == 0
        assert stats["removal_rate"] == 0.0

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_all_findings_valid(self, mock_get_client):
        """Test when self-critique validates all findings."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": [], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert len(result) == 3
        assert stats["original_count"] == 3
        assert stats["removed_count"] == 0
        assert stats["verified_count"] == 3
        assert stats["removal_rate"] == 0.0

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_some_findings_removed(self, mock_get_client):
        """Test when self-critique removes some findings."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": [1, 2], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert len(result) == 1
        assert result[0].specialist == ReviewSpecialist.SECURITY
        assert stats["original_count"] == 3
        assert stats["removed_count"] == 2
        assert stats["verified_count"] == 1
        assert stats["removal_rate"] == pytest.approx(2 / 3)

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_all_findings_removed(self, mock_get_client):
        """Test when self-critique removes all findings."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": [0, 1, 2], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert len(result) == 0
        assert stats["original_count"] == 3
        assert stats["removed_count"] == 3
        assert stats["verified_count"] == 0
        assert stats["removal_rate"] == 1.0

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_string_indices(self, mock_get_client):
        """Test that string indices are converted to integers."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # LLM might return string indices instead of integers
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": ["0", "2"], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert len(result) == 1
        assert result[0].specialist == ReviewSpecialist.PERFORMANCE
        assert stats["removed_count"] == 2

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_invalid_indices(self, mock_get_client):
        """Test that invalid indices are ignored."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": [0, 99, -1, "invalid"], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        # Only index 0 should be removed (99, -1, "invalid" are invalid)
        assert len(result) == 2
        assert stats["removed_count"] == 1

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_malformed_json(self, mock_get_client):
        """Test that malformed JSON response keeps all findings."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        # All findings should be kept when JSON parsing fails
        assert len(result) == 3
        assert stats["removed_count"] == 0

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_non_dict_response(self, mock_get_client):
        """Test that non-dict JSON response keeps all findings."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # LLM might return an array or null instead of dict
        mock_response.content = json.dumps([0, 1, 2])
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        # All findings should be kept when response is not a dict
        assert len(result) == 3
        assert stats["removed_count"] == 0

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_llm_exception(self, mock_get_client):
        """Test that LLM exception keeps all findings."""
        mock_get_client.side_effect = Exception("LLM service unavailable")

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        # All findings should be kept when LLM fails
        assert len(result) == 3
        assert stats["removed_count"] == 0
        assert "error" in stats

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_diff_truncation_for_large_findings(self, mock_get_client):
        """Test that diff is truncated when findings are large."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": [], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Create a very large diff
        large_diff = "x" * 50000

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=large_diff,
            pr_context={},
        )

        # Should still work without error
        assert len(result) == 3

        # Verify generate was called (diff should be truncated internally)
        mock_client.generate.assert_called_once()


class TestExtractJsonObject:
    """Tests for _extract_json_object helper method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reviewer = MultiSpecialistReviewer(trace_id="test-trace")

    def test_extract_simple_json(self):
        """Test extraction of simple JSON object."""
        text = '{"key": "value"}'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"key": "value"}'

    def test_extract_nested_json(self):
        """Test extraction of nested JSON object."""
        text = '{"outer": {"inner": "value"}}'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"outer": {"inner": "value"}}'

    def test_extract_deeply_nested_json(self):
        """Test extraction of deeply nested JSON with arrays."""
        text = '{"a": {"b": [{"c": 1}, {"d": 2}]}}'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"a": {"b": [{"c": 1}, {"d": 2}]}}'

    def test_extract_json_with_prefix(self):
        """Test extraction when JSON has text prefix."""
        text = 'Here is the result: {"key": "value"}'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"key": "value"}'

    def test_extract_json_with_suffix(self):
        """Test extraction when JSON has text suffix."""
        text = '{"key": "value"} and some more text'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"key": "value"}'

    def test_extract_json_with_braces_in_string(self):
        """Test extraction handles braces inside strings correctly."""
        text = '{"message": "Use {curly} braces"}'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"message": "Use {curly} braces"}'

    def test_extract_json_with_escaped_quotes(self):
        """Test extraction handles escaped quotes in strings."""
        text = '{"message": "He said \\"hello\\""}'
        result = self.reviewer._extract_json_object(text)
        assert result == '{"message": "He said \\"hello\\""}'

    def test_no_json_returns_original(self):
        """Test that text without JSON returns original."""
        text = 'No JSON here'
        result = self.reviewer._extract_json_object(text)
        assert result == 'No JSON here'

    def test_realistic_self_critique_response(self):
        """Test extraction of realistic self-critique response with nested verification_notes."""
        text = '''Here is my analysis:
{
  "false_positive_indices": [0, 2],
  "verification_notes": [
    {"index": 0, "reason": "Line 42 doesn't exist in the diff"},
    {"index": 2, "reason": "This is a style preference, not a real issue"}
  ]
}
That's my assessment.'''
        result = self.reviewer._extract_json_object(text)
        parsed = json.loads(result)
        assert parsed["false_positive_indices"] == [0, 2]
        assert len(parsed["verification_notes"]) == 2


class TestNestedJsonParsing:
    """Tests for nested JSON parsing in _self_critique_findings."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reviewer = MultiSpecialistReviewer(trace_id="test-trace")
        self.sample_findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="injection",
                message="SQL injection vulnerability",
                file_path="src/db.py",
                line_number=42,
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="n+1",
                message="N+1 query detected",
                file_path="src/api.py",
                line_number=100,
            ),
        ]
        self.sample_diff = "diff --git a/test.py b/test.py"

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_nested_verification_notes(self, mock_get_client):
        """Test that nested JSON with verification_notes is parsed correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "false_positive_indices": [1],
            "verification_notes": [
                {"index": 1, "reason": "N+1 is not actually present in this code"}
            ]
        })
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert len(result) == 1
        assert result[0].specialist == ReviewSpecialist.SECURITY
        assert stats["removed_count"] == 1
        assert len(stats["verification_notes"]) == 1
        assert stats["verification_notes"][0]["reason"] == "N+1 is not actually present in this code"

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_handles_json_with_text_wrapper(self, mock_get_client):
        """Test that JSON wrapped in text is extracted and parsed correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '''Based on my analysis, here is the result:
{"false_positive_indices": [0], "verification_notes": [{"index": 0, "reason": "False positive"}]}
That concludes my review.'''
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result, stats = self.reviewer._self_critique_findings(
            findings=self.sample_findings,
            diff_content=self.sample_diff,
            pr_context={},
        )

        assert len(result) == 1
        assert result[0].specialist == ReviewSpecialist.PERFORMANCE
        assert stats["removed_count"] == 1


class TestMultiSpecialistReviewerWithSelfCritique:
    """Integration tests for MultiSpecialistReviewer with self-critique enabled."""

    @patch("common.config.settings.settings")
    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_review_with_self_critique_disabled(self, mock_get_client, mock_settings):
        """Test that self-critique is skipped when disabled."""
        mock_settings.enable_self_critique = False
        mock_settings.enable_confidence_filtering = False  # B-18: Disable for this test

        mock_client = MagicMock()
        mock_response = MagicMock()
        # Return JSON array for specialist response
        mock_response.content = '[{"severity": "high", "category": "test", "message": "Test finding"}]'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        reviewer = MultiSpecialistReviewer(trace_id="test")

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            findings = loop.run_until_complete(
                reviewer.review(
                    diff_content="test diff",
                    pr_context={},
                )
            )

            # Self-critique should not be in specialists_used
            assert "self_critique" not in findings.specialists_used
        finally:
            loop.close()

    @patch("common.config.settings.settings")
    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_review_with_self_critique_enabled(self, mock_get_client, mock_settings):
        """Test that self-critique runs when enabled."""
        mock_settings.enable_self_critique = True
        mock_settings.enable_confidence_filtering = False  # B-18: Disable for this test

        mock_client = MagicMock()

        # First 3 calls are for specialists, 4th is for self-critique
        specialist_response = MagicMock()
        specialist_response.content = '[{"severity": "high", "category": "test", "message": "Test finding", "file_path": "test.py", "line_number": 1}]'

        self_critique_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        self_critique_response.content = '{"false_positive_indices": [], "verification_notes": []}'

        mock_client.generate.side_effect = [
            specialist_response,  # Security
            specialist_response,  # Performance
            specialist_response,  # Architecture
            self_critique_response,  # Self-critique
        ]
        mock_get_client.return_value = mock_client

        reviewer = MultiSpecialistReviewer(trace_id="test")

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            findings = loop.run_until_complete(
                reviewer.review(
                    diff_content="test diff",
                    pr_context={},
                )
            )

            # Self-critique should be in specialists_used
            assert "self_critique" in findings.specialists_used
            # Should have self_critique summary
            assert "self_critique" in findings.specialist_summaries
        finally:
            loop.close()


class TestSelfCritiqueStats:
    """Tests for self-critique telemetry stats."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reviewer = MultiSpecialistReviewer(trace_id="test-trace")

    @patch("review_context.multi_specialist_reviewer.get_client_for_task")
    def test_stats_include_removed_indices(self, mock_get_client):
        """Test that stats include removed indices for debugging."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Use simple JSON without nested objects (regex is non-greedy)
        mock_response.content = '{"false_positive_indices": [0, 2], "verification_notes": []}'
        mock_client.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        findings = [
            SpecialistFinding(
                specialist=ReviewSpecialist.SECURITY,
                severity="high",
                category="test",
                message="Finding 0",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.PERFORMANCE,
                severity="medium",
                category="test",
                message="Finding 1",
            ),
            SpecialistFinding(
                specialist=ReviewSpecialist.ARCHITECTURE,
                severity="low",
                category="test",
                message="Finding 2",
            ),
        ]

        _, stats = self.reviewer._self_critique_findings(
            findings=findings,
            diff_content="test diff",
            pr_context={},
        )

        assert "removed_indices" in stats
        assert set(stats["removed_indices"]) == {0, 2}
        assert "verification_notes" in stats
