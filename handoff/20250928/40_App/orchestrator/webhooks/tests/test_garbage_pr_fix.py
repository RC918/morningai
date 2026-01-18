"""
Tests for Garbage PR Fix - Self-Trigger Loop Prevention

Issue: Garbage PR Fix (Dec 2025)
Root Cause: UNKNOWN events bypass should_skip_orchestrator_pr_event() and
trigger garbage PR creation via keyword matching in is_actionable().

This test file validates:
1. UNKNOWN events are not actionable (Fix 1)
2. should_skip_orchestrator_pr_event() checks PR events AND UNKNOWN events (Fix 2)
3. Branch detection works for CI events (check_suite, check_run, status)
4. Non-PR events (ISSUE_CREATED, etc.) are NOT checked by should_skip_orchestrator_pr_event
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource


# Create mock module for utils.constants
_mock_constants = MagicMock()
_mock_constants.LABEL_ORCHESTRATOR_DOCS = "orchestrator-docs"
_mock_constants.LABEL_ORCHESTRATOR_DOCS_TEST = "orchestrator-docs-test"


@pytest.fixture(autouse=True)
def mock_utils_constants():
    """Mock utils.constants module for tests"""
    with patch.dict("sys.modules", {"utils.constants": _mock_constants}):
        yield


from ..normalizer import EventNormalizer, should_skip_orchestrator_pr_event  # noqa: E402


@pytest.fixture
def event_normalizer():
    """Create an EventNormalizer instance for testing"""
    return EventNormalizer()


def create_mock_event(
    event_type: WebhookEventType = WebhookEventType.UNKNOWN,
    raw_payload: dict = None,
    title: str = "Test Event",
    description: str = "",
    labels: list = None,
) -> WebhookEvent:
    """Create a mock WebhookEvent for testing"""
    return WebhookEvent(
        event_id="test-event-123",
        source=WebhookSource.GITHUB,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        raw_payload=raw_payload or {},
        title=title,
        description=description,
        url="https://github.com/test/repo/pull/1",
        actor_name="test-actor",
        metadata={},
        labels=labels or [],
        repo_owner="test",
        repo_name="repo",
    )


class TestUnknownEventNotActionable:
    """Tests for Fix 1: UNKNOWN events should not be actionable"""

    def test_unknown_event_not_actionable(self, event_normalizer):
        """Test that UNKNOWN events are not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add something",
            description="This contains add keyword",
        )
        assert event_normalizer.is_actionable(event) is False

    def test_unknown_event_with_action_keywords_not_actionable(self, event_normalizer):
        """Test that UNKNOWN events with action keywords are still not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="Fix the bug",
            description="Please implement this feature and add tests",
        )
        assert event_normalizer.is_actionable(event) is False

    def test_unknown_event_with_ai_reviewer_metadata_not_actionable(self, event_normalizer):
        """Test that UNKNOWN events with AI reviewer metadata are not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            description="Suggestion: Consider refactoring",
        )
        event.metadata = {"is_ai_reviewer": True, "review_source": "gemini"}
        assert event_normalizer.is_actionable(event) is False

    def test_pr_opened_event_still_actionable(self, event_normalizer):
        """Test that PR_OPENED events are still actionable (regression test)"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="Fix the bug",
            description="This PR fixes a critical bug",
        )
        assert event_normalizer.is_actionable(event) is True


class TestShouldSkipOrchestratorEvent:
    """Tests for Fix 2: should_skip_orchestrator_pr_event() checks all event types"""

    def test_skip_pr_event_with_orchestrator_branch(self):
        """Test that PR events from orchestrator/* branches are skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            raw_payload={
                "pull_request": {
                    "head": {"ref": "orchestrator/docs-test-123"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_unknown_event_with_orchestrator_branch_in_check_suite(self):
        """Test that UNKNOWN events from orchestrator/* branches are skipped (check_suite)"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": {
                    "head_branch": "orchestrator/docs-test-123"
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_unknown_event_with_orchestrator_branch_in_check_run(self):
        """Test that UNKNOWN events from orchestrator/* branches are skipped (check_run)"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_run": {
                    "check_suite": {
                        "head_branch": "orchestrator/docs-test-123"
                    }
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_unknown_event_with_orchestrator_branch_in_status(self):
        """Test that UNKNOWN events from orchestrator/* branches are skipped (status)"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": [
                    {"name": "orchestrator/docs-test-123"}
                ]
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_event_with_orchestrator_docs_label(self):
        """Test that events with orchestrator-docs label are skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            labels=["orchestrator-docs"],
            raw_payload={
                "pull_request": {
                    "head": {"ref": "devin/some-branch"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_event_with_orchestrator_docs_test_label(self):
        """Test that events with orchestrator-docs-test label are skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            labels=["orchestrator-docs-test"],
            raw_payload={
                "pull_request": {
                    "head": {"ref": "devin/some-branch"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_not_skip_regular_pr_event(self):
        """Test that regular PR events are not skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            raw_payload={
                "pull_request": {
                    "head": {"ref": "feature/new-feature"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_not_skip_unknown_event_without_orchestrator_branch(self):
        """Test that UNKNOWN events without orchestrator branch are not skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": {
                    "head_branch": "main"
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_non_pr_events_not_checked(self):
        """Test that non-PR events (ISSUE_CREATED, etc.) are NOT checked.

        This ensures we don't accidentally skip legitimate non-PR workflows
        that happen to have PR-like payload fragments.
        """
        non_pr_event_types = [
            WebhookEventType.ISSUE_CREATED,
            WebhookEventType.ISSUE_CLOSED,
            WebhookEventType.ISSUE_COMMENTED,
            WebhookEventType.PUSH,
        ]
        for event_type in non_pr_event_types:
            event = create_mock_event(
                event_type=event_type,
                raw_payload={
                    "pull_request": {
                        "head": {"ref": "orchestrator/docs-test-123"}
                    }
                },
            )
            assert should_skip_orchestrator_pr_event(event) is False, \
                f"Event type {event_type} should NOT be checked"


class TestAbnormalPayloads:
    """Tests for abnormal/malformed payloads - edge case coverage

    Issue: Review feedback (Dec 2025)
    These tests ensure the branch extraction logic handles unexpected
    payload structures gracefully without raising exceptions.
    """

    def test_missing_branch_field_in_check_suite(self):
        """Test handling of check_suite payload without head_branch field"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": {
                    "id": 12345,
                    "status": "completed",
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_missing_branch_field_in_check_run(self):
        """Test handling of check_run payload without head_branch field"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_run": {
                    "id": 12345,
                    "check_suite": {
                        "id": 67890,
                    }
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_empty_branches_array_in_status(self):
        """Test handling of status payload with empty branches array"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": []
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_branches_array_with_missing_name(self):
        """Test handling of status payload where branch object lacks name field"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": [
                    {"commit": {"sha": "abc123"}}
                ]
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_null_values_in_payload(self):
        """Test handling of payload with null/None values"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": None,
                "check_run": None,
                "branches": None,
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_non_dict_check_suite(self):
        """Test handling of check_suite that is not a dict"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": "not a dict"
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_non_list_branches(self):
        """Test handling of branches that is not a list"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": "not a list"
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_non_string_head_branch(self):
        """Test handling of head_branch that is not a string"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": {
                    "head_branch": 12345
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_deeply_nested_missing_fields(self):
        """Test handling of deeply nested payload with missing intermediate fields"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_run": {
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_multiple_branches_first_is_orchestrator(self):
        """Test that first branch in array is used for detection"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": [
                    {"name": "orchestrator/docs-test"},
                    {"name": "main"},
                    {"name": "feature/something"},
                ]
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_multiple_branches_first_is_not_orchestrator(self):
        """Test that non-orchestrator first branch is not skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": [
                    {"name": "main"},
                    {"name": "orchestrator/docs-test"},
                ]
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_empty_raw_payload(self):
        """Test handling of completely empty raw_payload"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={},
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_none_raw_payload(self):
        """Test handling of None raw_payload"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload=None,
        )
        assert should_skip_orchestrator_pr_event(event) is False


class TestGarbagePRScenario:
    """Integration tests for the garbage PR scenario"""

    def test_check_suite_event_from_orchestrator_pr_not_actionable(self, event_normalizer):
        """
        Test the exact scenario that caused garbage PRs:
        1. Orchestrator creates a docs PR on orchestrator/* branch
        2. GitHub sends check_suite webhook (parsed as UNKNOWN)
        3. Event should NOT be actionable
        """
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add githubunknown-docs-add-test",
            description="This contains add keyword that would trigger actionable",
            raw_payload={
                "check_suite": {
                    "head_branch": "orchestrator/docs-test-123",
                    "pull_requests": [
                        {"head": {"ref": "orchestrator/docs-test-123"}}
                    ]
                }
            },
        )

        # Fix 1: UNKNOWN events are not actionable
        assert event_normalizer.is_actionable(event) is False

        # Fix 2: should_skip_orchestrator_pr_event also catches this
        assert should_skip_orchestrator_pr_event(event) is True

    def test_check_run_event_from_orchestrator_pr_not_actionable(self, event_normalizer):
        """
        Test check_run events from orchestrator PRs are not actionable
        """
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add something",
            raw_payload={
                "check_run": {
                    "check_suite": {
                        "head_branch": "orchestrator/docs-fix-123"
                    }
                }
            },
        )

        assert event_normalizer.is_actionable(event) is False
        assert should_skip_orchestrator_pr_event(event) is True

    def test_status_event_from_orchestrator_pr_not_actionable(self, event_normalizer):
        """
        Test status events from orchestrator PRs are not actionable
        """
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add something",
            raw_payload={
                "branches": [
                    {"name": "orchestrator/docs-update-123"}
                ]
            },
        )

        assert event_normalizer.is_actionable(event) is False
        assert should_skip_orchestrator_pr_event(event) is True


class TestExtractHeadBranchFromPayload:
    """Tests for _extract_head_branch_from_payload helper function (#3047)"""

    def test_extract_from_pull_request(self):
        """Test extraction from PR payload"""
        from ..normalizer import _extract_head_branch_from_payload
        payload = {"pull_request": {"head": {"ref": "feature/my-branch"}}}
        assert _extract_head_branch_from_payload(payload) == "feature/my-branch"

    def test_extract_from_check_suite_head_branch(self):
        """Test extraction from check_suite.head_branch"""
        from ..normalizer import _extract_head_branch_from_payload
        payload = {"check_suite": {"head_branch": "orchestrator/docs-123"}}
        assert _extract_head_branch_from_payload(payload) == "orchestrator/docs-123"

    def test_extract_from_check_suite_pull_requests(self):
        """Test extraction from check_suite.pull_requests[0].head.ref"""
        from ..normalizer import _extract_head_branch_from_payload
        payload = {
            "check_suite": {
                "pull_requests": [{"head": {"ref": "feature/pr-branch"}}]
            }
        }
        assert _extract_head_branch_from_payload(payload) == "feature/pr-branch"

    def test_extract_from_check_run(self):
        """Test extraction from check_run.check_suite.head_branch"""
        from ..normalizer import _extract_head_branch_from_payload
        payload = {"check_run": {"check_suite": {"head_branch": "main"}}}
        assert _extract_head_branch_from_payload(payload) == "main"

    def test_extract_from_status_branches(self):
        """Test extraction from status event branches array"""
        from ..normalizer import _extract_head_branch_from_payload
        payload = {"branches": [{"name": "develop"}]}
        assert _extract_head_branch_from_payload(payload) == "develop"

    def test_empty_payload_returns_empty_string(self):
        """Test empty payload returns empty string"""
        from ..normalizer import _extract_head_branch_from_payload
        assert _extract_head_branch_from_payload({}) == ""

    def test_none_payload_returns_empty_string(self):
        """Test None payload returns empty string"""
        from ..normalizer import _extract_head_branch_from_payload
        assert _extract_head_branch_from_payload(None) == ""

    def test_non_dict_payload_returns_empty_string(self):
        """Test non-dict payload returns empty string"""
        from ..normalizer import _extract_head_branch_from_payload
        assert _extract_head_branch_from_payload("not a dict") == ""
        assert _extract_head_branch_from_payload([]) == ""

    def test_priority_pr_over_check_suite(self):
        """Test PR payload takes priority over check_suite"""
        from ..normalizer import _extract_head_branch_from_payload
        payload = {
            "pull_request": {"head": {"ref": "pr-branch"}},
            "check_suite": {"head_branch": "check-suite-branch"}
        }
        assert _extract_head_branch_from_payload(payload) == "pr-branch"


class TestStagingObservationLogging:
    """Tests for staging observation logging fields (#3047)"""

    def test_unknown_event_logging_fields(self, event_normalizer, caplog):
        """Test that UNKNOWN event skip logs contain required fields"""
        import logging
        caplog.set_level(logging.INFO)

        event = WebhookEvent(
            event_id="test-event-456",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.UNKNOWN,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"check_suite": {"head_branch": "orchestrator/test-123"}},
            title="Test Event",
            description="",
            url="https://github.com/test/repo/pull/1",
            actor_name="test-bot",
            metadata={"github_event": "check_suite", "action": "completed"},
            labels=[],
            repo_owner="test",
            repo_name="repo",
        )

        result = event_normalizer.is_actionable(event)
        assert result is False

        # Verify the log message contains expected text
        assert any("UNKNOWN event skipped" in r.message for r in caplog.records)

        # Find the log record and verify extra fields are present
        log_records = [r for r in caplog.records if "UNKNOWN event skipped" in r.message]
        assert len(log_records) >= 1
        record = log_records[0]
        # Verify extra fields are captured (they become attributes on the LogRecord)
        assert hasattr(record, "operation") and record.operation == "unknown_event_skip"
        assert hasattr(record, "github_event") and record.github_event == "check_suite"
        assert hasattr(record, "github_action") and record.github_action == "completed"
        assert hasattr(record, "head_branch") and record.head_branch == "orchestrator/test-123"
        assert hasattr(record, "actor") and record.actor == "test-bot"

    def test_orchestrator_branch_skip_logging_fields(self, caplog):
        """Test that orchestrator branch skip logs contain required fields"""
        import logging
        caplog.set_level(logging.INFO)

        event = WebhookEvent(
            event_id="test-event-789",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_OPENED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"pull_request": {"head": {"ref": "orchestrator/docs-456"}}},
            title="Test PR",
            description="",
            url="https://github.com/test/repo/pull/1",
            actor_name="test-user",
            metadata={"github_event": "pull_request", "action": "opened"},
            labels=[],
            repo_owner="test",
            repo_name="repo",
        )

        result = should_skip_orchestrator_pr_event(event)
        assert result is True

        # Verify the log message contains expected text
        assert any("orchestrator-generated event" in r.message for r in caplog.records)


# =============================================================================
# Smart PR Filtering Tests (Dec 2025)
# =============================================================================
# These tests validate the smart filtering strategy that reduces noise by
# skipping PRs that only modify config/docs/tests/CI files or have
# non-actionable title prefixes (chore/ci/test/docs/style).
# =============================================================================

from ..normalizer import (  # noqa: E402
    _title_is_non_actionable,
    _title_should_always_review,
    _path_is_non_code,
    _should_skip_by_paths,
    should_skip_pr_by_smart_filters,
)


class TestTitleIsNonActionable:
    """Tests for _title_is_non_actionable() semantic title filter"""

    def test_chore_prefix_is_actionable(self):
        """Test that chore: prefix is actionable (Blueprint alignment Jan 2026)
        
        chore: PRs are now reviewed because they can contain security-sensitive
        configuration changes. See: MorningAI_Ecosystem_Blueprint_2025_Final.md
        """
        assert _title_is_non_actionable("chore: update dependencies") is False
        assert _title_is_non_actionable("chore(deps): bump version") is False
        assert _title_is_non_actionable("Chore: Update something") is False

    def test_ci_prefix_is_non_actionable(self):
        """Test that ci: prefix is non-actionable"""
        assert _title_is_non_actionable("ci: fix workflow") is True
        assert _title_is_non_actionable("ci(github): update actions") is True
        assert _title_is_non_actionable("CI: Update pipeline") is True

    def test_test_prefix_is_non_actionable(self):
        """Test that test: prefix is non-actionable"""
        assert _title_is_non_actionable("test: add unit tests") is True
        assert _title_is_non_actionable("tests: improve coverage") is True
        assert _title_is_non_actionable("test(api): add integration tests") is True

    def test_docs_prefix_is_actionable(self):
        """Test that docs: prefix is actionable (Blueprint alignment Jan 2026)
        
        docs: PRs are now reviewed because they can contain bugs like incorrect
        line references or outdated API docs. See: MorningAI_Ecosystem_Blueprint_2025_Final.md
        """
        assert _title_is_non_actionable("docs: update README") is False
        assert _title_is_non_actionable("docs(api): add examples") is False

    def test_style_prefix_is_non_actionable(self):
        """Test that style: prefix is non-actionable"""
        assert _title_is_non_actionable("style: fix formatting") is True
        assert _title_is_non_actionable("style(lint): apply prettier") is True

    def test_build_prefix_is_non_actionable(self):
        """Test that build: prefix is non-actionable"""
        assert _title_is_non_actionable("build: update webpack config") is True
        assert _title_is_non_actionable("build(docker): optimize image") is True

    def test_feat_prefix_is_actionable(self):
        """Test that feat: prefix is actionable"""
        assert _title_is_non_actionable("feat: add new feature") is False
        assert _title_is_non_actionable("feat(api): implement endpoint") is False

    def test_fix_prefix_is_actionable(self):
        """Test that fix: prefix is actionable"""
        assert _title_is_non_actionable("fix: resolve bug") is False
        assert _title_is_non_actionable("fix(auth): handle edge case") is False

    def test_refactor_prefix_is_actionable(self):
        """Test that refactor: prefix is actionable"""
        assert _title_is_non_actionable("refactor: improve code structure") is False
        assert _title_is_non_actionable("refactor(core): optimize performance") is False

    def test_no_prefix_is_actionable(self):
        """Test that titles without conventional prefix are actionable"""
        assert _title_is_non_actionable("Add new feature") is False
        assert _title_is_non_actionable("Fix the bug") is False
        assert _title_is_non_actionable("Update something") is False

    def test_empty_title_is_actionable(self):
        """Test that empty title is actionable (fail open)"""
        assert _title_is_non_actionable("") is False
        assert _title_is_non_actionable(None) is False


class TestTitleShouldAlwaysReview:
    """Tests for _title_should_always_review() - Blueprint alignment Jan 2026
    
    docs: and chore: PRs should ALWAYS be reviewed, even if they only contain
    non-code files (e.g., .md files, config files).
    
    Rationale:
    - docs: PRs can contain bugs (incorrect line references, outdated API docs)
    - chore: PRs can contain security-sensitive configuration changes
    """

    def test_docs_prefix_should_always_review(self):
        """Test that docs: prefix triggers always-review"""
        assert _title_should_always_review("docs: update README") is True
        assert _title_should_always_review("docs(api): add examples") is True
        assert _title_should_always_review("Docs: Update something") is True

    def test_chore_prefix_should_always_review(self):
        """Test that chore: prefix triggers always-review"""
        assert _title_should_always_review("chore: update dependencies") is True
        assert _title_should_always_review("chore(deps): bump version") is True
        assert _title_should_always_review("Chore: Update something") is True

    def test_ci_prefix_should_not_always_review(self):
        """Test that ci: prefix does NOT trigger always-review"""
        assert _title_should_always_review("ci: fix workflow") is False
        assert _title_should_always_review("ci(github): update actions") is False

    def test_test_prefix_should_not_always_review(self):
        """Test that test: prefix does NOT trigger always-review"""
        assert _title_should_always_review("test: add unit tests") is False
        assert _title_should_always_review("tests: improve coverage") is False

    def test_feat_prefix_should_not_always_review(self):
        """Test that feat: prefix does NOT trigger always-review (uses normal flow)"""
        assert _title_should_always_review("feat: add new feature") is False
        assert _title_should_always_review("fix: resolve bug") is False

    def test_empty_title_should_not_always_review(self):
        """Test that empty title does NOT trigger always-review"""
        assert _title_should_always_review("") is False
        assert _title_should_always_review(None) is False


class TestPathIsNonCode:
    """Tests for _path_is_non_code() file path filter"""

    def test_yaml_files_are_non_code(self):
        """Test that YAML files are non-code"""
        assert _path_is_non_code("config.yaml") is True
        assert _path_is_non_code("settings.yml") is True
        assert _path_is_non_code("render.yaml") is True

    def test_json_files_are_non_code(self):
        """Test that JSON files are non-code"""
        assert _path_is_non_code("package.json") is True
        assert _path_is_non_code("tsconfig.json") is True

    def test_toml_files_are_non_code(self):
        """Test that TOML files are non-code"""
        assert _path_is_non_code("pyproject.toml") is True
        assert _path_is_non_code("Cargo.toml") is True

    def test_markdown_files_are_non_code(self):
        """Test that Markdown files are non-code"""
        assert _path_is_non_code("README.md") is True
        assert _path_is_non_code("CHANGELOG.md") is True
        assert _path_is_non_code("docs/guide.md") is True

    def test_docs_directory_is_non_code(self):
        """Test that docs/ directory files are non-code"""
        assert _path_is_non_code("docs/api.md") is True
        assert _path_is_non_code("docs/guide/setup.md") is True
        assert _path_is_non_code("docs/images/logo.png") is True

    def test_github_directory_is_non_code(self):
        """Test that .github/ directory files are non-code"""
        assert _path_is_non_code(".github/workflows/ci.yml") is True
        assert _path_is_non_code(".github/CODEOWNERS") is True
        assert _path_is_non_code(".github/dependabot.yml") is True

    def test_tests_directory_is_non_code(self):
        """Test that tests/ directory files are non-code"""
        assert _path_is_non_code("tests/test_api.py") is True
        assert _path_is_non_code("tests/unit/test_utils.py") is True
        assert _path_is_non_code("test/integration/test_flow.py") is True

    def test_test_file_suffixes_are_non_code(self):
        """Test that test file suffixes are non-code"""
        assert _path_is_non_code("api_test.py") is True
        assert _path_is_non_code("utils.test.py") is True
        assert _path_is_non_code("component.spec.ts") is True
        assert _path_is_non_code("component.test.js") is True

    def test_specific_filenames_are_non_code(self):
        """Test that specific filenames are non-code"""
        assert _path_is_non_code("LICENSE") is True
        assert _path_is_non_code("requirements.txt") is True
        assert _path_is_non_code(".gitignore") is True
        assert _path_is_non_code("Dockerfile") is True
        assert _path_is_non_code("Makefile") is True

    def test_python_files_are_code(self):
        """Test that Python files are code"""
        assert _path_is_non_code("main.py") is False
        assert _path_is_non_code("src/api/routes.py") is False
        assert _path_is_non_code("utils/helpers.py") is False

    def test_typescript_files_are_code(self):
        """Test that TypeScript files are code"""
        assert _path_is_non_code("app.ts") is False
        assert _path_is_non_code("src/components/Button.tsx") is False

    def test_javascript_files_are_code(self):
        """Test that JavaScript files are code"""
        assert _path_is_non_code("index.js") is False
        assert _path_is_non_code("src/utils.jsx") is False

    def test_go_files_are_code(self):
        """Test that Go files are code"""
        assert _path_is_non_code("main.go") is False
        assert _path_is_non_code("pkg/api/handler.go") is False

    def test_rust_files_are_code(self):
        """Test that Rust files are code"""
        assert _path_is_non_code("main.rs") is False
        assert _path_is_non_code("src/lib.rs") is False

    def test_empty_path_is_non_code(self):
        """Test that empty path is non-code"""
        assert _path_is_non_code("") is True
        assert _path_is_non_code(None) is True

    def test_setup_py_is_code(self):
        """Test that setup.py is treated as code (can contain executable logic)"""
        # setup.py can contain significant executable logic like custom build commands,
        # dynamic dependency resolution, or registration of entry points
        assert _path_is_non_code("setup.py") is False
        assert _path_is_non_code("src/setup.py") is False

    def test_backslash_paths_normalized(self):
        """Test that Windows-style backslash paths are normalized correctly"""
        # GitHub API always uses forward slashes, but this makes the helper reusable
        assert _path_is_non_code("docs\\readme.md") is True
        assert _path_is_non_code("tests\\test_main.py") is True
        assert _path_is_non_code("src\\main.py") is False
        assert _path_is_non_code("path\\to\\component.tsx") is False


class TestShouldSkipByPaths:
    """Tests for _should_skip_by_paths() aggregate path filter"""

    def test_all_non_code_files_should_skip(self):
        """Test that PRs with only non-code files should skip"""
        paths = ["README.md", "docs/guide.md", ".github/workflows/ci.yml"]
        should_skip, reason, sample = _should_skip_by_paths(paths)
        assert should_skip is True
        assert reason == "only_non_code_files"

    def test_mixed_files_should_not_skip(self):
        """Test that PRs with code files should not skip"""
        paths = ["README.md", "src/main.py", ".github/workflows/ci.yml"]
        should_skip, reason, sample = _should_skip_by_paths(paths)
        assert should_skip is False
        assert reason == "has_code_files"

    def test_only_code_files_should_not_skip(self):
        """Test that PRs with only code files should not skip"""
        paths = ["src/main.py", "src/utils.py", "lib/helpers.ts"]
        should_skip, reason, sample = _should_skip_by_paths(paths)
        assert should_skip is False
        assert reason == "has_code_files"

    def test_empty_paths_should_skip(self):
        """Test that PRs with no files should skip"""
        should_skip, reason, sample = _should_skip_by_paths([])
        assert should_skip is True
        assert reason == "no_files"

    def test_single_code_file_should_not_skip(self):
        """Test that PRs with a single code file should not skip"""
        paths = ["src/main.py"]
        should_skip, reason, sample = _should_skip_by_paths(paths)
        assert should_skip is False

    def test_single_non_code_file_should_skip(self):
        """Test that PRs with a single non-code file should skip"""
        paths = ["README.md"]
        should_skip, reason, sample = _should_skip_by_paths(paths)
        assert should_skip is True


class TestShouldSkipPrBySmartFilters:
    """Tests for should_skip_pr_by_smart_filters() integration"""

    def test_non_pr_event_not_filtered(self):
        """Test that non-PR events are not filtered"""
        event = create_mock_event(
            event_type=WebhookEventType.ISSUE_CREATED,
            title="chore: update something",
        )
        should_skip, reason, details = should_skip_pr_by_smart_filters(event)
        assert should_skip is False
        assert reason == "not_pr_event"

    def test_pr_opened_with_chore_title_not_skipped(self):
        """Test that PR_OPENED with chore: title is NOT skipped (Blueprint alignment Jan 2026)
        
        chore: PRs are now reviewed because they can contain security-sensitive
        configuration changes. See: MorningAI_Ecosystem_Blueprint_2025_Final.md
        """
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="chore: update dependencies",
        )
        should_skip, reason, details = should_skip_pr_by_smart_filters(event)
        # chore: is no longer skipped - it will either pass all filters or fail open on API error
        assert should_skip is False or "api_error" in reason

    def test_pr_merged_with_ci_title_skipped(self):
        """Test that PR_MERGED with ci: title is skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_MERGED,
            title="ci: fix workflow",
        )
        should_skip, reason, details = should_skip_pr_by_smart_filters(event)
        assert should_skip is True
        assert reason == "semantic_title_skip"

    def test_pr_opened_with_feat_title_not_skipped_by_title(self):
        """Test that PR_OPENED with feat: title passes title filter"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="feat: add new feature",
        )
        # Note: This will try to call the API for file paths
        # In tests, the API call will fail and we'll fail open
        should_skip, reason, details = should_skip_pr_by_smart_filters(event)
        # Should either pass all filters or fail open on API error
        assert should_skip is False or "api_error" in reason

    def test_pr_updated_not_filtered(self):
        """Test that PR_UPDATED events are not filtered by smart filters"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_UPDATED,
            title="chore: update something",
        )
        should_skip, reason, details = should_skip_pr_by_smart_filters(event)
        assert should_skip is False
        assert reason == "not_pr_event"


class TestSmartFilterIntegration:
    """Integration tests for smart filtering in is_actionable()"""

    def test_pr_opened_with_chore_title_is_actionable(self, event_normalizer):
        """Test that PR_OPENED with chore: title IS actionable (Blueprint alignment Jan 2026)
        
        chore: PRs are now reviewed because they can contain security-sensitive
        configuration changes. See: MorningAI_Ecosystem_Blueprint_2025_Final.md
        """
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="chore: update dependencies",
            raw_payload={"pull_request": {"head": {"ref": "feature/update-deps"}}},
        )
        assert event_normalizer.is_actionable(event) is True

    def test_pr_merged_with_docs_title_is_actionable(self, event_normalizer):
        """Test that PR_MERGED with docs: title IS actionable (Blueprint alignment Jan 2026)
        
        docs: PRs are now reviewed because they can contain bugs like incorrect
        line references or outdated API docs. See: MorningAI_Ecosystem_Blueprint_2025_Final.md
        """
        event = create_mock_event(
            event_type=WebhookEventType.PR_MERGED,
            title="docs: update README",
            raw_payload={"pull_request": {"head": {"ref": "docs/update-readme"}}},
        )
        assert event_normalizer.is_actionable(event) is True

    def test_pr_opened_with_test_title_not_actionable(self, event_normalizer):
        """Test that PR_OPENED with test: title is not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="test: add unit tests",
            raw_payload={"pull_request": {"head": {"ref": "test/add-tests"}}},
        )
        assert event_normalizer.is_actionable(event) is False

    def test_pr_opened_with_ci_title_not_actionable(self, event_normalizer):
        """Test that PR_OPENED with ci: title is not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="ci: fix workflow",
            raw_payload={"pull_request": {"head": {"ref": "ci/fix-workflow"}}},
        )
        assert event_normalizer.is_actionable(event) is False

    def test_pr_opened_with_style_title_not_actionable(self, event_normalizer):
        """Test that PR_OPENED with style: title is not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="style: fix formatting",
            raw_payload={"pull_request": {"head": {"ref": "style/fix-formatting"}}},
        )
        assert event_normalizer.is_actionable(event) is False


class TestSmartFilterLogging:
    """Tests for smart filter logging"""

    def test_semantic_title_skip_logging(self, caplog):
        """Test that semantic title skip logs contain required fields
        
        Note: Using ci: prefix since chore: is no longer skipped (Blueprint alignment Jan 2026)
        """
        import logging
        caplog.set_level(logging.INFO)

        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="ci: update workflow",  # Changed from chore: to ci: since chore: is no longer skipped
        )
        event.resource_id = "123"

        should_skip, reason, details = should_skip_pr_by_smart_filters(event)
        assert should_skip is True

        # Verify log contains expected operation
        assert any("pr_event_skip_semantic_title" in str(r.__dict__) for r in caplog.records)
