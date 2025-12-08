"""
Outbound Notifier - Post Status Updates to External Services

This module provides the OutboundNotifier that sends task status updates
back to external services (GitHub, Jira, Slack) when tasks are processed.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
Tier 5: GitHub/Jira/Slack Integration - Outbound Notifier

Flow:
    TaskIntakeService → Task Completed/Failed → OutboundNotifier → External Service
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .bot_protocol import WebhookSource

# Import retry and rate limiting utilities (Issue #2152, #2153)
try:
    from utils.retry import async_retry_with_backoff, NOTIFICATION_RETRY_CONFIG
    from utils.rate_limit import (
        check_notification_rate_limit,
        DEFAULT_NOTIFICATION_RATE_LIMITS,
    )
    _RETRY_AVAILABLE = True
    _RATE_LIMIT_AVAILABLE = True
except ImportError:
    _RETRY_AVAILABLE = False
    _RATE_LIMIT_AVAILABLE = False
    NOTIFICATION_RETRY_CONFIG = None
    DEFAULT_NOTIFICATION_RATE_LIMITS = {"github": 60, "jira": 30, "slack": 30}

logger = logging.getLogger(__name__)


class NotificationStatus(Enum):
    """Status of a notification attempt"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class NotificationType(Enum):
    """Type of notification to send"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"
    APPROVAL_REQUIRED = "approval_required"
    PR_CREATED = "pr_created"
    COMMENT_ADDED = "comment_added"


@dataclass
class NotificationPayload:
    """
    Payload for an outbound notification.
    """
    notification_id: str
    notification_type: NotificationType
    source: WebhookSource
    target_url: str
    message: str
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type.value,
            "source": self.source.value,
            "target_url": self.target_url,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseNotifier(ABC):
    """
    Abstract base class for service-specific notifiers.
    """

    @property
    @abstractmethod
    def source(self) -> WebhookSource:
        """Return the webhook source this notifier handles"""
        pass

    @abstractmethod
    async def send_notification(
        self,
        payload: NotificationPayload,
    ) -> bool:
        """
        Send a notification to the external service.

        Args:
            payload: Notification payload

        Returns:
            True if notification was sent successfully
        """
        pass

    @abstractmethod
    async def post_comment(
        self,
        resource_url: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Post a comment to a resource (issue, PR, ticket).

        Args:
            resource_url: URL of the resource to comment on
            comment: Comment text
            metadata: Additional metadata (e.g., repo, issue number)

        Returns:
            True if comment was posted successfully
        """
        pass


class GitHubNotifier(BaseNotifier):
    """
    Notifier for GitHub - posts comments to issues and PRs.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        api_base_url: str = "https://api.github.com",
    ):
        """
        Initialize GitHub notifier.

        Args:
            github_token: GitHub API token for authentication
            api_base_url: GitHub API base URL
        """
        self._token = github_token
        self._api_base_url = api_base_url
        logger.info("[GitHubNotifier] Initialized")

    @property
    def source(self) -> WebhookSource:
        return WebhookSource.GITHUB

    async def send_notification(
        self,
        payload: NotificationPayload,
    ) -> bool:
        """Send notification to GitHub (post comment)"""
        if not self._token:
            logger.warning("[GitHubNotifier] No token configured, skipping notification")
            payload.status = NotificationStatus.SKIPPED
            payload.error = "No GitHub token configured"
            return False

        # Extract repo and issue/PR number from metadata
        repo = payload.metadata.get("repo")
        issue_number = payload.metadata.get("issue_number") or payload.metadata.get("pr_number")

        if not repo or not issue_number:
            logger.warning(
                "[GitHubNotifier] Missing repo or issue_number in metadata"
            )
            payload.status = NotificationStatus.FAILED
            payload.error = "Missing repo or issue_number"
            return False

        return await self.post_comment(
            resource_url=f"{self._api_base_url}/repos/{repo}/issues/{issue_number}/comments",
            comment=payload.message,
            metadata=payload.metadata,
        )

    async def post_comment(
        self,
        resource_url: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Post a comment to a GitHub issue or PR"""
        if not self._token:
            logger.warning("[GitHubNotifier] No token configured")
            return False

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    resource_url,
                    headers=headers,
                    json={"body": comment},
                ) as response:
                    if response.status in (200, 201):
                        logger.info(
                            "[GitHubNotifier] Comment posted successfully to %s",
                            resource_url,
                        )
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            "[GitHubNotifier] Failed to post comment: %s - %s",
                            response.status,
                            error_text,
                        )
                        return False

        except ImportError:
            logger.warning("[GitHubNotifier] aiohttp not available, notification skipped")
            return False  # Return False when aiohttp is not available
        except Exception as e:
            logger.error("[GitHubNotifier] Error posting comment: %s", e)
            return False


class JiraNotifier(BaseNotifier):
    """
    Notifier for Jira - posts comments to issues and updates status.
    """

    def __init__(
        self,
        jira_url: Optional[str] = None,
        jira_email: Optional[str] = None,
        jira_api_token: Optional[str] = None,
    ):
        """
        Initialize Jira notifier.

        Args:
            jira_url: Jira instance URL
            jira_email: Jira user email
            jira_api_token: Jira API token
        """
        self._jira_url = jira_url
        self._email = jira_email
        self._token = jira_api_token
        logger.info("[JiraNotifier] Initialized")

    @property
    def source(self) -> WebhookSource:
        return WebhookSource.JIRA

    async def send_notification(
        self,
        payload: NotificationPayload,
    ) -> bool:
        """Send notification to Jira (post comment)"""
        if not self._jira_url or not self._token:
            logger.warning("[JiraNotifier] Not configured, skipping notification")
            payload.status = NotificationStatus.SKIPPED
            payload.error = "Jira not configured"
            return False

        issue_key = payload.metadata.get("issue_key")
        if not issue_key:
            logger.warning("[JiraNotifier] Missing issue_key in metadata")
            payload.status = NotificationStatus.FAILED
            payload.error = "Missing issue_key"
            return False

        return await self.post_comment(
            resource_url=f"{self._jira_url}/rest/api/3/issue/{issue_key}/comment",
            comment=payload.message,
            metadata=payload.metadata,
        )

    async def post_comment(
        self,
        resource_url: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Post a comment to a Jira issue"""
        if not self._jira_url or not self._token:
            logger.warning("[JiraNotifier] Not configured")
            return False

        try:
            import aiohttp
            import base64

            # Jira uses Basic auth with email:token
            auth_string = f"{self._email}:{self._token}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()

            headers = {
                "Authorization": f"Basic {auth_bytes}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Jira API v3 uses Atlassian Document Format
            body = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment,
                                }
                            ],
                        }
                    ],
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    resource_url,
                    headers=headers,
                    json=body,
                ) as response:
                    if response.status in (200, 201):
                        logger.info(
                            "[JiraNotifier] Comment posted successfully to %s",
                            resource_url,
                        )
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            "[JiraNotifier] Failed to post comment: %s - %s",
                            response.status,
                            error_text,
                        )
                        return False

        except ImportError:
            logger.warning("[JiraNotifier] aiohttp not available, notification skipped")
            return False  # Return False when aiohttp is not available
        except Exception as e:
            logger.error("[JiraNotifier] Error posting comment: %s", e)
            return False


class SlackNotifier(BaseNotifier):
    """
    Notifier for Slack - posts messages to channels and threads.
    """

    def __init__(
        self,
        slack_bot_token: Optional[str] = None,
        default_channel: Optional[str] = None,
    ):
        """
        Initialize Slack notifier.

        Args:
            slack_bot_token: Slack Bot OAuth token
            default_channel: Default channel to post to
        """
        self._token = slack_bot_token
        self._default_channel = default_channel
        logger.info("[SlackNotifier] Initialized")

    @property
    def source(self) -> WebhookSource:
        return WebhookSource.SLACK

    async def send_notification(
        self,
        payload: NotificationPayload,
    ) -> bool:
        """Send notification to Slack"""
        if not self._token:
            logger.warning("[SlackNotifier] No token configured, skipping notification")
            payload.status = NotificationStatus.SKIPPED
            payload.error = "No Slack token configured"
            return False

        channel = payload.metadata.get("channel") or self._default_channel
        thread_ts = payload.metadata.get("thread_ts")

        if not channel:
            logger.warning("[SlackNotifier] No channel specified")
            payload.status = NotificationStatus.FAILED
            payload.error = "No channel specified"
            return False

        return await self.post_comment(
            resource_url="https://slack.com/api/chat.postMessage",
            comment=payload.message,
            metadata={"channel": channel, "thread_ts": thread_ts},
        )

    async def post_comment(
        self,
        resource_url: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Post a message to Slack"""
        if not self._token:
            logger.warning("[SlackNotifier] Not configured")
            return False

        metadata = metadata or {}
        channel = metadata.get("channel")
        thread_ts = metadata.get("thread_ts")

        if not channel:
            logger.warning("[SlackNotifier] No channel specified")
            return False

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }

            body: Dict[str, Any] = {
                "channel": channel,
                "text": comment,
            }

            if thread_ts:
                body["thread_ts"] = thread_ts

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    resource_url,
                    headers=headers,
                    json=body,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info(
                                "[SlackNotifier] Message posted successfully to %s",
                                channel,
                            )
                            return True
                        else:
                            logger.error(
                                "[SlackNotifier] Slack API error: %s",
                                result.get("error"),
                            )
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(
                            "[SlackNotifier] Failed to post message: %s - %s",
                            response.status,
                            error_text,
                        )
                        return False

        except ImportError:
            logger.warning("[SlackNotifier] aiohttp not available, notification skipped")
            return False  # Return False when aiohttp is not available
        except Exception as e:
            logger.error("[SlackNotifier] Error posting message: %s", e)
            return False


# Default maximum notification history size to prevent memory leaks
DEFAULT_MAX_HISTORY_SIZE = 1000


class OutboundNotifier:
    """
    Central service for sending notifications to external services.

    This service:
    1. Routes notifications to appropriate service-specific notifiers
    2. Manages notification queue and retry logic
    3. Provides callbacks for notification status updates
    4. Supports feature flags for each service
    """

    @classmethod
    def from_settings(cls) -> "OutboundNotifier":
        """
        Factory method to create OutboundNotifier from settings.

        Reads feature flags from common.config.settings:
        - ENABLE_GITHUB_NOTIFICATIONS
        - ENABLE_JIRA_NOTIFICATIONS
        - ENABLE_SLACK_NOTIFICATIONS

        Returns:
            OutboundNotifier instance configured from settings
        """
        try:
            from common.config.settings import settings

            enable_github = getattr(settings, 'enable_github_notifications', False)
            enable_jira = getattr(settings, 'enable_jira_notifications', False)
            enable_slack = getattr(settings, 'enable_slack_notifications', False)

            # Get tokens from settings if available
            github_token = getattr(settings, 'github_token', None)
            slack_bot_token = getattr(settings, 'slack_bot_token', None)

            # Create notifiers if tokens are available
            github_notifier = GitHubNotifier(github_token=github_token) if github_token else None
            slack_notifier = SlackNotifier(slack_bot_token=slack_bot_token) if slack_bot_token else None

            # Jira requires multiple settings
            jira_url = getattr(settings, 'jira_url', None)
            jira_email = getattr(settings, 'jira_email', None)
            jira_api_token = getattr(settings, 'jira_api_token', None)
            jira_notifier = None
            if jira_url and jira_email and jira_api_token:
                jira_notifier = JiraNotifier(
                    jira_url=jira_url,
                    jira_email=jira_email,
                    jira_api_token=jira_api_token,
                )

            logger.info(
                "[OutboundNotifier.from_settings] Created with enable_github=%s, "
                "enable_jira=%s, enable_slack=%s",
                enable_github,
                enable_jira,
                enable_slack,
            )

            return cls(
                github_notifier=github_notifier,
                jira_notifier=jira_notifier,
                slack_notifier=slack_notifier,
                enable_github=enable_github,
                enable_jira=enable_jira,
                enable_slack=enable_slack,
            )

        except ImportError:
            logger.warning(
                "[OutboundNotifier.from_settings] Could not import settings, "
                "using defaults (all disabled)"
            )
            return cls(
                enable_github=False,
                enable_jira=False,
                enable_slack=False,
            )

    def __init__(
        self,
        github_notifier: Optional[GitHubNotifier] = None,
        jira_notifier: Optional[JiraNotifier] = None,
        slack_notifier: Optional[SlackNotifier] = None,
        enable_github: bool = True,
        enable_jira: bool = True,
        enable_slack: bool = True,
        max_history_size: int = DEFAULT_MAX_HISTORY_SIZE,
        # Issue #2152: Retry configuration
        enable_retry: bool = True,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        retry_backoff_factor: float = 2.0,
        max_retry_delay: float = 30.0,
        # Issue #2153: Rate limiting configuration
        enable_rate_limiting: bool = True,
        rate_limits: Optional[Dict[str, int]] = None,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize the OutboundNotifier.

        Args:
            github_notifier: GitHubNotifier instance
            jira_notifier: JiraNotifier instance
            slack_notifier: SlackNotifier instance
            enable_github: Enable GitHub notifications
            enable_jira: Enable Jira notifications
            enable_slack: Enable Slack notifications
            max_history_size: Maximum number of notifications to keep in history
                              (default: 1000, set to 0 for unlimited)
            enable_retry: Enable retry with exponential backoff (Issue #2152)
            max_retries: Maximum number of retry attempts (default: 3)
            initial_retry_delay: Initial delay in seconds (default: 1.0)
            retry_backoff_factor: Multiplier for delay between retries (default: 2.0)
            max_retry_delay: Maximum delay between retries (default: 30.0)
            enable_rate_limiting: Enable rate limiting (Issue #2153)
            rate_limits: Per-source rate limits (requests per minute)
            redis_url: Redis URL for rate limiting (optional)
        """
        self._notifiers: Dict[WebhookSource, BaseNotifier] = {}
        self._enabled: Dict[WebhookSource, bool] = {
            WebhookSource.GITHUB: enable_github,
            WebhookSource.JIRA: enable_jira,
            WebhookSource.SLACK: enable_slack,
        }

        if github_notifier:
            self._notifiers[WebhookSource.GITHUB] = github_notifier
        if jira_notifier:
            self._notifiers[WebhookSource.JIRA] = jira_notifier
        if slack_notifier:
            self._notifiers[WebhookSource.SLACK] = slack_notifier

        # Notification history with size limit to prevent memory leaks
        self._notifications: Dict[str, NotificationPayload] = {}
        self._max_history_size = max_history_size

        # Issue #2152: Retry configuration
        self._enable_retry = enable_retry and _RETRY_AVAILABLE
        self._max_retries = max_retries
        self._initial_retry_delay = initial_retry_delay
        self._retry_backoff_factor = retry_backoff_factor
        self._max_retry_delay = max_retry_delay

        # Issue #2153: Rate limiting configuration
        self._enable_rate_limiting = enable_rate_limiting and _RATE_LIMIT_AVAILABLE
        self._rate_limits = rate_limits or DEFAULT_NOTIFICATION_RATE_LIMITS
        self._redis_url = redis_url

        # Callbacks
        self.on_notification_sent: Optional[Callable[[NotificationPayload], None]] = None
        self.on_notification_failed: Optional[Callable[[NotificationPayload, str], None]] = None
        # Issue #2152: Callback for retry events
        self.on_retry: Optional[Callable[[NotificationPayload, Exception, int], None]] = None
        # Issue #2153: Callback for rate limit events
        self.on_rate_limited: Optional[Callable[[WebhookSource, int], None]] = None

        logger.info(
            "[OutboundNotifier] Initialized with notifiers: %s, enabled: %s, "
            "retry=%s (max=%d), rate_limiting=%s",
            list(self._notifiers.keys()),
            {k.value: v for k, v in self._enabled.items()},
            self._enable_retry,
            self._max_retries if self._enable_retry else 0,
            self._enable_rate_limiting,
        )

    def is_enabled(self, source: WebhookSource) -> bool:
        """Check if notifications are enabled for a source"""
        return self._enabled.get(source, False)

    def set_enabled(self, source: WebhookSource, enabled: bool) -> None:
        """Enable or disable notifications for a source"""
        self._enabled[source] = enabled
        logger.info(
            "[OutboundNotifier] %s notifications %s",
            source.value,
            "enabled" if enabled else "disabled",
        )

    def get_notifier(self, source: WebhookSource) -> Optional[BaseNotifier]:
        """Get the notifier for a specific source"""
        return self._notifiers.get(source)

    async def notify_task_started(
        self,
        source: WebhookSource,
        task_id: str,
        goal_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationPayload]:
        """
        Send a notification that a task has started.

        Args:
            source: Webhook source to notify
            task_id: Task ID
            goal_text: Task goal text
            metadata: Additional metadata (repo, issue_number, etc.)

        Returns:
            NotificationPayload if sent, None otherwise
        """
        message = f"Task started: {goal_text[:100]}{'...' if len(goal_text) > 100 else ''}\n\nTask ID: {task_id}"

        return await self._send_notification(
            source=source,
            notification_type=NotificationType.TASK_STARTED,
            message=message,
            metadata=metadata or {},
        )

    async def notify_task_completed(
        self,
        source: WebhookSource,
        task_id: str,
        goal_text: str,
        result: Optional[Dict[str, Any]] = None,
        pr_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationPayload]:
        """
        Send a notification that a task has completed.

        Args:
            source: Webhook source to notify
            task_id: Task ID
            goal_text: Task goal text
            result: Task result
            pr_url: URL of created PR (if any)
            metadata: Additional metadata

        Returns:
            NotificationPayload if sent, None otherwise
        """
        message = f"Task completed: {goal_text[:100]}{'...' if len(goal_text) > 100 else ''}\n\nTask ID: {task_id}"

        if pr_url:
            message += f"\n\nPR: {pr_url}"

        return await self._send_notification(
            source=source,
            notification_type=NotificationType.TASK_COMPLETED,
            message=message,
            metadata=metadata or {},
        )

    async def notify_task_failed(
        self,
        source: WebhookSource,
        task_id: str,
        goal_text: str,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationPayload]:
        """
        Send a notification that a task has failed.

        Args:
            source: Webhook source to notify
            task_id: Task ID
            goal_text: Task goal text
            error: Error message
            metadata: Additional metadata

        Returns:
            NotificationPayload if sent, None otherwise
        """
        message = f"Task failed: {goal_text[:100]}{'...' if len(goal_text) > 100 else ''}\n\nTask ID: {task_id}\nError: {error}"

        return await self._send_notification(
            source=source,
            notification_type=NotificationType.TASK_FAILED,
            message=message,
            metadata=metadata or {},
        )

    async def notify_approval_required(
        self,
        source: WebhookSource,
        task_id: str,
        goal_text: str,
        approval_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[NotificationPayload]:
        """
        Send a notification that a task requires approval.

        Args:
            source: Webhook source to notify
            task_id: Task ID
            goal_text: Task goal text
            approval_url: URL to approve the task
            metadata: Additional metadata

        Returns:
            NotificationPayload if sent, None otherwise
        """
        message = f"Approval required for task: {goal_text[:100]}{'...' if len(goal_text) > 100 else ''}\n\nTask ID: {task_id}"

        if approval_url:
            message += f"\n\nApprove: {approval_url}"

        return await self._send_notification(
            source=source,
            notification_type=NotificationType.APPROVAL_REQUIRED,
            message=message,
            metadata=metadata or {},
        )

    async def _send_notification(
        self,
        source: WebhookSource,
        notification_type: NotificationType,
        message: str,
        metadata: Dict[str, Any],
    ) -> Optional[NotificationPayload]:
        """
        Internal method to send a notification.

        Issue #2152: Implements retry with exponential backoff.
        Issue #2153: Implements rate limiting to avoid triggering API limits.

        Args:
            source: Webhook source to notify
            notification_type: Type of notification
            message: Notification message
            metadata: Additional metadata

        Returns:
            NotificationPayload if sent, None otherwise
        """
        # Check if notifications are enabled for this source
        if not self.is_enabled(source):
            logger.debug(
                "[OutboundNotifier] Notifications disabled for %s",
                source.value,
            )
            return None

        # Get the notifier
        notifier = self.get_notifier(source)
        if not notifier:
            logger.debug(
                "[OutboundNotifier] No notifier configured for %s",
                source.value,
            )
            return None

        # Issue #2153: Check rate limit before sending
        if self._enable_rate_limiting:
            rate_limit = self._rate_limits.get(source.value, 30)
            allowed, current_count = check_notification_rate_limit(
                source=source.value,
                max_per_minute=rate_limit,
                redis_url=self._redis_url,
            )
            if not allowed:
                logger.warning(
                    "[OutboundNotifier] Rate limited for %s: %d/%d requests this minute",
                    source.value,
                    current_count,
                    rate_limit,
                )
                if self.on_rate_limited:
                    self.on_rate_limited(source, current_count)
                return None

        # Create notification payload
        import uuid
        notification_id = f"notif-{uuid.uuid4().hex[:8]}"

        payload = NotificationPayload(
            notification_id=notification_id,
            notification_type=notification_type,
            source=source,
            target_url=metadata.get("url", ""),
            message=message,
            metadata=metadata,
        )

        # Store in history
        self._notifications[notification_id] = payload

        # Prune history if it exceeds max size (P2: avoid memory leak)
        self._prune_history()

        # Issue #2152: Define retry callback
        def on_retry_callback(exc: Exception, attempt: int, delay: float) -> None:
            logger.warning(
                "[OutboundNotifier] Retry %d for notification %s: %s (delay: %.1fs)",
                attempt,
                notification_id,
                str(exc),
                delay,
            )
            if self.on_retry:
                self.on_retry(payload, exc, attempt)

        # Send the notification with retry logic
        try:
            if self._enable_retry:
                # Issue #2152: Use async retry with exponential backoff
                success = await async_retry_with_backoff(
                    operation=lambda: notifier.send_notification(payload),
                    max_retries=self._max_retries,
                    initial_delay=self._initial_retry_delay,
                    backoff_factor=self._retry_backoff_factor,
                    max_delay=self._max_retry_delay,
                    exceptions=(Exception,),
                    operation_name=f"notification_{source.value}",
                    on_retry=on_retry_callback,
                )
            else:
                # No retry, send directly
                success = await notifier.send_notification(payload)

            if success:
                payload.status = NotificationStatus.SENT
                payload.sent_at = datetime.now()
                logger.info(
                    "[OutboundNotifier] Notification sent: id=%s, type=%s, source=%s",
                    notification_id,
                    notification_type.value,
                    source.value,
                )

                if self.on_notification_sent:
                    self.on_notification_sent(payload)
            else:
                payload.status = NotificationStatus.FAILED
                logger.warning(
                    "[OutboundNotifier] Notification failed: id=%s",
                    notification_id,
                )

                if self.on_notification_failed:
                    self.on_notification_failed(payload, payload.error or "Unknown error")

        except Exception as e:
            payload.status = NotificationStatus.FAILED
            payload.error = str(e)
            logger.error(
                "[OutboundNotifier] Error sending notification after retries: %s",
                e,
                exc_info=True,
            )

            if self.on_notification_failed:
                self.on_notification_failed(payload, str(e))

        return payload

    def _prune_history(self) -> int:
        """
        Prune notification history if it exceeds max size.

        Removes oldest notifications (by created_at) to stay within limit.

        Returns:
            Number of notifications pruned
        """
        if self._max_history_size <= 0:
            return 0  # Unlimited history

        current_size = len(self._notifications)
        if current_size <= self._max_history_size:
            return 0

        # Sort by created_at and remove oldest
        sorted_notifications = sorted(
            self._notifications.items(),
            key=lambda x: x[1].created_at,
        )

        # Calculate how many to remove
        to_remove = current_size - self._max_history_size

        # Remove oldest notifications
        for notification_id, _ in sorted_notifications[:to_remove]:
            del self._notifications[notification_id]

        logger.debug(
            "[OutboundNotifier] Pruned %d notifications from history (max=%d)",
            to_remove,
            self._max_history_size,
        )

        return to_remove

    def get_notification(self, notification_id: str) -> Optional[NotificationPayload]:
        """Get a notification by ID"""
        return self._notifications.get(notification_id)

    def get_notifications_by_status(
        self,
        status: NotificationStatus,
    ) -> List[NotificationPayload]:
        """Get all notifications with a specific status"""
        return [n for n in self._notifications.values() if n.status == status]

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        status_counts = {}
        for status in NotificationStatus:
            status_counts[status.value] = len(self.get_notifications_by_status(status))

        source_counts: Dict[str, int] = {}
        for notification in self._notifications.values():
            source = notification.source.value
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "total_notifications": len(self._notifications),
            "status_counts": status_counts,
            "source_counts": source_counts,
            "enabled_sources": {k.value: v for k, v in self._enabled.items()},
        }

    def clear_history(self) -> int:
        """
        Clear notification history.

        Returns:
            Number of notifications cleared
        """
        count = len(self._notifications)
        self._notifications.clear()
        logger.info("[OutboundNotifier] Cleared %d notifications", count)
        return count
