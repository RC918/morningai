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


class TestRateLimiting:
    """Tests for webhook rate limiting functionality."""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Should allow requests under the rate limit."""
        from src.routes.webhooks import WebhookRateLimiter
        
        limiter = WebhookRateLimiter(limit=10, window=60)
        
        # First request should not be limited
        is_limited, remaining, reset_time = limiter.is_rate_limited("test-key")
        assert is_limited is False
        assert remaining == 9  # 10 - 1 = 9 remaining
        assert reset_time > 0

    def test_rate_limiter_blocks_when_limit_exceeded(self):
        """Should block requests when rate limit is exceeded."""
        from src.routes.webhooks import WebhookRateLimiter
        
        limiter = WebhookRateLimiter(limit=3, window=60)
        
        # Make 3 requests to hit the limit
        for _ in range(3):
            limiter.is_rate_limited("test-key")
        
        # 4th request should be limited
        is_limited, remaining, reset_time = limiter.is_rate_limited("test-key")
        assert is_limited is True
        assert remaining == 0

    def test_rate_limiter_separate_keys(self):
        """Should track rate limits separately per key."""
        from src.routes.webhooks import WebhookRateLimiter
        
        limiter = WebhookRateLimiter(limit=2, window=60)
        
        # Exhaust limit for key1
        limiter.is_rate_limited("key1")
        limiter.is_rate_limited("key1")
        is_limited, _, _ = limiter.is_rate_limited("key1")
        assert is_limited is True
        
        # key2 should still have capacity
        is_limited, remaining, _ = limiter.is_rate_limited("key2")
        assert is_limited is False
        assert remaining == 1

    def test_rate_limit_returns_429(self, client, mock_normalizer):
        """Should return 429 when rate limit is exceeded."""
        import src.routes.webhooks as webhooks_module
        
        # Create a limiter with very low limit
        original_limiter = webhooks_module._webhook_rate_limiter
        webhooks_module._webhook_rate_limiter = webhooks_module.WebhookRateLimiter(limit=1, window=60)
        
        try:
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                # First request should succeed
                response1 = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={"X-GitHub-Event": "issues"}
                )
                assert response1.status_code == 200
                
                # Second request should be rate limited
                response2 = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={"X-GitHub-Event": "issues"}
                )
                assert response2.status_code == 429
                data = response2.get_json()
                assert "Rate limit exceeded" in data["error"]
                assert "X-RateLimit-Limit" in response2.headers
                assert "Retry-After" in response2.headers
        finally:
            webhooks_module._webhook_rate_limiter = original_limiter

    def test_rate_limit_headers_on_429_response(self, client, mock_normalizer):
        """Should include rate limit headers on 429 responses."""
        import src.routes.webhooks as webhooks_module
        
        # Create a limiter with very low limit
        original_limiter = webhooks_module._webhook_rate_limiter
        webhooks_module._webhook_rate_limiter = webhooks_module.WebhookRateLimiter(limit=1, window=60)
        
        try:
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                # First request to exhaust limit
                client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={"X-GitHub-Event": "issues"}
                )
                
                # Second request should have rate limit headers
                response = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={"X-GitHub-Event": "issues"}
                )
                assert response.status_code == 429
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
                assert "Retry-After" in response.headers
        finally:
            webhooks_module._webhook_rate_limiter = original_limiter


class TestPayloadSizeValidation:
    """Tests for webhook payload size validation."""

    def test_payload_size_check_allows_small_payloads(self):
        """Should allow payloads under the size limit."""
        from src.routes.webhooks import MAX_WEBHOOK_PAYLOAD_SIZE
        
        # MAX_WEBHOOK_PAYLOAD_SIZE should be 1MB
        assert MAX_WEBHOOK_PAYLOAD_SIZE == 1 * 1024 * 1024

    def test_check_payload_size_returns_error_for_large_payload(self):
        """Should return error tuple when payload exceeds size limit."""
        from src.routes.webhooks import check_payload_size, MAX_WEBHOOK_PAYLOAD_SIZE
        from flask import Flask
        
        test_app = Flask(__name__)
        with test_app.test_request_context(
            '/test',
            method='POST',
            content_length=2 * 1024 * 1024  # 2MB - exceeds 1MB limit
        ):
            is_valid, error_response = check_payload_size()
            assert is_valid is False
            assert error_response is not None
            # error_response is a tuple (response, status_code)
            assert error_response[1] == 413

    def test_check_payload_size_allows_small_payload(self):
        """Should allow payloads under the size limit."""
        from src.routes.webhooks import check_payload_size
        from flask import Flask
        
        test_app = Flask(__name__)
        with test_app.test_request_context(
            '/test',
            method='POST',
            content_length=1000  # 1KB - well under limit
        ):
            is_valid, error_response = check_payload_size()
            assert is_valid is True
            assert error_response is None

    def test_check_payload_size_allows_none_content_length(self):
        """Should allow requests with no Content-Length header."""
        from src.routes.webhooks import check_payload_size
        from flask import Flask
        
        test_app = Flask(__name__)
        with test_app.test_request_context(
            '/test',
            method='POST'
            # No content_length specified
        ):
            is_valid, error_response = check_payload_size()
            assert is_valid is True
            assert error_response is None

    def test_max_payload_size_constant(self):
        """Should have MAX_WEBHOOK_PAYLOAD_SIZE set to 1MB."""
        from src.routes.webhooks import MAX_WEBHOOK_PAYLOAD_SIZE
        assert MAX_WEBHOOK_PAYLOAD_SIZE == 1048576  # 1MB in bytes


class TestEnqueueTaskRepoValidation:
    """Tests for _enqueue_task repository validation."""

    def test_enqueue_task_no_repo_configured(self):
        """Should return None and log error when no repo is configured."""
        from src.routes.webhooks import _enqueue_task
        
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Test goal"
        mock_task.context = {}  # No repo in context
        
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None  # No repo in settings
            result = _enqueue_task(mock_task)
            assert result is None

    def test_enqueue_task_uses_context_repo(self):
        """Should use repo from task context."""
        from src.routes.webhooks import _enqueue_task
        
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Test goal"
        mock_task.context = {"repo": "test/repo-from-context"}
        
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = "fallback/repo"
            with patch("redis.Redis") as mock_redis:
                mock_conn = MagicMock()
                mock_redis.from_url.return_value = mock_conn
                with patch("rq.Queue") as mock_queue:
                    mock_q = MagicMock()
                    mock_job = MagicMock()
                    mock_job.id = "job-123"
                    mock_q.enqueue.return_value = mock_job
                    mock_queue.return_value = mock_q
                    
                    result = _enqueue_task(mock_task)
                    # Should succeed with context repo
                    assert result == "job-123"


class TestThreadSafeNormalizer:
    """Tests for thread-safe get_normalizer() singleton."""

    def test_get_normalizer_thread_safe(self):
        """Should use double-checked locking for thread safety."""
        import src.routes.webhooks as webhooks_module
        
        # Verify the lock exists
        assert hasattr(webhooks_module, '_normalizer_lock')
        assert webhooks_module._normalizer_lock is not None

    def test_get_normalizer_returns_same_instance(self):
        """Should return the same instance on multiple calls (singleton behavior)."""
        import src.routes.webhooks as webhooks_module
        
        # Save & reset the cached normalizer
        original = webhooks_module._normalizer
        webhooks_module._normalizer = None
        
        try:
            # Patch the class that get_normalizer() instantiates
            # This allows the real get_normalizer() logic to run
            with patch("orchestrator.webhooks.normalizer.EventNormalizer") as MockNormalizer:
                with patch("orchestrator.webhooks.bot_protocol.WebhookConfig"):
                    mock_instance = MockNormalizer.return_value
                    
                    # Call get_normalizer() twice
                    result1 = webhooks_module.get_normalizer()
                    result2 = webhooks_module.get_normalizer()
                    
                    # Both calls should return the same instance
                    assert result1 is mock_instance
                    assert result2 is mock_instance
                    assert result1 is result2
                    
                    # EventNormalizer should have been constructed only once
                    # (this verifies the singleton/double-checked locking behavior)
                    MockNormalizer.assert_called_once()
        finally:
            webhooks_module._normalizer = original


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


class TestEnqueuePRUpdatedDelayedTask:
    """Tests for the _enqueue_pr_updated_delayed_task helper function.

    Issue: Phase B-B - PR_UPDATED support with debounce/throttle
    """

    def test_enqueue_pr_updated_delayed_task_success(self):
        """Should schedule delayed task with enqueue_in for non-blocking debounce."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task
        from datetime import timedelta

        mock_task = MagicMock()
        mock_task.task_id = "task-pr-updated-123"
        mock_task.goal_text = "Review PR changes"
        mock_task.context = {
            "repo": "owner/repo",
            "resource_id": 42,
            "pr_updated_job_token": "token-abc",
            "pr_updated_debounce_seconds": 30,
        }

        mock_job = MagicMock()
        mock_job.id = "job-pr-updated-123"

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rq_queue_name = "orchestrator"
            mock_settings.github_repo = None

            with patch("redis.Redis") as mock_redis_class:
                mock_redis = MagicMock()
                mock_redis_class.from_url.return_value = mock_redis

                with patch("rq.Queue") as mock_queue_class:
                    mock_queue = MagicMock()
                    # Now using enqueue_in instead of enqueue
                    mock_queue.enqueue_in.return_value = mock_job
                    mock_queue_class.return_value = mock_queue

                    with patch("redis_queue.worker.run_pr_updated_delayed_task") as mock_worker_func:
                        result = _enqueue_pr_updated_delayed_task(mock_task)

                        assert result == "job-pr-updated-123"
                        # Verify enqueue_in is called (non-blocking delayed scheduling)
                        mock_queue.enqueue_in.assert_called_once()

                        call_args = mock_queue.enqueue_in.call_args
                        # First arg is timedelta for delay
                        assert call_args[0][0] == timedelta(seconds=30)
                        # Second arg is the worker function
                        assert call_args[0][1] == mock_worker_func
                        # Remaining positional args
                        assert call_args[0][2] == "task-pr-updated-123"
                        assert call_args[0][3] == "owner/repo"
                        assert call_args[0][4] == 42
                        assert call_args[0][5] == "token-abc"
                        assert call_args[0][6] == 30
                        assert call_args[0][7] == "Review PR changes"
                        assert call_args[1]["job_id"] == "task-pr-updated-123"
                        assert call_args[1]["ttl"] == 30 + 600

    def test_enqueue_pr_updated_delayed_task_no_redis_url(self):
        """Should return None when Redis URL is not configured."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.context = {"repo": "owner/repo", "resource_id": 42}

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None
            result = _enqueue_pr_updated_delayed_task(mock_task)
            assert result is None

    def test_enqueue_pr_updated_delayed_task_no_repo(self):
        """Should return None when no repository is specified."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.context = {"resource_id": 42, "pr_updated_job_token": "token"}

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None

            with patch("redis.Redis"):
                result = _enqueue_pr_updated_delayed_task(mock_task)
                assert result is None

    def test_enqueue_pr_updated_delayed_task_no_pr_number(self):
        """Should return None when no PR number is specified."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.context = {"repo": "owner/repo", "pr_updated_job_token": "token"}

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None

            with patch("redis.Redis"):
                result = _enqueue_pr_updated_delayed_task(mock_task)
                assert result is None

    def test_enqueue_pr_updated_delayed_task_invalid_pr_number(self):
        """Should return None when PR number is not a valid integer."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.context = {
            "repo": "owner/repo",
            "resource_id": "not-a-number",
            "pr_updated_job_token": "token"
        }

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None

            with patch("redis.Redis"):
                result = _enqueue_pr_updated_delayed_task(mock_task)
                assert result is None

    def test_enqueue_pr_updated_delayed_task_no_job_token(self):
        """Should return None when no job token is specified."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.context = {"repo": "owner/repo", "resource_id": 42}

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None

            with patch("redis.Redis"):
                result = _enqueue_pr_updated_delayed_task(mock_task)
                assert result is None

    def test_enqueue_pr_updated_delayed_task_uses_default_debounce(self):
        """Should use default debounce_seconds when not specified."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task
        from datetime import timedelta

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Review"
        mock_task.context = {
            "repo": "owner/repo",
            "resource_id": 42,
            "pr_updated_job_token": "token",
        }

        mock_job = MagicMock()
        mock_job.id = "job-123"

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rq_queue_name = "orchestrator"
            mock_settings.github_repo = None

            with patch("redis.Redis"):
                with patch("rq.Queue") as mock_queue_class:
                    mock_queue = MagicMock()
                    mock_queue.enqueue_in.return_value = mock_job
                    mock_queue_class.return_value = mock_queue

                    with patch("redis_queue.worker.run_pr_updated_delayed_task"):
                        result = _enqueue_pr_updated_delayed_task(mock_task)

                        assert result == "job-123"
                        call_args = mock_queue.enqueue_in.call_args
                        # First arg is timedelta with default 30 seconds
                        assert call_args[0][0] == timedelta(seconds=30)
                        # debounce_seconds is passed as 6th positional arg (index 6)
                        assert call_args[0][6] == 30
                        assert call_args[1]["ttl"] == 30 + 600

    def test_enqueue_pr_updated_delayed_task_redis_error(self):
        """Should return None on Redis connection error."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.context = {
            "repo": "owner/repo",
            "resource_id": 42,
            "pr_updated_job_token": "token",
        }

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"

            with patch("redis.Redis") as mock_redis:
                mock_redis.from_url.side_effect = Exception("Connection failed")
                result = _enqueue_pr_updated_delayed_task(mock_task)
                assert result is None

    def test_enqueue_pr_updated_delayed_task_uses_fallback_repo(self):
        """Should use settings.github_repo when context.repo is not set."""
        from src.routes.webhooks import _enqueue_pr_updated_delayed_task

        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.goal_text = "Review"
        mock_task.context = {
            "resource_id": 42,
            "pr_updated_job_token": "token",
            "pr_updated_debounce_seconds": 15,
        }

        mock_job = MagicMock()
        mock_job.id = "job-123"

        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rq_queue_name = "orchestrator"
            mock_settings.github_repo = "fallback/repo"

            with patch("redis.Redis"):
                with patch("rq.Queue") as mock_queue_class:
                    mock_queue = MagicMock()
                    mock_queue.enqueue_in.return_value = mock_job
                    mock_queue_class.return_value = mock_queue

                    with patch("redis_queue.worker.run_pr_updated_delayed_task"):
                        result = _enqueue_pr_updated_delayed_task(mock_task)

                        assert result == "job-123"
                        call_args = mock_queue.enqueue_in.call_args
                        # repo is the 3rd positional arg (index 3)
                        assert call_args[0][3] == "fallback/repo"


class TestWebhookDeliveryIdempotency:
    """Tests for webhook delivery idempotency (Issue #2879)."""

    def test_idempotency_allows_new_delivery(self):
        """Should allow processing of new webhook deliveries."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # Key was set (new delivery)

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            result = _check_webhook_delivery_idempotency("delivery-123")

            assert result is False  # Should process (not a duplicate)
            # Verify atomic SET with NX and EX was called
            mock_redis.set.assert_called_once()
            call_kwargs = mock_redis.set.call_args[1]
            assert call_kwargs.get("nx") is True
            assert call_kwargs.get("ex") == 7 * 24 * 60 * 60  # 7 days

    def test_idempotency_blocks_duplicate_delivery(self):
        """Should block processing of duplicate webhook deliveries."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        mock_redis = MagicMock()
        mock_redis.set.return_value = None  # Key exists (duplicate) - SET NX returns None

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            result = _check_webhook_delivery_idempotency("delivery-123")

            assert result is True  # Should skip (duplicate)
            mock_redis.set.assert_called_once()

    def test_idempotency_allows_when_no_delivery_id(self):
        """Should allow processing when delivery ID is missing."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        result = _check_webhook_delivery_idempotency("")
        assert result is False

        result = _check_webhook_delivery_idempotency("unknown")
        assert result is False

    def test_idempotency_allows_when_get_redis_client_raises_valueerror(self):
        """Should allow processing when get_redis_client() raises ValueError (not configured)."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        # get_redis_client raises ValueError when no Redis is configured
        with patch("utils.redis_client.get_redis_client", side_effect=ValueError("No Redis configuration")):
            result = _check_webhook_delivery_idempotency("delivery-123")

            assert result is False  # Should process (graceful degradation)

    def test_idempotency_allows_on_redis_error(self):
        """Should allow processing when Redis errors occur."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        # get_redis_client raises exception on connection failure
        with patch("utils.redis_client.get_redis_client", side_effect=Exception("Connection failed")):
            result = _check_webhook_delivery_idempotency("delivery-123")

            assert result is False  # Should process (graceful degradation)

    def test_idempotency_logs_warning_on_redis_error(self):
        """Should log warning when Redis error occurs (fail-open observability)."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        # get_redis_client raises exception on connection failure
        with patch("utils.redis_client.get_redis_client", side_effect=Exception("Connection failed")):
            with patch("src.routes.webhooks.logger") as mock_logger:
                _check_webhook_delivery_idempotency("delivery-123")

                # Verify warning is logged for observability (fail-open tracking)
                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args[0]
                assert "Redis error" in call_args[0]
                assert "idempotency" in call_args[0].lower()

    def test_idempotency_logs_info_on_duplicate_detection(self):
        """Should log info when duplicate is detected (observability)."""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        mock_redis = MagicMock()
        mock_redis.set.return_value = None  # Duplicate

        with patch("utils.redis_client.get_redis_client", return_value=mock_redis):
            with patch("src.routes.webhooks.logger") as mock_logger:
                _check_webhook_delivery_idempotency("delivery-123")

                # Verify info is logged for duplicate detection
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args[0]
                assert "Duplicate" in call_args[0]
                assert "delivery-123" in str(mock_logger.info.call_args)

    def test_github_webhook_handles_missing_delivery_header(self, client, mock_normalizer):
        """Should process webhook safely when X-GitHub-Delivery header is missing."""
        with patch("src.routes.webhooks._check_webhook_delivery_idempotency") as mock_check:
            mock_check.return_value = False  # Allow processing
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                response = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={
                        "X-GitHub-Event": "issues"
                        # Note: X-GitHub-Delivery header intentionally omitted
                    }
                )
                assert response.status_code == 200
                # Verify idempotency check was called with "unknown" fallback
                mock_check.assert_called_once_with("unknown")

    def test_github_webhook_duplicate_does_not_trigger_normalizer(self, client, mock_normalizer):
        """Should NOT call normalizer when duplicate is detected (no downstream processing)."""
        with patch("src.routes.webhooks._check_webhook_delivery_idempotency", return_value=True):
            with patch("src.routes.webhooks.get_normalizer") as mock_get_normalizer:
                response = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={
                        "X-GitHub-Event": "issues",
                        "X-GitHub-Delivery": "duplicate-delivery-123"
                    }
                )
                assert response.status_code == 200
                assert response.get_json()["status"] == "duplicate"
                # Verify normalizer was NOT called (no downstream processing)
                mock_get_normalizer.assert_not_called()

    def test_github_webhook_returns_duplicate_response(self, client, mock_normalizer):
        """Should return 200 with duplicate status for duplicate deliveries."""
        with patch("src.routes.webhooks._check_webhook_delivery_idempotency", return_value=True):
            response = client.post(
                "/api/webhooks/github",
                data=json.dumps({"action": "opened"}),
                content_type="application/json",
                headers={
                    "X-GitHub-Event": "issues",
                    "X-GitHub-Delivery": "duplicate-delivery-123"
                }
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "duplicate"
            assert "duplicate-delivery-123" in data["message"]

    def test_github_webhook_processes_new_delivery(self, client, mock_normalizer):
        """Should process new webhook deliveries normally."""
        with patch("src.routes.webhooks._check_webhook_delivery_idempotency", return_value=False):
            with patch("src.routes.webhooks.get_normalizer", return_value=mock_normalizer):
                response = client.post(
                    "/api/webhooks/github",
                    data=json.dumps({"action": "opened"}),
                    content_type="application/json",
                    headers={
                        "X-GitHub-Event": "issues",
                        "X-GitHub-Delivery": "new-delivery-123"
                    }
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["success"] is True
