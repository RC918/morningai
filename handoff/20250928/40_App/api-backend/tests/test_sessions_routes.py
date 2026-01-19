"""
Tests for sessions routes (Session Control endpoints)
PR 3: Controls + HITL Integration
PR B: Unit tests for #1982
"""
import pytest
import os
import sys
import json
import redis
from unittest.mock import patch, MagicMock

from src.routes.sessions import transform_session_for_frontend, _extract_ide_activity


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
                mock_redis_client.mget.return_value = [json.dumps(sample_session_data)]

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert 'sessions' in data
                assert 'total' in data
                assert 'page' in data
                assert 'perPage' in data
                assert 'counts' in data


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
                # Issue #1989: status should be 'running' (frontend format) not 'active' (internal)
                assert data['status'] == 'running'
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


class TestTransformSessionForFrontend:
    """Tests for transform_session_for_frontend() function - Issue #1982"""

    def test_transform_basic_session(self):
        """Test basic session transformation"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test goal',
            'status': 'active',
            'iteration': 5,
            'max_iterations': 10,
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)

        assert result['id'] == 'test-123'
        assert result['goal'] == 'Test goal'
        assert result['status'] == 'running'
        assert result['progress'] == 50
        assert result['startedAt'] == '2024-01-15T10:00:00Z'
        assert result['updatedAt'] == '2024-01-15T10:30:00Z'

    def test_transform_status_mapping(self):
        """Test status mapping from internal to frontend format"""
        test_cases = [
            ('active', 'running'),
            ('paused', 'paused'),
            ('completed', 'completed'),
            ('failed', 'failed'),
            ('escalated', 'paused'),
            ('unknown', 'running'),
        ]

        for internal_status, expected_frontend_status in test_cases:
            session_data = {
                'session_id': 'test-123',
                'goal': 'Test',
                'status': internal_status,
                'iteration': 0,
                'max_iterations': 10,
                'decisions': [],
                'actions': [],
                'observations': []
            }
            result = transform_session_for_frontend(session_data)
            assert result['status'] == expected_frontend_status, f"Expected {expected_frontend_status} for {internal_status}"

    def test_transform_progress_calculation(self):
        """Test progress calculation based on iterations"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 3,
            'max_iterations': 10,
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['progress'] == 30

    def test_transform_progress_max_100(self):
        """Test progress is capped at 100%"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 15,
            'max_iterations': 10,
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['progress'] == 100

    def test_transform_progress_zero_max_iterations(self):
        """Test progress when max_iterations is 0"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 5,
            'max_iterations': 0,
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['progress'] == 0

    def test_transform_with_tasks(self):
        """Test transformation with decisions and actions"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 2,
            'max_iterations': 10,
            'decisions': [
                {'decision': 'Analyze code', 'action_type': 'analyze_code'},
                {'decision': 'Fix bug', 'action_type': 'fix_bug'}
            ],
            'actions': [
                {'success': True, 'result': {'message': 'Done'}},
            ],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['plan']['totalTasks'] == 2
        assert result['plan']['completedTasks'] == 1
        assert len(result['plan']['tasks']) == 2
        assert result['plan']['tasks'][0]['status'] == 'completed'
        assert result['plan']['tasks'][1]['status'] == 'running'

    def test_transform_confidence_calculation(self):
        """Test confidence calculation based on action success rate"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 4,
            'max_iterations': 10,
            'decisions': [],
            'actions': [
                {'success': True, 'timestamp': '2024-01-15T10:00:00Z'},
                {'success': True, 'timestamp': '2024-01-15T10:01:00Z'},
                {'success': False, 'timestamp': '2024-01-15T10:02:00Z'},
                {'success': True, 'timestamp': '2024-01-15T10:03:00Z'}
            ],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['confidence'] == 0.75

    def test_transform_confidence_no_actions(self):
        """Test confidence defaults to 0.5 when no actions"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 0,
            'max_iterations': 10,
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['confidence'] == 0.5

    def test_transform_requires_approval(self):
        """Test requiresApproval flag for escalated sessions"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'escalated',
            'iteration': 0,
            'max_iterations': 10,
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert result['requiresApproval'] is True
        assert result['approvalReason'] == 'Task escalated for human review'

    def test_transform_title_truncation(self):
        """Test title is truncated to 50 characters"""
        long_goal = 'A' * 100
        session_data = {
            'session_id': 'test-123',
            'goal': long_goal,
            'status': 'active',
            'iteration': 0,
            'max_iterations': 10,
            'decisions': [],
            'actions': [],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)
        assert len(result['title']) == 50
        assert result['goal'] == long_goal


class TestSessionsListPagination:
    """Tests for pagination in list_sessions() - Issue #1982"""

    def test_list_sessions_pagination(self, client, auth_headers_admin, mock_redis_client):
        """Test pagination parameters work correctly"""
        sessions = []
        for i in range(10):
            sessions.append({
                'session_id': f'session-{i}',
                'goal': f'Goal {i}',
                'status': 'active',
                'iteration': 0,
                'max_iterations': 10,
                'updated_at': f'2024-01-15T10:{i:02d}:00Z',
                'decisions': [],
                'actions': [],
                'observations': []
            })

        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [f'dev_agent:session:session-{i}'.encode() for i in range(10)]
                mock_redis_client.mget.return_value = [json.dumps(s) for s in sessions]

                response = client.get('/api/sessions?limit=3&page=2', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['page'] == 2
                assert data['perPage'] == 3
                assert len(data['sessions']) <= 3

    def test_list_sessions_limit_max(self, client, auth_headers_admin, mock_redis_client):
        """Test limit is capped at 200"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = []

                response = client.get('/api/sessions?limit=500', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['perPage'] == 200

    def test_list_sessions_page_min(self, client, auth_headers_admin, mock_redis_client):
        """Test page is at least 1"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = []

                response = client.get('/api/sessions?page=0', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['page'] == 1


class TestSessionsListFiltering:
    """Tests for status filtering in list_sessions() - Issue #1982"""

    def test_list_sessions_filter_running(self, client, auth_headers_admin, mock_redis_client):
        """Test filtering by running status"""
        sessions = [
            {'session_id': 'active-1', 'goal': 'Active', 'status': 'active', 'iteration': 0, 'max_iterations': 10, 'updated_at': '2024-01-15T10:00:00Z', 'decisions': [], 'actions': [], 'observations': []},
            {'session_id': 'paused-1', 'goal': 'Paused', 'status': 'paused', 'iteration': 0, 'max_iterations': 10, 'updated_at': '2024-01-15T10:00:00Z', 'decisions': [], 'actions': [], 'observations': []},
        ]

        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [b'dev_agent:session:active-1', b'dev_agent:session:paused-1']
                mock_redis_client.mget.return_value = [json.dumps(s) for s in sessions]

                response = client.get('/api/sessions?status=running', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['filters']['status'] == 'running'
                assert all(s['status'] == 'running' for s in data['sessions'])

    def test_list_sessions_filter_completed(self, client, auth_headers_admin, mock_redis_client):
        """Test filtering by completed status"""
        sessions = [
            {'session_id': 'completed-1', 'goal': 'Completed', 'status': 'completed', 'iteration': 10, 'max_iterations': 10, 'updated_at': '2024-01-15T10:00:00Z', 'decisions': [], 'actions': [], 'observations': []},
            {'session_id': 'active-1', 'goal': 'Active', 'status': 'active', 'iteration': 0, 'max_iterations': 10, 'updated_at': '2024-01-15T10:00:00Z', 'decisions': [], 'actions': [], 'observations': []},
        ]

        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [b'dev_agent:session:completed-1', b'dev_agent:session:active-1']
                mock_redis_client.mget.return_value = [json.dumps(s) for s in sessions]

                response = client.get('/api/sessions?status=completed', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['filters']['status'] == 'completed'
                assert all(s['status'] == 'completed' for s in data['sessions'])


class TestSessionsErrorHandling:
    """Tests for error handling paths - Issue #1982"""

    def test_list_sessions_json_decode_error(self, client, auth_headers_admin, mock_redis_client):
        """Test list_sessions handles JSON decode errors gracefully"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [b'dev_agent:session:test-1', b'dev_agent:session:test-2']
                mock_redis_client.mget.return_value = ['invalid json', json.dumps({
                    'session_id': 'test-2',
                    'goal': 'Valid',
                    'status': 'active',
                    'iteration': 0,
                    'max_iterations': 10,
                    'updated_at': '2024-01-15T10:00:00Z',
                    'decisions': [],
                    'actions': [],
                    'observations': []
                })]

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert len(data['sessions']) == 1

    def test_get_session_detail_json_decode_error(self, client, auth_headers_admin, mock_redis_client):
        """Test get_session_detail handles JSON decode errors"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = 'invalid json'

                response = client.get('/api/sessions/test-123', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_pause_session_json_decode_error(self, client, auth_headers_admin, mock_redis_client):
        """Test pause_session handles JSON decode errors"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = 'invalid json'

                response = client.post('/api/sessions/test-123/pause', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_resume_session_json_decode_error(self, client, auth_headers_admin, mock_redis_client):
        """Test resume_session handles JSON decode errors"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = 'invalid json'

                response = client.post('/api/sessions/test-123/resume', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_cancel_session_json_decode_error(self, client, auth_headers_admin, mock_redis_client):
        """Test cancel_session handles JSON decode errors"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = 'invalid json'

                response = client.post('/api/sessions/test-123/cancel', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_list_sessions_general_exception(self, client, auth_headers_admin, mock_redis_client):
        """Test list_sessions handles general exceptions"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.side_effect = Exception('Redis connection error')

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data


class TestRequireRedisAvailableDecorator:
    """Tests for require_redis_available decorator - Issue #1982"""

    def test_decorator_allows_when_redis_available(self, client, auth_headers_admin, mock_redis_client):
        """Test decorator allows request when Redis is available"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = []
                mock_redis_client.mget.return_value = []

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 200

    def test_decorator_blocks_when_redis_unavailable(self, client, auth_headers_admin):
        """Test decorator returns 503 when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.get('/api/sessions', headers=auth_headers_admin)

            assert response.status_code == 503
            data = response.get_json()
            assert data['error'] == 'Redis not available'
            assert data['sessions_available'] is False


class TestSendCommandEndpoint:
    """Tests for POST /api/sessions/:id/command endpoint - Issue #2179"""

    def test_send_command_no_auth(self, client):
        """Test POST /api/sessions/:id/command without authentication returns 401"""
        response = client.post(
            '/api/sessions/test-session-123/command',
            json={'command': 'test command'}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_send_command_redis_unavailable(self, client, auth_headers_admin):
        """Test POST /api/sessions/:id/command returns 503 when Redis is unavailable"""
        with patch('src.routes.sessions.REDIS_AVAILABLE', False):
            response = client.post(
                '/api/sessions/test-session-123/command',
                headers=auth_headers_admin,
                json={'command': 'test command'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert data['sessions_available'] is False

    def test_send_command_missing_command(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when command is missing"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'command is required' in data['message']

    def test_send_command_whitespace_only_command(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when command is whitespace only"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': '   '}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'command is required' in data['message']

    def test_send_command_invalid_type(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when command type is invalid"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test', 'type': 'invalid_type'}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'Invalid command type' in data['error']
                assert 'quick_command' in data['message']
                assert 'user_command' in data['message']

    def test_send_command_invalid_quick_command_id(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when quick command ID is invalid - Issue #2179"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'invalid_quick_cmd', 'type': 'quick_command'}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'Invalid quick command' in data['error']
                assert 'continue' in data['message']
                assert 'explain' in data['message']
                assert 'skip' in data['message']
                assert 'retry' in data['message']

    # MAINTENANCE NOTE: When adding new quick commands, update these test cases
    # to match VALID_QUICK_COMMAND_IDS in sessions.py and QUICK_COMMANDS in SessionCommandInput.jsx
    @pytest.mark.parametrize("quick_command_id", ['continue', 'explain', 'skip', 'retry'])
    def test_send_command_valid_quick_command(self, client, auth_headers_admin, mock_redis_client, sample_session_data, quick_command_id):
        """Test POST /api/sessions/:id/command succeeds with valid quick commands - Issue #2179"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': quick_command_id, 'type': 'quick_command'}
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True

    def test_send_command_session_cancelled(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when session is cancelled"""
        sample_session_data['status'] = 'cancelled'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test command'}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'Cannot send command' in data['error']

    def test_send_command_session_not_found(self, client, auth_headers_admin, mock_redis_client):
        """Test POST /api/sessions/:id/command returns 404 when session not found"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = None

                response = client.post(
                    '/api/sessions/nonexistent-session/command',
                    headers=auth_headers_admin,
                    json={'command': 'test command'}
                )

                assert response.status_code == 404
                data = response.get_json()
                assert 'error' in data

    def test_send_command_session_completed(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when session is completed"""
        sample_session_data['status'] = 'completed'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test command'}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'Cannot send command' in data['error']

    def test_send_command_session_failed(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command returns 400 when session is failed"""
        sample_session_data['status'] = 'failed'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test command'}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'Cannot send command' in data['error']

    def test_send_command_success_active_session(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command succeeds for active session"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_pipe = MagicMock()
                mock_redis_client.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
                mock_redis_client.pipeline.return_value.__exit__ = MagicMock(return_value=False)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={
                        'command': 'continue',
                        'type': 'quick_command',
                        'timestamp': '2025-01-01T00:00:00Z'
                    }
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'accepted'
                assert data['session_id'] == 'test-session-123'
                assert 'command_id' in data
                assert 'timestamp' in data

                mock_pipe.rpush.assert_called_once()
                mock_pipe.expire.assert_called_once()
                mock_pipe.execute.assert_called_once()

    def test_send_command_success_paused_session(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command succeeds for paused session"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'explain current step'}
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'accepted'

    def test_send_command_default_type(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command uses default type 'user_command'"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_pipe = MagicMock()
                mock_redis_client.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
                mock_redis_client.pipeline.return_value.__exit__ = MagicMock(return_value=False)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'custom instruction'}
                )

                assert response.status_code == 200

                call_args = mock_pipe.rpush.call_args
                command_data = json.loads(call_args[0][1])
                assert command_data['type'] == 'user_command'

    def test_send_command_uses_pipeline_for_concurrency_safety(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command uses Redis pipeline for atomic RPUSH+EXPIRE"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_pipe = MagicMock()
                mock_redis_client.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
                mock_redis_client.pipeline.return_value.__exit__ = MagicMock(return_value=False)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'new command'}
                )

                assert response.status_code == 200

                mock_pipe.rpush.assert_called_once()
                call_args = mock_pipe.rpush.call_args
                commands_key = call_args[0][0]
                assert commands_key == 'dev_agent:session:test-session-123:commands'

                command_data = json.loads(call_args[0][1])
                assert command_data['command'] == 'new command'
                assert 'command_id' in command_data
                assert 'server_timestamp' in command_data

                mock_pipe.execute.assert_called_once()

    def test_send_command_sets_ttl_on_commands_key(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test POST /api/sessions/:id/command sets TTL on commands key via pipeline"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_pipe = MagicMock()
                mock_redis_client.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
                mock_redis_client.pipeline.return_value.__exit__ = MagicMock(return_value=False)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test'}
                )

                assert response.status_code == 200

                mock_pipe.expire.assert_called_once()
                call_args = mock_pipe.expire.call_args
                assert call_args[0][0] == 'dev_agent:session:test-session-123:commands'
                assert call_args[0][1] == 86400


class TestExtractIdeActivity:
    """Tests for _extract_ide_activity() function - Issue #2241"""

    def test_extract_empty_session(self):
        """Test extraction from session with no observations or actions"""
        session_data = {
            'observations': [],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert result['activeFile'] is None
        assert result['recentFiles'] == []
        assert result['ideUrl'] is None
        assert result['hasIdeSession'] is False

    def test_extract_write_action_sets_active_file(self):
        """Test that WRITE_CODE action sets activeFile"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': '/src/main.py'},
                    'timestamp': '2024-01-15T10:00:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert result['activeFile'] == '/src/main.py'
        assert len(result['recentFiles']) == 1
        assert result['recentFiles'][0]['action'] == 'modified'

    def test_extract_read_action_does_not_set_active_file(self):
        """Test that READ_FILE action does NOT set activeFile (regression test)"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'READ_FILE',
                    'result': {'file_path': '/src/config.py'},
                    'timestamp': '2024-01-15T10:00:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # activeFile should be None because READ_FILE is excluded
        assert result['activeFile'] is None
        assert len(result['recentFiles']) == 1
        assert result['recentFiles'][0]['action'] == 'read'

    def test_extract_active_file_excludes_reads_mixed(self):
        """Test activeFile picks most recent MODIFIED file, not read (regression test)"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': '/src/old.py'},
                    'timestamp': '2024-01-15T09:00:00Z'
                },
                {
                    'action_type': 'READ_FILE',
                    'result': {'file_path': '/src/newer_read.py'},
                    'timestamp': '2024-01-15T10:00:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # activeFile should be the WRITE_CODE file, not the newer READ_FILE
        assert result['activeFile'] == '/src/old.py'
        assert len(result['recentFiles']) == 2

    def test_extract_actions_take_precedence_over_observations(self):
        """Test that actions are processed first and take precedence"""
        session_data = {
            'observations': [
                {
                    'observation': 'reading /src/main.py',
                    'timestamp': '2024-01-15T10:00:00Z'
                }
            ],
            'actions': [
                {
                    'action_type': 'EDIT_FILE',
                    'result': {'file_path': '/src/main.py'},
                    'timestamp': '2024-01-15T09:00:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # File should be marked as 'modified' from action, not 'read' from observation
        assert len(result['recentFiles']) == 1
        assert result['recentFiles'][0]['action'] == 'modified'
        assert result['activeFile'] == '/src/main.py'

    def test_extract_observation_write_verbs(self):
        """Test observation parsing for write verbs (editing, modified, created, etc.)"""
        session_data = {
            'observations': [
                {'observation': 'editing /src/file1.py', 'timestamp': '2024-01-15T10:00:00Z'},
                {'observation': 'modified /src/file2.txt', 'timestamp': '2024-01-15T10:01:00Z'},
                {'observation': 'created /src/file3.cfg', 'timestamp': '2024-01-15T10:02:00Z'},
                {'observation': 'updated /src/file4.ini', 'timestamp': '2024-01-15T10:03:00Z'},
                {'observation': 'wrote /src/file5.log', 'timestamp': '2024-01-15T10:04:00Z'},
            ],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # All 5 files should be extracted and marked as 'modified'
        # Using non-code extensions to avoid fallback pattern matching extra files
        assert len(result['recentFiles']) == 5
        for f in result['recentFiles']:
            assert f['action'] == 'modified'

    def test_extract_observation_read_verbs(self):
        """Test observation parsing for read verbs (reading, opened)"""
        session_data = {
            'observations': [
                {'observation': 'reading /src/config.py', 'timestamp': '2024-01-15T10:00:00Z'},
                {'observation': 'opened /src/settings.cfg', 'timestamp': '2024-01-15T10:01:00Z'},
            ],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # All should be marked as 'read'
        # Using non-code extensions to avoid fallback pattern matching extra files
        assert len(result['recentFiles']) == 2
        for f in result['recentFiles']:
            assert f['action'] == 'read'
        # activeFile should be None since all are reads
        assert result['activeFile'] is None

    def test_extract_file_deduplication(self):
        """Test that same file appearing multiple times is deduplicated"""
        session_data = {
            'observations': [
                {'observation': 'editing /src/main.py', 'timestamp': '2024-01-15T10:00:00Z'},
                {'observation': 'modified /src/main.py', 'timestamp': '2024-01-15T10:01:00Z'},
            ],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # Should only have one entry for main.py
        assert len(result['recentFiles']) == 1
        assert result['recentFiles'][0]['path'] == '/src/main.py'

    def test_extract_ide_url_from_metadata(self):
        """Test IDE URL extraction from ide_session metadata"""
        session_data = {
            'observations': [],
            'actions': [],
            'ide_session': {
                'session_id': 'ide-123',
                'public_url': 'https://ide.example.com/session/123'
            },
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert result['ideUrl'] == 'https://ide.example.com/session/123'
        assert result['hasIdeSession'] is True

    def test_extract_ide_url_fallback_to_vscode_endpoint(self):
        """Test IDE URL fallback to vscode_endpoint"""
        session_data = {
            'observations': [],
            'actions': [],
            'ide_session': {
                'session_id': 'ide-123',
                'vscode_endpoint': 'https://vscode.example.com'
            },
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert result['ideUrl'] == 'https://vscode.example.com'

    def test_extract_ide_url_fallback_to_context(self):
        """Test IDE URL fallback to context.ide_url"""
        session_data = {
            'observations': [],
            'actions': [],
            'ide_session': {},
            'context': {'ide_url': 'https://context-ide.example.com'}
        }

        result = _extract_ide_activity(session_data)

        assert result['ideUrl'] == 'https://context-ide.example.com'

    def test_extract_limits_to_10_files(self):
        """Test that recentFiles is limited to 10 entries"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': f'/src/file{i}.py'},
                    'timestamp': f'2024-01-15T10:{i:02d}:00Z'
                }
                for i in range(15)
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 10

    def test_extract_sorts_by_timestamp_descending(self):
        """Test that recentFiles is sorted by timestamp descending"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': '/src/old.py'},
                    'timestamp': '2024-01-15T09:00:00Z'
                },
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': '/src/new.py'},
                    'timestamp': '2024-01-15T11:00:00Z'
                },
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': '/src/mid.py'},
                    'timestamp': '2024-01-15T10:00:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # Should be sorted: new, mid, old
        assert result['recentFiles'][0]['path'] == '/src/new.py'
        assert result['recentFiles'][1]['path'] == '/src/mid.py'
        assert result['recentFiles'][2]['path'] == '/src/old.py'

    def test_extract_handles_missing_timestamp(self):
        """Test graceful handling of missing timestamp"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': '/src/main.py'},
                    # No timestamp
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 1
        assert result['recentFiles'][0]['timestamp'] == ''

    def test_extract_handles_empty_file_path(self):
        """Test that empty file paths are ignored"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'file_path': ''},
                    'timestamp': '2024-01-15T10:00:00Z'
                },
                {
                    'action_type': 'WRITE_CODE',
                    'result': {},  # No file_path at all
                    'timestamp': '2024-01-15T10:01:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 0

    def test_extract_handles_path_key_fallback(self):
        """Test that 'path' key is used as fallback when 'file_path' is missing"""
        session_data = {
            'observations': [],
            'actions': [
                {
                    'action_type': 'WRITE_CODE',
                    'result': {'path': '/src/main.py'},  # Using 'path' instead of 'file_path'
                    'timestamp': '2024-01-15T10:00:00Z'
                }
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 1
        assert result['recentFiles'][0]['path'] == '/src/main.py'

    def test_extract_all_write_action_types(self):
        """Test all write action types are recognized"""
        session_data = {
            'observations': [],
            'actions': [
                {'action_type': 'WRITE_CODE', 'result': {'file_path': '/a.py'}, 'timestamp': '2024-01-15T10:00:00Z'},
                {'action_type': 'EDIT_FILE', 'result': {'file_path': '/b.py'}, 'timestamp': '2024-01-15T10:01:00Z'},
                {'action_type': 'CREATE_FILE', 'result': {'file_path': '/c.py'}, 'timestamp': '2024-01-15T10:02:00Z'},
            ],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 3
        for f in result['recentFiles']:
            assert f['action'] == 'modified'

    def test_extract_file_extension_pattern_fallback(self):
        """Test file extension pattern matching as fallback"""
        session_data = {
            'observations': [
                {'observation': 'Looking at src/utils/helper.ts for reference', 'timestamp': '2024-01-15T10:00:00Z'},
            ],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        # Should extract the .ts file from the observation
        assert len(result['recentFiles']) >= 1
        # Fallback patterns mark as 'read' since intent is unclear
        assert any(f['path'].endswith('.ts') for f in result['recentFiles'])

    def test_extract_quoted_file_paths(self):
        """Test extraction of file paths in quotes"""
        session_data = {
            'observations': [
                {'observation': 'editing "src/main.py"', 'timestamp': '2024-01-15T10:00:00Z'},
                {'observation': "modified 'src/utils.js'", 'timestamp': '2024-01-15T10:01:00Z'},
                {'observation': 'created `src/config.ts`', 'timestamp': '2024-01-15T10:02:00Z'},
            ],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 3

    def test_extract_case_insensitive_verbs(self):
        """Test that verb matching is case insensitive"""
        session_data = {
            'observations': [
                {'observation': 'EDITING /src/upper.py', 'timestamp': '2024-01-15T10:00:00Z'},
                {'observation': 'Editing /src/title.py', 'timestamp': '2024-01-15T10:01:00Z'},
                {'observation': 'READING /src/read_upper.py', 'timestamp': '2024-01-15T10:02:00Z'},
            ],
            'actions': [],
            'ide_session': {},
            'context': {}
        }

        result = _extract_ide_activity(session_data)

        assert len(result['recentFiles']) == 3
        # First two should be modified, last one read
        modified_files = [f for f in result['recentFiles'] if f['action'] == 'modified']
        read_files = [f for f in result['recentFiles'] if f['action'] == 'read']
        assert len(modified_files) == 2
        assert len(read_files) == 1


class TestSessionTTLEdgeCases:
    """Tests for session TTL (Time-To-Live) edge cases - Issue #4228"""

    def test_pause_session_uses_correct_ttl(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that pause_session uses SESSION_TTL_SECONDS (86400) when saving"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)

                assert response.status_code == 200
                mock_redis_client.setex.assert_called_once()
                call_args = mock_redis_client.setex.call_args
                assert call_args[0][1] == 86400

    def test_resume_session_uses_correct_ttl(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that resume_session uses SESSION_TTL_SECONDS (86400) when saving"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/resume', headers=auth_headers_admin)

                assert response.status_code == 200
                mock_redis_client.setex.assert_called_once()
                call_args = mock_redis_client.setex.call_args
                assert call_args[0][1] == 86400

    def test_cancel_session_uses_correct_ttl(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that cancel_session uses SESSION_TTL_SECONDS (86400) when saving"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/cancel', headers=auth_headers_admin)

                assert response.status_code == 200
                mock_redis_client.setex.assert_called_once()
                call_args = mock_redis_client.setex.call_args
                assert call_args[0][1] == 86400

    def test_pause_session_refreshes_ttl_on_update(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that pausing a session refreshes its TTL (extends expiration)"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)

                assert response.status_code == 200
                call_args = mock_redis_client.setex.call_args
                key = call_args[0][0]
                assert key == 'dev_agent:session:test-session-123'


class TestRedisConnectionFailures:
    """Tests for Redis connection failure scenarios - Issue #4228"""

    def test_list_sessions_redis_connection_timeout(self, client, auth_headers_admin, mock_redis_client):
        """Test list_sessions handles Redis connection timeout"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.side_effect = redis.exceptions.TimeoutError("Connection timed out")

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_get_session_detail_redis_connection_error(self, client, auth_headers_admin, mock_redis_client):
        """Test get_session_detail handles Redis connection error"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.side_effect = redis.exceptions.ConnectionError("Connection refused")

                response = client.get('/api/sessions/test-123', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_pause_session_redis_write_error(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test pause_session handles Redis write error"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_redis_client.setex.side_effect = redis.exceptions.ConnectionError("Write failed")

                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_resume_session_redis_write_error(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test resume_session handles Redis write error"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_redis_client.setex.side_effect = redis.exceptions.ConnectionError("Write failed")

                response = client.post('/api/sessions/test-session-123/resume', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_cancel_session_redis_write_error(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test cancel_session handles Redis write error"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_redis_client.setex.side_effect = redis.exceptions.ConnectionError("Write failed")

                response = client.post('/api/sessions/test-session-123/cancel', headers=auth_headers_admin)

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data

    def test_send_command_redis_pipeline_error(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test send_command handles Redis pipeline execution error"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_pipe = MagicMock()
                mock_redis_client.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
                mock_redis_client.pipeline.return_value.__exit__ = MagicMock(return_value=False)
                mock_pipe.execute.side_effect = redis.exceptions.ConnectionError("Pipeline failed")

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test'}
                )

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data


class TestConcurrentAccess:
    """Tests for concurrent access scenarios - Issue #4228"""

    def test_list_sessions_with_null_data_in_mget(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test list_sessions handles null values in MGET response (concurrent deletion)"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [
                    b'dev_agent:session:test-1',
                    b'dev_agent:session:test-2',
                    b'dev_agent:session:test-3'
                ]
                mock_redis_client.mget.return_value = [
                    json.dumps(sample_session_data),
                    None,
                    json.dumps({**sample_session_data, 'session_id': 'test-3'})
                ]

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert len(data['sessions']) == 2

    def test_send_command_uses_atomic_pipeline(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test send_command uses atomic pipeline for RPUSH+EXPIRE (race condition prevention)"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)
                mock_pipe = MagicMock()
                mock_redis_client.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
                mock_redis_client.pipeline.return_value.__exit__ = MagicMock(return_value=False)

                response = client.post(
                    '/api/sessions/test-session-123/command',
                    headers=auth_headers_admin,
                    json={'command': 'test command'}
                )

                assert response.status_code == 200
                mock_redis_client.pipeline.assert_called_once()
                mock_pipe.rpush.assert_called_once()
                mock_pipe.expire.assert_called_once()
                mock_pipe.execute.assert_called_once()

    def test_list_sessions_handles_mixed_valid_invalid_data(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test list_sessions gracefully handles mix of valid, invalid, and null data"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.scan_iter.return_value = [
                    b'dev_agent:session:valid-1',
                    b'dev_agent:session:invalid-json',
                    b'dev_agent:session:null-data',
                    b'dev_agent:session:valid-2'
                ]
                mock_redis_client.mget.return_value = [
                    json.dumps(sample_session_data),
                    'not valid json {{{',
                    None,
                    json.dumps({**sample_session_data, 'session_id': 'valid-2'})
                ]

                response = client.get('/api/sessions', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert len(data['sessions']) == 2


class TestSessionDataEdgeCases:
    """Tests for session data edge cases - Issue #4228"""

    def test_transform_session_with_missing_optional_fields(self):
        """Test transform handles session with minimal required fields"""
        minimal_session = {
            'session_id': 'minimal-123',
            'goal': 'Minimal goal',
            'status': 'active'
        }

        result = transform_session_for_frontend(minimal_session)

        assert result['id'] == 'minimal-123'
        assert result['goal'] == 'Minimal goal'
        assert result['status'] == 'running'
        assert result['progress'] == 0
        assert result['plan']['totalTasks'] == 0

    def test_transform_session_with_empty_context(self):
        """Test transform handles session with empty context"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 0,
            'max_iterations': 10,
            'decisions': [],
            'actions': [],
            'observations': [],
            'context': {}
        }

        result = transform_session_for_frontend(session_data)

        assert result['prUrl'] is None
        assert result['errorMessage'] is None

    def test_resume_escalated_session_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test resuming an escalated session succeeds"""
        sample_session_data['status'] = 'escalated'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/resume', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'running'

    def test_transform_session_with_failed_actions(self):
        """Test transform correctly calculates confidence with failed actions"""
        session_data = {
            'session_id': 'test-123',
            'goal': 'Test',
            'status': 'active',
            'iteration': 5,
            'max_iterations': 10,
            'decisions': [
                {'decision': 'Task 1', 'action_type': 'analyze'},
                {'decision': 'Task 2', 'action_type': 'fix'}
            ],
            'actions': [
                {'success': False, 'timestamp': '2024-01-15T10:00:00Z', 'result': {'message': 'Failed'}},
                {'success': False, 'timestamp': '2024-01-15T10:01:00Z', 'result': {'message': 'Failed again'}}
            ],
            'observations': []
        }

        result = transform_session_for_frontend(session_data)

        assert result['confidence'] == 0.0
        assert result['plan']['tasks'][0]['status'] == 'failed'
        assert result['plan']['tasks'][1]['status'] == 'failed'

    def test_cancel_session_without_reason(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test cancelling session without providing a reason"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/cancel', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['reason'] is None

    def test_cancel_paused_session_success(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test cancelling a paused session succeeds"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/cancel',
                    headers=auth_headers_admin,
                    json={'reason': 'No longer needed'}
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['status'] == 'failed'


class TestGetSessionAndUserHelper:
    """Tests for _get_session_and_user helper function - Issue #4228"""

    def test_get_session_and_user_extracts_user_info(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that _get_session_and_user correctly extracts user info from request context"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)

                assert response.status_code == 200
                data = response.get_json()
                assert 'paused_by' in data

    def test_pause_session_records_user_email(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that pause operation records the user who paused"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/pause', headers=auth_headers_admin)

                assert response.status_code == 200
                call_args = mock_redis_client.setex.call_args
                saved_data = json.loads(call_args[0][2])
                assert 'paused_by' in saved_data

    def test_resume_session_records_user_email(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that resume operation records the user who resumed"""
        sample_session_data['status'] = 'paused'
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post('/api/sessions/test-session-123/resume', headers=auth_headers_admin)

                assert response.status_code == 200
                call_args = mock_redis_client.setex.call_args
                saved_data = json.loads(call_args[0][2])
                assert 'resumed_by' in saved_data

    def test_cancel_session_records_user_and_reason(self, client, auth_headers_admin, mock_redis_client, sample_session_data):
        """Test that cancel operation records user and reason in context"""
        with patch('src.routes.sessions.get_redis_client', return_value=mock_redis_client):
            with patch('src.routes.sessions.REDIS_AVAILABLE', True):
                mock_redis_client.get.return_value = json.dumps(sample_session_data)

                response = client.post(
                    '/api/sessions/test-session-123/cancel',
                    headers=auth_headers_admin,
                    json={'reason': 'Test cancellation reason'}
                )

                assert response.status_code == 200
                call_args = mock_redis_client.setex.call_args
                saved_data = json.loads(call_args[0][2])
                assert 'cancelled_by' in saved_data
                assert saved_data['context']['cancellation_reason'] == 'Test cancellation reason'
