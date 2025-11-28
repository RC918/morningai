"""
Tests for ProjectEngineerAgent human entry point endpoint (Phase 3 PR-3)

This module tests the POST /api/agent/project-engineer/task endpoint
which allows humans to submit natural language task descriptions
to ProjectEngineerAgent.
"""
import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from src.main import app
from src.middleware import create_user_token


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_redis_project_engineer():
    """Mock Redis for ProjectEngineerAgent endpoint testing"""
    with patch('src.routes.agent.get_agent_redis_client') as mock_get_client, \
         patch('src.routes.agent.get_agent_queue') as mock_get_queue:

        tasks = {}
        mock_client = MagicMock()

        def mock_hset(key, mapping):
            tasks[key] = mapping
            return True

        def mock_hgetall(key):
            return tasks.get(key, {})

        def mock_expire(key, ttl):
            return True

        def mock_enqueue(*args, **kwargs):
            job = MagicMock()
            job.id = kwargs.get('job_id', str(uuid.uuid4()))
            return job

        mock_client.hset.side_effect = mock_hset
        mock_client.hgetall.side_effect = mock_hgetall
        mock_client.expire.side_effect = mock_expire
        mock_client.type.return_value = "hash"

        mock_get_client.return_value = mock_client

        mock_queue = MagicMock()
        mock_queue.enqueue.side_effect = mock_enqueue
        mock_get_queue.return_value = mock_queue

        yield mock_client, mock_queue, tasks


@pytest.fixture
def mock_tenant_resolution():
    """Mock tenant resolution for testing"""
    with patch('src.routes.agent.settings') as mock_settings:
        mock_settings.enable_project_engineer_codegen = False
        yield mock_settings


class TestProjectEngineerEndpoint:
    """Test suite for ProjectEngineerAgent endpoint"""

    def test_create_task_success(self, client, mock_redis_project_engineer, mock_tenant_resolution):
        """Test successful task creation returns 202 with task_id"""
        mock_client, mock_queue, tasks = mock_redis_project_engineer
        token = create_user_token()

        with patch('src.routes.agent.fetch_user_tenant_id', return_value='test-tenant-id'):
            response = client.post(
                '/api/agent/project-engineer/task',
                json={'description': 'Fix the login bug in the authentication module'},
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )

        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'task_id' in data
        assert data['status'] == 'queued'
        assert data['mode'] == 'analysis_only'

    def test_create_task_with_repo(self, client, mock_redis_project_engineer, mock_tenant_resolution):
        """Test task creation with custom repo"""
        mock_client, mock_queue, tasks = mock_redis_project_engineer
        token = create_user_token()

        with patch('src.routes.agent.fetch_user_tenant_id', return_value='test-tenant-id'):
            response = client.post(
                '/api/agent/project-engineer/task',
                json={
                    'description': 'Add unit tests for the API',
                    'repo': 'myorg/myrepo'
                },
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )

        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'task_id' in data
        assert data['status'] == 'queued'

    def test_create_task_execution_mode(self, client, mock_redis_project_engineer):
        """Test task creation in execution mode when codegen is enabled"""
        mock_client, mock_queue, tasks = mock_redis_project_engineer
        token = create_user_token()

        with patch('src.routes.agent.settings') as mock_settings, \
             patch('src.routes.agent.fetch_user_tenant_id', return_value='test-tenant-id'):
            mock_settings.enable_project_engineer_codegen = True

            response = client.post(
                '/api/agent/project-engineer/task',
                json={'description': 'Implement the new feature'},
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )

        assert response.status_code == 202
        data = json.loads(response.data)
        assert data['mode'] == 'execution'

    def test_create_task_empty_description(self, client):
        """Test task creation with empty description returns 400"""
        token = create_user_token()

        response = client.post(
            '/api/agent/project-engineer/task',
            json={'description': ''},
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'invalid_input'

    def test_create_task_whitespace_description(self, client):
        """Test task creation with whitespace-only description returns 400"""
        token = create_user_token()

        response = client.post(
            '/api/agent/project-engineer/task',
            json={'description': '   '},
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )

        assert response.status_code == 400

    def test_create_task_missing_description(self, client):
        """Test task creation without description returns 400"""
        token = create_user_token()

        response = client.post(
            '/api/agent/project-engineer/task',
            json={},
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )

        assert response.status_code == 400

    def test_create_task_invalid_repo_format(self, client):
        """Test task creation with invalid repo format returns 400"""
        token = create_user_token()

        response = client.post(
            '/api/agent/project-engineer/task',
            json={
                'description': 'Fix the bug',
                'repo': 'invalid-repo-format'
            },
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_task_requires_auth(self, client):
        """Test task creation without auth returns 401"""
        response = client.post(
            '/api/agent/project-engineer/task',
            json={'description': 'Fix the bug'},
            headers={'Content-Type': 'application/json'}
        )

        assert response.status_code == 401

    def test_get_method_not_allowed(self, client):
        """Test GET request returns 405"""
        token = create_user_token()

        response = client.get(
            '/api/agent/project-engineer/task',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 405
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Method Not Allowed'


class TestProjectEngineerTaskRequest:
    """Test suite for ProjectEngineerTaskRequest validation"""

    def test_valid_request(self):
        """Test valid request passes validation"""
        from src.routes.agent import ProjectEngineerTaskRequest

        request = ProjectEngineerTaskRequest(
            description='Fix the login bug',
            repo='RC918/morningai'
        )
        assert request.description == 'Fix the login bug'
        assert request.repo == 'RC918/morningai'

    def test_default_repo(self):
        """Test default repo is used when not provided"""
        from src.routes.agent import ProjectEngineerTaskRequest

        request = ProjectEngineerTaskRequest(description='Fix the bug')
        assert request.repo == 'RC918/morningai'

    def test_description_stripped(self):
        """Test description whitespace is stripped"""
        from src.routes.agent import ProjectEngineerTaskRequest

        request = ProjectEngineerTaskRequest(description='  Fix the bug  ')
        assert request.description == 'Fix the bug'

    def test_empty_description_raises(self):
        """Test empty description raises validation error"""
        from src.routes.agent import ProjectEngineerTaskRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProjectEngineerTaskRequest(description='')

    def test_invalid_repo_raises(self):
        """Test invalid repo format raises validation error"""
        from src.routes.agent import ProjectEngineerTaskRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProjectEngineerTaskRequest(
                description='Fix the bug',
                repo='invalid'
            )
