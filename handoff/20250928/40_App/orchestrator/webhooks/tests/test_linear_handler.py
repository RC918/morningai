"""
Tests for LinearWebhookHandler

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import hashlib
import hmac
import json
import pytest

from ..bot_protocol import WebhookConfig, WebhookEventType, WebhookSource
from ..handlers.linear_handler import LinearWebhookHandler, LINEAR_PRIORITY_MAP


@pytest.fixture
def linear_handler():
    """Create a LinearWebhookHandler instance for testing"""
    config = WebhookConfig(
        secret="test-secret",
        verify_signature=True,
    )
    return LinearWebhookHandler(config)


@pytest.fixture
def issue_created_payload():
    """Sample Linear issue created webhook payload"""
    return {
        "action": "create",
        "type": "Issue",
        "organizationId": "org-123",
        "data": {
            "id": "issue-uuid-123",
            "identifier": "ENG-456",
            "title": "Implement new feature",
            "description": "This is a detailed description of the feature to implement",
            "priority": 2,  # High priority
            "url": "https://linear.app/org-123/issue/ENG-456",
            "state": {
                "id": "state-123",
                "name": "Todo",
                "type": "unstarted",
            },
            "team": {
                "id": "team-123",
                "key": "ENG",
                "name": "Engineering",
            },
            "project": {
                "id": "project-123",
                "name": "Q1 Roadmap",
            },
            "labels": [
                {"id": "label-1", "name": "feature"},
                {"id": "label-2", "name": "frontend"},
            ],
            "assignee": {
                "id": "user-456",
                "name": "Jane Developer",
                "email": "jane@example.com",
            },
        },
        "actor": {
            "id": "user-123",
            "name": "John Manager",
            "email": "john@example.com",
        },
    }


@pytest.fixture
def issue_updated_completed_payload():
    """Sample Linear issue updated (completed) webhook payload"""
    return {
        "action": "update",
        "type": "Issue",
        "organizationId": "org-123",
        "data": {
            "id": "issue-uuid-123",
            "identifier": "ENG-456",
            "title": "Implement new feature",
            "description": "Feature description",
            "priority": 2,
            "url": "https://linear.app/org-123/issue/ENG-456",
            "state": {
                "id": "state-done",
                "name": "Done",
                "type": "completed",
            },
            "team": {
                "id": "team-123",
                "key": "ENG",
                "name": "Engineering",
            },
        },
        "actor": {
            "id": "user-123",
            "name": "John Manager",
        },
    }


@pytest.fixture
def comment_created_payload():
    """Sample Linear comment created webhook payload"""
    return {
        "action": "create",
        "type": "Comment",
        "organizationId": "org-123",
        "data": {
            "id": "comment-uuid-123",
            "body": "This is a comment on the issue",
            "issue": {
                "id": "issue-uuid-123",
                "identifier": "ENG-456",
                "title": "Implement new feature",
                "url": "https://linear.app/org-123/issue/ENG-456",
            },
            "user": {
                "id": "user-789",
                "name": "Commenter",
                "email": "commenter@example.com",
            },
        },
        "actor": {
            "id": "user-789",
            "name": "Commenter",
            "email": "commenter@example.com",
        },
    }


class TestLinearWebhookHandler:
    """Tests for LinearWebhookHandler"""

    def test_source(self, linear_handler):
        """Test that source returns LINEAR"""
        assert linear_handler.source == WebhookSource.LINEAR

    def test_validate_signature_valid(self, linear_handler, issue_created_payload):
        """Test signature validation with valid signature"""
        payload = json.dumps(issue_created_payload).encode()
        secret = "test-secret"

        # Compute expected signature
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        signature = mac.hexdigest()

        assert linear_handler.validate_signature(payload, signature, secret) is True

    def test_validate_signature_invalid(self, linear_handler, issue_created_payload):
        """Test signature validation with invalid signature"""
        payload = json.dumps(issue_created_payload).encode()
        secret = "test-secret"

        assert linear_handler.validate_signature(payload, "invalid-signature", secret) is False

    def test_validate_signature_empty(self, linear_handler):
        """Test signature validation with empty signature"""
        assert linear_handler.validate_signature(b"payload", "", "secret") is False

    def test_get_event_type_issue_created(self, linear_handler, issue_created_payload):
        """Test event type detection for issue created"""
        event_type = linear_handler.get_event_type({}, issue_created_payload)
        assert event_type == WebhookEventType.ISSUE_CREATED

    def test_get_event_type_issue_updated(self, linear_handler):
        """Test event type detection for issue updated"""
        payload = {
            "action": "update",
            "type": "Issue",
            "data": {
                "state": {"type": "started"},
            },
        }
        event_type = linear_handler.get_event_type({}, payload)
        assert event_type == WebhookEventType.ISSUE_UPDATED

    def test_get_event_type_issue_completed(self, linear_handler, issue_updated_completed_payload):
        """Test event type detection for issue completed"""
        event_type = linear_handler.get_event_type({}, issue_updated_completed_payload)
        assert event_type == WebhookEventType.ISSUE_CLOSED

    def test_get_event_type_comment_created(self, linear_handler, comment_created_payload):
        """Test event type detection for comment created"""
        event_type = linear_handler.get_event_type({}, comment_created_payload)
        assert event_type == WebhookEventType.ISSUE_COMMENTED

    def test_get_event_type_unknown(self, linear_handler):
        """Test event type detection for unknown event"""
        payload = {
            "action": "unknown",
            "type": "Unknown",
        }
        event_type = linear_handler.get_event_type({}, payload)
        assert event_type == WebhookEventType.UNKNOWN

    def test_parse_event_issue_created(self, linear_handler, issue_created_payload):
        """Test parsing issue created event"""
        headers = {"Linear-Delivery": "delivery-123"}
        event = linear_handler.parse_event(headers, issue_created_payload)

        assert event.event_id == "delivery-123"
        assert event.source == WebhookSource.LINEAR
        assert event.event_type == WebhookEventType.ISSUE_CREATED
        assert event.title == "Implement new feature"
        assert event.description == "This is a detailed description of the feature to implement"
        assert event.url == "https://linear.app/org-123/issue/ENG-456"
        assert event.actor_id == "user-123"
        assert event.actor_name == "John Manager"
        assert event.resource_id == "ENG-456"
        assert event.resource_type == "issue"
        assert event.priority == "high"
        assert "feature" in event.labels
        assert "frontend" in event.labels
        assert "Jane Developer" in event.assignees
        assert event.metadata["team_key"] == "ENG"
        assert event.metadata["project_name"] == "Q1 Roadmap"

    def test_parse_event_comment_created(self, linear_handler, comment_created_payload):
        """Test parsing comment created event"""
        headers = {}
        event = linear_handler.parse_event(headers, comment_created_payload)

        assert event.source == WebhookSource.LINEAR
        assert event.event_type == WebhookEventType.ISSUE_COMMENTED
        assert event.description == "This is a comment on the issue"
        assert event.title == "Implement new feature"
        assert event.resource_id == "ENG-456"

    def test_parse_event_without_delivery_header(self, linear_handler, issue_created_payload):
        """Test parsing event without delivery header generates UUID"""
        event = linear_handler.parse_event({}, issue_created_payload)
        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_priority_mapping(self):
        """Test Linear priority mapping"""
        assert LINEAR_PRIORITY_MAP[0] == "medium"  # No priority
        assert LINEAR_PRIORITY_MAP[1] == "critical"  # Urgent
        assert LINEAR_PRIORITY_MAP[2] == "high"
        assert LINEAR_PRIORITY_MAP[3] == "medium"
        assert LINEAR_PRIORITY_MAP[4] == "low"

    def test_should_process_default(self, linear_handler, issue_created_payload):
        """Test should_process with default config"""
        event = linear_handler.parse_event({}, issue_created_payload)
        assert linear_handler.should_process(event) is True

    def test_should_process_team_filter(self, issue_created_payload):
        """Test should_process with team filter"""
        config = WebhookConfig(
            metadata={"allowed_teams": ["BACKEND"]},
        )
        handler = LinearWebhookHandler(config)
        event = handler.parse_event({}, issue_created_payload)

        # Event is from ENG team, not BACKEND
        assert handler.should_process(event) is False

    def test_should_process_team_filter_allowed(self, issue_created_payload):
        """Test should_process with team filter (allowed)"""
        config = WebhookConfig(
            metadata={"allowed_teams": ["ENG"]},
        )
        handler = LinearWebhookHandler(config)
        event = handler.parse_event({}, issue_created_payload)

        assert handler.should_process(event) is True

    def test_should_process_project_filter(self, issue_created_payload):
        """Test should_process with project filter"""
        config = WebhookConfig(
            metadata={"allowed_projects": ["Q2 Roadmap"]},
        )
        handler = LinearWebhookHandler(config)
        event = handler.parse_event({}, issue_created_payload)

        # Event is from Q1 Roadmap, not Q2 Roadmap
        assert handler.should_process(event) is False

    def test_should_process_state_filter(self, issue_created_payload):
        """Test should_process with state type filter"""
        config = WebhookConfig(
            metadata={"allowed_state_types": ["started", "completed"]},
        )
        handler = LinearWebhookHandler(config)
        event = handler.parse_event({}, issue_created_payload)

        # Event state is "unstarted", not in allowed list
        assert handler.should_process(event) is False

    def test_get_signature_header(self, linear_handler):
        """Test getting signature header"""
        headers = {"Linear-Signature": "sig-123"}
        assert linear_handler._get_signature_header(headers) == "sig-123"

    def test_parse_event_with_labels_as_strings(self, linear_handler):
        """Test parsing event with labels as strings instead of dicts"""
        payload = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "issue-123",
                "identifier": "ENG-789",
                "title": "Test Issue",
                "labels": ["bug", "urgent"],
                "team": {"key": "ENG"},
            },
            "actor": {"id": "user-1", "name": "User"},
        }

        event = linear_handler.parse_event({}, payload)
        assert "bug" in event.labels
        assert "urgent" in event.labels

    def test_parse_event_minimal_payload(self, linear_handler):
        """Test parsing event with minimal payload"""
        payload = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "issue-123",
            },
            "actor": {},
        }

        event = linear_handler.parse_event({}, payload)
        assert event.source == WebhookSource.LINEAR
        assert event.resource_id == "issue-123"

    def test_url_construction_without_url(self, linear_handler):
        """Test URL construction when URL is not provided"""
        payload = {
            "action": "create",
            "type": "Issue",
            "organizationId": "my-org",
            "data": {
                "id": "issue-123",
                "identifier": "ENG-100",
                "team": {"key": "ENG"},
            },
            "actor": {},
        }

        event = linear_handler.parse_event({}, payload)
        assert event.url == "https://linear.app/my-org/issue/ENG-100"
