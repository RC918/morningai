"""
Unit tests for Pre-Auth Token functionality.

Tests cover:
- Token generation and storage
- Token validation and consumption
- Token expiry
- One-time-use enforcement
- Replay attack prevention
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.utils.preauth_token import (
    generate_preauth_token,
    validate_and_consume_preauth_token,
    revoke_preauth_tokens_for_user
)


class TestPreAuthTokenGeneration:
    """Test pre-auth token generation"""
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_generate_preauth_token_success(self, mock_redis):
        """Test successful pre-auth token generation"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        email = "test@example.com"
        ttl = 300
        
        token = generate_preauth_token(user_id, email, ttl)
        
        # Assert token is generated
        assert token is not None
        assert len(token) > 20  # URL-safe base64 encoded
        
        # Assert Redis setex was called
        mock_redis_instance.setex.assert_called_once()
        call_args = mock_redis_instance.setex.call_args
        
        # Verify Redis key format (token as key)
        redis_key = call_args[0][0]
        assert redis_key == f"preauth:{token}"
        
        # Verify TTL
        assert call_args[0][1] == ttl
        
        # Verify stored data
        stored_data = json.loads(call_args[0][2])
        assert stored_data['user_id'] == user_id
        assert stored_data['email'] == email
        assert 'issued_at' in stored_data
        assert stored_data['attempts'] == 0
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_generate_preauth_token_custom_ttl(self, mock_redis):
        """Test pre-auth token generation with custom TTL"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        email = "test@example.com"
        custom_ttl = 600  # 10 minutes
        
        token = generate_preauth_token(user_id, email, custom_ttl)
        
        # Verify custom TTL was used
        call_args = mock_redis_instance.setex.call_args
        assert call_args[0][1] == custom_ttl


class TestPreAuthTokenValidation:
    """Test pre-auth token validation and consumption"""
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_validate_and_consume_success(self, mock_redis):
        """Test successful token validation and consumption"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        email = "test@example.com"
        token = "test-token-abc123"
        
        # Mock Redis eval for Lua script (atomic GET-and-DELETE)
        redis_key = f"preauth:{token}"
        
        stored_data = {
            "user_id": user_id,
            "email": email,
            "issued_at": "2025-11-04T10:00:00",
            "attempts": 0
        }
        mock_redis_instance.eval.return_value = json.dumps(stored_data).encode('utf-8')
        
        # Validate and consume token
        result = validate_and_consume_preauth_token(token)
        
        # Assert success
        assert result is not None
        assert result['id'] == user_id
        assert result['email'] == email
        
        assert mock_redis_instance.eval.called
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_validate_invalid_token(self, mock_redis):
        """Test validation with invalid token"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        # Mock Redis eval returns None (token not found)
        mock_redis_instance.eval.return_value = None
        
        result = validate_and_consume_preauth_token("invalid-token")
        
        # Assert failure
        assert result is None
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_validate_empty_token(self, mock_redis):
        """Test validation with empty token"""
        result = validate_and_consume_preauth_token("")
        assert result is None
        
        result = validate_and_consume_preauth_token(None)
        assert result is None
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_validate_expired_token(self, mock_redis):
        """Test validation with expired token (Redis key not found)"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        # Mock Redis eval returns None (expired/not found)
        mock_redis_instance.eval.return_value = None
        
        result = validate_and_consume_preauth_token("test-token")
        
        # Assert failure
        assert result is None


class TestPreAuthTokenReplayPrevention:
    """Test one-time-use and replay attack prevention"""
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_token_cannot_be_reused(self, mock_redis):
        """Test that token cannot be used twice"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        email = "test@example.com"
        token = "test-token-abc123"
        redis_key = f"preauth:{token}"
        
        stored_data = {
            "user_id": user_id,
            "email": email,
            "issued_at": "2025-11-04T10:00:00",
            "attempts": 0
        }
        
        # First attempt: token exists (eval returns bytes)
        mock_redis_instance.eval.return_value = json.dumps(stored_data).encode('utf-8')
        
        # First use: success
        result1 = validate_and_consume_preauth_token(token)
        assert result1 is not None
        assert mock_redis_instance.eval.called
        
        # Second attempt: token deleted, eval returns None
        mock_redis_instance.eval.return_value = None
        
        # Second use: failure
        result2 = validate_and_consume_preauth_token(token)
        assert result2 is None


class TestPreAuthTokenRevocation:
    """Test token revocation"""
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_revoke_preauth_token(self, mock_redis):
        """Test revoking all pre-auth tokens for a user"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        
        # Mock multiple tokens with user_id in value
        keys = [
            "preauth:token1",
            "preauth:token2",
            "preauth:token3"
        ]
        mock_redis_instance.scan_iter.return_value = keys
        
        def mock_get(key):
            return json.dumps({"user_id": user_id, "email": "test@example.com"})
        
        mock_redis_instance.get.side_effect = mock_get
        
        # Revoke tokens
        count = revoke_preauth_tokens_for_user(user_id)
        
        # Assert all tokens deleted
        assert count == 3
        assert mock_redis_instance.delete.call_count == 3
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_revoke_no_tokens(self, mock_redis):
        """Test revoking when no tokens exist"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        # Mock no tokens
        mock_redis_instance.scan_iter.return_value = []
        
        count = revoke_preauth_tokens_for_user("test-user-123")
        
        # Assert no deletions
        assert count == 0
        mock_redis_instance.delete.assert_not_called()
