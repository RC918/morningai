"""
Error Path Tests - Systematic coverage of try/except blocks

Issue: #4231 - 系統性 Error Path 測試覆蓋
Blueprint Reference: Section 5.2 Telemetry & Logs v2

This module provides comprehensive tests for error handling paths in:
- routes/webhooks.py
- routes/governance.py
- services/auth_service.py

Test categories:
- Database connection errors
- Redis connection errors
- External API errors
- JSON parsing errors
- Permission/authentication errors
"""

import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-32chars")


class TestWebhooksErrorPaths:
    """Error path tests for routes/webhooks.py"""

    def test_enqueue_task_no_redis_url(self):
        """Test _enqueue_task returns None when Redis URL not configured"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None
            mock_settings.enable_meta_agent = False

            from src.routes.webhooks import _enqueue_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {"use_meta_agent": False}

            result = _enqueue_task(mock_task)
            assert result is None

    def test_enqueue_pr_updated_task_no_redis_url(self):
        """Test _enqueue_pr_updated_delayed_task handles missing Redis URL"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None

            from src.routes.webhooks import _enqueue_pr_updated_delayed_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {}

            result = _enqueue_pr_updated_delayed_task(mock_task)
            assert result is None

    def test_enqueue_pr_updated_task_no_repository(self):
        """Test _enqueue_pr_updated_delayed_task handles missing repository"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None
            mock_settings.rq_queue_name = "test"

            from src.routes.webhooks import _enqueue_pr_updated_delayed_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {}

            result = _enqueue_pr_updated_delayed_task(mock_task)
            assert result is None

    def test_enqueue_pr_updated_task_invalid_pr_number(self):
        """Test _enqueue_pr_updated_delayed_task handles invalid PR number"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = "test/repo"
            mock_settings.rq_queue_name = "test"

            from src.routes.webhooks import _enqueue_pr_updated_delayed_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {
                "repo": "test/repo",
                "resource_id": "not-a-number",
                "pr_updated_job_token": "token123",
            }

            result = _enqueue_pr_updated_delayed_task(mock_task)
            assert result is None

    def test_enqueue_pr_updated_task_no_job_token(self):
        """Test _enqueue_pr_updated_delayed_task handles missing job token"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = "test/repo"
            mock_settings.rq_queue_name = "test"

            from src.routes.webhooks import _enqueue_pr_updated_delayed_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {
                "repo": "test/repo",
                "resource_id": "123",
            }

            result = _enqueue_pr_updated_delayed_task(mock_task)
            assert result is None

    def test_enqueue_ci_failure_task_no_redis_url(self):
        """Test _enqueue_ci_failure_task handles missing Redis URL"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None

            from src.routes.webhooks import _enqueue_ci_failure_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {}

            result = _enqueue_ci_failure_task(mock_task)
            assert result is None

    def test_enqueue_ci_failure_task_no_repository(self):
        """Test _enqueue_ci_failure_task handles missing repository"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None
            mock_settings.rq_queue_name = "test"

            from src.routes.webhooks import _enqueue_ci_failure_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {}

            result = _enqueue_ci_failure_task(mock_task)
            assert result is None

    def test_enqueue_ci_failure_task_no_pr_number(self):
        """Test _enqueue_ci_failure_task handles missing PR number"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = "test/repo"
            mock_settings.rq_queue_name = "test"

            from src.routes.webhooks import _enqueue_ci_failure_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {"repo": "test/repo"}

            result = _enqueue_ci_failure_task(mock_task)
            assert result is None

    def test_post_manual_fix_acknowledgment_no_token(self):
        """Test _post_manual_fix_acknowledgment handles missing GitHub token"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.github_token = None

            from src.routes.webhooks import _post_manual_fix_acknowledgment

            result = _post_manual_fix_acknowledgment(
                "test/repo", 123, "testuser", "task-123"
            )
            assert result is False

    def test_get_pr_head_sha_no_token(self):
        """Test _get_pr_head_sha handles missing GitHub token"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.github_token = None

            from src.routes.webhooks import _get_pr_head_sha

            result = _get_pr_head_sha("test/repo", 123)
            assert result is None

    def test_sanitize_dedup_key_component_special_chars(self):
        """Test _sanitize_dedup_key_component handles special characters"""
        from src.routes.webhooks import _sanitize_dedup_key_component

        result = _sanitize_dedup_key_component("test:key:with:colons", "test")
        assert ":" not in result

        result = _sanitize_dedup_key_component("test\nkey\twith\rwhitespace", "test")
        assert "\n" not in result
        assert "\t" not in result

    def test_sanitize_dedup_key_component_empty(self):
        """Test _sanitize_dedup_key_component handles empty input"""
        from src.routes.webhooks import _sanitize_dedup_key_component

        result = _sanitize_dedup_key_component("", "test")
        assert result == ""

        result = _sanitize_dedup_key_component(None, "test")
        assert result == ""

    def test_check_webhook_delivery_idempotency_no_delivery_id(self):
        """Test _check_webhook_delivery_idempotency allows processing without delivery ID"""
        from src.routes.webhooks import _check_webhook_delivery_idempotency

        result = _check_webhook_delivery_idempotency("", "hook-456")
        assert result is False

    def test_enqueue_manual_fix_task_no_redis_url(self):
        """Test _enqueue_manual_fix_task handles missing Redis URL"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None

            from src.routes.webhooks import _enqueue_manual_fix_task

            result = _enqueue_manual_fix_task(
                "test/repo", 123, "abc123", {"manual_trigger_actor": "user"}, "task-123"
            )
            assert result is None

    def test_enqueue_meta_agent_task_no_redis_url(self):
        """Test _enqueue_meta_agent_task handles missing Redis URL"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None

            from src.routes.webhooks import _enqueue_meta_agent_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.context = {}

            result = _enqueue_meta_agent_task(mock_task)
            assert result is None

    def test_enqueue_meta_agent_task_no_repository(self):
        """Test _enqueue_meta_agent_task handles missing repository"""
        with patch("src.routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.github_repo = None
            mock_settings.rq_queue_name = "test"

            from src.routes.webhooks import _enqueue_meta_agent_task

            mock_task = MagicMock()
            mock_task.task_id = "test-task-123"
            mock_task.goal_text = "Test goal"
            mock_task.context = {}

            result = _enqueue_meta_agent_task(mock_task)
            assert result is None


class TestAuthServiceErrorPaths:
    """Error path tests for services/auth_service.py"""

    def test_get_redis_client_exception(self):
        """Test get_redis_client handles exceptions gracefully"""
        with patch("src.utils.redis_client.get_redis_client") as mock_get_redis:
            mock_get_redis.side_effect = Exception("Connection refused")

            from src.services.auth_service import get_redis_client

            result = get_redis_client()
            assert result is None

    def test_is_token_blacklisted_no_redis(self):
        """Test is_token_blacklisted returns False when Redis unavailable"""
        with patch("src.services.auth_service.get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = None

            from src.services.auth_service import is_token_blacklisted

            result = is_token_blacklisted("test-token")
            assert result is False

    def test_is_token_blacklisted_redis_error(self):
        """Test is_token_blacklisted handles Redis errors"""
        with patch("src.services.auth_service.get_redis_client") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.exists.side_effect = Exception("Redis error")
            mock_get_redis.return_value = mock_redis

            from src.services.auth_service import is_token_blacklisted

            result = is_token_blacklisted("test-token")
            assert result is False

    def test_blacklist_refresh_token_no_redis(self):
        """Test blacklist_refresh_token returns False when Redis unavailable"""
        with patch("src.services.auth_service.get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = None

            from src.services.auth_service import blacklist_refresh_token

            result = blacklist_refresh_token("test-token")
            assert result is False

    def test_blacklist_refresh_token_redis_error(self):
        """Test blacklist_refresh_token handles Redis errors"""
        with patch("src.services.auth_service.get_redis_client") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.setex.side_effect = Exception("Redis error")
            mock_get_redis.return_value = mock_redis

            from src.services.auth_service import blacklist_refresh_token

            result = blacklist_refresh_token("test-token")
            assert result is False

    def test_rotate_refresh_token_blacklist_failure(self):
        """Test rotate_refresh_token returns None when blacklist fails"""
        with patch("src.services.auth_service.blacklist_refresh_token") as mock_blacklist:
            mock_blacklist.return_value = False

            from src.services.auth_service import rotate_refresh_token

            result = rotate_refresh_token("old-token", "user-123", "test@example.com")
            assert result is None

    def test_verify_access_token_expired(self):
        """Test verify_access_token handles expired tokens"""
        import jwt

        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.side_effect = jwt.ExpiredSignatureError("Token expired")
            mock_service.return_value = mock_instance

            from src.services.auth_service import verify_access_token

            result = verify_access_token("expired-token")
            assert result is None

    def test_verify_access_token_invalid(self):
        """Test verify_access_token handles invalid tokens"""
        import jwt

        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.side_effect = jwt.InvalidTokenError("Invalid token")
            mock_service.return_value = mock_instance

            from src.services.auth_service import verify_access_token

            result = verify_access_token("invalid-token")
            assert result is None

    def test_verify_access_token_wrong_type(self):
        """Test verify_access_token rejects non-access tokens"""
        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.return_value = {"type": "refresh", "user_id": "123"}
            mock_service.return_value = mock_instance

            from src.services.auth_service import verify_access_token

            result = verify_access_token("refresh-token")
            assert result is None

    def test_verify_refresh_token_expired(self):
        """Test verify_refresh_token handles expired tokens"""
        import jwt

        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.side_effect = jwt.ExpiredSignatureError("Token expired")
            mock_service.return_value = mock_instance

            from src.services.auth_service import verify_refresh_token

            result = verify_refresh_token("expired-token")
            assert result is None

    def test_verify_refresh_token_invalid(self):
        """Test verify_refresh_token handles invalid tokens"""
        import jwt

        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.side_effect = jwt.InvalidTokenError("Invalid token")
            mock_service.return_value = mock_instance

            from src.services.auth_service import verify_refresh_token

            result = verify_refresh_token("invalid-token")
            assert result is None

    def test_verify_refresh_token_wrong_type(self):
        """Test verify_refresh_token rejects non-refresh tokens"""
        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.return_value = {"type": "access", "user_id": "123"}
            mock_service.return_value = mock_instance

            from src.services.auth_service import verify_refresh_token

            result = verify_refresh_token("access-token")
            assert result is None

    def test_verify_refresh_token_blacklisted(self):
        """Test verify_refresh_token rejects blacklisted tokens"""
        with patch("src.services.auth_service.get_token_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.decode.return_value = {"type": "refresh", "user_id": "123"}
            mock_service.return_value = mock_instance

            with patch("src.services.auth_service.is_token_blacklisted") as mock_blacklist:
                mock_blacklist.return_value = True

                from src.services.auth_service import verify_refresh_token

                result = verify_refresh_token("blacklisted-token")
                assert result is None

    def test_validate_security_config_weak_secret_production(self):
        """Test validate_security_config rejects weak secrets in production"""
        with patch("src.services.auth_service.is_production") as mock_prod:
            mock_prod.return_value = True

            with patch("src.services.auth_service._get_jwt_secret") as mock_secret:
                mock_secret.return_value = "short"

                from src.services.auth_service import validate_security_config

                with pytest.raises(RuntimeError):
                    validate_security_config()

    def test_validate_security_config_mock_users_production(self):
        """Test validate_security_config rejects mock users in production"""
        with patch("src.services.auth_service.is_production") as mock_prod:
            mock_prod.return_value = True

            with patch("src.services.auth_service._get_jwt_secret") as mock_secret:
                mock_secret.return_value = "a" * 32

                with patch("src.services.auth_service.is_mock_users_enabled") as mock_users:
                    mock_users.return_value = True

                    from src.services.auth_service import validate_security_config

                    with pytest.raises(SystemExit):
                        validate_security_config()

    def test_validate_security_config_invalid_samesite(self):
        """Test validate_security_config rejects invalid SameSite value"""
        with patch("src.services.auth_service.is_production") as mock_prod:
            mock_prod.return_value = False

            with patch("src.services.auth_service._get_jwt_secret") as mock_secret:
                mock_secret.return_value = "test-secret"

                with patch("src.services.auth_service.is_mock_users_enabled") as mock_users:
                    mock_users.return_value = False

                    with patch("src.services.auth_service.COOKIE_SAMESITE", "Invalid"):
                        from src.services.auth_service import validate_security_config

                        with pytest.raises(SystemExit):
                            validate_security_config()


class TestGovernanceErrorPaths:
    """Error path tests for routes/governance.py"""

    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from flask import Flask
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        return app

    def test_health_check_cost_tracker_exception(self, app):
        """Test health_check handles cost_tracker exception"""
        with patch("src.routes.governance.GOVERNANCE_AVAILABLE", True):
            with patch("src.routes.governance.get_cost_tracker") as mock_tracker:
                mock_tracker.side_effect = Exception("Redis error")

                from src.routes.governance import bp
                app.register_blueprint(bp)

                with app.test_client() as client:
                    response = client.get("/api/governance/health")
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data["components"]["cost_tracker"] == "unavailable"

    def test_health_check_reputation_engine_exception(self, app):
        """Test health_check handles reputation_engine exception"""
        with patch("src.routes.governance.GOVERNANCE_AVAILABLE", True):
            with patch("src.routes.governance.get_cost_tracker") as mock_tracker:
                mock_instance = MagicMock()
                mock_instance.redis = True
                mock_tracker.return_value = mock_instance

                with patch("src.routes.governance.get_reputation_engine") as mock_engine:
                    mock_engine.side_effect = Exception("Database error")

                    from src.routes.governance import bp
                    app.register_blueprint(bp)

                    with app.test_client() as client:
                        response = client.get("/api/governance/health")
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data["components"]["reputation_engine"] == "unavailable"

    def test_utc_now_iso_format(self):
        """Test _utc_now_iso returns correct format"""
        from src.routes.governance import _utc_now_iso

        result = _utc_now_iso()
        assert result.endswith("Z")
        assert "+" not in result


class TestWebhookRateLimiterErrorPaths:
    """Error path tests for WebhookRateLimiter"""

    def test_rate_limiter_allows_requests_under_limit(self):
        """Test rate limiter allows requests under limit"""
        from src.routes.webhooks import WebhookRateLimiter

        limiter = WebhookRateLimiter(limit=10, window=60)
        is_limited, remaining, reset_time = limiter.is_rate_limited("test-key")

        assert is_limited is False
        assert remaining == 9

    def test_rate_limiter_blocks_when_limit_exceeded(self):
        """Test rate limiter blocks when limit exceeded"""
        from src.routes.webhooks import WebhookRateLimiter

        limiter = WebhookRateLimiter(limit=2, window=60)

        limiter.is_rate_limited("test-key")
        limiter.is_rate_limited("test-key")
        is_limited, remaining, reset_time = limiter.is_rate_limited("test-key")

        assert is_limited is True
        assert remaining == 0

    def test_rate_limiter_separate_keys(self):
        """Test rate limiter tracks separate keys independently"""
        from src.routes.webhooks import WebhookRateLimiter

        limiter = WebhookRateLimiter(limit=2, window=60)

        limiter.is_rate_limited("key-1")
        limiter.is_rate_limited("key-1")
        is_limited_1, _, _ = limiter.is_rate_limited("key-1")

        is_limited_2, remaining_2, _ = limiter.is_rate_limited("key-2")

        assert is_limited_1 is True
        assert is_limited_2 is False
        assert remaining_2 == 1


class TestWebhookPayloadSizeErrorPaths:
    """Error path tests for webhook payload size validation"""

    def test_check_payload_size_valid(self):
        """Test check_payload_size allows valid payloads"""
        from flask import Flask
        from src.routes.webhooks import check_payload_size

        app = Flask(__name__)
        with app.test_request_context(
            "/test",
            method="POST",
            data=b"test",
            content_type="application/json"
        ):
            is_valid, error = check_payload_size()
            assert is_valid is True
            assert error is None

    def test_check_payload_size_too_large(self):
        """Test check_payload_size rejects oversized payloads"""
        from flask import Flask
        from src.routes.webhooks import check_payload_size, MAX_WEBHOOK_PAYLOAD_SIZE

        app = Flask(__name__)
        with app.test_request_context(
            "/test",
            method="POST",
            content_length=MAX_WEBHOOK_PAYLOAD_SIZE + 1,
            content_type="application/json"
        ):
            is_valid, error = check_payload_size()
            assert is_valid is False
            assert error is not None


class TestGetNormalizerErrorPaths:
    """Error path tests for get_normalizer function"""

    def test_get_normalizer_returns_cached_instance(self):
        """Test get_normalizer returns cached instance on subsequent calls"""
        import src.routes.webhooks as webhooks_module

        original_normalizer = webhooks_module._normalizer

        mock_normalizer = MagicMock()
        webhooks_module._normalizer = mock_normalizer

        result = webhooks_module.get_normalizer()
        assert result is mock_normalizer

        webhooks_module._normalizer = original_normalizer
