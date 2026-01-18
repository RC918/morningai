"""
Tests for GitHubCommentParser - D-5 Phase 1

EPIC D Stage 3: D-5 Review Feedback Handler (General Fixes)
Issue: D-5 Phase 1 - GitHub Comment Parser

Blueprint Alignment:
- This parser belongs to the Infrastructure Layer (webhooks/parsers/)
- It converts external "dirty" GitHub payloads into clean internal formats
"""

import sys
import os
import unittest

# Add the parsers directory to the path for direct import
# This avoids triggering the full webhooks module import chain
_parsers_dir = os.path.dirname(os.path.dirname(__file__))
if _parsers_dir not in sys.path:
    sys.path.insert(0, _parsers_dir)

from github_comment_parser import (  # noqa: E402
    GitHubCommentParser,
    ParsedReviewComment,
    FixTask,
    CommentType,
    CommentSeverity,
    parse_review_comments,
    get_github_comment_parser,
)


class TestGitHubCommentParser(unittest.TestCase):
    """Tests for GitHubCommentParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = GitHubCommentParser(trace_id="test-trace-123")

    def test_init(self):
        """Test parser initialization."""
        parser = GitHubCommentParser(trace_id="abc123")
        self.assertEqual(parser.trace_id, "abc123")
        self.assertEqual(parser.stats.total_comments, 0)

    def test_parse_inline_comment_basic(self):
        """Test parsing a basic inline comment."""
        comment_data = {
            "id": 12345,
            "body": "Please add a docstring here",
            "path": "src/main.py",
            "line": 42,
            "user": {"login": "reviewer1"},
            "created_at": "2026-01-18T10:00:00Z",
        }

        result = self.parser.parse_inline_comment(comment_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.comment_id, "12345")
        self.assertEqual(result.comment_type, CommentType.INLINE)
        self.assertEqual(result.file_path, "src/main.py")
        self.assertEqual(result.line_number, 42)
        self.assertEqual(result.body, "Please add a docstring here")
        self.assertEqual(result.author, "reviewer1")
        self.assertFalse(result.is_resolved)

    def test_parse_file_comment(self):
        """Test parsing a file-level comment (no line number)."""
        comment_data = {
            "id": 12346,
            "body": "This file needs better organization",
            "path": "src/utils.py",
            "user": {"login": "reviewer2"},
        }

        result = self.parser.parse_inline_comment(comment_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.comment_type, CommentType.FILE)
        self.assertEqual(result.file_path, "src/utils.py")
        self.assertIsNone(result.line_number)

    def test_parse_general_comment(self):
        """Test parsing a general PR comment (no file)."""
        comment_data = {
            "id": 12347,
            "body": "Overall looks good, just a few minor issues",
            "user": {"login": "reviewer3"},
        }

        result = self.parser.parse_inline_comment(comment_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.comment_type, CommentType.GENERAL)
        self.assertIsNone(result.file_path)
        self.assertIsNone(result.line_number)

    def test_parse_multiline_comment(self):
        """Test parsing a multi-line comment."""
        comment_data = {
            "id": 12348,
            "body": "This entire block should be refactored",
            "path": "src/main.py",
            "start_line": 10,
            "line": 20,
        }

        result = self.parser.parse_inline_comment(comment_data)

        self.assertIsNotNone(result)
        self.assertEqual(result.line_range, (10, 20))
        self.assertEqual(result.line_number, 20)

    def test_extract_suggestion_code(self):
        """Test extracting code from GitHub suggestion blocks."""
        body = """Please fix this:
```suggestion
def fixed_function():
    return True
```
"""
        result = self.parser._extract_suggestion_code(body)

        self.assertEqual(result, "def fixed_function():\n    return True")

    def test_extract_suggestion_code_no_match(self):
        """Test extraction when no suggestion block present."""
        body = "Just a regular comment without suggestions"
        result = self.parser._extract_suggestion_code(body)
        self.assertIsNone(result)

    def test_infer_severity_blocker(self):
        """Test severity inference for blocker comments."""
        bodies = [
            "This is a security vulnerability, must fix",
            "Critical bug - do not merge",
            "This breaks the build",
        ]
        for body in bodies:
            result = self.parser.infer_severity(body)
            self.assertEqual(result, CommentSeverity.BLOCKER, f"Failed for: {body}")

    def test_infer_severity_suggestion(self):
        """Test severity inference for suggestion comments."""
        bodies = [
            "You should consider using a different approach",
            "I recommend adding error handling",
            "Please add type hints",
        ]
        for body in bodies:
            result = self.parser.infer_severity(body)
            self.assertEqual(result, CommentSeverity.SUGGESTION, f"Failed for: {body}")

    def test_infer_severity_nit(self):
        """Test severity inference for nit comments."""
        bodies = [
            "nit: extra whitespace",
            "Minor style issue",
            "Optional: could rename this variable",
        ]
        for body in bodies:
            result = self.parser.infer_severity(body)
            self.assertEqual(result, CommentSeverity.NIT, f"Failed for: {body}")

    def test_infer_severity_question(self):
        """Test severity inference for question comments."""
        bodies = [
            "Why did you choose this approach?",
            "What does this function do?",
            "I'm confused about this logic",
        ]
        for body in bodies:
            result = self.parser.infer_severity(body)
            self.assertEqual(result, CommentSeverity.QUESTION, f"Failed for: {body}")

    def test_infer_severity_praise(self):
        """Test severity inference for praise comments."""
        bodies = [
            "Great work on this!",
            "LGTM",
            "Thanks for fixing this",
        ]
        for body in bodies:
            result = self.parser.infer_severity(body)
            self.assertEqual(result, CommentSeverity.PRAISE, f"Failed for: {body}")

    def test_parse_github_review_comments_array(self):
        """Test parsing a list of comments."""
        review_data = [
            {
                "id": 1,
                "body": "Fix this issue",
                "path": "src/a.py",
                "line": 10,
            },
            {
                "id": 2,
                "body": "Also fix this",
                "path": "src/b.py",
                "line": 20,
            },
        ]

        results = self.parser.parse_github_review(review_data)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].file_path, "src/a.py")
        self.assertEqual(results[1].file_path, "src/b.py")

    def test_parse_github_review_with_comments_key(self):
        """Test parsing review data with 'comments' key."""
        review_data = {
            "comments": [
                {
                    "id": 1,
                    "body": "Fix this",
                    "path": "src/main.py",
                    "line": 5,
                }
            ]
        }

        results = self.parser.parse_github_review(review_data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].file_path, "src/main.py")

    def test_parse_github_review_skip_resolved(self):
        """Test that resolved comments are skipped by default."""
        review_data = [
            {
                "id": 1,
                "body": "Fix this",
                "path": "src/a.py",
                "line": 10,
                "resolved": True,
            },
            {
                "id": 2,
                "body": "Also fix this",
                "path": "src/b.py",
                "line": 20,
                "resolved": False,
            },
        ]

        results = self.parser.parse_github_review(review_data, include_resolved=False)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].file_path, "src/b.py")

    def test_parse_github_review_include_resolved(self):
        """Test including resolved comments when requested."""
        review_data = [
            {
                "id": 1,
                "body": "Fix this",
                "path": "src/a.py",
                "line": 10,
                "resolved": True,
            },
        ]

        results = self.parser.parse_github_review(review_data, include_resolved=True)

        self.assertEqual(len(results), 1)

    def test_to_fix_tasks_basic(self):
        """Test converting comments to fix tasks."""
        comments = [
            ParsedReviewComment(
                comment_id="1",
                comment_type=CommentType.INLINE,
                body="Add docstring",
                severity=CommentSeverity.SUGGESTION,
                file_path="src/main.py",
                line_number=10,
            ),
        ]

        tasks = self.parser.to_fix_tasks(comments)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].file_path, "src/main.py")
        self.assertIn("Add docstring", tasks[0].review_comment)
        self.assertEqual(tasks[0].severity, "medium")

    def test_to_fix_tasks_group_by_file(self):
        """Test grouping comments by file."""
        comments = [
            ParsedReviewComment(
                comment_id="1",
                comment_type=CommentType.INLINE,
                body="Fix line 10",
                severity=CommentSeverity.SUGGESTION,
                file_path="src/main.py",
                line_number=10,
            ),
            ParsedReviewComment(
                comment_id="2",
                comment_type=CommentType.INLINE,
                body="Fix line 20",
                severity=CommentSeverity.SUGGESTION,
                file_path="src/main.py",
                line_number=20,
            ),
        ]

        tasks = self.parser.to_fix_tasks(comments, group_by_file=True)

        self.assertEqual(len(tasks), 1)
        self.assertIn("Fix line 10", tasks[0].review_comment)
        self.assertIn("Fix line 20", tasks[0].review_comment)

    def test_to_fix_tasks_no_grouping(self):
        """Test creating separate tasks per comment."""
        comments = [
            ParsedReviewComment(
                comment_id="1",
                comment_type=CommentType.INLINE,
                body="Fix line 10",
                severity=CommentSeverity.SUGGESTION,
                file_path="src/main.py",
                line_number=10,
            ),
            ParsedReviewComment(
                comment_id="2",
                comment_type=CommentType.INLINE,
                body="Fix line 20",
                severity=CommentSeverity.SUGGESTION,
                file_path="src/main.py",
                line_number=20,
            ),
        ]

        tasks = self.parser.to_fix_tasks(comments, group_by_file=False)

        self.assertEqual(len(tasks), 2)

    def test_to_fix_tasks_skip_praise_and_questions(self):
        """Test that praise and question comments are skipped."""
        comments = [
            ParsedReviewComment(
                comment_id="1",
                comment_type=CommentType.INLINE,
                body="Great work!",
                severity=CommentSeverity.PRAISE,
                file_path="src/main.py",
                line_number=10,
            ),
            ParsedReviewComment(
                comment_id="2",
                comment_type=CommentType.INLINE,
                body="Why this approach?",
                severity=CommentSeverity.QUESTION,
                file_path="src/main.py",
                line_number=20,
            ),
        ]

        tasks = self.parser.to_fix_tasks(comments)

        self.assertEqual(len(tasks), 0)

    def test_to_fix_tasks_skip_no_file_path(self):
        """Test that comments without file_path are skipped."""
        comments = [
            ParsedReviewComment(
                comment_id="1",
                comment_type=CommentType.GENERAL,
                body="General feedback",
                severity=CommentSeverity.SUGGESTION,
                file_path=None,
            ),
        ]

        tasks = self.parser.to_fix_tasks(comments)

        self.assertEqual(len(tasks), 0)

    def test_to_fix_tasks_severity_mapping(self):
        """Test severity mapping to GeneralCoder format."""
        test_cases = [
            (CommentSeverity.BLOCKER, "high"),
            (CommentSeverity.SUGGESTION, "medium"),
            (CommentSeverity.NIT, "low"),
        ]

        for comment_severity, expected_coder_severity in test_cases:
            comments = [
                ParsedReviewComment(
                    comment_id="1",
                    comment_type=CommentType.INLINE,
                    body="Fix this",
                    severity=comment_severity,
                    file_path="src/main.py",
                    line_number=10,
                ),
            ]

            tasks = self.parser.to_fix_tasks(comments)

            self.assertEqual(
                tasks[0].severity,
                expected_coder_severity,
                f"Failed for {comment_severity}"
            )

    def test_to_fix_tasks_with_suggestion_code(self):
        """Test that suggestion code is passed through."""
        comments = [
            ParsedReviewComment(
                comment_id="1",
                comment_type=CommentType.INLINE,
                body="Use this instead",
                severity=CommentSeverity.SUGGESTION,
                file_path="src/main.py",
                line_number=10,
                suggestion_code="return True",
            ),
        ]

        tasks = self.parser.to_fix_tasks(comments)

        self.assertEqual(tasks[0].suggestion_code, "return True")

    def test_get_stats(self):
        """Test statistics collection."""
        review_data = [
            {"id": 1, "body": "Fix this", "path": "a.py", "line": 1},
            {"id": 2, "body": "Great!", "path": "b.py", "line": 2},
        ]

        self.parser.parse_github_review(review_data)
        stats = self.parser.get_stats()

        self.assertEqual(stats["total_comments"], 2)
        self.assertEqual(stats["inline_comments"], 2)

    def test_parsed_review_comment_to_dict(self):
        """Test ParsedReviewComment serialization."""
        comment = ParsedReviewComment(
            comment_id="123",
            comment_type=CommentType.INLINE,
            body="Test body",
            severity=CommentSeverity.SUGGESTION,
            file_path="test.py",
            line_number=42,
        )

        result = comment.to_dict()

        self.assertEqual(result["comment_id"], "123")
        self.assertEqual(result["comment_type"], "inline")
        self.assertEqual(result["severity"], "suggestion")

    def test_parsed_review_comment_from_dict(self):
        """Test ParsedReviewComment deserialization."""
        data = {
            "comment_id": "123",
            "comment_type": "inline",
            "body": "Test body",
            "severity": "suggestion",
            "file_path": "test.py",
            "line_number": 42,
        }

        result = ParsedReviewComment.from_dict(data)

        self.assertEqual(result.comment_id, "123")
        self.assertEqual(result.comment_type, CommentType.INLINE)
        self.assertEqual(result.severity, CommentSeverity.SUGGESTION)

    def test_fix_task_to_dict(self):
        """Test FixTask serialization."""
        task = FixTask(
            task_id="test-123",
            file_path="src/main.py",
            review_comment="Fix this issue",
            severity="medium",
            line_number=42,
            source_comments=["1", "2"],
        )

        result = task.to_dict()

        self.assertEqual(result["task_id"], "test-123")
        self.assertEqual(result["file_path"], "src/main.py")
        self.assertEqual(result["severity"], "medium")
        self.assertEqual(result["source_comments"], ["1", "2"])


class TestConvenienceFunctions(unittest.TestCase):
    """Tests for module-level convenience functions."""

    def test_parse_review_comments(self):
        """Test parse_review_comments convenience function."""
        review_data = [
            {"id": 1, "body": "Fix this", "path": "a.py", "line": 1},
        ]

        results = parse_review_comments(review_data, trace_id="test")

        self.assertEqual(len(results), 1)

    def test_get_github_comment_parser(self):
        """Test get_github_comment_parser factory function."""
        parser = get_github_comment_parser(trace_id="test-123")

        self.assertIsInstance(parser, GitHubCommentParser)
        self.assertEqual(parser.trace_id, "test-123")


if __name__ == "__main__":
    unittest.main()
