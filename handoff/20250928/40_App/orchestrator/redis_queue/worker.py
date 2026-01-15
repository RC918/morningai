#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks with graceful shutdown and heartbeat monitoring

Environment Variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- RQ_QUEUE_NAME: Queue name to process (default: orchestrator)
- RQ_JOB_TIMEOUT: Job timeout in seconds (default: 600)
- RQ_MAX_JOBS: Max jobs before worker restart (default: 0 = unlimited)
  Recommended: 10-20 for LangGraph workloads to prevent OOM from MemorySaver
- SENTRY_DSN: Sentry DSN for error tracking (optional)
- RENDER_INSTANCE_ID / HOSTNAME: Worker identifier

Signal Handling:
- SIGTERM / SIGINT: Triggers graceful shutdown
  1. Sets shutting_down flag to stop accepting new tasks
  2. Waits for current tasks to complete (try/finally ensures cleanup)
  3. Updates heartbeat state to 'shutting_down'
  4. Cleans up heartbeat key and exits

Heartbeat:
- Updates worker:heartbeat:<worker_id> every WORKER_HEARTBEAT_INTERVAL (default 60s) with WORKER_HEARTBEAT_TTL (default 180s)
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
from typing import Optional, List, Dict, Any
from redis import Redis, ConnectionError as RedisConnectionError
from redis.exceptions import ReadOnlyError
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

try:
    from governance.runtime_policy_enforcer import (
        get_runtime_policy_enforcer,
        EnforcementAction,
    )
except ImportError:
    get_runtime_policy_enforcer = None
    EnforcementAction = None

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

_canary_metrics = None
_phase3_metrics = None
_rollout_tracker = None


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

redis_retry = RedisRetry(
    ExponentialBackoff(base=1, cap=10),
    retries=5,
    supported_errors=(RedisConnectionError, TimeoutError, ReadOnlyError)
)
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
    settings.render_instance_id or 
    settings.hostname or 
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
        "render_instance_id": settings.render_instance_id,
        "hostname_env": settings.hostname,
        "hostname_socket": socket.gethostname(),
        "pid": os.getpid()
    }
)

# Heartbeat configuration - optimized to reduce Redis command volume
# Interval increased from 30s to 60s to reduce commands by 50%
# TTL increased from 120s to 180s to maintain 3x safety margin
# Now uses settings.worker_heartbeat_interval/ttl instead of os.getenv for centralized configuration
HEARTBEAT_INTERVAL = settings.worker_heartbeat_interval
HEARTBEAT_TTL = settings.worker_heartbeat_ttl


def _run_governance_heartbeat():
    """
    Execute governance heartbeat cycle with full error isolation.
    
    EPIC I-1: Operationalization (Heartbeat + Distributed Lock)
    
    This function is called after each worker heartbeat update.
    It acquires a distributed lock and runs health checks + degradation advisory.
    
    Safety Contract:
    - Governance failures MUST NOT affect worker heartbeat
    - Non-blocking: Returns immediately if lock is held by another worker
    - All exceptions are caught and logged
    """
    try:
        from governance.heartbeat_handler import run_governance_cycle
        
        result = run_governance_cycle(
            redis_client=redis,
            evaluator_node_id=HEARTBEAT_ID,
            heartbeat_id=HEARTBEAT_ID,
            worker_id=WORKER_ID,
        )
        
        # Only log at DEBUG if skipped (to avoid log noise)
        if not result.executed and result.skipped_reason:
            logger.debug(
                f"Governance cycle skipped: {result.skipped_reason}",
                extra={
                    "operation": "governance_heartbeat",
                    "worker_id": WORKER_ID,
                    "heartbeat_id": HEARTBEAT_ID,
                    "skipped_reason": result.skipped_reason,
                }
            )
    except ImportError as e:
        # Governance module not available - this is expected in some environments
        logger.debug(
            f"Governance heartbeat not available: {e}",
            extra={
                "operation": "governance_heartbeat",
                "worker_id": WORKER_ID,
                "heartbeat_id": HEARTBEAT_ID,
            }
        )
    except Exception as e:
        # Catch all exceptions to ensure governance never affects worker heartbeat
        logger.warning(
            f"Governance heartbeat failed (isolated): {e}",
            extra={
                "operation": "governance_heartbeat",
                "worker_id": WORKER_ID,
                "heartbeat_id": HEARTBEAT_ID,
                "error": str(e),
            }
        )
        if SENTRY_DSN:
            try:
                sentry_sdk.capture_exception(e)
            except Exception:
                pass  # Sentry failure should not propagate


def update_worker_heartbeat():
    """
    Background thread to update worker heartbeat in Redis with TTL.
    Runs until shutdown_event is set.
    Updates state to 'shutting_down' when shutdown is initiated.
    Uses HEARTBEAT_ID for stable monitoring identity.
    
    EPIC I-1: Also triggers governance heartbeat cycle after each heartbeat update.
    Governance runs with distributed lock to ensure only one worker executes.
    
    Configuration (via settings.py):
    - settings.worker_heartbeat_interval: Heartbeat interval in seconds (default: 60)
    - settings.worker_heartbeat_ttl: Heartbeat key TTL in seconds (default: 180)
    """
    logger.info(f"Heartbeat thread started (interval={HEARTBEAT_INTERVAL}s, ttl={HEARTBEAT_TTL}s)", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME})
    
    while not shutdown_event.is_set():
        try:
            if redis:
                heartbeat_key = f"worker:heartbeat:{HEARTBEAT_ID}"
                state = "shutting_down" if shutting_down else "running"
                redis.setex(
                    heartbeat_key,
                    HEARTBEAT_TTL,
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
                
                # EPIC I-1: Run governance heartbeat after worker heartbeat
                # This is failure-isolated - governance errors never affect worker heartbeat
                if not shutting_down:
                    _run_governance_heartbeat()
            
            shutdown_event.wait(HEARTBEAT_INTERVAL)
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
# Now uses settings.rq_job_timeout instead of os.getenv for centralized configuration
JOB_TIMEOUT = settings.rq_job_timeout

# Max jobs configuration for memory management
# Worker will exit after processing this many jobs, allowing container orchestrator to restart
# This helps prevent memory accumulation from LangGraph MemorySaver checkpoints
# Set to 0 or None to disable (process unlimited jobs)
# Recommended: 10-20 for LangGraph workloads to prevent OOM
# Now uses settings.rq_max_jobs instead of os.getenv for centralized configuration
# Explicitly check for 0 to convert to None (unlimited), as 0 is a valid integer but means "no limit"
MAX_JOBS = settings.rq_max_jobs if settings.rq_max_jobs != 0 else None

@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=3, interval=[10, 30, 60]), timeout=JOB_TIMEOUT)
def run_orchestrator_task(
    task_id: str,
    question: str,
    repo: str,
    task_type: str = "faq",
    context: Optional[Dict[str, Any]] = None,
):
    """
    Execute orchestrator with retry logic (used by API for agent tasks)
    Configured with ttl=600, result_ttl=86400, failure_ttl=3600
    
    Uses LangGraph orchestrator for all tasks (Simple Mode removed as of 2025-12-18).
    See Issue #2651 for migration details.
    
    Args:
        task_id: Unique task identifier (also used as trace_id)
        question: FAQ question or topic
        repo: GitHub repository (owner/repo format)
        task_type: Task type for logging/metrics (default: "faq")
        context: Optional context dict from webhook containing PR info:
                 - resource_id: PR number from webhook event
                 - resource_type: "pull_request" for PR events
                 - url: PR URL
                 Issue: Phase B-B - Fix PR context passing
    
    Returns:
        dict: {"pr_url": str, "trace_id": str, "state": str}
    """
    global _canary_metrics, _rollout_tracker
    if _canary_metrics is None:
        try:
            from metrics import create_canary_metrics
            canary_metrics_enabled = getattr(settings, 'canary_metrics_enabled', True)
            _canary_metrics = create_canary_metrics(redis, enabled=canary_metrics_enabled)
            logger.info(f"Canary metrics initialized: enabled={canary_metrics_enabled}")
        except Exception as e:
            logger.warning(f"Failed to initialize canary metrics: {e}")
            _canary_metrics = None
    
    if _rollout_tracker is None:
        try:
            from rollout_tracker import create_rollout_tracker
            _rollout_tracker = create_rollout_tracker(redis, enabled=settings.rollout_tracker_enabled)
            logger.info(f"Rollout tracker initialized: enabled={settings.rollout_tracker_enabled}")
        except Exception as e:
            logger.warning(f"Failed to initialize rollout tracker: {e}")
            _rollout_tracker = None
    
    # Simple Mode removed - always use LangGraph (Issue #2651)
    # Circuit breaker check for observability (logs warning but doesn't block)
    if _rollout_tracker:
        try:
            if not _rollout_tracker.check_circuit_breaker():
                logger.warning(
                    "[Routing] Circuit breaker OPEN - proceeding with LangGraph (Simple Mode removed)",
                    extra={
                        "operation": "circuit_breaker",
                        "task_id": task_id,
                        "circuit_state": _rollout_tracker.get_circuit_breaker_state().state.value
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to check circuit breaker: {e}")
    
    if _canary_metrics:
        try:
            _canary_metrics.incr_counter("decisions.langgraph")
        except Exception as e:
            logger.warning(f"Failed to record routing decision metric: {e}")
    
    from langgraph_orchestrator import run_orchestrator
    logger.info(f"Using LangGraph orchestrator for task {task_id}")
    
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
                "task_type": task_type,
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
                message=f'Executing LangGraph orchestrator',
                level='info',
                data={'task_id': task_id, 'trace_id': task_id}
            )
        
        start_time_ns = time.monotonic_ns()
        execution_success = False
        
        # Issue: Phase B-B - Pass webhook context to orchestrator for PR info
        result = run_orchestrator(question, repo, task_id, context=context)
        pr_url = result.get("pr_url", "")
        state = result.get("ci_state", "unknown")
        trace_id = result.get("trace_id", task_id)
        # Issue: Fix false-positive alerts for review workflows
        # Previously: execution_success = bool(pr_url) marked review workflows as failures
        # because they don't create new PRs. Now we use the orchestrator's actual status.
        # A workflow is successful if:
        # 1. It completed without error (status == "success"), OR
        # 2. It was intentionally skipped (e.g., PR already merged/closed)
        orchestrator_status = result.get("status", "unknown")
        execution_success = orchestrator_status == "success"
        
        # Calculate elapsed_ms once for both _canary_metrics and _rollout_tracker (Issue #2286)
        elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000
        
        if _canary_metrics:
            try:
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
        
        if _rollout_tracker:
            try:
                # Issue #2737: Pass task_type for FAQ latency monitoring
                _rollout_tracker.record_langgraph_task(
                    trace_id=task_id,
                    success=execution_success,
                    latency_ms=elapsed_ms,
                    is_5xx_error=False,
                    task_type=task_type
                )
                logger.debug(f"Rollout tracker recorded: mode=langgraph, latency={elapsed_ms:.2f}ms, success={execution_success}, task_type={task_type}")
            except Exception as e:
                logger.warning(f"Failed to record rollout tracker metrics: {e}")
        
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
        
        if _canary_metrics:
            try:
                _canary_metrics.incr_counter("planner.error_5xx")
            except Exception as metric_error:
                logger.warning(f"Failed to record error metric: {metric_error}")
        
        if _rollout_tracker:
            try:
                # Issue #2737: Pass task_type for FAQ latency monitoring in error path
                _rollout_tracker.record_langgraph_task(
                    trace_id=task_id,
                    success=False,
                    latency_ms=None,
                    is_5xx_error=True,
                    task_type=task_type
                )
            except Exception as tracker_error:
                logger.warning(f"Failed to record rollout tracker error: {tracker_error}")
        
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


@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=3, interval=[10, 30, 60]), timeout=1800)
def run_meta_agent_task(task_id: str, goal_text: str, repo: str, tenant_id: str, context: dict = None):
    """
    Execute Meta Agent task using AutonomousExecutor for end-to-end autonomous execution.

    This is the entry point for #1822 integrated development tools flow:
    Webhook → TaskIntakeService → run_meta_agent_task → AutonomousExecutor

    The AutonomousExecutor handles:
    - Goal parsing and task planning
    - VM provisioning for isolated execution
    - VS Code IDE integration for code editing
    - Confidence scoring for implementation plans
    - Policy enforcement and safety limits

    Args:
        task_id: Unique task identifier (also used as trace_id)
        goal_text: Natural language goal description from webhook
        repo: GitHub repository (owner/repo format)
        tenant_id: Tenant UUID for multi-tenant isolation
        context: Optional context dict (branch, labels, priority, etc.)

    Returns:
        dict: {"task_id": str, "status": str, "execution_id": str, "pr_url": str, "trace_id": str}

    Feature Flags:
        - ENABLE_META_AGENT: Must be True to enable this path (default: False)
        - ENABLE_META_AGENT_VM: Controls VM provisioning (default: False)

    Note:
        timeout=1800 (30 minutes) to match the TTL in _enqueue_meta_agent_task,
        allowing sufficient time for autonomous execution including VM provisioning.
    """
    import asyncio

    job_id = task_id
    context = context or {}

    # Consolidated log data for consistent logging and Sentry breadcrumbs
    log_data = {
        "operation": "run_meta_agent_task",
        "task_id": task_id,
        "job_id": job_id,
        "trace_id": task_id,
        "tenant_id": tenant_id,
        "goal_text": goal_text[:100] if goal_text else "",
        "repo": repo
    }

    logger.info("[MetaAgent] Starting task", extra=log_data)

    if SENTRY_DSN:
        sentry_sdk.set_tag("trace_id", task_id)
        sentry_sdk.set_tag("task_id", task_id)
        sentry_sdk.set_tag("tenant_id", tenant_id)
        sentry_sdk.set_tag("operation", "meta_agent_task")
        sentry_sdk.add_breadcrumb(
            category='task',
            message='Starting Meta Agent task',
            level='info',
            data=log_data
        )

    start_time_ns = time.monotonic_ns()

    # Epic #2311: Runtime policy enforcement - check cost budget before execution
    if get_runtime_policy_enforcer is not None:
        try:
            enforcer = get_runtime_policy_enforcer()
            estimated_tokens = settings.meta_agent_estimated_tokens
            cost_check = enforcer.check_cost(
                task_id=task_id,
                estimated_tokens=estimated_tokens,
                model="qwen-plus",
                context={"tenant_id": tenant_id, "repo": repo, "goal_text": goal_text[:100]},
            )
            if not cost_check.allowed:
                action = cost_check.action.value if EnforcementAction else "block"
                if action == "block":
                    error_msg = f"Runtime policy blocked task: {cost_check.reason}"
                    logger.error(f"[MetaAgent] {error_msg}", extra=log_data)
                    return {
                        "task_id": task_id,
                        "status": "blocked",
                        "error": error_msg,
                        "trace_id": task_id,
                        "policy_action": action,
                    }
                elif action == "require_approval":
                    logger.warning(
                        f"[MetaAgent] Task requires approval due to cost policy: {cost_check.reason}",
                        extra=log_data
                    )
                elif action == "degrade_model":
                    context["suggested_model"] = cost_check.suggested_model
                    logger.info(
                        f"[MetaAgent] Cost budget exceeded, using degraded model: {cost_check.suggested_model}",
                        extra=log_data
                    )
        except Exception as e:
            error_msg = f"Runtime policy check failed (fail-closed): {e}"
            logger.error(f"[MetaAgent] {error_msg}", extra=log_data)
            return {
                "task_id": task_id,
                "status": "blocked",
                "error": error_msg,
                "trace_id": task_id,
                "policy_action": "block",
            }

    try:
        # Update Redis status to running
        redis_key = f"agent:task:{task_id}"
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": "running",
                "goal_text": goal_text[:500] if goal_text else "",
                "trace_id": task_id,
                "job_id": job_id,
                "task_type": "meta_agent",
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

        # Initialize AutonomousExecutor
        try:
            from meta_agent.autonomous_executor import AutonomousExecutor
            from meta_agent.vm_provisioner import VMProvider
        except ImportError as e:
            logger.error(f"[MetaAgent] Failed to import: {e}")
            raise ImportError(f"AutonomousExecutor not available: {e}")

        # Determine VM provider based on settings using dictionary mapping
        enable_vm = getattr(settings, 'enable_meta_agent_vm', False)
        vm_provider_mapping = {
            'local': VMProvider.LOCAL,
            'docker': VMProvider.DOCKER,
            'fly': VMProvider.FLY,
        }
        vm_provider = VMProvider.LOCAL
        if enable_vm:
            vm_provider_str = getattr(settings, 'meta_agent_vm_provider', 'local')
            vm_provider = vm_provider_mapping.get(vm_provider_str, VMProvider.LOCAL)

        logger.info(
            "[MetaAgent] Initializing executor",
            extra={
                "operation": "run_meta_agent_task",
                "task_id": task_id,
                "enable_vm": enable_vm,
                "vm_provider": vm_provider.value
            }
        )

        executor = AutonomousExecutor(vm_provider=vm_provider)

        # Build execution context
        execution_context = {
            "repo": repo,
            "tenant_id": tenant_id,
            "task_id": task_id,
            **context
        }

        # Issue #2321: Load session_data from Redis for command processing
        # Session ID can be passed in context, or defaults to task_id for backward compatibility
        session_id = context.get("session_id", task_id)
        session_key = f"dev_agent:session:{session_id}"
        commands_key = f"{session_key}:commands"
        session_data = None
        pending_commands = []

        try:
            session_data_raw = redis.get(session_key)
            if session_data_raw:
                session_data = json.loads(session_data_raw)

            pending_commands_raw = redis.lrange(commands_key, 0, -1)
            if pending_commands_raw:
                pending_commands = [
                    json.loads(cmd) for cmd in pending_commands_raw
                ]
                if session_data is None:
                    session_data = {}
                session_data["commands"] = pending_commands

            if session_data:
                executor.set_session_data(session_data)
                logger.info(
                    "[MetaAgent] Session data loaded for command processing",
                    extra={
                        "operation": "run_meta_agent_task",
                        "task_id": task_id,
                        "session_id": session_id,
                        "pending_commands_count": len(pending_commands)
                    }
                )
            else:
                logger.debug(
                    "[MetaAgent] No session data found, skipping command processing",
                    extra={
                        "operation": "run_meta_agent_task",
                        "task_id": task_id,
                        "session_id": session_id
                    }
                )
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(
                "[MetaAgent] Failed to load session data: %s",
                e,
                extra={
                    "operation": "run_meta_agent_task",
                    "task_id": task_id,
                    "session_id": session_id
                }
            )

        # Run the task asynchronously
        async def run_executor():
            return await executor.execute_goal(goal_text, context=execution_context)

        result = asyncio.run(run_executor())

        elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000

        # Extract result data
        execution_id = result.execution_id
        status = result.status.value
        pr_url = result.pr_url
        tasks_completed = result.tasks_completed
        tasks_failed = result.tasks_failed
        errors = result.errors

        logger.info(
            "[MetaAgent] Task completed",
            extra={
                "operation": "run_meta_agent_task",
                "task_id": task_id,
                "execution_id": execution_id,
                "status": status,
                "tasks_completed": tasks_completed,
                "tasks_failed": tasks_failed,
                "pr_url": pr_url,
                "elapsed_ms": elapsed_ms,
                "session_id": session_id,
                "pending_commands_count": len(pending_commands)
            }
        )

        # Issue #2322: Persist session_data back to Redis after command processing
        # Use LTRIM to remove only processed commands, preserving any new commands
        # that arrived between LRANGE and now (fixes race condition vs DELETE)
        commands_processed_count = len(pending_commands)
        if commands_processed_count > 0:
            try:
                redis.ltrim(commands_key, commands_processed_count, -1)
                logger.info(
                    "[MetaAgent] Processed commands cleared from queue",
                    extra={
                        "operation": "run_meta_agent_task",
                        "task_id": task_id,
                        "session_id": session_id,
                        "commands_processed": commands_processed_count
                    }
                )
            except Exception as cmd_error:
                logger.warning(
                    "[MetaAgent] Failed to clear processed commands: %s",
                    cmd_error,
                    extra={
                        "operation": "run_meta_agent_task",
                        "task_id": task_id,
                        "session_id": session_id
                    }
                )

        # Update session_data with execution results (without commands, they're in separate key)
        if session_data is not None:
            try:
                session_data.pop("commands", None)
                session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                session_data["execution_id"] = execution_id
                session_data["status"] = status
                session_data["last_commands_processed"] = commands_processed_count

                existing_ttl = redis.ttl(session_key)
                ttl_to_use = existing_ttl if existing_ttl > 0 else 86400

                redis.setex(session_key, ttl_to_use, json.dumps(session_data))
                logger.info(
                    "[MetaAgent] Session data persisted back to Redis",
                    extra={
                        "operation": "run_meta_agent_task",
                        "task_id": task_id,
                        "session_id": session_id,
                        "commands_processed": commands_processed_count
                    }
                )
            except Exception as session_error:
                logger.warning(
                    "[MetaAgent] Failed to persist session data: %s",
                    session_error,
                    extra={
                        "operation": "run_meta_agent_task",
                        "task_id": task_id,
                        "session_id": session_id
                    }
                )

        # Update Redis with result
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": status,
                "execution_id": execution_id,
                "pr_url": pr_url,
                "tasks_completed": str(tasks_completed),
                "tasks_failed": str(tasks_failed),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(redis_key, 3600)

        # Update DB with result
        try:
            upsert_task_done(
                task_id=task_id,
                trace_id=task_id,
                pr_url=pr_url,
                tenant_id=tenant_id
            )
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='agent_task',
                    message='Task completed and persisted to DB',
                    level='info',
                    data={
                        'task_id': task_id,
                        'trace_id': task_id,
                        'status': status,
                        'pr_url': pr_url
                    }
                )
        except Exception as db_error:
            logger.error(f"DB write failed for task {task_id} (done): {db_error}")

        return {
            "task_id": task_id,
            "execution_id": execution_id,
            "status": status,
            "pr_url": pr_url,
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "errors": errors,
            "trace_id": task_id,
            "elapsed_ms": elapsed_ms
        }

    except Exception as e:
        elapsed_ms = (time.monotonic_ns() - start_time_ns) / 1_000_000
        error_msg = str(e)

        logger.exception(
            "[MetaAgent] Task failed",
            extra={
                "operation": "run_meta_agent_task",
                "task_id": task_id,
                "error": error_msg,
                "elapsed_ms": elapsed_ms
            }
        )

        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)

        # Update Redis with error
        redis.hset(
            redis_key,
            mapping=sanitize_redis_mapping({
                "status": "error",
                "error": error_msg[:500],
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
        )
        redis.expire(redis_key, 3600)

        # Update DB with error
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


@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=2, interval=[10, 30]), timeout=JOB_TIMEOUT)
def run_auto_fix_task(task_data: dict):
    """
    Execute an auto-fix task from AI reviewer comments.

    This job processes auto-fix tasks that were enqueued by the webhook handler
    when CommentTriageAgent determines a comment should be auto-fixed.

    Issue #2252: Implement real auto-fix execution

    Args:
        task_data: Dictionary containing AutoFixTask data

    Returns:
        dict: {"success": bool, "task_id": str, "status": str, "message": str, ...}
    """
    import time
    from utils.auto_fix_executor import AutoFixExecutor, AutoFixTask

    start_time = time.time()

    task = AutoFixTask.from_dict(task_data)
    task_id = task.task_id

    logger.info(
        "[AutoFix] Starting auto-fix task",
        extra={
            "operation": "run_auto_fix_task",
            "task_id": task_id,
            "repo": task.repo,
            "pr_id": task.pr_id,
            "category": task.triage_result.get("category", "unknown"),
        }
    )

    if SENTRY_DSN:
        sentry_sdk.set_tag("trace_id", task_id)
        sentry_sdk.set_tag("task_id", task_id)
        sentry_sdk.set_tag("operation", "auto_fix_task")
        sentry_sdk.add_breadcrumb(
            category='task',
            message='Starting auto-fix task',
            level='info',
            data={
                'task_id': task_id,
                'repo': task.repo,
                'pr_id': task.pr_id,
            }
        )

    # Epic #2311: Runtime policy enforcement - check cost budget before auto-fix
    if get_runtime_policy_enforcer is not None:
        try:
            enforcer = get_runtime_policy_enforcer()
            estimated_tokens = settings.auto_fix_estimated_tokens
            cost_check = enforcer.check_cost(
                task_id=task_id,
                estimated_tokens=estimated_tokens,
                model="qwen-plus",
                context={"repo": task.repo, "pr_id": task.pr_id, "category": task.triage_result.get("category", "unknown")},
            )
            if not cost_check.allowed:
                action = cost_check.action.value if EnforcementAction else "block"
                if action == "block":
                    error_msg = f"Runtime policy blocked auto-fix: {cost_check.reason}"
                    logger.error(f"[AutoFix] {error_msg}")
                    return {
                        "success": False,
                        "task_id": task_id,
                        "status": "blocked",
                        "message": error_msg,
                        "pr_url": None,
                        "commit_sha": None,
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                        "safety_check_passed": False,
                        "canary_selected": False,
                        "policy_action": action,
                    }
        except Exception as e:
            error_msg = f"Runtime policy check failed (fail-closed): {e}"
            logger.error(f"[AutoFix] {error_msg}")
            return {
                "success": False,
                "task_id": task_id,
                "status": "blocked",
                "message": error_msg,
                "pr_url": None,
                "commit_sha": None,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "safety_check_passed": False,
                "canary_selected": False,
                "policy_action": "block",
            }

    try:
        executor = AutoFixExecutor(settings=settings, redis_url=redis_url)
        result = executor.execute(task)

        logger.info(
            "[AutoFix] Task completed",
            extra={
                "operation": "run_auto_fix_task_completed",
                "task_id": task_id,
                "success": result.success,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
            }
        )

        return {
            "success": result.success,
            "task_id": result.task_id,
            "status": result.status.value,
            "message": result.message,
            "pr_url": result.pr_url,
            "commit_sha": result.commit_sha,
            "execution_time_ms": result.execution_time_ms,
            "safety_check_passed": result.safety_check_passed,
            "canary_selected": result.canary_selected,
        }

    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        logger.error(
            "[AutoFix] Task failed with exception",
            extra={
                "operation": "run_auto_fix_task_error",
                "task_id": task_id,
                "error": error_msg,
                "execution_time_ms": execution_time_ms,
            },
            exc_info=True,
        )

        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)

        return {
            "success": False,
            "task_id": task_id,
            "status": "failed",
            "message": f"Exception: {error_msg}",
            "pr_url": None,
            "commit_sha": None,
            "execution_time_ms": execution_time_ms,
            "safety_check_passed": False,
            "canary_selected": False,
        }


vm_cleanup_thread = None
VM_CLEANUP_INTERVAL = settings.vm_cleanup_interval_seconds


@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=2, interval=[10, 30]), timeout=JOB_TIMEOUT)
def run_pr_updated_delayed_task(
    task_id: str,
    repo: str,
    pr_number: int,
    job_token: str,
    debounce_seconds: int,
    goal_text: str,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Execute a delayed PR_UPDATED review task after debounce window.

    This implements the non-blocking delayed scheduling pattern:
    1. Job is enqueued via enqueue_in() - no worker blocking
    2. Verify job token is still valid (no newer job scheduled)
    3. Check if new push happened within debounce window (true debounce)
    4. Read latest payload from Redis (may have been updated by subsequent events)
    5. Execute the orchestrator review task
    6. Mark as processed for throttle tracking

    Issue: Phase B-B - PR_UPDATED support with debounce/throttle
    CTO Decision: Prohibit time.sleep() inside worker - use enqueue_in() instead

    Args:
        task_id: Unique task identifier
        repo: Repository in owner/repo format
        pr_number: Pull request number
        job_token: Token to verify this job is still active
        debounce_seconds: Debounce window (used for checking if new push happened)
        goal_text: Review goal text
        context: Optional context dict with PR info

    Returns:
        dict: {"success": bool, "task_id": str, "reason": str, ...}
    """
    from utils.rate_limit import (
        verify_pr_updated_job_token,
        get_pr_updated_latest_payload,
        mark_pr_updated_processed,
        increment_reschedule_count,
    )

    start_time = time.time()

    logger.info(
        "[PRUpdatedDelayed] Starting delayed PR_UPDATED task",
        extra={
            "operation": "run_pr_updated_delayed_task",
            "task_id": task_id,
            "repo": repo,
            "pr_number": pr_number,
            "job_token": job_token,
            "debounce_seconds": debounce_seconds,
        }
    )

    if SENTRY_DSN:
        sentry_sdk.set_tag("trace_id", task_id)
        sentry_sdk.set_tag("task_id", task_id)
        sentry_sdk.set_tag("operation", "pr_updated_delayed_task")

    try:
        # Step 1: Verify job token is still valid (no newer job scheduled)
        # This is the primary debounce mechanism - if a new push happened,
        # a new job was scheduled and this token is now invalid
        if not verify_pr_updated_job_token(repo, pr_number, job_token):
            logger.info(
                "[PRUpdatedDelayed] Job token invalid - newer job exists, exiting",
                extra={
                    "operation": "pr_updated_token_invalid",
                    "task_id": task_id,
                    "repo": repo,
                    "pr_number": pr_number,
                    "job_token": job_token,
                }
            )
            return {
                "success": False,
                "task_id": task_id,
                "reason": "token_invalid",
                "message": "Newer job scheduled, this job is stale",
            }

        # Step 2: Get latest payload and check for recent pushes (true debounce)
        latest_payload = get_pr_updated_latest_payload(repo, pr_number)
        if latest_payload:
            logger.info(
                "[PRUpdatedDelayed] Retrieved latest payload",
                extra={
                    "operation": "pr_updated_latest_payload",
                    "task_id": task_id,
                    "repo": repo,
                    "pr_number": pr_number,
                    "event_count": latest_payload.get("event_count", 1),
                    "updated_at": latest_payload.get("updated_at"),
                }
            )

            # Check if a new push happened within the debounce window
            # If updated_at is more recent than (now - debounce_seconds), reschedule
            # This implements true debounce: "wait until quiet period is satisfied"
            updated_at = latest_payload.get("updated_at")
            if updated_at:
                # Clock skew protection: ensure time_since_update is non-negative
                time_since_update = max(0, time.time() - updated_at)
                if time_since_update < debounce_seconds:
                    # P2 Robustness: Check reschedule count limit before rescheduling
                    reschedule_count, exceeded_limit = increment_reschedule_count(
                        repo, pr_number, job_token
                    )
                    if exceeded_limit:
                        logger.warning(
                            "[PRUpdatedDelayed] Reschedule limit exceeded, proceeding with review",
                            extra={
                                "operation": "pr_updated_reschedule_limit_exceeded",
                                "task_id": task_id,
                                "repo": repo,
                                "pr_number": pr_number,
                                "reschedule_count": reschedule_count,
                            }
                        )
                        # Fall through to execute review instead of infinite rescheduling
                    else:
                        # Calculate remaining time until quiet period is satisfied
                        # Minimum 1 second to avoid tight loops
                        remaining_seconds = max(1, int(debounce_seconds - time_since_update) + 1)
                        
                        logger.info(
                            "[PRUpdatedDelayed] Recent push detected, rescheduling for remaining debounce",
                            extra={
                                "operation": "pr_updated_reschedule",
                                "task_id": task_id,
                                "repo": repo,
                                "pr_number": pr_number,
                                "time_since_update": time_since_update,
                                "debounce_seconds": debounce_seconds,
                                "remaining_seconds": remaining_seconds,
                                "reschedule_count": reschedule_count,
                            }
                        )
                        
                        # Self-reschedule: enqueue this same task to run after remaining time
                        # This ensures the last push is always processed after quiet period
                        try:
                            from datetime import timedelta
                            from redis import Redis
                            from rq import Queue
                            from rq.serializers import JSONSerializer
                            
                            redis_url = getattr(settings, 'redis_url', None)
                            if redis_url:
                                redis_client = Redis.from_url(redis_url, decode_responses=False)
                                queue_name = getattr(settings, 'rq_queue_name', None) or 'orchestrator'
                                queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())
                                
                                # Use same job_id to replace/deduplicate
                                # RQ will handle job replacement when using same job_id
                                new_job = queue.enqueue_in(
                                    timedelta(seconds=remaining_seconds),
                                    run_pr_updated_delayed_task,
                                    task_id,
                                    repo,
                                    pr_number,
                                    job_token,
                                    debounce_seconds,
                                    goal_text,
                                    context,
                                    job_id=f"{task_id}-reschedule",  # New job_id to avoid conflict
                                    ttl=remaining_seconds + 600,
                                    job_timeout=settings.rq_job_timeout,
                                    result_ttl=86400,
                                    failure_ttl=3600,
                                )
                                
                                logger.info(
                                    "[PRUpdatedDelayed] Successfully rescheduled task",
                                    extra={
                                        "operation": "pr_updated_rescheduled",
                                        "task_id": task_id,
                                        "new_job_id": new_job.id,
                                        "repo": repo,
                                        "pr_number": pr_number,
                                        "remaining_seconds": remaining_seconds,
                                        "reschedule_count": reschedule_count,
                                    }
                                )
                                
                                return {
                                    "success": False,
                                    "task_id": task_id,
                                    "reason": "rescheduled",
                                    "message": f"Rescheduled for {remaining_seconds}s (quiet period not satisfied)",
                                    "new_job_id": new_job.id,
                                    "reschedule_count": reschedule_count,
                                }
                            else:
                                logger.error(
                                    "[PRUpdatedDelayed] Cannot reschedule - Redis URL not configured",
                                    extra={
                                        "operation": "pr_updated_reschedule_failed",
                                        "task_id": task_id,
                                        "repo": repo,
                                        "pr_number": pr_number,
                                    }
                                )
                        except Exception as reschedule_error:
                            logger.error(
                                "[PRUpdatedDelayed] Failed to reschedule task, proceeding with review",
                                extra={
                                    "operation": "pr_updated_reschedule_error",
                                    "task_id": task_id,
                                    "repo": repo,
                                    "pr_number": pr_number,
                                    "error": str(reschedule_error),
                                },
                                exc_info=True
                            )
                            # Fall through to execute review if reschedule fails
                            # This is fail-open: better to review than to lose the task

        # Step 3: Execute orchestrator review
        logger.info(
            "[PRUpdatedDelayed] Executing orchestrator review",
            extra={
                "operation": "pr_updated_execute_review",
                "task_id": task_id,
                "repo": repo,
                "pr_number": pr_number,
            }
        )

        review_context = context or {}
        review_context["pr_updated_event"] = True
        review_context["pr_updated_event_count"] = latest_payload.get("event_count", 1) if latest_payload else 1

        from langgraph_orchestrator import run_orchestrator
        result = run_orchestrator(
            question=goal_text,
            repo=repo,
            trace_id=task_id,
            context=review_context,
        )

        throttle_seconds = getattr(settings, 'pr_updated_throttle_seconds', 600)
        mark_pr_updated_processed(repo, pr_number, throttle_seconds)

        execution_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "[PRUpdatedDelayed] Task completed successfully",
            extra={
                "operation": "pr_updated_task_complete",
                "task_id": task_id,
                "repo": repo,
                "pr_number": pr_number,
                "execution_time_ms": execution_time_ms,
            }
        )

        return {
            "success": True,
            "task_id": task_id,
            "reason": "completed",
            "pr_url": result.get("pr_url") if isinstance(result, dict) else None,
            "execution_time_ms": execution_time_ms,
        }

    except Exception as e:
        error_msg = str(e)
        execution_time_ms = int((time.time() - start_time) * 1000)

        logger.error(
            "[PRUpdatedDelayed] Task failed",
            extra={
                "operation": "pr_updated_task_failed",
                "task_id": task_id,
                "repo": repo,
                "pr_number": pr_number,
                "error": error_msg,
                "execution_time_ms": execution_time_ms,
            },
            exc_info=True
        )

        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)

        raise


def run_vm_cleanup_scheduler():
    """
    Background thread to periodically clean up stale VM entries.
    
    Runs cleanup_stale_vms from DistributedVMLockManager at configured interval.
    Only runs if USE_DISTRIBUTED_VM_LOCKING is enabled and interval > 0.
    
    Configuration (via settings.py):
    - settings.vm_cleanup_interval_seconds: Cleanup interval (default: 300 = 5 minutes)
    - settings.use_distributed_vm_locking: Must be True to enable cleanup
    """
    if not settings.use_distributed_vm_locking:
        logger.info(
            "VM cleanup scheduler disabled (USE_DISTRIBUTED_VM_LOCKING=false)",
            extra={"operation": "vm_cleanup"}
        )
        return
    
    if VM_CLEANUP_INTERVAL <= 0:
        logger.info(
            "VM cleanup scheduler disabled (VM_CLEANUP_INTERVAL_SECONDS=0)",
            extra={"operation": "vm_cleanup"}
        )
        return
    
    logger.info(
        f"VM cleanup scheduler started (interval={VM_CLEANUP_INTERVAL}s)",
        extra={"operation": "vm_cleanup", "interval": VM_CLEANUP_INTERVAL}
    )
    
    lock_manager = None
    
    while not shutdown_event.is_set():
        try:
            if lock_manager is None:
                try:
                    from meta_agent.distributed_vm_lock import DistributedVMLockManager
                    import redis as redis_lib
                    
                    async_redis = redis_lib.asyncio.from_url(
                        redis_url,
                        decode_responses=False,
                        socket_connect_timeout=10,
                    )
                    lock_manager = DistributedVMLockManager(
                        redis_client=async_redis,
                        max_concurrent_vms=getattr(settings, 'max_concurrent_vms', 10),
                        lock_ttl_seconds=settings.vm_lock_ttl_seconds,
                        registry_ttl_buffer=settings.vm_registry_ttl_buffer,
                    )
                    logger.info(
                        "VM cleanup lock manager initialized",
                        extra={"operation": "vm_cleanup"}
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize VM cleanup lock manager: {e}",
                        extra={"operation": "vm_cleanup", "error": str(e)}
                    )
                    shutdown_event.wait(VM_CLEANUP_INTERVAL)
                    continue
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            cleaned = loop.run_until_complete(lock_manager.cleanup_stale_vms())
            
            if cleaned > 0:
                logger.info(
                    f"VM cleanup completed: {cleaned} stale entries removed",
                    extra={"operation": "vm_cleanup", "cleaned": cleaned}
                )
            else:
                logger.debug(
                    "VM cleanup completed: no stale entries",
                    extra={"operation": "vm_cleanup"}
                )
            
            shutdown_event.wait(VM_CLEANUP_INTERVAL)
            
        except RedisConnectionError as e:
            logger.error(
                f"VM cleanup Redis connection error: {e}",
                extra={"operation": "vm_cleanup"}
            )
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            shutdown_event.wait(60)
        except Exception as e:
            logger.exception(
                f"VM cleanup failed: {e}",
                extra={"operation": "vm_cleanup"}
            )
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            shutdown_event.wait(60)
    
    logger.info("VM cleanup scheduler stopped", extra={"operation": "vm_cleanup"})


def run_memory_consolidation_scheduler():
    """
    Background thread to run memory consolidation job.

    EPIC G-2: Memory Consolidation Agent
    Transfers important short-term memories to long-term Knowledge Base.

    Configuration (via environment variables):
    - ENABLE_MEMORY_CONSOLIDATION: Must be 'true' to enable (default: false)
    - MEMORY_CONSOLIDATION_DRY_RUN: Safe mode, logs only (default: true)
    - MEMORY_CONSOLIDATION_THRESHOLD: Importance threshold (default: 0.5)
    - MEMORY_CONSOLIDATION_INTERVAL_HOURS: Run interval (default: 6)
    """
    try:
        from memory.memory_consolidation import get_consolidation_job

        job = get_consolidation_job()
        if job is None:
            logger.info(
                "Memory consolidation scheduler disabled (ENABLE_MEMORY_CONSOLIDATION=false)",
                extra={"operation": "memory_consolidation"}
            )
            return

        # Start the scheduler - it will run in its own thread internally
        job.start_scheduler()
        logger.info(
            f"Memory consolidation scheduler started (interval={job.interval_hours}h, "
            f"threshold={job.importance_threshold}, dry_run={job.dry_run})",
            extra={
                "operation": "memory_consolidation",
                "interval_hours": job.interval_hours,
                "threshold": job.importance_threshold,
                "dry_run": job.dry_run,
            }
        )

        # Wait for shutdown signal
        while not shutdown_event.is_set():
            shutdown_event.wait(60)

        # Stop the scheduler on shutdown
        job.stop_scheduler()
        logger.info(
            "Memory consolidation scheduler stopped",
            extra={"operation": "memory_consolidation"}
        )

    except ImportError as e:
        logger.debug(
            f"Memory consolidation not available: {e}",
            extra={"operation": "memory_consolidation"}
        )
    except Exception as e:
        logger.warning(
            f"Memory consolidation scheduler failed to start: {e}",
            extra={"operation": "memory_consolidation", "error": str(e)}
        )
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)


def run_router_metrics_alert_scheduler():
    """
    Background thread to run router metrics alert evaluator.

    EPIC C: Flow Controller v3 - Issue #3499
    Scheduled Alert Evaluator for RouterMetrics.

    Configuration (via environment variables):
    - ROUTER_METRICS_ALERTING_ENABLED: Must be 'true' to enable (default: false)
    - ROUTER_ALERT_INTERVAL_MINUTES: Evaluation interval (default: 5)
    - ROUTER_ALERT_COOLDOWN_MINUTES: Cooldown between same alerts (default: 15)
    - SLACK_WEBHOOK_URL: Slack webhook for notifications
    - PAGERDUTY_ROUTING_KEY: PagerDuty routing key for critical alerts
    """
    try:
        from governance.router_metrics_alerter import get_router_metrics_alert_evaluator

        evaluator = get_router_metrics_alert_evaluator()
        if evaluator is None:
            logger.info(
                "Router metrics alert scheduler disabled (ROUTER_METRICS_ALERTING_ENABLED=false)",
                extra={"operation": "router_metrics_alerting"}
            )
            return

        # Start the scheduler - it will run in its own thread internally
        evaluator.start_scheduler()
        logger.info(
            f"Router metrics alert scheduler started (interval={evaluator.interval_minutes}m, "
            f"cooldown={evaluator.cooldown_minutes}m)",
            extra={
                "operation": "router_metrics_alerting",
                "interval_minutes": evaluator.interval_minutes,
                "cooldown_minutes": evaluator.cooldown_minutes,
            }
        )

        # Wait for shutdown signal
        while not shutdown_event.is_set():
            shutdown_event.wait(60)

        # Stop the scheduler on shutdown
        evaluator.stop_scheduler()
        logger.info(
            "Router metrics alert scheduler stopped",
            extra={"operation": "router_metrics_alerting"}
        )

    except ImportError as e:
        logger.debug(
            f"Router metrics alerting not available: {e}",
            extra={"operation": "router_metrics_alerting"}
        )
    except Exception as e:
        logger.warning(
            f"Router metrics alert scheduler failed to start: {e}",
            extra={"operation": "router_metrics_alerting", "error": str(e)}
        )
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)


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
    
    if settings.worker_drain_mode:
        # Sleep before exit to prevent rapid restart loops on Render
        # This reduces container orchestrator churn and avoids health check failures
        drain_sleep_seconds = 60
        logger.info(
            "Drain mode active, worker exiting without consuming jobs",
            extra={
                "operation": "drain_mode",
                "drain_mode": True,
                "drain_sleep_seconds": drain_sleep_seconds,
                "heartbeat_id": HEARTBEAT_ID,
                "rq_worker_name": RQ_WORKER_NAME,
                "queue": RQ_QUEUE_NAME,
            }
        )
        time.sleep(drain_sleep_seconds)
        sys.exit(0)
    
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
                "use_llm_planner": getattr(settings, 'use_llm_planner', False),
                "canary_metrics_enabled": getattr(settings, 'canary_metrics_enabled', True),
                "canary_alerting_enabled": getattr(settings, 'canary_alerting_enabled', True),
                "sentry_dsn_configured": bool(SENTRY_DSN),
                "max_jobs": MAX_JOBS
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
            "ttl": HEARTBEAT_TTL,
            "interval": HEARTBEAT_INTERVAL
        }
    )
    
    vm_cleanup_thread = threading.Thread(target=run_vm_cleanup_scheduler, daemon=False, name="VMCleanupThread")
    vm_cleanup_thread.start()
    logger.info(
        f"VM cleanup scheduler started",
        extra={
            "operation": "startup",
            "heartbeat_id": HEARTBEAT_ID,
            "rq_worker_name": RQ_WORKER_NAME,
            "interval": VM_CLEANUP_INTERVAL,
            "enabled": settings.use_distributed_vm_locking
        }
    )
    
    # EPIC G-2: Memory Consolidation Scheduler
    memory_consolidation_thread = threading.Thread(
        target=run_memory_consolidation_scheduler,
        daemon=False,
        name="MemoryConsolidationThread"
    )
    memory_consolidation_thread.start()
    logger.info(
        "Memory consolidation scheduler thread started",
        extra={
            "operation": "startup",
            "heartbeat_id": HEARTBEAT_ID,
            "rq_worker_name": RQ_WORKER_NAME,
        }
    )

    # EPIC C: Router Metrics Alert Scheduler (Issue #3499)
    router_metrics_alert_thread = threading.Thread(
        target=run_router_metrics_alert_scheduler,
        daemon=False,
        name="RouterMetricsAlertThread"
    )
    router_metrics_alert_thread.start()
    logger.info(
        "Router metrics alert scheduler thread started",
        extra={
            "operation": "startup",
            "heartbeat_id": HEARTBEAT_ID,
            "rq_worker_name": RQ_WORKER_NAME,
        }
    )
    
    readonly_sleep_seconds = settings.redis_readonly_sleep_seconds
    readonly_max_retries = settings.redis_readonly_max_retries
    consecutive_readonly_count = 0
    
    while True:
        max_retries = 1
        should_exit = False
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
                        "serializer": "JSONSerializer",
                        "max_jobs": MAX_JOBS,
                        "with_scheduler": True
                    }
                )
                # max_jobs: Worker exits after processing this many jobs
                # Previously relied on container orchestrator (Render) to restart the worker,
                # but this was unreliable. Now uses os.execl for self-healing restart.
                # This clears accumulated memory from LangGraph MemorySaver checkpoints
                # with_scheduler: Enable RQ scheduler for enqueue_in() delayed jobs
                # Required for PR_UPDATED debounce mechanism (Phase B-B)
                worker.work(max_jobs=MAX_JOBS, with_scheduler=True)
                consecutive_readonly_count = 0
                
                # Self-healing restart: Use os.execl to replace current process
                # instead of exiting and relying on Render to restart (which is flaky)
                # os.execl replaces the process image, completely clearing memory
                # while keeping the same PID (Render won't see it as a crash)
                if MAX_JOBS and MAX_JOBS > 0:
                    logger.info(
                        f"Worker finished {MAX_JOBS} jobs. Performing self-healing restart to clear memory...",
                        extra={
                            "operation": "self_healing_restart",
                            "heartbeat_id": HEARTBEAT_ID,
                            "rq_worker_name": RQ_WORKER_NAME,
                            "max_jobs": MAX_JOBS
                        }
                    )
                    
                    # Clean up threads and Redis state before restart
                    # This is important because os.execl doesn't trigger atexit handlers
                    # cleanup_heartbeat() already handles heartbeat_thread.join() with timeout
                    cleanup_heartbeat()
                    
                    # Wait for VM cleanup thread to stop (not handled by cleanup_heartbeat)
                    if vm_cleanup_thread and vm_cleanup_thread.is_alive():
                        vm_cleanup_thread.join(timeout=5)
                        if vm_cleanup_thread.is_alive():
                            logger.warning(
                                "VM cleanup thread did not stop within timeout before restart",
                                extra={"operation": "self_healing_restart", "heartbeat_id": HEARTBEAT_ID}
                            )
                    
                    # Wait for memory consolidation thread to stop
                    if memory_consolidation_thread and memory_consolidation_thread.is_alive():
                        memory_consolidation_thread.join(timeout=5)
                        if memory_consolidation_thread.is_alive():
                            logger.warning(
                                "Memory consolidation thread did not stop within timeout before restart",
                                extra={"operation": "self_healing_restart", "heartbeat_id": HEARTBEAT_ID}
                            )

                    # Wait for router metrics alert thread to stop (EPIC C - Issue #3499)
                    if router_metrics_alert_thread and router_metrics_alert_thread.is_alive():
                        router_metrics_alert_thread.join(timeout=5)
                        if router_metrics_alert_thread.is_alive():
                            logger.warning(
                                "Router metrics alert thread did not stop within timeout before restart",
                                extra={"operation": "self_healing_restart", "heartbeat_id": HEARTBEAT_ID}
                            )
                    
                    # Perform in-place restart using os.execl
                    # This replaces the current process with a fresh Python process
                    # Wrapped in try/except for graceful fallback if os.execl fails
                    #
                    # IMPORTANT: We use `-m redis_queue.worker` instead of sys.argv because:
                    # When started with `python -m redis_queue.worker`, sys.argv[0] becomes
                    # the path to the script file (e.g., /path/to/worker.py), not `-m ...`.
                    # Using sys.argv would run the worker as a script, breaking module imports.
                    # Using `-m` ensures Python sets up the module path correctly.
                    try:
                        python = sys.executable
                        # Use -m to run as module, ensuring proper import path setup
                        os.execl(python, python, "-m", "redis_queue.worker")
                        # Note: Code after os.execl never executes (process is replaced)
                    except OSError as e:
                        logger.critical(
                            "Self-healing restart with os.execl failed. Falling back to normal exit.",
                            extra={
                                "operation": "self_healing_restart_failed",
                                "error": str(e),
                                "heartbeat_id": HEARTBEAT_ID,
                                "rq_worker_name": RQ_WORKER_NAME
                            },
                            exc_info=True
                        )
                        # Fall through to normal exit, allowing Render to restart
                
                should_exit = True
                break
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
                should_exit = True
                break
            except ReadOnlyError as e:
                consecutive_readonly_count += 1
                if consecutive_readonly_count >= readonly_max_retries:
                    logger.error(
                        f"Redis ReadOnlyError exceeded max retries ({readonly_max_retries}). Exiting to trigger restart.",
                        extra={
                            "operation": "redis_readonly_exceeded",
                            "heartbeat_id": HEARTBEAT_ID,
                            "rq_worker_name": RQ_WORKER_NAME,
                            "consecutive_readonly_count": consecutive_readonly_count,
                            "max_retries": readonly_max_retries,
                            "total_sleep_seconds": consecutive_readonly_count * readonly_sleep_seconds,
                            "error": str(e)
                        }
                    )
                    if SENTRY_DSN:
                        sentry_sdk.capture_message(
                            f"Redis ReadOnlyError exceeded max retries ({readonly_max_retries})",
                            level="error"
                        )
                    should_exit = True
                    break
                logger.warning(
                    f"Redis is in Read-Only mode (Maintenance/Upgrade). Sleeping for {readonly_sleep_seconds}s... ({consecutive_readonly_count}/{readonly_max_retries})",
                    extra={
                        "operation": "redis_readonly",
                        "heartbeat_id": HEARTBEAT_ID,
                        "rq_worker_name": RQ_WORKER_NAME,
                        "consecutive_readonly_count": consecutive_readonly_count,
                        "max_retries": readonly_max_retries,
                        "sleep_seconds": readonly_sleep_seconds,
                        "error": str(e)
                    }
                )
                time.sleep(readonly_sleep_seconds)
                break
            except Exception as e:
                logger.exception(
                    f"Unexpected worker error",
                    extra={"operation": "shutdown", "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME}
                )
                if SENTRY_DSN:
                    sentry_sdk.capture_exception(e)
                raise
        
        if should_exit:
            break
    
    cleanup_heartbeat()
    logger.info(
        f"Worker shutdown complete",
        extra={"operation": "shutdown", "heartbeat_id": HEARTBEAT_ID, "rq_worker_name": RQ_WORKER_NAME}
    )
