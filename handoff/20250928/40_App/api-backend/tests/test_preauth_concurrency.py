"""
Concurrency Tests for Pre-Auth Token System

Tests that verify the pre-auth token system handles concurrent requests correctly:
1. Atomic token consumption (no double-consume race conditions)
2. Concurrent token generation produces unique tokens
3. Thread-safe operations under load

These tests use threading to simulate real-world concurrent access patterns
and verify that the system maintains correctness guarantees.
"""

import pytest
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Barrier
from typing import List, Optional, Dict
from unittest.mock import patch

from src.utils.preauth_token import (
    generate_preauth_token,
    validate_and_consume_preauth_token,
)
from src.utils.redis_client import get_redis_client


@pytest.fixture(scope="module")
def redis_client():
    """
    Provide Redis client for tests, skip if Redis is unavailable.
    """
    try:
        client = get_redis_client()
        client.ping()
        yield client
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def cleanup_tokens(redis_client):
    """
    Track and cleanup test tokens after each test.
    """
    tokens = []
    
    def register_token(token: str):
        tokens.append(token)
        return token
    
    yield register_token
    
    for token in tokens:
        try:
            redis_client.delete(f"preauth:{token}")
        except:
            pass


class TestPreAuthConcurrency:
    """Concurrency tests for pre-auth token system"""
    
    @pytest.mark.timeout(10)
    def test_double_consume_same_token_is_atomic(self, redis_client, cleanup_tokens):
        """
        Test that concurrent attempts to consume the same token result in
        exactly one success and all others fail.
        
        This verifies the atomic GET-and-DELETE operation prevents race conditions.
        """
        user_id = "test-user-concurrent-123"
        email = "concurrent@example.com"
        token = generate_preauth_token(user_id, email, ttl=60)
        cleanup_tokens(token)
        
        n_threads = 10
        barrier = Barrier(n_threads)
        results = []
        
        def consume_token():
            """Each thread waits at barrier then tries to consume"""
            barrier.wait()  # Synchronize start to maximize race condition
            result = validate_and_consume_preauth_token(token)
            return result
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_token) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_results = [r for r in results if r is not None]
        failed_results = [r for r in results if r is None]
        
        assert len(successful_results) == 1, \
            f"Expected exactly 1 successful consume, got {len(successful_results)}"
        assert len(failed_results) == n_threads - 1, \
            f"Expected {n_threads - 1} failed consumes, got {len(failed_results)}"
        
        success = successful_results[0]
        assert success['id'] == user_id
        assert success['email'] == email
        
        final_result = validate_and_consume_preauth_token(token)
        assert final_result is None, "Token should not be consumable after first consume"
    
    @pytest.mark.timeout(10)
    def test_generate_tokens_concurrently_unique(self, redis_client, cleanup_tokens):
        """
        Test that concurrent token generation for the same user produces
        unique tokens with no collisions.
        """
        user_id = "test-user-gen-123"
        email = "gen@example.com"
        n_threads = 20
        
        def generate_token():
            """Generate a token"""
            token = generate_preauth_token(user_id, email, ttl=60)
            cleanup_tokens(token)
            return token
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(generate_token) for _ in range(n_threads)]
            tokens = [future.result() for future in as_completed(futures)]
        
        assert len(tokens) == n_threads
        assert len(set(tokens)) == n_threads, \
            f"Expected {n_threads} unique tokens, got {len(set(tokens))}"
        
        for token in tokens[:5]:  # Test a sample to avoid cleanup issues
            result = validate_and_consume_preauth_token(token)
            assert result is not None
            assert result['id'] == user_id
            assert result['email'] == email
    
    @pytest.mark.timeout(10)
    def test_concurrent_consume_different_tokens(self, redis_client, cleanup_tokens):
        """
        Test that concurrent consumption of different tokens all succeed.
        This verifies that the atomic operation doesn't create false contention.
        """
        n_tokens = 10
        user_id = "test-user-multi-123"
        
        tokens = []
        for i in range(n_tokens):
            email = f"user{i}@example.com"
            token = generate_preauth_token(user_id, email, ttl=60)
            cleanup_tokens(token)
            tokens.append((token, email))
        
        barrier = Barrier(n_tokens)
        
        def consume_specific_token(token_email_pair):
            """Each thread consumes its own token"""
            token, expected_email = token_email_pair
            barrier.wait()  # Synchronize start
            result = validate_and_consume_preauth_token(token)
            return (result, expected_email)
        
        with ThreadPoolExecutor(max_workers=n_tokens) as executor:
            futures = [executor.submit(consume_specific_token, te) for te in tokens]
            results = [future.result() for future in as_completed(futures)]
        
        for result, expected_email in results:
            assert result is not None, "All different tokens should consume successfully"
            assert result['id'] == user_id
            assert result['email'] == expected_email
    
    @pytest.mark.timeout(10)
    def test_consume_under_load_no_deadlock(self, redis_client, cleanup_tokens):
        """
        Test that the system handles high concurrent load without deadlocks
        or timeouts. Mix of same-token and different-token consumption.
        """
        n_tokens = 5
        n_threads = 20
        user_id = "test-user-load-123"
        
        tokens = []
        for i in range(n_tokens):
            email = f"load{i}@example.com"
            token = generate_preauth_token(user_id, email, ttl=60)
            cleanup_tokens(token)
            tokens.append(token)
        
        token_assignments = [tokens[i % n_tokens] for i in range(n_threads)]
        
        barrier = Barrier(n_threads)
        
        def consume_assigned_token(token):
            """Try to consume assigned token"""
            barrier.wait()
            result = validate_and_consume_preauth_token(token)
            return result
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_assigned_token, t) for t in token_assignments]
            results = [future.result() for future in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"Test took too long ({elapsed}s), possible deadlock"
        
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) == n_tokens, \
            f"Expected {n_tokens} successful consumes, got {len(successful_results)}"
    
    @pytest.mark.timeout(10)
    def test_token_expiry_during_concurrent_access(self, redis_client, cleanup_tokens):
        """
        Test that expired tokens are properly rejected even under concurrent access.
        """
        user_id = "test-user-expiry-123"
        email = "expiry@example.com"
        
        token = generate_preauth_token(user_id, email, ttl=1)
        cleanup_tokens(token)
        
        time.sleep(1.5)
        
        n_threads = 5
        barrier = Barrier(n_threads)
        
        def consume_expired():
            barrier.wait()
            return validate_and_consume_preauth_token(token)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_expired) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        assert all(r is None for r in results), \
            "All attempts to consume expired token should fail"


class TestPreAuthAtomicityEdgeCases:
    """Edge case tests for atomic operations"""
    
    @pytest.mark.timeout(5)
    def test_consume_nonexistent_token_concurrent(self, redis_client):
        """
        Test that concurrent attempts to consume a non-existent token
        all fail gracefully without errors.
        """
        fake_token = "nonexistent-token-xyz123"
        n_threads = 5
        barrier = Barrier(n_threads)
        
        def consume_fake():
            barrier.wait()
            return validate_and_consume_preauth_token(fake_token)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_fake) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        assert all(r is None for r in results)
    
    @pytest.mark.timeout(5)
    def test_consume_empty_token_concurrent(self, redis_client):
        """
        Test that concurrent attempts to consume empty/None token
        fail gracefully.
        """
        n_threads = 5
        barrier = Barrier(n_threads)
        
        def consume_empty():
            barrier.wait()
            return validate_and_consume_preauth_token("")
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_empty) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        assert all(r is None for r in results)
