"""
Tests for failures API routes (Phase 5 PR-1 and PR-2)
Covers failure recording, retrieval, and replay functionality
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create Flask app instance for testing"""
    with patch.dict(os.environ, {'SENTRY_DSN': '', 'SECRET_KEY': 'test-secret'}):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']

        from src.main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create authentication headers with JWT token"""
    from src.middleware.auth_middleware import create_user_token
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


class TestFailuresHealthEndpoint:
    """Test failures health check endpoint"""

    def test_health_check_success(self, client):
        """Test health check returns status"""
        response = client.get('/api/failures/health')

        assert response.status_code == 200
        data = response.get_json()
        assert 'failure_recorder_available' in data
        assert 'components' in data


class TestFailuresListEndpoint:
    """Test failures list endpoint"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', False)
    def test_list_failures_unavailable(self, client, auth_headers):
        """Test list failures when recorder unavailable"""
        response = client.get('/api/failures', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_list_failures_success(self, mock_get_recorder, client, auth_headers):
        """Test successful list failures"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.to_dict.return_value = {
            'id': 'test-id',
            'trace_id': 'trace-123',
            'goal': 'Test goal',
            'error_type': 'ci_failure',
            'metadata': {'repo': 'test/repo'}
        }
        mock_recorder.list_failures.return_value = [mock_failure]
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'failures' in data
        assert 'count' in data
        assert 'limit' in data
        assert 'offset' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_list_failures_with_filters(self, mock_get_recorder, client, auth_headers):
        """Test list failures with query filters"""
        mock_recorder = MagicMock()
        mock_recorder.list_failures.return_value = []
        mock_get_recorder.return_value = mock_recorder

        response = client.get(
            '/api/failures?limit=10&offset=5&error_type=ci_failure',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 10
        assert data['offset'] == 5
        assert data['filters']['error_type'] == 'ci_failure'


class TestFailuresGetEndpoint:
    """Test get single failure endpoint"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', False)
    def test_get_failure_unavailable(self, client, auth_headers):
        """Test get failure when recorder unavailable"""
        response = client.get('/api/failures/test-id', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_get_failure_not_found(self, mock_get_recorder, client, auth_headers):
        """Test get failure when not found"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure.return_value = None
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/non-existent', headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_get_failure_success(self, mock_get_recorder, client, auth_headers):
        """Test successful get failure"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.to_dict.return_value = {
            'id': 'test-id',
            'trace_id': 'trace-123',
            'goal': 'Test goal',
            'error_type': 'ci_failure'
        }
        mock_recorder.get_failure.return_value = mock_failure
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/test-id', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == 'test-id'
        assert data['trace_id'] == 'trace-123'


class TestFailuresSummaryEndpoint:
    """Test failures summary endpoint"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', False)
    def test_summary_unavailable(self, client, auth_headers):
        """Test summary when recorder unavailable"""
        response = client.get('/api/failures/summary', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_summary_success(self, mock_get_recorder, client, auth_headers):
        """Test successful summary retrieval"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure_summary.return_value = {
            'total_count': 10,
            'by_error_type': {'ci_failure': 5, 'workflow_error': 5},
            'by_task_type': {'code_review': 10}
        }
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/summary', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'summary' in data
        assert 'timestamp' in data


class TestFailuresReplayEndpoint:
    """Test failures replay endpoint (Phase 5 PR-2)"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', False)
    def test_replay_unavailable(self, client, auth_headers):
        """Test replay when recorder unavailable"""
        response = client.post(
            '/api/failures/test-id/replay',
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_replay_failure_not_found(self, mock_get_recorder, client, auth_headers):
        """Test replay when failure not found"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure.return_value = None
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/non-existent/replay',
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_replay_success(self, mock_get_recorder, client, auth_headers):
        """Test successful replay"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.goal = 'Test goal for replay'
        mock_recorder.get_failure.return_value = mock_failure

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.failure_id = 'test-id'
        mock_result.new_trace_id = 'replay-test-12345678'
        mock_result.job_id = 'job-123'
        mock_result.error = None
        mock_result.to_dict.return_value = {
            'success': True,
            'failure_id': 'test-id',
            'new_trace_id': 'replay-test-12345678',
            'job_id': 'job-123',
            'error': None
        }
        mock_recorder.replay_failure.return_value = mock_result
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/test-id/replay',
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['failure_id'] == 'test-id'
        assert data['new_trace_id'] == 'replay-test-12345678'
        assert data['job_id'] == 'job-123'
        assert 'original_goal' in data
        assert 'timestamp' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_replay_with_repo_override(self, mock_get_recorder, client, auth_headers):
        """Test replay with repository override"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.goal = 'Test goal'
        mock_recorder.get_failure.return_value = mock_failure

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.failure_id = 'test-id'
        mock_result.new_trace_id = 'replay-test-abcd1234'
        mock_result.job_id = 'job-456'
        mock_result.error = None
        mock_result.to_dict.return_value = {
            'success': True,
            'failure_id': 'test-id',
            'new_trace_id': 'replay-test-abcd1234',
            'job_id': 'job-456',
            'error': None
        }
        mock_recorder.replay_failure.return_value = mock_result
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/test-id/replay',
            headers=auth_headers,
            json={'repo': 'custom/repo'}
        )

        assert response.status_code == 200
        mock_recorder.replay_failure.assert_called_once_with('test-id', repo='custom/repo')

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_replay_failure_error(self, mock_get_recorder, client, auth_headers):
        """Test replay when replay fails"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.goal = 'Test goal'
        mock_recorder.get_failure.return_value = mock_failure

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.failure_id = 'test-id'
        mock_result.new_trace_id = None
        mock_result.job_id = None
        mock_result.error = 'RQ not available'
        mock_result.to_dict.return_value = {
            'success': False,
            'failure_id': 'test-id',
            'new_trace_id': None,
            'job_id': None,
            'error': 'RQ not available'
        }
        mock_recorder.replay_failure.return_value = mock_result
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/test-id/replay',
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
        assert data['error'] == 'RQ not available'

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_replay_exception_handling(self, mock_get_recorder, client, auth_headers):
        """Test replay exception handling"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure.side_effect = Exception('Database error')
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/test-id/replay',
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestFailuresErrorHandling:
    """Test error handling in failures routes"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_list_failures_exception(self, mock_get_recorder, client, auth_headers):
        """Test list failures exception handling"""
        mock_recorder = MagicMock()
        mock_recorder.list_failures.side_effect = Exception('Redis error')
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_get_failure_exception(self, mock_get_recorder, client, auth_headers):
        """Test get failure exception handling"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure.side_effect = Exception('Redis error')
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/test-id', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_summary_exception(self, mock_get_recorder, client, auth_headers):
        """Test summary exception handling"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure_summary.side_effect = Exception('Redis error')
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/summary', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
