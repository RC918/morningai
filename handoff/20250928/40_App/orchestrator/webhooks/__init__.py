"""
Webhooks Module - External Tool Integration for Meta Agent

This module provides webhook handlers for integrating external tools
(GitHub, Jira, Slack) with the Meta Agent autonomous execution system.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Architecture:
    External Service → Webhook Route → Handler → Normalizer → Meta Agent

    1. Webhook routes receive events from external services
    2. Platform-specific handlers validate and parse events
    3. Event normalizer converts to unified WebhookEvent format
    4. Meta Agent processes events through GoalParser → TaskPlanner → Executor
"""

from .bot_protocol import (
    WebhookHandler,
    WebhookEvent,
    WebhookEventType,
    WebhookSource,
    WebhookResponse,
    WebhookConfig,
)
from .normalizer import EventNormalizer, NormalizedTask
from .task_intake import TaskIntakeService, IntakeTask, IntakeTaskStatus
from .outbound_notifier import (
    OutboundNotifier,
    NotificationPayload,
    NotificationStatus,
    NotificationType,
    GitHubNotifier,
    JiraNotifier,
    SlackNotifier,
)
from .handlers.github_handler import GitHubWebhookHandler
from .handlers.jira_handler import JiraWebhookHandler
from .handlers.linear_handler import LinearWebhookHandler
from .handlers.slack_handler import SlackWebhookHandler

__all__ = [
    # Protocols and Types
    "WebhookHandler",
    "WebhookEvent",
    "WebhookEventType",
    "WebhookSource",
    "WebhookResponse",
    "WebhookConfig",
    # Normalizer
    "EventNormalizer",
    "NormalizedTask",
    # Task Intake
    "TaskIntakeService",
    "IntakeTask",
    "IntakeTaskStatus",
    # Outbound Notifier
    "OutboundNotifier",
    "NotificationPayload",
    "NotificationStatus",
    "NotificationType",
    "GitHubNotifier",
    "JiraNotifier",
    "SlackNotifier",
    # Handlers
    "GitHubWebhookHandler",
    "JiraWebhookHandler",
    "LinearWebhookHandler",
    "SlackWebhookHandler",
]
