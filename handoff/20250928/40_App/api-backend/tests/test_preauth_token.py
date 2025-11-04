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
    revoke_preauth_token
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
        
        token, nonce = generate_preauth_token(user_id, email, ttl)
        
        # Assert token and nonce are generated
        assert token is not None
        assert len(token) > 20  # URL-safe base64 encoded
        assert nonce is not None
        assert len(nonce) > 10
        
        # Assert Redis setex was called
        mock_redis_instance.setex.assert_called_once()
        call_args = mock_redis_instance.setex.call_args
        
        # Verify Redis key format
        redis_key = call_args[0][0]
        assert redis_key.startswith(f"preauth:{user_id}:")
        assert redis_key.endswith(nonce)
        
        # Verify TTL
        assert call_args[0][1] == ttl
        
        # Verify stored data
        stored_data = json.loads(call_args[0][2])
        assert stored_data['token'] == token
        assert stored_data['email'] == email
        assert stored_data['nonce'] == nonce
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
        
        token, nonce = generate_preauth_token(user_id, email, custom_ttl)
        
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
        nonce = "test-nonce"
        
        # Mock Redis scan and get
        redis_key = f"preauth:{user_id}:{nonce}"
        mock_redis_instance.scan_iter.return_value = [redis_key]
        
        stored_data = {
            "token": token,
            "issued_at": "2025-11-04T10:00:00",
            "attempts": 0,
            "email": email,
            "nonce": nonce
        }
        mock_redis_instance.get.return_value = json.dumps(stored_data)
        
        # Validate and consume token
        result = validate_and_consume_preauth_token(token)
        
        # Assert success
        assert result is not None
        assert result['id'] == user_id
        assert result['email'] == email
        
        # Assert token was deleted (one-time-use)
        mock_redis_instance.delete.assert_called_once_with(redis_key)
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_validate_invalid_token(self, mock_redis):
        """Test validation with invalid token"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        # Mock empty scan result
        mock_redis_instance.scan_iter.return_value = []
        
        result = validate_and_consume_preauth_token("invalid-token")
        
        # Assert failure
        assert result is None
        
        # Assert no deletion occurred
        mock_redis_instance.delete.assert_not_called()
    
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
        
        # Mock Redis key exists but get returns None (expired)
        redis_key = "preauth:user-123:nonce"
        mock_redis_instance.scan_iter.return_value = [redis_key]
        mock_redis_instance.get.return_value = None
        
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
        nonce = "test-nonce"
        redis_key = f"preauth:{user_id}:{nonce}"
        
        stored_data = {
            "token": token,
            "issued_at": "2025-11-04T10:00:00",
            "attempts": 0,
            "email": email,
            "nonce": nonce
        }
        
        # First attempt: token exists
        mock_redis_instance.scan_iter.return_value = [redis_key]
        mock_redis_instance.get.return_value = json.dumps(stored_data)
        
        # First use: success
        result1 = validate_and_consume_preauth_token(token)
        assert result1 is not None
        assert mock_redis_instance.delete.called
        
        # Second attempt: token deleted, scan returns empty
        mock_redis_instance.scan_iter.return_value = []
        
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
        
        # Mock multiple tokens for user
        keys = [
            f"preauth:{user_id}:nonce1",
            f"preauth:{user_id}:nonce2",
            f"preauth:{user_id}:nonce3"
        ]
        mock_redis_instance.scan_iter.return_value = keys
        
        # Revoke tokens
        count = revoke_preauth_token(user_id)
        
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
        
        count = revoke_preauth_token("test-user-123")
        
        # Assert no deletions
        assert count == 0
        mock_redis_instance.delete.assert_not_called()
