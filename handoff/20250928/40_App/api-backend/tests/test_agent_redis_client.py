"""
Unit tests for get_agent_redis_client() sentinel pattern

Tests verify that the sentinel-based initialization works correctly:
- Default behavior: lazy initialization creates Redis client
- Explicit None: returns None (simulates Redis unavailable)
- Explicit mock: returns the mock (test override)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from redis import Redis


class TestGetAgentRedisClientSentinel:
    """Test get_agent_redis_client() sentinel pattern for lazy initialization"""
    
    def test_default_creates_client_when_unset(self, monkeypatch):
        """Default behavior: lazy initialization creates Redis client on first call"""
        import src.routes.agent as agent_module
        agent_module._redis_client = None
        agent_module.redis_client = agent_module._UNSET
        
        mock_redis = Mock(spec=Redis)
        with patch('src.routes.agent.Redis.from_url', return_value=mock_redis) as mock_from_url:
            from src.routes.agent import get_agent_redis_client
            
            result = get_agent_redis_client()
            assert result is mock_redis
            
            result2 = get_agent_redis_client()
            assert result2 is mock_redis
            
            assert mock_from_url.call_count == 1
    
    def test_explicit_none_is_respected(self, monkeypatch):
        """Explicit None: returns None (simulates Redis unavailable in tests)"""
        import src.routes.agent as agent_module
        
        agent_module.redis_client = None
        
        from src.routes.agent import get_agent_redis_client
        
        result = get_agent_redis_client()
        assert result is None
    
    def test_explicit_mock_is_respected(self, monkeypatch):
        """Explicit mock: returns the mock (test override)"""
        import src.routes.agent as agent_module
        
        mock_redis = Mock(spec=Redis)
        agent_module.redis_client = mock_redis
        
        from src.routes.agent import get_agent_redis_client
        
        result = get_agent_redis_client()
        assert result is mock_redis
    
    def test_patch_to_none_works(self, monkeypatch):
        """Test that patching redis_client to None works (common test pattern)"""
        with patch('src.routes.agent.redis_client', None):
            from src.routes.agent import get_agent_redis_client
            
            result = get_agent_redis_client()
            assert result is None
    
    def test_patch_to_mock_works(self, monkeypatch):
        """Test that patching redis_client to mock works (common test pattern)"""
        mock_redis = Mock(spec=Redis)
        with patch('src.routes.agent.redis_client', mock_redis):
            from src.routes.agent import get_agent_redis_client
            
            result = get_agent_redis_client()
            assert result is mock_redis
    
    def test_lazy_init_uses_correct_config(self, monkeypatch):
        """Verify lazy initialization uses correct Redis configuration"""
        import src.routes.agent as agent_module
        agent_module._redis_client = None
        agent_module.redis_client = agent_module._UNSET
        
        mock_redis = Mock(spec=Redis)
        
        with patch('src.routes.agent.Redis.from_url', return_value=mock_redis) as mock_from_url:
            from src.routes.agent import get_agent_redis_client
            
            result = get_agent_redis_client()
            
            assert mock_from_url.called
            call_kwargs = mock_from_url.call_args[1]
            assert call_kwargs['decode_responses'] is True
            assert call_kwargs['socket_connect_timeout'] == 5
            assert call_kwargs['socket_timeout'] == 30
            assert 'retry' in call_kwargs
            assert call_kwargs['retry_on_timeout'] is True
    
    def test_subsequent_calls_return_cached_client(self, monkeypatch):
        """Verify subsequent calls return cached client without re-initialization"""
        import src.routes.agent as agent_module
        agent_module._redis_client = None
        agent_module.redis_client = agent_module._UNSET
        
        mock_redis = Mock(spec=Redis)
        
        with patch('src.routes.agent.Redis.from_url', return_value=mock_redis) as mock_from_url:
            from src.routes.agent import get_agent_redis_client
            
            result1 = get_agent_redis_client()
            call_count_after_first = mock_from_url.call_count
            
            result2 = get_agent_redis_client()
            call_count_after_second = mock_from_url.call_count
            
            assert result1 is result2
            assert result1 is mock_redis
            
            assert call_count_after_first == 1
            assert call_count_after_second == 1
    
    def test_sentinel_value_is_not_none(self):
        """Verify sentinel value is distinct from None"""
        from src.routes.agent import _UNSET
        
        assert _UNSET is not None
        assert _UNSET != None
        assert type(_UNSET) is object
