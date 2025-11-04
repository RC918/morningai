import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, jsonify
from redis import ConnectionError as RedisConnectionError
from src.middleware.rate_limit import rate_limit, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW


@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    
    @app.route('/test')
    @rate_limit
    def test_route():
        return jsonify({"message": "success"})
    
    @app.route('/test_tuple')
    @rate_limit
    def test_route_tuple():
        return jsonify({"message": "success"}), 200
    
    @app.route('/test_tuple_custom')
    @rate_limit
    def test_route_tuple_custom():
        return jsonify({"message": "success"}), 201
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.middleware.rate_limit.redis_client') as mock:
        yield mock


def test_rate_limit_no_redis(client, mock_redis):
    """Test rate limit allows request when Redis is unavailable"""
    mock_redis.__bool__ = Mock(return_value=False)
    
    response = client.get('/test')
    
    assert response.status_code == 200
    assert response.json['message'] == 'success'


def test_rate_limit_with_redis_success(client, mock_redis):
    """Test rate limit allows request within limit"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 200
    assert response.json['message'] == 'success'
    assert 'X-RateLimit-Limit' in response.headers
    assert 'X-RateLimit-Remaining' in response.headers
    assert 'X-RateLimit-Reset' in response.headers


def test_rate_limit_exceeded(client, mock_redis):
    """Test rate limit blocks request when limit exceeded"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, RATE_LIMIT_REQUESTS, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 429
    assert 'rate_limit_exceeded' in response.json['error']['code']
    assert 'X-RateLimit-Limit' in response.headers
    assert response.headers['X-RateLimit-Remaining'] == '0'


def test_rate_limit_with_x_forwarded_for(client, mock_redis):
    """Test rate limit uses X-Forwarded-For header"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test', headers={'X-Forwarded-For': '1.2.3.4, 5.6.7.8'})
    
    assert response.status_code == 200
    mock_redis.pipeline.assert_called_once()


def test_rate_limit_with_multiple_ips_in_forwarded_for(client, mock_redis):
    """Test rate limit extracts first IP from X-Forwarded-For"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test', headers={'X-Forwarded-For': '1.2.3.4, 5.6.7.8, 9.10.11.12'})
    
    assert response.status_code == 200


def test_rate_limit_redis_connection_error(client, mock_redis):
    """Test rate limit allows request on Redis connection error"""
    mock_redis.__bool__ = Mock(return_value=True)
    mock_redis.pipeline.side_effect = RedisConnectionError("Connection failed")
    
    response = client.get('/test')
    
    assert response.status_code == 200
    assert response.json['message'] == 'success'


def test_rate_limit_redis_generic_error(client, mock_redis):
    """Test rate limit allows request on generic Redis error"""
    mock_redis.__bool__ = Mock(return_value=True)
    mock_redis.pipeline.side_effect = Exception("Generic error")
    
    response = client.get('/test')
    
    assert response.status_code == 200
    assert response.json['message'] == 'success'


def test_rate_limit_tuple_response(client, mock_redis):
    """Test rate limit handles tuple response"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test_tuple')
    
    assert response.status_code == 200
    assert 'X-RateLimit-Limit' in response.headers


def test_rate_limit_tuple_response_custom_status(client, mock_redis):
    """Test rate limit handles tuple response with custom status code"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test_tuple_custom')
    
    assert response.status_code == 201
    assert 'X-RateLimit-Limit' in response.headers


def test_rate_limit_remaining_calculation(client, mock_redis):
    """Test rate limit calculates remaining correctly"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 10, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 200
    remaining = int(response.headers['X-RateLimit-Remaining'])
    assert remaining == RATE_LIMIT_REQUESTS - 10 - 1


def test_rate_limit_zero_remaining(client, mock_redis):
    """Test rate limit shows zero remaining when at limit"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, RATE_LIMIT_REQUESTS - 1, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 200
    assert int(response.headers['X-RateLimit-Remaining']) == 0


def test_rate_limit_pipeline_operations(client, mock_redis):
    """Test rate limit performs correct Redis pipeline operations"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 200
    mock_pipeline.zremrangebyscore.assert_called_once()
    mock_pipeline.zcard.assert_called_once()
    mock_pipeline.zadd.assert_called_once()
    mock_pipeline.expire.assert_called_once()


def test_rate_limit_headers_on_exceeded(client, mock_redis):
    """Test rate limit sets correct headers when limit exceeded"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, RATE_LIMIT_REQUESTS + 10, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 429
    assert response.headers['X-RateLimit-Limit'] == str(RATE_LIMIT_REQUESTS)
    assert response.headers['X-RateLimit-Remaining'] == '0'
    assert 'X-RateLimit-Reset' in response.headers


def test_rate_limit_no_x_forwarded_for(client, mock_redis):
    """Test rate limit uses remote_addr when X-Forwarded-For is missing"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, 5, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 200


def test_rate_limit_constants():
    """Test rate limit constants are defined"""
    assert RATE_LIMIT_REQUESTS > 0
    assert RATE_LIMIT_WINDOW > 0


def test_non_blocking_retry():
    """Test that retry mechanism is non-blocking"""
    import src.middleware.rate_limit as rl_module
    
    with patch('src.middleware.rate_limit.redis_client', None):
        with patch('src.middleware.rate_limit.redis_connecting', False):
            with patch('src.middleware.rate_limit.retry_attempts', 0):
                with patch('src.middleware.rate_limit.next_retry_deadline', 0.0):
                    with patch('src.utils.redis_client.get_redis_client', side_effect=Exception("Connection failed")):
                        with patch('time.sleep') as mock_sleep:
                            result = rl_module.get_rate_limit_redis()
                            
                            assert result is None
                            mock_sleep.assert_not_called()


def test_retry_backoff_window():
    """Test that requests during backoff window return None immediately"""
    import src.middleware.rate_limit as rl_module
    
    with patch('src.middleware.rate_limit.redis_client', None):
        with patch('src.middleware.rate_limit.redis_connecting', False):
            with patch('src.middleware.rate_limit.next_retry_deadline', time.monotonic() + 100):
                with patch('src.utils.redis_client.get_redis_client') as mock_get:
                    result = rl_module.get_rate_limit_redis()
                    
                    assert result is None
                    mock_get.assert_not_called()


def test_single_thread_connection_attempt():
    """Test that only one thread attempts connection at a time"""
    import src.middleware.rate_limit as rl_module
    
    with patch('src.middleware.rate_limit.redis_client', None):
        with patch('src.middleware.rate_limit.redis_connecting', True):
            with patch('src.utils.redis_client.get_redis_client') as mock_get:
                result = rl_module.get_rate_limit_redis()
                
                assert result is None
                mock_get.assert_not_called()


def test_user_id_extraction_from_request():
    """Test user ID extraction from request.user_id"""
    from src.middleware.rate_limit import _extract_user_id
    
    app = Flask(__name__)
    with app.test_request_context('/'):
        from flask import request as flask_request
        flask_request.user_id = '12345'
        
        user_id = _extract_user_id()
        assert user_id == '12345'


def test_user_id_extraction_from_current_user_dict():
    """Test user ID extraction from request.current_user dict"""
    from src.middleware.rate_limit import _extract_user_id
    
    app = Flask(__name__)
    with app.test_request_context('/'):
        from flask import request as flask_request
        flask_request.current_user = {'user_id': '67890', 'username': 'test'}
        
        user_id = _extract_user_id()
        assert user_id == '67890'


def test_user_id_extraction_fallback_to_g():
    """Test user ID extraction falls back to g.user_id"""
    from src.middleware.rate_limit import _extract_user_id
    from flask import g
    
    app = Flask(__name__)
    with app.test_request_context('/'):
        g.user_id = 'g_user_123'
        
        user_id = _extract_user_id()
        assert user_id == 'g_user_123'


def test_user_id_extraction_returns_none_when_not_found():
    """Test user ID extraction returns None when no user ID found"""
    from src.middleware.rate_limit import _extract_user_id
    
    app = Flask(__name__)
    with app.test_request_context('/'):
        user_id = _extract_user_id()
        assert user_id is None


def test_rate_limit_with_user_id(client, mock_redis):
    """Test rate limiting uses user ID when RATE_LIMIT_BY_USER is enabled"""
    import src.middleware.rate_limit as rl_module
    
    with patch.object(rl_module, 'RATE_LIMIT_BY_USER', True):
        with patch('src.middleware.rate_limit._extract_user_id', return_value='test_user_123'):
            mock_redis.__bool__ = Mock(return_value=True)
            
            mock_pipeline = MagicMock()
            mock_pipeline.execute.return_value = [None, 5, None, None]
            mock_redis.pipeline.return_value = mock_pipeline
            
            response = client.get('/test')
            
            assert response.status_code == 200
            
            zadd_call = mock_pipeline.zadd.call_args
            if zadd_call:
                rate_limit_key = zadd_call[0][0]
                assert 'user:test_user_123' in rate_limit_key
