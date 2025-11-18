"""
Tests for utils/retry.py

Phase 0: Test coverage improvement (41% -> 80%+)
Focus: Deterministic unit tests without external dependencies
"""
import pytest
import time
import sys
import os
from unittest.mock import Mock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.retry import (
    retry_with_backoff,
    retry_operation,
    RetryConfig,
    DEFAULT_RETRY_CONFIG,
    DB_RETRY_CONFIG,
    API_RETRY_CONFIG
)


class TestRetryWithBackoffDecorator:
    """Test retry_with_backoff decorator"""
    
    def test_successful_operation_no_retry(self):
        """Should return immediately on success"""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_exception(self):
        """Should retry on exception"""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Should raise exception after max retries"""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            always_fails()
        
        assert call_count == 3
    
    def test_exponential_backoff(self):
        """Should apply exponential backoff"""
        delays = []
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def track_delays():
            delays.append(time.time())
            if len(delays) < 4:
                raise ValueError("Retry")
            return "success"
        
        result = track_delays()
        assert result == "success"
        assert len(delays) == 4
        
        if len(delays) >= 3:
            delay1 = delays[1] - delays[0]
            delay2 = delays[2] - delays[1]
            assert delay2 > delay1
    
    def test_specific_exceptions_only(self):
        """Should only catch specified exceptions"""
        @retry_with_backoff(max_retries=2, initial_delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("Wrong exception type")
        
        with pytest.raises(TypeError, match="Wrong exception type"):
            raises_type_error()
    
    def test_on_retry_callback(self):
        """Should call on_retry callback"""
        retry_calls = []
        
        def on_retry_handler(exception, attempt, delay):
            retry_calls.append({
                'exception': str(exception),
                'attempt': attempt,
                'delay': delay
            })
        
        @retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            on_retry=on_retry_handler
        )
        def flaky_func():
            if len(retry_calls) < 2:
                raise ValueError("Retry")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0]['attempt'] == 1
        assert retry_calls[1]['attempt'] == 2
    
    def test_preserves_function_metadata(self):
        """Should preserve original function metadata"""
        @retry_with_backoff(max_retries=3)
        def documented_func():
            """This is a documented function"""
            return "result"
        
        assert documented_func.__name__ == "documented_func"
        assert "documented function" in documented_func.__doc__


class TestRetryOperation:
    """Test retry_operation functional interface"""
    
    def test_successful_operation_no_retry(self):
        """Should return immediately on success"""
        mock_op = Mock(return_value="success")
        
        result = retry_operation(mock_op, max_retries=3)
        
        assert result == "success"
        assert mock_op.call_count == 1
    
    def test_retry_on_exception(self):
        """Should retry on exception"""
        mock_op = Mock(side_effect=[
            ValueError("Error 1"),
            ValueError("Error 2"),
            "success"
        ])
        
        result = retry_operation(
            mock_op,
            max_retries=3,
            initial_delay=0.01
        )
        
        assert result == "success"
        assert mock_op.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Should raise exception after max retries"""
        mock_op = Mock(side_effect=ValueError("Permanent error"))
        
        with pytest.raises(ValueError, match="Permanent error"):
            retry_operation(
                mock_op,
                max_retries=2,
                initial_delay=0.01
            )
        
        assert mock_op.call_count == 3
    
    def test_exponential_backoff(self):
        """Should apply exponential backoff"""
        call_times = []
        
        def track_time():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise ValueError("Retry")
            return "success"
        
        result = retry_operation(
            track_time,
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0
        )
        
        assert result == "success"
        assert len(call_times) == 4
        
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay2 > delay1
    
    def test_specific_exceptions_only(self):
        """Should only catch specified exceptions"""
        mock_op = Mock(side_effect=TypeError("Wrong type"))
        
        with pytest.raises(TypeError, match="Wrong type"):
            retry_operation(
                mock_op,
                max_retries=2,
                initial_delay=0.01,
                exceptions=(ValueError,)
            )
        
        assert mock_op.call_count == 1
    
    def test_custom_operation_name(self):
        """Should use custom operation name in logs"""
        mock_op = Mock(side_effect=ValueError("Error"))
        
        with patch('utils.retry.logger') as mock_logger:
            with pytest.raises(ValueError):
                retry_operation(
                    mock_op,
                    max_retries=1,
                    initial_delay=0.01,
                    operation_name="custom_operation"
                )
            
            warning_calls = [c for c in mock_logger.warning.call_args_list]
            assert len(warning_calls) > 0
            assert "custom_operation" in str(warning_calls[0])


class TestRetryConfig:
    """Test RetryConfig class"""
    
    def test_default_initialization(self):
        """Should initialize with default values"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.backoff_factor == 2.0
        assert config.max_delay == 60.0
    
    def test_custom_initialization(self):
        """Should initialize with custom values"""
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.5,
            backoff_factor=1.5,
            max_delay=30.0
        )
        
        assert config.max_retries == 5
        assert config.initial_delay == 0.5
        assert config.backoff_factor == 1.5
        assert config.max_delay == 30.0
    
    def test_get_delay_exponential(self):
        """Should calculate exponential delay"""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_factor=2.0,
            max_delay=100.0
        )
        
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 8.0
    
    def test_get_delay_max_cap(self):
        """Should cap delay at max_delay"""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_factor=2.0,
            max_delay=5.0
        )
        
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 5.0
        assert config.get_delay(10) == 5.0
    
    def test_get_delay_different_backoff_factor(self):
        """Should handle different backoff factors"""
        config = RetryConfig(
            initial_delay=2.0,
            backoff_factor=3.0,
            max_delay=100.0
        )
        
        assert config.get_delay(0) == 2.0
        assert config.get_delay(1) == 6.0
        assert config.get_delay(2) == 18.0


class TestPredefinedConfigs:
    """Test predefined retry configurations"""
    
    def test_default_retry_config(self):
        """Should have correct default config values"""
        assert DEFAULT_RETRY_CONFIG.max_retries == 3
        assert DEFAULT_RETRY_CONFIG.initial_delay == 1.0
        assert DEFAULT_RETRY_CONFIG.backoff_factor == 2.0
        assert DEFAULT_RETRY_CONFIG.max_delay == 30.0
    
    def test_db_retry_config(self):
        """Should have correct DB config values"""
        assert DB_RETRY_CONFIG.max_retries == 5
        assert DB_RETRY_CONFIG.initial_delay == 0.5
        assert DB_RETRY_CONFIG.backoff_factor == 1.5
        assert DB_RETRY_CONFIG.max_delay == 10.0
    
    def test_api_retry_config(self):
        """Should have correct API config values"""
        assert API_RETRY_CONFIG.max_retries == 3
        assert API_RETRY_CONFIG.initial_delay == 2.0
        assert API_RETRY_CONFIG.backoff_factor == 2.0
        assert API_RETRY_CONFIG.max_delay == 60.0


class TestLogging:
    """Test logging behavior"""
    
    def test_logs_warning_on_retry(self):
        """Should log warning on retry"""
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def flaky_func():
            if not hasattr(flaky_func, 'called'):
                flaky_func.called = True
                raise ValueError("Retry me")
            return "success"
        
        with patch('utils.retry.logger') as mock_logger:
            result = flaky_func()
            assert result == "success"
            assert mock_logger.warning.called
    
    def test_logs_error_on_final_failure(self):
        """Should log error on final failure"""
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def always_fails():
            raise ValueError("Always fails")
        
        with patch('utils.retry.logger') as mock_logger:
            with pytest.raises(ValueError):
                always_fails()
            
            assert mock_logger.error.called
            error_call = mock_logger.error.call_args
            assert "failed after" in str(error_call)


class TestEdgeCases:
    """Test edge cases"""
    
    def test_zero_retries(self):
        """Should work with zero retries"""
        call_count = 0
        
        @retry_with_backoff(max_retries=0, initial_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return "success"
        
        with pytest.raises(ValueError):
            func()
        
        assert call_count == 1
    
    def test_very_small_delay(self):
        """Should handle very small delays"""
        @retry_with_backoff(max_retries=2, initial_delay=0.001)
        def func():
            if not hasattr(func, 'called'):
                func.called = True
                raise ValueError("Retry")
            return "success"
        
        result = func()
        assert result == "success"
    
    def test_lambda_function(self):
        """Should work with lambda functions"""
        counter = {'value': 0}
        
        def operation():
            counter['value'] += 1
            if counter['value'] < 3:
                raise ValueError("Retry")
            return "success"
        
        result = retry_operation(
            operation,
            max_retries=3,
            initial_delay=0.01
        )
        
        assert result == "success"
        assert counter['value'] == 3
