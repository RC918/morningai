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
        secret: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Validate Jira webhook signature.

        Jira Cloud webhooks can be configured with a secret for HMAC validation.

        Args:
            payload: Raw request body
            signature: Signature header value
            secret: Webhook secret
            headers: Optional request headers (not used by Jira handler)

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
        # Fix: Phase B-B - Use lowercase key for consistent access
        event_id = headers.get(self.EVENT_HEADER.lower(), str(uuid.uuid4()))
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
        This method supports a comprehensive set of ADF node types including:
        - paragraph, text, heading
        - bulletList, orderedList, listItem
        - codeBlock, blockquote, panel
        - table, tableRow, tableCell, tableHeader
        - hardBreak, rule, mention, emoji

        Args:
            adf: ADF document

        Returns:
            Plain text content
        """
        if not isinstance(adf, dict):
            return str(adf)

        return self._extract_adf_node(adf)

    def _extract_adf_node(self, node: Dict[str, Any], depth: int = 0) -> str:
        """
        Recursively extract text from an ADF node.

        Args:
            node: ADF node
            depth: Current nesting depth for indentation

        Returns:
            Extracted text content
        """
        if not isinstance(node, dict):
            return str(node) if node else ""

        node_type = node.get("type", "")
        content = node.get("content", [])
        text_parts = []

        # Handle text node (leaf node)
        if node_type == "text":
            return node.get("text", "")

        # Handle hard break
        if node_type == "hardBreak":
            return "\n"

        # Handle horizontal rule
        if node_type == "rule":
            return "\n---\n"

        # Handle mention
        if node_type == "mention":
            attrs = node.get("attrs", {})
            return f"@{attrs.get('text', attrs.get('id', ''))}"

        # Handle emoji
        if node_type == "emoji":
            attrs = node.get("attrs", {})
            return attrs.get("text", attrs.get("shortName", ""))

        # Handle heading
        if node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            heading_text = " ".join(
                self._extract_adf_node(child, depth)
                for child in content
            )
            return f"{'#' * level} {heading_text}\n"

        # Handle paragraph
        if node_type == "paragraph":
            para_text = "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )
            return para_text + "\n" if para_text else ""

        # Handle bullet list
        if node_type == "bulletList":
            for item in content:
                item_text = self._extract_adf_node(item, depth)
                if item_text.strip():
                    text_parts.append(f"{'  ' * depth}- {item_text.strip()}")
            return "\n".join(text_parts)

        # Handle ordered list
        if node_type == "orderedList":
            for i, item in enumerate(content, 1):
                item_text = self._extract_adf_node(item, depth)
                if item_text.strip():
                    text_parts.append(f"{'  ' * depth}{i}. {item_text.strip()}")
            return "\n".join(text_parts)

        # Handle list item
        # List items are containers that concatenate their children's text.
        # Only increase depth for nested lists to handle indentation properly.
        if node_type == "listItem":
            parts = []
            for child in content:
                child_type = child.get("type") if isinstance(child, dict) else ""
                # Increase depth only for nested lists so they indent properly
                child_depth = depth + 1 if child_type in ("bulletList", "orderedList") else depth
                parts.append(self._extract_adf_node(child, child_depth))
            # Let children control their own newlines; just concatenate
            return "".join(parts)

        # Handle code block
        if node_type == "codeBlock":
            language = node.get("attrs", {}).get("language", "")
            code_text = "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )
            return f"```{language}\n{code_text}\n```\n"

        # Handle blockquote
        if node_type == "blockquote":
            quote_text = "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )
            # Prefix each line with >
            quoted_lines = [f"> {line}" for line in quote_text.split("\n") if line]
            return "\n".join(quoted_lines) + "\n"

        # Handle panel (info, note, warning, error, success)
        if node_type == "panel":
            panel_type = node.get("attrs", {}).get("panelType", "info")
            panel_text = "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )
            return f"[{panel_type.upper()}] {panel_text}"

        # Handle table
        if node_type == "table":
            rows = []
            for row in content:
                row_text = self._extract_adf_node(row, depth)
                if row_text:
                    rows.append(row_text)
            return "\n".join(rows) + "\n"

        # Handle table row
        if node_type == "tableRow":
            cells = []
            for cell in content:
                cell_text = self._extract_adf_node(cell, depth)
                cells.append(cell_text.strip() if cell_text else "")
            return "| " + " | ".join(cells) + " |"

        # Handle table cell and header
        if node_type in ("tableCell", "tableHeader"):
            return "".join(
                self._extract_adf_node(child, depth)
                for child in content
            ).strip()

        # Handle media (images, files)
        if node_type == "media":
            attrs = node.get("attrs", {})
            return f"[Media: {attrs.get('type', 'file')}]"

        # Handle media single (wrapper for media)
        if node_type == "mediaSingle":
            return "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )

        # Handle inline card (links)
        if node_type == "inlineCard":
            attrs = node.get("attrs", {})
            return attrs.get("url", "[Link]")

        # Handle doc (root node) and other container nodes
        if node_type in ("doc", "expand", "nestedExpand", "layoutSection", "layoutColumn"):
            return "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )

        # Default: recursively process children
        if content:
            return "".join(
                self._extract_adf_node(child, depth)
                for child in content
            )

        return ""

    def _get_signature_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Get the Jira signature header"""
        # Fix: Phase B-B - Use lowercase key for consistent access
        return headers.get(self.SIGNATURE_HEADER.lower())

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
