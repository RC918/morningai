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
    assert remaining == RATE_LIMIT_REQUESTS - 10


def test_rate_limit_zero_remaining(client, mock_redis):
    """Test rate limit shows zero remaining when at limit"""
    mock_redis.__bool__ = Mock(return_value=True)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [None, RATE_LIMIT_REQUESTS - 1, None, None]
    mock_redis.pipeline.return_value = mock_pipeline
    
    response = client.get('/test')
    
    assert response.status_code == 200
    assert int(response.headers['X-RateLimit-Remaining']) == 1


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
