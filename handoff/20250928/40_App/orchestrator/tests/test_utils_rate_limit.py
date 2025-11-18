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
    get_pr_count_last_hour
)


class TestCheckPRRateLimit:
    """Test check_pr_rate_limit function"""
    
    def test_allows_pr_within_limit(self):
        """Should allow PR creation within rate limit"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 5
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            allowed, count = check_pr_rate_limit('trace-123', max_per_hour=10)
            
            assert allowed is True
            assert count == 5
            assert mock_redis.incr.called
            assert mock_redis.expire.called
    
    def test_blocks_pr_over_limit(self):
        """Should block PR creation when over rate limit"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 12
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            allowed, count = check_pr_rate_limit('trace-456', max_per_hour=10)
            
            assert allowed is False
            assert count == 12
    
    def test_uses_redis_url_when_provided(self):
        """Should use Redis URL when provided"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 3
        
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
        mock_redis.incr.return_value = 2
        
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
    
    def test_sets_key_expiration(self):
        """Should set key expiration to 1 hour"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            check_pr_rate_limit('trace-def')
            
            mock_redis.expire.assert_called_once()
            call_args = mock_redis.expire.call_args
            assert call_args[0][1] == 3600
    
    def test_uses_current_hour_in_key(self):
        """Should use current hour in Redis key"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        
        with patch('redis.Redis') as mock_redis_class, \
             patch('time.time', return_value=1700000000):
            mock_redis_class.return_value = mock_redis
            
            check_pr_rate_limit('trace-ghi')
            
            expected_hour = int(1700000000 / 3600)
            expected_key = f"orchestrator:pr_count:{expected_hour}"
            mock_redis.incr.assert_called_once_with(expected_key)
    
    def test_handles_redis_connection_error(self):
        """Should allow PR creation when Redis is unavailable"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.side_effect = redis.ConnectionError("Connection refused")
            
            allowed, count = check_pr_rate_limit('trace-jkl')
            
            assert allowed is True
            assert count == 0
    
    def test_handles_redis_operation_error(self):
        """Should allow PR creation on Redis operation error"""
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = redis.RedisError("Operation failed")
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            allowed, count = check_pr_rate_limit('trace-mno')
            
            assert allowed is True
            assert count == 0
    
    def test_handles_unexpected_exception(self):
        """Should allow PR creation on unexpected exception"""
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = Exception("Unexpected error")
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            allowed, count = check_pr_rate_limit('trace-pqr')
            
            assert allowed is True
            assert count == 0
    
    def test_custom_max_per_hour(self):
        """Should respect custom max_per_hour parameter"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 18
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            allowed, count = check_pr_rate_limit('trace-stu', max_per_hour=20)
            
            assert allowed is True
            assert count == 18
            
            mock_redis.incr.return_value = 22
            allowed, count = check_pr_rate_limit('trace-vwx', max_per_hour=20)
            
            assert allowed is False
            assert count == 22
    
    def test_boundary_condition_at_limit(self):
        """Should allow PR at exact limit"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 10
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            allowed, count = check_pr_rate_limit('trace-yz', max_per_hour=10)
            
            assert allowed is True
            assert count == 10
    
    def test_boundary_condition_over_limit(self):
        """Should block PR at limit + 1"""
        mock_redis = MagicMock()
        mock_redis.incr.return_value = 11
        
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
    """Test integration scenarios"""
    
    def test_sequential_pr_creation(self):
        """Should track sequential PR creation correctly"""
        mock_redis = MagicMock()
        counts = [1, 2, 3, 4, 5]
        mock_redis.incr.side_effect = counts
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            for i, expected_count in enumerate(counts):
                allowed, count = check_pr_rate_limit(f'trace-{i}', max_per_hour=10)
                assert allowed is True
                assert count == expected_count
    
    def test_rate_limit_enforcement(self):
        """Should enforce rate limit correctly"""
        mock_redis = MagicMock()
        
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            
            mock_redis.incr.return_value = 10
            allowed, count = check_pr_rate_limit('trace-1', max_per_hour=10)
            assert allowed is True
            
            mock_redis.incr.return_value = 11
            allowed, count = check_pr_rate_limit('trace-2', max_per_hour=10)
            assert allowed is False
            
            mock_redis.incr.return_value = 12
            allowed, count = check_pr_rate_limit('trace-3', max_per_hour=10)
            assert allowed is False
