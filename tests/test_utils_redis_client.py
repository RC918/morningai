"""
Tests for redis_client utility.

Tests cover:
- create_redis_client function with Upstash and standard Redis
- get_redis_client singleton pattern
- get_redis_connection_info function
- check_redis_security function
"""

import pytest
from unittest.mock import MagicMock, patch


class TestCreateRedisClient:
    """Test create_redis_client function"""
    
    def test_create_upstash_client(self):
        """Should create Upstash Redis client when URL provided"""
        from utils.redis_client import create_redis_client
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = 'https://test.upstash.io'
        mock_settings.upstash_redis_rest_token = 'test-token'
        mock_settings.redis_url = None
        
        mock_upstash_redis = MagicMock()
        mock_client = MagicMock()
        mock_upstash_redis.return_value = mock_client
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.Redis', mock_upstash_redis):
                client = create_redis_client(skip_ping=True)
        
        assert client == mock_client
    
    def test_create_standard_redis_client(self):
        """Should create standard Redis client when Redis URL provided"""
        from utils.redis_client import create_redis_client
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        
        mock_redis = MagicMock()
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis', mock_redis):
                client = create_redis_client(skip_ping=True)
        
        assert client == mock_client
        mock_redis.from_url.assert_called_once()
    
    def test_create_redis_client_with_tls(self):
        """Should create Redis client with TLS"""
        from utils.redis_client import create_redis_client
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'rediss://localhost:6379'
        
        mock_redis = MagicMock()
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis', mock_redis):
                client = create_redis_client(skip_ping=True)
        
        assert client == mock_client
        call_args = mock_redis.from_url.call_args
        assert call_args[0][0] == 'rediss://localhost:6379'
    
    def test_create_redis_client_no_config(self):
        """Should raise ValueError when no Redis config provided"""
        from utils.redis_client import create_redis_client
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="No Redis configuration found"):
                create_redis_client(skip_ping=True)
    
    def test_create_redis_client_with_ping(self):
        """Should ping Redis when skip_ping=False"""
        from utils.redis_client import create_redis_client
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        
        mock_redis = MagicMock()
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.from_url.return_value = mock_client
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis', mock_redis):
                client = create_redis_client(skip_ping=False)
        
        mock_client.ping.assert_called_once()


class TestGetRedisClient:
    """Test get_redis_client singleton function"""
    
    def test_get_redis_client_returns_client(self):
        """Should return Redis client"""
        from utils.redis_client import get_redis_client
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        mock_settings.testing = True
        
        mock_redis = MagicMock()
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis', mock_redis):
                with patch('utils.redis_client.redis_client', None):
                    client = get_redis_client()
        
        assert client == mock_client
    
    def test_get_redis_client_singleton(self):
        """Should return same client on multiple calls"""
        from utils.redis_client import get_redis_client
        import utils.redis_client as redis_module
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        mock_settings.testing = True
        
        mock_redis = MagicMock()
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        
        redis_module.redis_client = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis', mock_redis):
                client1 = get_redis_client()
                client2 = get_redis_client()
        
        assert client1 == client2
        assert mock_redis.from_url.call_count == 1


class TestGetRedisConnectionInfo:
    """Test get_redis_connection_info function"""
    
    def test_get_upstash_connection_info(self):
        """Should return Upstash connection info"""
        from utils.redis_client import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = 'https://test@upstash.io'
        mock_settings.redis_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'upstash'
        assert info['protocol'] == 'https'
        assert info['tls_enabled'] is True
    
    def test_get_redis_tls_connection_info(self):
        """Should return Redis TLS connection info"""
        from utils.redis_client import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'rediss://user@localhost:6379'
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'redis'
        assert info['protocol'] == 'rediss'
        assert info['tls_enabled'] is True
    
    def test_get_redis_non_tls_connection_info(self):
        """Should return Redis non-TLS connection info"""
        from utils.redis_client import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'redis'
        assert info['protocol'] == 'redis'
        assert info['tls_enabled'] is False
    
    def test_get_no_connection_info(self):
        """Should return none connection info when not configured"""
        from utils.redis_client import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'none'
        assert info['protocol'] == 'none'
        assert info['tls_enabled'] is False


class TestCheckRedisSecurity:
    """Test check_redis_security function"""
    
    def test_check_upstash_security(self):
        """Should return secure status for Upstash"""
        from utils.redis_client import check_redis_security
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = 'https://test.upstash.io'
        mock_settings.redis_url = None
        
        mock_client = MagicMock()
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
        
        assert result['status'] == 'secure'
        assert result['type'] == 'upstash'
        assert result['cve_2025_49844_risk'] == 'low'
    
    def test_check_redis_vulnerable_version(self):
        """Should detect vulnerable Redis version"""
        from utils.redis_client import check_redis_security
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        
        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '7.0.0'}
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
        
        assert result['status'] == 'vulnerable'
        assert result['type'] == 'redis'
        assert result['version'] == '7.0.0'
        assert result['cve_2025_49844_risk'] == 'high'
        assert len(result['recommendations']) > 0
    
    def test_check_redis_secure_version(self):
        """Should detect secure Redis version"""
        from utils.redis_client import check_redis_security
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'rediss://localhost:6379'
        
        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '8.2.2'}
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
        
        assert result['status'] == 'secure'
        assert result['type'] == 'redis'
        assert result['version'] == '8.2.2'
        assert result['cve_2025_49844_risk'] == 'low'
        assert result['tls_enabled'] is True
    
    def test_check_redis_security_no_tls(self):
        """Should recommend TLS when not enabled"""
        from utils.redis_client import check_redis_security
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        
        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '8.2.2'}
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
        
        assert result['tls_enabled'] is False
        assert any('TLS' in rec for rec in result['recommendations'])
    
    def test_check_redis_security_error(self):
        """Should handle errors gracefully"""
        from utils.redis_client import check_redis_security
        
        with patch('utils.redis_client.get_redis_client', side_effect=Exception('Connection failed')):
            result = check_redis_security()
        
        assert result['status'] == 'error'
        assert 'Failed to check Redis security' in result['message']
