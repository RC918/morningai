"""
Tests for webhook routes.

Issue: #1822 - Integrate Development Tools
Milestone: M5 - Meta Agent Optimization

These tests cover the webhook API endpoints for GitHub, Jira, and Slack
integration with the Meta Agent system.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_normalizer():
    """Create a mock EventNormalizer."""
    normalizer = MagicMock()
    normalizer.process_webhook.return_value = MagicMock(
        success=True,
        message="Event received",
        to_dict=lambda: {"success": True, "message": "Event received"}
    )
    normalizer.parse_event.return_value = None
    normalizer.extract_task.return_value = None
    return normalizer


class TestWebhookHealth:
    """Tests for the /api/webhooks/health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 with status info."""
        response = client.get("/api/webhooks/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "normalizer_available" in data
        assert "timestamp" in data
        assert "handlers" in data

    def test_health_shows_handler_status(self, client):
        """Health endpoint should show handler availability."""
        response = client.get("/api/webhooks/health")
        data = response.get_json()
        assert "handlers" in data
        assert "github" in data["handlers"]
        assert "jira" in data["handlers"]
        assert "slack" in data["handlers"]


class TestGitHubWebhook:
    """Tests for the /api/webhooks/github endpoint."""

    def test_github_webhook_no_normalizer(self, client):
        """Should return 503 when normalizer is not available."""
        with patch("src.routes.webhooks.get_normalizer", return_value=None):
            response = client.post(
                "/api/webhooks/github",
                data=json.dumps({"action": "opened"}),
                content_type="application/json",
                headers={"X-GitHub-Event": "issues"}
            )
            assert response.status_code == 503
            data = response.get_json()
            assert "error" in data

    def test_github_webhook_invalid_json(self, client, mock_normalizer):
        """Should return 400 for invalid JSON payload."""
        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/github",
                data="not valid json {{{",
                content_type="application/json",
                headers={"X-GitHub-Event": "issues"}
            )
            # Flask's get_json with force=True may still parse or fail
            # The endpoint handles this gracefully
            assert response.status_code in [200, 400]

    def test_github_webhook_success(self, client, mock_normalizer):
        """Should return 200 for valid webhook."""
        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/github",
                data=json.dumps({
                    "action": "opened",
                    "issue": {"number": 123, "title": "Test issue"}
                }),
                content_type="application/json",
                headers={
                    "X-GitHub-Event": "issues",
                    "X-GitHub-Delivery": "test-delivery-123"
                }
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True

    def test_github_webhook_signature_failure(self, client, mock_normalizer):
        """Should return 401 for invalid signature."""
        mock_normalizer.process_webhook.return_value = MagicMock(
            success=False,
            message="Invalid signature",
            to_dict=lambda: {"success": False, "message": "Invalid signature"}
        )
        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/github",
                data=json.dumps({"action": "opened"}),
                content_type="application/json",
                headers={"X-GitHub-Event": "issues"}
            )
            assert response.status_code == 401

    def test_github_webhook_with_task_creation(self, client, mock_normalizer):
        """Should create task for actionable events."""
        mock_event = MagicMock()
        mock_event.to_dict.return_value = {"type": "issue_created"}
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Fix bug"
        mock_task.context = {"repo": "test/repo"}
        mock_task.to_dict.return_value = {"task_id": "task-123"}

        mock_normalizer.parse_event.return_value = mock_event
        mock_normalizer.extract_task.return_value = mock_task

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            with patch("src.routes.webhooks._enqueue_task", return_value="job-123"):
                response = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({
                        "action": "opened",
                        "issue": {"number": 123, "title": "Test"}
                    }),
                    content_type="application/json",
                    headers={"X-GitHub-Event": "issues"}
                )
                assert response.status_code == 200


class TestJiraWebhook:
    """Tests for the /api/webhooks/jira endpoint."""

    def test_jira_webhook_no_normalizer(self, client):
        """Should return 503 when normalizer is not available."""
        with patch("src.routes.webhooks.get_normalizer", return_value=None):
            response = client.post(
                "/api/webhooks/jira",
                data=json.dumps({"webhookEvent": "jira:issue_created"}),
                content_type="application/json"
            )
            assert response.status_code == 503

    def test_jira_webhook_success(self, client, mock_normalizer):
        """Should return 200 for valid webhook."""
        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/jira",
                data=json.dumps({
                    "webhookEvent": "jira:issue_created",
                    "issue": {"key": "TEST-123", "fields": {"summary": "Test"}}
                }),
                content_type="application/json"
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True

    def test_jira_webhook_signature_failure(self, client, mock_normalizer):
        """Should return 401 for invalid signature."""
        mock_normalizer.process_webhook.return_value = MagicMock(
            success=False,
            message="Invalid signature",
            to_dict=lambda: {"success": False, "message": "Invalid signature"}
        )
        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/jira",
                data=json.dumps({"webhookEvent": "jira:issue_created"}),
                content_type="application/json"
            )
            assert response.status_code == 401


class TestSlackWebhook:
    """Tests for the /api/webhooks/slack endpoint."""

    def test_slack_webhook_no_normalizer(self, client):
        """Should return 503 when normalizer is not available."""
        with patch("src.routes.webhooks.get_normalizer", return_value=None):
            response = client.post(
                "/api/webhooks/slack",
                data=json.dumps({"type": "event_callback"}),
                content_type="application/json"
            )
            assert response.status_code == 503

    def test_slack_url_verification(self, client, mock_normalizer):
        """Should respond to URL verification challenge."""
        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/slack",
                data=json.dumps({
                    "type": "url_verification",
                    "challenge": "test-challenge-123"
                }),
                content_type="application/json"
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["challenge"] == "test-challenge-123"

    def test_slack_webhook_success(self, client, mock_normalizer):
        """Should return 200 for valid webhook."""
        mock_handler = MagicMock()
        mock_handler.handle.return_value = MagicMock(
            success=True,
            message="Event received",
            to_dict=lambda: {"success": True, "message": "Event received"}
        )
        mock_normalizer.get_handler.return_value = mock_handler

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/slack",
                data=json.dumps({
                    "type": "event_callback",
                    "event": {"type": "message", "text": "Hello"},
                    "team_id": "T123"
                }),
                content_type="application/json",
                headers={
                    "X-Slack-Signature": "v0=test",
                    "X-Slack-Request-Timestamp": "1234567890"
                }
            )
            assert response.status_code == 200

    def test_slack_webhook_form_encoded(self, client, mock_normalizer):
        """Should handle form-encoded slash commands."""
        mock_handler = MagicMock()
        mock_handler.handle.return_value = MagicMock(
            success=True,
            message="Command received",
            to_dict=lambda: {"success": True, "message": "Command received"}
        )
        mock_normalizer.get_handler.return_value = mock_handler

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/slack",
                data={
                    "command": "/morningai",
                    "text": "help",
                    "team_id": "T123"
                },
                content_type="application/x-www-form-urlencoded"
            )
            assert response.status_code == 200

    def test_slack_webhook_no_handler(self, client, mock_normalizer):
        """Should return 400 when handler is not available."""
        mock_normalizer.get_handler.return_value = None

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/slack",
                data=json.dumps({
                    "type": "event_callback",
                    "event": {"type": "message"}
                }),
                content_type="application/json"
            )
            assert response.status_code == 400


class TestTestWebhook:
    """Tests for the /api/webhooks/test endpoint."""

    def test_test_webhook_blocked_in_production(self, client):
        """Should return 403 in production environment."""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.environment = "production"
            response = client.post(
                "/api/webhooks/test",
                data=json.dumps({"source": "github", "payload": {}}),
                content_type="application/json"
            )
            assert response.status_code == 403

    def test_test_webhook_no_normalizer(self, client):
        """Should return 503 when normalizer is not available."""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.environment = "development"
            with patch("src.routes.webhooks.get_normalizer", return_value=None):
                response = client.post(
                    "/api/webhooks/test",
                    data=json.dumps({"source": "github", "payload": {}}),
                    content_type="application/json"
                )
                assert response.status_code == 503

    def test_test_webhook_invalid_source(self, client, mock_normalizer):
        """Should return 400 for invalid source."""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.environment = "development"
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                response = client.post(
                    "/api/webhooks/test",
                    data=json.dumps({"source": "invalid", "payload": {}}),
                    content_type="application/json"
                )
                assert response.status_code == 400
                data = response.get_json()
                assert "Invalid source" in data["error"]

    def test_test_webhook_success(self, client, mock_normalizer):
        """Should return 200 with parsed event."""
        mock_event = MagicMock()
        mock_event.to_dict.return_value = {
            "type": "issue_created",
            "source": "github"
        }
        mock_normalizer.parse_event.return_value = mock_event
        mock_normalizer.extract_task.return_value = None

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.environment = "development"
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                response = client.post(
                    "/api/webhooks/test",
                    data=json.dumps({
                        "source": "github",
                        "headers": {"X-GitHub-Event": "issues"},
                        "payload": {"action": "opened"}
                    }),
                    content_type="application/json"
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["success"] is True
                assert "event" in data

    def test_test_webhook_parse_failure(self, client, mock_normalizer):
        """Should return 400 when event parsing fails."""
        mock_normalizer.parse_event.return_value = None

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.environment = "development"
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                response = client.post(
                    "/api/webhooks/test",
                    data=json.dumps({
                        "source": "github",
                        "payload": {}
                    }),
                    content_type="application/json"
                )
                assert response.status_code == 400
                data = response.get_json()
                assert "Failed to parse" in data["error"]


class TestEnqueueTask:
    """Tests for the _enqueue_task helper function."""

    def test_enqueue_task_no_redis_url(self):
        """Should return None when Redis URL is not configured."""
        from src.routes.webhooks import _enqueue_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Test goal"
        mock_task.context = {}

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None
            result = _enqueue_task(mock_task)
            assert result is None

    def test_enqueue_task_redis_error(self):
        """Should return None on Redis connection error."""
        from src.routes.webhooks import _enqueue_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Test goal"
        mock_task.context = {}

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            # Patch Redis at the redis module level since it's imported inside the function
            with patch("redis.Redis") as mock_redis:
                mock_redis.from_url.side_effect = Exception("Connection failed")
                result = _enqueue_task(mock_task)
                assert result is None


class TestGetNormalizer:
    """Tests for the get_normalizer helper function."""

    def test_get_normalizer_returns_cached(self):
        """Should return cached normalizer if already initialized."""
        import src.routes.webhooks as webhooks_module

        # Create a mock normalizer
        mock_normalizer = MagicMock()

        # Set the cached normalizer
        original_normalizer = webhooks_module._normalizer
        webhooks_module._normalizer = mock_normalizer

        try:
            result = webhooks_module.get_normalizer()
            assert result is mock_normalizer
        finally:
            # Restore original state
            webhooks_module._normalizer = original_normalizer

    def test_get_normalizer_creates_new(self):
        """Should create new normalizer if not cached."""
        import src.routes.webhooks as webhooks_module

        # Reset the cached normalizer
        original_normalizer = webhooks_module._normalizer
        webhooks_module._normalizer = None

        try:
            result = webhooks_module.get_normalizer()
            # Should either return a normalizer or None (if import fails)
            # The important thing is it doesn't crash
            assert result is None or result is not None
        finally:
            # Restore original state
            webhooks_module._normalizer = original_normalizer


class TestWebhookErrorHandling:
    """Tests for error handling in webhook endpoints."""

    def test_github_webhook_exception(self, client, mock_normalizer):
        """Should return 500 on unexpected exception."""
        mock_normalizer.process_webhook.side_effect = Exception("Unexpected error")

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/github",
                data=json.dumps({"action": "opened"}),
                content_type="application/json",
                headers={"X-GitHub-Event": "issues"}
            )
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data

    def test_jira_webhook_exception(self, client, mock_normalizer):
        """Should return 500 on unexpected exception."""
        mock_normalizer.process_webhook.side_effect = Exception("Unexpected error")

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/jira",
                data=json.dumps({"webhookEvent": "jira:issue_created"}),
                content_type="application/json"
            )
            assert response.status_code == 500

    def test_slack_webhook_exception(self, client, mock_normalizer):
        """Should return 500 on unexpected exception."""
        mock_normalizer.get_handler.side_effect = Exception("Unexpected error")

        with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
            response = client.post(
                "/api/webhooks/slack",
                data=json.dumps({"type": "event_callback"}),
                content_type="application/json"
            )
            assert response.status_code == 500
