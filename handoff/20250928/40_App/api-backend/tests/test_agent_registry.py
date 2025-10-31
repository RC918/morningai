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
from copy import deepcopy
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.main import app
from src.routes.agent_registry import agents_store, tasks_store


@pytest.fixture(autouse=True)
def reset_stores():
    """Clear in-memory stores before each test to prevent cross-test contamination"""
    agents_store.clear()
    tasks_store.clear()
    yield
    agents_store.clear()
    tasks_store.clear()


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
    assert 'pagination' in data
    assert data['pagination']['page'] == 1
    assert data['pagination']['total_items'] >= 1
    assert len(data['agents']) > 0


def test_list_agents_with_filters(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents - Filter by status"""
    client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    
    response = client.get(
        '/api/v1/agents?status=idle',
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(agent['status'] == 'idle' for agent in data['agents'])


def test_list_agents_pagination(client, admin_headers, sample_agent_data):
    """Test GET /api/v1/agents - Pagination"""
    for i in range(3):
        agent_data = deepcopy(sample_agent_data)
        agent_data['metadata']['name'] = f"Agent {i}"
        agent_data['capabilities'] = [f"capability_{i}"]
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
    assert data['pagination']['page'] == 1


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
    assert data['agent_id'] == agent_id
    assert data['metadata']['name'] == sample_agent_data['metadata']['name']


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
    
    update_data = {"status": "active", "metadata": {"description": "Updated description"}}
    response = client.patch(
        f'/api/v1/agents/{agent_id}',
        data=json.dumps(update_data),
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'active'
    assert data['metadata']['description'] == 'Updated description'


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
        "status": "active",
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
    assert data['status'] == 'active'



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


def test_list_agents_invalid_page(client, admin_headers):
    """Test GET /api/v1/agents - Invalid page parameter (page < 1)"""
    response = client.get('/api/v1/agents?page=0', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_parameter'
    assert 'page must be >= 1' in data['error']['message']


def test_list_agents_invalid_page_size_too_small(client, admin_headers):
    """Test GET /api/v1/agents - Invalid page_size (< 1)"""
    response = client.get('/api/v1/agents?page_size=0', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_parameter'
    assert 'page_size must be between 1 and 100' in data['error']['message']


def test_list_agents_invalid_page_size_too_large(client, admin_headers):
    """Test GET /api/v1/agents - Invalid page_size (> 100)"""
    response = client.get('/api/v1/agents?page_size=101', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_parameter'
    assert 'page_size must be between 1 and 100' in data['error']['message']


def test_list_agents_invalid_agent_type(client, admin_headers):
    """Test GET /api/v1/agents - Invalid agent_type filter"""
    response = client.get('/api/v1/agents?agent_type=invalid_type', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_parameter'
    assert 'Invalid agent_type' in data['error']['message']


def test_list_agents_invalid_status(client, admin_headers):
    """Test GET /api/v1/agents - Invalid status filter"""
    response = client.get('/api/v1/agents?status=invalid_status', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_parameter'
    assert 'Invalid status' in data['error']['message']


def test_list_agents_invalid_permission_level(client, admin_headers):
    """Test GET /api/v1/agents - Invalid permission_level filter"""
    response = client.get('/api/v1/agents?permission_level=invalid_level', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_parameter'
    assert 'Invalid permission_level' in data['error']['message']


def test_list_agents_exception_handling(client, admin_headers):
    """Test GET /api/v1/agents - Exception handling with Sentry"""
    with patch('src.routes.agent_registry.AgentDB') as mock_agent_db:
        mock_agent_db.query.count.side_effect = Exception("Database error")
        
        response = client.get('/api/v1/agents', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'internal_error'


def test_register_agent_exception_handling(client, admin_headers, sample_agent_data):
    """Test POST /api/v1/agents - Exception handling"""
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        response = client.post(
            '/api/v1/agents',
            data=json.dumps(sample_agent_data),
            headers=admin_headers
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_get_agent_exception_handling(client, admin_headers):
    """Test GET /api/v1/agents/{agent_id} - Exception handling"""
    with patch('src.routes.agent_registry.AgentDB') as mock_agent_db:
        mock_agent_db.query.get.side_effect = Exception("Database error")
        
        response = client.get(f'/api/v1/agents/{uuid.uuid4()}', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_update_agent_not_found(client, admin_headers):
    """Test PATCH /api/v1/agents/{agent_id} - Agent not found"""
    response = client.patch(
        f'/api/v1/agents/{uuid.uuid4()}',
        data=json.dumps({"status": "active"}),
        headers=admin_headers
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_update_agent_exception_handling(client, admin_headers, sample_agent_data):
    """Test PATCH /api/v1/agents/{agent_id} - Exception handling"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        response = client.patch(
            f'/api/v1/agents/{agent_id}',
            data=json.dumps({"status": "active"}),
            headers=admin_headers
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_unregister_agent_not_found(client, admin_headers):
    """Test DELETE /api/v1/agents/{agent_id} - Agent not found"""
    response = client.delete(f'/api/v1/agents/{uuid.uuid4()}', headers=admin_headers)
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_unregister_agent_exception_handling(client, admin_headers, sample_agent_data):
    """Test DELETE /api/v1/agents/{agent_id} - Exception handling"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        response = client.delete(f'/api/v1/agents/{agent_id}', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_get_agent_health_not_found(client, admin_headers):
    """Test GET /api/v1/agents/{agent_id}/health - Agent not found"""
    response = client.get(f'/api/v1/agents/{uuid.uuid4()}/health', headers=admin_headers)
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_get_agent_health_exception_handling(client, admin_headers):
    """Test GET /api/v1/agents/{agent_id}/health - Exception handling"""
    with patch('src.routes.agent_registry.AgentDB') as mock_agent_db:
        mock_agent_db.query.get.side_effect = Exception("Database error")
        
        response = client.get(f'/api/v1/agents/{uuid.uuid4()}/health', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_report_agent_health_not_found(client, admin_headers):
    """Test POST /api/v1/agents/{agent_id}/health - Agent not found"""
    health_data = {"status": "active", "metrics": {"cpu_usage": 45.2}}
    response = client.post(
        f'/api/v1/agents/{uuid.uuid4()}/health',
        data=json.dumps(health_data),
        headers=admin_headers
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_report_agent_health_exception_handling(client, admin_headers, sample_agent_data):
    """Test POST /api/v1/agents/{agent_id}/health - Exception handling"""
    create_response = client.post(
        '/api/v1/agents',
        data=json.dumps(sample_agent_data),
        headers=admin_headers
    )
    agent_id = json.loads(create_response.data)['agent_id']
    
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        health_data = {"status": "active", "metrics": {"cpu_usage": 45.2}}
        response = client.post(
            f'/api/v1/agents/{agent_id}/health',
            data=json.dumps(health_data),
            headers=admin_headers
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_list_tasks_invalid_page(client, admin_headers):
    """Test GET /api/v1/tasks - Invalid page parameter"""
    response = client.get('/api/v1/tasks?page=0', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'page must be >= 1' in data['error']['message']


def test_list_tasks_invalid_page_size(client, admin_headers):
    """Test GET /api/v1/tasks - Invalid page_size parameter"""
    response = client.get('/api/v1/tasks?page_size=101', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'page_size must be between 1 and 100' in data['error']['message']


def test_list_tasks_invalid_status(client, admin_headers):
    """Test GET /api/v1/tasks - Invalid status filter"""
    response = client.get('/api/v1/tasks?status=invalid_status', headers=admin_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid status' in data['error']['message']


def test_list_tasks_exception_handling(client, admin_headers):
    """Test GET /api/v1/tasks - Exception handling"""
    with patch('src.routes.agent_registry.TaskDB') as mock_task_db:
        mock_task_db.query.count.side_effect = Exception("Database error")
        
        response = client.get('/api/v1/tasks', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_create_task_exception_handling(client, admin_headers, sample_task_data):
    """Test POST /api/v1/tasks - Exception handling"""
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        response = client.post(
            '/api/v1/tasks',
            data=json.dumps(sample_task_data),
            headers=admin_headers
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_get_task_not_found(client, admin_headers):
    """Test GET /api/v1/tasks/{task_id} - Task not found"""
    response = client.get(f'/api/v1/tasks/{uuid.uuid4()}', headers=admin_headers)
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_get_task_exception_handling(client, admin_headers):
    """Test GET /api/v1/tasks/{task_id} - Exception handling"""
    with patch('src.routes.agent_registry.TaskDB') as mock_task_db:
        mock_task_db.query.get.side_effect = Exception("Database error")
        
        response = client.get(f'/api/v1/tasks/{uuid.uuid4()}', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_update_task_not_found(client, admin_headers):
    """Test PATCH /api/v1/tasks/{task_id} - Task not found"""
    response = client.patch(
        f'/api/v1/tasks/{uuid.uuid4()}',
        data=json.dumps({"status": "running"}),
        headers=admin_headers
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_update_task_exception_handling(client, admin_headers, sample_task_data):
    """Test PATCH /api/v1/tasks/{task_id} - Exception handling"""
    task_response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    task_id = json.loads(task_response.data)['task_id']
    
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        response = client.patch(
            f'/api/v1/tasks/{task_id}',
            data=json.dumps({"status": "running"}),
            headers=admin_headers
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


def test_cancel_task_not_found(client, admin_headers):
    """Test POST /api/v1/tasks/{task_id}/cancel - Task not found"""
    response = client.post(f'/api/v1/tasks/{uuid.uuid4()}/cancel', headers=admin_headers)
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_cancel_task_exception_handling(client, admin_headers, sample_task_data):
    """Test POST /api/v1/tasks/{task_id}/cancel - Exception handling"""
    task_response = client.post(
        '/api/v1/tasks',
        data=json.dumps(sample_task_data),
        headers=admin_headers
    )
    task_id = json.loads(task_response.data)['task_id']
    
    with patch('src.routes.agent_registry.db.session.commit') as mock_commit:
        mock_commit.side_effect = Exception("Database error")
        
        response = client.post(f'/api/v1/tasks/{task_id}/cancel', headers=admin_headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
