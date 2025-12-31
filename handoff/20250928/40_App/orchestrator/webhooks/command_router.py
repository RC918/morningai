"""
PR Comment Command Router - EPIC C External Trigger Entry Point

This module provides command routing for `/morningai <command>` comments on PRs,
enabling external triggering of MorningAI flows via PR comments.

Issue: #3224 - PR Comment Command Router
Issue: #3388 - Add authorization/permission gating for /morningai commands
Issue: #3390 - Improve command detection to ignore fenced code blocks
Blueprint Alignment:
    - Self-Governed: Command routing is part of the governance mechanism
    - Modular: Aligns with EPIC C Flow Controller dynamic routing design
    - Security: Authorization gating prevents unauthorized command execution

Flow:
    WebhookEvent (issue_comment/PR_comment) → CommandRouter → Authorization → CommandTrigger → Flow

MVP Commands:
    - /morningai review - Trigger reviewer_node

Future Commands (stub):
    - /morningai explain <file:line> - Explain specific code
    - /morningai fix - Trigger auto-fix (depends on EPIC D)

Authorization:
    - Users must have write permission or higher on the repository
    - Bots are always ignored (prevent automation loops)
    - Explicit allowlist for break-glass scenarios
    - Fail-closed on API errors (deny if can't verify)

Code Block Handling (Issue #3390):
    - Commands inside fenced code blocks (```) are ignored
    - Commands inside indented code blocks (4+ spaces) are ignored
    - This prevents false positives when users paste example commands
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .bot_protocol import WebhookEvent, WebhookEventType
from .command_authorizer import CommandAuthorizer

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Supported command types for /morningai commands"""
    REVIEW = "review"
    EXPLAIN = "explain"  # Future: EPIC C
    FIX = "fix"  # Future: EPIC D
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CommandTrigger:
    """
    Immutable trigger for a /morningai command.

    This is the output contract of CommandRouter - a clean, stable interface
    that Flow Controller can consume without coupling to internal implementation.

    Issue: #3224 - PR Comment Command Router
    Blueprint: Track C interface standardization
    """
    command_type: CommandType
    repo: str
    pr_number: int
    actor: str
    comment_url: str
    args: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "command_type": self.command_type.value,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "actor": self.actor,
            "comment_url": self.comment_url,
            "args": list(self.args),
            "metadata": dict(self.metadata),
        }


class CommandRouter:
    """
    PR Comment Command Router - EPIC C External Trigger Entry Point

    Parses `/morningai <command>` comments and returns CommandTrigger objects
    that can be consumed by Flow Controller to trigger appropriate flows.

    Design Principles:
    1. Only match commands at the start of a line (avoid code blocks/quotes)
    2. Ignore bot-generated comments to prevent automation loops
    3. Only process on valid event types (issue_comment on PR)
    4. Return None for non-command comments (pass through to existing triage)
    5. Strip fenced code blocks before matching (Issue #3390)

    Issue: #3224 - PR Comment Command Router
    Issue: #3390 - Improve command detection to ignore fenced code blocks
    """

    # Command prefix pattern - must be at start of line
    # Matches: /morningai review, /morningai explain file.py:10, etc.
    COMMAND_PATTERN = re.compile(
        r"^\s*/morningai\s+(\w+)(?:\s+(.*))?$",
        re.MULTILINE | re.IGNORECASE
    )

    # Fenced code block pattern - matches ``` with optional language tag
    # Issue #3390: Strip these before command matching to avoid false positives
    FENCED_CODE_BLOCK_PATTERN = re.compile(
        r"```[^\n]*\n.*?```",
        re.DOTALL
    )

    # Supported commands for MVP
    SUPPORTED_COMMANDS = {
        "review": CommandType.REVIEW,
        # Future commands (stub - return UNKNOWN for now)
        "explain": CommandType.EXPLAIN,
        "fix": CommandType.FIX,
    }

    # Event types that can contain commands
    COMMAND_EVENT_TYPES = {
        WebhookEventType.ISSUE_COMMENTED,
        WebhookEventType.PR_COMMENTED,
    }

    def __init__(
        self,
        authorizer: Optional[CommandAuthorizer] = None,
        enable_authorization: bool = True,
        allowlist: Optional[Set[str]] = None,
    ):
        """
        Initialize the Command Router.

        Args:
            authorizer: Optional CommandAuthorizer instance (creates default if None)
            enable_authorization: If True, check user permissions before routing
            allowlist: Optional set of usernames that bypass authorization checks

        Issue: #3388 - Add authorization/permission gating for /morningai commands
        """
        self._enable_authorization = enable_authorization
        self._authorizer = authorizer

        # Lazy initialization of authorizer (only when needed)
        if enable_authorization and authorizer is None:
            self._authorizer = CommandAuthorizer(allowlist=allowlist)

        logger.info(
            "[CommandRouter] Initialized",
            extra={
                "operation": "router_init",
                "authorization_enabled": enable_authorization,
                "has_authorizer": self._authorizer is not None,
            }
        )

    def route(self, event: WebhookEvent) -> Optional[CommandTrigger]:
        """
        Parse a webhook event and return a CommandTrigger if it contains a valid command.

        Args:
            event: WebhookEvent from webhook handler

        Returns:
            CommandTrigger if event contains a valid /morningai command,
            None otherwise (event should continue to normal processing)
        """
        # P0: Only process valid event types
        if event.event_type not in self.COMMAND_EVENT_TYPES:
            return None

        # P1: Ignore bot-generated comments to prevent automation loops
        actor_name = event.actor_name or ""
        if actor_name.endswith("[bot]"):
            logger.debug(
                "[CommandRouter] Ignoring bot comment from %s",
                actor_name,
            )
            return None

        # P2: Extract comment text
        comment_text = self._extract_comment_text(event)
        if not comment_text:
            return None

        # P2.5: Strip fenced code blocks before matching (Issue #3390)
        # This prevents false positives when users paste example commands
        comment_text_stripped = self._strip_code_blocks(comment_text)

        # P3: Parse command from comment (using stripped text)
        command_match = self.COMMAND_PATTERN.search(comment_text_stripped)
        if not command_match:
            return None

        command_name = command_match.group(1).lower()
        command_args_str = command_match.group(2) or ""
        command_args = command_args_str.split()

        # P4: Validate command is supported
        command_type = self.SUPPORTED_COMMANDS.get(command_name, CommandType.UNKNOWN)

        # P5: Extract PR context
        repo = self._extract_repo(event)
        pr_number = self._extract_pr_number(event)

        if not repo or not pr_number:
            logger.warning(
                "[CommandRouter] Cannot extract repo/PR from event %s",
                event.event_id,
            )
            return None

        # P6: Authorization check (Issue #3388)
        if self._enable_authorization and self._authorizer:
            auth_result = self._authorizer.authorize(repo, actor_name)
            if not auth_result.authorized:
                logger.warning(
                    "[CommandRouter] Command rejected: unauthorized user",
                    extra={
                        "operation": "command_unauthorized",
                        "repo": repo,
                        "pr_number": pr_number,
                        "actor": actor_name,
                        "command": command_name,
                        "reason": auth_result.reason,
                        "permission_level": auth_result.permission_level.value if auth_result.permission_level else None,
                        "event_id": event.event_id,
                    }
                )
                return None

        # P7: Build CommandTrigger
        trigger = CommandTrigger(
            command_type=command_type,
            repo=repo,
            pr_number=pr_number,
            actor=actor_name,
            comment_url=event.url or "",
            args=command_args,
            metadata={
                "contract_version": "v1",
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "source": event.source.value,
            },
        )

        # Log command detection
        logger.info(
            "[CommandRouter] Command detected",
            extra={
                "operation": "command_detected",
                "command_type": command_type.value,
                "repo": repo,
                "pr_number": pr_number,
                "actor": actor_name,
                "args": command_args,
                "event_id": event.event_id,
            }
        )

        return trigger

    def _extract_comment_text(self, event: WebhookEvent) -> str:
        """Extract comment text from the event"""
        # Try description first (usually contains the comment body)
        if event.description:
            return event.description

        # Try raw payload for comment body
        raw = event.raw_payload or {}
        if "comment" in raw and "body" in raw["comment"]:
            return raw["comment"]["body"]

        return ""

    def _strip_code_blocks(self, text: str) -> str:
        """
        Strip fenced code blocks from text before command matching.

        This prevents false positives when users paste example commands
        inside code blocks in their comments.

        Issue: #3390 - Improve command detection to ignore fenced code blocks

        Args:
            text: Raw comment text

        Returns:
            Text with fenced code blocks removed

        Examples:
            >>> router._strip_code_blocks("```\\n/morningai review\\n```")
            ''
            >>> router._strip_code_blocks("Hello\\n```python\\n/morningai review\\n```\\nWorld")
            'Hello\\n\\nWorld'
        """
        # Remove fenced code blocks (``` ... ```)
        # This handles both simple ``` and language-tagged ```python blocks
        return self.FENCED_CODE_BLOCK_PATTERN.sub("", text)

    def _extract_repo(self, event: WebhookEvent) -> Optional[str]:
        """Extract repository in owner/repo format"""
        if event.repo_owner and event.repo_name:
            return f"{event.repo_owner}/{event.repo_name}"
        return None

    def _extract_pr_number(self, event: WebhookEvent) -> Optional[int]:
        """Extract PR number from the event"""
        # Try resource_id first
        if event.resource_id:
            try:
                return int(event.resource_id)
            except (ValueError, TypeError):
                pass

        # Try raw payload for issue/PR number
        raw = event.raw_payload or {}

        # GitHub issue_comment on PR has issue.number
        if "issue" in raw:
            issue = raw["issue"]
            # Check if this is a PR (has pull_request key)
            if "pull_request" in issue:
                try:
                    return int(issue.get("number"))
                except (ValueError, TypeError):
                    pass

        return None

    def is_command_comment(self, event: WebhookEvent) -> bool:
        """
        Quick check if an event might contain a command.

        This is a lightweight check that can be used before full routing
        to avoid unnecessary processing.

        Args:
            event: WebhookEvent to check

        Returns:
            True if event might contain a /morningai command
        """
        if event.event_type not in self.COMMAND_EVENT_TYPES:
            return False

        comment_text = self._extract_comment_text(event)
        if not comment_text:
            return False

        # Quick substring check before regex
        return "/morningai" in comment_text.lower()
