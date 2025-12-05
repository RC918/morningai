"""
Slack Webhook Handler - Process Slack Events

This module handles Slack events including:
- Message events (new messages, edits)
- App mentions
- Slash commands
- Interactive components (buttons, modals)

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import hashlib
import hmac
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..bot_protocol import (
    BaseWebhookHandler,
    WebhookConfig,
    WebhookEvent,
    WebhookEventType,
    WebhookSource,
)

logger = logging.getLogger(__name__)


# Slack event type to normalized event type mapping
SLACK_EVENT_MAP: Dict[str, WebhookEventType] = {
    "message": WebhookEventType.MESSAGE_RECEIVED,
    "app_mention": WebhookEventType.MENTION_RECEIVED,
    "message.channels": WebhookEventType.MESSAGE_RECEIVED,
    "message.groups": WebhookEventType.MESSAGE_RECEIVED,
    "message.im": WebhookEventType.MESSAGE_RECEIVED,
    "message.mpim": WebhookEventType.MESSAGE_RECEIVED,
}


class SlackWebhookHandler(BaseWebhookHandler):
    """
    Handler for Slack webhook events.

    Supports Slack's signature validation using HMAC-SHA256 and converts
    Slack-specific events to normalized WebhookEvent format.

    Slack uses the Events API which sends events in a specific format:
    - URL verification challenges
    - Event callbacks with nested event data
    """

    SIGNATURE_HEADER = "X-Slack-Signature"
    TIMESTAMP_HEADER = "X-Slack-Request-Timestamp"
    SIGNATURE_VERSION = "v0"

    # Maximum age of request timestamp (5 minutes)
    MAX_TIMESTAMP_AGE = 300

    def __init__(self, config: Optional[WebhookConfig] = None):
        """Initialize Slack webhook handler"""
        super().__init__(config)
        logger.info("[SlackWebhookHandler] Initialized")

    @property
    def source(self) -> WebhookSource:
        """Return Slack as the webhook source"""
        return WebhookSource.SLACK

    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Validate Slack webhook signature using HMAC-SHA256.

        Slack's signature format: v0=<hex_digest>
        The signature is computed over: v0:<timestamp>:<body>

        Args:
            payload: Raw request body
            signature: X-Slack-Signature header value
            secret: Slack signing secret
            timestamp: X-Slack-Request-Timestamp header value

        Returns:
            True if signature is valid
        """
        if not signature or not signature.startswith(f"{self.SIGNATURE_VERSION}="):
            logger.warning("[SlackWebhookHandler] Invalid signature format")
            return False

        if not timestamp:
            logger.warning("[SlackWebhookHandler] Missing timestamp")
            return False

        # Check timestamp age to prevent replay attacks
        try:
            request_timestamp = int(timestamp)
            current_timestamp = int(time.time())
            if abs(current_timestamp - request_timestamp) > self.MAX_TIMESTAMP_AGE:
                logger.warning(
                    "[SlackWebhookHandler] Request timestamp too old: %d vs %d",
                    request_timestamp,
                    current_timestamp,
                )
                return False
        except ValueError:
            logger.warning("[SlackWebhookHandler] Invalid timestamp format")
            return False

        # Compute signature
        sig_basestring = f"{self.SIGNATURE_VERSION}:{timestamp}:{payload.decode('utf-8')}"
        mac = hmac.new(
            secret.encode("utf-8"),
            msg=sig_basestring.encode("utf-8"),
            digestmod=hashlib.sha256
        )
        computed_signature = f"{self.SIGNATURE_VERSION}={mac.hexdigest()}"

        # Use constant-time comparison
        is_valid = hmac.compare_digest(computed_signature, signature)

        if not is_valid:
            logger.warning("[SlackWebhookHandler] Signature validation failed")

        return is_valid

    def get_event_type(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEventType:
        """
        Determine the normalized event type from Slack webhook.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEventType
        """
        # Handle URL verification challenge
        if payload.get("type") == "url_verification":
            return WebhookEventType.UNKNOWN

        # Handle event callbacks
        if payload.get("type") == "event_callback":
            event = payload.get("event", {})
            event_type = event.get("type", "")

            # Check for slash commands
            if event_type == "message" and event.get("subtype") == "slash_command":
                return WebhookEventType.COMMAND_RECEIVED

            return SLACK_EVENT_MAP.get(event_type, WebhookEventType.UNKNOWN)

        # Handle slash commands (direct POST)
        if "command" in payload:
            return WebhookEventType.COMMAND_RECEIVED

        # Handle interactive components
        if payload.get("type") == "block_actions":
            return WebhookEventType.COMMAND_RECEIVED

        return WebhookEventType.UNKNOWN

    def parse_event(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEvent:
        """
        Parse Slack webhook payload into normalized WebhookEvent.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEvent
        """
        event_id = payload.get("event_id", str(uuid.uuid4()))
        event_type = self.get_event_type(headers, payload)

        # Handle URL verification (return early)
        if payload.get("type") == "url_verification":
            return WebhookEvent(
                event_id=event_id,
                source=WebhookSource.SLACK,
                event_type=WebhookEventType.UNKNOWN,
                timestamp=datetime.now(timezone.utc),
                raw_payload=payload,
                metadata={"challenge": payload.get("challenge")},
            )

        # Extract event data
        event_data = payload.get("event", {})
        if not event_data and "command" in payload:
            # Handle slash command format
            event_data = payload

        # Extract actor information
        actor_id = event_data.get("user", "")
        actor_name = ""  # Slack doesn't include username in events

        # Extract message content
        text = event_data.get("text", "")
        if "command" in payload:
            text = f"{payload.get('command')} {payload.get('text', '')}"

        # Extract channel information
        channel_id = event_data.get("channel", "")
        channel_type = event_data.get("channel_type", "")

        # Extract team/workspace information
        team_id = payload.get("team_id", "")

        # Extract timestamp
        event_ts = event_data.get("ts", "")
        try:
            if event_ts:
                ts_float = float(event_ts)
                timestamp = datetime.fromtimestamp(ts_float, tz=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)

        # Build message URL (if possible)
        url = None
        if channel_id and event_ts:
            # Slack message URLs use the format: slack://channel?team=T&id=C&message=ts
            url = f"slack://channel?team={team_id}&id={channel_id}&message={event_ts}"

        # Extract mentions
        mentions = self._extract_mentions(text)

        # Create normalized event
        event = WebhookEvent(
            event_id=event_id,
            source=WebhookSource.SLACK,
            event_type=event_type,
            timestamp=timestamp,
            raw_payload=payload,
            title=text[:100] if text else None,
            description=text,
            url=url,
            actor_id=actor_id,
            actor_name=actor_name,
            resource_id=event_ts,
            resource_type="message",
            metadata={
                "channel_id": channel_id,
                "channel_type": channel_type,
                "team_id": team_id,
                "thread_ts": event_data.get("thread_ts"),
                "mentions": mentions,
                "is_bot": event_data.get("bot_id") is not None,
            },
        )

        logger.info(
            "[SlackWebhookHandler] Parsed event: id=%s, type=%s, channel=%s",
            event_id,
            event_type.value,
            channel_id,
        )

        return event

    def _extract_mentions(self, text: str) -> List[str]:
        """
        Extract user mentions from Slack message text.

        Slack mentions are in format: <@U12345678>

        Args:
            text: Message text

        Returns:
            List of mentioned user IDs
        """
        import re
        mentions = re.findall(r"<@([A-Z0-9]+)>", text)
        return mentions

    def _get_signature_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Get the Slack signature header"""
        return headers.get(self.SIGNATURE_HEADER)

    def handle(
        self,
        headers: Dict[str, str],
        payload: bytes,
        parsed_payload: Dict[str, Any]
    ):
        """
        Handle Slack webhook with special handling for URL verification.

        Args:
            headers: Request headers
            payload: Raw request body
            parsed_payload: Parsed JSON payload

        Returns:
            WebhookResponse or challenge response for URL verification
        """
        # Handle URL verification challenge
        if parsed_payload.get("type") == "url_verification":
            challenge = parsed_payload.get("challenge", "")
            logger.info("[SlackWebhookHandler] Responding to URL verification challenge")
            return {"challenge": challenge}

        # Validate signature with timestamp
        if self.config.verify_signature and self.config.secret:
            signature = headers.get(self.SIGNATURE_HEADER)
            timestamp = headers.get(self.TIMESTAMP_HEADER)

            if not self.validate_signature(payload, signature, self.config.secret, timestamp):
                from ..bot_protocol import WebhookResponse
                return WebhookResponse(
                    success=False,
                    message="Invalid signature",
                    errors=["Webhook signature validation failed"],
                )

        # Use base class handling for the rest
        return super().handle(headers, payload, parsed_payload)

    def should_process(
        self,
        event: WebhookEvent,
        config: Optional[WebhookConfig] = None
    ) -> bool:
        """
        Determine if a Slack event should be processed.

        Additional Slack-specific filtering:
        - Ignore bot messages
        - Filter by channel
        - Require app mention
        """
        # First check base class filtering
        if not super().should_process(event, config):
            return False

        cfg = config or self.config

        # Ignore bot messages by default
        if event.metadata.get("is_bot"):
            logger.info("[SlackWebhookHandler] Ignoring bot message")
            return False

        # Filter by channel if specified
        allowed_channels = cfg.metadata.get("allowed_channels", [])
        channel_id = event.metadata.get("channel_id", "")
        if allowed_channels and channel_id not in allowed_channels:
            logger.info(
                "[SlackWebhookHandler] Ignoring message from channel %s (not in allowed list)",
                channel_id,
            )
            return False

        # Require mention if configured
        require_mention = cfg.metadata.get("require_mention", False)
        if require_mention and event.event_type != WebhookEventType.MENTION_RECEIVED:
            logger.info("[SlackWebhookHandler] Ignoring non-mention message")
            return False

        return True
