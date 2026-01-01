"""
Tests for Deterministic Signals Ingestion Layer

Issue #3222: Deterministic Signals Ingestion - CI/Linters integration
"""

import pytest
from unittest.mock import MagicMock

from tools.signal_ingestion import (
    Signal,
    SignalSeverity,
    SignalSource,
    CheckRunSignalSource,
    WorkflowAnnotationSignalSource,
    fetch_signals,
    signals_to_review_comments,
)


class TestSignal:
    """Tests for Signal dataclass"""

    def test_signal_creation(self):
        """Test basic signal creation"""
        signal = Signal(
            source="eslint",
            severity=SignalSeverity.ERROR,
            file_path="src/index.ts",
            message="Unexpected console statement",
            line=42,
            rule_id="no-console",
        )

        assert signal.source == "eslint"
        assert signal.severity == SignalSeverity.ERROR
        assert signal.file_path == "src/index.ts"
        assert signal.message == "Unexpected console statement"
        assert signal.line == 42
        assert signal.rule_id == "no-console"

    def test_signal_to_dict(self):
        """Test signal serialization to dict"""
        signal = Signal(
            source="codeql",
            severity=SignalSeverity.WARNING,
            file_path="src/utils.py",
            message="Potential SQL injection",
            line=100,
            end_line=105,
        )

        result = signal.to_dict()

        assert result["source"] == "codeql"
        assert result["severity"] == "warning"
        assert result["file_path"] == "src/utils.py"
        assert result["message"] == "Potential SQL injection"
        assert result["line"] == 100
        assert result["end_line"] == 105

    def test_signal_to_review_comment(self):
        """Test signal conversion to review comment format with canonical schema"""
        signal = Signal(
            source="eslint",
            severity=SignalSeverity.ERROR,
            file_path="src/index.ts",
            message="Unexpected console statement",
            line=42,
            rule_id="no-console",
        )

        comment = signal.to_review_comment()

        assert comment["severity"] == "high"  # ERROR -> high
        assert "[eslint]" in comment["message"]
        assert comment["file"] == "src/index.ts"
        # Uses canonical start_line/end_line format (not legacy 'line')
        assert comment["start_line"] == 42
        assert comment["end_line"] == 42
        assert "line" not in comment  # Legacy field should not be present
        assert comment["deterministic"] is True

    def test_signal_to_review_comment_multiline(self):
        """Test signal conversion for multi-line annotations"""
        signal = Signal(
            source="codeql",
            severity=SignalSeverity.WARNING,
            file_path="src/utils.py",
            message="Potential SQL injection",
            line=100,
            end_line=105,
        )

        comment = signal.to_review_comment()

        assert comment["start_line"] == 100
        assert comment["end_line"] == 105
        assert "line" not in comment

    def test_signal_severity_mapping(self):
        """Test severity mapping in to_review_comment"""
        error_signal = Signal(
            source="test", severity=SignalSeverity.ERROR,
            file_path="test.py", message="error"
        )
        warning_signal = Signal(
            source="test", severity=SignalSeverity.WARNING,
            file_path="test.py", message="warning"
        )
        info_signal = Signal(
            source="test", severity=SignalSeverity.INFO,
            file_path="test.py", message="info"
        )

        assert error_signal.to_review_comment()["severity"] == "high"
        assert warning_signal.to_review_comment()["severity"] == "medium"
        assert info_signal.to_review_comment()["severity"] == "low"

    def test_signal_immutable(self):
        """Test that Signal is immutable (frozen dataclass)"""
        signal = Signal(
            source="test",
            severity=SignalSeverity.ERROR,
            file_path="test.py",
            message="test message",
        )

        with pytest.raises(AttributeError):
            signal.source = "modified"


class TestCheckRunSignalSource:
    """Tests for CheckRunSignalSource"""

    def test_fetch_signals_success(self):
        """Test successful signal fetch from check runs"""
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_check_run = MagicMock()
        mock_annotation = MagicMock()

        mock_annotation.annotation_level = "failure"
        mock_annotation.path = "src/index.ts"
        mock_annotation.message = "Type error: expected string"
        mock_annotation.title = "TypeScript Error"
        mock_annotation.start_line = 10
        mock_annotation.end_line = 10
        mock_annotation.start_column = 5
        mock_annotation.end_column = 20

        mock_check_run.name = "TypeScript Check"
        mock_check_run.output = MagicMock()
        mock_check_run.output.annotations_count = 1
        mock_check_run.get_annotations.return_value = [mock_annotation]

        mock_commit.get_check_runs.return_value = [mock_check_run]
        mock_repo.get_commit.return_value = mock_commit

        source = CheckRunSignalSource()
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 1
        assert signals[0].source == "check_run:TypeScript Check"
        assert signals[0].severity == SignalSeverity.ERROR
        assert signals[0].file_path == "src/index.ts"
        assert signals[0].message == "Type error: expected string"
        assert signals[0].line == 10

    def test_fetch_signals_no_annotations(self):
        """Test fetch when check runs have no annotations"""
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_check_run = MagicMock()

        mock_check_run.name = "Build"
        mock_check_run.output = MagicMock()
        mock_check_run.output.annotations_count = 0

        mock_commit.get_check_runs.return_value = [mock_check_run]
        mock_repo.get_commit.return_value = mock_commit

        source = CheckRunSignalSource()
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 0

    def test_fetch_signals_no_output(self):
        """Test fetch when check runs have no output"""
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_check_run = MagicMock()

        mock_check_run.name = "Build"
        mock_check_run.output = None

        mock_commit.get_check_runs.return_value = [mock_check_run]
        mock_repo.get_commit.return_value = mock_commit

        source = CheckRunSignalSource()
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 0

    def test_fetch_signals_max_annotations_limit(self):
        """Test that max_annotations_per_run limit is respected"""
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_check_run = MagicMock()

        # Create 100 annotations
        annotations = []
        for i in range(100):
            ann = MagicMock()
            ann.annotation_level = "warning"
            ann.path = f"file{i}.py"
            ann.message = f"Warning {i}"
            ann.title = None
            ann.start_line = i
            ann.end_line = i
            ann.start_column = None
            ann.end_column = None
            annotations.append(ann)

        mock_check_run.name = "Lint"
        mock_check_run.output = MagicMock()
        mock_check_run.output.annotations_count = 100
        mock_check_run.get_annotations.return_value = annotations

        mock_commit.get_check_runs.return_value = [mock_check_run]
        mock_repo.get_commit.return_value = mock_commit

        source = CheckRunSignalSource(max_annotations_per_run=10)
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 10

    def test_fetch_signals_github_api_error(self):
        """Test graceful handling of GitHub API errors"""
        from github import GithubException

        mock_repo = MagicMock()
        mock_repo.get_commit.side_effect = GithubException(404, {"message": "Not found"}, None)

        source = CheckRunSignalSource()
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 0

    def test_annotation_level_mapping(self):
        """Test annotation level to severity mapping"""
        mock_repo = MagicMock()
        mock_commit = MagicMock()

        # Create annotations with different levels
        levels = [
            ("failure", SignalSeverity.ERROR),
            ("error", SignalSeverity.ERROR),
            ("warning", SignalSeverity.WARNING),
            ("notice", SignalSeverity.INFO),
        ]

        check_runs = []
        for level, _ in levels:
            mock_check_run = MagicMock()
            mock_annotation = MagicMock()
            mock_annotation.annotation_level = level
            mock_annotation.path = f"file_{level}.py"
            mock_annotation.message = f"Message for {level}"
            mock_annotation.title = None
            mock_annotation.start_line = 1
            mock_annotation.end_line = 1
            mock_annotation.start_column = None
            mock_annotation.end_column = None

            mock_check_run.name = f"Check_{level}"
            mock_check_run.output = MagicMock()
            mock_check_run.output.annotations_count = 1
            mock_check_run.get_annotations.return_value = [mock_annotation]
            check_runs.append(mock_check_run)

        mock_commit.get_check_runs.return_value = check_runs
        mock_repo.get_commit.return_value = mock_commit

        source = CheckRunSignalSource()
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 4
        for signal, (level, expected_severity) in zip(signals, levels):
            assert signal.severity == expected_severity


class TestWorkflowAnnotationSignalSource:
    """Tests for WorkflowAnnotationSignalSource"""

    def test_fetch_signals_failed_job(self):
        """Test signal creation for failed workflow jobs"""
        mock_repo = MagicMock()
        mock_workflow_run = MagicMock()
        mock_job = MagicMock()

        mock_workflow_run.name = "Test CI"
        mock_workflow_run.id = 12345
        mock_job.name = "unit-tests"
        mock_job.conclusion = "failure"

        mock_workflow_run.jobs.return_value = [mock_job]
        mock_repo.get_workflow_runs.return_value = [mock_workflow_run]

        source = WorkflowAnnotationSignalSource(workflow_patterns=['test', 'ci'])
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 1
        assert signals[0].severity == SignalSeverity.ERROR
        assert "unit-tests" in signals[0].message
        assert signals[0].source == "workflow:Test CI"

    def test_fetch_signals_no_matching_workflow(self):
        """Test when no workflow matches the patterns"""
        mock_repo = MagicMock()
        mock_workflow_run = MagicMock()

        mock_workflow_run.name = "Deploy"  # Doesn't match 'test' or 'ci'

        mock_repo.get_workflow_runs.return_value = [mock_workflow_run]

        source = WorkflowAnnotationSignalSource(workflow_patterns=['test', 'ci'])
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 0

    def test_fetch_signals_successful_jobs(self):
        """Test that successful jobs don't create signals"""
        mock_repo = MagicMock()
        mock_workflow_run = MagicMock()
        mock_job = MagicMock()

        mock_workflow_run.name = "Test CI"
        mock_workflow_run.id = 12345
        mock_job.name = "unit-tests"
        mock_job.conclusion = "success"

        mock_workflow_run.jobs.return_value = [mock_job]
        mock_repo.get_workflow_runs.return_value = [mock_workflow_run]

        source = WorkflowAnnotationSignalSource(workflow_patterns=['test', 'ci'])
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 0

    def test_fetch_signals_github_api_error(self):
        """Test graceful handling of GitHub API errors"""
        from github import GithubException

        mock_repo = MagicMock()
        mock_repo.get_workflow_runs.side_effect = GithubException(500, {"message": "Server error"}, None)

        source = WorkflowAnnotationSignalSource()
        signals = source.fetch_signals(mock_repo, 123, "abc123", "trace-1")

        assert len(signals) == 0


class TestFetchSignals:
    """Tests for fetch_signals aggregation function"""

    def test_fetch_signals_aggregates_from_sources(self):
        """Test that fetch_signals aggregates from all sources"""
        mock_repo = MagicMock()

        # Create mock sources
        mock_source1 = MagicMock(spec=SignalSource)
        mock_source1.fetch_signals.return_value = [
            Signal(source="source1", severity=SignalSeverity.ERROR,
                   file_path="file1.py", message="Error 1"),
        ]

        mock_source2 = MagicMock(spec=SignalSource)
        mock_source2.fetch_signals.return_value = [
            Signal(source="source2", severity=SignalSeverity.WARNING,
                   file_path="file2.py", message="Warning 1"),
        ]

        signals = fetch_signals(
            mock_repo, 123, "abc123", "trace-1",
            sources=[mock_source1, mock_source2]
        )

        assert len(signals) == 2
        mock_source1.fetch_signals.assert_called_once()
        mock_source2.fetch_signals.assert_called_once()

    def test_fetch_signals_sorts_by_severity(self):
        """Test that signals are sorted by severity (errors first)"""
        mock_repo = MagicMock()

        mock_source = MagicMock(spec=SignalSource)
        mock_source.fetch_signals.return_value = [
            Signal(source="test", severity=SignalSeverity.INFO,
                   file_path="file1.py", message="Info"),
            Signal(source="test", severity=SignalSeverity.ERROR,
                   file_path="file2.py", message="Error"),
            Signal(source="test", severity=SignalSeverity.WARNING,
                   file_path="file3.py", message="Warning"),
        ]

        signals = fetch_signals(
            mock_repo, 123, "abc123", "trace-1",
            sources=[mock_source]
        )

        assert signals[0].severity == SignalSeverity.ERROR
        assert signals[1].severity == SignalSeverity.WARNING
        assert signals[2].severity == SignalSeverity.INFO

    def test_fetch_signals_handles_source_error(self):
        """Test that errors from one source don't affect others"""
        mock_repo = MagicMock()

        mock_source1 = MagicMock(spec=SignalSource)
        mock_source1.fetch_signals.side_effect = Exception("Source 1 failed")

        mock_source2 = MagicMock(spec=SignalSource)
        mock_source2.fetch_signals.return_value = [
            Signal(source="source2", severity=SignalSeverity.WARNING,
                   file_path="file.py", message="Warning"),
        ]

        signals = fetch_signals(
            mock_repo, 123, "abc123", "trace-1",
            sources=[mock_source1, mock_source2]
        )

        assert len(signals) == 1
        assert signals[0].source == "source2"


class TestSignalsToReviewComments:
    """Tests for signals_to_review_comments conversion"""

    def test_converts_signals_to_comments(self):
        """Test basic conversion of signals to review comments"""
        signals = [
            Signal(source="eslint", severity=SignalSeverity.ERROR,
                   file_path="src/index.ts", message="Error", line=10),
            Signal(source="codeql", severity=SignalSeverity.WARNING,
                   file_path="src/utils.py", message="Warning", line=20),
        ]

        comments = signals_to_review_comments(signals)

        assert len(comments) == 2
        assert comments[0]["severity"] == "high"
        assert comments[1]["severity"] == "medium"

    def test_excludes_info_by_default(self):
        """Test that info-level signals are excluded by default"""
        signals = [
            Signal(source="test", severity=SignalSeverity.ERROR,
                   file_path="file.py", message="Error"),
            Signal(source="test", severity=SignalSeverity.INFO,
                   file_path="file.py", message="Info"),
        ]

        comments = signals_to_review_comments(signals)

        assert len(comments) == 1
        assert comments[0]["severity"] == "high"

    def test_includes_info_when_requested(self):
        """Test that info-level signals are included when requested"""
        signals = [
            Signal(source="test", severity=SignalSeverity.ERROR,
                   file_path="file.py", message="Error"),
            Signal(source="test", severity=SignalSeverity.INFO,
                   file_path="file.py", message="Info"),
        ]

        comments = signals_to_review_comments(signals, include_info=True)

        assert len(comments) == 2

    def test_filters_signals_without_file_path(self):
        """Test that signals without file_path are filtered out (can't be inline comments)"""
        signals = [
            Signal(source="eslint", severity=SignalSeverity.ERROR,
                   file_path="src/index.ts", message="Error with file", line=10),
            Signal(source="workflow:test", severity=SignalSeverity.ERROR,
                   file_path="", message="Job-level failure without file"),  # Empty file_path
            Signal(source="codeql", severity=SignalSeverity.WARNING,
                   file_path="src/utils.py", message="Warning with file", line=20),
        ]

        comments = signals_to_review_comments(signals)

        # Only signals with file_path should be included
        assert len(comments) == 2
        assert all(c["file"] for c in comments)
        assert "eslint" in comments[0]["message"]
        assert "codeql" in comments[1]["message"]


class TestSignalSourceProtocol:
    """Tests for SignalSource protocol compliance"""

    def test_check_run_source_implements_protocol(self):
        """Test that CheckRunSignalSource implements SignalSource protocol"""
        source = CheckRunSignalSource()
        assert isinstance(source, SignalSource)

    def test_workflow_source_implements_protocol(self):
        """Test that WorkflowAnnotationSignalSource implements SignalSource protocol"""
        source = WorkflowAnnotationSignalSource()
        assert isinstance(source, SignalSource)
