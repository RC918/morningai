"""
Tests for GitHub Annotations extraction in _fetch_failed_check_runs

Issue: #3681 - Add unit tests for GitHub Annotations extraction
Issue: #3676 - D-1b fix - Extract file paths from check_run annotations
Milestone: EPIC D - GeneralCoder multi-file support
"""

import pytest
from unittest.mock import MagicMock, patch

from ..normalizer import EventNormalizer


@pytest.fixture
def normalizer():
    """Create an EventNormalizer instance for testing"""
    return EventNormalizer()


class MockAnnotation:
    """Mock GitHub annotation object"""
    def __init__(self, path: str, start_line: int = 1, message: str = "Error message"):
        self.path = path
        self.start_line = start_line
        self.message = message


class MockCheckRun:
    """Mock GitHub check_run object"""
    def __init__(
        self,
        name: str,
        conclusion: str,
        annotations: list = None,
        output_summary: str = None
    ):
        self.name = name
        self.conclusion = conclusion
        self.status = "completed"
        self._annotations = annotations or []
        self.output = {"summary": output_summary} if output_summary else None

    def get_annotations(self):
        return self._annotations


class MockCheckSuite:
    """Mock GitHub check_suite object"""
    def __init__(self, check_runs: list):
        self._check_runs = check_runs

    def get_check_runs(self):
        return self._check_runs


class TestFetchAnnotationsSuccess:
    """Tests for successful annotation extraction"""

    def test_fetch_annotations_success(self, normalizer):
        """Test that annotations are extracted correctly from failed check_runs"""
        annotations = [
            MockAnnotation("src/main.py", 10, "Undefined variable 'foo'"),
            MockAnnotation("src/utils.py", 25, "Missing import"),
        ]
        check_run = MockCheckRun("lint", "failure", annotations)
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                failed_names, error_summary, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-123"
                )

        assert failed_names == ["lint"]
        assert "src/main.py" in file_paths
        assert "src/utils.py" in file_paths
        assert len(file_paths) == 2
        assert error_summary is not None
        assert "Undefined variable" in error_summary

    def test_extract_file_paths_from_annotations(self, normalizer):
        """Test that file paths are correctly extracted from annotation objects"""
        annotations = [
            MockAnnotation("src/components/Button.tsx", 15, "Type error"),
            MockAnnotation("src/hooks/useAuth.ts", 42, "Missing return"),
            MockAnnotation("src/utils/helpers.ts", 8, "Unused variable"),
        ]
        check_run = MockCheckRun("typecheck", "failure", annotations)
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                _, _, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-456"
                )

        assert len(file_paths) == 3
        assert "src/components/Button.tsx" in file_paths
        assert "src/hooks/useAuth.ts" in file_paths
        assert "src/utils/helpers.ts" in file_paths


class TestFilterGitHubWorkflowFiles:
    """Tests for filtering .github workflow files from annotations"""

    def test_filter_github_workflow_files(self, normalizer):
        """Test that .github files are filtered out from annotations"""
        annotations = [
            MockAnnotation(".github/workflows/ci.yml", 10, "Workflow error"),
            MockAnnotation("src/main.py", 20, "Code error"),
            MockAnnotation(".github/CODEOWNERS", 1, "Invalid owner"),
        ]
        check_run = MockCheckRun("validate", "failure", annotations)
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                _, _, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-789"
                )

        assert len(file_paths) == 1
        assert "src/main.py" in file_paths
        assert ".github/workflows/ci.yml" not in file_paths
        assert ".github/CODEOWNERS" not in file_paths


class TestAnnotationAPIFailureFallback:
    """Tests for fallback behavior when annotation API fails"""

    def test_annotation_api_failure_fallback(self, normalizer):
        """Test fallback to output.summary when annotation API fails"""
        check_run = MockCheckRun(
            "build",
            "failure",
            annotations=[],
            output_summary="Build failed: missing dependency 'lodash'"
        )
        # Make get_annotations raise an exception
        check_run.get_annotations = MagicMock(side_effect=Exception("API rate limit"))
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                failed_names, error_summary, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-fallback"
                )

        assert failed_names == ["build"]
        assert error_summary is not None
        assert "Build failed" in error_summary or "build" in error_summary.lower()
        assert file_paths == []  # No file paths from fallback

    def test_empty_annotations_fallback(self, normalizer):
        """Test fallback when annotations list is empty"""
        check_run = MockCheckRun(
            "test",
            "failure",
            annotations=[],
            output_summary="Test suite failed: 3 tests failed"
        )
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                failed_names, error_summary, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-empty"
                )

        assert failed_names == ["test"]
        assert error_summary is not None
        assert "Test suite failed" in error_summary or "test" in error_summary.lower()
        assert file_paths == []


class TestAnnotationAPIRateLimit:
    """Tests for graceful handling of API rate limits"""

    def test_annotation_api_rate_limit(self, normalizer):
        """Test graceful handling of API rate limits"""
        mock_repo = MagicMock()
        mock_repo.get_check_suite.side_effect = Exception("API rate limit exceeded")

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                failed_names, error_summary, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-rate-limit"
                )

        # Should return empty results on API failure (fail-open)
        assert failed_names == []
        assert error_summary is None
        assert file_paths == []


class TestMaxFilesLimit:
    """Tests for D-1b 5-file limit"""

    def test_max_5_files_limit(self, normalizer):
        """Test that only 5 files are returned (D-1b limit)"""
        annotations = [
            MockAnnotation(f"src/file{i}.py", i, f"Error in file {i}")
            for i in range(10)  # 10 files
        ]
        check_run = MockCheckRun("lint", "failure", annotations)
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                _, _, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-limit"
                )

        # Should be limited to 5 files (D-1b limit)
        assert len(file_paths) == 5


class TestDuplicateFilePaths:
    """Tests for duplicate file path deduplication"""

    def test_duplicate_file_paths_dedup(self, normalizer):
        """Test that duplicate paths are deduplicated"""
        annotations = [
            MockAnnotation("src/main.py", 10, "Error 1"),
            MockAnnotation("src/main.py", 20, "Error 2"),  # Same file
            MockAnnotation("src/utils.py", 5, "Error 3"),
            MockAnnotation("src/main.py", 30, "Error 4"),  # Same file again
        ]
        check_run = MockCheckRun("lint", "failure", annotations)
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                _, _, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-dedup"
                )

        # Should have only 2 unique files
        assert len(file_paths) == 2
        assert "src/main.py" in file_paths
        assert "src/utils.py" in file_paths


class TestAnnotationMissingAttributes:
    """Tests for handling malformed annotations"""

    def test_annotation_missing_path_attribute(self, normalizer):
        """Test handling of annotations missing path attribute"""
        # Create annotation without path attribute
        ann_with_path = MockAnnotation("src/valid.py", 10, "Valid error")
        ann_without_path = MagicMock()
        del ann_without_path.path  # Remove path attribute

        check_run = MockCheckRun("lint", "failure", [ann_with_path, ann_without_path])
        check_suite = MockCheckSuite([check_run])

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                _, _, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-missing-attr"
                )

        # Should only include the valid annotation
        assert len(file_paths) == 1
        assert "src/valid.py" in file_paths


class TestNoGitHubToken:
    """Tests for missing GITHUB_TOKEN"""

    def test_no_github_token_returns_empty(self, normalizer):
        """Test that missing GITHUB_TOKEN returns empty results"""
        with patch.dict("os.environ", {}, clear=True):
            # Ensure GITHUB_TOKEN is not set
            import os
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]

            failed_names, error_summary, file_paths = normalizer._fetch_failed_check_runs(
                "test-owner/test-repo", 12345, "test-event-no-token"
            )

        assert failed_names == []
        assert error_summary is None
        assert file_paths == []


class TestMultipleFailedCheckRuns:
    """Tests for multiple failed check_runs in a check_suite"""

    def test_multiple_failed_check_runs(self, normalizer):
        """Test extraction from multiple failed check_runs"""
        lint_annotations = [
            MockAnnotation("src/lint_error.py", 10, "Lint error"),
        ]
        test_annotations = [
            MockAnnotation("src/test_error.py", 20, "Test error"),
        ]

        check_runs = [
            MockCheckRun("lint", "failure", lint_annotations),
            MockCheckRun("test", "failure", test_annotations),
            MockCheckRun("build", "success", []),  # Success, should be ignored
        ]
        check_suite = MockCheckSuite(check_runs)

        mock_repo = MagicMock()
        mock_repo.get_check_suite.return_value = check_suite

        mock_github = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            with patch("github.Github", return_value=mock_github):
                failed_names, error_summary, file_paths = normalizer._fetch_failed_check_runs(
                    "test-owner/test-repo", 12345, "test-event-multiple"
                )

        assert "lint" in failed_names
        assert "test" in failed_names
        assert "build" not in failed_names
        assert "src/lint_error.py" in file_paths
        assert "src/test_error.py" in file_paths
