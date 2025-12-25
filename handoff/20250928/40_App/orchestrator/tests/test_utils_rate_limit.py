"""
Tests for utils/rate_limit.py

Phase 0: Test coverage improvement (44% -> 80%+)
Focus: Deterministic unit tests without external dependencies
"""
import pytest
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import redis

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.rate_limit import (
    check_pr_rate_limit,
    get_pr_count_last_hour,
    check_ai_reviewer_rate_limit,
    get_ai_reviewer_rate_limit_counts,
    AIReviewerRateLimitResult,
    AI_REVIEWER_RATE_LIMITS,
    _get_redis_key_prefix,
    _get_pr_updated_keys,
    _get_with_legacy_fallback,
    # Issue #2943: New atomic rate limiting imports
    RateLimitResult,
    _atomic_rate_limit_check,
    _emit_rate_limit_telemetry,
    _check_and_alert_rate_limit_pattern,
    RATE_LIMIT_ALERT_THRESHOLD,
    check_deepwiki_rate_limit,
    check_notification_rate_limit,
)


class TestCheckPRRateLimit:
    """Test check_pr_rate_limit function

    Issue #2943: Tests updated to reflect atomic Lua script implementation.
    Now we mock r.eval() which returns [allowed (0 or 1), count].
    """

    def test_allows_pr_within_limit(self):
        """Should allow PR creation within rate limit

        Issue #2943: Updated to reflect atomic Lua script pattern.
        Now we call eval() which atomically checks and increments.
        """
        mock_redis = MagicMock()
        # Lua script returns [1, 5] meaning allowed=True, count=5
        mock_redis.eval.return_value = [1, 5]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-123', max_per_hour=10)

            assert allowed is True
            assert count == 5
            assert mock_redis.eval.called

    def test_blocks_pr_over_limit(self):
        """Should block PR creation when over rate limit

        Issue #2943: Updated to reflect atomic Lua script pattern.
        Lua script returns [0, count] when blocked.
        """
        mock_redis = MagicMock()
        # Lua script returns [0, 12] meaning allowed=False, count=12
        mock_redis.eval.return_value = [0, 12]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-456', max_per_hour=10)

            assert allowed is False
            assert count == 12

    def test_uses_redis_url_when_provided(self):
        """Should use Redis URL when provided"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 3]

        with patch('redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value = mock_redis

            allowed, count = check_pr_rate_limit(
                'trace-789',
                redis_url='redis://custom:6379/0'
            )

            assert allowed is True
            assert count == 3
            mock_from_url.assert_called_once()

    def test_uses_localhost_when_no_url(self):
        """Should use localhost Redis when no URL provided"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 2]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-abc')

            assert allowed is True
            mock_redis_class.assert_called_once_with(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )

    def test_lua_script_called_with_correct_args(self):
        """Should call Lua script with correct key, max_limit, and expiry

        Issue #2943: Verify Lua script is called with correct arguments.
        """
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 1]

        with patch('redis.Redis') as mock_redis_class, \
             patch('time.time', return_value=1700000000):
            mock_redis_class.return_value = mock_redis

            check_pr_rate_limit('trace-def', max_per_hour=10)

            # Verify eval was called
            assert mock_redis.eval.called
            call_args = mock_redis.eval.call_args
            # Args: (script, num_keys, key, max_limit, expiry_seconds)
            expected_hour = int(1700000000 / 3600)
            expected_key = f"orchestrator:pr_count:{expected_hour}"
            assert call_args[0][2] == expected_key  # key
            assert call_args[0][3] == 10  # max_limit
            assert call_args[0][4] == 3600  # expiry_seconds

    def test_uses_current_hour_in_key(self):
        """Should use current hour in Redis key"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 1]

        with patch('redis.Redis') as mock_redis_class, \
             patch('time.time', return_value=1700000000):
            mock_redis_class.return_value = mock_redis

            check_pr_rate_limit('trace-ghi')

            expected_hour = int(1700000000 / 3600)
            expected_key = f"orchestrator:pr_count:{expected_hour}"
            # Verify the key is passed to eval
            call_args = mock_redis.eval.call_args
            assert expected_key in call_args[0]

    def test_handles_redis_connection_error(self):
        """Should allow PR creation when Redis is unavailable (fail-open)"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.side_effect = redis.ConnectionError("Connection refused")

            allowed, count = check_pr_rate_limit('trace-jkl')

            assert allowed is True
            assert count == 0

    def test_handles_redis_operation_error(self):
        """Should allow PR creation on Redis operation error (fail-open)"""
        mock_redis = MagicMock()
        mock_redis.eval.side_effect = redis.RedisError("Operation failed")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-mno')

            assert allowed is True
            assert count == 0

    def test_handles_unexpected_exception(self):
        """Should allow PR creation on unexpected exception (fail-open)"""
        mock_redis = MagicMock()
        mock_redis.eval.side_effect = Exception("Unexpected error")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-pqr')

            assert allowed is True
            assert count == 0

    def test_custom_max_per_hour(self):
        """Should respect custom max_per_hour parameter

        Issue #2943: Updated to reflect atomic Lua script pattern.
        """
        mock_redis = MagicMock()
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            # First call: allowed, count=18
            mock_redis.eval.return_value = [1, 18]
            allowed, count = check_pr_rate_limit('trace-stu', max_per_hour=20)

            assert allowed is True
            assert count == 18

            # Second call: blocked, count=22
            mock_redis.eval.return_value = [0, 22]
            allowed, count = check_pr_rate_limit('trace-vwx', max_per_hour=20)

            assert allowed is False
            assert count == 22

    def test_boundary_condition_at_limit(self):
        """Should allow PR when count reaches exactly max_limit

        Issue #2943: Verify >= comparison is correct.
        When current count is 9 and max is 10, we allow and increment to 10.
        """
        mock_redis = MagicMock()
        # Lua script allows when current < max, so count=10 means we just reached limit
        mock_redis.eval.return_value = [1, 10]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-yz', max_per_hour=10)

            assert allowed is True
            assert count == 10

    def test_boundary_condition_at_exact_limit(self):
        """Should block PR when count == max_limit (Issue #2943 verification)

        Issue #2943: Verify >= comparison blocks at exact limit.
        When current count is already 10 and max is 10, we block.
        """
        mock_redis = MagicMock()
        # Lua script blocks when current >= max
        mock_redis.eval.return_value = [0, 10]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-boundary', max_per_hour=10)

            assert allowed is False
            assert count == 10

    def test_boundary_condition_over_limit(self):
        """Should block PR at limit + 1

        Issue #2943: Updated to reflect atomic Lua script pattern.
        """
        mock_redis = MagicMock()
        # Lua script returns [0, 11] meaning blocked, count=11
        mock_redis.eval.return_value = [0, 11]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-123', max_per_hour=10)

            assert allowed is False
            assert count == 11


class TestGetPRCountLastHour:
    """Test get_pr_count_last_hour function"""

    def test_returns_current_count(self):
        """Should return current PR count"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '7'

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 7

    def test_returns_zero_when_no_count(self):
        """Should return 0 when no count exists"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 0

    def test_uses_redis_url_when_provided(self):
        """Should use Redis URL when provided"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '5'

        with patch('redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value = mock_redis

            count = get_pr_count_last_hour(redis_url='redis://custom:6379/0')

            assert count == 5
            mock_from_url.assert_called_once()

    def test_uses_localhost_when_no_url(self):
        """Should use localhost Redis when no URL provided"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '3'

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 3
            mock_redis_class.assert_called_once_with(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )

    def test_uses_current_hour_in_key(self):
        """Should use current hour in Redis key"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '4'

        with patch('redis.Redis') as mock_redis_class, \
             patch('time.time', return_value=1700000000):
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            expected_hour = int(1700000000 / 3600)
            expected_key = f"orchestrator:pr_count:{expected_hour}"
            mock_redis.get.assert_called_once_with(expected_key)
            assert count == 4

    def test_handles_redis_connection_error(self):
        """Should return 0 when Redis is unavailable"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.side_effect = redis.ConnectionError("Connection refused")

            count = get_pr_count_last_hour()

            assert count == 0

    def test_handles_redis_operation_error(self):
        """Should return 0 on Redis operation error"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = redis.RedisError("Operation failed")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 0

    def test_handles_unexpected_exception(self):
        """Should return 0 on unexpected exception"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Unexpected error")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 0

    def test_handles_non_numeric_value(self):
        """Should return 0 for non-numeric values"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = 'invalid'

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 0

    def test_handles_zero_count(self):
        """Should handle zero count correctly"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '0'

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            count = get_pr_count_last_hour()

            assert count == 0


class TestIntegration:
    """Test integration scenarios

    Issue #2943: Updated to reflect atomic Lua script implementation.
    """

    def test_sequential_pr_creation(self):
        """Should track sequential PR creation correctly

        Issue #2943: Updated to reflect atomic Lua script pattern.
        Now we mock eval() which returns [allowed, count].
        """
        mock_redis = MagicMock()
        # Simulate sequential counts: eval returns [1, 1], [1, 2], [1, 3], [1, 4], [1, 5]
        eval_results = [[1, 1], [1, 2], [1, 3], [1, 4], [1, 5]]
        mock_redis.eval.side_effect = eval_results

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            for i, expected_count in enumerate([1, 2, 3, 4, 5]):
                allowed, count = check_pr_rate_limit(f'trace-{i}', max_per_hour=10)
                assert allowed is True
                assert count == expected_count

    def test_rate_limit_enforcement(self):
        """Should enforce rate limit correctly

        Issue #2943: Updated to reflect atomic Lua script pattern.
        """
        mock_redis = MagicMock()
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            # First call: allowed, count reaches 10
            mock_redis.eval.return_value = [1, 10]
            allowed, count = check_pr_rate_limit('trace-1', max_per_hour=10)
            assert allowed is True

            # Second call: blocked at limit (count == 10)
            mock_redis.eval.return_value = [0, 10]
            allowed, count = check_pr_rate_limit('trace-2', max_per_hour=10)
            assert allowed is False

            # Third call: blocked over limit (count == 11)
            mock_redis.eval.return_value = [0, 11]
            allowed, count = check_pr_rate_limit('trace-3', max_per_hour=10)
            assert allowed is False


class TestAIReviewerRateLimitResult:
    """Test AIReviewerRateLimitResult dataclass"""

    def test_default_values(self):
        """Should have correct default values"""
        result = AIReviewerRateLimitResult(allowed=True)
        assert result.allowed is True
        assert result.exceeded_dimension is None
        assert result.current_count == 0
        assert result.limit == 0
        assert result.pr_id is None
        assert result.repo is None
        assert result.bot_name is None

    def test_with_all_values(self):
        """Should store all values correctly"""
        result = AIReviewerRateLimitResult(
            allowed=False,
            exceeded_dimension='pr',
            current_count=25,
            limit=20,
            pr_id='owner/repo#123',
            repo='owner/repo',
            bot_name='copilot',
        )
        assert result.allowed is False
        assert result.exceeded_dimension == 'pr'
        assert result.current_count == 25
        assert result.limit == 20
        assert result.pr_id == 'owner/repo#123'
        assert result.repo == 'owner/repo'
        assert result.bot_name == 'copilot'


class TestCheckAIReviewerRateLimit:
    """Test check_ai_reviewer_rate_limit function (Issue #2253)"""

    def test_allows_within_all_limits(self):
        """Should allow when all dimensions are within limits"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [0, 5]
        mock_redis.pipeline.return_value = mock_pipeline

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert result.allowed is True
            assert result.exceeded_dimension is None
            assert result.pr_id == 'owner/repo#123'
            assert result.repo == 'owner/repo'
            assert result.bot_name == 'copilot'

    def test_blocks_when_pr_limit_exceeded(self):
        """Should block when per-PR limit is exceeded"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [0, 25]
        mock_redis.pipeline.return_value = mock_pipeline

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert result.allowed is False
            assert result.exceeded_dimension == 'pr'
            assert result.current_count == 25
            assert result.limit == 20

    def test_blocks_when_repo_limit_exceeded(self):
        """Should block when per-repo limit is exceeded"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return [0, 5]
            else:
                return [0, 150]

        mock_pipeline.execute.side_effect = execute_side_effect
        mock_redis.pipeline.return_value = mock_pipeline

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert result.allowed is False
            assert result.exceeded_dimension == 'repo'
            assert result.current_count == 150
            assert result.limit == 100

    def test_blocks_when_bot_limit_exceeded(self):
        """Should block when per-bot limit is exceeded"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] <= 2:
                return [0, 5]
            else:
                return [0, 60]

        mock_pipeline.execute.side_effect = execute_side_effect
        mock_redis.pipeline.return_value = mock_pipeline

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert result.allowed is False
            assert result.exceeded_dimension == 'bot'
            assert result.current_count == 60
            assert result.limit == 50

    def test_uses_custom_limits(self):
        """Should respect custom limits"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [0, 8]
        mock_redis.pipeline.return_value = mock_pipeline

        custom_limits = {
            'per_pr_per_hour': 5,
            'per_repo_per_hour': 50,
            'per_bot_per_hour': 25,
        }

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
                limits=custom_limits,
            )

            assert result.allowed is False
            assert result.exceeded_dimension == 'pr'
            assert result.limit == 5

    def test_uses_redis_url_when_provided(self):
        """Should use Redis URL when provided"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [0, 5]
        mock_redis.pipeline.return_value = mock_pipeline

        with patch('redis.Redis.from_url') as mock_from_url:
            mock_from_url.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
                redis_url='redis://custom:6379/0',
            )

            assert result.allowed is True
            mock_from_url.assert_called_once()

    def test_handles_redis_connection_error(self):
        """Should allow when Redis is unavailable"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.side_effect = redis.ConnectionError("Connection refused")

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert result.allowed is True

    def test_handles_unexpected_exception(self):
        """Should allow on unexpected exception"""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Unexpected error")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert result.allowed is True

    def test_default_rate_limits(self):
        """Should have correct default rate limits"""
        assert AI_REVIEWER_RATE_LIMITS['per_pr_per_hour'] == 20
        assert AI_REVIEWER_RATE_LIMITS['per_repo_per_hour'] == 100
        assert AI_REVIEWER_RATE_LIMITS['per_bot_per_hour'] == 50

    def test_partial_limits_fall_back_to_defaults(self):
        """Should use AI_REVIEWER_RATE_LIMITS for missing keys in partial limits dict"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return [0, 12]
            elif call_count[0] == 2:
                return [0, 5]
            else:
                return [0, 5]

        mock_pipeline.execute.side_effect = execute_side_effect
        mock_redis.pipeline.return_value = mock_pipeline

        partial_limits = {'per_pr_per_hour': 10}

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            result = check_ai_reviewer_rate_limit(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
                limits=partial_limits,
            )

            assert result.allowed is False
            assert result.exceeded_dimension == 'pr'
            assert result.limit == 10


class TestGetAIReviewerRateLimitCounts:
    """Test get_ai_reviewer_rate_limit_counts function"""

    def test_returns_pr_count(self):
        """Should return PR count when pr_id provided"""
        mock_redis = MagicMock()
        mock_redis.zcard.return_value = 15

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            counts = get_ai_reviewer_rate_limit_counts(pr_id='owner/repo#123')

            assert counts.get('pr') == 15

    def test_returns_repo_count(self):
        """Should return repo count when repo provided"""
        mock_redis = MagicMock()
        mock_redis.zcard.return_value = 75

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            counts = get_ai_reviewer_rate_limit_counts(repo='owner/repo')

            assert counts.get('repo') == 75

    def test_returns_bot_count(self):
        """Should return bot count when bot_name provided"""
        mock_redis = MagicMock()
        mock_redis.zcard.return_value = 30

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            counts = get_ai_reviewer_rate_limit_counts(bot_name='copilot')

            assert counts.get('bot') == 30

    def test_returns_all_counts(self):
        """Should return all counts when all params provided"""
        mock_redis = MagicMock()
        mock_redis.zcard.side_effect = [10, 50, 25]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            counts = get_ai_reviewer_rate_limit_counts(
                pr_id='owner/repo#123',
                repo='owner/repo',
                bot_name='copilot',
            )

            assert counts.get('pr') == 10
            assert counts.get('repo') == 50
            assert counts.get('bot') == 25

    def test_returns_empty_dict_on_error(self):
        """Should return empty dict on error"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.side_effect = Exception("Error")

            counts = get_ai_reviewer_rate_limit_counts(pr_id='owner/repo#123')

            assert counts == {}

    def test_returns_empty_dict_when_no_params(self):
        """Should return empty dict when no params provided"""
        mock_redis = MagicMock()

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            counts = get_ai_reviewer_rate_limit_counts()

            assert counts == {}


class TestGetRedisKeyPrefix:
    """Test _get_redis_key_prefix helper function via _get_pr_updated_keys integration"""

    def test_prefix_with_trailing_colon_is_normalized(self):
        """Should normalize prefix by removing trailing colon"""
        # Test via _get_pr_updated_keys which uses _get_redis_key_prefix internally
        with patch('utils.rate_limit._get_redis_key_prefix', return_value="stg"):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 123)
            # Verify no double colon in result
            assert "::" not in prefixed
            assert prefixed == "stg:pr_updated:owner/repo:123"

    def test_prefix_without_colon_works_correctly(self):
        """Should work correctly with prefix that has no trailing colon"""
        with patch('utils.rate_limit._get_redis_key_prefix', return_value="morningai"):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 123)
            assert prefixed == "morningai:pr_updated:owner/repo:123"
            assert legacy == "pr_updated:owner/repo:123"

    def test_empty_prefix_returns_same_keys(self):
        """Should return same key for both when prefix is empty"""
        with patch('utils.rate_limit._get_redis_key_prefix', return_value=""):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 456)
            assert prefixed == legacy
            assert prefixed == "pr_updated:owner/repo:456"

    def test_none_prefix_treated_as_empty(self):
        """Should treat None prefix as empty string"""
        # _get_redis_key_prefix returns "" when prefix is None
        with patch('utils.rate_limit._get_redis_key_prefix', return_value=""):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 789)
            assert prefixed == legacy
            assert prefixed == "pr_updated:owner/repo:789"


class TestGetPrUpdatedKeys:
    """Test _get_pr_updated_keys helper function"""

    def test_returns_prefixed_and_legacy_keys_with_prefix(self):
        """Should return both prefixed and legacy keys when prefix is set"""
        with patch('utils.rate_limit._get_redis_key_prefix', return_value="stg"):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 123)
            assert prefixed == "stg:pr_updated:owner/repo:123"
            assert legacy == "pr_updated:owner/repo:123"

    def test_returns_same_keys_when_no_prefix(self):
        """Should return same key for both when no prefix is set"""
        with patch('utils.rate_limit._get_redis_key_prefix', return_value=""):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 456)
            assert prefixed == "pr_updated:owner/repo:456"
            assert legacy == "pr_updated:owner/repo:456"
            assert prefixed == legacy

    def test_handles_repo_with_special_characters(self):
        """Should handle repo names with special characters"""
        with patch('utils.rate_limit._get_redis_key_prefix', return_value="prod"):
            prefixed, legacy = _get_pr_updated_keys("org-name/repo_name", 789)
            assert prefixed == "prod:pr_updated:org-name/repo_name:789"
            assert legacy == "pr_updated:org-name/repo_name:789"

    def test_no_double_colon_with_colon_prefix(self):
        """Should not produce double colons even if prefix has trailing colon"""
        with patch('utils.rate_limit._get_redis_key_prefix', return_value="stg"):
            prefixed, legacy = _get_pr_updated_keys("owner/repo", 100)
            assert "::" not in prefixed
            assert prefixed == "stg:pr_updated:owner/repo:100"


class TestGetWithLegacyFallback:
    """Test _get_with_legacy_fallback helper function"""

    def test_returns_prefixed_value_when_exists(self):
        """Should return value from prefixed key when it exists"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: "prefixed_value" if key == "prefix:key" else None

        result = _get_with_legacy_fallback(mock_redis, "prefix:key", "key")
        assert result == "prefixed_value"
        mock_redis.get.assert_called_once_with("prefix:key")

    def test_returns_legacy_value_when_prefixed_not_found(self):
        """Should fallback to legacy key when prefixed key not found"""
        mock_redis = MagicMock()
        call_count = [0]

        def get_side_effect(key):
            call_count[0] += 1
            if key == "prefix:key":
                return None
            elif key == "key":
                return "legacy_value"
            return None

        mock_redis.get.side_effect = get_side_effect

        result = _get_with_legacy_fallback(mock_redis, "prefix:key", "key")
        assert result == "legacy_value"
        assert call_count[0] == 2

    def test_returns_none_when_neither_key_exists(self):
        """Should return None when neither key exists"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        result = _get_with_legacy_fallback(mock_redis, "prefix:key", "key")
        assert result is None

    def test_does_not_fallback_when_keys_are_same(self):
        """Should not make second call when prefixed and legacy keys are same"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        result = _get_with_legacy_fallback(mock_redis, "same_key", "same_key")
        assert result is None
        mock_redis.get.assert_called_once_with("same_key")

    def test_returns_prefixed_even_if_legacy_also_exists(self):
        """Should return prefixed value even if legacy also has value"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "prefixed_value"

        result = _get_with_legacy_fallback(mock_redis, "prefix:key", "key")
        assert result == "prefixed_value"
        mock_redis.get.assert_called_once_with("prefix:key")


# =============================================================================
# Issue #2943: North Star Alignment Tests
# =============================================================================

class TestRateLimitResult:
    """Test RateLimitResult dataclass (Issue #2943)"""

    def test_default_values(self):
        """Should have correct default values"""
        result = RateLimitResult(
            allowed=True,
            current_count=5,
            key="test:key",
            max_limit=10,
            decision="allowed"
        )
        assert result.allowed is True
        assert result.current_count == 5
        assert result.key == "test:key"
        assert result.max_limit == 10
        assert result.decision == "allowed"
        assert result.trace_id is None
        assert result.context_id is None

    def test_with_all_values(self):
        """Should store all values correctly"""
        result = RateLimitResult(
            allowed=False,
            current_count=10,
            key="test:key",
            max_limit=10,
            decision="blocked",
            trace_id="trace-123",
            context_id="pr_rate_limit:12345"
        )
        assert result.allowed is False
        assert result.current_count == 10
        assert result.decision == "blocked"
        assert result.trace_id == "trace-123"
        assert result.context_id == "pr_rate_limit:12345"


class TestAtomicRateLimitCheck:
    """Test _atomic_rate_limit_check function (Issue #2943)"""

    def test_returns_allowed_when_under_limit(self):
        """Should return allowed=True when under limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 5]  # allowed, count=5

        result = _atomic_rate_limit_check(
            r=mock_redis,
            key="test:key",
            max_limit=10,
            expiry_seconds=3600,
            trace_id="trace-123",
            context_id="test",
            operation="test_rate_limit"
        )

        assert result.allowed is True
        assert result.current_count == 5
        assert result.decision == "allowed"
        assert result.trace_id == "trace-123"

    def test_returns_blocked_when_at_limit(self):
        """Should return allowed=False when at limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 10]  # blocked, count=10

        result = _atomic_rate_limit_check(
            r=mock_redis,
            key="test:key",
            max_limit=10,
            expiry_seconds=3600,
            operation="test_rate_limit"
        )

        assert result.allowed is False
        assert result.current_count == 10
        assert result.decision == "blocked"

    def test_calls_lua_script_with_correct_args(self):
        """Should call Lua script with correct arguments"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 1]

        _atomic_rate_limit_check(
            r=mock_redis,
            key="test:key",
            max_limit=10,
            expiry_seconds=3600,
            operation="test_rate_limit"
        )

        mock_redis.eval.assert_called_once()
        call_args = mock_redis.eval.call_args[0]
        assert call_args[1] == 1  # num_keys
        assert call_args[2] == "test:key"  # key
        assert call_args[3] == 10  # max_limit
        assert call_args[4] == 3600  # expiry_seconds


class TestEmitRateLimitTelemetry:
    """Test _emit_rate_limit_telemetry function (Issue #2943)"""

    def test_logs_allowed_decision(self):
        """Should log debug message for allowed decisions"""
        result = RateLimitResult(
            allowed=True,
            current_count=5,
            key="test:key",
            max_limit=10,
            decision="allowed",
            trace_id="trace-123"
        )

        with patch('utils.rate_limit.logger') as mock_logger:
            _emit_rate_limit_telemetry(result, "test_operation")
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args
            assert "allowed" in call_args[0][0]
            assert "5/10" in call_args[0][0]

    def test_logs_blocked_decision(self):
        """Should log warning message for blocked decisions"""
        result = RateLimitResult(
            allowed=False,
            current_count=10,
            key="test:key",
            max_limit=10,
            decision="blocked",
            trace_id="trace-123"
        )

        with patch('utils.rate_limit.logger') as mock_logger:
            _emit_rate_limit_telemetry(result, "test_operation")
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "blocked" in call_args[0][0]
            assert "10/10" in call_args[0][0]

    def test_includes_extra_context(self):
        """Should include extra context in telemetry"""
        result = RateLimitResult(
            allowed=True,
            current_count=5,
            key="test:key",
            max_limit=10,
            decision="allowed"
        )

        with patch('utils.rate_limit.logger') as mock_logger:
            _emit_rate_limit_telemetry(
                result,
                "test_operation",
                extra_context={"custom_field": "custom_value"}
            )
            call_kwargs = mock_logger.debug.call_args[1]
            assert "custom_field" in call_kwargs["extra"]
            assert call_kwargs["extra"]["custom_field"] == "custom_value"


class TestCheckAndAlertRateLimitPattern:
    """Test _check_and_alert_rate_limit_pattern function (Issue #2943 Auto-Recovery)"""

    def test_increments_alert_counter_on_block(self):
        """Should increment alert counter when blocked"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1

        _check_and_alert_rate_limit_pattern(
            r=mock_redis,
            key="test:key",
            was_blocked=True,
            operation="test_rate_limit"
        )

        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()

    def test_resets_alert_counter_on_allow(self):
        """Should reset alert counter when allowed"""
        mock_redis = MagicMock()

        _check_and_alert_rate_limit_pattern(
            r=mock_redis,
            key="test:key",
            was_blocked=False,
            operation="test_rate_limit"
        )

        mock_redis.delete.assert_called_once()

    def test_emits_alert_when_threshold_exceeded(self):
        """Should emit alert when consecutive blocks exceed threshold"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = RATE_LIMIT_ALERT_THRESHOLD

        with patch('utils.rate_limit.logger') as mock_logger:
            _check_and_alert_rate_limit_pattern(
                r=mock_redis,
                key="test:key",
                was_blocked=True,
                operation="test_rate_limit"
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "consecutive blocks" in call_args[0][0]

    def test_no_alert_below_threshold(self):
        """Should not emit alert when below threshold"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = RATE_LIMIT_ALERT_THRESHOLD - 1

        with patch('utils.rate_limit.logger') as mock_logger:
            _check_and_alert_rate_limit_pattern(
                r=mock_redis,
                key="test:key",
                was_blocked=True,
                operation="test_rate_limit"
            )

            mock_logger.warning.assert_not_called()


class TestCheckDeepwikiRateLimit:
    """Test check_deepwiki_rate_limit function with atomic Lua script (Issue #2943)"""

    def test_allows_query_within_limit(self):
        """Should allow query within rate limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 5]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_deepwiki_rate_limit('code_question', max_per_minute=60)

            assert allowed is True
            assert count == 5

    def test_blocks_query_over_limit(self):
        """Should block query over rate limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 60]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_deepwiki_rate_limit('code_question', max_per_minute=60)

            assert allowed is False
            assert count == 60

    def test_handles_redis_error_gracefully(self):
        """Should fail-open on Redis error"""
        mock_redis = MagicMock()
        mock_redis.eval.side_effect = redis.ConnectionError("Connection refused")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_deepwiki_rate_limit('code_question')

            assert allowed is True
            assert count == 0


class TestCheckNotificationRateLimit:
    """Test check_notification_rate_limit function with atomic Lua script (Issue #2943)"""

    def test_allows_notification_within_limit(self):
        """Should allow notification within rate limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 10]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_notification_rate_limit('github', max_per_minute=30)

            assert allowed is True
            assert count == 10

    def test_blocks_notification_over_limit(self):
        """Should block notification over rate limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 30]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_notification_rate_limit('github', max_per_minute=30)

            assert allowed is False
            assert count == 30

    def test_handles_redis_error_gracefully(self):
        """Should fail-open on Redis error"""
        mock_redis = MagicMock()
        mock_redis.eval.side_effect = redis.ConnectionError("Connection refused")

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_notification_rate_limit('github')

            assert allowed is True
            assert count == 0


class TestBoundaryConditions:
    """Test boundary conditions for >= comparison (Issue #2943 verification)"""

    def test_pr_rate_limit_boundary_at_max_minus_one(self):
        """Should allow when current count is max - 1"""
        mock_redis = MagicMock()
        # Current is 9, max is 10, so allowed and incremented to 10
        mock_redis.eval.return_value = [1, 10]

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-1', max_per_hour=10)

            assert allowed is True
            assert count == 10

    def test_pr_rate_limit_boundary_at_exact_max(self):
        """Should block when current count equals max (>= check)"""
        mock_redis = MagicMock()
        # Current is 10, max is 10, so blocked
        mock_redis.eval.return_value = [0, 10]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_pr_rate_limit('trace-2', max_per_hour=10)

            assert allowed is False
            assert count == 10

    def test_deepwiki_rate_limit_boundary_at_exact_max(self):
        """Should block DeepWiki query when at exact limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 60]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_deepwiki_rate_limit('code_question', max_per_minute=60)

            assert allowed is False
            assert count == 60

    def test_notification_rate_limit_boundary_at_exact_max(self):
        """Should block notification when at exact limit"""
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 30]
        # Mock auto-recovery mechanism calls
        mock_redis.incr.return_value = 1

        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis

            allowed, count = check_notification_rate_limit('github', max_per_minute=30)

            assert allowed is False
            assert count == 30
