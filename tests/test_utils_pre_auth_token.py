"""
Tests for pre_auth_token utility.

Tests cover:
- PreAuthTokenManager class initialization
- Token generation with different scopes
- Token verification with various scenarios
- Token consumption (atomic and non-atomic)
- Attempt tracking and rate limiting
- Token revocation
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import jwt
from datetime import datetime, timedelta, UTC
import redis.exceptions
import sys

mock_auth_service = MagicMock()
mock_auth_service.is_production = MagicMock(return_value=False)
sys.modules['src'] = MagicMock()
sys.modules['src.services'] = MagicMock()
sys.modules['src.services.auth_service'] = mock_auth_service


class TestPreAuthTokenManagerInit:
    """Test PreAuthTokenManager initialization"""
    
    def test_init_with_jwt_secret(self, monkeypatch):
        """Should initialize with JWT secret from environment"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        with patch('utils.pre_auth_token.get_redis_client'):
            manager = PreAuthTokenManager()
        
        assert manager.jwt_secret == 'test-secret-123'
    
    def test_init_production_without_secret(self, monkeypatch):
        """Should raise RuntimeError in production without proper secret"""
        monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
        monkeypatch.setenv('ENVIRONMENT', 'production')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = None
        
        # Patch is_production before importing PreAuthTokenManager
        with patch('sys.modules', {**sys.modules, 'src.services.auth_service': MagicMock(is_production=MagicMock(return_value=True))}):
            from utils.pre_auth_token import PreAuthTokenManager
            
            with patch('utils.pre_auth_token.settings', mock_settings):
                with patch('utils.pre_auth_token.get_redis_client'):
                    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY must be set"):
                        PreAuthTokenManager()
    
    def test_init_production_with_test_secret(self, monkeypatch):
        """Should raise RuntimeError in production with test secret"""
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-key-for-testing')
        monkeypatch.setenv('ENVIRONMENT', 'production')
        
        # Patch is_production before importing PreAuthTokenManager
        with patch('sys.modules', {**sys.modules, 'src.services.auth_service': MagicMock(is_production=MagicMock(return_value=True))}):
            from utils.pre_auth_token import PreAuthTokenManager
            
            with patch('utils.pre_auth_token.get_redis_client'):
                with pytest.raises(RuntimeError, match="default test key is not allowed"):
                    PreAuthTokenManager()
    
    def test_init_development_with_fallback_secret(self, monkeypatch):
        """Should use fallback secret in development"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = None
        
        with patch('utils.pre_auth_token.settings', mock_settings):
            with patch('utils.pre_auth_token.get_redis_client'):
                manager = PreAuthTokenManager()
        
        assert manager.jwt_secret == 'test-secret-key-for-testing'
    
    def test_redis_client_lazy_initialization(self, monkeypatch):
        """Should lazily initialize Redis client"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            with patch('services.auth_service.is_production', return_value=False):
                manager = PreAuthTokenManager()
                
                assert manager._redis_client is None
                
                client = manager.redis_client
                
                assert client == mock_redis
                assert manager._redis_client == mock_redis


class TestGenerateToken:
    """Test token generation"""
    
    def test_generate_token_enroll_scope(self, monkeypatch):
        """Should generate token with enroll scope"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            token = manager.generate_token('user-123', 'test@example.com', 'enroll')
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        mock_redis.hset.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    def test_generate_token_challenge_scope(self, monkeypatch):
        """Should generate token with challenge scope"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            token = manager.generate_token('user-123', 'test@example.com', 'challenge')
        
        payload = jwt.decode(token, 'test-secret-123', algorithms=['HS256'])
        
        assert payload['pre_auth'] is True
        assert payload['scope'] == 'challenge'
        assert payload['user_id'] == 'user-123'
        assert payload['email'] == 'test@example.com'
        assert 'jti' in payload
        assert 'iat' in payload
        assert 'exp' in payload
    
    def test_generate_token_stores_in_redis(self, monkeypatch):
        """Should store token metadata in Redis"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            token = manager.generate_token('user-123', 'test@example.com', 'enroll')
        
        call_args = mock_redis.hset.call_args
        assert 'mapping' in call_args.kwargs
        mapping = call_args.kwargs['mapping']
        
        assert mapping['user_id'] == 'user-123'
        assert mapping['email'] == 'test@example.com'
        assert mapping['scope'] == 'enroll'
        assert mapping['attempts'] == '0'
        assert mapping['consumed'] == 'False'
    
    def test_generate_token_sets_expiry(self, monkeypatch):
        """Should set 5 minute expiry in Redis"""
        from utils.pre_auth_token import PreAuthTokenManager, PRE_AUTH_TOKEN_EXPIRY_MINUTES
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            manager.generate_token('user-123', 'test@example.com', 'enroll')
        
        expire_call = mock_redis.expire.call_args
        assert expire_call[0][1] == PRE_AUTH_TOKEN_EXPIRY_MINUTES * 60


class TestVerifyToken:
    """Test token verification"""
    
    def test_verify_valid_token(self, monkeypatch):
        """Should verify valid token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            token = manager.generate_token('user-123', 'test@example.com', 'enroll')
            
            payload = manager.verify_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 'user-123'
        assert payload['scope'] == 'enroll'
    
    def test_verify_expired_token(self, monkeypatch):
        """Should reject expired token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        now = datetime.now(UTC)
        past = now - timedelta(minutes=10)
        
        payload = {
            'pre_auth': True,
            'scope': 'enroll',
            'user_id': 'user-123',
            'email': 'test@example.com',
            'jti': 'test-jti',
            'iat': past,
            'exp': past + timedelta(minutes=5)
        }
        
        expired_token = jwt.encode(payload, 'test-secret-123', algorithm='HS256')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.verify_token(expired_token)
        
        assert result is None
    
    def test_verify_invalid_token(self, monkeypatch):
        """Should reject invalid token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.verify_token('invalid-token')
        
        assert result is None
    
    def test_verify_token_without_pre_auth_claim(self, monkeypatch):
        """Should reject token without pre_auth claim"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        payload = {
            'user_id': 'user-123',
            'jti': 'test-jti'
        }
        
        token = jwt.encode(payload, 'test-secret-123', algorithm='HS256')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.verify_token(token)
        
        assert result is None
    
    def test_verify_token_without_jti(self, monkeypatch):
        """Should reject token without jti"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        payload = {
            'pre_auth': True,
            'user_id': 'user-123'
        }
        
        token = jwt.encode(payload, 'test-secret-123', algorithm='HS256')
        
        mock_redis = MagicMock()
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.verify_token(token)
        
        assert result is None
    
    def test_verify_token_not_in_redis(self, monkeypatch):
        """Should reject token not found in Redis"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {}
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            token = manager.generate_token('user-123', 'test@example.com', 'enroll')
            
            result = manager.verify_token(token)
        
        assert result is None
    
    def test_verify_consumed_token(self, monkeypatch):
        """Should reject already consumed token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {
            'user_id': 'user-123',
            'consumed': 'True'
        }
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            token = manager.generate_token('user-123', 'test@example.com', 'enroll')
            
            result = manager.verify_token(token)
        
        assert result is None
    
    def test_verify_token_max_attempts_exceeded(self, monkeypatch):
        """Should reject token with too many attempts"""
        from utils.pre_auth_token import PreAuthTokenManager, MAX_ATTEMPTS_PER_TOKEN
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {
            'user_id': 'user-123',
            'attempts': str(MAX_ATTEMPTS_PER_TOKEN),
            'consumed': 'False'
        }
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            token = manager.generate_token('user-123', 'test@example.com', 'enroll')
            
            result = manager.verify_token(token)
        
        assert result is None


class TestIncrementAttempts:
    """Test attempt tracking"""
    
    def test_increment_attempts(self, monkeypatch):
        """Should increment attempt counter"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hincrby.return_value = 1
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            count = manager.increment_attempts('test-jti')
        
        assert count == 1
        mock_redis.hincrby.assert_called_once()


class TestConsumeToken:
    """Test token consumption"""
    
    def test_consume_token_success(self, monkeypatch):
        """Should consume token successfully"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {
            'user_id': 'user-123',
            'consumed': 'False'
        }
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token('test-jti')
        
        assert result is True
        assert mock_redis.hset.call_count == 2
    
    def test_consume_token_not_found(self, monkeypatch):
        """Should fail to consume non-existent token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {}
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token('test-jti')
        
        assert result is False
    
    def test_consume_token_already_consumed(self, monkeypatch):
        """Should fail to consume already consumed token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {
            'user_id': 'user-123',
            'consumed': 'True'
        }
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token('test-jti')
        
        assert result is False


class TestConsumeTokenAtomic:
    """Test atomic token consumption"""
    
    def test_consume_token_atomic_success(self, monkeypatch):
        """Should atomically consume token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.hgetall.return_value = {
            'user_id': 'user-123',
            'consumed': 'False'
        }
        mock_pipeline.ttl.return_value = 300
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token_atomic('test-jti')
        
        assert result is True
        mock_pipeline.watch.assert_called_once()
        mock_pipeline.multi.assert_called_once()
        mock_pipeline.execute.assert_called_once()
    
    def test_consume_token_atomic_not_found(self, monkeypatch):
        """Should fail atomic consume for non-existent token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.hgetall.return_value = {}
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token_atomic('test-jti')
        
        assert result is False
        mock_pipeline.unwatch.assert_called_once()
    
    def test_consume_token_atomic_already_consumed(self, monkeypatch):
        """Should fail atomic consume for already consumed token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.hgetall.return_value = {
            'consumed': 'True'
        }
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token_atomic('test-jti')
        
        assert result is False
    
    def test_consume_token_atomic_watch_error_retry(self, monkeypatch):
        """Should retry on WatchError"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.hgetall.return_value = {
            'consumed': 'False'
        }
        mock_pipeline.ttl.return_value = 300
        mock_pipeline.execute.side_effect = [redis.exceptions.WatchError(), None]
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.consume_token_atomic('test-jti', max_retries=3)
        
        assert result is True
        assert mock_pipeline.execute.call_count == 2


class TestGetTokenInfo:
    """Test get token info"""
    
    def test_get_token_info_exists(self, monkeypatch):
        """Should get token info from Redis"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {
            'user_id': 'user-123',
            'scope': 'enroll'
        }
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            info = manager.get_token_info('test-jti')
        
        assert info is not None
        assert info['user_id'] == 'user-123'
    
    def test_get_token_info_not_found(self, monkeypatch):
        """Should return None for non-existent token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {}
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            info = manager.get_token_info('test-jti')
        
        assert info is None


class TestRevokeToken:
    """Test token revocation"""
    
    def test_revoke_token_success(self, monkeypatch):
        """Should revoke token successfully"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.revoke_token('test-jti')
        
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_revoke_token_not_found(self, monkeypatch):
        """Should return False for non-existent token"""
        from utils.pre_auth_token import PreAuthTokenManager
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 0
        
        with patch('utils.pre_auth_token.get_redis_client', return_value=mock_redis):
            manager = PreAuthTokenManager()
            
            result = manager.revoke_token('test-jti')
        
        assert result is False


class TestGetPreAuthManager:
    """Test get_pre_auth_manager singleton"""
    
    def test_get_pre_auth_manager_singleton(self, monkeypatch):
        """Should return singleton instance"""
        from utils.pre_auth_token import get_pre_auth_manager
        import utils.pre_auth_token as module
        
        monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-123')
        
        module._pre_auth_manager = None
        
        with patch('utils.pre_auth_token.get_redis_client'):
            manager1 = get_pre_auth_manager()
            manager2 = get_pre_auth_manager()
        
        assert manager1 is manager2
