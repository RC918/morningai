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
from typing import Any, Dict, List, Optional

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
    # Issue: #3684 - Add check_run event support for annotations extraction
    # GitHub sends check_run events for individual CI jobs (e.g., lint, test)
    # These contain check_run.check_suite.id needed for annotations API
    "check_run": {
        "completed": WebhookEventType.CI_CHECK_COMPLETED,
    },
    # EPIC B-18: Review Comment Feedback (Human-in-the-Loop Learning)
    # pull_request_review_thread events are sent when a review thread is resolved/unresolved
    # This captures human feedback signals on AI review comments
    "pull_request_review_thread": {
        "resolved": WebhookEventType.REVIEW_THREAD_RESOLVED,
        "unresolved": WebhookEventType.REVIEW_THREAD_UNRESOLVED,
    },
}


# =============================================================================
# Helper functions for check_suite/check_run event parsing (Issue #3686)
# =============================================================================
# These helpers reduce code duplication and complexity in parse_event()


def _safe_parse_int_id(
    raw_id: Any,
    field_name: str,
    event_id: str,
    repo: str
) -> Optional[int]:
    """
    Safely parse an integer ID with warning logging on failure.

    Args:
        raw_id: The raw value to parse (may be int, str, or None)
        field_name: Name of the field for logging (e.g., "check_suite_id")
        event_id: Event ID for logging context
        repo: Repository name for logging context

    Returns:
        Parsed integer ID, or None if parsing fails or raw_id is None
    """
    if raw_id is None:
        return None
    try:
        return int(raw_id)
    except (ValueError, TypeError):
        # Issue #3686: Sanitize raw_value to prevent log injection (CWE-117)
        # Replace control characters and newlines that could inject fake log entries
        sanitized_value = str(raw_id)[:50]
        sanitized_value = sanitized_value.replace('\n', '\\n').replace('\r', '\\r')
        # Remove other control characters (ASCII 0-31 except tab)
        sanitized_value = ''.join(
            c if ord(c) >= 32 or c == '\t' else f'\\x{ord(c):02x}'
            for c in sanitized_value
        )
        logger.warning(
            "[GitHubWebhookHandler] Invalid %s, using fallback dedup",
            field_name,
            extra={
                "event_id": event_id,
                "repo": repo,
                "raw_value": sanitized_value,
            }
        )
        return None


def _extract_pr_numbers(pull_requests: Any) -> List[int]:
    """
    Extract PR numbers from pull_requests array with type safety.

    Args:
        pull_requests: The pull_requests array from check_suite/check_run payload

    Returns:
        List of PR numbers (integers), empty list if input is invalid
    """
    if not pull_requests or not isinstance(pull_requests, list):
        return []
    return [
        pr.get("number") for pr in pull_requests
        if isinstance(pr, dict) and pr.get("number") is not None
    ]


def _extract_first_pr_info(
    pull_requests: Any
) -> tuple[Optional[str], Optional[str]]:
    """
    Extract resource_id and resource_url from the first PR in pull_requests array.

    Args:
        pull_requests: The pull_requests array from check_suite/check_run payload

    Returns:
        Tuple of (resource_id, resource_url), both None if no valid PR found
    """
    if not pull_requests or not isinstance(pull_requests, list) or len(pull_requests) == 0:
        return None, None

    first_pr = pull_requests[0]
    if not isinstance(first_pr, dict):
        return None, None

    pr_number = first_pr.get("number")
    resource_id = str(pr_number) if pr_number is not None else None
    resource_url = first_pr.get("url", "")

    return resource_id, resource_url


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
        # Issue: #3686 - Refactored to use helper functions
        elif github_event == "check_suite":
            check_suite = payload.get("check_suite", {})
            conclusion = check_suite.get("conclusion", "")
            head_branch = check_suite.get("head_branch", "")

            # Extract PR info using helper function (Issue #3686)
            pull_requests = check_suite.get("pull_requests", [])
            resource_id, resource_url = _extract_first_pr_info(pull_requests)

            resource_type = "check_suite"
            title = f"CI Check Suite: {conclusion} on {head_branch}"
            description = f"Check suite completed with conclusion: {conclusion}"
            url = check_suite.get("url", "")

        # Issue: #3684 - Add check_run event support for annotations extraction
        # Handle check_run events to extract PR information and check_suite_id
        # GitHub sends check_run events for individual CI jobs (e.g., lint, test)
        # Issue: #3686 - Refactored to use helper functions
        elif github_event == "check_run":
            check_run = payload.get("check_run", {})
            conclusion = check_run.get("conclusion", "")
            # check_run has nested check_suite with head_branch
            check_suite = check_run.get("check_suite", {})
            head_branch = check_suite.get("head_branch", "")

            # Extract PR info using helper function (Issue #3686)
            pull_requests = check_run.get("pull_requests", [])
            resource_id, resource_url = _extract_first_pr_info(pull_requests)

            check_run_name = check_run.get("name", "unknown")
            resource_type = "check_run"
            title = f"CI Check Run: {check_run_name} - {conclusion} on {head_branch}"
            description = f"Check run '{check_run_name}' completed with conclusion: {conclusion}"
            url = check_run.get("html_url", "")

        # EPIC B-18: Review Comment Feedback (Human-in-the-Loop Learning)
        # Handle pull_request_review_thread events for resolved/unresolved signals
        # This captures human feedback on AI review comments
        elif github_event == "pull_request_review_thread":
            thread = payload.get("thread", {})
            pr = payload.get("pull_request", {})
            action = payload.get("action", "")

            # Extract PR info
            pr_number = pr.get("number")
            resource_id = str(pr_number) if pr_number is not None else None
            resource_type = "review_thread"
            resource_url = pr.get("html_url")
            url = thread.get("comments", [{}])[0].get("html_url", "") if thread.get("comments") else ""

            # Get the first comment in the thread (the original review comment)
            comments = thread.get("comments", [])
            first_comment = comments[0] if comments else {}
            comment_body = first_comment.get("body", "")
            comment_path = first_comment.get("path", "")

            title = f"Review Thread {action.capitalize()}: {comment_path}"
            description = comment_body[:200] + "..." if len(comment_body) > 200 else comment_body

            # Store PR labels and assignees
            labels = [label.get("name") for label in pr.get("labels", [])]
            assignees = [a.get("login") for a in pr.get("assignees", [])]

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
        # Issue: #3686 - Refactored to use helper functions
        if github_event == "check_suite":
            check_suite = payload.get("check_suite", {})
            metadata["ci_conclusion"] = check_suite.get("conclusion", "")
            metadata["ci_head_branch"] = check_suite.get("head_branch", "")
            metadata["ci_head_sha"] = check_suite.get("head_sha", "")
            metadata["ci_app_name"] = check_suite.get("app", {}).get("name", "")
            # Issue: #3513 - Add check_suite_id for dedup refinement
            # Issue: #3686 - Use helper function for safe int parsing
            repo = f"{repo_owner}/{repo_name}"
            metadata["ci_check_suite_id"] = _safe_parse_int_id(
                check_suite.get("id"), "check_suite_id", event_id, repo
            )
            # Store PR numbers for dedup and multi-PR handling (Issue #3686)
            pull_requests = check_suite.get("pull_requests", [])
            metadata["ci_pr_numbers"] = _extract_pr_numbers(pull_requests)

        # Issue: #3684 - Add CI-specific metadata for check_run events
        # check_run events contain nested check_suite with the check_suite_id needed for annotations API
        # Issue: #3686 - Refactored to use helper functions
        if github_event == "check_run":
            check_run = payload.get("check_run", {})
            check_suite = check_run.get("check_suite", {})
            metadata["ci_conclusion"] = check_run.get("conclusion", "")
            metadata["ci_head_branch"] = check_suite.get("head_branch", "")
            metadata["ci_head_sha"] = check_suite.get("head_sha", "")
            metadata["ci_app_name"] = check_run.get("app", {}).get("name", "")
            # Issue: #3686 - Use helper functions for safe int parsing
            repo = f"{repo_owner}/{repo_name}"
            metadata["ci_check_run_id"] = _safe_parse_int_id(
                check_run.get("id"), "check_run_id", event_id, repo
            )
            metadata["ci_check_suite_id"] = _safe_parse_int_id(
                check_suite.get("id"), "check_suite_id", event_id, repo
            )
            # Store PR numbers for dedup and multi-PR handling (Issue #3686)
            pull_requests = check_run.get("pull_requests", [])
            metadata["ci_pr_numbers"] = _extract_pr_numbers(pull_requests)
            # Store check_run name for better logging
            metadata["ci_check_run_name"] = check_run.get("name", "")

        # EPIC B-18: Add review thread metadata for feedback processing
        if github_event == "pull_request_review_thread":
            thread = payload.get("thread", {})
            comments = thread.get("comments", [])
            first_comment = comments[0] if comments else {}

            # Thread identification
            metadata["thread_id"] = thread.get("id")
            metadata["thread_node_id"] = thread.get("node_id", "")

            # Comment details for feedback classification
            metadata["comment_id"] = first_comment.get("id")
            metadata["comment_body"] = first_comment.get("body", "")
            metadata["comment_path"] = first_comment.get("path", "")
            metadata["comment_line"] = first_comment.get("line") or first_comment.get("original_line")

            # Check if the comment author is an AI reviewer
            comment_author = first_comment.get("user", {}).get("login", "")
            if ai_source := AI_REVIEWER_BOTS.get(comment_author):
                metadata["comment_author_is_ai"] = True
                metadata["comment_ai_source"] = ai_source
            else:
                metadata["comment_author_is_ai"] = False

            # Store all comment IDs in the thread for context
            metadata["thread_comment_ids"] = [c.get("id") for c in comments if c.get("id")]

            logger.info(
                "[GitHubWebhookHandler] Review thread %s: thread_id=%s, comment_id=%s, ai_source=%s",
                payload.get("action"),
                thread.get("id"),
                first_comment.get("id"),
                metadata.get("comment_ai_source", "human"),
            )

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
