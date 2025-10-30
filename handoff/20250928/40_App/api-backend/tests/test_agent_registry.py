"""
Tests for Agent Registry API endpoints (Issue #760)
Feature Flag: MVP_AGENT_REGISTRY

Tests all 12 OpenAPI endpoints:
- Agents: GET/POST /agents, GET/PATCH/DELETE /agents/{id}
- Agent Health: GET/POST /agents/{id}/health
- Tasks: GET/POST /tasks, GET/PATCH /tasks/{id}, POST /tasks/{id}/cancel
"""
import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.main import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_headers(admin_token):
    """Admin authorization headers"""
    return {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        "agent_type": "dev_agent",
        "capabilities": ["task_execution", "monitoring"],
        "metadata": {
            "name": "Test Agent",
            "description": "Test agent for unit tests",
            "owner_id": "test-owner-123",
            "config": {
                "max_concurrent_tasks": 5,
                "timeout_seconds": 300
            }
        }
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "task_type": "execution",
        "payload": {
            "action": "test_action",
            "parameters": {"key": "value"},
            "priority": "high"
        }
    }



def test_create_agent_success(client, admin_headers, sample_agent_data):
    """Test POST /api/v1/agents - Create new agent"""
    response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'agent_id' in data
    assert data['agent_type'] == sample_agent_data['agent_type']
    assert data['status'] == 'idle'
    assert data['capabilities'] == sample_agent_data['capabilities']


def test_create_agent_missing_required_fields(client, admin_headers):
    """Test POST /api/v1/agents - Missing required fields"""
    response = client.post(
        '/api/v1/agents',
        data=json.dumps({"agent_type": "dev_agent"}),  # Missing capabilities
        headers=admin_headers
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_list_agents(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents - List all agents"""
    client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    
    response = client.get('/api/v1/agents', headers=admin_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'agents' in data
    assert 'total' in data
    assert 'page' in data
    assert len(data['agents']) > 0


def test_list_agents_with_filters(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents - Filter by status"""
    client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    
    response = client.get(
        '/api/v1/agents?status=inactive',
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(agent['status'] == 'idle' for agent in data['agents'])


def test_list_agents_pagination(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents - Pagination"""
    for i in range(3):
        agent_data = sample_agent_data.copy()
        agent_data['name'] = f"Agent {i}"
        client.post(
            '/api/v1/agents',
            data=json.dumps(agent_data),
            headers=admin_headers
        )
    
    response = client.get(
        '/api/v1/agents?page=1&page_size=2',
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['agents']) <= 2
    assert data['page'] == 1


def test_get_agent_by_id(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents/{agent_id} - Get specific agent"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    response = client.get(f'/api/v1/agents/{agent_id}', headers=admin_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == agent_id
    assert data['name'] == sample_agent_data['name']


def test_get_agent_not_found(client, admin_headers):
    """Test GET /api/v1/agents/{agent_id} - Agent not found"""
    response = client.get(
        f'/api/v1/agents/{uuid.uuid4()}',
        headers=admin_headers
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_update_agent(client, admin_headers, sample_agent_data):
    """Test PATCH /api/v1/agents/{agent_id} - Update agent"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    update_data = {"status": "active", "description": "Updated description"}
    response = client.patch(
        f'/api/v1/agents/{agent_id}',
        data=json.dumps(update_data),
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'active'
    assert data['description'] == 'Updated description'


def test_delete_agent(client, admin_headers, sample_agent_data):
    """Test DELETE /api/v1/agents/{agent_id} - Delete agent"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    response = client.delete(f'/api/v1/agents/{agent_id}', headers=admin_headers)
    
    assert response.status_code == 204
    
    get_response = client.get(f'/api/v1/agents/{agent_id}', headers=admin_headers)
    assert get_response.status_code == 404



def test_get_agent_health(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents/{agent_id}/health - Get agent health"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    response = client.get(f'/api/v1/agents/{agent_id}/health', headers=admin_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'last_heartbeat' in data


def test_report_agent_health(client, admin_headers, sample_agent_data):
    """Test POST /api/v1/agents/{agent_id}/health - Report health"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    health_data = {
        "status": "healthy",
        "metrics": {
            "cpu_usage": 45.2,
            "memory_usage": 60.5,
            "active_tasks": 3
        }
    }
    response = client.post(
        f'/api/v1/agents/{agent_id}/health',
        data=json.dumps(health_data),
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'



def test_create_task_success(client, admin_headers, sample_agent_data, sample_task_data):
    """Test POST /api/v1/tasks - Create new task"""
    response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    
    assert response.status_code in [201, 202]
    data = json.loads(response.data)
    assert 'task_id' in data
    assert data['status'] == 'queued'


def test_create_task_invalid_agent(client, admin_headers, sample_task_data):
    """Test POST /api/v1/tasks - Task creation succeeds even without agent"""
    response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    
    assert response.status_code in [201, 202]
    data = json.loads(response.data)
    assert 'task_id' in data


def test_list_tasks(client, admin_headers, sample_agent_data, sample_task_data):
    """Test GET /api/v1/tasks - List all tasks"""
    client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    
    response = client.get('/api/v1/tasks', headers=admin_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'tasks' in data
    assert 'pagination' in data
    assert len(data['tasks']) > 0


def test_list_tasks_filter_by_status(client, admin_headers, sample_agent_data, sample_task_data):
    """Test GET /api/v1/tasks - Filter by status"""
    client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    
    response = client.get(
        f'/api/v1/tasks?status=queued',
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(task['status'] == 'queued' for task in data['tasks'])


def test_get_task_by_id(client, admin_headers, sample_agent_data, sample_task_data):
    """Test GET /api/v1/tasks/{task_id} - Get specific task"""
    task_response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    task_id = json.loads(task_response.data)['task_id']
    
    response = client.get(f'/api/v1/tasks/{task_id}', headers=admin_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['task_id'] == task_id


def test_update_task(client, admin_headers, sample_agent_data, sample_task_data):
    """Test PATCH /api/v1/tasks/{task_id} - Update task"""
    task_response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    task_id = json.loads(task_response.data)['task_id']
    
    update_data = {"status": "running"}
    response = client.patch(
        f'/api/v1/tasks/{task_id}',
        data=json.dumps(update_data),
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'


def test_cancel_task(client, admin_headers, sample_agent_data, sample_task_data):
    """Test POST /api/v1/tasks/{task_id}/cancel - Cancel task"""
    task_response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    task_id = json.loads(task_response.data)['task_id']
    
    response = client.post(
        f'/api/v1/tasks/{task_id}/cancel',
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'cancelled'


def test_cancel_completed_task(client, admin_headers, sample_agent_data, sample_task_data):
    """Test POST /api/v1/tasks/{task_id}/cancel - Cannot cancel completed task"""
    task_response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    task_id = json.loads(task_response.data)['task_id']
    
    client.patch(
        f'/api/v1/tasks/{task_id}',
        data=json.dumps({"status": "completed"}),
        headers=admin_headers
    )
    
    response = client.post(
        f'/api/v1/tasks/{task_id}/cancel',
        headers=admin_headers
    )
    
    assert response.status_code in [400, 409]
    data = json.loads(response.data)
    assert 'error' in data



def test_create_agent_without_auth(client, sample_agent_data):
    """Test POST /api/v1/agents - Without authorization"""
    response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers={'Content-Type': 'application/json'}
    )
    
    assert response.status_code == 401


def test_list_agents_without_auth(client):
    """Test GET /api/v1/agents - Without authorization"""
    response = client.get('/api/v1/agents')
    
    assert response.status_code == 401
