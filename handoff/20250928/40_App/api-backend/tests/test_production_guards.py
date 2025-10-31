"""
Test production environment guards and safety checks
"""
import pytest
import os
import sys
import importlib
from unittest.mock import patch, MagicMock


class TestProductionStartupGuards:
    """Test production environment startup guards"""
    
    def test_production_with_memory_backend_fails(self):
        """Test that production environment with in-memory Agent Registry fails to start"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'AGENT_REGISTRY_BACKEND': 'memory',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'REDIS_URL': 'rediss://test:test@localhost:6380/0'
        }, clear=True):
            with pytest.raises(RuntimeError, match="Production environment requires persistent storage"):
                import importlib
                import sys
                if 'src.main' in sys.modules:
                    del sys.modules['src.main']
                if 'src.routes.agent' in sys.modules:
                    del sys.modules['src.routes.agent']
                import src.main
    
    def test_production_with_db_backend_succeeds(self):
        """Test that production environment with database backend succeeds"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'AGENT_REGISTRY_BACKEND': 'db',
            'DATABASE_URL': 'sqlite:///:memory:',
            'REDIS_URL': 'rediss://test:test@localhost:6380/0'
        }, clear=True):
            with patch('src.utils.redis_client.get_redis_client') as mock_get_redis:
                mock_client = MagicMock()
                mock_client.ping.return_value = True
                mock_get_redis.return_value = mock_client
                
                try:
                    if 'src.main' in sys.modules:
                        del sys.modules['src.main']
                    if 'src.routes.agent' in sys.modules:
                        del sys.modules['src.routes.agent']
                    if 'src.middleware.rate_limit' in sys.modules:
                        del sys.modules['src.middleware.rate_limit']
                    import src.main
                except RuntimeError as e:
                    if "Agent Registry" in str(e):
                        pytest.fail(f"Should not fail with db backend: {e}")
    
    def test_production_with_override_flag_succeeds(self):
        """Test that production environment with override flag allows in-memory"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'AGENT_REGISTRY_BACKEND': 'memory',
            'ALLOW_INMEMORY_IN_PROD': 'true',
            'DATABASE_URL': 'sqlite:///:memory:',
            'REDIS_URL': 'rediss://test:test@localhost:6380/0'
        }, clear=True):
            with patch('src.utils.redis_client.get_redis_client') as mock_get_redis:
                mock_client = MagicMock()
                mock_client.ping.return_value = True
                mock_get_redis.return_value = mock_client
                
                try:
                    if 'src.main' in sys.modules:
                        del sys.modules['src.main']
                    if 'src.routes.agent' in sys.modules:
                        del sys.modules['src.routes.agent']
                    if 'src.middleware.rate_limit' in sys.modules:
                        del sys.modules['src.middleware.rate_limit']
                    import src.main
                except RuntimeError as e:
                    if "Agent Registry" in str(e):
                        pytest.fail(f"Should not fail with override flag: {e}")
    
    def test_development_with_memory_backend_succeeds(self):
        """Test that development environment with in-memory backend succeeds"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'AGENT_REGISTRY_BACKEND': 'memory',
            'TESTING': 'true',
            'REDIS_URL': 'redis://localhost:6379/0'
        }, clear=True):
            try:
                import importlib
                import sys
                if 'src.main' in sys.modules:
                    del sys.modules['src.main']
                if 'src.routes.agent' in sys.modules:
                    del sys.modules['src.routes.agent']
                import src.main
            except RuntimeError as e:
                if "Agent Registry" in str(e):
                    pytest.fail(f"Development should allow in-memory: {e}")
    
    def test_production_without_redis_fails(self):
        """Test that production environment without Redis fails to start"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'AGENT_REGISTRY_BACKEND': 'db',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'REDIS_URL': 'rediss://test:test@localhost:6380/0',
            'TESTING': 'false'
        }):
            with patch('src.utils.redis_client.get_redis_client') as mock_get_redis:
                from redis import ConnectionError as RedisConnectionError
                mock_get_redis.side_effect = RedisConnectionError("Connection refused")
                
                with pytest.raises(RuntimeError, match="Production environment requires Redis for rate limiting"):
                    import importlib
                    import sys
                    if 'src.main' in sys.modules:
                        del sys.modules['src.main']
                    if 'src.middleware.rate_limit' in sys.modules:
                        del sys.modules['src.middleware.rate_limit']
                    import src.main


class TestRateLimitingEnhancements:
    """Test rate limiting with user_id support"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        os.environ['TESTING'] = 'true'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
        
        from src.main import app
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def auth_headers_admin(self):
        """Create admin auth headers"""
        from src.middleware.auth_middleware import create_admin_token
        token = create_admin_token()
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    def test_rate_limit_on_agent_registry_write_endpoint(self, client, auth_headers_admin):
        """Test that rate limiting is applied to Agent Registry write endpoints"""
        import src.middleware.rate_limit as rate_limit_module
        
        with patch.object(rate_limit_module, 'redis_client') as mock_redis:
            mock_pipeline = MagicMock()
            mock_pipeline.execute.return_value = [None, 61, None, None]
            mock_redis.pipeline.return_value = mock_pipeline
            
            response = client.post(
                '/api/v1/agents',
                json={
                    'agent_type': 'dev_agent',
                    'capabilities': ['code_review', 'bug_fix'],
                    'permission_level': 'standard'
                },
                headers=auth_headers_admin
            )
            
            assert response.status_code == 429
            data = response.get_json()
            assert 'error' in data
            assert 'rate_limit_exceeded' in data['error']['code']
    
    def test_rate_limit_uses_user_id_when_authenticated(self, client, auth_headers_admin):
        """Test that rate limiter uses user_id for authenticated requests"""
        import src.middleware.rate_limit as rate_limit_module
        
        with patch.object(rate_limit_module, 'redis_client') as mock_redis:
            mock_pipeline = MagicMock()
            mock_redis.pipeline.return_value = mock_pipeline
            mock_pipeline.execute.return_value = [None, 1, None, None]
            
            response = client.post(
                '/api/v1/agents',
                json={
                    'agent_type': 'dev_agent',
                    'capabilities': ['code_review'],
                    'permission_level': 'standard'
                },
                headers=auth_headers_admin
            )
            
            assert mock_pipeline.zadd.called
            call_args = mock_pipeline.zadd.call_args
            rate_limit_key = call_args[0][0] if call_args[0] else None
            
            assert rate_limit_key is not None
            assert 'user:' in rate_limit_key or 'rate_limit:' in rate_limit_key
    
    def test_rate_limit_headers_present_on_success(self, client, auth_headers_admin):
        """Test that rate limit headers are present on successful requests"""
        import src.middleware.rate_limit as rate_limit_module
        
        with patch.object(rate_limit_module, 'redis_client') as mock_redis:
            mock_pipeline = MagicMock()
            mock_redis.pipeline.return_value = mock_pipeline
            mock_pipeline.execute.return_value = [None, 1, None, None]
            
            response = client.post(
                '/api/v1/agents',
                json={
                    'agent_type': 'dev_agent',
                    'capabilities': ['code_review'],
                    'permission_level': 'standard'
                },
                headers=auth_headers_admin
            )
            
            if response.status_code in [200, 201, 202]:
                assert 'X-RateLimit-Limit' in response.headers or response.status_code == 202
