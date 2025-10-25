"""Tests for Redis configuration helper"""
import pytest
import os
from unittest.mock import patch


class TestRedisConfig:
    """Test Redis configuration helper functions"""
    
    def test_get_secure_redis_url_with_rediss(self):
        """Test get_secure_redis_url with rediss:// URL"""
        from src.utils.redis_config import get_secure_redis_url
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}):
            url = get_secure_redis_url()
            assert url == 'rediss://example.com:6380/0'
    
    def test_get_secure_redis_url_with_local_allowed(self):
        """Test get_secure_redis_url with local Redis when allowed"""
        from src.utils.redis_config import get_secure_redis_url
        
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379/0'}):
            url = get_secure_redis_url(allow_local=True)
            assert url == 'redis://localhost:6379/0'
    
    def test_get_secure_redis_url_with_local_not_allowed(self):
        """Test get_secure_redis_url with local Redis when not allowed"""
        from src.utils.redis_config import get_secure_redis_url
        
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379/0'}):
            with pytest.raises(ValueError, match="must use TLS"):
                get_secure_redis_url(allow_local=False)
    
    def test_get_secure_redis_url_no_config(self):
        """Test get_secure_redis_url with no configuration"""
        from src.utils.redis_config import get_secure_redis_url
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No REDIS_URL"):
                get_secure_redis_url()
    
    def test_is_redis_tls_enabled_with_upstash(self):
        """Test is_redis_tls_enabled with Upstash"""
        from src.utils.redis_config import is_redis_tls_enabled
        
        with patch.dict(os.environ, {'UPSTASH_REDIS_REST_URL': 'https://example.upstash.io'}):
            assert is_redis_tls_enabled() is True
    
    def test_is_redis_tls_enabled_with_rediss(self):
        """Test is_redis_tls_enabled with rediss://"""
        from src.utils.redis_config import is_redis_tls_enabled
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}):
            assert is_redis_tls_enabled() is True
    
    def test_is_redis_tls_enabled_with_redis(self):
        """Test is_redis_tls_enabled with redis://"""
        from src.utils.redis_config import is_redis_tls_enabled
        
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379/0'}, clear=True):
            assert is_redis_tls_enabled() is False
    
    def test_get_redis_connection_info_upstash(self):
        """Test get_redis_connection_info with Upstash"""
        from src.utils.redis_config import get_redis_connection_info
        
        with patch.dict(os.environ, {'UPSTASH_REDIS_REST_URL': 'https://user:pass@example.upstash.io'}):
            info = get_redis_connection_info()
            assert info['type'] == 'upstash'
            assert info['protocol'] == 'https'
            assert info['tls_enabled'] is True
            assert info['secure'] is True
    
    def test_get_redis_connection_info_rediss(self):
        """Test get_redis_connection_info with rediss://"""
        from src.utils.redis_config import get_redis_connection_info
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://user:pass@example.com:6380/0'}, clear=True):
            info = get_redis_connection_info()
            assert info['type'] == 'redis'
            assert info['protocol'] == 'rediss'
            assert info['tls_enabled'] is True
            assert info['secure'] is True
    
    def test_get_redis_connection_info_local(self):
        """Test get_redis_connection_info with local Redis"""
        from src.utils.redis_config import get_redis_connection_info
        
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379/0'}, clear=True):
            info = get_redis_connection_info()
            assert info['type'] == 'redis'
            assert info['protocol'] == 'redis'
            assert info['tls_enabled'] is False
            assert info['secure'] is False
            assert info['local_dev'] is True
    
    def test_get_redis_connection_info_no_config(self):
        """Test get_redis_connection_info with no configuration"""
        from src.utils.redis_config import get_redis_connection_info
        
        with patch.dict(os.environ, {}, clear=True):
            info = get_redis_connection_info()
            assert info['type'] == 'none'
            assert info['protocol'] == 'none'
            assert info['tls_enabled'] is False
            assert info['secure'] is False
