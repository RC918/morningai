"""
Integration test for 503 dual failure scenario using DB health check seam
"""
import pytest
from unittest.mock import patch
from src.main import app


class TestDashboard503Integration:
    """Test 503 Service Unavailable response when both Redis and DB fail"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_dual_failure_returns_503_with_health_seam(self, client):
        """Test dashboard returns 503 when both Redis and DB fail using check_db_health seam"""
        with patch('src.utils.redis_client.get_redis_client') as mock_redis, \
             patch('src.routes.dashboard.check_db_health') as mock_db_health:
            
            # Simulate Redis failure
            mock_redis.side_effect = Exception("Redis connection failed")
            
            # Simulate DB failure using the health check seam
            mock_db_health.return_value = (False, "Database connection failed")
            
            response = client.get('/api/phase7/monitoring/dashboard')
            
            # Verify 503 status code
            assert response.status_code == 503
            data = response.get_json()
            
            # Verify response structure matches ServiceUnavailableError schema
            assert 'error' in data
            assert data['error'] == 'Core services unavailable'
            assert 'message' in data
            assert data['message'] == 'Both Redis and Database connections failed'
            assert 'status' in data
            assert data['status'] == 'service_unavailable'
            
            print("✅ 503 dual failure test passed with health check seam")

    def test_db_failure_only_returns_200_degraded(self, client):
        """Test dashboard returns 200 with degraded status when only DB fails"""
        from unittest.mock import MagicMock
        
        mock_redis_client = MagicMock()
        mock_redis_client.llen.return_value = 5
        
        with patch('src.utils.redis_client.get_redis_client', return_value=mock_redis_client), \
             patch('src.routes.dashboard.check_db_health') as mock_db_health:
            
            # Simulate DB failure only (Redis is healthy)
            mock_db_health.return_value = (False, "Database connection failed")
            
            response = client.get('/api/phase7/monitoring/dashboard')
            
            # Should still return 200 (not 503) since Redis is available
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify degraded status
            assert data['system_health']['overall_status'] == 'degraded'
            
            # Verify DB error alert
            db_alerts = [a for a in data['alerts'] if a.get('id') == 'db_error']
            assert len(db_alerts) > 0
            assert db_alerts[0]['severity'] == 'critical'
            
            print("✅ DB-only failure test passed")
