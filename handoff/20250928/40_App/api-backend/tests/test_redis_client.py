"""Tests for Redis client skip_ping behavior with testing flag"""
import pytest
from unittest.mock import patch, MagicMock, Mock


class TestRedisClientSkipPing:
    """Test Redis client skip_ping behavior respects get_settings().testing"""
    
    def test_get_redis_client_respects_testing_flag_true(self):
        """Verify skip_ping uses get_settings().testing when testing=True"""
        mock_settings = MagicMock()
        mock_settings.testing = True
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis') as mock_redis_module:
                mock_client = MagicMock()
                mock_redis_module.from_url.return_value = mock_client
                
                import utils.redis_client as redis_client_module
                redis_client_module.redis_client = None
                
                from utils.redis_client import get_redis_client
                client = get_redis_client()
                
                assert client is not None
                mock_redis_module.from_url.assert_called_once()
                mock_client.ping.assert_not_called()
    
    def test_get_redis_client_respects_testing_flag_false(self):
        """Verify skip_ping uses get_settings().testing when testing=False"""
        mock_settings = MagicMock()
        mock_settings.testing = False
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis') as mock_redis_module:
                mock_client = MagicMock()
                mock_redis_module.from_url.return_value = mock_client
                
                import utils.redis_client as redis_client_module
                redis_client_module.redis_client = None
                
                from utils.redis_client import get_redis_client
                client = get_redis_client()
                
                assert client is not None
                mock_redis_module.from_url.assert_called_once()
                mock_client.ping.assert_called_once()
    
    def test_create_redis_client_with_skip_ping_true(self):
        """Verify create_redis_client respects skip_ping=True parameter"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis') as mock_redis_module:
                mock_client = MagicMock()
                mock_redis_module.from_url.return_value = mock_client
                
                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=True)
                
                assert client is not None
                mock_client.ping.assert_not_called()
    
    def test_create_redis_client_with_skip_ping_false(self):
        """Verify create_redis_client respects skip_ping=False parameter"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis') as mock_redis_module:
                mock_client = MagicMock()
                mock_redis_module.from_url.return_value = mock_client
                
                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=False)
                
                assert client is not None
                mock_client.ping.assert_called_once()
    
    def test_create_redis_client_upstash_with_skip_ping_true(self):
        """Verify create_redis_client respects skip_ping=True for Upstash"""
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.upstash_redis_rest_token = "test_token"
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.Redis') as mock_upstash_redis:
                mock_client = MagicMock()
                mock_upstash_redis.return_value = mock_client
                
                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=True)
                
                assert client is not None
                mock_client.ping.assert_not_called()
    
    def test_create_redis_client_upstash_with_skip_ping_false(self):
        """Verify create_redis_client respects skip_ping=False for Upstash"""
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.upstash_redis_rest_token = "test_token"
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.Redis') as mock_upstash_redis:
                mock_client = MagicMock()
                mock_upstash_redis.return_value = mock_client
                
                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=False)
                
                assert client is not None
                mock_client.ping.assert_called_once()
    
    def test_get_redis_client_singleton_behavior(self):
        """Verify get_redis_client returns the same instance on subsequent calls"""
        mock_settings = MagicMock()
        mock_settings.testing = True
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None
        
        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('utils.redis_client.redis') as mock_redis_module:
                mock_client = MagicMock()
                mock_redis_module.from_url.return_value = mock_client
                
                import utils.redis_client as redis_client_module
                redis_client_module.redis_client = None
                
                from utils.redis_client import get_redis_client
                client1 = get_redis_client()
                client2 = get_redis_client()
                
                assert client1 is client2
                assert mock_redis_module.from_url.call_count == 1
