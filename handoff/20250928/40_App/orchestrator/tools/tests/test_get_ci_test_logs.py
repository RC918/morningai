"""
Tests for get_ci_test_logs function.

Issue #3369: Wire DiscoveryAuditor into Reviewer Agent workflow
This tests the CI log fetching functionality that enables DiscoveryAuditor
to cross-reference PR diff with CI logs to detect silent test failures.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestGetCiTestLogs:
    """Tests for get_ci_test_logs function."""

    def test_returns_error_when_repo_is_none(self):
        """Test that function returns error when repo is None."""
        from tools.github_api import get_ci_test_logs

        result = get_ci_test_logs(
            repo=None,
            pr_number=123,
            trace_id="test-trace"
        )

        assert result["success"] is False
        assert result["error"] == "Repository not available"
        assert result["logs"] == ""

    def test_returns_error_when_pr_not_found(self):
        """Test that function returns error when PR cannot be fetched."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_repo.get_pull.side_effect = Exception("PR not found")

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=999,
            trace_id="test-trace"
        )

        assert result["success"] is False
        assert "Failed to get PR" in result["error"]

    def test_returns_pending_when_no_workflow_runs(self):
        """Test that function returns pending status when no workflow runs found."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_workflow_runs.return_value = iter([])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            trace_id="test-trace"
        )

        assert result["success"] is False
        assert result["ci_status"] == "pending"
        assert "No workflow runs found" in result["error"]

    def test_returns_status_when_workflow_still_running(self):
        """Test that function returns workflow status when still running."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "in_progress"
        mock_run.conclusion = None
        mock_run.id = 12345
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            trace_id="test-trace"
        )

        assert result["success"] is False
        assert result["ci_status"] == "in_progress"
        assert "Workflow still in_progress" in result["error"]
        assert result["workflow_run_id"] == 12345

    def test_returns_error_when_no_jobs_found(self):
        """Test that function returns error when no jobs found in workflow run."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 12345
        mock_run.jobs.return_value = iter([])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            trace_id="test-trace"
        )

        assert result["success"] is False
        assert "No jobs found" in result["error"]

    @patch('requests.get')
    def test_successfully_fetches_logs_plaintext(self, mock_requests_get):
        """Test that function successfully fetches plaintext logs."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr

        mock_job = MagicMock()
        mock_job.name = "Orchestrator Tests"
        # logs_url is a property, not a method (Issue #3369 fix)
        mock_job.logs_url = "https://api.github.com/logs/12345"

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 12345
        mock_run.jobs.return_value = iter([mock_job])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "collected 100 items\ntest_foo.py::test_bar PASSED"
        # Issue #3369: Mock content for zip detection (plaintext has no zip signature)
        mock_response.content = b"collected 100 items\ntest_foo.py::test_bar PASSED"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_requests_get.return_value = mock_response

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123def456",
            trace_id="test-trace"
        )

        assert result["success"] is True
        assert result["ci_status"] == "success"
        assert result["workflow_run_id"] == 12345
        assert result["job_name"] == "Orchestrator Tests"
        assert "collected 100 items" in result["logs"]
        assert result["format"] == "plaintext"

    @patch('requests.get')
    def test_successfully_fetches_logs_from_zip(self, mock_requests_get):
        """Test that function successfully extracts logs from zip response."""
        from tools.github_api import get_ci_test_logs
        import zipfile
        import io

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr

        mock_job = MagicMock()
        mock_job.name = "Orchestrator Tests"
        mock_job.logs_url = "https://api.github.com/logs/12345"

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 12345
        mock_run.jobs.return_value = iter([mock_job])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        # Create a real zip file in memory with test logs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("job_logs.txt", "collected 50 items\ntest_bar.py::test_baz PASSED")
        zip_content = zip_buffer.getvalue()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = zip_content  # Has PK\x03\x04 signature
        mock_response.headers = {"Content-Type": "application/zip"}
        mock_requests_get.return_value = mock_response

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123def456",
            trace_id="test-trace"
        )

        assert result["success"] is True
        assert result["format"] == "zip"
        assert "collected 50 items" in result["logs"]
        assert "test_bar.py::test_baz PASSED" in result["logs"]

    @patch('requests.get')
    def test_handles_zip_extraction_failure(self, mock_requests_get):
        """Test that function handles zip extraction failure gracefully (fail-open)."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr

        mock_job = MagicMock()
        mock_job.name = "Orchestrator Tests"
        mock_job.logs_url = "https://api.github.com/logs/12345"

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 12345
        mock_run.jobs.return_value = iter([mock_job])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        # Create invalid zip content (has signature but corrupted)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'PK\x03\x04corrupted_zip_data'
        mock_response.headers = {"Content-Type": "application/zip"}
        mock_requests_get.return_value = mock_response

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123def456",
            trace_id="test-trace"
        )

        # Fail-open: extraction failure should not crash, but return error
        assert result["success"] is False
        assert "zip" in result["error"].lower() or "extract" in result["error"].lower()
        assert result["format"] == "zip_extraction_failed"

    @patch('requests.get')
    def test_returns_error_when_log_download_fails(self, mock_requests_get):
        """Test that function returns error when log download fails."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.head.sha = "abc123def456"
        mock_repo.get_pull.return_value = mock_pr

        mock_job = MagicMock()
        mock_job.name = "Orchestrator Tests"
        # logs_url is a property, not a method (Issue #3369 fix)
        mock_job.logs_url = "https://api.github.com/logs/12345"

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 12345
        mock_run.jobs.return_value = iter([mock_job])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            trace_id="test-trace"
        )

        assert result["success"] is False
        assert "Failed to download logs: HTTP 404" in result["error"]

    def test_uses_provided_head_sha(self):
        """Test that function uses provided head_sha instead of fetching from PR."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()
        mock_repo.get_workflow_runs.return_value = iter([])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="provided_sha_123",
            trace_id="test-trace"
        )

        mock_repo.get_pull.assert_not_called()
        # Verify event='pull_request' filter is applied (Issue #3369 fix)
        mock_repo.get_workflow_runs.assert_called_once_with(
            head_sha="provided_sha_123",
            event='pull_request'
        )

    def test_prefers_test_workflow_over_other_workflows(self):
        """Test that function prefers workflow with 'test' in name."""
        from tools.github_api import get_ci_test_logs

        mock_repo = MagicMock()

        mock_deploy_run = MagicMock()
        mock_deploy_run.name = "Deploy"
        mock_deploy_run.status = "completed"
        mock_deploy_run.conclusion = "success"
        mock_deploy_run.id = 11111

        mock_test_run = MagicMock()
        mock_test_run.name = "Test Apps"
        mock_test_run.status = "completed"
        mock_test_run.conclusion = "success"
        mock_test_run.id = 22222
        mock_test_run.jobs.return_value = iter([])

        mock_repo.get_workflow_runs.return_value = iter([mock_deploy_run, mock_test_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        assert result["workflow_run_id"] == 22222

    @patch('tools.github_api.settings')
    def test_uses_configurable_workflow_patterns(self, mock_settings):
        """Test that function uses configurable CI_WORKFLOW_PATTERNS (Issue #3377)."""
        from tools.github_api import get_ci_test_logs

        # Configure custom patterns
        mock_settings.ci_workflow_patterns = "build,lint"

        mock_repo = MagicMock()

        mock_deploy_run = MagicMock()
        mock_deploy_run.name = "Deploy"
        mock_deploy_run.status = "completed"
        mock_deploy_run.conclusion = "success"
        mock_deploy_run.id = 11111

        mock_test_run = MagicMock()
        mock_test_run.name = "Test Apps"  # Contains "test" but not in custom patterns
        mock_test_run.status = "completed"
        mock_test_run.conclusion = "success"
        mock_test_run.id = 22222

        mock_build_run = MagicMock()
        mock_build_run.name = "Build and Verify"  # Contains "build" - matches custom pattern
        mock_build_run.status = "completed"
        mock_build_run.conclusion = "success"
        mock_build_run.id = 33333
        mock_build_run.jobs.return_value = iter([])

        mock_repo.get_workflow_runs.return_value = iter([
            mock_deploy_run, mock_test_run, mock_build_run
        ])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "Build and Verify" because it contains "build"
        assert result["workflow_run_id"] == 33333

    @patch('tools.github_api.settings')
    def test_uses_default_patterns_when_empty(self, mock_settings):
        """Test that function falls back to default patterns when empty (Issue #3377)."""
        from tools.github_api import get_ci_test_logs

        # Configure empty patterns - should fall back to defaults
        mock_settings.ci_workflow_patterns = ""

        mock_repo = MagicMock()

        mock_test_run = MagicMock()
        mock_test_run.name = "CI Tests"  # Contains "ci" - default pattern
        mock_test_run.status = "completed"
        mock_test_run.conclusion = "success"
        mock_test_run.id = 44444
        mock_test_run.jobs.return_value = iter([])

        mock_repo.get_workflow_runs.return_value = iter([mock_test_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "CI Tests" using default pattern "ci"
        assert result["workflow_run_id"] == 44444

    @patch('tools.github_api.settings')
    def test_pattern_matching_is_case_insensitive(self, mock_settings):
        """Test that workflow pattern matching is case-insensitive (Issue #3377)."""
        from tools.github_api import get_ci_test_logs

        # Configure patterns in lowercase
        mock_settings.ci_workflow_patterns = "test,ci"

        mock_repo = MagicMock()

        mock_run = MagicMock()
        mock_run.name = "UNIT TESTS"  # Uppercase - should still match
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 55555
        mock_run.jobs.return_value = iter([])

        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "UNIT TESTS" because pattern matching is case-insensitive
        assert result["workflow_run_id"] == 55555

    @patch('tools.github_api.settings')
    def test_uses_configurable_job_patterns(self, mock_settings):
        """Test that function uses configurable CI_JOB_PATTERNS (Issue #3378)."""
        from tools.github_api import get_ci_test_logs

        # Configure custom job patterns
        mock_settings.ci_workflow_patterns = "test,ci"
        mock_settings.ci_job_patterns = "backend&test,frontend"

        mock_repo = MagicMock()

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 66666

        # Create mock jobs
        mock_job1 = MagicMock()
        mock_job1.name = "Frontend Tests"  # Contains "frontend" - matches second pattern
        mock_job1.logs_url = None

        mock_job2 = MagicMock()
        mock_job2.name = "Backend Test Suite"  # Contains "backend" AND "test" - matches first pattern
        mock_job2.logs_url = None

        mock_run.jobs.return_value = iter([mock_job1, mock_job2])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "Backend Test Suite" because it matches first pattern (backend&test)
        assert result["job_name"] == "Backend Test Suite"

    @patch('tools.github_api.settings')
    def test_job_pattern_and_logic(self, mock_settings):
        """Test that & in job patterns requires all parts to match (Issue #3378)."""
        from tools.github_api import get_ci_test_logs

        # Configure patterns with AND logic
        mock_settings.ci_workflow_patterns = "test"
        mock_settings.ci_job_patterns = "orchestrator&test"

        mock_repo = MagicMock()

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 77777

        # Create mock jobs
        mock_job1 = MagicMock()
        mock_job1.name = "API Tests"  # Contains "test" but not "orchestrator"
        mock_job1.logs_url = None

        mock_job2 = MagicMock()
        mock_job2.name = "Orchestrator Tests"  # Contains both "orchestrator" AND "test"
        mock_job2.logs_url = None

        mock_run.jobs.return_value = iter([mock_job1, mock_job2])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "Orchestrator Tests" because it contains both "orchestrator" AND "test"
        assert result["job_name"] == "Orchestrator Tests"

    @patch('tools.github_api.settings')
    def test_job_pattern_priority_order(self, mock_settings):
        """Test that job patterns are tried in priority order (Issue #3378)."""
        from tools.github_api import get_ci_test_logs

        # Configure patterns with priority order
        mock_settings.ci_workflow_patterns = "test"
        mock_settings.ci_job_patterns = "orchestrator&test,test"

        mock_repo = MagicMock()

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 88888

        # Create mock jobs - note: generic test job comes first
        mock_job1 = MagicMock()
        mock_job1.name = "API Backend Tests"  # Contains "test" - matches second pattern
        mock_job1.logs_url = None

        mock_job2 = MagicMock()
        mock_job2.name = "Orchestrator Tests"  # Contains "orchestrator" AND "test" - matches first pattern
        mock_job2.logs_url = None

        mock_run.jobs.return_value = iter([mock_job1, mock_job2])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "Orchestrator Tests" because first pattern has higher priority
        assert result["job_name"] == "Orchestrator Tests"

    @patch('tools.github_api.settings')
    def test_job_pattern_fallback_to_defaults(self, mock_settings):
        """Test that empty job patterns fall back to defaults (Issue #3378)."""
        from tools.github_api import get_ci_test_logs

        # Configure empty job patterns
        mock_settings.ci_workflow_patterns = "test"
        mock_settings.ci_job_patterns = ""

        mock_repo = MagicMock()

        mock_run = MagicMock()
        mock_run.name = "Test Apps"
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.id = 99999

        # Create mock jobs
        mock_job1 = MagicMock()
        mock_job1.name = "Lint Check"  # No match
        mock_job1.logs_url = None

        mock_job2 = MagicMock()
        mock_job2.name = "Orchestrator Tests"  # Matches default "orchestrator&test"
        mock_job2.logs_url = None

        mock_run.jobs.return_value = iter([mock_job1, mock_job2])
        mock_repo.get_workflow_runs.return_value = iter([mock_run])

        result = get_ci_test_logs(
            repo=mock_repo,
            pr_number=123,
            head_sha="abc123",
            trace_id="test-trace"
        )

        # Should match "Orchestrator Tests" using default pattern
        assert result["job_name"] == "Orchestrator Tests"
