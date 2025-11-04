"""
Tests for monitoring dashboard degradation paths
Tests Redis failure, DB failure, and dual failure scenarios
"""
import pytest
from unittest.mock import patch, MagicMock
from src.main import app


class TestDashboardDegradationPaths:
    """Test degradation behavior of /api/phase7/monitoring/dashboard endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_redis_failure_degradation(self, client):
        """Test dashboard returns fallback data when Redis fails"""
        with patch('src.utils.redis_client.get_redis_client') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            response = client.get('/api/phase7/monitoring/dashboard')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'metrics' in data
            assert 'queue_depth' in data['metrics']
            queue_depth = data['metrics']['queue_depth']
            
            assert queue_depth.get('available') == False
            assert queue_depth.get('source') == 'fallback'
            assert queue_depth.get('error') == 'Redis unavailable'
            assert queue_depth.get('current') == 0
            assert queue_depth.get('trend') == 'unknown'
            
            assert data['system_health']['overall_status'] in ['healthy', 'degraded']

    def test_db_failure_degradation(self, client):
        """Test dashboard returns fallback data when DB fails"""
        with patch('src.extensions.db.engine.connect') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.get('/api/phase7/monitoring/dashboard')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'metrics' in data
            assert 'active_agents' in data['metrics']
            active_agents = data['metrics']['active_agents']
            
            assert active_agents.get('available') == False
            assert active_agents.get('source') == 'fallback'
            assert active_agents.get('error') == 'Database unavailable'
            assert active_agents.get('current') == 0
            
            assert data['agents'] == []
            
            assert data['system_health']['overall_status'] == 'degraded'
            
            alerts = data.get('alerts', [])
            db_alerts = [a for a in alerts if 'database' in a.get('message', '').lower()]
            assert len(db_alerts) > 0

    def test_dual_failure_returns_503(self, client):
        """Test dashboard returns 503 Service Unavailable when both Redis and DB fail"""
        with patch('src.utils.redis_client.get_redis_client') as mock_redis, \
             patch('src.extensions.db.engine.connect') as mock_db:
            
            mock_redis.side_effect = Exception("Redis connection failed")
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.get('/api/phase7/monitoring/dashboard')
            
            assert response.status_code == 503
            data = response.get_json()
            
            assert 'error' in data
            assert data.get('status') == 'service_unavailable'

    def test_redis_failure_with_computed_false(self, client):
        """Test that agent metrics include computed: false when using fallback"""
        with patch('src.utils.redis_client.get_redis_client') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            response = client.get('/api/phase7/monitoring/dashboard')
            
            assert response.status_code == 200
            data = response.get_json()
            
            if data.get('agents'):
                for agent in data['agents']:
                    assert 'computed' in agent
                    assert agent['computed'] == False
