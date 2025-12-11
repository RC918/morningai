"""
Additional tests for failures API routes to improve coverage
Covers eval task generation, metrics, and health check edge cases
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


class TestHealthCheckEdgeCases:
    """Test health check edge cases"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_health_check_redis_available(self, mock_get_recorder, client):
        """Test health check when Redis is available"""
        mock_recorder = MagicMock()
        mock_recorder.enabled = True
        mock_recorder.get_failure_count.return_value = 5
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['failure_recorder_available'] is True
        assert data['components']['redis'] == 'available'
        assert data['components']['failure_count'] == 5

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_health_check_redis_degraded(self, mock_get_recorder, client):
        """Test health check when Redis is degraded"""
        mock_recorder = MagicMock()
        mock_recorder.enabled = False
        mock_recorder.get_failure_count.return_value = 0
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['components']['redis'] == 'degraded'

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_health_check_redis_error(self, mock_get_recorder, client):
        """Test health check when Redis throws error"""
        mock_recorder = MagicMock()
        mock_recorder.enabled = True
        mock_recorder.get_failure_count.side_effect = Exception('Redis connection failed')
        mock_get_recorder.return_value = mock_recorder

        response = client.get('/api/failures/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['components']['redis'] == 'unavailable'
        assert 'error' in data['components']

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', False)
    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', False)
    def test_health_check_all_unavailable(self, client):
        """Test health check when all services unavailable"""
        response = client.get('/api/failures/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['failure_recorder_available'] is False
        assert data['agent_eval_available'] is False

    def test_health_check_exception(self, client):
        """Test health check when _get_recorder raises exception - returns 200 with error in components"""
        with patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True):
            with patch('src.routes.failures._get_recorder') as mock_get_recorder:
                mock_get_recorder.side_effect = Exception('Unexpected error')

                response = client.get('/api/failures/health')

                # The inner try/except catches the exception and returns 200 with redis=unavailable
                assert response.status_code == 200
                data = response.get_json()
                assert data['components']['redis'] == 'unavailable'
                assert 'error' in data['components']
                assert 'Unexpected error' in data['components']['error']


class TestGenerateEvalTask:
    """Test generate eval task endpoint"""

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', False)
    def test_generate_eval_task_recorder_unavailable(self, client, auth_headers):
        """Test generate eval task when recorder unavailable"""
        response = client.post(
            '/api/failures/test-id/generate-eval-task',
            headers=auth_headers
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', False)
    def test_generate_eval_task_eval_unavailable(self, client, auth_headers):
        """Test generate eval task when agent eval unavailable"""
        response = client.post(
            '/api/failures/test-id/generate-eval-task',
            headers=auth_headers
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'agent eval' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_generate_eval_task_failure_not_found(self, mock_get_recorder, client, auth_headers):
        """Test generate eval task when failure not found"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure.return_value = None
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/non-existent/generate-eval-task',
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    @patch('src.routes.failures._get_agent_eval')
    def test_generate_eval_task_success(self, mock_get_agent_eval, mock_get_recorder, client, auth_headers):
        """Test successful eval task generation"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.to_dict.return_value = {
            'id': 'test-id',
            'goal': 'Test goal',
            'error_type': 'ci_failure'
        }
        mock_recorder.get_failure.return_value = mock_failure
        mock_get_recorder.return_value = mock_recorder

        mock_agent_eval = MagicMock()
        mock_task = MagicMock()
        mock_task.to_dict.return_value = {
            'task_id': 'eval-task-123',
            'description': 'Test eval task',
            'difficulty': 'medium'
        }
        mock_agent_eval.generate_eval_task_from_failure.return_value = mock_task
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.post(
            '/api/failures/test-id/generate-eval-task',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'task' in data
        assert data['task']['task_id'] == 'eval-task-123'
        assert 'timestamp' in data

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    @patch('src.routes.failures._get_agent_eval')
    def test_generate_eval_task_generation_failed(self, mock_get_agent_eval, mock_get_recorder, client, auth_headers):
        """Test eval task generation failure"""
        mock_recorder = MagicMock()
        mock_failure = MagicMock()
        mock_failure.to_dict.return_value = {'id': 'test-id'}
        mock_recorder.get_failure.return_value = mock_failure
        mock_get_recorder.return_value = mock_recorder

        mock_agent_eval = MagicMock()
        mock_agent_eval.generate_eval_task_from_failure.return_value = None
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.post(
            '/api/failures/test-id/generate-eval-task',
            headers=auth_headers
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'failed to generate' in data['error'].lower()

    @patch('src.routes.failures.FAILURE_RECORDER_AVAILABLE', True)
    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_recorder')
    def test_generate_eval_task_exception(self, mock_get_recorder, client, auth_headers):
        """Test eval task generation exception handling"""
        mock_recorder = MagicMock()
        mock_recorder.get_failure.side_effect = Exception('Database error')
        mock_get_recorder.return_value = mock_recorder

        response = client.post(
            '/api/failures/test-id/generate-eval-task',
            headers=auth_headers
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestListEvalTasks:
    """Test list eval tasks endpoint"""

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', False)
    def test_list_eval_tasks_unavailable(self, client, auth_headers):
        """Test list eval tasks when agent eval unavailable"""
        response = client.get('/api/failures/eval/tasks', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_list_eval_tasks_json_format(self, mock_get_agent_eval, client, auth_headers):
        """Test list eval tasks in JSON format"""
        mock_agent_eval = MagicMock()
        mock_task = MagicMock()
        mock_task.to_dict.return_value = {
            'task_id': 'eval-task-1',
            'description': 'Test task'
        }
        mock_agent_eval.list_eval_tasks.return_value = [mock_task]
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/tasks', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'tasks' in data
        assert 'count' in data
        assert data['count'] == 1

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_list_eval_tasks_jsonl_format(self, mock_get_agent_eval, client, auth_headers):
        """Test list eval tasks in JSONL format"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.export_eval_tasks_jsonl.return_value = '{"task_id": "1"}\n{"task_id": "2"}'
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/tasks?format=jsonl', headers=auth_headers)

        assert response.status_code == 200
        assert response.content_type == 'application/x-ndjson'

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_list_eval_tasks_with_pagination(self, mock_get_agent_eval, client, auth_headers):
        """Test list eval tasks with pagination"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.list_eval_tasks.return_value = []
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/tasks?limit=10&offset=5', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 10
        assert data['offset'] == 5

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_list_eval_tasks_exception(self, mock_get_agent_eval, client, auth_headers):
        """Test list eval tasks exception handling"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.list_eval_tasks.side_effect = Exception('Database error')
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/tasks', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestGetEvalMetrics:
    """Test get eval metrics endpoint"""

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', False)
    def test_get_eval_metrics_unavailable(self, client, auth_headers):
        """Test get eval metrics when agent eval unavailable"""
        response = client.get('/api/failures/eval/metrics', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_get_eval_metrics_success(self, mock_get_agent_eval, client, auth_headers):
        """Test successful get eval metrics"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.get_metrics_summary.return_value = {
            'success_rate': 0.85,
            'fixer_metrics': {'avg_iterations': 2.5},
            'security_risk_distribution': {'low': 10, 'high': 2}
        }
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/metrics', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data
        assert data['metrics']['success_rate'] == 0.85
        assert 'timestamp' in data

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_get_eval_metrics_exception(self, mock_get_agent_eval, client, auth_headers):
        """Test get eval metrics exception handling"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.get_metrics_summary.side_effect = Exception('Database error')
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/metrics', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestGetWorkflowEvalMetrics:
    """Test get workflow eval metrics endpoint"""

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', False)
    def test_get_workflow_metrics_unavailable(self, client, auth_headers):
        """Test get workflow metrics when agent eval unavailable"""
        response = client.get('/api/failures/eval/metrics/trace-123', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_get_workflow_metrics_not_found(self, mock_get_agent_eval, client, auth_headers):
        """Test get workflow metrics when not found"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.get_metrics.return_value = None
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/metrics/non-existent', headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_get_workflow_metrics_success(self, mock_get_agent_eval, client, auth_headers):
        """Test successful get workflow metrics"""
        mock_agent_eval = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.to_dict.return_value = {
            'trace_id': 'trace-123',
            'success': True,
            'duration_ms': 5000
        }
        mock_agent_eval.get_metrics.return_value = mock_metrics
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/metrics/trace-123', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data
        assert data['metrics']['trace_id'] == 'trace-123'
        assert 'timestamp' in data

    @patch('src.routes.failures.AGENT_EVAL_AVAILABLE', True)
    @patch('src.routes.failures._get_agent_eval')
    def test_get_workflow_metrics_exception(self, mock_get_agent_eval, client, auth_headers):
        """Test get workflow metrics exception handling"""
        mock_agent_eval = MagicMock()
        mock_agent_eval.get_metrics.side_effect = Exception('Database error')
        mock_get_agent_eval.return_value = mock_agent_eval

        response = client.get('/api/failures/eval/metrics/trace-123', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
