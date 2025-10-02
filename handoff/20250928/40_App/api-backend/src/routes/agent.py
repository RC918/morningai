import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from redis import Redis
from rq import Queue

bp = Blueprint("agent", __name__, url_prefix="/api/agent")

redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
q = Queue("orchestrator", connection=redis_client)

@bp.post("/faq")
def create_faq_task():
    """Create FAQ generation task"""
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    
    if not question:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "question parameter is required and cannot be empty"
            }
        }), 400
    
    try:
        repo = os.getenv("GITHUB_REPO", "RC918/morningai")
        task_id = str(uuid.uuid4())
        
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "queued",
                "question": question,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
        )
        
        q.enqueue(
            'redis_queue.worker.run_orchestrator_task',
            task_id,
            question,
            repo,
            job_id=task_id
        )
        
        return jsonify({
            "task_id": task_id,
            "status": "queued"
        }), 202
    except Exception as e:
        import logging
        logging.exception("Failed to enqueue FAQ task", extra={
            "op": "faq",
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None
        })
        return jsonify({
            "error": {
                "code": "queue_unavailable",
                "message": "Service temporarily unavailable. Please try again later."
            }
        }), 503

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
