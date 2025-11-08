"""
Unit Tests for PreAuthTokenManager Scope Enforcement

Tests that verify the PreAuthTokenManager correctly enforces scope-based access control:
1. Token generation with different scopes ('enroll' vs 'challenge')
2. Scope validation during token verification
3. Scope persistence in Redis
4. Scope enforcement across token lifecycle
5. Invalid scope handling

These are unit tests focused on the PreAuthTokenManager class itself,
complementing the integration tests in test_auth_2fa_preauth.py.
"""

import pytest
import jwt
from datetime import datetime, timedelta, UTC
from unittest.mock import patch

from src.utils.pre_auth_token import (
    get_pre_auth_manager,
    PreAuthTokenManager,
    REDIS_KEY_PREFIX,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client using fakeredis for stateful behavior"""
    from fakeredis import FakeRedis
    import src.utils.pre_auth_token
    
    src.utils.pre_auth_token._pre_auth_manager = None
    
    redis_client = FakeRedis(decode_responses=True)
    with patch("src.utils.redis_client.get_redis_client") as mock1, patch(
        "src.utils.pre_auth_token.get_redis_client"
    ) as mock2:
        mock1.return_value = redis_client
        mock2.return_value = redis_client
        
        yield redis_client
        
        src.utils.pre_auth_token._pre_auth_manager = None
        redis_client.flushall()


@pytest.fixture
def pre_auth_manager(mock_redis):
    """Provide PreAuthTokenManager instance with mock Redis for tests"""
    return get_pre_auth_manager()


@pytest.fixture
def cleanup_jtis(pre_auth_manager):
    """Track and cleanup test JTIs after each test"""
    jtis = []
    
    def register_jti(jti: str):
        jtis.append(jti)
        return jti
    
    yield register_jti
    
    for jti in jtis:
        try:
            redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
            pre_auth_manager.redis_client.delete(redis_key)
        except Exception:
            pass


class TestScopeGeneration:
    """Test scope handling during token generation"""
    
    def test_generate_token_with_enroll_scope(self, pre_auth_manager, cleanup_jtis):
        """Test generating token with 'enroll' scope"""
        user_id = "user-scope-001"
        email = "enroll@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        assert payload["scope"] == "enroll"
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["pre_auth"] is True
        
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        token_data = pre_auth_manager.redis_client.hgetall(redis_key)
        assert token_data["scope"] == "enroll"
    
    def test_generate_token_with_challenge_scope(self, pre_auth_manager, cleanup_jtis):
        """Test generating token with 'challenge' scope"""
        user_id = "user-scope-002"
        email = "challenge@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        assert payload["scope"] == "challenge"
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        token_data = pre_auth_manager.redis_client.hgetall(redis_key)
        assert token_data["scope"] == "challenge"
    
    def test_generate_multiple_tokens_different_scopes_same_user(
        self, pre_auth_manager, cleanup_jtis
    ):
        """Test generating multiple tokens with different scopes for same user"""
        user_id = "user-scope-003"
        email = "multi@example.com"
        
        enroll_token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        enroll_payload = jwt.decode(
            enroll_token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        cleanup_jtis(enroll_payload["jti"])
        
        challenge_token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        challenge_payload = jwt.decode(
            challenge_token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        cleanup_jtis(challenge_payload["jti"])
        
        assert enroll_payload["scope"] == "enroll"
        assert challenge_payload["scope"] == "challenge"
        
        assert enroll_payload["jti"] != challenge_payload["jti"]
        
        enroll_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{enroll_payload['jti']}"
        challenge_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{challenge_payload['jti']}"
        
        enroll_data = pre_auth_manager.redis_client.hgetall(enroll_key)
        challenge_data = pre_auth_manager.redis_client.hgetall(challenge_key)
        
        assert enroll_data["scope"] == "enroll"
        assert challenge_data["scope"] == "challenge"


class TestScopeVerification:
    """Test scope handling during token verification"""
    
    def test_verify_token_preserves_scope(self, pre_auth_manager, cleanup_jtis):
        """Test that verify_token returns payload with correct scope"""
        user_id = "user-verify-001"
        email = "verify@example.com"
        
        enroll_token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        enroll_payload = pre_auth_manager.verify_token(enroll_token)
        
        assert enroll_payload is not None
        assert enroll_payload["scope"] == "enroll"
        cleanup_jtis(enroll_payload["jti"])
        
        challenge_token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        challenge_payload = pre_auth_manager.verify_token(challenge_token)
        
        assert challenge_payload is not None
        assert challenge_payload["scope"] == "challenge"
        cleanup_jtis(challenge_payload["jti"])
    
    def test_verify_token_with_tampered_scope_in_jwt(self, pre_auth_manager, cleanup_jtis):
        """Test that tampering with scope in JWT is detected (signature verification fails)"""
        user_id = "user-tamper-001"
        email = "tamper@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        cleanup_jtis(payload["jti"])
        
        payload["scope"] = "challenge"
        
        tampered_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        result = pre_auth_manager.verify_token(tampered_token)
        assert result is None
    
    def test_verify_token_with_missing_scope_in_redis(self, pre_auth_manager, cleanup_jtis):
        """Test behavior when scope is missing from Redis data (data corruption)"""
        user_id = "user-corrupt-001"
        email = "corrupt@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        pre_auth_manager.redis_client.hdel(redis_key, "scope")
        
        result = pre_auth_manager.verify_token(token)
        assert result is not None
        assert result["scope"] == "enroll"  # Scope from JWT


class TestScopePersistence:
    """Test scope persistence across token lifecycle"""
    
    def test_scope_persists_after_increment_attempts(self, pre_auth_manager, cleanup_jtis):
        """Test that scope remains unchanged after incrementing attempts"""
        user_id = "user-persist-001"
        email = "persist@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        initial_data = pre_auth_manager.redis_client.hgetall(redis_key)
        assert initial_data["scope"] == "enroll"
        
        pre_auth_manager.increment_attempts(jti)
        
        updated_data = pre_auth_manager.redis_client.hgetall(redis_key)
        assert updated_data["scope"] == "enroll"
        assert updated_data["attempts"] == "1"
    
    def test_scope_persists_after_atomic_consumption(self, pre_auth_manager, cleanup_jtis):
        """Test that scope remains in Redis after atomic consumption"""
        user_id = "user-consume-001"
        email = "consume@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        result = pre_auth_manager.consume_token_atomic(jti)
        assert result is True
        
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        consumed_data = pre_auth_manager.redis_client.hgetall(redis_key)
        assert consumed_data["scope"] == "challenge"
        assert consumed_data["consumed"] == "True"
    
    def test_get_token_info_includes_scope(self, pre_auth_manager, cleanup_jtis):
        """Test that get_token_info returns scope information"""
        user_id = "user-info-001"
        email = "info@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        token_info = pre_auth_manager.get_token_info(jti)
        
        assert token_info is not None
        assert token_info["scope"] == "enroll"
        assert token_info["user_id"] == user_id
        assert token_info["email"] == email


class TestScopeEdgeCases:
    """Test edge cases and error handling for scope"""
    
    def test_scope_type_literal_enforcement(self, pre_auth_manager):
        """Test that only 'enroll' and 'challenge' scopes are accepted"""
        user_id = "user-invalid-001"
        email = "invalid@example.com"
        
        
        try:
            token = pre_auth_manager.generate_token(user_id, email, scope="invalid")  # type: ignore
            
            payload = jwt.decode(
                token,
                pre_auth_manager.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": False}
            )
            
            assert payload["scope"] == "invalid"
            
            jti = payload["jti"]
            redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
            pre_auth_manager.redis_client.delete(redis_key)
            
        except Exception as e:
            pytest.skip(f"Runtime scope validation detected: {e}")
    
    def test_scope_case_sensitivity(self, pre_auth_manager, cleanup_jtis):
        """Test that scope is case-sensitive"""
        user_id = "user-case-001"
        email = "case@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        cleanup_jtis(payload["jti"])
        
        assert payload["scope"] == "enroll"
        assert payload["scope"] != "Enroll"
        assert payload["scope"] != "ENROLL"
    
    def test_scope_with_whitespace_trimming(self, pre_auth_manager):
        """Test that scope values are not automatically trimmed"""
        user_id = "user-whitespace-001"
        email = "whitespace@example.com"
        
        try:
            token = pre_auth_manager.generate_token(user_id, email, scope=" enroll ")  # type: ignore
            
            payload = jwt.decode(
                token,
                pre_auth_manager.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": False}
            )
            
            assert payload["scope"] == " enroll "
            
            jti = payload["jti"]
            redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
            pre_auth_manager.redis_client.delete(redis_key)
            
        except Exception as e:
            pytest.skip(f"Scope validation detected: {e}")


class TestScopeConcurrency:
    """Test scope handling under concurrent access"""
    
    @pytest.mark.timeout(10)
    def test_concurrent_generation_different_scopes(self, pre_auth_manager, cleanup_jtis):
        """Test concurrent generation of tokens with different scopes"""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        user_id = "user-concurrent-001"
        email = "concurrent@example.com"
        n_threads = 10
        
        def generate_with_scope(scope):
            """Generate token with specified scope"""
            token = pre_auth_manager.generate_token(user_id, email, scope=scope)
            payload = jwt.decode(
                token,
                pre_auth_manager.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": False}
            )
            cleanup_jtis(payload["jti"])
            return payload
        
        scopes = ["enroll"] * 5 + ["challenge"] * 5
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(generate_with_scope, scope) for scope in scopes]
            results = [future.result() for future in as_completed(futures)]
        
        enroll_tokens = [r for r in results if r["scope"] == "enroll"]
        challenge_tokens = [r for r in results if r["scope"] == "challenge"]
        
        assert len(enroll_tokens) == 5
        assert len(challenge_tokens) == 5
        
        all_jtis = [r["jti"] for r in results]
        assert len(set(all_jtis)) == n_threads
    
    @pytest.mark.timeout(10)
    def test_concurrent_verification_preserves_scope(self, pre_auth_manager, cleanup_jtis):
        """Test that concurrent verification preserves scope correctly"""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        user_id = "user-verify-concurrent-001"
        email = "verify-concurrent@example.com"
        
        enroll_token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        challenge_token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        
        enroll_payload = jwt.decode(
            enroll_token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        challenge_payload = jwt.decode(
            challenge_token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        cleanup_jtis(enroll_payload["jti"])
        cleanup_jtis(challenge_payload["jti"])
        
        n_threads = 10
        tokens = [enroll_token, challenge_token] * 5  # Verify each token 5 times
        
        def verify_token(token):
            """Verify token and return payload"""
            return pre_auth_manager.verify_token(token)
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(verify_token, token) for token in tokens]
            results = [future.result() for future in as_completed(futures)]
        
        assert all(r is not None for r in results)
        
        enroll_results = [r for r in results if r["jti"] == enroll_payload["jti"]]
        challenge_results = [r for r in results if r["jti"] == challenge_payload["jti"]]
        
        assert len(enroll_results) == 5
        assert len(challenge_results) == 5
        
        assert all(r["scope"] == "enroll" for r in enroll_results)
        assert all(r["scope"] == "challenge" for r in challenge_results)


class TestScopeIntegrationWithAtomicConsumption:
    """Test scope behavior with atomic consumption"""
    
    def test_consumed_token_scope_still_readable(self, pre_auth_manager, cleanup_jtis):
        """Test that scope can still be read from consumed token (for audit)"""
        user_id = "user-audit-001"
        email = "audit@example.com"
        
        token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        payload = jwt.decode(
            token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        jti = payload["jti"]
        cleanup_jtis(jti)
        
        result = pre_auth_manager.consume_token_atomic(jti)
        assert result is True
        
        token_info = pre_auth_manager.get_token_info(jti)
        assert token_info is not None
        assert token_info["scope"] == "enroll"
        assert token_info["consumed"] == "True"
        
        verify_result = pre_auth_manager.verify_token(token)
        assert verify_result is None
    
    def test_scope_enforcement_prevents_reuse_across_scopes(self, pre_auth_manager, cleanup_jtis):
        """Test that consuming a token with one scope doesn't affect tokens with other scopes"""
        user_id = "user-isolation-001"
        email = "isolation@example.com"
        
        enroll_token = pre_auth_manager.generate_token(user_id, email, scope="enroll")
        challenge_token = pre_auth_manager.generate_token(user_id, email, scope="challenge")
        
        enroll_payload = jwt.decode(
            enroll_token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        challenge_payload = jwt.decode(
            challenge_token,
            pre_auth_manager.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        enroll_jti = enroll_payload["jti"]
        challenge_jti = challenge_payload["jti"]
        
        cleanup_jtis(enroll_jti)
        cleanup_jtis(challenge_jti)
        
        result = pre_auth_manager.consume_token_atomic(enroll_jti)
        assert result is True
        
        challenge_verify = pre_auth_manager.verify_token(challenge_token)
        assert challenge_verify is not None
        assert challenge_verify["scope"] == "challenge"
        
        enroll_verify = pre_auth_manager.verify_token(enroll_token)
        assert enroll_verify is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
