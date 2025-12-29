"""
Unit tests for staging_webhook.py CLI tool.

These tests verify payload generation and basic functionality without
requiring network access or Redis connection.

Issue: #3265
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from staging_webhook import construct_task_payload, get_github_token, validate_payload  # noqa: E402


class TestConstructTaskPayload:
    """Tests for construct_task_payload function."""

    def test_payload_has_required_fields(self):
        """Payload should contain all required fields for orchestrator."""
        pr_data = {
            "number": 123,
            "title": "Test PR",
            "html_url": "https://github.com/test/repo/pull/123",
            "head": {"sha": "abc123def456789012345678901234567890abcd"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "test/repo")

        assert "task_id" in payload
        assert "question" in payload
        assert "repo" in payload
        assert "task_type" in payload
        assert "context" in payload

    def test_payload_task_id_format(self):
        """Task ID should follow staging-{uuid}-{pr_number} format."""
        pr_data = {
            "number": 456,
            "title": "Another PR",
            "html_url": "https://github.com/test/repo/pull/456",
            "head": {"sha": "def456abc789012345678901234567890abcdef"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "test/repo")

        assert payload["task_id"].startswith("staging-")
        assert payload["task_id"].endswith("-456")

    def test_payload_context_has_required_fields(self):
        """Context should contain all required fields for dedup and tracking."""
        pr_data = {
            "number": 789,
            "title": "PR with context",
            "html_url": "https://github.com/owner/repo/pull/789",
            "head": {"sha": "789abc012345678901234567890abcdef012345"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "owner/repo")
        context = payload["context"]

        assert context["resource_id"] == 789
        assert context["resource_type"] == "pull_request"
        assert context["url"] == "https://github.com/owner/repo/pull/789"
        assert context["head_sha"] == "789abc012345678901234567890abcdef012345"
        assert context["source"] == "staging_webhook_cli"
        assert "triggered_at" in context

    def test_payload_question_includes_pr_info(self):
        """Question should include PR number and title."""
        pr_data = {
            "number": 100,
            "title": "Fix important bug",
            "html_url": "https://github.com/test/repo/pull/100",
            "head": {"sha": "100abc012345678901234567890abcdef012345"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "test/repo")

        assert "#100" in payload["question"]
        assert "Fix important bug" in payload["question"]

    def test_payload_repo_matches_input(self):
        """Repo in payload should match input repo."""
        pr_data = {
            "number": 1,
            "title": "Test",
            "html_url": "https://github.com/RC918/morningai/pull/1",
            "head": {"sha": "abc123def456789012345678901234567890abcd"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "RC918/morningai")

        assert payload["repo"] == "RC918/morningai"

    def test_payload_task_type_is_review(self):
        """Task type should be 'review' for PR review tasks."""
        pr_data = {
            "number": 1,
            "title": "Test",
            "html_url": "https://github.com/test/repo/pull/1",
            "head": {"sha": "abc123def456789012345678901234567890abcd"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "test/repo")

        assert payload["task_type"] == "review"

    def test_head_sha_is_full_40_char(self):
        """Head SHA in context should be full 40-character hash."""
        full_sha = "abc123def456789012345678901234567890abcd"
        pr_data = {
            "number": 1,
            "title": "Test",
            "html_url": "https://github.com/test/repo/pull/1",
            "head": {"sha": full_sha},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "test/repo")

        assert payload["context"]["head_sha"] == full_sha
        assert len(payload["context"]["head_sha"]) == 40


class TestGetGithubToken:
    """Tests for get_github_token function."""

    def test_returns_env_token_if_set(self, monkeypatch):
        """Should return GITHUB_TOKEN from environment if set."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")

        token = get_github_token()

        assert token == "test-token-123"

    def test_returns_none_if_no_token_and_no_gh_cli(self, monkeypatch):
        """Should return None if no token and gh CLI not available."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        token = get_github_token()

        assert token is None or isinstance(token, str)


class TestValidatePayload:
    """Tests for validate_payload function."""

    def test_valid_payload_returns_no_errors(self):
        """Valid payload should return empty error list."""
        payload = {
            "task_id": "staging-abc12345-123",
            "question": "Review PR #123: Test",
            "repo": "test/repo",
            "task_type": "review",
            "context": {
                "resource_id": 123,
                "resource_type": "pull_request",
                "url": "https://github.com/test/repo/pull/123",
                "head_sha": "abc123def456789012345678901234567890abcd",
                "source": "staging_webhook_cli",
            },
        }

        errors = validate_payload(payload)

        assert errors == []

    def test_missing_required_field_returns_error(self):
        """Missing required field should return error."""
        payload = {
            "question": "Review PR #123: Test",
            "repo": "test/repo",
            "task_type": "review",
            "context": {},
        }

        errors = validate_payload(payload)

        assert any("task_id" in e for e in errors)

    def test_missing_context_field_returns_error(self):
        """Missing context field should return error."""
        payload = {
            "task_id": "staging-abc12345-123",
            "question": "Review PR #123: Test",
            "repo": "test/repo",
            "task_type": "review",
            "context": {
                "resource_id": 123,
            },
        }

        errors = validate_payload(payload)

        assert any("resource_type" in e for e in errors)
        assert any("url" in e for e in errors)
        assert any("head_sha" in e for e in errors)
        assert any("source" in e for e in errors)

    def test_invalid_resource_id_type_returns_error(self):
        """Non-integer resource_id should return error."""
        payload = {
            "task_id": "staging-abc12345-123",
            "question": "Review PR #123: Test",
            "repo": "test/repo",
            "task_type": "review",
            "context": {
                "resource_id": "123",
                "resource_type": "pull_request",
                "url": "https://github.com/test/repo/pull/123",
                "head_sha": "abc123def456789012345678901234567890abcd",
                "source": "staging_webhook_cli",
            },
        }

        errors = validate_payload(payload)

        assert any("resource_id must be an integer" in e for e in errors)

    def test_invalid_head_sha_length_returns_error(self):
        """Head SHA not 40 characters should return error."""
        payload = {
            "task_id": "staging-abc12345-123",
            "question": "Review PR #123: Test",
            "repo": "test/repo",
            "task_type": "review",
            "context": {
                "resource_id": 123,
                "resource_type": "pull_request",
                "url": "https://github.com/test/repo/pull/123",
                "head_sha": "abc123",
                "source": "staging_webhook_cli",
            },
        }

        errors = validate_payload(payload)

        assert any("head_sha must be a 40-character" in e for e in errors)

    def test_construct_payload_passes_validation(self):
        """Payload from construct_task_payload should pass validation."""
        pr_data = {
            "number": 123,
            "title": "Test PR",
            "html_url": "https://github.com/test/repo/pull/123",
            "head": {"sha": "abc123def456789012345678901234567890abcd"},
            "state": "open",
        }

        payload = construct_task_payload(pr_data, "test/repo")
        errors = validate_payload(payload)

        assert errors == []
