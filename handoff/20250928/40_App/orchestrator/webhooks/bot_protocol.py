"""
Bot Protocol - Interface Definitions for Webhook Handlers

This module defines the Protocol interfaces and data types for webhook handlers,
ensuring consistent behavior across different external service integrations.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class WebhookSource(Enum):
    """Supported webhook sources"""
    GITHUB = "github"
    JIRA = "jira"
    SLACK = "slack"
    LINEAR = "linear"
    UNKNOWN = "unknown"


class WebhookEventType(Enum):
    """Normalized webhook event types"""
    # Issue/Task events
    ISSUE_CREATED = "issue_created"
    ISSUE_UPDATED = "issue_updated"
    ISSUE_CLOSED = "issue_closed"
    ISSUE_COMMENTED = "issue_commented"
    ISSUE_ASSIGNED = "issue_assigned"

    # Pull Request events
    PR_OPENED = "pr_opened"
    PR_UPDATED = "pr_updated"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    PR_REVIEWED = "pr_reviewed"
    PR_COMMENTED = "pr_commented"

    # Code events
    PUSH = "push"
    BRANCH_CREATED = "branch_created"
    BRANCH_DELETED = "branch_deleted"

    # CI events
    # Issue: #3366 - CI Failure Reflex Integration
    CI_CHECK_COMPLETED = "ci_check_completed"

    # Message events (Slack)
    MESSAGE_RECEIVED = "message_received"
    COMMAND_RECEIVED = "command_received"
    MENTION_RECEIVED = "mention_received"

    # Generic events
    UNKNOWN = "unknown"


@dataclass
class WebhookEvent:
    """
    Normalized webhook event representation.

    All platform-specific events are converted to this unified format
    for processing by the Meta Agent.
    """
    event_id: str
    source: WebhookSource
    event_type: WebhookEventType
    timestamp: datetime
    raw_payload: Dict[str, Any]

    # Common fields across all event types
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

    # Actor information
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_email: Optional[str] = None

    # Resource information
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_url: Optional[str] = None

    # Repository/Project context
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    project_key: Optional[str] = None

    # Additional metadata
    labels: List[str] = field(default_factory=list)
    assignees: List[str] = field(default_factory=list)
    priority: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "source": self.source.value,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actor_email": self.actor_email,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_url": self.resource_url,
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "project_key": self.project_key,
            "labels": self.labels,
            "assignees": self.assignees,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    def to_goal_text(self) -> str:
        """
        Convert event to natural language goal text for Meta Agent.

        This generates a goal description that can be parsed by GoalParser.
        """
        parts = []

        # Add source context
        source_name = self.source.value.capitalize()
        parts.append(f"[{source_name}]")

        # Add event type context
        event_desc = self.event_type.value.replace("_", " ").title()
        parts.append(event_desc)

        # Add title if available
        if self.title:
            parts.append(f": {self.title}")

        # Add description if available
        if self.description:
            # Truncate long descriptions
            desc = self.description[:500] + "..." if len(self.description) > 500 else self.description
            parts.append(f"\n\nDetails: {desc}")

        # Add repository context
        if self.repo_owner and self.repo_name:
            parts.append(f"\n\nRepository: {self.repo_owner}/{self.repo_name}")

        # Add URL for reference
        if self.url:
            parts.append(f"\nURL: {self.url}")

        return "".join(parts)


@dataclass
class WebhookResponse:
    """Response from webhook processing"""
    success: bool
    message: str
    event_id: Optional[str] = None
    task_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "success": self.success,
            "message": self.message,
            "event_id": self.event_id,
            "task_id": self.task_id,
            "errors": self.errors,
        }


@dataclass
class WebhookConfig:
    """Configuration for webhook handlers"""
    secret: Optional[str] = None
    verify_signature: bool = True
    allowed_events: List[str] = field(default_factory=list)
    ignored_events: List[str] = field(default_factory=list)
    auto_process: bool = True
    require_approval: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class WebhookHandler(Protocol):
    """
    Protocol for webhook handlers.

    All platform-specific handlers must implement this interface.
    """

    @property
    def source(self) -> WebhookSource:
        """Return the webhook source this handler supports"""
        ...

    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Validate the webhook signature.

        Args:
            payload: Raw request body
            signature: Signature from request headers
            secret: Webhook secret for validation
            headers: Optional request headers for handlers that need
                     additional header values (e.g., Slack needs timestamp)

        Returns:
            True if signature is valid, False otherwise
        """
        ...

    def parse_event(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEvent:
        """
        Parse raw webhook payload into normalized WebhookEvent.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEvent
        """
        ...

    def get_event_type(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEventType:
        """
        Determine the event type from headers and payload.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEventType
        """
        ...

    def should_process(
        self,
        event: WebhookEvent,
        config: WebhookConfig
    ) -> bool:
        """
        Determine if an event should be processed.

        Args:
            event: Normalized webhook event
            config: Handler configuration

        Returns:
            True if event should be processed, False otherwise
        """
        ...


class BaseWebhookHandler(ABC):
    """
    Abstract base class for webhook handlers.

    Provides common functionality and enforces the WebhookHandler protocol.
    """

    def __init__(self, config: Optional[WebhookConfig] = None):
        """
        Initialize the handler.

        Args:
            config: Optional handler configuration
        """
        self.config = config or WebhookConfig()
        logger.info(
            "[%s] Handler initialized with config: verify_signature=%s, auto_process=%s",
            self.__class__.__name__,
            self.config.verify_signature,
            self.config.auto_process,
        )

    @property
    @abstractmethod
    def source(self) -> WebhookSource:
        """Return the webhook source this handler supports"""
        pass

    @abstractmethod
    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Validate the webhook signature.

        Args:
            payload: Raw request body
            signature: Signature from request headers
            secret: Webhook secret for validation
            headers: Optional request headers for handlers that need
                     additional header values (e.g., Slack needs timestamp)
        """
        pass

    @abstractmethod
    def parse_event(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEvent:
        """Parse raw webhook payload into normalized WebhookEvent"""
        pass

    @abstractmethod
    def get_event_type(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEventType:
        """Determine the event type from headers and payload"""
        pass

    def should_process(
        self,
        event: WebhookEvent,
        config: Optional[WebhookConfig] = None
    ) -> bool:
        """
        Determine if an event should be processed.

        Default implementation checks allowed/ignored event lists.
        """
        cfg = config or self.config
        event_type = event.event_type.value

        # Check if event is in ignored list
        if cfg.ignored_events and event_type in cfg.ignored_events:
            logger.info(
                "[%s] Event %s ignored (in ignored_events list)",
                self.__class__.__name__,
                event_type,
            )
            return False

        # Check if event is in allowed list (if specified)
        if cfg.allowed_events and event_type not in cfg.allowed_events:
            logger.info(
                "[%s] Event %s not in allowed_events list",
                self.__class__.__name__,
                event_type,
            )
            return False

        return True

    def handle(
        self,
        headers: Dict[str, str],
        payload: bytes,
        parsed_payload: Dict[str, Any]
    ) -> WebhookResponse:
        """
        Main entry point for handling webhooks.

        Args:
            headers: Request headers
            payload: Raw request body (for signature validation)
            parsed_payload: Parsed JSON payload

        Returns:
            WebhookResponse with processing result
        """
        try:
            # Validate signature if configured
            if self.config.verify_signature and self.config.secret:
                signature = self._get_signature_header(headers)
                if not signature:
                    return WebhookResponse(
                        success=False,
                        message="Missing signature header",
                        errors=["Signature header not found"],
                    )

                if not self.validate_signature(payload, signature, self.config.secret, headers):
                    return WebhookResponse(
                        success=False,
                        message="Invalid signature",
                        errors=["Webhook signature validation failed"],
                    )

            # Parse the event
            event = self.parse_event(headers, parsed_payload)

            # Check if we should process this event
            if not self.should_process(event):
                return WebhookResponse(
                    success=True,
                    message="Event ignored",
                    event_id=event.event_id,
                )

            # Return success with event details
            return WebhookResponse(
                success=True,
                message="Event received",
                event_id=event.event_id,
            )

        except Exception as e:
            logger.exception(
                "[%s] Error handling webhook: %s",
                self.__class__.__name__,
                e,
            )
            return WebhookResponse(
                success=False,
                message="Error processing webhook",
                errors=[str(e)],
            )

    @abstractmethod
    def _get_signature_header(self, headers: Dict[str, str]) -> Optional[str]:
        """
        Get the signature header for this webhook source.

        Must be implemented by subclasses to specify the correct header name.
        This is marked as abstract to enforce implementation in all handlers
        and prevent silent failures in signature validation.
        """
        pass
