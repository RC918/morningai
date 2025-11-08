"""
Concurrency Tests for PreAuthTokenManager (JWT-based system)

Tests that verify the JWT-based PreAuthTokenManager handles concurrent requests correctly:
1. Atomic token consumption via WATCH/MULTI transactions (no double-consume race conditions)
2. TTL preservation during atomic consumption
3. Concurrent token generation produces unique JTI values
4. Thread-safe operations under load
5. Proper retry behavior on contention

These tests complement test_preauth_concurrency.py which tests the legacy preauth_token.py module.
The PreAuthTokenManager uses WATCH/MULTI transactions for atomicity, while the legacy module
uses Lua eval() scripts.
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Barrier
from typing import List, Optional, Dict
import jwt

from src.utils.pre_auth_token import PreAuthTokenManager, get_pre_auth_manager
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
def pre_auth_manager(redis_client):
    """
    Provide PreAuthTokenManager instance for tests.
    """
    return PreAuthTokenManager()


@pytest.fixture
def cleanup_jtis(redis_client):
    """
    Track and cleanup test JTIs after each test.
    """
    jtis = []
    
    def register_jti(jti: str):
        jtis.append(jti)
        return jti
    
    yield register_jti
    
    for jti in jtis:
        try:
            redis_key = f"morningai:pre_auth:jti:{jti}"
            redis_client.delete(redis_key)
        except:
            pass


class TestPreAuthManagerConcurrency:
    """Concurrency tests for PreAuthTokenManager.consume_token_atomic()"""
    
    @pytest.mark.timeout(10)
    def test_double_consume_same_token_is_atomic(self, pre_auth_manager, cleanup_jtis):
        """
        Test that concurrent attempts to consume the same token result in
        exactly one success and all others fail.
        
        This verifies the WATCH/MULTI transaction prevents race conditions.
        """
        user_id = "test-user-concurrent-123"
        email = "concurrent@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        
        payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        n_threads = 10
        barrier = Barrier(n_threads)
        results = []
        
        def consume_token():
            """Each thread waits at barrier then tries to consume"""
            barrier.wait()  # Synchronize start to maximize race condition
            success = pre_auth_manager.consume_token_atomic(jti)
            return success
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_token) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_results = [r for r in results if r is True]
        failed_results = [r for r in results if r is False]
        
        assert len(successful_results) == 1, \
            f"Expected exactly 1 successful consume, got {len(successful_results)}"
        assert len(failed_results) == n_threads - 1, \
            f"Expected {n_threads - 1} failed consumes, got {len(failed_results)}"
        
        token_info = pre_auth_manager.get_token_info(jti)
        assert token_info is not None
        assert token_info.get("consumed") == "True"
        assert "consumed_at" in token_info
        
        final_result = pre_auth_manager.consume_token_atomic(jti)
        assert final_result is False, "Token should not be consumable after first consume"
    
    @pytest.mark.timeout(10)
    def test_ttl_preserved_during_atomic_consume(self, pre_auth_manager, redis_client, cleanup_jtis):
        """
        Test that TTL is preserved when consuming a token atomically.
        
        This is a key feature of consume_token_atomic() - it preserves the original
        TTL so the consumed token data remains available for audit/logging until expiry.
        """
        user_id = "test-user-ttl-123"
        email = "ttl@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        redis_key = f"morningai:pre_auth:jti:{jti}"
        
        time.sleep(2)
        
        ttl_before = redis_client.ttl(redis_key)
        assert ttl_before > 0, "Token should have positive TTL"
        assert ttl_before < 300, "TTL should have decreased from initial 300s"
        
        success = pre_auth_manager.consume_token_atomic(jti)
        assert success is True
        
        ttl_after = redis_client.ttl(redis_key)
        assert ttl_after > 0, "Token should still have positive TTL after consumption"
        
        ttl_diff = abs(ttl_before - ttl_after)
        assert ttl_diff <= 2, f"TTL should be preserved, but changed by {ttl_diff}s"
        
        token_info = pre_auth_manager.get_token_info(jti)
        assert token_info.get("consumed") == "True"
    
    @pytest.mark.timeout(10)
    def test_generate_tokens_concurrently_unique_jti(self, pre_auth_manager, cleanup_jtis):
        """
        Test that concurrent token generation produces unique JTI values with no collisions.
        
        JTI is generated using uuid.uuid4() which should be collision-resistant.
        """
        user_id = "test-user-gen-123"
        email = "gen@example.com"
        n_threads = 20
        
        def generate_token():
            """Generate a token and extract JTI"""
            token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
            payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
            jti = payload["jti"]
            cleanup_jtis(jti)
            return (token, jti)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(generate_token) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        tokens = [r[0] for r in results]
        jtis = [r[1] for r in results]
        
        assert len(tokens) == n_threads
        assert len(jtis) == n_threads
        
        assert len(set(jtis)) == n_threads, \
            f"Expected {n_threads} unique JTIs, got {len(set(jtis))}"
        
        assert len(set(tokens)) == n_threads, \
            f"Expected {n_threads} unique tokens, got {len(set(tokens))}"
        
        for jti in jtis[:5]:
            success = pre_auth_manager.consume_token_atomic(jti)
            assert success is True
    
    @pytest.mark.timeout(10)
    def test_concurrent_consume_different_tokens(self, pre_auth_manager, cleanup_jtis):
        """
        Test that concurrent consumption of different tokens all succeed.
        
        This verifies that the WATCH/MULTI transaction doesn't create false contention
        between different tokens.
        """
        n_tokens = 10
        user_id = "test-user-multi-123"
        
        token_data = []
        for i in range(n_tokens):
            email = f"user{i}@example.com"
            token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
            payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
            jti = payload["jti"]
            cleanup_jtis(jti)
            token_data.append((jti, email))
        
        barrier = Barrier(n_tokens)
        
        def consume_specific_token(jti_email_pair):
            """Each thread consumes its own token"""
            jti, expected_email = jti_email_pair
            barrier.wait()  # Synchronize start
            success = pre_auth_manager.consume_token_atomic(jti)
            token_info = pre_auth_manager.get_token_info(jti) if success else None
            return (success, token_info, expected_email)
        
        with ThreadPoolExecutor(max_workers=n_tokens) as executor:
            futures = [executor.submit(consume_specific_token, td) for td in token_data]
            results = [future.result() for future in as_completed(futures)]
        
        for success, token_info, expected_email in results:
            assert success is True, "All different tokens should consume successfully"
            assert token_info is not None
            assert token_info.get("consumed") == "True"
            assert token_info.get("email") == expected_email
    
    @pytest.mark.timeout(10)
    def test_consume_under_load_no_deadlock(self, pre_auth_manager, cleanup_jtis):
        """
        Test that the system handles high concurrent load without deadlocks or timeouts.
        
        Mix of same-token and different-token consumption with retry logic.
        """
        n_tokens = 5
        n_threads = 20
        user_id = "test-user-load-123"
        
        jtis = []
        for i in range(n_tokens):
            email = f"load{i}@example.com"
            token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
            payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
            jti = payload["jti"]
            cleanup_jtis(jti)
            jtis.append(jti)
        
        jti_assignments = [jtis[i % n_tokens] for i in range(n_threads)]
        
        barrier = Barrier(n_threads)
        
        def consume_assigned_token(jti):
            """Try to consume assigned token"""
            barrier.wait()
            success = pre_auth_manager.consume_token_atomic(jti)
            return success
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_assigned_token, j) for j in jti_assignments]
            results = [future.result() for future in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"Test took too long ({elapsed}s), possible deadlock"
        
        successful_results = [r for r in results if r is True]
        assert len(successful_results) == n_tokens, \
            f"Expected {n_tokens} successful consumes, got {len(successful_results)}"
    
    @pytest.mark.timeout(10)
    def test_retry_on_contention(self, pre_auth_manager, cleanup_jtis):
        """
        Test that consume_token_atomic() properly retries on WatchError contention.
        
        This test verifies the retry mechanism works by creating high contention
        on a single token.
        """
        user_id = "test-user-retry-123"
        email = "retry@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        n_threads = 15
        barrier = Barrier(n_threads)
        
        def consume_with_contention():
            """Try to consume with high contention"""
            barrier.wait()
            success = pre_auth_manager.consume_token_atomic(jti, max_retries=5)
            return success
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_with_contention) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_results = [r for r in results if r is True]
        
        assert len(successful_results) == 1, \
            f"Expected exactly 1 successful consume even with retries, got {len(successful_results)}"


class TestPreAuthManagerAtomicityEdgeCases:
    """Edge case tests for PreAuthTokenManager atomic operations"""
    
    @pytest.mark.timeout(5)
    def test_consume_nonexistent_token_concurrent(self, pre_auth_manager):
        """
        Test that concurrent attempts to consume a non-existent JTI
        all fail gracefully without errors.
        """
        fake_jti = "00000000-0000-0000-0000-000000000000"
        n_threads = 5
        barrier = Barrier(n_threads)
        
        def consume_fake():
            barrier.wait()
            return pre_auth_manager.consume_token_atomic(fake_jti)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_fake) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        assert all(r is False for r in results)
    
    @pytest.mark.timeout(5)
    def test_consume_already_consumed_token_concurrent(self, pre_auth_manager, cleanup_jtis):
        """
        Test that concurrent attempts to consume an already-consumed token
        all fail correctly.
        """
        user_id = "test-user-consumed-123"
        email = "consumed@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        first_consume = pre_auth_manager.consume_token_atomic(jti)
        assert first_consume is True
        
        n_threads = 5
        barrier = Barrier(n_threads)
        
        def consume_consumed():
            barrier.wait()
            return pre_auth_manager.consume_token_atomic(jti)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_consumed) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        assert all(r is False for r in results), \
            "All attempts to consume already-consumed token should fail"
    
    @pytest.mark.timeout(10)
    def test_verify_and_consume_workflow_concurrent(self, pre_auth_manager, cleanup_jtis):
        """
        Test the typical workflow: verify_token() followed by consume_token_atomic()
        under concurrent access.
        
        This simulates the real usage pattern in routes.
        """
        user_id = "test-user-workflow-123"
        email = "workflow@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        payload = jwt.decode(token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        n_threads = 10
        barrier = Barrier(n_threads)
        
        def verify_and_consume():
            """Typical workflow: verify then consume"""
            barrier.wait()
            
            verified_payload = pre_auth_manager.verify_token(token)
            if not verified_payload:
                return (False, "verify_failed")
            
            success = pre_auth_manager.consume_token_atomic(jti)
            return (success, "consumed" if success else "already_consumed")
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(verify_and_consume) for _ in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        verify_failures = [r for r in results if r[1] == "verify_failed"]
        assert len(verify_failures) == 0, "All threads should verify token successfully"
        
        consume_successes = [r for r in results if r[0] is True]
        assert len(consume_successes) == 1, \
            f"Expected exactly 1 successful consume, got {len(consume_successes)}"
        
        already_consumed = [r for r in results if r[1] == "already_consumed"]
        assert len(already_consumed) == n_threads - 1


class TestPreAuthManagerScopeEnforcement:
    """Tests for scope enforcement under concurrent access"""
    
    @pytest.mark.timeout(10)
    def test_concurrent_consume_different_scopes(self, pre_auth_manager, cleanup_jtis):
        """
        Test that tokens with different scopes can be consumed concurrently
        without interference.
        """
        user_id = "test-user-scope-123"
        email = "scope@example.com"
        
        enroll_token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        challenge_token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        
        enroll_payload = jwt.decode(enroll_token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        challenge_payload = jwt.decode(challenge_token, pre_auth_manager.jwt_secret, algorithms=["HS256"])
        
        enroll_jti = enroll_payload["jti"]
        challenge_jti = challenge_payload["jti"]
        
        cleanup_jtis(enroll_jti)
        cleanup_jtis(challenge_jti)
        
        n_threads = 10
        barrier = Barrier(n_threads)
        
        def consume_by_index(index):
            barrier.wait()
            jti = enroll_jti if index % 2 == 0 else challenge_jti
            return pre_auth_manager.consume_token_atomic(jti)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(consume_by_index, i) for i in range(n_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_results = [r for r in results if r is True]
        assert len(successful_results) == 2, \
            f"Expected 2 successful consumes (1 per scope), got {len(successful_results)}"
        
        enroll_info = pre_auth_manager.get_token_info(enroll_jti)
        challenge_info = pre_auth_manager.get_token_info(challenge_jti)
        
        assert enroll_info.get("consumed") == "True"
        assert enroll_info.get("scope") == "enroll"
        assert challenge_info.get("consumed") == "True"
        assert challenge_info.get("scope") == "challenge"
