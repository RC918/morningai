"""
Concurrency utilities for Memory v2.

Issue #3998: Token bucket algorithm for LLM rate limiting
Issue #3999: Separate concerns (SRP) for LLMSummarizer

Blueprint Section 5.1: Memory v2 - Infrastructure Layer

This module provides reusable concurrency primitives:
- TokenBucketRateLimiter: Smooth rate limiting with burst support
- ConcurrencyManager: Semaphore-based concurrency control
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TokenBucketConfig:
    """Configuration for token bucket rate limiter.

    Args:
        capacity: Maximum number of tokens in the bucket (burst capacity)
        refill_rate: Tokens added per second
        initial_tokens: Starting tokens (defaults to capacity)
    """
    capacity: float = 10.0
    refill_rate: float = 5.0
    initial_tokens: Optional[float] = None

    def __post_init__(self):
        if self.initial_tokens is None:
            self.initial_tokens = self.capacity


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for smooth request distribution.

    Issue #3998: Implement token bucket algorithm for LLM rate limiting.

    The token bucket algorithm:
    1. Bucket has a maximum capacity of tokens
    2. Tokens are added at a fixed rate (refill_rate per second)
    3. Each request consumes one token
    4. If no tokens available, request waits until tokens are available

    Benefits over simple time-sleep:
    - Allows controlled bursts (up to bucket capacity)
    - Provides smoother request distribution
    - More predictable behavior under high concurrency

    Usage:
        limiter = TokenBucketRateLimiter(capacity=10, refill_rate=5)

        # Synchronous
        limiter.acquire()

        # Asynchronous
        await limiter.acquire_async()
    """

    def __init__(
        self,
        capacity: float = 10.0,
        refill_rate: float = 5.0,
        initial_tokens: Optional[float] = None,
    ):
        """
        Initialize token bucket rate limiter.

        Args:
            capacity: Maximum tokens in bucket (burst capacity)
            refill_rate: Tokens added per second
            initial_tokens: Starting tokens (defaults to capacity)

        Thread-safety: Uses a single threading.Lock for all access to shared
        state, ensuring correctness in both sync and async contexts.
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = initial_tokens if initial_tokens is not None else capacity
        self._last_refill_time = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time. MUST be called within lock."""
        now = time.monotonic()
        elapsed = now - self._last_refill_time
        tokens_to_add = elapsed * self.refill_rate
        self._tokens = min(self.capacity, self._tokens + tokens_to_add)
        self._last_refill_time = now

    def _calculate_wait_time(self) -> float:
        """Calculate time to wait for one token. MUST be called within lock."""
        if self._tokens >= 1.0:
            return 0.0
        tokens_needed = 1.0 - self._tokens
        return tokens_needed / self.refill_rate

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token (synchronous, blocking).

        Args:
            timeout: Maximum time to wait for token (None = wait forever)

        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.monotonic()

        while True:
            with self._lock:
                self._refill()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

                wait_time = self._calculate_wait_time()

            if timeout is not None:
                elapsed = time.monotonic() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            time.sleep(wait_time)

    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token (asynchronous, non-blocking).

        Args:
            timeout: Maximum time to wait for token (None = wait forever)

        Returns:
            True if token acquired, False if timeout

        Note: Uses threading.Lock for correctness across sync/async contexts.
        The critical section is very short (no I/O), so blocking is minimal.
        """
        start_time = time.monotonic()

        while True:
            with self._lock:
                self._refill()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

                wait_time = self._calculate_wait_time()

            if timeout is not None:
                elapsed = time.monotonic() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            await asyncio.sleep(wait_time)

    def try_acquire(self) -> bool:
        """
        Try to acquire a token without waiting.

        Returns:
            True if token acquired, False if no tokens available
        """
        with self._lock:
            self._refill()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    async def try_acquire_async(self) -> bool:
        """
        Try to acquire a token without waiting (async version).

        Returns:
            True if token acquired, False if no tokens available
        """
        with self._lock:
            self._refill()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    @property
    def available_tokens(self) -> float:
        """Get current number of available tokens (thread-safe)."""
        with self._lock:
            self._refill()
            return self._tokens

    def get_stats(self) -> dict:
        """Get rate limiter statistics (thread-safe)."""
        with self._lock:
            self._refill()
            return {
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "available_tokens": self._tokens,
                "utilization": 1.0 - (self._tokens / self.capacity),
            }


class ConcurrencyManager:
    """
    Semaphore-based concurrency manager.

    Issue #3999: Separate concerns (SRP) for LLMSummarizer.

    Provides a reusable concurrency control mechanism that can be
    shared across multiple components.

    Usage:
        manager = ConcurrencyManager(max_concurrency=5)

        async with manager.acquire():
            # Do work with limited concurrency
            pass
    """

    def __init__(self, max_concurrency: int = 5):
        """
        Initialize concurrency manager.

        Args:
            max_concurrency: Maximum concurrent operations allowed
        """
        self.max_concurrency = max_concurrency
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._active_count = 0
        self._total_acquired = 0
        self._lock = asyncio.Lock()

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore (lazy initialization)."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)
        return self._semaphore

    async def acquire(self):
        """
        Acquire a concurrency slot.

        Returns an async context manager for use with 'async with'.
        """
        return _ConcurrencySlot(self)

    async def _acquire_slot(self) -> None:
        """Internal: acquire a slot.

        Handles task cancellation to prevent semaphore slot leaks.
        """
        await self._get_semaphore().acquire()
        try:
            async with self._lock:
                self._active_count += 1
                self._total_acquired += 1
        except asyncio.CancelledError:
            self._get_semaphore().release()
            raise

    async def _release_slot(self) -> None:
        """Internal: release a slot."""
        async with self._lock:
            self._active_count -= 1
        self._get_semaphore().release()

    @property
    def active_count(self) -> int:
        """Get number of currently active operations."""
        return self._active_count

    def get_stats(self) -> dict:
        """Get concurrency manager statistics."""
        return {
            "max_concurrency": self.max_concurrency,
            "active_count": self._active_count,
            "total_acquired": self._total_acquired,
            "available_slots": self.max_concurrency - self._active_count,
        }


class _ConcurrencySlot:
    """Async context manager for concurrency slot."""

    def __init__(self, manager: ConcurrencyManager):
        self._manager = manager

    async def __aenter__(self):
        await self._manager._acquire_slot()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._manager._release_slot()
        return False


def create_llm_rate_limiter(
    requests_per_second: float = 5.0,
    burst_capacity: Optional[float] = None,
) -> TokenBucketRateLimiter:
    """
    Factory function to create a rate limiter configured for LLM APIs.

    Args:
        requests_per_second: Target request rate
        burst_capacity: Maximum burst size (defaults to 2x rate)

    Returns:
        Configured TokenBucketRateLimiter
    """
    if burst_capacity is None:
        burst_capacity = requests_per_second * 2

    return TokenBucketRateLimiter(
        capacity=burst_capacity,
        refill_rate=requests_per_second,
    )
