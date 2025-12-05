"""
Event Normalizer - Unified Event Processing for Meta Agent

This module provides event normalization and processing logic that bridges
webhook events from external services to the Meta Agent execution system.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Flow:
    WebhookEvent → EventNormalizer → GoalParser → TaskPlanner → Executor
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .bot_protocol import (
    BaseWebhookHandler,
    WebhookConfig,
    WebhookEvent,
    WebhookEventType,
    WebhookResponse,
    WebhookSource,
)
from .handlers.github_handler import GitHubWebhookHandler
from .handlers.jira_handler import JiraWebhookHandler
from .handlers.linear_handler import LinearWebhookHandler
from .handlers.slack_handler import SlackWebhookHandler

logger = logging.getLogger(__name__)


@dataclass
class NormalizedTask:
    """
    A task extracted from a webhook event, ready for Meta Agent processing.

    This represents the bridge between external events and internal task execution.
    """
    task_id: str
    source_event: WebhookEvent
    goal_text: str
    priority: str
    requires_approval: bool
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "source_event_id": self.source_event.event_id,
            "source": self.source_event.source.value,
            "event_type": self.source_event.event_type.value,
            "goal_text": self.goal_text,
            "priority": self.priority,
            "requires_approval": self.requires_approval,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
        }


class EventNormalizer:
    """
    Normalizes webhook events from different sources into a unified format
    and prepares them for Meta Agent processing.

    This class:
    1. Routes events to appropriate handlers based on source
    2. Validates and normalizes event data
    3. Extracts actionable tasks from events
    4. Determines priority and approval requirements
    """

    # Event types that typically require human approval
    HIGH_RISK_EVENT_TYPES = {
        WebhookEventType.PR_MERGED,
        WebhookEventType.ISSUE_CLOSED,
        WebhookEventType.BRANCH_DELETED,
    }

    # Event types that are actionable (can trigger Meta Agent tasks)
    ACTIONABLE_EVENT_TYPES = {
        WebhookEventType.ISSUE_CREATED,
        WebhookEventType.ISSUE_COMMENTED,
        WebhookEventType.ISSUE_ASSIGNED,
        WebhookEventType.PR_OPENED,
        WebhookEventType.PR_REVIEWED,
        WebhookEventType.PR_COMMENTED,
        WebhookEventType.MENTION_RECEIVED,
        WebhookEventType.COMMAND_RECEIVED,
    }

    # Priority mapping based on labels
    PRIORITY_LABELS = {
        "critical": ["critical", "urgent", "p0", "blocker", "緊急"],
        "high": ["high", "important", "p1", "高優先"],
        "medium": ["medium", "normal", "p2", "中優先"],
        "low": ["low", "minor", "p3", "低優先"],
    }

    def __init__(
        self,
        github_config: Optional[WebhookConfig] = None,
        jira_config: Optional[WebhookConfig] = None,
        linear_config: Optional[WebhookConfig] = None,
        slack_config: Optional[WebhookConfig] = None,
    ):
        """
        Initialize the EventNormalizer with handler configurations.

        Args:
            github_config: Configuration for GitHub webhook handler
            jira_config: Configuration for Jira webhook handler
            linear_config: Configuration for Linear webhook handler
            slack_config: Configuration for Slack webhook handler
        """
        self.handlers: Dict[WebhookSource, BaseWebhookHandler] = {
            WebhookSource.GITHUB: GitHubWebhookHandler(github_config),
            WebhookSource.JIRA: JiraWebhookHandler(jira_config),
            WebhookSource.LINEAR: LinearWebhookHandler(linear_config),
            WebhookSource.SLACK: SlackWebhookHandler(slack_config),
        }

        logger.info(
            "[EventNormalizer] Initialized with handlers: %s",
            list(self.handlers.keys()),
        )

    def get_handler(self, source: WebhookSource) -> Optional[BaseWebhookHandler]:
        """
        Get the handler for a specific webhook source.

        Args:
            source: Webhook source

        Returns:
            Handler instance or None if not configured
        """
        return self.handlers.get(source)

    def process_webhook(
        self,
        source: WebhookSource,
        headers: Dict[str, str],
        payload: bytes,
        parsed_payload: Dict[str, Any],
    ) -> WebhookResponse:
        """
        Process a webhook request from any supported source.

        Args:
            source: Webhook source (github, jira, slack)
            headers: Request headers
            payload: Raw request body
            parsed_payload: Parsed JSON payload

        Returns:
            WebhookResponse with processing result
        """
        handler = self.get_handler(source)
        if not handler:
            logger.warning("[EventNormalizer] No handler for source: %s", source)
            return WebhookResponse(
                success=False,
                message=f"Unsupported webhook source: {source.value}",
                errors=[f"No handler configured for {source.value}"],
            )

        return handler.handle(headers, payload, parsed_payload)

    def parse_event(
        self,
        source: WebhookSource,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> Optional[WebhookEvent]:
        """
        Parse a webhook payload into a normalized WebhookEvent.

        Args:
            source: Webhook source
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEvent or None if parsing fails
        """
        handler = self.get_handler(source)
        if not handler:
            logger.warning("[EventNormalizer] No handler for source: %s", source)
            return None

        try:
            return handler.parse_event(headers, payload)
        except Exception as e:
            logger.exception(
                "[EventNormalizer] Failed to parse event from %s: %s",
                source.value,
                e,
            )
            return None

    def is_actionable(self, event: WebhookEvent) -> bool:
        """
        Determine if an event is actionable (should trigger Meta Agent).

        Args:
            event: Normalized webhook event

        Returns:
            True if event should trigger task creation
        """
        # Check if event type is in actionable list
        if event.event_type in self.ACTIONABLE_EVENT_TYPES:
            return True

        # Check for specific keywords in title/description
        text = f"{event.title or ''} {event.description or ''}".lower()
        action_keywords = [
            "fix", "implement", "add", "create", "update", "refactor",
            "修復", "實現", "新增", "建立", "更新", "重構",
            "@bot", "@agent", "@meta-agent",
        ]

        for keyword in action_keywords:
            if keyword in text:
                return True

        return False

    def extract_task(self, event: WebhookEvent) -> Optional[NormalizedTask]:
        """
        Extract an actionable task from a webhook event.

        Args:
            event: Normalized webhook event

        Returns:
            NormalizedTask ready for Meta Agent, or None if not actionable
        """
        if not self.is_actionable(event):
            logger.debug(
                "[EventNormalizer] Event %s is not actionable",
                event.event_id,
            )
            return None

        # Generate goal text from event
        goal_text = event.to_goal_text()

        # Determine priority
        priority = self._determine_priority(event)

        # Determine if approval is required
        requires_approval = self._requires_approval(event)

        # Build context for Meta Agent
        context = self._build_context(event)

        # Generate task ID
        import uuid
        task_id = f"webhook-{event.source.value}-{uuid.uuid4().hex[:8]}"

        task = NormalizedTask(
            task_id=task_id,
            source_event=event,
            goal_text=goal_text,
            priority=priority,
            requires_approval=requires_approval,
            context=context,
        )

        logger.info(
            "[EventNormalizer] Extracted task: id=%s, priority=%s, approval=%s",
            task_id,
            priority,
            requires_approval,
        )

        return task

    def _determine_priority(self, event: WebhookEvent) -> str:
        """
        Determine task priority from event labels and content.

        Args:
            event: Normalized webhook event

        Returns:
            Priority string (critical, high, medium, low)
        """
        # Check event priority field first
        if event.priority:
            return event.priority

        # Check labels
        labels_lower = [label.lower() for label in event.labels]
        for priority, keywords in self.PRIORITY_LABELS.items():
            for keyword in keywords:
                if keyword in labels_lower:
                    return priority

        # Check title/description for priority keywords
        text = f"{event.title or ''} {event.description or ''}".lower()
        for priority, keywords in self.PRIORITY_LABELS.items():
            for keyword in keywords:
                if keyword in text:
                    return priority

        # Default to medium
        return "medium"

    def _requires_approval(self, event: WebhookEvent) -> bool:
        """
        Determine if task requires human approval.

        Args:
            event: Normalized webhook event

        Returns:
            True if approval is required
        """
        # High-risk event types always require approval
        if event.event_type in self.HIGH_RISK_EVENT_TYPES:
            return True

        # Check for high-risk keywords
        text = f"{event.title or ''} {event.description or ''}".lower()
        high_risk_keywords = [
            "production", "deploy", "delete", "remove", "drop",
            "生產", "部署", "刪除", "移除",
            "security", "credential", "secret", "password",
            "安全", "憑證", "密碼",
        ]

        for keyword in high_risk_keywords:
            if keyword in text:
                return True

        return False

    def _build_context(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Build context dictionary for Meta Agent.

        Args:
            event: Normalized webhook event

        Returns:
            Context dictionary with relevant information
        """
        context = {
            "source": event.source.value,
            "event_type": event.event_type.value,
            "event_id": event.event_id,
            "url": event.url,
            "actor": event.actor_name,
        }

        # Add repository context
        if event.repo_owner and event.repo_name:
            context["repo"] = f"{event.repo_owner}/{event.repo_name}"

        # Add project context (for Jira)
        if event.project_key:
            context["project"] = event.project_key

        # Add resource context
        if event.resource_id:
            context["resource_id"] = event.resource_id
            context["resource_type"] = event.resource_type

        # Add labels and assignees
        if event.labels:
            context["labels"] = event.labels
        if event.assignees:
            context["assignees"] = event.assignees

        return context

    def batch_process(
        self,
        events: List[WebhookEvent],
    ) -> List[NormalizedTask]:
        """
        Process multiple events and extract actionable tasks.

        Args:
            events: List of normalized webhook events

        Returns:
            List of extracted tasks
        """
        tasks = []
        for event in events:
            task = self.extract_task(event)
            if task:
                tasks.append(task)

        logger.info(
            "[EventNormalizer] Batch processed %d events, extracted %d tasks",
            len(events),
            len(tasks),
        )

        return tasks
