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
    def test_successfully_fetches_logs(self, mock_requests_get):
        """Test that function successfully fetches logs when everything works."""
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
