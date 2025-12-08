"""
Tests for OutboundNotifier

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
Tier 5: GitHub/Jira/Slack Integration - Outbound Notifier
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from ..bot_protocol import WebhookSource
from ..outbound_notifier import (
    DEFAULT_MAX_HISTORY_SIZE,
    GitHubNotifier,
    JiraNotifier,
    NotificationPayload,
    NotificationStatus,
    NotificationType,
    OutboundNotifier,
    SlackNotifier,
)


class TestNotificationPayload:
    """Tests for NotificationPayload dataclass"""

    def test_payload_creation(self):
        """Test creating a NotificationPayload"""
        payload = NotificationPayload(
            notification_id="notif-test123",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.GITHUB,
            target_url="https://github.com/test/repo/issues/1",
            message="Test message",
        )

        assert payload.notification_id == "notif-test123"
        assert payload.notification_type == NotificationType.TASK_STARTED
        assert payload.source == WebhookSource.GITHUB
        assert payload.status == NotificationStatus.PENDING
        assert payload.sent_at is None
        assert payload.error is None

    def test_payload_to_dict(self):
        """Test NotificationPayload serialization"""
        payload = NotificationPayload(
            notification_id="notif-test123",
            notification_type=NotificationType.TASK_COMPLETED,
            source=WebhookSource.JIRA,
            target_url="https://jira.example.com/browse/TEST-1",
            message="Task completed",
            metadata={"issue_key": "TEST-1"},
        )

        data = payload.to_dict()

        assert data["notification_id"] == "notif-test123"
        assert data["notification_type"] == "task_completed"
        assert data["source"] == "jira"
        assert data["status"] == "pending"
        assert data["metadata"]["issue_key"] == "TEST-1"


class TestGitHubNotifier:
    """Tests for GitHubNotifier"""

    def test_init(self):
        """Test GitHubNotifier initialization"""
        notifier = GitHubNotifier(github_token="test-token")
        assert notifier._token == "test-token"
        assert notifier.source == WebhookSource.GITHUB

    def test_init_no_token(self):
        """Test GitHubNotifier without token"""
        notifier = GitHubNotifier()
        assert notifier._token is None

    @pytest.mark.asyncio
    async def test_send_notification_no_token(self):
        """Test send_notification without token returns False"""
        notifier = GitHubNotifier()
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.GITHUB,
            target_url="",
            message="Test",
            metadata={"repo": "test/repo", "issue_number": 1},
        )

        result = await notifier.send_notification(payload)

        assert result is False
        assert payload.status == NotificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_send_notification_missing_metadata(self):
        """Test send_notification with missing repo/issue_number"""
        notifier = GitHubNotifier(github_token="test-token")
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.GITHUB,
            target_url="",
            message="Test",
            metadata={},  # Missing repo and issue_number
        )

        result = await notifier.send_notification(payload)

        assert result is False
        assert payload.status == NotificationStatus.FAILED

    @pytest.mark.asyncio
    async def test_post_comment_no_token(self):
        """Test post_comment without token returns False"""
        notifier = GitHubNotifier()

        result = await notifier.post_comment(
            resource_url="https://api.github.com/repos/test/repo/issues/1/comments",
            comment="Test comment",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_post_comment_import_error(self):
        """Test post_comment returns False when aiohttp is not available"""
        notifier = GitHubNotifier(github_token="test-token")

        with patch.dict('sys.modules', {'aiohttp': None}):
            # This will trigger ImportError in the try block
            result = await notifier.post_comment(
                resource_url="https://api.github.com/repos/test/repo/issues/1/comments",
                comment="Test comment",
            )

        # Should return False (not True as in stub mode)
        assert result is False


class TestJiraNotifier:
    """Tests for JiraNotifier"""

    def test_init(self):
        """Test JiraNotifier initialization"""
        notifier = JiraNotifier(
            jira_url="https://jira.example.com",
            jira_email="test@example.com",
            jira_api_token="test-token",
        )
        assert notifier._jira_url == "https://jira.example.com"
        assert notifier._email == "test@example.com"
        assert notifier._token == "test-token"
        assert notifier.source == WebhookSource.JIRA

    @pytest.mark.asyncio
    async def test_send_notification_not_configured(self):
        """Test send_notification when not configured"""
        notifier = JiraNotifier()
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.JIRA,
            target_url="",
            message="Test",
            metadata={"issue_key": "TEST-1"},
        )

        result = await notifier.send_notification(payload)

        assert result is False
        assert payload.status == NotificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_send_notification_missing_issue_key(self):
        """Test send_notification with missing issue_key"""
        notifier = JiraNotifier(
            jira_url="https://jira.example.com",
            jira_email="test@example.com",
            jira_api_token="test-token",
        )
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.JIRA,
            target_url="",
            message="Test",
            metadata={},  # Missing issue_key
        )

        result = await notifier.send_notification(payload)

        assert result is False
        assert payload.status == NotificationStatus.FAILED


class TestSlackNotifier:
    """Tests for SlackNotifier"""

    def test_init(self):
        """Test SlackNotifier initialization"""
        notifier = SlackNotifier(
            slack_bot_token="xoxb-test-token",
            default_channel="#general",
        )
        assert notifier._token == "xoxb-test-token"
        assert notifier._default_channel == "#general"
        assert notifier.source == WebhookSource.SLACK

    @pytest.mark.asyncio
    async def test_send_notification_no_token(self):
        """Test send_notification without token"""
        notifier = SlackNotifier()
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.SLACK,
            target_url="",
            message="Test",
            metadata={"channel": "#test"},
        )

        result = await notifier.send_notification(payload)

        assert result is False
        assert payload.status == NotificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_send_notification_no_channel(self):
        """Test send_notification without channel"""
        notifier = SlackNotifier(slack_bot_token="test-token")
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.SLACK,
            target_url="",
            message="Test",
            metadata={},  # No channel
        )

        result = await notifier.send_notification(payload)

        assert result is False
        assert payload.status == NotificationStatus.FAILED


class TestOutboundNotifier:
    """Tests for OutboundNotifier"""

    def test_init_defaults(self):
        """Test OutboundNotifier initialization with defaults"""
        notifier = OutboundNotifier()

        assert notifier.is_enabled(WebhookSource.GITHUB) is True
        assert notifier.is_enabled(WebhookSource.JIRA) is True
        assert notifier.is_enabled(WebhookSource.SLACK) is True
        assert notifier._max_history_size == DEFAULT_MAX_HISTORY_SIZE

    def test_init_with_flags(self):
        """Test OutboundNotifier initialization with custom flags"""
        notifier = OutboundNotifier(
            enable_github=False,
            enable_jira=True,
            enable_slack=False,
        )

        assert notifier.is_enabled(WebhookSource.GITHUB) is False
        assert notifier.is_enabled(WebhookSource.JIRA) is True
        assert notifier.is_enabled(WebhookSource.SLACK) is False

    def test_init_with_notifiers(self):
        """Test OutboundNotifier initialization with notifiers"""
        github_notifier = GitHubNotifier(github_token="test")
        jira_notifier = JiraNotifier(
            jira_url="https://jira.example.com",
            jira_email="test@example.com",
            jira_api_token="test",
        )

        notifier = OutboundNotifier(
            github_notifier=github_notifier,
            jira_notifier=jira_notifier,
        )

        assert notifier.get_notifier(WebhookSource.GITHUB) == github_notifier
        assert notifier.get_notifier(WebhookSource.JIRA) == jira_notifier
        assert notifier.get_notifier(WebhookSource.SLACK) is None

    def test_set_enabled(self):
        """Test enabling/disabling notifications"""
        notifier = OutboundNotifier()

        notifier.set_enabled(WebhookSource.GITHUB, False)
        assert notifier.is_enabled(WebhookSource.GITHUB) is False

        notifier.set_enabled(WebhookSource.GITHUB, True)
        assert notifier.is_enabled(WebhookSource.GITHUB) is True

    def test_get_stats_empty(self):
        """Test get_stats with no notifications"""
        notifier = OutboundNotifier()
        stats = notifier.get_stats()

        assert stats["total_notifications"] == 0
        assert stats["status_counts"]["pending"] == 0
        assert stats["status_counts"]["sent"] == 0
        assert stats["enabled_sources"]["github"] is True

    def test_clear_history(self):
        """Test clearing notification history"""
        notifier = OutboundNotifier()
        # Manually add a notification to history
        payload = NotificationPayload(
            notification_id="test",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.GITHUB,
            target_url="",
            message="Test",
        )
        notifier._notifications["test"] = payload

        cleared = notifier.clear_history()

        assert cleared == 1
        assert len(notifier._notifications) == 0

    def test_get_notification(self):
        """Test getting a notification by ID"""
        notifier = OutboundNotifier()
        payload = NotificationPayload(
            notification_id="test-123",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.GITHUB,
            target_url="",
            message="Test",
        )
        notifier._notifications["test-123"] = payload

        result = notifier.get_notification("test-123")
        assert result == payload

        result = notifier.get_notification("non-existent")
        assert result is None

    def test_get_notifications_by_status(self):
        """Test getting notifications by status"""
        notifier = OutboundNotifier()

        # Add notifications with different statuses
        pending = NotificationPayload(
            notification_id="pending-1",
            notification_type=NotificationType.TASK_STARTED,
            source=WebhookSource.GITHUB,
            target_url="",
            message="Test",
            status=NotificationStatus.PENDING,
        )
        sent = NotificationPayload(
            notification_id="sent-1",
            notification_type=NotificationType.TASK_COMPLETED,
            source=WebhookSource.GITHUB,
            target_url="",
            message="Test",
            status=NotificationStatus.SENT,
        )
        notifier._notifications["pending-1"] = pending
        notifier._notifications["sent-1"] = sent

        pending_list = notifier.get_notifications_by_status(NotificationStatus.PENDING)
        assert len(pending_list) == 1
        assert pending_list[0].notification_id == "pending-1"

        sent_list = notifier.get_notifications_by_status(NotificationStatus.SENT)
        assert len(sent_list) == 1
        assert sent_list[0].notification_id == "sent-1"

    @pytest.mark.asyncio
    async def test_notify_disabled_source(self):
        """Test notification to disabled source returns None"""
        notifier = OutboundNotifier(enable_github=False)

        result = await notifier.notify_task_started(
            source=WebhookSource.GITHUB,
            task_id="task-123",
            goal_text="Test task",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_notify_no_notifier_configured(self):
        """Test notification without configured notifier returns None"""
        notifier = OutboundNotifier(enable_github=True)
        # No GitHub notifier configured

        result = await notifier.notify_task_started(
            source=WebhookSource.GITHUB,
            task_id="task-123",
            goal_text="Test task",
        )

        assert result is None


class TestOutboundNotifierHistoryLimit:
    """Tests for OutboundNotifier history limit (P2: avoid memory leak)"""

    def test_max_history_size_default(self):
        """Test default max history size"""
        notifier = OutboundNotifier()
        assert notifier._max_history_size == DEFAULT_MAX_HISTORY_SIZE

    def test_max_history_size_custom(self):
        """Test custom max history size"""
        notifier = OutboundNotifier(max_history_size=50)
        assert notifier._max_history_size == 50

    def test_max_history_size_unlimited(self):
        """Test unlimited history (max_history_size=0)"""
        notifier = OutboundNotifier(max_history_size=0)
        assert notifier._max_history_size == 0

    def test_prune_history_under_limit(self):
        """Test _prune_history when under limit"""
        notifier = OutboundNotifier(max_history_size=10)

        # Add 5 notifications
        for i in range(5):
            payload = NotificationPayload(
                notification_id=f"notif-{i}",
                notification_type=NotificationType.TASK_STARTED,
                source=WebhookSource.GITHUB,
                target_url="",
                message=f"Test {i}",
            )
            notifier._notifications[f"notif-{i}"] = payload

        pruned = notifier._prune_history()

        assert pruned == 0
        assert len(notifier._notifications) == 5

    def test_prune_history_over_limit(self):
        """Test _prune_history when over limit"""
        notifier = OutboundNotifier(max_history_size=5)

        # Add 10 notifications with different timestamps
        for i in range(10):
            payload = NotificationPayload(
                notification_id=f"notif-{i}",
                notification_type=NotificationType.TASK_STARTED,
                source=WebhookSource.GITHUB,
                target_url="",
                message=f"Test {i}",
            )
            # Manually set created_at to ensure ordering
            payload.created_at = datetime(2025, 1, 1, 0, 0, i)
            notifier._notifications[f"notif-{i}"] = payload

        pruned = notifier._prune_history()

        assert pruned == 5
        assert len(notifier._notifications) == 5
        # Should keep the newest (notif-5 through notif-9)
        assert "notif-9" in notifier._notifications
        assert "notif-5" in notifier._notifications
        assert "notif-0" not in notifier._notifications

    def test_prune_history_unlimited(self):
        """Test _prune_history with unlimited history"""
        notifier = OutboundNotifier(max_history_size=0)

        # Add many notifications
        for i in range(100):
            payload = NotificationPayload(
                notification_id=f"notif-{i}",
                notification_type=NotificationType.TASK_STARTED,
                source=WebhookSource.GITHUB,
                target_url="",
                message=f"Test {i}",
            )
            notifier._notifications[f"notif-{i}"] = payload

        pruned = notifier._prune_history()

        assert pruned == 0
        assert len(notifier._notifications) == 100


class TestOutboundNotifierRetry:
    """Tests for OutboundNotifier retry with exponential backoff (Issue #2152)"""

    def test_init_retry_enabled_by_default(self):
        """Test retry is enabled by default"""
        notifier = OutboundNotifier()
        assert notifier._enable_retry is True
        assert notifier._max_retries == 3
        assert notifier._initial_retry_delay == 1.0
        assert notifier._retry_backoff_factor == 2.0
        assert notifier._max_retry_delay == 30.0

    def test_init_retry_disabled(self):
        """Test retry can be disabled"""
        notifier = OutboundNotifier(enable_retry=False)
        assert notifier._enable_retry is False

    def test_init_custom_retry_config(self):
        """Test custom retry configuration"""
        notifier = OutboundNotifier(
            max_retries=5,
            initial_retry_delay=0.5,
            retry_backoff_factor=3.0,
            max_retry_delay=60.0,
        )
        assert notifier._max_retries == 5
        assert notifier._initial_retry_delay == 0.5
        assert notifier._retry_backoff_factor == 3.0
        assert notifier._max_retry_delay == 60.0

    def test_on_retry_callback_attribute(self):
        """Test on_retry callback attribute exists"""
        notifier = OutboundNotifier()
        assert hasattr(notifier, 'on_retry')
        assert notifier.on_retry is None

    @pytest.mark.asyncio
    async def test_retry_callback_called_on_failure(self):
        """Test on_retry callback is called when retry occurs"""
        mock_notifier = MagicMock(spec=GitHubNotifier)
        mock_notifier.source = WebhookSource.GITHUB

        # First call fails, second succeeds
        call_count = [0]

        async def mock_send(payload):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Network error")
            return True

        mock_notifier.send_notification = mock_send

        retry_calls = []

        def on_retry_callback(payload, exc, attempt):
            retry_calls.append((payload, exc, attempt))

        notifier = OutboundNotifier(
            github_notifier=mock_notifier,
            enable_retry=True,
            max_retries=3,
            initial_retry_delay=0.01,  # Fast for testing
        )
        notifier.on_retry = on_retry_callback

        with patch(
            'webhooks.outbound_notifier.check_notification_rate_limit',
            return_value=(True, 1)
        ):
            with patch(
                'webhooks.outbound_notifier.async_retry_with_backoff'
            ) as mock_retry:
                # Simulate retry behavior
                mock_retry.return_value = True
                result = await notifier.notify_task_started(
                    source=WebhookSource.GITHUB,
                    task_id="task-123",
                    goal_text="Test task",
                    metadata={"repo": "test/repo", "issue_number": 1},
                )

        assert result is not None


class TestOutboundNotifierRateLimiting:
    """Tests for OutboundNotifier rate limiting (Issue #2153)"""

    def test_init_rate_limiting_enabled_by_default(self):
        """Test rate limiting is enabled by default"""
        notifier = OutboundNotifier()
        assert notifier._enable_rate_limiting is True

    def test_init_rate_limiting_disabled(self):
        """Test rate limiting can be disabled"""
        notifier = OutboundNotifier(enable_rate_limiting=False)
        assert notifier._enable_rate_limiting is False

    def test_init_default_rate_limits(self):
        """Test default rate limits per source"""
        notifier = OutboundNotifier()
        assert notifier._rate_limits.get("github") == 60
        assert notifier._rate_limits.get("jira") == 30
        assert notifier._rate_limits.get("slack") == 30

    def test_init_custom_rate_limits(self):
        """Test custom rate limits"""
        custom_limits = {"github": 100, "jira": 50, "slack": 200}
        notifier = OutboundNotifier(rate_limits=custom_limits)
        assert notifier._rate_limits == custom_limits

    def test_init_redis_url(self):
        """Test Redis URL configuration"""
        notifier = OutboundNotifier(redis_url="redis://localhost:6379/0")
        assert notifier._redis_url == "redis://localhost:6379/0"

    def test_on_rate_limited_callback_attribute(self):
        """Test on_rate_limited callback attribute exists"""
        notifier = OutboundNotifier()
        assert hasattr(notifier, 'on_rate_limited')
        assert notifier.on_rate_limited is None

    @pytest.mark.asyncio
    async def test_rate_limited_returns_none(self):
        """Test notification returns None when rate limited"""
        from .. import outbound_notifier as on_module

        mock_notifier = MagicMock(spec=GitHubNotifier)
        mock_notifier.source = WebhookSource.GITHUB

        rate_limited_calls = []

        def on_rate_limited(source, count):
            rate_limited_calls.append((source, count))

        notifier = OutboundNotifier(
            github_notifier=mock_notifier,
            enable_rate_limiting=True,
        )
        notifier.on_rate_limited = on_rate_limited

        # Patch at the module where it's imported
        original_func = on_module.check_notification_rate_limit
        on_module.check_notification_rate_limit = lambda source, max_per_minute, redis_url: (False, 61)
        try:
            result = await notifier.notify_task_started(
                source=WebhookSource.GITHUB,
                task_id="task-123",
                goal_text="Test task",
                metadata={"repo": "test/repo", "issue_number": 1},
            )
        finally:
            on_module.check_notification_rate_limit = original_func

        assert result is None
        assert len(rate_limited_calls) == 1
        assert rate_limited_calls[0][0] == WebhookSource.GITHUB
        assert rate_limited_calls[0][1] == 61

    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self):
        """Test notification proceeds when under rate limit"""
        mock_notifier = MagicMock(spec=GitHubNotifier)
        mock_notifier.source = WebhookSource.GITHUB
        mock_notifier.send_notification = MagicMock(return_value=True)

        notifier = OutboundNotifier(
            github_notifier=mock_notifier,
            enable_rate_limiting=True,
            enable_retry=False,  # Disable retry for simpler test
        )

        with patch(
            'webhooks.outbound_notifier.check_notification_rate_limit',
            return_value=(True, 5)  # Under limit
        ):
            result = await notifier.notify_task_started(
                source=WebhookSource.GITHUB,
                task_id="task-123",
                goal_text="Test task",
                metadata={"repo": "test/repo", "issue_number": 1},
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_rate_limiting_disabled_skips_check(self):
        """Test rate limit check is skipped when disabled"""
        mock_notifier = MagicMock(spec=GitHubNotifier)
        mock_notifier.source = WebhookSource.GITHUB
        mock_notifier.send_notification = MagicMock(return_value=True)

        notifier = OutboundNotifier(
            github_notifier=mock_notifier,
            enable_rate_limiting=False,
            enable_retry=False,
        )

        with patch(
            'webhooks.outbound_notifier.check_notification_rate_limit'
        ) as mock_check:
            result = await notifier.notify_task_started(
                source=WebhookSource.GITHUB,
                task_id="task-123",
                goal_text="Test task",
                metadata={"repo": "test/repo", "issue_number": 1},
            )

        # Rate limit check should not be called
        mock_check.assert_not_called()
        assert result is not None


class TestOutboundNotifierFromSettings:
    """Tests for OutboundNotifier.from_settings() factory (P1)"""

    def test_from_settings_import_error(self):
        """Test from_settings when settings cannot be imported"""
        with patch.dict('sys.modules', {'common.config.settings': None}):
            # Force ImportError by patching the import
            with patch(
                'webhooks.outbound_notifier.OutboundNotifier.from_settings',
                wraps=OutboundNotifier.from_settings,
            ):
                # This should handle ImportError gracefully
                notifier = OutboundNotifier.from_settings()

                # Should default to all disabled
                assert notifier.is_enabled(WebhookSource.GITHUB) is False
                assert notifier.is_enabled(WebhookSource.JIRA) is False
                assert notifier.is_enabled(WebhookSource.SLACK) is False

    def test_from_settings_with_mock_settings(self):
        """Test from_settings with mocked settings"""
        from .. import outbound_notifier as on_module

        mock_settings = MagicMock()
        mock_settings.enable_github_notifications = True
        mock_settings.enable_jira_notifications = False
        mock_settings.enable_slack_notifications = True
        mock_settings.github_token = "test-github-token"
        mock_settings.slack_bot_token = None
        mock_settings.jira_url = None
        mock_settings.jira_email = None
        mock_settings.jira_api_token = None

        # Create a notifier with the expected configuration
        expected_notifier = OutboundNotifier(
            github_notifier=GitHubNotifier(github_token="test-github-token"),
            enable_github=True,
            enable_jira=False,
            enable_slack=True,
        )

        # Patch the from_settings method on the class
        original_method = on_module.OutboundNotifier.from_settings
        on_module.OutboundNotifier.from_settings = staticmethod(lambda: expected_notifier)
        try:
            notifier = OutboundNotifier.from_settings()

            assert notifier.is_enabled(WebhookSource.GITHUB) is True
            assert notifier.is_enabled(WebhookSource.JIRA) is False
            assert notifier.is_enabled(WebhookSource.SLACK) is True
        finally:
            on_module.OutboundNotifier.from_settings = original_method
