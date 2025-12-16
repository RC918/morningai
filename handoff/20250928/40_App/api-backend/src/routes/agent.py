import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from redis import Redis, ConnectionError as RedisConnectionError
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from rq import Queue
from rq.serializers import JSONSerializer
from src.middleware.auth_middleware import jwt_required, roles_required
from src.utils.redis_config import get_secure_redis_url
from pydantic import BaseModel, Field, ValidationError, field_validator
from redis_queue.worker import run_orchestrator_task, run_project_engineer_task
from common.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

SENTRY_DSN = settings.sentry_dsn
if SENTRY_DSN and SENTRY_DSN.strip():
    import sentry_sdk
else:
    sentry_sdk = None

# Default tenant ID for testing environments (DRY: used in multiple fallback paths)
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


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


class ProjectEngineerTaskRequest(BaseModel):
    """Request model for ProjectEngineerAgent task (Phase 3 PR-3)"""
    description: str = Field(..., description="Natural language task description")
    repo: str = Field(default="RC918/morningai", description="GitHub repository (owner/repo format)")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Strip whitespace and validate description is not empty"""
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('description cannot be empty or whitespace only')
        return v

    @field_validator('repo')
    @classmethod
    def validate_repo(cls, v: str) -> str:
        """Validate repo format (owner/repo)"""
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError('repo cannot be empty')
        if '/' not in v:
            raise ValueError('repo must be in owner/repo format')
        return v

bp = Blueprint("agent", __name__, url_prefix="/api/agent")

retry = Retry(ExponentialBackoff(base=1, cap=10), retries=3)

def _is_testing_mode():
    """Check if running in testing mode (dynamic check)"""
    try:
        from flask import current_app
        if current_app:
            v = current_app.config.get("TESTING")
            if v is not None:
                return bool(v)
    except Exception:
        pass
    return settings.testing


def resolve_tenant_or_error(user_id: str, task_id: str, operation: str = "task"):
    """
    Resolve tenant_id for a user or return an error response (Phase 3 PR-4: DRY refactor)

    This shared helper extracts the common tenant resolution logic used by
    /faq and /project-engineer/task endpoints.

    Args:
        user_id: User ID from authenticated request
        task_id: Task ID for logging context
        operation: Operation name for logging (e.g., "faq", "project_engineer")

    Returns:
        tuple: (tenant_id, None) on success, or (None, (response, status_code)) on error

    Usage:
        tenant_id, error_response = resolve_tenant_or_error(user_id, task_id, "faq")
        if error_response:
            return error_response
        # Continue with tenant_id
    """
    try:
        from orchestrator.persistence.db_writer import fetch_user_tenant_id
        tenant_id = fetch_user_tenant_id(user_id)

        if not tenant_id:
            logger.error(f"User {user_id} not assigned to any tenant for {operation} task {task_id}")
            return None, (jsonify({
                "error": {
                    "code": "tenant_not_found",
                    "message": "User is not assigned to any organization. Please contact support."
                }
            }), 403)

        logger.info(f"{operation.capitalize()} task {task_id} assigned to tenant={tenant_id} for user={user_id}")
        return tenant_id, None

    except ImportError as e:
        # Expected in testing environment where orchestrator module is not available
        logger.warning(f"orchestrator module not available (testing environment?): {e}")
        if _is_testing_mode():
            return DEFAULT_TENANT_ID, None

        logger.error(f"CRITICAL: orchestrator module failed to import in a non-testing environment: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return None, (jsonify({
            "error": {
                "code": "server_configuration_error",
                "message": "A server configuration error occurred. Please contact support."
            }
        }), 500)

    except ValueError as e:
        logger.error(f"User {user_id} not in user_profiles: {e}")
        return None, (jsonify({
            "error": {
                "code": "tenant_not_found",
                "message": "User is not assigned to any organization. Please contact support."
            }
        }), 403)

    except Exception as e:
        logger.error(f"Failed to fetch tenant for user {user_id}: {e}")
        
        # In testing mode, fall back to default tenant ONLY for database-related errors
        # (DatabaseReadError, DatabaseConnectionError). Do NOT fall back for
        # TenantResolutionError which indicates a user is not assigned to a tenant.
        if _is_testing_mode():
            # Check if this is a database availability error (not a tenant resolution error)
            error_type = type(e).__name__
            is_db_error = error_type in ('DatabaseReadError', 'DatabaseConnectionError', 'DatabaseException')
            # Also check error message for common database unavailability patterns
            error_msg = str(e).lower()
            is_credentials_error = any(pattern in error_msg for pattern in [
                'supabase credentials missing',
                'failed to get database client',
                'connection refused',
                'connection error'
            ])
            
            if is_db_error or is_credentials_error:
                logger.warning(f"Testing mode: falling back to default tenant due to database error: {e}")
                return DEFAULT_TENANT_ID, None
            else:
                # For non-database errors (e.g., TenantResolutionError), don't fall back
                logger.warning(f"Testing mode: NOT falling back for non-database error: {error_type}")
        
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return None, (jsonify({
            "error": {
                "code": "tenant_resolution_failed",
                "message": "Unable to resolve organization membership. Please try again or contact support."
            }
        }), 500)


AGENT_REDIS_URL = get_secure_redis_url(allow_local=_is_testing_mode())

_UNSET = object()

_redis_client = None
_redis_client_rq = None
_queue = None

# Module-level aliases for backward compatibility with tests that patch these attributes
redis_client = _UNSET
redis_client_rq = None
q = None

def get_agent_redis_client():
    """Get or create Redis client for agent routes (lazy initialization)
    
    Returns None if redis_client is explicitly set to None (e.g., by tests).
    Otherwise performs lazy initialization on first call.
    
    The sentinel pattern allows tests to:
    - Patch redis_client to a mock → returns the mock
    - Patch redis_client to None → returns None (simulates Redis unavailable)
    - Leave redis_client unpatched → performs lazy initialization
    """
    global _redis_client, redis_client
    
    if redis_client is not _UNSET:
        return redis_client
    
    if _redis_client is None:
        redis_url = AGENT_REDIS_URL
        redis_kwargs = {
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 30,
            "retry": retry,
            "retry_on_timeout": True
        }
        _redis_client = Redis.from_url(redis_url, **redis_kwargs)
        redis_client = _redis_client
    return _redis_client

def get_agent_redis_client_rq():
    """Get or create Redis client for RQ (lazy initialization)"""
    global _redis_client_rq, redis_client_rq
    if redis_client_rq is not None:
        return redis_client_rq
    if _redis_client_rq is None:
        redis_url = AGENT_REDIS_URL
        redis_kwargs_rq = {
            "socket_connect_timeout": 5,
            "socket_timeout": 30,
            "retry": retry,
            "retry_on_timeout": True
        }
        _redis_client_rq = Redis.from_url(redis_url, **redis_kwargs_rq)
        redis_client_rq = _redis_client_rq
    return _redis_client_rq

def get_agent_queue():
    """Get or create RQ Queue (lazy initialization)"""
    global _queue, q
    if q is not None:
        return q
    if _queue is None:
        queue_name = settings.rq_queue_name or "orchestrator"
        _queue = Queue(queue_name, connection=get_agent_redis_client_rq(), serializer=JSONSerializer())
        q = _queue
    return _queue

@bp.route("/faq", methods=["GET"])
def faq_method_not_allowed():
    """Return 405 for GET requests to prevent misuse"""
    return jsonify({
        "error": "Method Not Allowed",
        "message": "This endpoint only accepts POST requests. "
                   "Please use POST with a JSON body containing 'question' field."
    }), 405, {"Allow": "POST"}

@bp.route("/faq", methods=["POST"])
@jwt_required
def create_faq_task():
    """Create FAQ generation task (Phase 3: tenant-aware)"""
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
        repo = settings.github_repo or "RC918/morningai"
        task_id = str(uuid.uuid4())
        
        user_id = getattr(request, 'user_id', None)

        if not user_id:
            logger.error(f"No user_id found in authenticated request for task {task_id}")
            return jsonify({
                "error": {
                    "code": "authentication_error",
                    "message": "User ID not found in authenticated request. Please re-authenticate."
                }
            }), 401

        # Use shared tenant resolution helper (Phase 3 PR-4: DRY refactor)
        tenant_id, error_response = resolve_tenant_or_error(user_id, task_id, "faq")
        if error_response:
            return error_response

        if sentry_sdk:
            sentry_sdk.set_tag("trace_id", task_id)
            sentry_sdk.set_tag("task_id", task_id)
            sentry_sdk.set_tag("operation", "faq_create")
            sentry_sdk.set_tag("tenant_id", tenant_id)

        job = get_agent_queue().enqueue(
            run_orchestrator_task,
            task_id,
            question,
            repo,
            "faq",
            job_id=task_id,
            ttl=600,
            result_ttl=86400,
            failure_ttl=3600
        )
        
        get_agent_redis_client().hset(
            f"agent:task:{task_id}",
            mapping={
                "status": "queued",
                "question": question,
                "job_id": job.id,
                "task_type": "faq",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        get_agent_redis_client().expire(f"agent:task:{task_id}", 3600)
        
        try:
            from orchestrator.persistence.db_writer import upsert_task_queued
            upsert_task_queued(
                task_id=task_id,
                trace_id=task_id,
                question=question,
                job_id=job.id,
                tenant_id=tenant_id
            )
            
            if sentry_sdk:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task enqueued to DB',
                    level='info',
                    data={
                        'task_id': task_id,
                        'trace_id': task_id,
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
        logger.error("Redis connection failed for task creation", extra={
            "op": "faq",
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None,
            "error_type": "redis_connection"
        })
        
        if sentry_sdk:
            if 'task_id' in locals():
                sentry_sdk.set_tag("trace_id", task_id)
                sentry_sdk.set_tag("task_id", task_id)
            sentry_sdk.add_breadcrumb(
                category='redis',
                message='Redis connection failed during task creation',
                level='error',
                data={
                    'task_id': task_id if 'task_id' in locals() else None,
                    'trace_id': task_id if 'task_id' in locals() else None,
                    'question': question
                }
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
        
        if sentry_sdk:
            if 'task_id' in locals():
                sentry_sdk.set_tag("trace_id", task_id)
                sentry_sdk.set_tag("task_id", task_id)
            sentry_sdk.capture_exception(e)
        
        return jsonify({
            "error": {
                "code": "queue_unavailable",
                "message": "Service temporarily unavailable. Please try again later."
            }
        }), 503


@bp.route("/project-engineer/task", methods=["GET"])
def project_engineer_task_method_not_allowed():
    """Return 405 for GET requests to prevent misuse"""
    return jsonify({
        "error": "Method Not Allowed",
        "message": "This endpoint only accepts POST requests. "
                   "Please use POST with a JSON body containing 'description' field."
    }), 405, {"Allow": "POST"}


@bp.route("/project-engineer/task", methods=["POST"])
@jwt_required
def create_project_engineer_task():
    """
    Create ProjectEngineerAgent task (Phase 3 PR-3: Human Entry Point)

    This endpoint allows humans to submit natural language task descriptions
    to ProjectEngineerAgent for analysis and optional code generation.

    Request Body:
        {
            "description": "Natural language task description",
            "repo": "owner/repo" (optional, defaults to RC918/morningai)
        }

    Response (202 Accepted):
        {
            "task_id": "uuid",
            "status": "queued",
            "mode": "analysis_only" | "execution"
        }

    Feature Flags:
        - ENABLE_PROJECT_ENGINEER_CODEGEN: Controls code generation mode
          - false: Analysis-only mode (safe, no code changes)
          - true: Execution mode (can create PRs)
    """
    try:
        payload = request.get_json(silent=True) or {}
        validated_request = ProjectEngineerTaskRequest(**payload)
        description = validated_request.description
        repo = validated_request.repo
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
        task_id = str(uuid.uuid4())

        user_id = getattr(request, 'user_id', None)

        if not user_id:
            logger.error(f"No user_id found in authenticated request for task {task_id}")
            return jsonify({
                "error": {
                    "code": "authentication_error",
                    "message": "User ID not found in authenticated request. Please re-authenticate."
                }
            }), 401

        # Use shared tenant resolution helper (Phase 3 PR-4: DRY refactor)
        tenant_id, error_response = resolve_tenant_or_error(user_id, task_id, "project_engineer")
        if error_response:
            return error_response

        if sentry_sdk:
            sentry_sdk.set_tag("trace_id", task_id)
            sentry_sdk.set_tag("task_id", task_id)
            sentry_sdk.set_tag("operation", "project_engineer_create")
            sentry_sdk.set_tag("tenant_id", tenant_id)

        # Determine mode based on feature flag
        enable_codegen = settings.enable_project_engineer_codegen
        mode = "execution" if enable_codegen else "analysis_only"

        # Enqueue the task (pass tenant_id for multi-tenant isolation)
        job = get_agent_queue().enqueue(
            run_project_engineer_task,
            task_id,
            description,
            repo,
            tenant_id,
            job_id=task_id,
            ttl=600,
            result_ttl=86400,
            failure_ttl=3600
        )

        # Store initial status in Redis
        get_agent_redis_client().hset(
            f"agent:task:{task_id}",
            mapping={
                "status": "queued",
                "description": description,
                "repo": repo,
                "job_id": job.id,
                "task_type": "project_engineer",
                "mode": mode,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        get_agent_redis_client().expire(f"agent:task:{task_id}", 3600)

        # Store in DB
        try:
            from orchestrator.persistence.db_writer import upsert_task_queued
            upsert_task_queued(
                task_id=task_id,
                trace_id=task_id,
                question=description,  # Reuse question field for description
                job_id=job.id,
                tenant_id=tenant_id
            )

            if sentry_sdk:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='ProjectEngineer task enqueued to DB',
                    level='info',
                    data={
                        'task_id': task_id,
                        'trace_id': task_id,
                        'status': 'queued',
                        'mode': mode
                    }
                )
        except Exception as e:
            logger.error(f"DB write failed for task {task_id}: {e}")

        logger.info(f"enqueued project_engineer task_id={task_id} job_id={job.id} mode={mode}")

        return jsonify({
            "task_id": task_id,
            "status": "queued",
            "mode": mode
        }), 202
    except RedisConnectionError as e:
        logger.error("Redis connection failed for ProjectEngineer task creation", extra={
            "op": "project_engineer",
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None,
            "error_type": "redis_connection"
        })

        if sentry_sdk:
            if 'task_id' in locals():
                sentry_sdk.set_tag("trace_id", task_id)
                sentry_sdk.set_tag("task_id", task_id)
            sentry_sdk.add_breadcrumb(
                category='redis',
                message='Redis connection failed during ProjectEngineer task creation',
                level='error',
                data={'task_id': task_id if 'task_id' in locals() else None, 'description': description[:100]}
            )
            sentry_sdk.capture_exception(e)

        return jsonify({
            "error": {
                "code": "redis_unavailable",
                "message": "Service temporarily unavailable. Please try again later."
            }
        }), 503
    except Exception as e:
        logger.exception("Failed to enqueue ProjectEngineer task", extra={
            "op": "project_engineer",
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None
        })

        if sentry_sdk:
            if 'task_id' in locals():
                sentry_sdk.set_tag("trace_id", task_id)
                sentry_sdk.set_tag("task_id", task_id)
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
        key_type = get_agent_redis_client().type(key)
        
        if key_type == "hash":
            task_data = get_agent_redis_client().hgetall(key)
        elif key_type == "string":
            task_json = get_agent_redis_client().get(key)
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
        if get_agent_redis_client() is None or get_agent_redis_client_rq() is None:
            logger.error("Redis clients not initialized")
            return jsonify({
                "error": "Redis connection not available",
                "queue_length": 0,
                "recent_job_ids": [],
                "sample_task": None,
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
        try:
            get_agent_redis_client().ping()
            get_agent_redis_client_rq().ping()
        except (RedisConnectionError, AttributeError, Exception) as conn_err:
            logger.error(f"Redis connection test failed: {conn_err}")
            return jsonify({
                "error": "Redis connection unavailable",
                "queue_length": 0,
                "recent_job_ids": [],
                "sample_task": None,
                "timestamp": datetime.utcnow().isoformat()
            }), 503
        
        queue_name = settings.rq_queue_name or "orchestrator"
        queue_length = get_agent_redis_client_rq().llen(f"rq:queue:{queue_name}")
        
        recent_jobs = get_agent_redis_client_rq().lrange(f"rq:queue:{queue_name}", 0, 4)
        
        task_keys = list(get_agent_redis_client().scan_iter("agent:task:*", count=100))
        sample_task = None
        if task_keys:
            latest_key = sorted(task_keys)[-1] if task_keys else None
            if latest_key:
                key_type = get_agent_redis_client().type(latest_key)
                
                if key_type == "hash":
                    task_data = get_agent_redis_client().hgetall(latest_key)
                elif key_type == "string":
                    task_json = get_agent_redis_client().get(latest_key)
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
    except RedisConnectionError as e:
        logger.error(f"Redis connection error in debug endpoint: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({
            "error": "Redis connection error",
            "queue_length": 0,
            "recent_job_ids": [],
            "sample_task": None,
            "timestamp": datetime.utcnow().isoformat()
        }), 503
    except Exception as e:
        logger.error(f"Failed to get debug status: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": str(e)}), 500
