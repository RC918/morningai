#!/usr/bin/env python3
"""
E2E Tests for source_pr_number Flow and Fail-Open Monitoring

Issue #2928: Webhook-driven E2E test for source_pr_number
Issue #2934: E2E tests for fail-open monitoring

These tests verify:
1. source_pr_number is correctly passed end-to-end from webhook to dedup key generation
2. Fail-open monitoring correctly records events when Redis is unavailable
3. Sentry alerts are triggered when fail-open threshold is exceeded

Test Strategy:
- Simulate webhook payloads with source PR information
- Verify dedup key generation includes source_pr_number
- Test fail-open behavior with mocked Redis failures
- Verify Sentry breadcrumbs and alerts are recorded correctly
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from governance.pr_deduplication import (  # noqa: E402
    generate_dedup_key,
    generate_deterministic_branch,
    acquire_pr_lease,
    _record_fail_open_event,
    get_fail_open_count,
    check_fail_open_alert_threshold,
    FAIL_OPEN_METRIC_NAME,
    DEFAULT_FAIL_OPEN_ALERT_THRESHOLD,
    DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES,
)


class TestSourcePrNumberE2E:
    """
    E2E tests for source_pr_number flow (Issue #2928).

    These tests verify that source_pr_number is correctly passed
    from webhook payload through the orchestrator to dedup key generation.
    """

    def test_dedup_key_includes_source_pr_number(self):
        """
        Test that generate_dedup_key includes source_pr_number in the key.

        This ensures that PRs triggered by different source PRs get different
        dedup keys, preventing false positive duplicate detection.
        """
        repo = "RC918/morningai"
        doc_file_path = "docs/generated/test-doc.md"

        # Without source_pr_number
        key_without_pr = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=None
        )

        # With source_pr_number
        key_with_pr_100 = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=100
        )

        key_with_pr_200 = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=200
        )

        # Keys should be different when source_pr_number differs
        assert key_without_pr != key_with_pr_100, (
            "Key without source_pr_number should differ from key with source_pr_number"
        )
        assert key_with_pr_100 != key_with_pr_200, (
            "Keys with different source_pr_numbers should be different"
        )

        # Same inputs should produce same key (deterministic)
        key_with_pr_100_again = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=100
        )
        assert key_with_pr_100 == key_with_pr_100_again, (
            "Same inputs should produce same dedup key (deterministic)"
        )

    def test_deterministic_branch_includes_source_pr_number(self):
        """
        Test that generate_deterministic_branch includes source_pr_number.

        This ensures that branches created for different source PRs have
        different names, preventing branch name collisions.
        """
        repo = "RC918/morningai"
        doc_file_path = "docs/generated/test-doc.md"

        # Without source_pr_number
        branch_without_pr = generate_deterministic_branch(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=None
        )

        # With source_pr_number
        branch_with_pr_100 = generate_deterministic_branch(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=100
        )

        branch_with_pr_200 = generate_deterministic_branch(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=200
        )

        # Branches should be different when source_pr_number differs
        assert branch_without_pr != branch_with_pr_100, (
            "Branch without source_pr_number should differ from branch with source_pr_number"
        )
        assert branch_with_pr_100 != branch_with_pr_200, (
            "Branches with different source_pr_numbers should be different"
        )

        # Same inputs should produce same branch (deterministic)
        branch_with_pr_100_again = generate_deterministic_branch(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=100
        )
        assert branch_with_pr_100 == branch_with_pr_100_again, (
            "Same inputs should produce same branch name (deterministic)"
        )

        # Branch name should follow expected format
        assert branch_with_pr_100.startswith("orchestrator/docs-"), (
            "Branch name should start with 'orchestrator/docs-'"
        )

    def test_dedup_key_with_event_action(self):
        """
        Test that generate_dedup_key correctly handles event_action parameter.

        Different event actions (opened, merged, etc.) should produce different keys.
        """
        repo = "RC918/morningai"
        doc_file_path = "docs/generated/test-doc.md"
        source_pr_number = 100

        key_opened = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=source_pr_number,
            event_action="opened"
        )

        key_merged = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=source_pr_number,
            event_action="merged"
        )

        key_no_action = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=source_pr_number,
            event_action=None
        )

        # Different event actions should produce different keys
        assert key_opened != key_merged, (
            "Different event actions should produce different keys"
        )
        assert key_opened != key_no_action, (
            "Key with event_action should differ from key without"
        )

    def test_webhook_payload_source_pr_extraction(self):
        """
        Test that source PR number can be correctly extracted from webhook payload.

        This simulates the webhook → orchestrator flow where source_pr_number
        is extracted from the payload and passed to dedup key generation.
        """
        # Simulate a PR webhook payload
        webhook_payload = {
            "action": "opened",
            "pull_request": {
                "number": 2847,
                "title": "feat: add new feature",
                "body": "This PR adds a new feature",
                "html_url": "https://github.com/RC918/morningai/pull/2847",
            },
            "repository": {
                "full_name": "RC918/morningai",
            },
        }

        # Extract source_pr_number from payload (as orchestrator would do)
        source_pr_number = webhook_payload["pull_request"]["number"]
        repo = webhook_payload["repository"]["full_name"]

        # Generate dedup key with extracted source_pr_number
        dedup_key = generate_dedup_key(
            repo=repo,
            doc_file_path="docs/generated/add-new-feature.md",
            source_pr_number=source_pr_number,
            event_action=webhook_payload["action"]
        )

        # Verify key is generated correctly
        assert dedup_key.startswith("RC918/morningai:"), (
            "Dedup key should start with repo name"
        )
        assert len(dedup_key) > len("RC918/morningai:"), (
            "Dedup key should include hash suffix"
        )

        # Verify determinism
        dedup_key_again = generate_dedup_key(
            repo=repo,
            doc_file_path="docs/generated/add-new-feature.md",
            source_pr_number=source_pr_number,
            event_action=webhook_payload["action"]
        )
        assert dedup_key == dedup_key_again, (
            "Same webhook payload should produce same dedup key"
        )


class TestFailOpenMonitoringE2E:
    """
    E2E tests for fail-open monitoring (Issue #2934).

    These tests verify that fail-open events are correctly recorded
    and alerts are triggered when thresholds are exceeded.
    """

    def test_record_fail_open_event_adds_sentry_breadcrumb(self):
        """
        Test that _record_fail_open_event adds a Sentry breadcrumb.

        This ensures fail-open events are traceable in Sentry for debugging.
        """
        mock_sentry = MagicMock()

        with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
            _record_fail_open_event(
                trace_id="trace-123",
                dedup_key="RC918/morningai:abc123",
                reason="redis_unavailable",
                error="Connection refused",
                redis_client=None
            )

        # Verify Sentry breadcrumb was added
        mock_sentry.add_breadcrumb.assert_called_once()
        call_kwargs = mock_sentry.add_breadcrumb.call_args[1]
        assert call_kwargs["category"] == "pr_dedup"
        assert "redis_unavailable" in call_kwargs["message"]
        assert call_kwargs["level"] == "warning"
        assert call_kwargs["data"]["fail_open"] is True

    def test_record_fail_open_event_increments_redis_metric(self):
        """
        Test that _record_fail_open_event increments the Redis metric counter.

        This ensures fail-open events are counted for threshold alerting.
        """
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        _record_fail_open_event(
            trace_id="trace-123",
            dedup_key="RC918/morningai:abc123",
            reason="connection_error",
            error="Connection refused",
            redis_client=mock_redis
        )

        # Verify Redis pipeline was used
        mock_redis.pipeline.assert_called_once_with(transaction=True)
        mock_pipeline.incr.assert_called_once()
        mock_pipeline.expire.assert_called_once()
        mock_pipeline.execute.assert_called_once()

        # Verify metric key format
        incr_call_args = mock_pipeline.incr.call_args[0][0]
        assert f"metrics:orchestrator:{FAIL_OPEN_METRIC_NAME}:" in incr_call_args

    def test_acquire_pr_lease_fail_open_when_redis_unavailable(self):
        """
        Test that acquire_pr_lease returns fail-open result when Redis is unavailable.

        This ensures the system continues to function (fail-open) when Redis is down.
        """
        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            result = acquire_pr_lease(
                dedup_key="RC918/morningai:abc123",
                worker_id="worker-1",
                trace_id="trace-123"
            )

        # Should acquire lease (fail-open behavior)
        assert result.acquired is True
        assert "unavailable" in result.reason.lower() or "fail-open" in result.reason.lower()

    def test_acquire_pr_lease_fail_open_on_connection_error(self):
        """
        Test that acquire_pr_lease returns fail-open result on Redis connection error.

        This ensures transient Redis errors don't block PR creation.
        """
        mock_redis = MagicMock()
        mock_redis.set.side_effect = Exception("Connection refused")

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = acquire_pr_lease(
                dedup_key="RC918/morningai:abc123",
                worker_id="worker-1",
                trace_id="trace-123"
            )

        # Should acquire lease (fail-open behavior)
        assert result.acquired is True
        assert "fail-open" in result.reason.lower()

    def test_get_fail_open_count_returns_zero_when_redis_unavailable(self):
        """
        Test that get_fail_open_count returns 0 when Redis is unavailable.

        This ensures the function doesn't raise exceptions when Redis is down.
        """
        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            count = get_fail_open_count()

        assert count == 0

    def test_get_fail_open_count_sums_minute_buckets(self):
        """
        Test that get_fail_open_count correctly sums values from minute buckets.

        This verifies the time-windowed counting logic.
        """
        mock_redis = MagicMock()
        # Simulate 3 minute buckets with values 2, 3, 1
        mock_redis.get.side_effect = [b"2", b"3", b"1", None, None]

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            count = get_fail_open_count(window_minutes=5)

        assert count == 6  # 2 + 3 + 1

    def test_check_fail_open_alert_threshold_below_threshold(self):
        """
        Test that check_fail_open_alert_threshold returns False when below threshold.
        """
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"1"  # Low count

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            exceeded = check_fail_open_alert_threshold()

        assert exceeded is False

    def test_check_fail_open_alert_threshold_above_threshold(self):
        """
        Test that check_fail_open_alert_threshold returns True when above threshold.
        """
        mock_redis = MagicMock()
        # 10 per minute * 5 minutes = 50 > default threshold of 5
        mock_redis.get.return_value = b"10"

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            exceeded = check_fail_open_alert_threshold()

        assert exceeded is True

    def test_check_fail_open_alert_threshold_sends_sentry_alert(self):
        """
        Test that check_fail_open_alert_threshold sends Sentry alert when exceeded.

        This verifies the alerting mechanism works correctly.
        """
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"10"  # High count to exceed threshold
        mock_sentry = MagicMock()

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
                check_fail_open_alert_threshold()

        # Verify Sentry alert was sent
        mock_sentry.capture_message.assert_called_once()
        call_args = mock_sentry.capture_message.call_args
        assert "threshold exceeded" in call_args[0][0].lower()
        assert call_args[1]["level"] == "error"

    def test_fail_open_constants_are_configured(self):
        """
        Test that fail-open monitoring constants are properly configured.
        """
        assert FAIL_OPEN_METRIC_NAME == "pr_lease.fail_open"
        assert DEFAULT_FAIL_OPEN_ALERT_THRESHOLD == 5
        assert DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES == 5


class TestFailOpenGracefulDegradation:
    """
    Tests for graceful degradation when monitoring infrastructure fails.

    These tests ensure the system continues to function even when
    Sentry or Redis monitoring is unavailable.
    """

    def test_record_fail_open_event_graceful_when_sentry_unavailable(self):
        """
        Test that _record_fail_open_event doesn't raise when Sentry is unavailable.
        """
        # Don't mock sentry_sdk - let it fail naturally
        # This should not raise any exception
        _record_fail_open_event(
            trace_id="trace-123",
            dedup_key="RC918/morningai:abc123",
            reason="redis_unavailable",
            error=None,
            redis_client=None
        )
        # Test passes if no exception is raised

    def test_record_fail_open_event_graceful_when_sentry_raises(self):
        """
        Test that _record_fail_open_event continues when Sentry add_breadcrumb raises.
        """
        mock_sentry = MagicMock()
        mock_sentry.add_breadcrumb.side_effect = Exception("Sentry error")

        with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
            # This should not raise any exception
            _record_fail_open_event(
                trace_id="trace-123",
                dedup_key="RC918/morningai:abc123",
                reason="connection_error",
                error="Connection refused",
                redis_client=None
            )
        # Test passes if no exception is raised

    def test_record_fail_open_event_graceful_when_redis_pipeline_fails(self):
        """
        Test that _record_fail_open_event continues when Redis pipeline fails.
        """
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Redis pipeline error")

        # This should not raise any exception
        _record_fail_open_event(
            trace_id="trace-123",
            dedup_key="RC918/morningai:abc123",
            reason="connection_error",
            error="Connection refused",
            redis_client=mock_redis
        )
        # Test passes if no exception is raised


class TestConfigurableThresholds:
    """
    Tests for configurable fail-open alert thresholds (Issue #2933).

    These tests verify that thresholds can be configured via settings.
    """

    def test_check_fail_open_alert_uses_settings_threshold(self):
        """
        Test that check_fail_open_alert_threshold uses settings values.

        Note: Settings are imported inside the function, so we patch
        common.config.settings.settings to override the values.
        """
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"3"  # 3 per minute * 5 = 15

        mock_settings = MagicMock()
        mock_settings.fail_open_alert_threshold = 10  # Custom threshold
        mock_settings.fail_open_alert_window_minutes = 5

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            with patch('common.config.settings.settings', mock_settings):
                exceeded = check_fail_open_alert_threshold()

        # 15 > 10, so should exceed
        assert exceeded is True

    def test_check_fail_open_alert_uses_settings_window(self):
        """
        Test that check_fail_open_alert_threshold uses settings window value.

        Note: Settings are imported inside the function, so we patch
        common.config.settings.settings to override the values.
        """
        mock_redis = MagicMock()
        # Return 2 for each minute bucket
        mock_redis.get.return_value = b"2"

        mock_settings = MagicMock()
        mock_settings.fail_open_alert_threshold = 5
        mock_settings.fail_open_alert_window_minutes = 3  # Custom window

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            with patch('common.config.settings.settings', mock_settings):
                # With 3-minute window and 2 per minute = 6 total
                # 6 > 5 threshold, so should exceed
                exceeded = check_fail_open_alert_threshold()

        assert exceeded is True


class TestE2EWebhookToLeaseFlow:
    """
    End-to-end tests simulating the complete webhook → lease flow.

    These tests verify the entire flow from webhook receipt to lease acquisition.
    """

    def test_complete_webhook_to_lease_flow_with_source_pr(self):
        """
        Test the complete flow from webhook to lease acquisition with source_pr_number.

        This simulates:
        1. Webhook received with PR number
        2. source_pr_number extracted
        3. Dedup key generated
        4. Lease acquired
        """
        # Step 1: Simulate webhook payload
        webhook_payload = {
            "action": "opened",
            "pull_request": {
                "number": 2847,
                "title": "feat: add new feature",
            },
            "repository": {
                "full_name": "RC918/morningai",
            },
        }

        # Step 2: Extract source_pr_number (as orchestrator would do)
        source_pr_number = webhook_payload["pull_request"]["number"]
        repo = webhook_payload["repository"]["full_name"]
        doc_file_path = "docs/generated/add-new-feature.md"

        # Step 3: Generate dedup key
        dedup_key = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=source_pr_number,
            event_action=webhook_payload["action"]
        )

        # Step 4: Acquire lease (mock Redis for success case)
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # SETNX success

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = acquire_pr_lease(
                dedup_key=dedup_key,
                worker_id="worker-1",
                trace_id="trace-123"
            )

        # Verify lease was acquired
        assert result.acquired is True
        assert result.lease_key is not None

    def test_complete_webhook_to_lease_flow_fail_open(self):
        """
        Test the complete flow with Redis failure (fail-open behavior).

        This simulates:
        1. Webhook received
        2. Redis unavailable
        3. Fail-open allows PR creation
        4. Fail-open event recorded
        """
        # Step 1: Simulate webhook payload
        webhook_payload = {
            "action": "opened",
            "pull_request": {
                "number": 2848,
                "title": "fix: bug fix",
            },
            "repository": {
                "full_name": "RC918/morningai",
            },
        }

        # Step 2: Extract source_pr_number
        source_pr_number = webhook_payload["pull_request"]["number"]
        repo = webhook_payload["repository"]["full_name"]
        doc_file_path = "docs/generated/bug-fix.md"

        # Step 3: Generate dedup key
        dedup_key = generate_dedup_key(
            repo=repo,
            doc_file_path=doc_file_path,
            source_pr_number=source_pr_number
        )

        # Step 4: Acquire lease with Redis unavailable
        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            result = acquire_pr_lease(
                dedup_key=dedup_key,
                worker_id="worker-1",
                trace_id="trace-123"
            )

        # Verify fail-open behavior
        assert result.acquired is True
        assert "unavailable" in result.reason.lower() or "fail-open" in result.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
