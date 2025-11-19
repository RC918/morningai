"""
Tests for redis_config utility.

Tests cover:
- get_secure_redis_url function with TLS enforcement
- is_redis_tls_enabled function
- get_redis_connection_info function
"""

import pytest
from unittest.mock import MagicMock, patch


class TestGetSecureRedisUrl:
    """Test get_secure_redis_url function"""
    
    def test_get_secure_redis_url_with_tls(self):
        """Should return Redis URL with TLS"""
        from utils.redis_config import get_secure_redis_url
        
        mock_settings = MagicMock()
        mock_settings.redis_url = 'rediss://user:pass@host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            url = get_secure_redis_url()
        
        assert url == 'rediss://user:pass@host:6379'
    
    def test_get_secure_redis_url_localhost_with_allow_local(self):
        """Should allow localhost without TLS when allow_local=True"""
        from utils.redis_config import get_secure_redis_url
        
        mock_settings = MagicMock()
        mock_settings.redis_url = 'redis://localhost:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            url = get_secure_redis_url(allow_local=True)
        
        assert url == 'redis://localhost:6379'
    
    def test_get_secure_redis_url_localhost_without_allow_local(self):
        """Should reject localhost without TLS when allow_local=False"""
        from utils.redis_config import get_secure_redis_url
        
        mock_settings = MagicMock()
        mock_settings.redis_url = 'redis://localhost:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="must use TLS"):
                get_secure_redis_url(allow_local=False)
    
    def test_get_secure_redis_url_no_tls_non_localhost(self):
        """Should reject non-TLS URL for non-localhost"""
        from utils.redis_config import get_secure_redis_url
        
        mock_settings = MagicMock()
        mock_settings.redis_url = 'redis://remote-host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="must use TLS"):
                get_secure_redis_url()
    
    def test_get_secure_redis_url_no_url(self):
        """Should raise ValueError when no Redis URL configured"""
        from utils.redis_config import get_secure_redis_url
        
        mock_settings = MagicMock()
        mock_settings.redis_url = None
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="No REDIS_URL"):
                get_secure_redis_url()
    
    def test_get_secure_redis_url_default_allow_local(self):
        """Should default to allow_local=False"""
        from utils.redis_config import get_secure_redis_url
        
        mock_settings = MagicMock()
        mock_settings.redis_url = 'redis://remote-host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="must use TLS"):
                get_secure_redis_url()


class TestIsRedisTlsEnabled:
    """Test is_redis_tls_enabled function"""
    
    def test_is_redis_tls_enabled_with_upstash(self):
        """Should return True for Upstash"""
        from utils.redis_config import is_redis_tls_enabled
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = 'https://test.upstash.io'
        mock_settings.redis_url = None
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            result = is_redis_tls_enabled()
        
        assert result is True
    
    def test_is_redis_tls_enabled_with_rediss(self):
        """Should return True for rediss://"""
        from utils.redis_config import is_redis_tls_enabled
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'rediss://host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            result = is_redis_tls_enabled()
        
        assert result is True
    
    def test_is_redis_tls_enabled_with_redis(self):
        """Should return False for redis://"""
        from utils.redis_config import is_redis_tls_enabled
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            result = is_redis_tls_enabled()
        
        assert result is False
    
    def test_is_redis_tls_enabled_no_config(self):
        """Should return False when no Redis configured"""
        from utils.redis_config import is_redis_tls_enabled
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = None
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            result = is_redis_tls_enabled()
        
        assert result is False


class TestGetRedisConnectionInfo:
    """Test get_redis_connection_info function"""
    
    def test_get_upstash_connection_info(self):
        """Should return Upstash connection info"""
        from utils.redis_config import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = 'https://user@test.upstash.io'
        mock_settings.redis_url = None
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'upstash'
        assert info['protocol'] == 'https'
        assert info['tls_enabled'] is True
        assert info['secure'] is True
    
    def test_get_redis_tls_connection_info(self):
        """Should return Redis TLS connection info"""
        from utils.redis_config import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'rediss://user@host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'redis'
        assert info['protocol'] == 'rediss'
        assert info['tls_enabled'] is True
        assert info['secure'] is True
    
    def test_get_redis_non_tls_connection_info(self):
        """Should return Redis non-TLS connection info"""
        from utils.redis_config import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'redis'
        assert info['protocol'] == 'redis'
        assert info['tls_enabled'] is False
        assert info['secure'] is False
    
    def test_get_redis_localhost_connection_info(self):
        """Should detect localhost in connection info"""
        from utils.redis_config import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'redis://localhost:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'redis'
        assert info['local_dev'] is True
    
    def test_get_no_connection_info(self):
        """Should return none connection info when not configured"""
        from utils.redis_config import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = None
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert info['type'] == 'none'
        assert info['protocol'] == 'none'
        assert info['tls_enabled'] is False
        assert info['secure'] is False
    
    def test_get_connection_info_masks_credentials(self):
        """Should mask credentials in URL"""
        from utils.redis_config import get_redis_connection_info
        
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = None
        mock_settings.redis_url = 'rediss://user:password@host:6379'
        
        with patch('utils.redis_config.get_settings', return_value=mock_settings):
            info = get_redis_connection_info()
        
        assert 'password' not in info['url']
        assert info['url'] == 'host:6379'
