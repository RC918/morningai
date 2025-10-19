#!/usr/bin/env python3
"""
Retry utilities for handling transient failures

Provides decorators and functions for implementing retry logic with exponential backoff.
"""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
):
    """
    Decorator for retrying a function with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        exceptions: Tuple of exception types to catch (default: all exceptions)
        on_retry: Optional callback function(exception, attempt, delay) called before each retry
    
    Returns:
        Decorator function
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=0.5)
        def flaky_operation():
            return api_call()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries",
                            extra={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "error": str(e)
                            }
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay}s",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_retries + 1,
                            "delay": delay,
                            "error": str(e)
                        }
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1, delay)
                    
                    time.sleep(delay)
                    delay *= backoff_factor
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_operation(
    operation: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    operation_name: str = "operation"
) -> any:
    """
    Retry a function call with exponential backoff (functional interface)
    
    Args:
        operation: Function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        exceptions: Tuple of exception types to catch (default: all exceptions)
        operation_name: Name for logging purposes (default: "operation")
    
    Returns:
        Result of the operation
    
    Raises:
        Last exception if all retries fail
    
    Example:
        result = retry_operation(
            lambda: api.call_endpoint(),
            max_retries=3,
            exceptions=(ConnectionError, TimeoutError)
        )
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except exceptions as e:
            last_exception = e
            
            if attempt >= max_retries:
                logger.error(
                    f"{operation_name} failed after {max_retries} retries",
                    extra={
                        "operation": operation_name,
                        "attempts": attempt + 1,
                        "error": str(e)
                    }
                )
                raise
            
            logger.warning(
                f"{operation_name} failed (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {delay}s",
                extra={
                    "operation": operation_name,
                    "attempt": attempt + 1,
                    "max_attempts": max_retries + 1,
                    "delay": delay,
                    "error": str(e)
                }
            )
            
            time.sleep(delay)
            delay *= backoff_factor
    
    raise last_exception


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    max_delay=30.0
)


DB_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=0.5,
    backoff_factor=1.5,
    max_delay=10.0
)


API_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=2.0,
    backoff_factor=2.0,
    max_delay=60.0
)
