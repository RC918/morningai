"""
Jira Webhook Handler - Process Jira Events

This module handles Jira webhook events including:
- Issue events (created, updated, deleted)
- Comment events
- Sprint events
- Project events

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
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


# Jira event type to normalized event type mapping
JIRA_EVENT_MAP: Dict[str, WebhookEventType] = {
    "jira:issue_created": WebhookEventType.ISSUE_CREATED,
    "jira:issue_updated": WebhookEventType.ISSUE_UPDATED,
    "jira:issue_deleted": WebhookEventType.ISSUE_CLOSED,
    "comment_created": WebhookEventType.ISSUE_COMMENTED,
    "comment_updated": WebhookEventType.ISSUE_COMMENTED,
    "issuelink_created": WebhookEventType.ISSUE_UPDATED,
    "issuelink_deleted": WebhookEventType.ISSUE_UPDATED,
}

# Jira priority mapping
JIRA_PRIORITY_MAP: Dict[str, str] = {
    "Highest": "critical",
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "Lowest": "low",
}


class JiraWebhookHandler(BaseWebhookHandler):
    """
    Handler for Jira webhook events.

    Supports signature validation and converts Jira-specific events
    to normalized WebhookEvent format.
    """

    SIGNATURE_HEADER = "X-Hub-Signature"  # Jira Cloud uses this header
    EVENT_HEADER = "X-Atlassian-Webhook-Identifier"

    def __init__(self, config: Optional[WebhookConfig] = None):
        """Initialize Jira webhook handler"""
        super().__init__(config)
        logger.info("[JiraWebhookHandler] Initialized")

    @property
    def source(self) -> WebhookSource:
        """Return Jira as the webhook source"""
        return WebhookSource.JIRA

    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate Jira webhook signature.

        Jira Cloud webhooks can be configured with a secret for HMAC validation.

        Args:
            payload: Raw request body
            signature: Signature header value
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        if not signature:
            logger.warning("[JiraWebhookHandler] No signature provided")
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
            logger.warning("[JiraWebhookHandler] Signature validation failed")

        return is_valid

    def get_event_type(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEventType:
        """
        Determine the normalized event type from Jira webhook.

        Args:
            headers: Request headers
            payload: Parsed JSON payload (contains webhookEvent)

        Returns:
            Normalized WebhookEventType
        """
        # Get Jira event type from payload
        jira_event = payload.get("webhookEvent", "")

        # Look up in event map
        event_type = JIRA_EVENT_MAP.get(jira_event, WebhookEventType.UNKNOWN)

        # Handle status transitions
        if jira_event == "jira:issue_updated":
            changelog = payload.get("changelog", {})
            items = changelog.get("items", [])
            for item in items:
                if item.get("field") == "status":
                    to_status = item.get("toString", "").lower()
                    if to_status in ("done", "closed", "resolved"):
                        event_type = WebhookEventType.ISSUE_CLOSED

        logger.debug(
            "[JiraWebhookHandler] Event mapping: %s -> %s",
            jira_event,
            event_type.value,
        )

        return event_type

    def parse_event(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEvent:
        """
        Parse Jira webhook payload into normalized WebhookEvent.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEvent
        """
        # Get event metadata
        event_id = headers.get(self.EVENT_HEADER, str(uuid.uuid4()))
        event_type = self.get_event_type(headers, payload)
        jira_event = payload.get("webhookEvent", "")

        # Extract issue information
        issue = payload.get("issue", {})
        fields = issue.get("fields", {})

        # Extract project information
        project = fields.get("project", {})
        project_key = project.get("key")
        project_name = project.get("name")

        # Extract actor information
        user = payload.get("user", {})
        actor_id = user.get("accountId", "")
        actor_name = user.get("displayName", "")
        actor_email = user.get("emailAddress", "")

        # Extract issue details
        title = fields.get("summary")
        description = fields.get("description")

        # Handle Atlassian Document Format (ADF) description
        if isinstance(description, dict):
            description = self._extract_text_from_adf(description)

        issue_key = issue.get("key", "")
        issue_id = issue.get("id", "")

        # Build issue URL
        base_url = payload.get("baseUrl", "")
        url = f"{base_url}/browse/{issue_key}" if base_url and issue_key else None

        # Extract labels and assignees
        labels = [label for label in fields.get("labels", [])]
        assignee = fields.get("assignee", {})
        assignees = [assignee.get("displayName")] if assignee else []

        # Extract priority
        priority_obj = fields.get("priority", {})
        priority_name = priority_obj.get("name", "")
        priority = JIRA_PRIORITY_MAP.get(priority_name, "medium")

        # Handle comments
        if "comment" in payload:
            comment = payload.get("comment", {})
            description = comment.get("body")
            if isinstance(description, dict):
                description = self._extract_text_from_adf(description)

        # Create normalized event
        event = WebhookEvent(
            event_id=event_id,
            source=WebhookSource.JIRA,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            raw_payload=payload,
            title=title,
            description=description,
            url=url,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_email=actor_email,
            resource_id=issue_key,
            resource_type="issue",
            resource_url=url,
            project_key=project_key,
            labels=labels,
            assignees=assignees,
            priority=priority,
            metadata={
                "jira_event": jira_event,
                "issue_id": issue_id,
                "issue_type": fields.get("issuetype", {}).get("name"),
                "status": fields.get("status", {}).get("name"),
                "project_name": project_name,
            },
        )

        logger.info(
            "[JiraWebhookHandler] Parsed event: id=%s, type=%s, issue=%s",
            event_id,
            event_type.value,
            issue_key,
        )

        return event

    def _extract_text_from_adf(self, adf: Dict[str, Any]) -> str:
        """
        Extract plain text from Atlassian Document Format (ADF).

        ADF is a JSON-based document format used by Jira Cloud.

        Args:
            adf: ADF document

        Returns:
            Plain text content
        """
        if not isinstance(adf, dict):
            return str(adf)

        content = adf.get("content", [])
        text_parts = []

        for block in content:
            block_type = block.get("type", "")

            if block_type == "paragraph":
                para_content = block.get("content", [])
                for item in para_content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

            elif block_type == "bulletList":
                items = block.get("content", [])
                for item in items:
                    item_content = item.get("content", [])
                    for para in item_content:
                        if para.get("type") == "paragraph":
                            for text_item in para.get("content", []):
                                if text_item.get("type") == "text":
                                    text_parts.append(f"- {text_item.get('text', '')}")

            elif block_type == "codeBlock":
                code_content = block.get("content", [])
                for item in code_content:
                    if item.get("type") == "text":
                        text_parts.append(f"```\n{item.get('text', '')}\n```")

        return "\n".join(text_parts)

    def _get_signature_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Get the Jira signature header"""
        return headers.get(self.SIGNATURE_HEADER)

    def should_process(
        self,
        event: WebhookEvent,
        config: Optional[WebhookConfig] = None
    ) -> bool:
        """
        Determine if a Jira event should be processed.

        Additional Jira-specific filtering:
        - Filter by project key
        - Filter by issue type
        """
        # First check base class filtering
        if not super().should_process(event, config):
            return False

        cfg = config or self.config

        # Filter by project key if specified
        allowed_projects = cfg.metadata.get("allowed_projects", [])
        if allowed_projects and event.project_key not in allowed_projects:
            logger.info(
                "[JiraWebhookHandler] Ignoring event from project %s (not in allowed list)",
                event.project_key,
            )
            return False

        # Filter by issue type if specified
        allowed_issue_types = cfg.metadata.get("allowed_issue_types", [])
        issue_type = event.metadata.get("issue_type", "")
        if allowed_issue_types and issue_type not in allowed_issue_types:
            logger.info(
                "[JiraWebhookHandler] Ignoring event for issue type %s (not in allowed list)",
                issue_type,
            )
            return False

        return True
