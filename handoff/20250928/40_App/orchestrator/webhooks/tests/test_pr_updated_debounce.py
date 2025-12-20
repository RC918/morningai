"""
Tests for PR_UPDATED event debounce/throttle functionality

Phase B-B: PR_UPDATED Event Support with Debounce/Throttle
Issue: P2 - Support PR_UPDATED event with debounce/throttle

CRITICAL FIX: Updated tests to verify "sleep inside job" debounce pattern.
Single push now triggers review after debounce window.

This tests:
1. is_pr_updated_allowed() helper function (returns PRUpdatedAllowedResult)
2. check_pr_updated_debounce() rate limit function (returns should_schedule_job)
3. verify_pr_updated_job_token() token verification
4. get_pr_updated_latest_payload() payload retrieval
5. mark_pr_updated_processed() processed marking
"""

import time
from unittest.mock import MagicMock, patch

from .. import normalizer as normalizer_module
from ..normalizer import is_pr_updated_allowed, PRUpdatedAllowedResult

try:
    from ...utils import rate_limit as rate_limit_module
    from ...utils.rate_limit import (
        check_pr_updated_debounce,
        verify_pr_updated_job_token,
        get_pr_updated_latest_payload,
        mark_pr_updated_processed,
        PRUpdatedDebounceResult,
    )
except ImportError:
    from utils import rate_limit as rate_limit_module
    from utils.rate_limit import (
        check_pr_updated_debounce,
        verify_pr_updated_job_token,
        get_pr_updated_latest_payload,
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
        redis_url: str = "redis://localhost:6379",
    ):
        self.enable_pr_updated_review = enable_pr_updated_review
        self.pr_updated_debounce_seconds = pr_updated_debounce_seconds
        self.pr_updated_throttle_seconds = pr_updated_throttle_seconds
        self.pr_updated_repos_whitelist = pr_updated_repos_whitelist
        self.redis_url = redis_url


class TestIsPrUpdatedAllowed:
    """Tests for is_pr_updated_allowed() function - returns PRUpdatedAllowedResult"""

    def test_returns_false_when_settings_is_none(self):
        """Test that function returns False when settings is None"""
        with patch.object(normalizer_module, "settings", None):
            result = is_pr_updated_allowed("RC918/morningai", 123)
            assert isinstance(result, PRUpdatedAllowedResult)
            assert result.is_allowed is False
            assert result.reason == "settings_unavailable"

    def test_returns_false_when_pr_updated_review_disabled(self):
        """Test that function returns False when enable_pr_updated_review is False"""
        mock_settings = MockSettings(enable_pr_updated_review=False)
        with patch.object(normalizer_module, "settings", mock_settings):
            result = is_pr_updated_allowed("RC918/morningai", 123)
            assert result.is_allowed is False
            assert result.reason == "pr_updated_review_disabled"

    def test_returns_false_when_repo_not_in_whitelist(self):
        """Test that function returns False when repo is not in whitelist"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="other/repo",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            result = is_pr_updated_allowed("RC918/morningai", 123)
            assert result.is_allowed is False
            assert result.reason == "repo_not_in_whitelist"

    def test_returns_true_with_job_token_when_first_event(self):
        """Test that first event returns is_allowed=True with job_token"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=False,
            should_schedule_job=True,
            job_token="test-token-123",
            reason="first_event: job scheduled",
            pr_key="pr_updated:RC918/morningai:123",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                result = is_pr_updated_allowed("RC918/morningai", 123)
                assert result.is_allowed is True
                assert result.should_schedule_job is True
                assert result.job_token == "test-token-123"
                assert "first_event" in result.reason

    def test_returns_true_when_repo_in_whitelist(self):
        """Test that function returns True when repo is in whitelist"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="RC918/morningai,other/repo",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=False,
            should_schedule_job=True,
            job_token="test-token-456",
            reason="first_event: job scheduled",
            pr_key="pr_updated:RC918/morningai:123",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                result = is_pr_updated_allowed("RC918/morningai", 123)
                assert result.is_allowed is True
                assert result.should_schedule_job is True

    def test_returns_false_when_debounced(self):
        """Test that function returns False when job already scheduled"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=False,
            should_schedule_job=False,
            reason="debounced: job already scheduled (event #2)",
            pr_key="pr_updated:RC918/morningai:123",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            with patch.object(
                normalizer_module,
                "check_pr_updated_debounce",
                return_value=mock_debounce_result,
            ):
                result = is_pr_updated_allowed("RC918/morningai", 123)
                assert result.is_allowed is False
                assert result.should_schedule_job is False
                assert "debounced" in result.reason

    def test_returns_false_when_throttled(self):
        """Test that function returns False when throttle check fails"""
        mock_settings = MockSettings(
            enable_pr_updated_review=True,
            pr_updated_repos_whitelist="",
        )
        mock_debounce_result = PRUpdatedDebounceResult(
            should_process=False,
            should_schedule_job=False,
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
                result = is_pr_updated_allowed("RC918/morningai", 123)
                assert result.is_allowed is False
                assert "throttled" in result.reason


class TestCheckPrUpdatedDebounce:
    """Tests for check_pr_updated_debounce() - uses 'sleep inside job' pattern"""

    def _create_mock_redis(self, get_values=None, set_return=True):
        """Create a mock Redis client with configurable behavior"""
        mock_redis = MagicMock()
        if get_values is None:
            get_values = {}

        def mock_get(key):
            return get_values.get(key)

        mock_redis.get = mock_get
        mock_redis.set = MagicMock(return_value=set_return)
        mock_redis.delete = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=MagicMock())
        return mock_redis

    def test_first_event_schedules_job(self):
        """Test that first PR_UPDATED event returns should_schedule_job=True"""
        mock_redis = self._create_mock_redis(get_values={}, set_return=True)

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = check_pr_updated_debounce(
                repo="RC918/morningai",
                pr_number=123,
                debounce_seconds=30,
                throttle_seconds=600,
                redis_url="redis://localhost:6379",
            )

        assert result.should_process is False
        assert result.should_schedule_job is True
        assert result.job_token is not None
        assert "first_event" in result.reason

    def test_subsequent_event_updates_payload_only(self):
        """Test that subsequent event only updates payload (job already scheduled)"""
        mock_redis = self._create_mock_redis(
            get_values={},
            set_return=False,
        )

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = check_pr_updated_debounce(
                repo="RC918/morningai",
                pr_number=123,
                debounce_seconds=30,
                throttle_seconds=600,
                redis_url="redis://localhost:6379",
            )

        assert result.should_process is False
        assert result.should_schedule_job is False
        assert "debounced" in result.reason

    def test_throttle_blocks_recent_review(self):
        """Test that throttle blocks if PR was reviewed recently"""
        current_time = time.time()
        last_processed_time = current_time - 300

        mock_redis = self._create_mock_redis(
            get_values={
                "pr_updated:RC918/morningai:123:last_processed": str(last_processed_time),
            }
        )

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            with patch("time.time", return_value=current_time):
                result = check_pr_updated_debounce(
                    repo="RC918/morningai",
                    pr_number=123,
                    debounce_seconds=30,
                    throttle_seconds=600,
                    redis_url="redis://localhost:6379",
                )

        assert result.should_process is False
        assert result.should_schedule_job is False
        assert "throttled" in result.reason

    def test_throttle_allows_after_window(self):
        """Test that throttle allows if enough time has passed"""
        current_time = time.time()
        last_processed_time = current_time - 700

        mock_redis = self._create_mock_redis(
            get_values={
                "pr_updated:RC918/morningai:123:last_processed": str(last_processed_time),
            },
            set_return=True,
        )

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            with patch("time.time", return_value=current_time):
                result = check_pr_updated_debounce(
                    repo="RC918/morningai",
                    pr_number=123,
                    debounce_seconds=30,
                    throttle_seconds=600,
                    redis_url="redis://localhost:6379",
                )

        assert result.should_schedule_job is True
        assert result.job_token is not None

    def test_redis_connection_error_fails_closed(self):
        """Test that Redis connection error skips PR_UPDATED (fail-closed)"""
        import redis as redis_lib

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            side_effect=redis_lib.ConnectionError("Connection refused"),
        ):
            result = check_pr_updated_debounce(
                repo="RC918/morningai",
                pr_number=123,
                redis_url="redis://localhost:6379",
            )

        assert result.should_process is False
        assert result.should_schedule_job is False
        assert "fail-closed" in result.reason


class TestVerifyPrUpdatedJobToken:
    """Tests for verify_pr_updated_job_token() function"""

    def test_returns_true_when_token_matches(self):
        """Test that verification returns True when token matches"""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value="test-token-123")

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = verify_pr_updated_job_token(
                repo="RC918/morningai",
                pr_number=123,
                job_token="test-token-123",
                redis_url="redis://localhost:6379",
            )

        assert result is True

    def test_returns_false_when_token_mismatch(self):
        """Test that verification returns False when token doesn't match"""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value="different-token")

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = verify_pr_updated_job_token(
                repo="RC918/morningai",
                pr_number=123,
                job_token="test-token-123",
                redis_url="redis://localhost:6379",
            )

        assert result is False

    def test_returns_false_when_token_expired(self):
        """Test that verification returns False when token key doesn't exist"""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value=None)

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = verify_pr_updated_job_token(
                repo="RC918/morningai",
                pr_number=123,
                job_token="test-token-123",
                redis_url="redis://localhost:6379",
            )

        assert result is False


class TestGetPrUpdatedLatestPayload:
    """Tests for get_pr_updated_latest_payload() function"""

    def test_returns_payload_when_exists(self):
        """Test that function returns payload when it exists"""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(
            return_value='{"repo": "RC918/morningai", "pr_number": 123, "event_count": 3}'
        )

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = get_pr_updated_latest_payload(
                repo="RC918/morningai",
                pr_number=123,
                redis_url="redis://localhost:6379",
            )

        assert result is not None
        assert result["repo"] == "RC918/morningai"
        assert result["pr_number"] == 123
        assert result["event_count"] == 3

    def test_returns_none_when_not_exists(self):
        """Test that function returns None when payload doesn't exist"""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value=None)

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            result = get_pr_updated_latest_payload(
                repo="RC918/morningai",
                pr_number=123,
                redis_url="redis://localhost:6379",
            )

        assert result is None


class TestMarkPrUpdatedProcessed:
    """Tests for mark_pr_updated_processed() function"""

    def test_marks_processed_and_clears_keys(self):
        """Test that marking processed sets last_processed and clears job keys"""
        mock_pipeline = MagicMock()
        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        with patch.object(
            rate_limit_module,
            "_get_redis_client",
            return_value=mock_redis,
        ), patch.object(
            rate_limit_module,
            "_get_pr_updated_keys",
            return_value=("pr_updated:RC918/morningai:123", "pr_updated:RC918/morningai:123"),
        ):
            mark_pr_updated_processed(
                repo="RC918/morningai",
                pr_number=123,
                throttle_seconds=600,
                redis_url="redis://localhost:6379",
            )

        mock_pipeline.set.assert_called_once()
        assert mock_pipeline.delete.call_count >= 2
        mock_pipeline.execute.assert_called_once()
