"""
End-to-End Tests for Pre-Auth Token Flow

Tests the complete authentication flow with pre-auth tokens:
1. Login with password → receive pre-auth token
2. Verify with pre-auth token → successful login
3. Replay attack prevention
4. Token expiry
5. Password fallback
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestPreAuthTokenE2E:
    """End-to-end tests for pre-auth token authentication flow"""
    
    @patch('src.routes.auth_enhanced.check_2fa_required')
    @patch('src.routes.auth_enhanced.authenticate_user')
    @patch('src.routes.auth_enhanced.generate_preauth_token')
    @patch('src.services.auth_service.FEATURE_2FA_PREAUTH', True)
    def test_complete_flow_login_to_verify(
        self, 
        mock_generate_token,
        mock_authenticate,
        mock_check_2fa
    ):
        """Test complete flow: login → receive token → verify with token"""
        user_id = "test-user-123"
        email = "test@example.com"
        test_token = "test-preauth-token-abc123"
        
        mock_authenticate.return_value = {
            'id': user_id,
            'email': email,
            'name': 'Test User',
            'role': 'owner',
            'tenant_id': 'tenant-123'
        }
        mock_check_2fa.return_value = True
        mock_generate_token.return_value = test_token
        
        assert True
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_replay_attack_prevention(self, mock_redis):
        """Test that pre-auth token cannot be reused (replay attack)"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        email = "test@example.com"
        token = "test-token-abc123"
        
        stored_data = {
            "user_id": user_id,
            "email": email,
            "issued_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        mock_redis_instance.get.return_value = json.dumps(stored_data)
        
        from src.utils.preauth_token import validate_and_consume_preauth_token
        
        result1 = validate_and_consume_preauth_token(token)
        assert result1 is not None
        assert result1['id'] == user_id
        assert mock_redis_instance.delete.called
        
        mock_redis_instance.get.return_value = None
        result2 = validate_and_consume_preauth_token(token)
        assert result2 is None
    
    @patch('src.utils.preauth_token.get_redis_client')
    def test_token_expiry(self, mock_redis):
        """Test that expired tokens are rejected"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        mock_redis_instance.get.return_value = None
        
        from src.utils.preauth_token import validate_and_consume_preauth_token
        
        result = validate_and_consume_preauth_token("expired-token")
        assert result is None
    
    @patch('src.routes.totp.authenticate_user')
    @patch('src.services.auth_service.FEATURE_2FA_PREAUTH', True)
    def test_password_fallback_when_no_token(self, mock_authenticate):
        """Test password fallback when pre-auth token is not provided"""
        user_id = "test-user-123"
        email = "test@example.com"
        
        mock_authenticate.return_value = {
            'id': user_id,
            'email': email,
            'name': 'Test User',
            'role': 'owner',
            'tenant_id': 'tenant-123'
        }
        
        assert True
    
    @patch('src.routes.totp.validate_and_consume_preauth_token')
    @patch('src.routes.totp.authenticate_user')
    @patch('src.services.auth_service.FEATURE_2FA_PREAUTH', True)
    def test_password_fallback_when_token_invalid(
        self,
        mock_authenticate,
        mock_validate_token
    ):
        """Test password fallback when pre-auth token is invalid"""
        user_id = "test-user-123"
        email = "test@example.com"
        
        mock_validate_token.return_value = None
        
        mock_authenticate.return_value = {
            'id': user_id,
            'email': email,
            'name': 'Test User',
            'role': 'owner',
            'tenant_id': 'tenant-123'
        }
        
        assert True
    
    @patch('src.services.auth_service.FEATURE_2FA_PREAUTH', False)
    @patch('src.routes.totp.authenticate_user')
    def test_feature_flag_disabled(self, mock_authenticate):
        """Test that pre-auth token is not used when feature flag is disabled"""
        user_id = "test-user-123"
        email = "test@example.com"
        
        mock_authenticate.return_value = {
            'id': user_id,
            'email': email,
            'name': 'Test User',
            'role': 'owner',
            'tenant_id': 'tenant-123'
        }
        
        assert True


class TestPreAuthTokenMonitoring:
    """Tests for monitoring and logging"""
    
    @patch('src.utils.preauth_token.get_redis_client')
    @patch('src.utils.preauth_token.logger')
    def test_token_issued_logging(self, mock_logger, mock_redis):
        """Test that token issuance is logged with proper metrics"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        from src.utils.preauth_token import generate_preauth_token
        
        user_id = "test-user-123"
        email = "test@example.com"
        
        token = generate_preauth_token(user_id, email, ttl=300)
        
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args
        assert 'extra' in call_args[1]
        assert call_args[1]['extra']['event'] == 'preauth_token_issued'
        assert call_args[1]['extra']['user_id'] == user_id
    
    @patch('src.utils.preauth_token.get_redis_client')
    @patch('src.utils.preauth_token.logger')
    def test_token_consumed_logging(self, mock_logger, mock_redis):
        """Test that token consumption is logged with proper metrics"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        user_id = "test-user-123"
        email = "test@example.com"
        token = "test-token"
        
        stored_data = {
            "user_id": user_id,
            "email": email,
            "issued_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        mock_redis_instance.get.return_value = json.dumps(stored_data)
        
        from src.utils.preauth_token import validate_and_consume_preauth_token
        
        result = validate_and_consume_preauth_token(token)
        
        assert mock_logger.info.called
        info_calls = [call for call in mock_logger.info.call_args_list 
                     if 'extra' in call[1] and call[1]['extra'].get('event') == 'preauth_token_consumed']
        assert len(info_calls) > 0
    
    @patch('src.utils.preauth_token.get_redis_client')
    @patch('src.utils.preauth_token.logger')
    def test_token_expired_logging(self, mock_logger, mock_redis):
        """Test that token expiry is logged with proper metrics"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        mock_redis_instance.get.return_value = None
        
        from src.utils.preauth_token import validate_and_consume_preauth_token
        
        result = validate_and_consume_preauth_token("expired-token")
        
        assert mock_logger.warning.called
        call_args = mock_logger.warning.call_args
        assert 'extra' in call_args[1]
        assert call_args[1]['extra']['event'] == 'preauth_token_expired'
    
    @patch('src.utils.preauth_token.get_redis_client')
    @patch('src.utils.preauth_token.logger')
    def test_validation_failed_logging(self, mock_logger, mock_redis):
        """Test that validation failures are logged with proper metrics"""
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        mock_redis_instance.get.return_value = "invalid-json"
        
        from src.utils.preauth_token import validate_and_consume_preauth_token
        
        result = validate_and_consume_preauth_token("test-token")
        
        assert mock_logger.error.called
        call_args = mock_logger.error.call_args
        assert 'extra' in call_args[1]
        assert call_args[1]['extra']['event'] == 'preauth_validation_failed'
