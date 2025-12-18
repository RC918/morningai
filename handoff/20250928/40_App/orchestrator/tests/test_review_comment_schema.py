#!/usr/bin/env python3
"""
Unit tests for Review Comment Schema - EPIC B Phase B-2

Tests cover:
1. Parsing old format (line) and new format (start_line/end_line)
2. Severity normalization from LLM and CI sources
3. Category normalization and aliases
4. Line range validation edge cases
5. Inline comment detection
6. GitHub payload generation
7. Comment merging from multiple sources

Issue #2595: EPIC B - Diff-Aware Review Plumbing
Phase B-2: Review Comment Schema Definition
"""
from review_comment_schema import (
    parse_review_comment,
    normalize_review_comments,
    validate_line_range,
    is_inline_comment,
    to_github_inline_payload,
    merge_review_comments,
    _normalize_severity,
    _normalize_category,
    _parse_line_number,
    ReviewComment,
    MAX_LINE_RANGE,
)


class TestParseLineNumber:
    """Tests for _parse_line_number helper"""

    def test_valid_integer(self):
        assert _parse_line_number(42) == 42
        assert _parse_line_number(1) == 1
        assert _parse_line_number(1000) == 1000

    def test_valid_string_integer(self):
        assert _parse_line_number("42") == 42
        assert _parse_line_number("1") == 1

    def test_zero_returns_none(self):
        assert _parse_line_number(0) is None

    def test_negative_returns_none(self):
        assert _parse_line_number(-1) is None
        assert _parse_line_number(-100) is None

    def test_none_returns_none(self):
        assert _parse_line_number(None) is None

    def test_invalid_string_returns_none(self):
        assert _parse_line_number("abc") is None
        assert _parse_line_number("") is None
        assert _parse_line_number("12.5") is None

    def test_float_truncates(self):
        assert _parse_line_number(42.9) == 42


class TestNormalizeSeverity:
    """Tests for severity normalization"""

    def test_llm_severity_mapping(self):
        assert _normalize_severity("nit", "llm") == "info"
        assert _normalize_severity("suggestion", "llm") == "suggestion"
        assert _normalize_severity("warning", "llm") == "warning"
        assert _normalize_severity("error", "llm") == "error"

    def test_ci_severity_mapping(self):
        assert _normalize_severity("none", "ci") == "info"
        assert _normalize_severity("low", "ci") == "info"
        assert _normalize_severity("medium", "ci") == "warning"
        assert _normalize_severity("high", "ci") == "error"
        assert _normalize_severity("critical", "ci") == "critical"

    def test_case_insensitive(self):
        assert _normalize_severity("NIT", "llm") == "info"
        assert _normalize_severity("Warning", "llm") == "warning"
        assert _normalize_severity("HIGH", "ci") == "error"

    def test_unknown_severity_defaults(self):
        assert _normalize_severity("unknown", "llm") == "suggestion"
        assert _normalize_severity("unknown", "ci") == "warning"

    def test_none_severity(self):
        assert _normalize_severity(None, "llm") == "info"
        assert _normalize_severity(None, "ci") == "info"

    def test_whitespace_handling(self):
        assert _normalize_severity("  warning  ", "llm") == "warning"


class TestNormalizeCategory:
    """Tests for category normalization"""

    def test_valid_categories(self):
        assert _normalize_category("style") == "style"
        assert _normalize_category("bug") == "bug"
        assert _normalize_category("performance") == "performance"
        assert _normalize_category("security") == "security"
        assert _normalize_category("maintainability") == "maintainability"
        assert _normalize_category("documentation") == "documentation"
        assert _normalize_category("other") == "other"

    def test_case_insensitive(self):
        assert _normalize_category("STYLE") == "style"
        assert _normalize_category("Bug") == "bug"

    def test_aliases(self):
        assert _normalize_category("formatting") == "style"
        assert _normalize_category("lint") == "style"
        assert _normalize_category("error") == "bug"
        assert _normalize_category("perf") == "performance"
        assert _normalize_category("sec") == "security"
        assert _normalize_category("refactor") == "maintainability"
        assert _normalize_category("docs") == "documentation"

    def test_unknown_defaults_to_other(self):
        assert _normalize_category("unknown") == "other"
        assert _normalize_category("random") == "other"

    def test_none_defaults_to_other(self):
        assert _normalize_category(None) == "other"


class TestValidateLineRange:
    """Tests for line range validation"""

    def test_valid_single_line(self):
        start, end, valid = validate_line_range(42, 42)
        assert start == 42
        assert end == 42
        assert valid is True

    def test_valid_range(self):
        start, end, valid = validate_line_range(10, 20)
        assert start == 10
        assert end == 20
        assert valid is True

    def test_both_none_is_valid(self):
        start, end, valid = validate_line_range(None, None)
        assert start is None
        assert end is None
        assert valid is True

    def test_only_end_line_becomes_single_line(self):
        start, end, valid = validate_line_range(None, 42)
        assert start == 42
        assert end == 42
        assert valid is True

    def test_only_start_line_becomes_single_line(self):
        start, end, valid = validate_line_range(42, None)
        assert start == 42
        assert end == 42
        assert valid is True

    def test_reversed_range_gets_swapped(self):
        start, end, valid = validate_line_range(50, 10)
        assert start == 10
        assert end == 50
        assert valid is True

    def test_large_range_flagged_invalid(self):
        start, end, valid = validate_line_range(1, MAX_LINE_RANGE + 100)
        assert start == 1
        assert end == MAX_LINE_RANGE + 100
        assert valid is False

    def test_custom_max_range(self):
        start, end, valid = validate_line_range(1, 20, max_range=10)
        assert valid is False

        start, end, valid = validate_line_range(1, 10, max_range=10)
        assert valid is True


class TestParseReviewComment:
    """Tests for parse_review_comment function"""

    def test_old_format_single_line(self):
        raw = {
            "file": "src/utils.py",
            "line": 42,
            "message": "Consider using list comprehension",
            "severity": "suggestion",
            "category": "style"
        }
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["file"] == "src/utils.py"
        assert comment["start_line"] == 42
        assert comment["end_line"] == 42
        assert comment["message"] == "Consider using list comprehension"
        assert comment["severity"] == "suggestion"
        assert comment["category"] == "style"
        assert comment["source"] == "llm"

    def test_new_format_multi_line(self):
        raw = {
            "file": "src/utils.py",
            "start_line": 10,
            "end_line": 15,
            "message": "This function is too complex",
            "severity": "warning",
            "category": "maintainability"
        }
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["start_line"] == 10
        assert comment["end_line"] == 15

    def test_mixed_format_prefers_end_line(self):
        raw = {
            "file": "src/utils.py",
            "line": 42,
            "end_line": 45,
            "start_line": 40,
            "message": "Test"
        }
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["start_line"] == 40
        assert comment["end_line"] == 45

    def test_missing_message_returns_none(self):
        raw = {"file": "src/utils.py", "line": 42}
        assert parse_review_comment(raw) is None

    def test_empty_message_returns_none(self):
        raw = {"file": "src/utils.py", "line": 42, "message": ""}
        assert parse_review_comment(raw) is None

        raw = {"file": "src/utils.py", "line": 42, "message": "   "}
        assert parse_review_comment(raw) is None

    def test_invalid_input_returns_none(self):
        assert parse_review_comment(None) is None
        assert parse_review_comment("not a dict") is None
        assert parse_review_comment([]) is None

    def test_ci_source_severity_mapping(self):
        raw = {"message": "CI failed", "severity": "high"}
        comment = parse_review_comment(raw, source="ci")

        assert comment is not None
        assert comment["severity"] == "error"
        assert comment["source"] == "ci"

    def test_file_path_aliases(self):
        for key in ["file", "path", "file_path"]:
            raw = {"message": "Test", key: "src/test.py"}
            comment = parse_review_comment(raw)
            assert comment is not None
            assert comment["file"] == "src/test.py"

    def test_preserve_raw(self):
        raw = {"message": "Test", "line": 42}
        comment = parse_review_comment(raw, preserve_raw=True)

        assert comment is not None
        assert comment["raw"] == raw

    def test_message_whitespace_trimmed(self):
        raw = {"message": "  Test message  "}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["message"] == "Test message"

    def test_comment_without_line_info(self):
        raw = {"message": "General comment about the PR"}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment.get("start_line") is None
        assert comment.get("end_line") is None
        assert comment.get("file") is None


class TestNormalizeReviewComments:
    """Tests for normalize_review_comments function"""

    def test_empty_list(self):
        assert normalize_review_comments([]) == []
        assert normalize_review_comments(None) == []

    def test_filters_invalid_comments(self):
        raw_comments = [
            {"message": "Valid comment"},
            {"file": "no message"},
            {"message": "Another valid"},
            None,
        ]
        normalized = normalize_review_comments(raw_comments)

        assert len(normalized) == 2
        assert normalized[0]["message"] == "Valid comment"
        assert normalized[1]["message"] == "Another valid"

    def test_source_propagation(self):
        raw_comments = [{"message": "Test"}]

        llm_comments = normalize_review_comments(raw_comments, source="llm")
        assert llm_comments[0]["source"] == "llm"

        ci_comments = normalize_review_comments(raw_comments, source="ci")
        assert ci_comments[0]["source"] == "ci"


class TestIsInlineComment:
    """Tests for is_inline_comment function"""

    def test_valid_inline_comment(self):
        comment: ReviewComment = {
            "message": "Test",
            "file": "src/test.py",
            "end_line": 42,
            "severity": "info",
            "category": "other",
            "source": "llm"
        }
        assert is_inline_comment(comment) is True

    def test_missing_file(self):
        comment: ReviewComment = {
            "message": "Test",
            "end_line": 42,
            "severity": "info",
            "category": "other",
            "source": "llm"
        }
        assert is_inline_comment(comment) is False

    def test_missing_line(self):
        comment: ReviewComment = {
            "message": "Test",
            "file": "src/test.py",
            "severity": "info",
            "category": "other",
            "source": "llm"
        }
        assert is_inline_comment(comment) is False


class TestToGithubInlinePayload:
    """Tests for to_github_inline_payload function"""

    def test_single_line_comment(self):
        comment: ReviewComment = {
            "message": "Fix this bug",
            "file": "src/test.py",
            "start_line": 42,
            "end_line": 42,
            "severity": "error",
            "category": "bug",
            "source": "llm"
        }
        payload = to_github_inline_payload(comment, "abc123")

        assert payload is not None
        assert payload["body"] == "Fix this bug"
        assert payload["commit_id"] == "abc123"
        assert payload["path"] == "src/test.py"
        assert payload["line"] == 42
        assert payload["side"] == "RIGHT"
        assert "start_line" not in payload

    def test_multi_line_comment(self):
        comment: ReviewComment = {
            "message": "Refactor this block",
            "file": "src/test.py",
            "start_line": 10,
            "end_line": 20,
            "severity": "warning",
            "category": "maintainability",
            "source": "llm"
        }
        payload = to_github_inline_payload(comment, "abc123")

        assert payload is not None
        assert payload["line"] == 20
        assert payload["start_line"] == 10
        assert payload["start_side"] == "RIGHT"

    def test_custom_side(self):
        comment: ReviewComment = {
            "message": "Test",
            "file": "src/test.py",
            "end_line": 42,
            "severity": "info",
            "category": "other",
            "source": "llm"
        }
        payload = to_github_inline_payload(comment, "abc123", side="LEFT")

        assert payload is not None
        assert payload["side"] == "LEFT"

    def test_missing_commit_id_returns_none(self):
        comment: ReviewComment = {
            "message": "Test",
            "file": "src/test.py",
            "end_line": 42,
            "severity": "info",
            "category": "other",
            "source": "llm"
        }
        assert to_github_inline_payload(comment, "") is None
        assert to_github_inline_payload(comment, None) is None

    def test_non_inline_comment_returns_none(self):
        comment: ReviewComment = {
            "message": "General comment",
            "severity": "info",
            "category": "other",
            "source": "llm"
        }
        assert to_github_inline_payload(comment, "abc123") is None


class TestMergeReviewComments:
    """Tests for merge_review_comments function"""

    def test_merge_ci_and_llm_comments(self):
        ci_comments = [
            {"message": "CI failed", "severity": "high"}
        ]
        llm_comments = [
            {"message": "Style issue", "severity": "nit", "file": "test.py", "line": 10}
        ]

        merged = merge_review_comments(ci_comments, llm_comments)

        assert len(merged) == 2
        assert merged[0]["source"] == "ci"
        assert merged[0]["severity"] == "error"  # high -> error
        assert merged[1]["source"] == "llm"
        assert merged[1]["severity"] == "info"  # nit -> info

    def test_empty_lists(self):
        assert merge_review_comments([], []) == []
        assert len(merge_review_comments([{"message": "Test"}], [])) == 1
        assert len(merge_review_comments([], [{"message": "Test"}])) == 1


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_negative_line_numbers_ignored(self):
        raw = {"message": "Test", "line": -5}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment.get("end_line") is None

    def test_zero_line_number_ignored(self):
        raw = {"message": "Test", "line": 0}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment.get("end_line") is None

    def test_string_line_numbers_parsed(self):
        raw = {"message": "Test", "line": "42"}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["end_line"] == 42

    def test_reversed_line_range_swapped(self):
        raw = {"message": "Test", "start_line": 50, "end_line": 10}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["start_line"] == 10
        assert comment["end_line"] == 50

    def test_very_large_line_numbers(self):
        raw = {"message": "Test", "line": 999999}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["end_line"] == 999999

    def test_special_characters_in_message(self):
        raw = {"message": "Fix: `foo()` -> `bar()` in <script>"}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["message"] == "Fix: `foo()` -> `bar()` in <script>"

    def test_unicode_in_message(self):
        raw = {"message": "修復這個問題 🐛"}
        comment = parse_review_comment(raw)

        assert comment is not None
        assert "修復" in comment["message"]

    def test_large_range_downgrades_to_file_level(self):
        """When line range is too large (>500), downgrade to file-level comment"""
        raw = {
            "message": "Suspicious range",
            "file": "src/test.py",
            "start_line": 1,
            "end_line": 600  # > MAX_LINE_RANGE (500)
        }
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["file"] == "src/test.py"
        # Line info should be stripped (downgraded to file-level)
        assert comment.get("start_line") is None
        assert comment.get("end_line") is None
        # Should NOT be considered an inline comment
        assert is_inline_comment(comment) is False

    def test_valid_range_keeps_line_info(self):
        """Valid line ranges should keep line info"""
        raw = {
            "message": "Valid range",
            "file": "src/test.py",
            "start_line": 1,
            "end_line": 100  # < MAX_LINE_RANGE (500)
        }
        comment = parse_review_comment(raw)

        assert comment is not None
        assert comment["start_line"] == 1
        assert comment["end_line"] == 100
        assert is_inline_comment(comment) is True
