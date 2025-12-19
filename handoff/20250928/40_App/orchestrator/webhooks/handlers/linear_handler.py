"""
Linear Webhook Handler - Process Linear Events

This module handles Linear webhook events including:
- Issue events (created, updated, removed)
- Comment events
- Project events
- Cycle events

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Linear Webhook Documentation:
https://developers.linear.app/docs/graphql/webhooks
"""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..bot_protocol import (
    BaseWebhookHandler,
    WebhookConfig,
    WebhookEvent,
    WebhookEventType,
    WebhookSource,
)

logger = logging.getLogger(__name__)


# Linear action to normalized event type mapping
LINEAR_EVENT_MAP: Dict[str, Dict[str, WebhookEventType]] = {
    "Issue": {
        "create": WebhookEventType.ISSUE_CREATED,
        "update": WebhookEventType.ISSUE_UPDATED,
        "remove": WebhookEventType.ISSUE_CLOSED,
    },
    "Comment": {
        "create": WebhookEventType.ISSUE_COMMENTED,
        "update": WebhookEventType.ISSUE_COMMENTED,
        "remove": WebhookEventType.ISSUE_UPDATED,
    },
    "IssueLabel": {
        "create": WebhookEventType.ISSUE_UPDATED,
        "remove": WebhookEventType.ISSUE_UPDATED,
    },
}

# Linear priority mapping (0 = No priority, 1 = Urgent, 2 = High, 3 = Medium, 4 = Low)
LINEAR_PRIORITY_MAP: Dict[int, str] = {
    0: "medium",  # No priority defaults to medium
    1: "critical",  # Urgent
    2: "high",
    3: "medium",
    4: "low",
}


class LinearWebhookHandler(BaseWebhookHandler):
    """
    Handler for Linear webhook events.

    Supports signature validation and converts Linear-specific events
    to normalized WebhookEvent format.
    """

    SIGNATURE_HEADER = "Linear-Signature"
    DELIVERY_HEADER = "Linear-Delivery"

    def __init__(self, config: Optional[WebhookConfig] = None):
        """Initialize Linear webhook handler"""
        super().__init__(config)
        logger.info("[LinearWebhookHandler] Initialized")

    @property
    def source(self) -> WebhookSource:
        """Return Linear as the webhook source"""
        return WebhookSource.LINEAR

    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Validate Linear webhook signature.

        Linear uses HMAC-SHA256 for webhook signature validation.

        Args:
            payload: Raw request body
            signature: Signature header value
            secret: Webhook secret
            headers: Optional request headers (not used by Linear handler)

        Returns:
            True if signature is valid
        """
        if not signature:
            logger.warning("[LinearWebhookHandler] No signature provided")
            return False

        # Compute HMAC-SHA256
        mac = hmac.new(
            secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256
        )
        computed_signature = mac.hexdigest()

        # Use constant-time comparison
        is_valid = hmac.compare_digest(computed_signature, signature)

        if not is_valid:
            logger.warning("[LinearWebhookHandler] Signature validation failed")

        return is_valid

    def get_event_type(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEventType:
        """
        Determine the normalized event type from Linear webhook.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEventType
        """
        # Get Linear event type and action
        event_type = payload.get("type", "")
        action = payload.get("action", "")

        # Look up in event map
        type_map = LINEAR_EVENT_MAP.get(event_type, {})
        normalized_type = type_map.get(action, WebhookEventType.UNKNOWN)

        # Handle state transitions for issues
        if event_type == "Issue" and action == "update":
            data = payload.get("data", {})
            state = data.get("state", {})
            state_type = state.get("type", "")

            # Check if issue was completed or cancelled
            if state_type in ("completed", "canceled"):
                normalized_type = WebhookEventType.ISSUE_CLOSED

        logger.debug(
            "[LinearWebhookHandler] Event mapping: %s/%s -> %s",
            event_type,
            action,
            normalized_type.value,
        )

        return normalized_type

    def parse_event(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEvent:
        """
        Parse Linear webhook payload into normalized WebhookEvent.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEvent
        """
        # Get event metadata
        # Fix: Phase B-B - Use lowercase key for consistent access
        event_id = headers.get(self.DELIVERY_HEADER.lower(), str(uuid.uuid4()))
        event_type = self.get_event_type(headers, payload)
        linear_type = payload.get("type", "")
        linear_action = payload.get("action", "")

        # Extract data based on event type
        data = payload.get("data", {})

        # Extract actor information
        actor = payload.get("actor", data.get("user", {}))
        actor_id = actor.get("id", "")
        actor_name = actor.get("name", "")
        actor_email = actor.get("email", "")

        # Extract issue/resource information
        title = data.get("title")
        description = data.get("description")
        identifier = data.get("identifier", "")  # e.g., "ENG-123"
        issue_id = data.get("id", "")

        # Build URL
        url = data.get("url")
        if not url and identifier:
            # Construct URL from organization and identifier
            org = payload.get("organizationId", "")
            if org:
                url = f"https://linear.app/{org}/issue/{identifier}"

        # Extract team/project information
        team = data.get("team", {})
        team_key = team.get("key", "")
        team_name = team.get("name", "")

        project = data.get("project", {})
        project_key = project.get("id", team_key)
        project_name = project.get("name", team_name)

        # Extract labels
        labels = []
        label_data = data.get("labels", [])
        for label in label_data:
            if isinstance(label, dict):
                labels.append(label.get("name", ""))
            elif isinstance(label, str):
                labels.append(label)

        # Extract assignee
        assignees = []
        assignee = data.get("assignee", {})
        if assignee and assignee.get("name"):
            assignees.append(assignee.get("name"))

        # Extract priority
        priority_value = data.get("priority", 0)
        priority = LINEAR_PRIORITY_MAP.get(priority_value, "medium")

        # Handle comment events
        if linear_type == "Comment":
            # For comments, the body is the description
            description = data.get("body", description)
            # Get the parent issue info
            issue = data.get("issue", {})
            if issue:
                title = issue.get("title", title)
                identifier = issue.get("identifier", identifier)
                url = issue.get("url", url)

        # Extract state information
        state = data.get("state", {})
        state_name = state.get("name", "")
        state_type = state.get("type", "")

        # Extract timestamp - prefer Linear's createdAt, fallback to now
        timestamp = datetime.now(timezone.utc)
        created_at = data.get("createdAt")
        if created_at:
            try:
                # Linear uses ISO 8601 format
                timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                logger.warning(
                    "[LinearWebhookHandler] Failed to parse createdAt: %s, using current time",
                    created_at,
                )

        # Create normalized event
        event = WebhookEvent(
            event_id=event_id,
            source=WebhookSource.LINEAR,
            event_type=event_type,
            timestamp=timestamp,
            raw_payload=payload,
            title=title,
            description=description,
            url=url,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_email=actor_email,
            resource_id=identifier or issue_id,
            resource_type="issue" if linear_type == "Issue" else linear_type.lower(),
            resource_url=url,
            project_key=project_key,
            labels=labels,
            assignees=assignees,
            priority=priority,
            metadata={
                "linear_type": linear_type,
                "linear_action": linear_action,
                "issue_id": issue_id,
                "identifier": identifier,
                "team_key": team_key,
                "team_name": team_name,
                "project_name": project_name,
                "state": state_name,
                "state_type": state_type,
                "priority_value": priority_value,
            },
        )

        logger.info(
            "[LinearWebhookHandler] Parsed event: id=%s, type=%s, issue=%s",
            event_id,
            event_type.value,
            identifier or issue_id,
        )

        return event

    def _get_signature_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Get the Linear signature header"""
        # Fix: Phase B-B - Use lowercase key for consistent access
        return headers.get(self.SIGNATURE_HEADER.lower())

    def should_process(
        self,
        event: WebhookEvent,
        config: Optional[WebhookConfig] = None
    ) -> bool:
        """
        Determine if a Linear event should be processed.

        Additional Linear-specific filtering:
        - Filter by team key
        - Filter by project
        - Filter by state type
        """
        # First check base class filtering
        if not super().should_process(event, config):
            return False

        cfg = config or self.config

        # Filter by team key if specified
        allowed_teams = cfg.metadata.get("allowed_teams", [])
        team_key = event.metadata.get("team_key", "")
        if allowed_teams and team_key not in allowed_teams:
            logger.info(
                "[LinearWebhookHandler] Ignoring event from team %s (not in allowed list)",
                team_key,
            )
            return False

        # Filter by project if specified
        allowed_projects = cfg.metadata.get("allowed_projects", [])
        project_name = event.metadata.get("project_name", "")
        if allowed_projects and project_name not in allowed_projects:
            logger.info(
                "[LinearWebhookHandler] Ignoring event from project %s (not in allowed list)",
                project_name,
            )
            return False

        # Filter by state type if specified (e.g., only process "started" issues)
        allowed_states = cfg.metadata.get("allowed_state_types", [])
        state_type = event.metadata.get("state_type", "")
        if allowed_states and state_type not in allowed_states:
            logger.info(
                "[LinearWebhookHandler] Ignoring event with state type %s (not in allowed list)",
                state_type,
            )
            return False

        return True
