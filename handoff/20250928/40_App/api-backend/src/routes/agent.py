import os
import json
import uuid
import subprocess
import threading
import re
from datetime import datetime
from flask import Blueprint, jsonify, request
from redis import Redis

bp = Blueprint("agent", __name__, url_prefix="/api/agent")

redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

def execute_orchestrator_task(task_id, topic, repo):
    """Background thread to execute orchestrator and update task status"""
    try:
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "running",
                "topic": topic,
                "updated_at": datetime.utcnow().isoformat()
            })
        )
        
        orchestrator_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..", "orchestrator"
        )
        
        result = subprocess.run(
            ["python", "graph.py", "--goal", topic, "--repo", repo],
            cwd=orchestrator_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout + result.stderr
        trace_id = None
        pr_url = None
        
        trace_match = re.search(r'trace-id: ([a-f0-9-]+)', output)
        if trace_match:
            trace_id = trace_match.group(1)
        
        pr_match = re.search(r'\[PR\] (https://[^\s]+)', output)
        if pr_match:
            pr_url = pr_match.group(1)
        
        if result.returncode == 0:
            redis_client.setex(
                f"agent:task:{task_id}",
                3600,
                json.dumps({
                    "status": "done",
                    "topic": topic,
                    "trace_id": trace_id,
                    "pr_url": pr_url,
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
        else:
            redis_client.setex(
                f"agent:task:{task_id}",
                3600,
                json.dumps({
                    "status": "error",
                    "topic": topic,
                    "error": f"Orchestrator failed with code {result.returncode}",
                    "output": output[-500:],
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
    except Exception as e:
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "error",
                "topic": topic,
                "error": str(e),
                "updated_at": datetime.utcnow().isoformat()
            })
        )

@bp.post("/faq")
def create_faq_task():
    """Create FAQ generation task"""
    try:
        payload = request.get_json(silent=True) or {}
        topic = payload.get("topic", "Update FAQ with common questions")
        repo = os.getenv("GITHUB_REPO", "RC918/morningai")
        
        task_id = str(uuid.uuid4())
        
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "queued",
                "topic": topic,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
        )
        
        thread = threading.Thread(
            target=execute_orchestrator_task,
            args=(task_id, topic, repo)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({"task_id": task_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.get("/tasks/<task_id>")
def get_task_status(task_id):
    """Get task status by ID"""
    try:
        task_data = redis_client.get(f"agent:task:{task_id}")
        
        if not task_data:
            return jsonify({"error": "Task not found"}), 404
        
        task = json.loads(task_data)
        return jsonify(task), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
