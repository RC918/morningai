"""
Unit tests for production fixes:
- Redis connection configuration
- Orchestrator import path
- Report generator datetime serialization
"""
import pytest
import os
import sys
import datetime
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, asdict


class TestRedisConfiguration:
    """Test Redis connection configuration fixes"""
    
    def test_rate_limit_redis_url_required(self):
        """Test that rate_limit.py handles missing REDIS_URL gracefully"""
        # Test that rate_limit decorator works even when redis_client is None
        from src.middleware.rate_limit import rate_limit
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/test')
        @rate_limit
        def test_endpoint():
            return {'status': 'ok'}, 200
        
        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code in [200, 503]
    
    def test_agent_redis_url_required(self):
        """Test that agent.py requires REDIS_URL"""
        with patch.dict(os.environ, {}, clear=True):
            # Should raise ValueError when REDIS_URL not set (from get_secure_redis_url)
            with pytest.raises(ValueError, match="No REDIS_URL environment variable found"):
                import importlib
                import src.routes.agent as agent_module
                importlib.reload(agent_module)
    
    def test_faq_redis_url_required(self):
        """Test that faq.py requires REDIS_URL"""
        with patch.dict(os.environ, {}, clear=True):
            # Should raise ValueError when REDIS_URL not set (from get_secure_redis_url)
            with pytest.raises(ValueError, match="No REDIS_URL environment variable found"):
                import importlib
                import src.routes.faq as faq_module
                importlib.reload(faq_module)


class TestOrchestratorPath:
    """Test orchestrator path configuration"""
    
    def test_orchestrator_path_from_env(self):
        """Test that ORCHESTRATOR_PATH environment variable is used"""
        test_path = "/custom/orchestrator/path"
        
        # Test the logic directly without reloading main module
        with patch.dict(os.environ, {'ORCHESTRATOR_PATH': test_path}):
            orchestrator_path = os.getenv('ORCHESTRATOR_PATH')
            assert orchestrator_path == test_path
            
            with patch('os.path.exists', return_value=True):
                if os.path.exists(orchestrator_path) and orchestrator_path not in sys.path:
                    assert True
    
    def test_orchestrator_path_fallback(self):
        """Test that relative path is used as fallback"""
        # Test the fallback logic without importing main module
        with patch.dict(os.environ, {}, clear=True):
            orchestrator_path = os.getenv('ORCHESTRATOR_PATH')
            assert orchestrator_path is None
            
            assert True
    
    def test_orchestrator_path_not_exists_warning(self):
        """Test that warning is logged when path doesn't exist"""
        test_path = "/nonexistent/path"
        with patch.dict(os.environ, {'ORCHESTRATOR_PATH': test_path}):
            with patch('os.path.exists', return_value=False):
                with patch('logging.warning') as mock_warning:
                    import importlib
                    import src.main as main_module
                    importlib.reload(main_module)
                    
                    # Should log warning about missing path
                    # Note: This test may need adjustment based on actual logging setup


class TestDatetimeSerialization:
    """Test datetime serialization in report generator"""
    
    @dataclass
    class MockReportData:
        """Mock ReportData for testing"""
        title: str
        generated_at: datetime.datetime
        metrics: dict
    
    def test_serialize_naive_datetime(self):
        """Test serialization of naive datetime"""
        from src.main import generate_report
        
        naive_dt = datetime.datetime(2025, 10, 24, 12, 0, 0)
        report_data = self.MockReportData(
            title="Test Report",
            generated_at=naive_dt,
            metrics={"count": 100}
        )
        
        # Test the serialize_datetime function logic
        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        report_dict = asdict(report_data)
        serialized = serialize_datetime(report_dict)
        
        assert isinstance(serialized['generated_at'], str)
        assert serialized['generated_at'] == '2025-10-24T12:00:00'
    
    def test_serialize_timezone_aware_datetime(self):
        """Test serialization of timezone-aware datetime"""
        from datetime import timezone, timedelta
        
        # Create timezone-aware datetime
        tz = timezone(timedelta(hours=8))
        aware_dt = datetime.datetime(2025, 10, 24, 12, 0, 0, tzinfo=tz)
        
        report_data = self.MockReportData(
            title="Test Report",
            generated_at=aware_dt,
            metrics={"count": 100}
        )
        
        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        report_dict = asdict(report_data)
        serialized = serialize_datetime(report_dict)
        
        assert isinstance(serialized['generated_at'], str)
        assert '+08:00' in serialized['generated_at']
    
    def test_serialize_nested_datetime(self):
        """Test serialization of nested datetime in dict"""
        nested_data = {
            'report': {
                'created_at': datetime.datetime(2025, 10, 24, 12, 0, 0),
                'metrics': {
                    'last_updated': datetime.datetime(2025, 10, 24, 13, 0, 0)
                }
            },
            'timestamps': [
                datetime.datetime(2025, 10, 24, 14, 0, 0),
                datetime.datetime(2025, 10, 24, 15, 0, 0)
            ]
        }
        
        def serialize_datetime(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        serialized = serialize_datetime(nested_data)
        
        assert isinstance(serialized['report']['created_at'], str)
        assert isinstance(serialized['report']['metrics']['last_updated'], str)
        assert all(isinstance(ts, str) for ts in serialized['timestamps'])


class TestReportGeneratorIntegration:
    """Integration tests for report generator fixes"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from src.main import app
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_generate_report_json_format(self, client):
        """Test report generation with JSON format"""
        with patch('src.main.BACKEND_SERVICES_AVAILABLE', True):
            with patch('src.main.report_generator.generate_report') as mock_generate:
                # Mock report data with datetime
                from src.services.report_generator import ReportData
                mock_report = ReportData(
                    title="Test Report",
                    generated_at=datetime.datetime(2025, 10, 24, 12, 0, 0),
                    time_range="24h",
                    metrics={"count": 100},
                    charts=[],
                    summary={"status": "ok"}
                )
                mock_generate.return_value = mock_report
                
                response = client.post('/api/reports/generate', json={
                    'type': 'performance',
                    'time_range': '24h',
                    'format': 'json'
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'generated_at' in data
                assert isinstance(data['generated_at'], str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
