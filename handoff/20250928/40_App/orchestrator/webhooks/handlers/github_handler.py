"""
GitHub Webhook Handler - Process GitHub Events

This module handles GitHub webhook events including:
- Pull Request events (opened, closed, merged, reviewed)
- Issue events (opened, closed, commented)
- Push events
- Branch events

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


# AI Reviewer bot whitelist - these bots should NOT be filtered out
# Issue: #2209 - 修復 AI Reviewer 評論接收機制
# Issue: #2255 - Verified bot login names with documentation sources
#
# Verification sources:
# - GitHub Copilot: https://github.com/apps/github-copilot
# - Gemini Code Assist: https://github.com/apps/gemini-code-assist
# - CodeRabbit: https://github.com/apps/coderabbitai
# - Sourcery: https://github.com/apps/sourcery-ai
# - Devin: https://github.com/apps/devin-ai-integration
#
# Note: Bot login names follow the pattern "{app-slug}[bot]" where app-slug
# is the URL slug from the GitHub App's installation page.
AI_REVIEWER_BOTS: Dict[str, str] = {
    # GitHub Copilot - Official GitHub AI assistant
    # Source: https://github.com/apps/github-copilot
    "github-copilot[bot]": "copilot",
    # Legacy/alternative Copilot bot name (for backwards compatibility)
    "copilot[bot]": "copilot",

    # OpenAI Codex - ChatGPT code assistant integration
    # Note: These are hypothetical names based on common patterns
    # Actual bot names should be verified when integrations are available
    "openai-codex[bot]": "codex",
    "chatgpt-codex-connector[bot]": "codex",

    # Google Gemini Code Assist - Google's AI code reviewer
    # Source: https://github.com/apps/gemini-code-assist
    "gemini-code-assist[bot]": "gemini",
    # Alternative Gemini bot name (for potential future variations)
    "google-gemini[bot]": "gemini",

    # CodeRabbit - AI-powered code review tool
    # Source: https://github.com/apps/coderabbitai
    "coderabbitai[bot]": "coderabbit",

    # Sourcery - AI code quality tool
    # Source: https://github.com/apps/sourcery-ai
    "sourcery-ai[bot]": "sourcery",

    # Devin - Cognition AI's autonomous coding agent
    # Source: https://github.com/apps/devin-ai-integration
    "devin-ai-integration[bot]": "devin",
}

# Automation bots that are allowed for specific event types
# These are NOT AI reviewers, but automation bots that trigger PR events
# Fix: Phase B-B - Allow github-actions[bot] for PR events to enable webhook testing
ALLOWED_AUTOMATION_BOTS: Dict[str, str] = {
    # GitHub Actions - CI/CD automation bot
    "github-actions[bot]": "github-actions",
    # Dependabot - Dependency update bot
    "dependabot[bot]": "dependabot",
}

# Event types that automation bots are allowed to trigger
# Only allow PR-related events to avoid infinite loops
# Issue: #3366 - Added CI_CHECK_COMPLETED for CI failure reflex
AUTOMATION_BOT_ALLOWED_EVENTS = {
    WebhookEventType.PR_OPENED,
    WebhookEventType.PR_UPDATED,
    WebhookEventType.PR_CLOSED,
    WebhookEventType.PR_MERGED,
    WebhookEventType.CI_CHECK_COMPLETED,
}


# GitHub event type to normalized event type mapping
GITHUB_EVENT_MAP: Dict[str, Dict[str, WebhookEventType]] = {
    "pull_request": {
        "opened": WebhookEventType.PR_OPENED,
        "closed": WebhookEventType.PR_CLOSED,
        "merged": WebhookEventType.PR_MERGED,
        "synchronize": WebhookEventType.PR_UPDATED,
        "edited": WebhookEventType.PR_UPDATED,
        "reopened": WebhookEventType.PR_OPENED,
    },
    "pull_request_review": {
        "submitted": WebhookEventType.PR_REVIEWED,
    },
    "pull_request_review_comment": {
        "created": WebhookEventType.PR_COMMENTED,
    },
    "issues": {
        "opened": WebhookEventType.ISSUE_CREATED,
        "closed": WebhookEventType.ISSUE_CLOSED,
        "edited": WebhookEventType.ISSUE_UPDATED,
        "reopened": WebhookEventType.ISSUE_CREATED,
        "assigned": WebhookEventType.ISSUE_ASSIGNED,
    },
    "issue_comment": {
        "created": WebhookEventType.ISSUE_COMMENTED,
    },
    "push": {
        "default": WebhookEventType.PUSH,
    },
    "create": {
        "branch": WebhookEventType.BRANCH_CREATED,
    },
    "delete": {
        "branch": WebhookEventType.BRANCH_DELETED,
    },
    # Issue: #3366 - CI Failure Reflex Integration
    # check_suite events are sent when CI checks complete on a PR
    "check_suite": {
        "completed": WebhookEventType.CI_CHECK_COMPLETED,
    },
}


class GitHubWebhookHandler(BaseWebhookHandler):
    """
    Handler for GitHub webhook events.

    Supports signature validation using HMAC-SHA256 and converts
    GitHub-specific events to normalized WebhookEvent format.
    """

    SIGNATURE_HEADER = "X-Hub-Signature-256"
    EVENT_HEADER = "X-GitHub-Event"
    DELIVERY_HEADER = "X-GitHub-Delivery"

    def __init__(self, config: Optional[WebhookConfig] = None):
        """Initialize GitHub webhook handler"""
        super().__init__(config)
        logger.info("[GitHubWebhookHandler] Initialized")

    @property
    def source(self) -> WebhookSource:
        """Return GitHub as the webhook source"""
        return WebhookSource.GITHUB

    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Validate GitHub webhook signature using HMAC-SHA256.

        GitHub sends signatures in format: sha256=<hex_digest>

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            secret: Webhook secret configured in GitHub
            headers: Optional request headers (not used by GitHub handler)

        Returns:
            True if signature is valid
        """
        if not signature or not signature.startswith("sha256="):
            logger.warning("[GitHubWebhookHandler] Invalid signature format")
            return False

        expected_signature = signature[7:]  # Remove "sha256=" prefix

        # Compute HMAC-SHA256
        mac = hmac.new(
            secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256
        )
        computed_signature = mac.hexdigest()

        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(computed_signature, expected_signature)

        if not is_valid:
            logger.warning("[GitHubWebhookHandler] Signature validation failed")

        return is_valid

    def get_event_type(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEventType:
        """
        Determine the normalized event type from GitHub webhook.

        Args:
            headers: Request headers (contains X-GitHub-Event)
            payload: Parsed JSON payload (contains action)

        Returns:
            Normalized WebhookEventType
        """
        # Defensive normalization: accept headers with any case
        # Fix: Phase B-B - Normalize headers to lowercase for consistent access
        headers_lc = {k.lower(): v for k, v in headers.items()} if headers else {}

        # Get GitHub event type from header
        github_event = headers_lc.get(self.EVENT_HEADER.lower(), "").lower()
        action = payload.get("action", "default")

        # Handle special cases
        if github_event == "pull_request" and action == "closed":
            # Check if PR was merged
            pr = payload.get("pull_request", {})
            if pr.get("merged"):
                return WebhookEventType.PR_MERGED

        if github_event == "create":
            ref_type = payload.get("ref_type", "")
            action = ref_type

        if github_event == "delete":
            ref_type = payload.get("ref_type", "")
            action = ref_type

        # Look up in event map
        event_actions = GITHUB_EVENT_MAP.get(github_event, {})
        event_type = event_actions.get(action, WebhookEventType.UNKNOWN)

        logger.debug(
            "[GitHubWebhookHandler] Event mapping: %s/%s -> %s",
            github_event,
            action,
            event_type.value,
        )

        return event_type

    def parse_event(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> WebhookEvent:
        """
        Parse GitHub webhook payload into normalized WebhookEvent.

        Args:
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            Normalized WebhookEvent
        """
        # Defensive normalization: accept headers with any case
        # Fix: Phase B-B - Normalize headers to lowercase for consistent access
        headers_lc = {k.lower(): v for k, v in headers.items()} if headers else {}

        # Get event metadata
        event_id = headers_lc.get(self.DELIVERY_HEADER.lower(), str(uuid.uuid4()))
        event_type = self.get_event_type(headers, payload)
        github_event = headers_lc.get(self.EVENT_HEADER.lower(), "").lower()

        # Extract repository information
        repo = payload.get("repository", {})
        repo_owner = repo.get("owner", {}).get("login")
        repo_name = repo.get("name")

        # Extract actor information
        sender = payload.get("sender", {})
        actor_id = str(sender.get("id", ""))
        actor_name = sender.get("login", "")

        # Extract resource-specific information based on event type
        title = None
        description = None
        url = None
        resource_id = None
        resource_type = None
        resource_url = None
        labels = []
        assignees = []

        if github_event in ("pull_request", "pull_request_review", "pull_request_review_comment"):
            pr = payload.get("pull_request", {})
            title = pr.get("title")
            description = pr.get("body")
            url = pr.get("html_url")
            # Fix: Avoid empty string trap - use None instead of "" when number is missing
            # Empty string "" is falsy, causing _build_context() to skip resource_type
            pr_number = pr.get("number")
            resource_id = str(pr_number) if pr_number is not None else None
            resource_type = "pull_request"
            resource_url = pr.get("html_url")
            labels = [label.get("name") for label in pr.get("labels", [])]
            assignees = [a.get("login") for a in pr.get("assignees", [])]

        elif github_event in ("issues", "issue_comment"):
            issue = payload.get("issue", {})
            title = issue.get("title")
            description = issue.get("body")
            url = issue.get("html_url")
            # Fix: Avoid empty string trap - use None instead of "" when number is missing
            issue_number = issue.get("number")
            resource_id = str(issue_number) if issue_number is not None else None
            resource_type = "issue"
            resource_url = issue.get("html_url")
            labels = [label.get("name") for label in issue.get("labels", [])]
            assignees = [a.get("login") for a in issue.get("assignees", [])]

            # For comments, include comment body
            if github_event == "issue_comment":
                comment = payload.get("comment", {})
                description = comment.get("body")
                url = comment.get("html_url")

        elif github_event == "push":
            commits = payload.get("commits", [])
            if commits:
                title = f"Push: {len(commits)} commit(s)"
                description = "\n".join(
                    f"- {c.get('message', '').split(chr(10))[0]}"
                    for c in commits[:5]
                )
            ref = payload.get("ref", "")
            resource_id = ref.replace("refs/heads/", "")
            resource_type = "branch"
            url = payload.get("compare")

        elif github_event in ("create", "delete"):
            ref = payload.get("ref", "")
            ref_type = payload.get("ref_type", "")
            title = f"{github_event.capitalize()} {ref_type}: {ref}"
            resource_id = ref
            resource_type = ref_type

        # Issue: #3366 - CI Failure Reflex Integration
        # Handle check_suite events to extract PR information for CI failure triggering
        elif github_event == "check_suite":
            check_suite = payload.get("check_suite", {})
            conclusion = check_suite.get("conclusion", "")
            head_branch = check_suite.get("head_branch", "")
            # head_sha is extracted in metadata section below

            # Extract PR number from check_suite.pull_requests array
            pull_requests = check_suite.get("pull_requests", [])
            if pull_requests and isinstance(pull_requests, list) and len(pull_requests) > 0:
                first_pr = pull_requests[0]
                if isinstance(first_pr, dict):
                    pr_number = first_pr.get("number")
                    resource_id = str(pr_number) if pr_number is not None else None
                    resource_url = first_pr.get("url", "")

            resource_type = "check_suite"
            title = f"CI Check Suite: {conclusion} on {head_branch}"
            description = f"Check suite completed with conclusion: {conclusion}"
            url = check_suite.get("url", "")

        # Build metadata
        metadata: Dict[str, Any] = {
            "github_event": github_event,
            "action": payload.get("action"),
        }

        # Check if actor is an AI reviewer and add review_source to metadata
        # Issue: #2209 - 修復 AI Reviewer 評論接收機制
        # Using walrus operator for single lookup (Gemini suggestion)
        if review_source := AI_REVIEWER_BOTS.get(actor_name):
            metadata["review_source"] = review_source
            metadata["is_ai_reviewer"] = True
            logger.info(
                "[GitHubWebhookHandler] AI reviewer detected: %s (source: %s)",
                actor_name,
                review_source,
            )

        # Issue: #3366 - CI Failure Reflex Integration
        # Add CI-specific metadata for check_suite events
        if github_event == "check_suite":
            check_suite = payload.get("check_suite", {})
            metadata["ci_conclusion"] = check_suite.get("conclusion", "")
            metadata["ci_head_branch"] = check_suite.get("head_branch", "")
            metadata["ci_head_sha"] = check_suite.get("head_sha", "")
            metadata["ci_app_name"] = check_suite.get("app", {}).get("name", "")
            # Store PR numbers for dedup and multi-PR handling
            pull_requests = check_suite.get("pull_requests", [])
            metadata["ci_pr_numbers"] = [
                pr.get("number") for pr in pull_requests
                if isinstance(pr, dict) and pr.get("number") is not None
            ]

        # Create normalized event
        event = WebhookEvent(
            event_id=event_id,
            source=WebhookSource.GITHUB,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            raw_payload=payload,
            title=title,
            description=description,
            url=url,
            actor_id=actor_id,
            actor_name=actor_name,
            resource_id=resource_id,
            resource_type=resource_type,
            resource_url=resource_url,
            repo_owner=repo_owner,
            repo_name=repo_name,
            labels=labels,
            assignees=assignees,
            metadata=metadata,
        )

        logger.info(
            "[GitHubWebhookHandler] Parsed event: id=%s, type=%s, repo=%s/%s",
            event_id,
            event_type.value,
            repo_owner,
            repo_name,
        )

        return event

    def _get_signature_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Get the GitHub signature header"""
        # Defensive normalization: accept headers with any case
        # Fix: Phase B-B - Normalize headers to lowercase for consistent access
        headers_lc = {k.lower(): v for k, v in headers.items()} if headers else {}
        return headers_lc.get(self.SIGNATURE_HEADER.lower())

    def should_process(
        self,
        event: WebhookEvent,
        config: Optional[WebhookConfig] = None
    ) -> bool:
        """
        Determine if a GitHub event should be processed.

        Additional GitHub-specific filtering:
        - Allow whitelisted AI reviewer bots (Codex, Gemini, etc.)
        - Ignore other bot-generated events
        - Ignore events from specific users

        Issue: #2209 - 修復 AI Reviewer 評論接收機制
        """
        # First check base class filtering
        if not super().should_process(event, config):
            return False

        # Check if actor is a bot
        actor_name = event.actor_name or ""
        if actor_name.endswith("[bot]"):
            # Allow whitelisted AI reviewer bots
            # Using walrus operator for single lookup (Gemini suggestion)
            if review_source := AI_REVIEWER_BOTS.get(actor_name):
                logger.info(
                    "[GitHubWebhookHandler] Allowing AI reviewer bot: %s (source: %s)",
                    actor_name,
                    review_source,
                )
                return True

            # Allow automation bots for specific event types (PR events only)
            # Fix: Phase B-B - Allow github-actions[bot] for PR events
            if bot_type := ALLOWED_AUTOMATION_BOTS.get(actor_name):
                if event.event_type in AUTOMATION_BOT_ALLOWED_EVENTS:
                    logger.info(
                        "[GitHubWebhookHandler] Allowing automation bot: %s (type: %s) for event: %s",
                        actor_name,
                        bot_type,
                        event.event_type.value,
                    )
                    return True
                else:
                    logger.info(
                        "[GitHubWebhookHandler] Ignoring automation bot %s for non-PR event: %s",
                        actor_name,
                        event.event_type.value,
                    )
                    return False

            # Ignore other bot-generated events
            logger.info(
                "[GitHubWebhookHandler] Ignoring non-whitelisted bot event from %s",
                actor_name,
            )
            return False

        return True
