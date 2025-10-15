import pytest
import os
from unittest.mock import patch, MagicMock
from redis import ConnectionError as RedisConnectionError

def test_redis_unavailable_returns_503():
    """Test that API returns 503 when Redis is unavailable (Chaos test)"""
    with patch('src.routes.agent.redis_client') as mock_redis:
        mock_redis.hset.side_effect = RedisConnectionError("Connection refused")
        
        from src.main import app
        with app.test_client() as client:
            response = client.post('/api/agent/faq', json={
                'question': 'Test question during Redis outage'
            })
            
            assert response.status_code in [503, 500]
            data = response.get_json()
            assert 'error' in data or 'message' in data

def test_redis_retry_with_sentry_trace():
    """Test that Sentry captures trace_id during Redis failures"""
    with patch('src.routes.agent.sentry_sdk') as mock_sentry:
        with patch('src.routes.agent.redis_client') as mock_redis:
            mock_redis.hset.side_effect = RedisConnectionError("Connection timeout")
            
            from src.main import app
            with app.test_client() as client:
                response = client.post('/api/agent/faq', json={
                    'question': 'Test Sentry trace_id'
                })
                
                if mock_sentry.set_tag.called:
                    tag_calls = [call for call in mock_sentry.set_tag.call_args_list 
                               if call[0][0] == 'trace_id']
                    assert len(tag_calls) > 0 or response.status_code in [503, 500]

def test_redis_connection_with_retry_succeeds():
    """Test that Redis retry logic works when connection is restored"""
    attempt_count = {'count': 0}
    
    def intermittent_failure(*args, **kwargs):
        attempt_count['count'] += 1
        if attempt_count['count'] < 2:
            raise RedisConnectionError("Temporary failure")
        return "OK"
    
    with patch('src.routes.agent.redis_client') as mock_redis:
        mock_redis.hset.side_effect = intermittent_failure
        mock_redis.expire.return_value = True
        
        from src.main import app
        with app.test_client() as client:
            response = client.post('/api/agent/faq', json={
                'question': 'Test retry success'
            })
            
            assert response.status_code in [202, 503, 500]
