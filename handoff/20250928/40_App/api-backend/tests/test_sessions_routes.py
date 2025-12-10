"""
Tests for sessions routes (Session Control endpoints)
PR 3: Controls + HITL Integration
PR B: Unit tests for #1982
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock

from src.routes.sessions import transform_session_for_frontend


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
