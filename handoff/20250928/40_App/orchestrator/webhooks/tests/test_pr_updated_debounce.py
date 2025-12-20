"""
Tests for PR_UPDATED event debounce/throttle functionality

Phase B-B: PR_UPDATED Event Support with Debounce/Throttle
Issue: P2 - Support PR_UPDATED event with debounce/throttle

This tests:
1. is_pr_updated_allowed() helper function
2. check_pr_updated_debounce() rate limit function
3. Integration with is_actionable() for PR_UPDATED events
"""

import time
from unittest.mock import MagicMock, patch

from .. import normalizer as normalizer_module
from ..normalizer import is_pr_updated_allowed

try:
    from ...utils.rate_limit import (
        check_pr_updated_debounce,
        mark_pr_updated_processed,
        PRUpdatedDebounceResult,
    )
except ImportError:
    from utils.rate_limit import (
        check_pr_updated_debounce,
        mark_pr_updated_processed,
        PRUpdatedDebounceResult,
    )


class MockSettings:
    """Mock settings object for testing PR_UPDATED functionality"""

    def __init__(
        self,
        enable_pr_updated_review: bool = False,
        pr_updated_debounce_seconds: int = 30,
        pr_updated_throttle_seconds: int = 600,
        pr_updated_repos_whitelist: str = "",
    ):
        self.enable_pr_updated_review = enable_pr_updated_review
        self.pr_updated_debounce_seconds = pr_updated_debounce_seconds
        self.pr_updated_throttle_seconds = pr_updated_throttle_seconds
        self.pr_updated_repos_whitelist = pr_updated_repos_whitelist


class TestIsPrUpdatedAllowed:
    """Tests for is_pr_updated_allowed() function"""

    def test_returns_false_when_settings_is_none(self):
        """Test that function returns False when settings is None"""
        with patch.object(normalizer_module, "settings", None):
            allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
            assert allowed is False
            assert reason == "settings_unavailable"

    def test_returns_false_when_pr_updated_review_disabled(self):
        """Test that function returns False when enable_pr_updated_review is False"""
        mock_settings = MockSettings(enable_pr_updated_review=False)
        with patch.object(normalizer_module, "settings", mock_settings):
            allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
            assert allowed is False
            assert reason == "pr_updated_review_disabled"

    def test_returns_false_when_repo_not_in_whitelist(self):
        """Test that function returns False when repo is not in whitelist"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="other/repo",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
            assert allowed is False
            assert reason == "repo_not_in_whitelist"

    def test_returns_true_when_whitelist_empty(self):
        """Test that empty whitelist allows all repos"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=True,
            reason="allowed",
            pr_key="pr_updated:RC918/morningai:123",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
                assert allowed is True
                assert reason == "allowed"

    def test_returns_true_when_repo_in_whitelist(self):
        """Test that function returns True when repo is in whitelist"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="RC918/morningai,other/repo",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=True,
            reason="allowed",
            pr_key="pr_updated:RC918/morningai:123",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
                assert allowed is True
                assert reason == "allowed"

    def test_returns_false_when_debounced(self):
        """Test that function returns False when debounce check fails"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=False,
            reason="debounced: pending event 5s ago",
            pr_key="pr_updated:RC918/morningai:123",
            pending_since=time.time() - 5,
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
                assert allowed is False
                assert "debounced" in reason

    def test_returns_false_when_throttled(self):
        """Test that function returns False when throttle check fails"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=False,
            reason="throttled: last review 300s ago",
            pr_key="pr_updated:RC918/morningai:123",
            last_processed_at=time.time() - 300,
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                allowed, reason = is_pr_updated_allowed("RC918/morningai", 123)
                assert allowed is False
                assert "throttled" in reason


class TestCheckPrUpdatedDebounce:
    """Tests for check_pr_updated_debounce() function"""

    def _create_mock_redis(self, get_values=None):
        """Create a mock Redis client with configurable get() return values"""
        mock_redis = MagicMock()
        if get_values is None:
            get_values = {}

        def mock_get(key):
            return get_values.get(key)

        mock_redis.get = mock_get
        mock_redis.set = MagicMock()
        mock_redis.delete = MagicMock()
        return mock_redis

    def test_first_event_sets_pending(self):
        """Test that first PR_UPDATED event sets pending key"""
        mock_redis = self._create_mock_redis(get_values={})

        with patch("redis.Redis.from_url", return_value=mock_redis):
            result = check_pr_updated_debounce(
                repo="RC918/morningai",
                pr_number=123,
                debounce_seconds=30,
                throttle_seconds=600,
                redis_url="redis://localhost:6379",
            )

        assert result.should_process is False
        assert "pending" in result.reason
        mock_redis.set.assert_called_once()

    def test_event_within_debounce_window_updates_pending(self):
        """Test that event within debounce window updates pending timestamp"""
        current_time = time.time()
        pending_time = current_time - 10  # 10 seconds ago

        mock_redis = self._create_mock_redis(
            get_values={
                "pr_updated:RC918/morningai:123:pending": str(pending_time),
            }
        )

        with patch("redis.Redis.from_url", return_value=mock_redis):
            with patch("time.time", return_value=current_time):
                result = check_pr_updated_debounce(
                    repo="RC918/morningai",
                    pr_number=123,
                    debounce_seconds=30,
                    throttle_seconds=600,
                    redis_url="redis://localhost:6379",
                )

        assert result.should_process is False
        assert "debounced" in result.reason
        mock_redis.set.assert_called_once()

    def test_event_after_debounce_window_processes(self):
        """Test that event after debounce window expires is processed"""
        current_time = time.time()
        pending_time = current_time - 35  # 35 seconds ago (> 30s debounce)

        mock_redis = self._create_mock_redis(
            get_values={
                "pr_updated:RC918/morningai:123:pending": str(pending_time),
            }
        )

        with patch("redis.Redis.from_url", return_value=mock_redis):
            with patch("time.time", return_value=current_time):
                result = check_pr_updated_debounce(
                    repo="RC918/morningai",
                    pr_number=123,
                    debounce_seconds=30,
                    throttle_seconds=600,
                    redis_url="redis://localhost:6379",
                )

        assert result.should_process is True
        assert result.reason == "debounce_expired"
        mock_redis.delete.assert_called_once()

    def test_throttle_blocks_recent_review(self):
        """Test that throttle blocks if PR was reviewed recently"""
        current_time = time.time()
        last_processed_time = current_time - 300  # 5 minutes ago (< 10 min throttle)

        mock_redis = self._create_mock_redis(
            get_values={
                "pr_updated:RC918/morningai:123:last_processed": str(last_processed_time),
            }
        )

        with patch("redis.Redis.from_url", return_value=mock_redis):
            with patch("time.time", return_value=current_time):
                result = check_pr_updated_debounce(
                    repo="RC918/morningai",
                    pr_number=123,
                    debounce_seconds=30,
                    throttle_seconds=600,
                    redis_url="redis://localhost:6379",
                )

        assert result.should_process is False
        assert "throttled" in result.reason

    def test_throttle_allows_after_window(self):
        """Test that throttle allows if enough time has passed"""
        current_time = time.time()
        last_processed_time = current_time - 700  # 11+ minutes ago (> 10 min throttle)

        mock_redis = self._create_mock_redis(
            get_values={
                "pr_updated:RC918/morningai:123:last_processed": str(last_processed_time),
            }
        )

        with patch("redis.Redis.from_url", return_value=mock_redis):
            with patch("time.time", return_value=current_time):
                result = check_pr_updated_debounce(
                    repo="RC918/morningai",
                    pr_number=123,
                    debounce_seconds=30,
                    throttle_seconds=600,
                    redis_url="redis://localhost:6379",
                )

        assert result.should_process is False
        assert "pending" in result.reason

    def test_redis_connection_error_allows_request(self):
        """Test that Redis connection error allows request (fail-open)"""
        import redis as redis_lib

        with patch(
            "redis.Redis.from_url",
            side_effect=redis_lib.ConnectionError("Connection refused"),
        ):
            result = check_pr_updated_debounce(
                repo="RC918/morningai",
                pr_number=123,
                redis_url="redis://localhost:6379",
            )

        assert result.should_process is True
        assert result.reason == "redis_unavailable"


class TestMarkPrUpdatedProcessed:
    """Tests for mark_pr_updated_processed() function"""

    def test_marks_processed_and_clears_pending(self):
        """Test that marking processed sets last_processed and clears pending"""
        mock_redis = MagicMock()

        with patch("redis.Redis.from_url", return_value=mock_redis):
            mark_pr_updated_processed(
                repo="RC918/morningai",
                pr_number=123,
                throttle_seconds=600,
                redis_url="redis://localhost:6379",
            )

        mock_redis.set.assert_called_once()
        mock_redis.delete.assert_called_once()

        set_call = mock_redis.set.call_args
        assert "last_processed" in set_call[0][0]

        delete_call = mock_redis.delete.call_args
        assert "pending" in delete_call[0][0]
