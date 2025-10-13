import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from redis import Redis, ConnectionError as RedisConnectionError
from rq import Queue
from rq.serializers import JSONSerializer
from src.middleware.auth_middleware import analyst_required, jwt_required, roles_required
from pydantic import BaseModel, Field, ValidationError, field_validator
from redis_queue.worker import run_orchestrator_task

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

class FAQRequest(BaseModel):
    """Request model for FAQ generation"""
    question: str = Field(..., description="Question to generate FAQ for")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Strip whitespace and validate question is not empty"""
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('question cannot be empty or whitespace only')
        return v

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN and SENTRY_DSN.strip():
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "production"),
            traces_sample_rate=1.0,
        )
        logger.info("Sentry initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}. Continuing without Sentry integration.")
        SENTRY_DSN = None

bp = Blueprint("agent", __name__, url_prefix="/api/agent")

redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
redis_client_rq = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "orchestrator")
q = Queue(RQ_QUEUE_NAME, connection=redis_client_rq, serializer=JSONSerializer())

@bp.route("/faq", methods=["GET"])
def faq_method_not_allowed():
    """Return 405 for GET requests to prevent misuse"""
    return jsonify({
        "error": "Method Not Allowed",
        "message": "This endpoint only accepts POST requests. Please use POST with a JSON body containing 'question' field."
    }), 405, {"Allow": "POST"}

@bp.route("/faq", methods=["POST"])
def create_faq_task():
    """Create FAQ generation task"""
    try:
        payload = request.get_json(silent=True) or {}
        validated_request = FAQRequest(**payload)
        question = validated_request.question
    except ValidationError as e:
        error_details = json.loads(e.json())
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": error_details
            }
        }), 400
    
    try:
        repo = os.getenv("GITHUB_REPO", "RC918/morningai")
        task_id = str(uuid.uuid4())
        
        job = q.enqueue(
            run_orchestrator_task,
            task_id,
            question,
            repo,
            job_id=task_id,
            ttl=600,
            result_ttl=86400,
            failure_ttl=3600
        )
        
        redis_client.hset(
            f"agent:task:{task_id}",
            mapping={
                "status": "queued",
                "question": question,
                "job_id": job.id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        redis_client.expire(f"agent:task:{task_id}", 3600)
        
        try:
            from orchestrator.persistence.db_writer import upsert_task_queued
            upsert_task_queued(
                task_id=task_id,
                trace_id=task_id,
                question=question,
                job_id=job.id
            )
            
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task enqueued to DB',
                    level='info',
                    data={
                        'task_id': task_id,
                        'status': 'queued'
                    }
                )
        except Exception as e:
            logger.error(f"DB write failed for task {task_id}: {e}")
        
        logger.info(f"enqueued task_id={task_id} job_id={job.id}")
        
        return jsonify({
            "task_id": task_id,
            "status": "queued"
        }), 202
    except RedisConnectionError as e:
        logger.error(f"Redis connection failed for task creation", extra={
            "op": "faq",
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None,
            "error_type": "redis_connection"
        })
        
        if SENTRY_DSN and SENTRY_DSN.strip():
            sentry_sdk.add_breadcrumb(
                category='redis',
                message='Redis connection failed during task creation',
                level='error',
                data={'task_id': task_id if 'task_id' in locals() else None, 'question': question}
            )
            sentry_sdk.capture_exception(e)
        
        return jsonify({
            "error": {
                "code": "redis_unavailable",
                "message": "Service temporarily unavailable. Please try again later."
            }
        }), 503
    except Exception as e:
        logger.exception("Failed to enqueue FAQ task", extra={
            "op": "faq",
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None
        })
        
        if SENTRY_DSN and SENTRY_DSN.strip():
            sentry_sdk.capture_exception(e)
        
        return jsonify({
            "error": {
                "code": "queue_unavailable",
                "message": "Service temporarily unavailable. Please try again later."
            }
        }), 503

@bp.get("/tasks/<task_id>")
def get_task_status(task_id):
    """Get task status by ID - reads from DB first, Redis as fallback"""
    try:
        from orchestrator.persistence.db_client import get_client
        client = get_client()
        
        response = client.table("agent_tasks").select("*").eq("task_id", task_id).execute()
        
        if response.data and len(response.data) > 0:
            task = response.data[0]
            return jsonify({
                "task_id": task["task_id"],
                "status": task["status"],
                "trace_id": task["trace_id"],
                "question": task.get("question"),
                "pr_url": task.get("pr_url"),
                "error_msg": task.get("error_msg"),
                "created_at": task.get("created_at"),
                "started_at": task.get("started_at"),
                "finished_at": task.get("finished_at"),
                "updated_at": task.get("updated_at"),
                "source": "database"
            }), 200
    except Exception as e:
        logger.warning(f"DB read failed for task {task_id}, falling back to Redis: {e}")
    
    try:
        key = f"agent:task:{task_id}"
        key_type = redis_client.type(key)
        
        if key_type == "hash":
            task_data = redis_client.hgetall(key)
        elif key_type == "string":
            task_json = redis_client.get(key)
            task_data = json.loads(task_json) if task_json else None
        else:
            task_data = None
        
        if not task_data:
            return jsonify({"error": "Task not found"}), 404
        
        task_data["source"] = "redis"
        return jsonify(task_data), 200
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", extra={"task_id": task_id})
        return jsonify({"error": str(e)}), 500

@bp.get("/debug/queue")
@jwt_required
@roles_required("analyst", "admin")
def debug_queue_status():
    """Debug endpoint showing queue and task status"""
    try:
        queue_length = redis_client_rq.llen(f"rq:queue:{RQ_QUEUE_NAME}")
        
        recent_jobs = redis_client_rq.lrange(f"rq:queue:{RQ_QUEUE_NAME}", 0, 4)
        
        task_keys = list(redis_client.scan_iter("agent:task:*", count=100))
        sample_task = None
        if task_keys:
            latest_key = sorted(task_keys)[-1] if task_keys else None
            if latest_key:
                key_type = redis_client.type(latest_key)
                
                if key_type == "hash":
                    task_data = redis_client.hgetall(latest_key)
                elif key_type == "string":
                    task_json = redis_client.get(latest_key)
                    task_data = json.loads(task_json) if task_json else None
                else:
                    task_data = None
                
                if task_data:
                    sample_task = {
                        "task_id": latest_key.split(":")[-1],
                        "status": task_data.get("status"),
                        "job_id": task_data.get("job_id"),
                        "created_at": task_data.get("created_at"),
                        "question_length": len(task_data.get("question", ""))
                    }
        
        return jsonify({
            "queue_length": queue_length,
            "recent_job_ids": [job.decode() if isinstance(job, bytes) else job for job in recent_jobs[:5]],
            "sample_task": sample_task,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Failed to get debug status: {e}")
        return jsonify({"error": str(e)}), 500
