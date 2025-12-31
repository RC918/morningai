"""
Tests for CommandRouter - PR Comment Command Router

Issue: #3224 - PR Comment Command Router
Issue: #3388 - Add authorization/permission gating for /morningai commands
Blueprint: Track C interface standardization
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource
from ..command_router import (
    CommandRouter,
    CommandTrigger,
    CommandType,
)
from ..command_authorizer import (
    CommandAuthorizer,
    AuthorizationResult,
    PermissionLevel,
    AUTHORIZED_PERMISSION_LEVELS,
)


@pytest.fixture
def command_router():
    """Create a CommandRouter instance for testing (authorization disabled)"""
    return CommandRouter(enable_authorization=False)


@pytest.fixture
def command_router_with_auth():
    """Create a CommandRouter instance with authorization enabled"""
    # Use a mock authorizer for testing
    mock_authorizer = MagicMock(spec=CommandAuthorizer)
    mock_authorizer.authorize.return_value = AuthorizationResult(
        authorized=True,
        reason="Test authorized",
        permission_level=PermissionLevel.WRITE,
    )
    return CommandRouter(authorizer=mock_authorizer, enable_authorization=True)


def create_comment_event(
    description: str,
    event_type: WebhookEventType = WebhookEventType.ISSUE_COMMENTED,
    actor_name: str = "human-user",
    repo_owner: str = "test-owner",
    repo_name: str = "test-repo",
    resource_id: str = "123",
    raw_payload: dict = None,
    url: str = "https://github.com/test-owner/test-repo/pull/123#issuecomment-456",
) -> WebhookEvent:
    """Create a mock comment WebhookEvent for testing"""
    default_payload = {
        "issue": {
            "number": 123,
            "pull_request": {"url": "https://api.github.com/repos/test-owner/test-repo/pulls/123"},
        },
        "comment": {
            "body": description,
        },
    }
    return WebhookEvent(
        event_id="test-event-123",
        source=WebhookSource.GITHUB,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        raw_payload=raw_payload or default_payload,
        title="Test Comment",
        description=description,
        url=url,
        actor_name=actor_name,
        repo_owner=repo_owner,
        repo_name=repo_name,
        resource_id=resource_id,
        metadata={},
    )


class TestCommandTrigger:
    """Tests for CommandTrigger dataclass"""

    def test_command_trigger_creation(self):
        """Test that CommandTrigger can be created with required fields"""
        trigger = CommandTrigger(
            command_type=CommandType.REVIEW,
            repo="test-owner/test-repo",
            pr_number=123,
            actor="test-user",
            comment_url="https://github.com/test-owner/test-repo/pull/123#issuecomment-456",
        )

        assert trigger.command_type == CommandType.REVIEW
        assert trigger.repo == "test-owner/test-repo"
        assert trigger.pr_number == 123
        assert trigger.actor == "test-user"
        assert trigger.args == []
        assert trigger.metadata == {}

    def test_command_trigger_with_args(self):
        """Test CommandTrigger with arguments"""
        trigger = CommandTrigger(
            command_type=CommandType.EXPLAIN,
            repo="test-owner/test-repo",
            pr_number=123,
            actor="test-user",
            comment_url="https://github.com/test-owner/test-repo/pull/123#issuecomment-456",
            args=["file.py:10"],
        )

        assert trigger.args == ["file.py:10"]

    def test_command_trigger_immutable(self):
        """Test that CommandTrigger is immutable (frozen)"""
        trigger = CommandTrigger(
            command_type=CommandType.REVIEW,
            repo="test-owner/test-repo",
            pr_number=123,
            actor="test-user",
            comment_url="https://github.com/test-owner/test-repo/pull/123#issuecomment-456",
        )

        with pytest.raises(AttributeError):
            trigger.command_type = CommandType.FIX

    def test_command_trigger_to_dict(self):
        """Test CommandTrigger serialization to dict"""
        trigger = CommandTrigger(
            command_type=CommandType.REVIEW,
            repo="test-owner/test-repo",
            pr_number=123,
            actor="test-user",
            comment_url="https://github.com/test-owner/test-repo/pull/123#issuecomment-456",
            args=["arg1", "arg2"],
            metadata={"event_id": "test-123"},
        )

        result = trigger.to_dict()

        assert result["command_type"] == "review"
        assert result["repo"] == "test-owner/test-repo"
        assert result["pr_number"] == 123
        assert result["actor"] == "test-user"
        assert result["args"] == ["arg1", "arg2"]
        assert result["metadata"] == {"event_id": "test-123"}


class TestCommandRouterBasicRouting:
    """Tests for basic command routing"""

    def test_route_review_command(self, command_router):
        """Test routing /morningai review command"""
        event = create_comment_event("/morningai review")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.REVIEW
        assert trigger.repo == "test-owner/test-repo"
        assert trigger.pr_number == 123
        assert trigger.actor == "human-user"

    def test_route_review_command_case_insensitive(self, command_router):
        """Test that command routing is case-insensitive"""
        event = create_comment_event("/MorningAI Review")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.REVIEW

    def test_route_review_command_with_leading_whitespace(self, command_router):
        """Test routing command with leading whitespace"""
        event = create_comment_event("  /morningai review")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.REVIEW

    def test_route_explain_command_with_args(self, command_router):
        """Test routing /morningai explain command with arguments"""
        event = create_comment_event("/morningai explain src/auth.py:42")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.EXPLAIN
        assert trigger.args == ["src/auth.py:42"]

    def test_route_fix_command(self, command_router):
        """Test routing /morningai fix command"""
        event = create_comment_event("/morningai fix")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.FIX

    def test_route_unknown_command(self, command_router):
        """Test routing unknown command returns UNKNOWN type"""
        event = create_comment_event("/morningai unknown_cmd")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.UNKNOWN


class TestCommandRouterNonCommandComments:
    """Tests for non-command comments"""

    def test_ignore_regular_comment(self, command_router):
        """Test that regular comments are ignored"""
        event = create_comment_event("This is a regular comment")
        trigger = command_router.route(event)

        assert trigger is None

    def test_ignore_command_in_code_block(self, command_router):
        """Test that commands in code blocks are ignored (not at line start)"""
        event = create_comment_event("```\n/morningai review\n```")
        trigger = command_router.route(event)

        # The regex matches at line start, so this should still match
        # because /morningai is at the start of a line within the code block
        # This is a known limitation - we may want to improve this later
        assert trigger is not None  # Current behavior

    def test_ignore_command_in_quote(self, command_router):
        """Test that commands in quotes are ignored (quote prefix blocks match)"""
        event = create_comment_event("> /morningai review")
        trigger = command_router.route(event)

        # Quote prefix `>` is not whitespace, so regex doesn't match
        # This is the desired behavior - quoted commands should be ignored
        assert trigger is None

    def test_ignore_command_mid_sentence(self, command_router):
        """Test that commands mid-sentence are ignored"""
        event = create_comment_event("Please run /morningai review for me")
        trigger = command_router.route(event)

        # Command not at start of line - should be ignored
        assert trigger is None

    def test_command_on_second_line(self, command_router):
        """Test that command on second line is detected"""
        event = create_comment_event("First line\n/morningai review")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.REVIEW


class TestCommandRouterBotFiltering:
    """Tests for bot comment filtering"""

    def test_ignore_bot_comment(self, command_router):
        """Test that bot comments are ignored"""
        event = create_comment_event(
            "/morningai review",
            actor_name="github-actions[bot]",
        )
        trigger = command_router.route(event)

        assert trigger is None

    def test_ignore_ai_reviewer_bot(self, command_router):
        """Test that AI reviewer bot comments are ignored"""
        event = create_comment_event(
            "/morningai review",
            actor_name="gemini-code-assist[bot]",
        )
        trigger = command_router.route(event)

        assert trigger is None

    def test_allow_human_user(self, command_router):
        """Test that human user comments are processed"""
        event = create_comment_event(
            "/morningai review",
            actor_name="human-developer",
        )
        trigger = command_router.route(event)

        assert trigger is not None


class TestCommandRouterEventTypeFiltering:
    """Tests for event type filtering"""

    def test_process_issue_commented(self, command_router):
        """Test that ISSUE_COMMENTED events are processed"""
        event = create_comment_event(
            "/morningai review",
            event_type=WebhookEventType.ISSUE_COMMENTED,
        )
        trigger = command_router.route(event)

        assert trigger is not None

    def test_process_pr_commented(self, command_router):
        """Test that PR_COMMENTED events are processed"""
        event = create_comment_event(
            "/morningai review",
            event_type=WebhookEventType.PR_COMMENTED,
        )
        trigger = command_router.route(event)

        assert trigger is not None

    def test_ignore_pr_opened(self, command_router):
        """Test that PR_OPENED events are ignored"""
        event = create_comment_event(
            "/morningai review",
            event_type=WebhookEventType.PR_OPENED,
        )
        trigger = command_router.route(event)

        assert trigger is None

    def test_ignore_pr_reviewed(self, command_router):
        """Test that PR_REVIEWED events are ignored"""
        event = create_comment_event(
            "/morningai review",
            event_type=WebhookEventType.PR_REVIEWED,
        )
        trigger = command_router.route(event)

        assert trigger is None


class TestCommandRouterContextExtraction:
    """Tests for context extraction from events"""

    def test_extract_repo_from_event(self, command_router):
        """Test repo extraction from event"""
        event = create_comment_event(
            "/morningai review",
            repo_owner="my-org",
            repo_name="my-repo",
        )
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.repo == "my-org/my-repo"

    def test_extract_pr_number_from_resource_id(self, command_router):
        """Test PR number extraction from resource_id"""
        event = create_comment_event(
            "/morningai review",
            resource_id="456",
        )
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.pr_number == 456

    def test_extract_pr_number_from_raw_payload(self, command_router):
        """Test PR number extraction from raw payload"""
        event = create_comment_event(
            "/morningai review",
            resource_id=None,
            raw_payload={
                "issue": {
                    "number": 789,
                    "pull_request": {"url": "https://api.github.com/repos/test/test/pulls/789"},
                },
            },
        )
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.pr_number == 789

    def test_missing_repo_returns_none(self, command_router):
        """Test that missing repo returns None"""
        event = create_comment_event(
            "/morningai review",
            repo_owner=None,
            repo_name=None,
        )
        trigger = command_router.route(event)

        assert trigger is None

    def test_missing_pr_number_returns_none(self, command_router):
        """Test that missing PR number returns None"""
        event = create_comment_event(
            "/morningai review",
            resource_id=None,
            raw_payload={
                "issue": {
                    "number": 123,
                    # No pull_request key - this is a regular issue, not a PR
                },
            },
        )
        trigger = command_router.route(event)

        assert trigger is None


class TestCommandRouterIsCommandComment:
    """Tests for is_command_comment quick check"""

    def test_is_command_comment_true(self, command_router):
        """Test is_command_comment returns True for command comments"""
        event = create_comment_event("/morningai review")
        assert command_router.is_command_comment(event) is True

    def test_is_command_comment_false(self, command_router):
        """Test is_command_comment returns False for regular comments"""
        event = create_comment_event("This is a regular comment")
        assert command_router.is_command_comment(event) is False

    def test_is_command_comment_wrong_event_type(self, command_router):
        """Test is_command_comment returns False for wrong event type"""
        event = create_comment_event(
            "/morningai review",
            event_type=WebhookEventType.PR_OPENED,
        )
        assert command_router.is_command_comment(event) is False


class TestCommandRouterMetadata:
    """Tests for metadata in CommandTrigger"""

    def test_trigger_includes_event_metadata(self, command_router):
        """Test that trigger includes event metadata"""
        event = create_comment_event("/morningai review")
        trigger = command_router.route(event)

        assert trigger is not None
        assert "contract_version" in trigger.metadata
        assert "event_id" in trigger.metadata
        assert "event_type" in trigger.metadata
        assert "source" in trigger.metadata
        assert trigger.metadata["contract_version"] == "v1"
        assert trigger.metadata["event_id"] == "test-event-123"
        assert trigger.metadata["source"] == "github"

    def test_trigger_includes_comment_url(self, command_router):
        """Test that trigger includes comment URL"""
        event = create_comment_event(
            "/morningai review",
            url="https://github.com/test/repo/pull/123#issuecomment-789",
        )
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.comment_url == "https://github.com/test/repo/pull/123#issuecomment-789"


class TestCommandRouterEdgeCases:
    """Tests for edge cases"""

    def test_empty_comment(self, command_router):
        """Test handling of empty comment"""
        event = create_comment_event("")
        trigger = command_router.route(event)

        assert trigger is None

    def test_only_command_prefix(self, command_router):
        """Test handling of only command prefix without command"""
        event = create_comment_event("/morningai")
        trigger = command_router.route(event)

        # No command after prefix - should not match
        assert trigger is None

    def test_command_with_multiple_args(self, command_router):
        """Test command with multiple arguments"""
        event = create_comment_event("/morningai explain file1.py:10 file2.py:20")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.args == ["file1.py:10", "file2.py:20"]

    def test_command_with_special_characters_in_args(self, command_router):
        """Test command with special characters in arguments"""
        event = create_comment_event("/morningai explain src/utils/helper.py:42")
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.args == ["src/utils/helper.py:42"]

    def test_comment_from_raw_payload(self, command_router):
        """Test extracting comment from raw payload when description is empty"""
        event = WebhookEvent(
            event_id="test-event-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.ISSUE_COMMENTED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={
                "issue": {
                    "number": 123,
                    "pull_request": {"url": "https://api.github.com/repos/test/test/pulls/123"},
                },
                "comment": {
                    "body": "/morningai review",
                },
            },
            description=None,  # Empty description
            url="https://github.com/test/repo/pull/123#issuecomment-456",
            actor_name="human-user",
            repo_owner="test-owner",
            repo_name="test-repo",
            resource_id="123",
            metadata={},
        )
        trigger = command_router.route(event)

        assert trigger is not None
        assert trigger.command_type == CommandType.REVIEW

# === Authorization Tests (Issue #3388) ===


class TestCommandAuthorizer:
    """Tests for CommandAuthorizer - permission gating for commands"""

    def test_authorizer_allowlist_bypass(self):
        """Test that allowlisted users bypass permission checks"""
        authorizer = CommandAuthorizer(allowlist={"admin-user"})
        result = authorizer.authorize("test-owner/test-repo", "admin-user")

        assert result.authorized is True
        assert "allowlist" in result.reason.lower()

    def test_authorizer_permission_levels(self):
        """Test that only admin/maintain/write are authorized"""
        assert PermissionLevel.ADMIN in AUTHORIZED_PERMISSION_LEVELS
        assert PermissionLevel.MAINTAIN in AUTHORIZED_PERMISSION_LEVELS
        assert PermissionLevel.WRITE in AUTHORIZED_PERMISSION_LEVELS
        assert PermissionLevel.TRIAGE not in AUTHORIZED_PERMISSION_LEVELS
        assert PermissionLevel.READ not in AUTHORIZED_PERMISSION_LEVELS
        assert PermissionLevel.NONE not in AUTHORIZED_PERMISSION_LEVELS

    def test_authorizer_caching(self):
        """Test that permission results are cached"""
        authorizer = CommandAuthorizer()
        # Manually cache a permission
        authorizer._cache_permission("test/repo", "test-user", PermissionLevel.WRITE)

        # Get cached result
        cached = authorizer._get_cached_permission("test/repo", "test-user")
        assert cached is not None
        permission_level, _ = cached
        assert permission_level == PermissionLevel.WRITE

    def test_authorizer_cache_clear(self):
        """Test that cache can be cleared"""
        authorizer = CommandAuthorizer()
        authorizer._cache_permission("test/repo", "test-user", PermissionLevel.WRITE)
        authorizer.clear_cache()

        cached = authorizer._get_cached_permission("test/repo", "test-user")
        assert cached is None

    def test_authorizer_add_to_allowlist(self):
        """Test adding users to allowlist"""
        authorizer = CommandAuthorizer()
        authorizer.add_to_allowlist("new-admin")

        result = authorizer.authorize("test/repo", "new-admin")
        assert result.authorized is True

    def test_authorizer_remove_from_allowlist(self):
        """Test removing users from allowlist"""
        authorizer = CommandAuthorizer(allowlist={"temp-admin"})
        authorizer.remove_from_allowlist("temp-admin")

        # Without API, this will fail-closed
        result = authorizer.authorize("test/repo", "temp-admin", skip_cache=True)
        # Should not be authorized via allowlist anymore
        assert "allowlist" not in result.reason.lower()

    def test_authorization_result_to_dict(self):
        """Test AuthorizationResult serialization"""
        result = AuthorizationResult(
            authorized=True,
            reason="Test reason",
            permission_level=PermissionLevel.WRITE,
            cached=True,
        )
        d = result.to_dict()

        assert d["authorized"] is True
        assert d["reason"] == "Test reason"
        assert d["permission_level"] == "write"
        assert d["cached"] is True


class TestCommandRouterAuthorization:
    """Tests for CommandRouter authorization integration"""

    def test_router_with_authorization_enabled(self, command_router_with_auth):
        """Test that router with authorization enabled calls authorizer"""
        event = create_comment_event("/morningai review")
        trigger = command_router_with_auth.route(event)

        # Should succeed because mock authorizer returns authorized=True
        assert trigger is not None
        assert trigger.command_type == CommandType.REVIEW

    def test_router_rejects_unauthorized_user(self):
        """Test that router rejects unauthorized users"""
        mock_authorizer = MagicMock(spec=CommandAuthorizer)
        mock_authorizer.authorize.return_value = AuthorizationResult(
            authorized=False,
            reason="Insufficient permission: read",
            permission_level=PermissionLevel.READ,
        )
        router = CommandRouter(authorizer=mock_authorizer, enable_authorization=True)

        event = create_comment_event("/morningai review")
        trigger = router.route(event)

        assert trigger is None
        mock_authorizer.authorize.assert_called_once()

    def test_router_authorization_disabled(self):
        """Test that router without authorization skips permission check"""
        mock_authorizer = MagicMock(spec=CommandAuthorizer)
        router = CommandRouter(authorizer=mock_authorizer, enable_authorization=False)

        event = create_comment_event("/morningai review")
        trigger = router.route(event)

        # Should succeed without calling authorizer
        assert trigger is not None
        mock_authorizer.authorize.assert_not_called()

    def test_router_authorization_with_allowlist(self):
        """Test router with allowlist configuration"""
        router = CommandRouter(
            enable_authorization=True,
            allowlist={"allowed-user"},
        )

        # The allowlist is passed to the authorizer
        assert router._authorizer is not None
        assert "allowed-user" in router._authorizer._allowlist

    def test_router_passes_correct_params_to_authorizer(self):
        """Test that router passes correct repo and actor to authorizer"""
        mock_authorizer = MagicMock(spec=CommandAuthorizer)
        mock_authorizer.authorize.return_value = AuthorizationResult(
            authorized=True,
            reason="Authorized",
            permission_level=PermissionLevel.WRITE,
        )
        router = CommandRouter(authorizer=mock_authorizer, enable_authorization=True)

        event = create_comment_event(
            "/morningai review",
            actor_name="test-developer",
            repo_owner="my-org",
            repo_name="my-repo",
        )
        router.route(event)

        mock_authorizer.authorize.assert_called_once_with(
            "my-org/my-repo",
            "test-developer",
        )

    def test_router_api_error_denies_command(self):
        """Test that API errors result in command denial (fail-closed)"""
        mock_authorizer = MagicMock(spec=CommandAuthorizer)
        mock_authorizer.authorize.return_value = AuthorizationResult(
            authorized=False,
            reason="Failed to verify permission (API error)",
            permission_level=PermissionLevel.UNKNOWN,
        )
        router = CommandRouter(authorizer=mock_authorizer, enable_authorization=True)

        event = create_comment_event("/morningai review")
        trigger = router.route(event)

        assert trigger is None


class TestCommandAuthorizerWithMockedGitHub:
    """Tests for CommandAuthorizer with mocked GitHub API (using _fetch_permission_level mock)"""

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_authorize_write_permission(self, mock_fetch):
        """Test authorization with write permission"""
        mock_fetch.return_value = PermissionLevel.WRITE

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is True
        assert result.permission_level == PermissionLevel.WRITE
        mock_fetch.assert_called_once_with("test/repo", "test-user")

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_authorize_admin_permission(self, mock_fetch):
        """Test authorization with admin permission"""
        mock_fetch.return_value = PermissionLevel.ADMIN

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is True
        assert result.permission_level == PermissionLevel.ADMIN

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_authorize_maintain_permission(self, mock_fetch):
        """Test authorization with maintain permission"""
        mock_fetch.return_value = PermissionLevel.MAINTAIN

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is True
        assert result.permission_level == PermissionLevel.MAINTAIN

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_deny_read_permission(self, mock_fetch):
        """Test denial with read-only permission"""
        mock_fetch.return_value = PermissionLevel.READ

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is False
        assert result.permission_level == PermissionLevel.READ

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_deny_triage_permission(self, mock_fetch):
        """Test denial with triage permission"""
        mock_fetch.return_value = PermissionLevel.TRIAGE

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is False
        assert result.permission_level == PermissionLevel.TRIAGE

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_deny_none_permission(self, mock_fetch):
        """Test denial with no permission"""
        mock_fetch.return_value = PermissionLevel.NONE

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is False
        assert result.permission_level == PermissionLevel.NONE

    @patch.object(CommandAuthorizer, '_fetch_permission_level')
    def test_github_api_error_fails_closed(self, mock_fetch):
        """Test that GitHub API errors result in denial (fail-closed)"""
        mock_fetch.return_value = PermissionLevel.UNKNOWN

        authorizer = CommandAuthorizer(github_token="test-token")
        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is False
        assert result.permission_level == PermissionLevel.UNKNOWN

    def test_no_token_fails_closed(self):
        """Test that missing token results in denial"""
        authorizer = CommandAuthorizer(github_token=None)
        # Clear any token from settings
        authorizer._github_token = None

        result = authorizer.authorize("test/repo", "test-user", skip_cache=True)

        assert result.authorized is False
        assert result.permission_level == PermissionLevel.UNKNOWN
