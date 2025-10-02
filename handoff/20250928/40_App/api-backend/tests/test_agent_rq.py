import pytest
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from main import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_faq_task_enqueues_job(client):
    """Test that POST /api/agent/faq enqueues an RQ job"""
    with patch('routes.agent.queue.enqueue') as mock_enqueue:
        mock_job = MagicMock()
        mock_job.id = 'test-job-id'
        mock_enqueue.return_value = mock_job
        
        response = client.post('/api/agent/faq', 
                              json={'topic': 'test topic'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'task_id' in data
        assert mock_enqueue.called
        
        call_kwargs = mock_enqueue.call_args[1]
        assert call_kwargs['retry'] == 3
        assert call_kwargs['job_timeout'] == 600

def test_get_task_status_returns_queued(client):
    """Test that GET /api/agent/tasks/:id returns queued status"""
    with patch('routes.agent.redis_client') as mock_redis:
        mock_redis.get.return_value = json.dumps({
            'status': 'queued',
            'topic': 'test',
            'created_at': '2025-01-01T00:00:00'
        })
        
        response = client.get('/api/agent/tasks/test-id')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'queued'

def test_get_task_status_not_found(client):
    """Test that GET /api/agent/tasks/:id returns 404 for missing task"""
    with patch('routes.agent.redis_client') as mock_redis:
        mock_redis.get.return_value = None
        
        response = client.get('/api/agent/tasks/nonexistent')
        assert response.status_code == 404

def test_execute_orchestrator_task_retry_on_failure():
    """Test that orchestrator task raises exception for RQ retry"""
    from routes.agent import execute_orchestrator_task
    
    with patch('routes.agent.subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            execute_orchestrator_task('task-id', 'test topic', 'RC918/morningai')
