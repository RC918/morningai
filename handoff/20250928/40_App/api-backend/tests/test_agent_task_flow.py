import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from src.main import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_redis_task_flow():
    """Mock Redis for complete task flow testing"""
    with patch('src.routes.agent.redis_client') as mock_client, \
         patch('src.routes.agent.redis_client_rq') as mock_client_rq, \
         patch('src.routes.agent.q') as mock_queue:
        
        tasks = {}
        
        def mock_get(key):
            return tasks.get(key)
        
        def mock_setex(key, ttl, value):
            tasks[key] = value
            return True
        
        def mock_enqueue(*args, **kwargs):
            job = MagicMock()
            job.id = kwargs.get('job_id', str(uuid.uuid4()))
            return job
        
        mock_client.get.side_effect = mock_get
        mock_client.setex.side_effect = mock_setex
        mock_client.type.return_value = "string"
        mock_queue.enqueue.side_effect = mock_enqueue
        
        mock_client_rq.llen.return_value = 1
        mock_client_rq.lrange.return_value = [b'test-job-1']
        
        yield mock_client, tasks

def test_task_flow_enqueue_success(client, mock_redis_task_flow):
    """Test task enqueue creates task with queued status"""
    mock_client, tasks = mock_redis_task_flow
    
    response = client.post(
        '/api/agent/faq',
        json={'question': 'What is the architecture?'},
        headers={'Content-Type': 'application/json'}
    )
    
    assert response.status_code == 202
    data = json.loads(response.data)
    assert 'task_id' in data
    assert data['status'] == 'queued'

def test_task_flow_status_polling(client, mock_redis_task_flow):
    """Test task status polling returns correct status"""
    mock_client, tasks = mock_redis_task_flow
    
    task_id = str(uuid.uuid4())
    task_key = f"agent:task:{task_id}"
    tasks[task_key] = json.dumps({
        "status": "running",
        "task_id": task_id,
        "question": "test question"
    })
    
    response = client.get(f'/api/agent/tasks/{task_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'
    assert data['task_id'] == task_id

def test_task_flow_completion(client, mock_redis_task_flow):
    """Test completed task returns result"""
    mock_client, tasks = mock_redis_task_flow
    
    task_id = str(uuid.uuid4())
    task_key = f"agent:task:{task_id}"
    tasks[task_key] = json.dumps({
        "status": "done",
        "task_id": task_id,
        "result": {
            "pr_url": "https://github.com/test/repo/pull/1",
            "summary": "Created PR successfully"
        }
    })
    
    response = client.get(f'/api/agent/tasks/{task_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'done'
    assert 'result' in data
    assert data['result']['pr_url'] == "https://github.com/test/repo/pull/1"

def test_task_flow_error_handling(client, mock_redis_task_flow):
    """Test error task returns error details"""
    mock_client, tasks = mock_redis_task_flow
    
    task_id = str(uuid.uuid4())
    task_key = f"agent:task:{task_id}"
    tasks[task_key] = json.dumps({
        "status": "error",
        "task_id": task_id,
        "error": {
            "code": "ORCHESTRATOR_FAILED",
            "message": "Failed to create PR"
        }
    })
    
    response = client.get(f'/api/agent/tasks/{task_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'error' in data
    assert data['error']['code'] == "ORCHESTRATOR_FAILED"

def test_task_flow_nonexistent_task(client, mock_redis_task_flow):
    """Test polling nonexistent task returns 404"""
    mock_client, tasks = mock_redis_task_flow
    
    response = client.get(f'/api/agent/tasks/{uuid.uuid4()}')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_task_flow_invalid_question(client):
    """Test task creation with invalid question"""
    response = client.post(
        '/api/agent/faq',
        json={'question': ''},
        headers={'Content-Type': 'application/json'}
    )
    
    assert response.status_code == 400
