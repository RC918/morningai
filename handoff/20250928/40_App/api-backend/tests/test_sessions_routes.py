"""
Tests for sessions routes (Session Control endpoints)
PR 3: Controls + HITL Integration
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create Flask app for testing"""
    with patch.dict(os.environ, {
        'TESTING': 'true',
        'JWT_SECRET_KEY': 'test-secret-key-that-is-at-least-32-characters-long',
        'FLASK_SECRET_KEY': 'test-flask-secret-key-at-least-32-chars',
        'SENTRY_DSN': ''
    }):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']
        
        from src.main import app as flask_app
        from src.models.user import db
        
        flask_app.config['TESTING'] = True
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with flask_app.app_context():
            db.create_all()
            yield flask_app
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client"""
    mock = MagicMock()
    return mock


@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        'session_id': 'test-session-123',
        'task_id': 'task-456',
        'goal': 'Test goal',
        'status': 'active',
        'current_phase': 'observe',
        'iteration': 0,
        'max_iterations': 10,
        'observations': [],
        'decisions': [],
        'actions': [],
        'attempted_solutions': [],
        'context': {},
        'conversation_history': [],
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:30:00Z'
    }


class TestSessionsListEndpoint:
    """Tests for GET /api/sessions endpoint"""
    
    def test_list_sessions_no_auth(self, client):
        """Test GET /api/sessions without authentication returns 401"""
        response = client.get('/api/sessions')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_list_sessions_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test GET /api/sessions returns session list"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [b'dev_agent:session:test-123']
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.get('/api/sessions', headers=auth_headers_admin)
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'sessions' in data
                assert 'total' in data
                assert 'page' in data
                assert 'perPage' in data


class TestSessionDetailEndpoint:
    """Tests for GET /api/sessions/:id endpoint"""
    
    def test_get_session_detail_no_auth(self, client):
        """Test GET /api/sessions/:id without authentication returns 401"""
        response = client.get('/api/sessions/test-session-123')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_get_session_detail_not_found(self, client, auth_headers_admin, mock_redis_client):
        """Test GET /api/sessions/:id returns 404 for non-existent session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = None
                
                response = client.get('/api/sessions/non-existent', headers=auth_headers_admin)
                
                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data
    
    def test_get_session_detail_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test GET /api/sessions/:id returns session details"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.get('/api/sessions/test-session-123', headers=auth_headers_admin)
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'id' in data
                assert 'status' in data
                assert 'goal' in data


class TestPauseSessionEndpoint:
    """Tests for POST /api/sessions/:id/pause endpoint"""
    
    def test_pause_session_no_auth(self, client):
        """Test POST /api/sessions/:id/pause without authentication returns 401"""
        response = client.post('/api/sessions/test-session-123/pause')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_pause_session_not_found(self, client, auth_headers_admin, mock_redis_client):
        """Test POST /api/sessions/:id/pause returns 404 for non-existent session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = None
                
                response = client.post('/api/sessions/non-existent/pause', headers=auth_headers_admin)
                
                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data
    
    def test_pause_session_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/pause pauses an active session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'paused'
                assert 'paused_by' in data
                assert 'timestamp' in data
    
    def test_pause_session_already_paused(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/pause returns 400 for already paused session"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)
                
                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data


class TestResumeSessionEndpoint:
    """Tests for POST /api/sessions/:id/resume endpoint"""
    
    def test_resume_session_no_auth(self, client):
        """Test POST /api/sessions/:id/resume without authentication returns 401"""
        response = client.post('/api/sessions/test-session-123/resume')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_resume_session_not_found(self, client, auth_headers_admin, mock_redis_client):
        """Test POST /api/sessions/:id/resume returns 404 for non-existent session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = None
                
                response = client.post('/api/sessions/non-existent/resume', headers=auth_headers_admin)
                
                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data
    
    def test_resume_session_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/resume resumes a paused session"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post('/api/sessions/test-session-123/resume', headers=auth_headers_admin)
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'active'
                assert 'resumed_by' in data
                assert 'timestamp' in data
    
    def test_resume_session_not_paused(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/resume returns 400 for active session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post('/api/sessions/test-session-123/resume', headers=auth_headers_admin)
                
                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data


class TestCancelSessionEndpoint:
    """Tests for POST /api/sessions/:id/cancel endpoint"""
    
    def test_cancel_session_no_auth(self, client):
        """Test POST /api/sessions/:id/cancel without authentication returns 401"""
        response = client.post('/api/sessions/test-session-123/cancel')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_cancel_session_not_found(self, client, auth_headers_admin, mock_redis_client):
        """Test POST /api/sessions/:id/cancel returns 404 for non-existent session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = None
                
                response = client.post('/api/sessions/non-existent/cancel', headers=auth_headers_admin)
                
                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data
    
    def test_cancel_session_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/cancel cancels an active session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post(
                    '/api/sessions/test-session-123/cancel',
                    headers=auth_headers_admin,
                    json={'reason': 'Test cancellation'}
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'failed'
                assert 'cancelled_by' in data
                assert data['reason'] == 'Test cancellation'
                assert 'timestamp' in data
    
    def test_cancel_session_already_completed(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/cancel returns 400 for completed session"""
        sample_session_data['status'] = 'completed'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post('/api/sessions/test-session-123/cancel', headers=auth_headers_admin)
                
                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
    
    def test_cancel_session_already_failed(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/cancel returns 400 for failed session"""
        sample_session_data['status'] = 'failed'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                
                response = client.post('/api/sessions/test-session-123/cancel', headers=auth_headers_admin)
                
                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data


class TestSessionsHealthEndpoint:
    """Tests for GET /api/sessions/health endpoint"""
    
    def test_health_check_redis_available(self, client):
        """Test GET /api/sessions/health when Redis is available"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', True):
            response = client.get('/api/sessions/health')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['sessions_available'] is True
            assert data['status'] == 'healthy'
            assert 'timestamp' in data
    
    def test_health_check_redis_unavailable(self, client):
        """Test GET /api/sessions/health when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.get('/api/sessions/health')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['sessions_available'] is False
            assert data['status'] == 'degraded'


class TestRedisUnavailable:
    """Tests for Redis unavailable scenarios"""
    
    def test_list_sessions_redis_unavailable(self, client, auth_headers_admin):
        """Test GET /api/sessions returns 503 when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.get('/api/sessions', headers=auth_headers_admin)
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert data['sessions_available'] is False
    
    def test_pause_session_redis_unavailable(self, client, auth_headers_admin):
        """Test POST /api/sessions/:id/pause returns 503 when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.post('/api/sessions/test-123/pause', headers=auth_headers_admin)
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
    
    def test_resume_session_redis_unavailable(self, client, auth_headers_admin):
        """Test POST /api/sessions/:id/resume returns 503 when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.post('/api/sessions/test-123/resume', headers=auth_headers_admin)
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
    
    def test_cancel_session_redis_unavailable(self, client, auth_headers_admin):
        """Test POST /api/sessions/:id/cancel returns 503 when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.post('/api/sessions/test-123/cancel', headers=auth_headers_admin)
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
