#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks with graceful shutdown and heartbeat monitoring

Environment Variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- RQ_QUEUE_NAME: Queue name to process (default: orchestrator)
- RQ_JOB_TIMEOUT: Job timeout in seconds (default: 600)
- SENTRY_DSN: Sentry DSN for error tracking (optional)
- RENDER_INSTANCE_ID / HOSTNAME: Worker identifier

Signal Handling:
- SIGTERM / SIGINT: Triggers graceful shutdown
  1. Sets shutting_down flag to stop accepting new tasks
  2. Waits for current tasks to complete (try/finally ensures cleanup)
  3. Updates heartbeat state to 'shutting_down'
  4. Cleans up heartbeat key and exits

Heartbeat:
- Updates worker:heartbeat:<worker_id> every 30s with 120s TTL
- Payload: {"state": "running|shutting_down", "last_heartbeat": "...", "timestamp": ...}
- Key deleted on clean shutdown or expires via TTL

Job Configuration:
- timeout=600 (job timeout, configurable via RQ_JOB_TIMEOUT)
- result_ttl=86400 (result retention: 24h)
- failure_ttl=3600 (failure retention: 1h)

Usage: python redis_queue/worker.py
"""

import os
import sys
import time
import json
import socket
import threading
import signal
import atexit
from datetime import datetime, timezone
from typing import Optional, List
from redis import Redis, ConnectionError as RedisConnectionError
from redis.retry import Retry as RedisRetry
from redis.backoff import ExponentialBackoff
from rq import Queue
from rq.decorators import job
from rq import Retry
from rq.serializers import JSONSerializer
import logging
from persistence.db_writer import (
    upsert_task_running,
    upsert_task_done,
    upsert_task_error
)
from common.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

_canary_metrics = None
_phase3_metrics = None


def sanitize_redis_mapping(mapping: dict) -> dict:
    """
    Remove None values from Redis mapping to prevent DataError.
    
    Redis commands like hset() require values to be bytes, string, int, or float.
    Passing None causes: redis.exceptions.DataError: Invalid input of type: 'NoneType'
    
    Args:
        mapping: Dictionary with potential None values
        
    Returns:
        Dictionary with None values filtered out
    """
    return {k: v for k, v in mapping.items() if v is not None}

SENTRY_DSN = settings.sentry_dsn
APP_VERSION = settings.app_version or "8.0.0"

if SENTRY_DSN and SENTRY_DSN.strip():
    try:
        import sentry_sdk
        from sentry_sdk.integrations.rq import RqIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=settings.environment or "production",
            release=f"morningai@{APP_VERSION}",
            integrations=[RqIntegration()],
            traces_sample_rate=1.0,
        )
        logger.info(f"Sentry initialized in worker with release morningai@{APP_VERSION}")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}. Continuing without Sentry integration.")
        SENTRY_DSN = None
else:
    SENTRY_DSN = None

redis_url = settings.redis_url
if not redis_url:
    import sys
    _api_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api-backend/src'))
    if _api_backend_path not in sys.path:
        sys.path.insert(0, _api_backend_path)
    
    try:
        from utils.redis_config import get_secure_redis_url
        redis_url = get_secure_redis_url(allow_local=settings.testing)
    except (ImportError, ValueError) as e:
        redis_url = "redis://localhost:6379/0"
        logger.warning(f"⚠️ Failed to get secure Redis URL: {e}, using fallback: {redis_url}")
else:
    if not redis_url.startswith("rediss://") and not redis_url.startswith("redis://localhost"):
        logger.warning(f"⚠️ Redis URL does not use TLS: {redis_url[:30]}...")
RQ_QUEUE_NAME = settings.rq_queue_name or "orchestrator"

redis_retry = RedisRetry(ExponentialBackoff(base=1, cap=10), retries=5)
redis = Redis.from_url(
    redis_url, 
    decode_responses=True,
    socket_connect_timeout=10,
    socket_keepalive=True,
    socket_keepalive_options={
        socket.TCP_KEEPIDLE: 30,
        socket.TCP_KEEPINTVL: 10,
        socket.TCP_KEEPCNT: 6
    },
    retry=redis_retry,
    retry_on_timeout=True
)
redis_client_rq = Redis.from_url(
    redis_url, 
    decode_responses=False,
    socket_connect_timeout=10,
    socket_keepalive=True,
    socket_keepalive_options={
        socket.TCP_KEEPIDLE: 30,
        socket.TCP_KEEPINTVL: 10,
        socket.TCP_KEEPCNT: 6
    },
    retry=redis_retry,
    retry_on_timeout=True
)
q = Queue(RQ_QUEUE_NAME, connection=redis_client_rq, serializer=JSONSerializer())

HEARTBEAT_ID = (
    os.getenv('RENDER_INSTANCE_ID') or 
    os.getenv('HOSTNAME') or 
    socket.gethostname() or 
    'worker'
)

RQ_WORKER_NAME = f"{HEARTBEAT_ID}-{os.getpid()}"

# Backward compatibility alias for tests and monitoring
WORKER_ID = RQ_WORKER_NAME

LEGACY_WORKER_NAME = "worker-local"

shutdown_event = threading.Event()
shutting_down = False
cleanup_started = False
heartbeat_thread = None

logger.info(
    f"Worker identity computed",
    extra={
        "operation": "startup",
        "worker_id": WORKER_ID,
        "heartbeat_id": HEARTBEAT_ID,
        "rq_worker_name": RQ_WORKER_NAME,
        "render_instance_id": os.getenv('RENDER_INSTANCE_ID'),
        "hostname_env": os.getenv('HOSTNAME'),
        "hostname_socket": socket.gethostname(),
        "pid": os.getpid()
    }
)

def update_worker_heartbeat():
    """
    Background thread to update worker heartbeat in Redis with TTL.
    Runs until shutdown_event is set.
    Updates state to 'shutting_down' when shutdown is initiated.
    Uses HEARTBEAT_ID for stable monitoring identity.
    """
    logger.info(f"Heartbeat thread started", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME})
    
    while not shutdown_event.is_set():
        try:
            if redis:
                heartbeat_key = f"worker:heartbeat:{HEARTBEAT_ID}"
                state = "shutting_down" if shutting_down else "running"
                redis.setex(
                    heartbeat_key,
                    120,
                    json.dumps({
                        "state": state,
                        "last_heartbeat": datetime.now(timezone.utc).isoformat() + "Z",
                        "worker_id": WORKER_ID,
                        "heartbeat_id": HEARTBEAT_ID,
                        "rq_worker_name": RQ_WORKER_NAME,
                        "timestamp": int(time.time())
                    })
                )
                logger.debug(f"Heartbeat updated", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME, "state": state})
            
            shutdown_event.wait(30)
        except RedisConnectionError as e:
            logger.error(f"Heartbeat Redis connection error: {e}", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            shutdown_event.wait(30)
        except Exception as e:
            logger.exception(f"Heartbeat update failed", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            shutdown_event.wait(30)
    
    logger.info(f"Heartbeat thread stopped", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})

def cleanup_heartbeat():
    """
    Cleanup function to gracefully shutdown heartbeat thread.
    Called on worker shutdown or exit.
    Sets shutting_down flag, updates heartbeat state, and cleans up Redis keys.
    Uses RQ_WORKER_NAME for RQ cleanup and HEARTBEAT_ID for heartbeat cleanup.
    Idempotent: safe to call multiple times.
    """
    global heartbeat_thread, shutting_down, cleanup_started
    
    if cleanup_started:
        logger.debug(f"Cleanup already in progress, skipping duplicate call", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME})
        return
    
    cleanup_started = True
    logger.info(f"Initiating graceful shutdown", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME})
    shutting_down = True
    
    try:
        heartbeat_key = f"worker:heartbeat:{HEARTBEAT_ID}"
        redis.setex(
            heartbeat_key,
            120,
            json.dumps({
                "state": "shutting_down",
                "last_heartbeat": datetime.now(timezone.utc).isoformat() + "Z",
                "worker_id": WORKER_ID,
                "heartbeat_id": HEARTBEAT_ID,
                "rq_worker_name": RQ_WORKER_NAME,
                "timestamp": int(time.time())
            })
        )
        logger.info(f"Updated heartbeat state to shutting_down", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})
    except Exception as e:
        logger.exception(f"Failed to update heartbeat state during shutdown", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
    
    shutdown_event.set()
    
    if heartbeat_thread and heartbeat_thread.is_alive():
        heartbeat_thread.join(timeout=5)
        if heartbeat_thread.is_alive():
            logger.warning(f"Heartbeat thread did not stop within timeout", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})
        else:
            logger.info(f"Heartbeat thread stopped successfully", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID})
    
    try:
        if redis_client_rq:
            redis_client_rq.srem('rq:workers', WORKER_ID)
            logger.info(f"Removed worker from rq:workers set", extra={"operation": "shutdown", "worker_id": WORKER_ID})
        
        if redis:
            heartbeat_key = f"worker:heartbeat:{HEARTBEAT_ID}"
            redis.delete(heartbeat_key)
            logger.info(f"Cleaned up heartbeat key", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "key": heartbeat_key})
    except Exception as e:
        logger.exception(f"Failed to cleanup Redis keys", extra={"operation": "shutdown", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME})
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)

def signal_handler(signum, frame):
    """Handle termination signals gracefully (SIGTERM from container orchestrator, SIGINT from Ctrl+C)"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown", extra={"operation": "signal_handler", "signal": signum, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME})
    cleanup_heartbeat()
    sys.exit(0)

def run_step(step: str):
    """Demo function for testing worker with steps"""
    print(f"[Worker] running step: {step}")
    time.sleep(2)
    if step == "check CI":
        return {"ok": False, "error": "build failed"}
    return {"ok": True}

def enqueue(steps, idempotency_key: Optional[str] = None) -> List[str]:
    """
    Enqueue steps to RQ worker (used by graph.py for orchestrator demo)
    
    Args:
        steps: List of step names to execute
        idempotency_key: Optional key to prevent duplicate job submission
    
    Returns:
        List of job IDs
    """
    try:
        if idempotency_key:
            key = f"orchestrator:job:{idempotency_key}"
            if redis.exists(key):
                result = redis.get(key)
                if result:
                    existing_job_ids = result.split(',')
                    logger.info(f"Job with idempotency key already exists", extra={"operation": "enqueue", "idempotency_key": idempotency_key, "job_ids": existing_job_ids})
                    return existing_job_ids
            
            jobs = [q.enqueue(run_step, s, ttl=600, result_ttl=86400, failure_ttl=3600) for s in steps]
            job_ids = [j.id for j in jobs]
            
            redis.setex(key, 3600, ','.join(job_ids))
            logger.info(f"Created idempotent jobs", extra={"operation": "enqueue", "idempotency_key": idempotency_key, "job_ids": job_ids})
            return job_ids
        else:
            jobs = [q.enqueue(run_step, s, ttl=600, result_ttl=86400, failure_ttl=3600) for s in steps]
            job_ids = [j.id for j in jobs]
            logger.info(f"Enqueued jobs", extra={"operation": "enqueue", "job_ids": job_ids})
            return job_ids
    except Exception as e:
        logger.exception(f"Redis unavailable, running in demo mode", extra={"operation": "enqueue"})
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        return [f"demo-job-{i}" for i in range(len(steps))]

# Job timeout configuration (default: 600 seconds = 10 minutes)
# Can be overridden via RQ_JOB_TIMEOUT environment variable
JOB_TIMEOUT = int(os.getenv("RQ_JOB_TIMEOUT", "600"))

@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=3, interval=[10, 30, 60]), timeout=JOB_TIMEOUT)
def run_orchestrator_task(task_id: str, question: str, repo: str):
    """
    Execute orchestrator with retry logic (used by API for agent tasks)
    Configured with ttl=600, result_ttl=86400, failure_ttl=3600
    
    Supports two modes:
    - LangGraph mode (USE_LANGGRAPH=true): Full stateful workflow with retry logic
    - Simple mode (default): Direct execution for faster response
    
    Args:
        task_id: Unique task identifier (also used as trace_id)
        question: FAQ question or topic
        repo: GitHub repository (owner/repo format)
    
    Returns:
        dict: {"pr_url": str, "trace_id": str, "state": str}
    """
    global _canary_metrics
    if _canary_metrics is None:
        try:
            from metrics import create_canary_metrics
            canary_metrics_enabled = getattr(settings, 'canary_metrics_enabled', True)
            _canary_metrics = create_canary_metrics(redis, enabled=canary_metrics_enabled)
            logger.info(f"Canary metrics initialized: enabled={canary_metrics_enabled}")
        except Exception as e:
            logger.warning(f"Failed to initialize canary metrics: {e}")
            _canary_metrics = None
    
    use_langgraph = settings.use_langgraph or False
    use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)
    
    if not use_langgraph and use_langgraph_percent > 0:
        import hashlib
        task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
        task_percent = task_hash % 100
        use_langgraph = task_percent < use_langgraph_percent
        
        logger.info(
            f"Canary deployment: task_percent={task_percent}, threshold={use_langgraph_percent}, use_langgraph={use_langgraph}",
            extra={
                "operation": "canary_selection",
                "task_id": task_id,
                "task_percent": task_percent,
                "use_langgraph_percent": use_langgraph_percent,
                "use_langgraph": use_langgraph
            }
        )
    
    if _canary_metrics:
        try:
            if use_langgraph:
                _canary_metrics.incr_counter("decisions.langgraph")
            else:
                _canary_metrics.incr_counter("decisions.simple")
        except Exception as e:
            logger.warning(f"Failed to record routing decision metric: {e}")
    
    if use_langgraph:
        from langgraph_orchestrator import run_orchestrator
        logger.info(f"Using LangGraph orchestrator for task {task_id}")
    else:
        from graph import execute
        logger.info(f"Using simple orchestrator for task {task_id}")
    
    job_id = task_id
    logger.info(f"Starting orchestrator task", extra={"operation": "run_orchestrator_task", "task_id": task_id, "job_id": job_id, "trace_id": task_id, "question": question[:50]})
    
    if SENTRY_DSN:
        sentry_sdk.set_tag("trace_id", task_id)
        sentry_sdk.set_tag("task_id", task_id)
        sentry_sdk.set_tag("operation", "orchestrator_task")
        sentry_sdk.add_breadcrumb(
            category='task',
            message=f'Starting orchestrator task',
            level='info',
            data={'task_id': task_id, 'job_id': job_id, 'trace_id': task_id, 'question': question, 'repo': repo}
        )
    
    try:
        redis_key = f"agent:task:{task_id}"
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='redis',
                message=f'Updating task status to running',
                level='info',
                data={'redis_key': redis_key, 'task_id': task_id}
            )
        
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": "running",
                "question": question,
                "trace_id": task_id,
                "job_id": job_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(redis_key, 3600)
        
        try:
            upsert_task_running(task_id=task_id, trace_id=task_id)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task status updated to running in DB',
                    level='info',
                    data={'task_id': task_id, 'trace_id': task_id, 'status': 'running'}
                )
        except Exception as e:
            logger.error(f"DB write failed for task {task_id} (running): {e}")
        
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='orchestrator',
                message=f'Executing orchestrator',
                level='info',
                data={'task_id': task_id, 'trace_id': task_id, 'use_langgraph': use_langgraph}
            )
        
        start_time_ns = time.monotonic_ns()
        execution_success = False
        
        if use_langgraph:
            result = run_orchestrator(question, repo, task_id)
            pr_url = result.get("pr_url", "")
            state = result.get("ci_state", "unknown")
            trace_id = result.get("trace_id", task_id)
            execution_success = bool(pr_url)  # Success if PR was created
        else:
            pr_url, state, trace_id = execute(question, repo, trace_id=task_id)
            execution_success = bool(pr_url)  # Success if PR was created
        
        if _canary_metrics and use_langgraph:
            try:
                elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000
                _canary_metrics.observe_latency_ms(elapsed_ms)
                
                if execution_success:
                    _canary_metrics.incr_counter("planner.success")
                else:
                    _canary_metrics.incr_counter("planner.failure")
                    
                logger.info(f"Canary metrics recorded: latency={elapsed_ms:.2f}ms, success={execution_success}")
                
                canary_alerting_enabled = getattr(settings, 'canary_alerting_enabled', True)
                if canary_alerting_enabled:
                    try:
                        # This prevents alert storms and reduces Redis GET load by ~60x
                        eval_lock_key = "metrics:canary:slo_eval_lock"
                        acquired_lock = redis.set(eval_lock_key, "1", ex=60, nx=True)
                        
                        if acquired_lock:
                            from canary_alerting import create_canary_alerting
                            
                            canary_window_minutes = getattr(settings, 'canary_window_minutes', 15)
                            canary_p95_threshold = getattr(settings, 'canary_p95_ms_threshold', 2500)
                            canary_5xx_threshold = getattr(settings, 'canary_5xx_rate_threshold', 1.0)
                            canary_failure_threshold = getattr(settings, 'canary_failure_rate_threshold', 5.0)
                            ops_webhook_url = getattr(settings, 'ops_alert_webhook_url', None)
                            
                            canary_summary = _canary_metrics.get_canary_summary(window_minutes=canary_window_minutes)
                            
                            alerting = create_canary_alerting(
                                redis,
                                enabled=True,
                                sentry_dsn=SENTRY_DSN,
                                webhook_url=ops_webhook_url
                            )
                            
                            thresholds = {
                                'p95_ms': canary_p95_threshold,
                                'error_5xx_rate': canary_5xx_threshold,
                                'failure_rate': canary_failure_threshold
                            }
                            
                            alerting.evaluate_slos(canary_summary, thresholds)
                            logger.info("SLO evaluation completed")
                    except Exception as alert_error:
                        logger.warning(f"Failed to evaluate SLOs: {alert_error}")
            except Exception as e:
                logger.warning(f"Failed to record execution metrics: {e}")
        
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='redis',
                message=f'Updating task status to done',
                level='info',
                data={'redis_key': redis_key, 'task_id': task_id, 'pr_url': pr_url}
            )
        
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": "done",
                "question": question,
                "trace_id": trace_id,
                "job_id": job_id,
                "pr_url": pr_url,
                "state": state,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(redis_key, 3600)
        
        try:
            upsert_task_done(task_id=task_id, trace_id=trace_id, pr_url=pr_url)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task completed and persisted to DB',
                    level='info',
                    data={
                        'task_id': task_id,
                        'trace_id': trace_id,
                        'status': 'done',
                        'pr_url': pr_url
                    }
                )
        except Exception as e:
            logger.error(f"DB write failed for task {task_id} (done): {e}")
        
        logger.info(f"Job OK", extra={"operation": "run_orchestrator_task", "task_id": task_id, "job_id": job_id, "trace_id": trace_id, "status": "done", "pr_url": pr_url})
        return {"pr_url": pr_url, "trace_id": trace_id, "state": state}
        
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Task failed", extra={"operation": "run_orchestrator_task", "task_id": task_id, "job_id": job_id, "trace_id": task_id, "status": "error", "error": error_msg})
        
        if _canary_metrics and use_langgraph:
            try:
                _canary_metrics.incr_counter("planner.error_5xx")
            except Exception as metric_error:
                logger.warning(f"Failed to record error metric: {metric_error}")
        
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='error',
                message=f'Task execution failed',
                level='error',
                data={'task_id': task_id, 'trace_id': task_id, 'error': error_msg}
            )
            sentry_sdk.capture_exception(e)
        
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='redis',
                message=f'Updating task status to error',
                level='error',
                data={'redis_key': f"agent:task:{task_id}", 'task_id': task_id}
            )
        
        redis.hset(
            f"agent:task:{task_id}",
            mapping=sanitize_redis_mapping({
                "status": "error",
                "question": question,
                "trace_id": task_id,
                "job_id": job_id,
                "error_code": "ORCHESTRATOR_FAILED",
                "error_message": error_msg,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(f"agent:task:{task_id}", 3600)
        
        try:
            upsert_task_error(task_id=task_id, trace_id=task_id, error_msg=error_msg)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task error persisted to DB',
                    level='error',
                    data={
                        'task_id': task_id,
                        'trace_id': task_id,
                        'status': 'error',
                        'error_msg': error_msg[:200]
                    }
                )
        except Exception as db_error:
            logger.error(f"DB write failed for task {task_id} (error): {db_error}")
        
        raise


@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=3, interval=[10, 30, 60]), timeout=JOB_TIMEOUT)
def run_project_engineer_task(task_id: str, description: str, repo: str, tenant_id: str):
    """
    Execute ProjectEngineerAgent task for human-initiated requests (Phase 3 PR-3)

    This is the human entry point for ProjectEngineerAgent, allowing users to submit
    natural language task descriptions through the API.

    Args:
        task_id: Unique task identifier (also used as trace_id)
        description: Natural language task description
        repo: GitHub repository (owner/repo format)
        tenant_id: Tenant UUID for multi-tenant isolation

    Returns:
        dict: {"task_id": str, "status": str, "results": list, "trace_id": str}

    Feature Flags:
        - ENABLE_PROJECT_ENGINEER_CODEGEN: Controls code generation mode
          - false: Analysis-only mode (safe, no code changes)
          - true: Execution mode (can create PRs)
    """
    import asyncio

    # Phase 3 PR-5: Initialize Phase 3 metrics
    global _phase3_metrics
    if _phase3_metrics is None:
        try:
            from phase3_metrics import create_phase3_metrics
            phase3_metrics_enabled = getattr(settings, 'phase3_metrics_enabled', True)
            _phase3_metrics = create_phase3_metrics(redis, enabled=phase3_metrics_enabled)
            logger.info(f"[Phase3Metrics] Initialized: enabled={phase3_metrics_enabled}")
        except Exception as e:
            logger.warning(f"[Phase3Metrics] Failed to initialize: {e}")
            _phase3_metrics = None

    job_id = task_id
    logger.info(
        "[ProjectEngineerAgent] Starting task",
        extra={
            "operation": "run_project_engineer_task",
            "task_id": task_id,
            "job_id": job_id,
            "trace_id": task_id,
            "tenant_id": tenant_id,
            "description": description[:100] if description else "",
            "repo": repo
        }
    )

    if SENTRY_DSN:
        sentry_sdk.set_tag("trace_id", task_id)
        sentry_sdk.set_tag("task_id", task_id)
        sentry_sdk.set_tag("tenant_id", tenant_id)
        sentry_sdk.set_tag("operation", "project_engineer_task")
        sentry_sdk.add_breadcrumb(
            category='task',
            message='Starting ProjectEngineerAgent task',
            level='info',
            data={'task_id': task_id, 'job_id': job_id, 'trace_id': task_id, 'tenant_id': tenant_id, 'description': description[:100], 'repo': repo}
        )

    # Phase 3 PR-5: Start timing before try block to capture elapsed time on exceptions
    start_time_ns = time.monotonic_ns()

    try:
        # Update Redis status to running
        redis_key = f"agent:task:{task_id}"
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": "running",
                "description": description,
                "trace_id": task_id,
                "job_id": job_id,
                "task_type": "project_engineer",
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(redis_key, 3600)

        # Update DB status to running
        try:
            upsert_task_running(task_id=task_id, trace_id=task_id, tenant_id=tenant_id)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task status updated to running in DB',
                    level='info',
                    data={'task_id': task_id, 'trace_id': task_id, 'tenant_id': tenant_id, 'status': 'running'}
                )
        except Exception as e:
            logger.error(f"DB write failed for task {task_id} (running): {e}")

        # Initialize and run ProjectEngineerAgent
        try:
            from project_engineer.agent import ProjectEngineerAgent
        except ImportError as e:
            logger.error(f"[ProjectEngineerAgent] Failed to import: {e}")
            raise ImportError(f"ProjectEngineerAgent not available: {e}")

        # Respect existing feature flags
        enable_codegen = settings.enable_project_engineer_codegen
        logger.info(
            "[ProjectEngineerAgent] Initializing agent",
            extra={
                "operation": "run_project_engineer_task",
                "task_id": task_id,
                "enable_codegen": enable_codegen,
                "mode": "execution" if enable_codegen else "analysis_only"
            }
        )

        # Initialize agent. A DevAgent instance is required for execution mode.
        # Pattern from fixer_integration.py: AutoFixer._create_dev_agent()
        dev_agent_instance = None
        if enable_codegen:
            try:
                from agents.dev_agent.dev_agent_wrapper import DevAgent
                dev_agent_instance = DevAgent(openai_api_key=settings.openai_api_key)
                logger.info("[ProjectEngineerAgent] DevAgent initialized for execution mode")
            except ImportError as e:
                logger.error(f"[ProjectEngineerAgent] Failed to import DevAgent: {e}")
                raise ImportError(f"DevAgent required for execution mode but not available: {e}")
            except Exception as e:
                logger.error(f"[ProjectEngineerAgent] Failed to create DevAgent: {e}")
                raise

        agent = ProjectEngineerAgent(enable_code_generation=enable_codegen, dev_agent=dev_agent_instance)

        # Phase 3 PR-4: Get task timeout from agent settings
        task_timeout = agent._get_task_timeout()
        logger.info(
            "[ProjectEngineerAgent] Running task with timeout",
            extra={
                "operation": "run_project_engineer_task",
                "task_id": task_id,
                "timeout_seconds": task_timeout
            }
        )

        # Run the task asynchronously with timeout (Phase 3 PR-4: Agent-level timeout)
        # Note: start_time_ns is set before the main try block (line 693)

        async def run_with_timeout():
            """Wrapper to enforce task timeout"""
            return await asyncio.wait_for(
                agent.run_task(description, repo),
                timeout=task_timeout
            )

        try:
            results = asyncio.run(run_with_timeout())
        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000
            logger.error(
                "[ProjectEngineerAgent] Task timed out",
                extra={
                    "operation": "run_project_engineer_task",
                    "task_id": task_id,
                    "timeout_seconds": task_timeout,
                    "elapsed_ms": elapsed_ms
                }
            )
            
            # Phase 3 PR-5: Record timeout metrics (Phase3Metrics has internal error handling)
            if _phase3_metrics:
                _phase3_metrics.record_timeout(
                    task_id=task_id,
                    timeout_seconds=task_timeout,
                    elapsed_ms=elapsed_ms
                )
            
            # Return timeout error result
            from project_engineer.agent import TaskResult
            results = [TaskResult(
                task_id=task_id,
                task_type="timeout",
                status="failed",
                is_safe=False,
                details=f"Task execution timed out after {task_timeout} seconds",
                error=f"TimeoutError: Task exceeded {task_timeout}s limit"
            )]

        elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000

        # Process results
        success_count = sum(1 for r in results if r.status == "success")
        failed_count = sum(1 for r in results if r.status == "failed")
        skipped_count = sum(1 for r in results if r.status == "skipped")

        # Extract PR URL if any task created one
        pr_url = None
        pr_number = None
        for r in results:
            if r.pr_url:
                pr_url = r.pr_url
                pr_number = r.pr_number
                break

        # Determine overall status
        if failed_count > 0:
            overall_status = "partial_success" if success_count > 0 else "failed"
        elif success_count > 0:
            overall_status = "done"
        else:
            overall_status = "done"  # All skipped is still "done" (analysis-only mode)

        # Serialize results for storage
        results_serialized = [
            {
                "task_id": r.task_id,
                "task_type": r.task_type,
                "status": r.status,
                "is_safe": r.is_safe,
                "details": r.details,
                "pr_number": r.pr_number,
                "pr_url": r.pr_url,
                "error": r.error
            }
            for r in results
        ]

        logger.info(
            "[ProjectEngineerAgent] Task completed",
            extra={
                "operation": "run_project_engineer_task",
                "task_id": task_id,
                "trace_id": task_id,
                "overall_status": overall_status,
                "success_count": success_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "elapsed_ms": elapsed_ms,
                "pr_url": pr_url
            }
        )

        # Phase 3 PR-5: Record task execution metrics (Phase3Metrics has internal error handling)
        if _phase3_metrics:
            # Determine task type from results (use first result's task_type or "general")
            task_type = "general"
            if results and len(results) > 0:
                task_type = results[0].task_type or "general"

            # Determine status for metrics
            if overall_status == "done":
                metrics_status = "success"
            elif overall_status == "partial_success":
                metrics_status = "success"  # Count partial success as success for metrics
            else:
                metrics_status = "failed"

            # Determine mode
            mode = "execution" if enable_codegen else "analysis_only"

            _phase3_metrics.record_task_execution(
                task_id=task_id,
                status=metrics_status,
                task_type=task_type,
                elapsed_ms=elapsed_ms,
                mode=mode,
                tenant_id=tenant_id
            )

        # Update Redis with final status
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": overall_status,
                "description": description,
                "trace_id": task_id,
                "job_id": job_id,
                "task_type": "project_engineer",
                "pr_url": pr_url,
                "pr_number": pr_number,
                "success_count": success_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "elapsed_ms": int(elapsed_ms),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(redis_key, 3600)

        # Update DB with final status
        try:
            if pr_url:
                upsert_task_done(task_id=task_id, trace_id=task_id, pr_url=pr_url, tenant_id=tenant_id)
            else:
                upsert_task_done(task_id=task_id, trace_id=task_id, pr_url="", tenant_id=tenant_id)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task completed and persisted to DB',
                    level='info',
                    data={
                        'task_id': task_id,
                        'trace_id': task_id,
                        'tenant_id': tenant_id,
                        'status': overall_status,
                        'pr_url': pr_url
                    }
                )
        except Exception as e:
            logger.error(f"DB write failed for task {task_id} (done): {e}")

        return {
            "task_id": task_id,
            "status": overall_status,
            "results": results_serialized,
            "trace_id": task_id,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "elapsed_ms": int(elapsed_ms)
        }

    except Exception as e:
        error_msg = str(e)
        logger.exception(
            "[ProjectEngineerAgent] Task failed",
            extra={
                "operation": "run_project_engineer_task",
                "task_id": task_id,
                "job_id": job_id,
                "trace_id": task_id,
                "status": "error",
                "error": error_msg
            }
        )

        # Phase 3 PR-5: Record failed task metrics (Phase3Metrics has internal error handling)
        # Note: start_time_ns is set before the main try block (line 693)
        if _phase3_metrics:
            elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000
            mode = "execution" if enable_codegen else "analysis_only"
            _phase3_metrics.record_task_execution(
                task_id=task_id,
                status="failed",
                task_type="general",
                elapsed_ms=elapsed_ms,
                mode=mode,
                tenant_id=tenant_id
            )

        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='error',
                message='ProjectEngineerAgent task execution failed',
                level='error',
                data={'task_id': task_id, 'trace_id': task_id, 'error': error_msg}
            )
            sentry_sdk.capture_exception(e)

        # Update Redis with error status
        redis.hset(
            f"agent:task:{task_id}",
            mapping=sanitize_redis_mapping({
                "status": "error",
                "description": description,
                "trace_id": task_id,
                "job_id": job_id,
                "task_type": "project_engineer",
                "error_code": "PROJECT_ENGINEER_FAILED",
                "error_message": error_msg,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(f"agent:task:{task_id}", 3600)

        # Update DB with error status
        try:
            upsert_task_error(task_id=task_id, trace_id=task_id, error_msg=error_msg, tenant_id=tenant_id)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task error persisted to DB',
                    level='error',
                    data={
                        'task_id': task_id,
                        'trace_id': task_id,
                        'tenant_id': tenant_id,
                        'status': 'error',
                        'error_msg': error_msg[:200]
                    }
                )
        except Exception as db_error:
            logger.error(f"DB write failed for task {task_id} (error): {db_error}")

        raise


def cleanup_stale_legacy_worker():
    """
    Defensive cleanup for stale legacy 'worker-local' registrations.
    Only cleans up if:
    1. The legacy worker name exists in rq:workers
    2. The heartbeat key for legacy worker is missing or expired
    This prevents nuking a live worker while recovering from stale registrations.
    """
    try:
        if redis_client_rq and redis:
            is_registered = redis_client_rq.sismember('rq:workers', LEGACY_WORKER_NAME)
            
            if is_registered:
                heartbeat_key = f"worker:heartbeat:{LEGACY_WORKER_NAME}"
                heartbeat_exists = redis.exists(heartbeat_key)
                
                if not heartbeat_exists:
                    logger.warning(
                        f"Detected stale legacy worker registration without heartbeat, cleaning up",
                        extra={
                            "operation": "startup",
                            "legacy_worker_name": LEGACY_WORKER_NAME,
                            "heartbeat_key": heartbeat_key
                        }
                    )
                    redis_client_rq.srem('rq:workers', LEGACY_WORKER_NAME)
                    logger.info(
                        f"Removed stale legacy worker from rq:workers",
                        extra={"operation": "startup", "legacy_worker_name": LEGACY_WORKER_NAME}
                    )
                else:
                    logger.info(
                        f"Legacy worker has active heartbeat, skipping cleanup",
                        extra={
                            "operation": "startup",
                            "legacy_worker_name": LEGACY_WORKER_NAME,
                            "heartbeat_key": heartbeat_key
                        }
                    )
    except Exception as e:
        logger.warning(
            f"Failed to cleanup stale legacy worker (non-fatal): {e}",
            extra={"operation": "startup", "legacy_worker_name": LEGACY_WORKER_NAME}
        )
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)

if __name__ == "__main__":
    from rq import Worker
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_heartbeat)
    
    logger.info(
        f"Starting RQ worker",
        extra={
            "operation": "startup",
            "heartbeat_id": HEARTBEAT_ID,
            "rq_worker_name": RQ_WORKER_NAME,
            "queue": RQ_QUEUE_NAME,
            "redis_url": redis_url[:30] + "..." if len(redis_url) > 30 else redis_url
        }
    )
    
    logger.info(
        f"Feature flags snapshot",
        extra={
            "operation": "startup",
            "flags": {
                "use_langgraph": settings.use_langgraph,
                "use_langgraph_percent": getattr(settings, 'use_langgraph_percent', 0),
                "use_llm_planner": getattr(settings, 'use_llm_planner', False),
                "canary_metrics_enabled": getattr(settings, 'canary_metrics_enabled', True),
                "canary_alerting_enabled": getattr(settings, 'canary_alerting_enabled', True),
                "sentry_dsn_configured": bool(SENTRY_DSN)
            }
        }
    )
    
    cleanup_stale_legacy_worker()
    
    heartbeat_thread = threading.Thread(target=update_worker_heartbeat, daemon=False, name="HeartbeatThread")
    heartbeat_thread.start()
    logger.info(
        f"Heartbeat monitoring enabled",
        extra={
            "operation": "startup",
            "heartbeat_id": HEARTBEAT_ID,
            "rq_worker_name": RQ_WORKER_NAME,
            "ttl": 120,
            "interval": 30
        }
    )
    
    max_retries = 1
    for attempt in range(max_retries + 1):
        try:
            worker = Worker(
                [q],
                connection=redis_client_rq,
                name=RQ_WORKER_NAME,
                default_worker_ttl=600,
                default_result_ttl=86400,
                serializer=JSONSerializer()
            )
            logger.info(
                f"Worker configuration complete",
                extra={
                    "operation": "startup",
                    "heartbeat_id": HEARTBEAT_ID,
                    "rq_worker_name": RQ_WORKER_NAME,
                    "worker_ttl": 600,
                    "result_ttl": 86400,
                    "serializer": "JSONSerializer"
                }
            )
            worker.work()
            break  # Success, exit retry loop
        except ValueError as e:
            if "exists an active worker" in str(e) and attempt < max_retries:
                import random
                suffix = f"{int(time.time())}-{random.randint(1000, 9999)}"
                RQ_WORKER_NAME = f"{HEARTBEAT_ID}-{os.getpid()}-{suffix}"
                WORKER_ID = RQ_WORKER_NAME  # Sync WORKER_ID for cleanup compatibility
                logger.warning(
                    f"Worker name collision detected, retrying with new name",
                    extra={
                        "operation": "startup",
                        "error": str(e),
                        "new_rq_worker_name": RQ_WORKER_NAME,
                        "worker_id": WORKER_ID,
                        "attempt": attempt + 1
                    }
                )
                continue
            else:
                raise
        except KeyboardInterrupt:
            logger.info(
                f"KeyboardInterrupt received",
                extra={"operation": "shutdown", "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME}
            )
            break
        except Exception as e:
            logger.exception(
                f"Unexpected worker error",
                extra={"operation": "shutdown", "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME}
            )
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            raise
    
    cleanup_heartbeat()
    logger.info(
        f"Worker shutdown complete",
        extra={"operation": "shutdown", "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME}
    )
