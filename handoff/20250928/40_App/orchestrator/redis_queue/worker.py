#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks with graceful shutdown and heartbeat monitoring

Environment Variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- RQ_QUEUE_NAME: Queue name to process (default: orchestrator)
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
- ttl=600 (job timeout)
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

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

SENTRY_DSN = os.getenv("SENTRY_DSN")
APP_VERSION = os.getenv("APP_VERSION", "8.0.0")

if SENTRY_DSN and SENTRY_DSN.strip():
    try:
        import sentry_sdk
        from sentry_sdk.integrations.rq import RqIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "production"),
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "orchestrator")

redis_retry = RedisRetry(ExponentialBackoff(base=1, cap=10), retries=3)
redis = Redis.from_url(
    redis_url, 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=30,
    retry=redis_retry,
    retry_on_timeout=True
)
redis_client_rq = Redis.from_url(
    redis_url, 
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=30,
    retry=redis_retry,
    retry_on_timeout=True
)
q = Queue(RQ_QUEUE_NAME, connection=redis_client_rq, serializer=JSONSerializer())

WORKER_ID = os.getenv("RENDER_INSTANCE_ID", os.getenv("HOSTNAME", "worker-local"))
shutdown_event = threading.Event()
shutting_down = False
cleanup_started = False
heartbeat_thread = None

def update_worker_heartbeat():
    """
    Background thread to update worker heartbeat in Redis with TTL.
    Runs until shutdown_event is set.
    Updates state to 'shutting_down' when shutdown is initiated.
    """
    logger.info(f"Heartbeat thread started", extra={"operation": "heartbeat", "worker_id": WORKER_ID})
    
    while not shutdown_event.is_set():
        try:
            if redis:
                heartbeat_key = f"worker:heartbeat:{WORKER_ID}"
                state = "shutting_down" if shutting_down else "running"
                redis.setex(
                    heartbeat_key,
                    120,
                    json.dumps({
                        "state": state,
                        "last_heartbeat": datetime.now(timezone.utc).isoformat() + "Z",
                        "worker_id": WORKER_ID,
                        "timestamp": int(time.time())
                    })
                )
                logger.debug(f"Heartbeat updated", extra={"operation": "heartbeat", "worker_id": WORKER_ID, "state": state})
            
            shutdown_event.wait(30)
        except RedisConnectionError as e:
            logger.error(f"Heartbeat Redis connection error: {e}", extra={"operation": "heartbeat", "worker_id": WORKER_ID})
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            shutdown_event.wait(30)
        except Exception as e:
            logger.exception(f"Heartbeat update failed", extra={"operation": "heartbeat", "worker_id": WORKER_ID})
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            shutdown_event.wait(30)
    
    logger.info(f"Heartbeat thread stopped", extra={"operation": "heartbeat", "worker_id": WORKER_ID})

def cleanup_heartbeat():
    """
    Cleanup function to gracefully shutdown heartbeat thread.
    Called on worker shutdown or exit.
    Sets shutting_down flag, updates heartbeat state, and cleans up Redis key.
    Idempotent: safe to call multiple times.
    """
    global heartbeat_thread, shutting_down, cleanup_started
    
    if cleanup_started:
        logger.debug(f"Cleanup already in progress, skipping duplicate call", extra={"operation": "shutdown", "worker_id": WORKER_ID})
        return
    
    cleanup_started = True
    logger.info(f"Initiating graceful shutdown", extra={"operation": "shutdown", "worker_id": WORKER_ID})
    shutting_down = True
    
    try:
        heartbeat_key = f"worker:heartbeat:{WORKER_ID}"
        redis.setex(
            heartbeat_key,
            120,
            json.dumps({
                "state": "shutting_down",
                "last_heartbeat": datetime.now(timezone.utc).isoformat() + "Z",
                "worker_id": WORKER_ID,
                "timestamp": int(time.time())
            })
        )
        logger.info(f"Updated heartbeat state to shutting_down", extra={"operation": "shutdown", "worker_id": WORKER_ID})
    except Exception as e:
        logger.exception(f"Failed to update heartbeat state during shutdown", extra={"operation": "shutdown", "worker_id": WORKER_ID})
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
    
    shutdown_event.set()
    
    if heartbeat_thread and heartbeat_thread.is_alive():
        heartbeat_thread.join(timeout=5)
        if heartbeat_thread.is_alive():
            logger.warning(f"Heartbeat thread did not stop within timeout", extra={"operation": "shutdown", "worker_id": WORKER_ID})
        else:
            logger.info(f"Heartbeat thread stopped successfully", extra={"operation": "shutdown", "worker_id": WORKER_ID})
    
    try:
        if redis:
            heartbeat_key = f"worker:heartbeat:{WORKER_ID}"
            redis.delete(heartbeat_key)
            logger.info(f"Cleaned up heartbeat key", extra={"operation": "shutdown", "worker_id": WORKER_ID, "key": heartbeat_key})
    except Exception as e:
        logger.exception(f"Failed to cleanup heartbeat key", extra={"operation": "shutdown", "worker_id": WORKER_ID})
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)

def signal_handler(signum, frame):
    """Handle termination signals gracefully (SIGTERM from container orchestrator, SIGINT from Ctrl+C)"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown", extra={"operation": "signal_handler", "signal": signum, "worker_id": WORKER_ID})
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

@job(RQ_QUEUE_NAME, connection=redis_client_rq, retry=Retry(max=3, interval=[10, 30, 60]))
def run_orchestrator_task(task_id: str, question: str, repo: str):
    """
    Execute orchestrator with retry logic (used by API for agent tasks)
    Configured with ttl=600, result_ttl=86400, failure_ttl=3600
    
    Args:
        task_id: Unique task identifier (also used as trace_id)
        question: FAQ question or topic
        repo: GitHub repository (owner/repo format)
    
    Returns:
        dict: {"pr_url": str, "trace_id": str, "state": str}
    """
    from graph import execute
    
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
            mapping={
                "status": "running",
                "question": question,
                "trace_id": task_id,
                "job_id": job_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
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
                data={'task_id': task_id, 'trace_id': task_id}
            )
        
        pr_url, state, trace_id = execute(question, repo, trace_id=task_id)
        
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='redis',
                message=f'Updating task status to done',
                level='info',
                data={'redis_key': redis_key, 'task_id': task_id, 'pr_url': pr_url}
            )
        
        redis.hset(
            redis_key,
            mapping={
                "status": "done",
                "question": question,
                "trace_id": trace_id,
                "job_id": job_id,
                "pr_url": pr_url,
                "state": state,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
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
            mapping={
                "status": "error",
                "question": question,
                "trace_id": task_id,
                "job_id": job_id,
                "error_code": "ORCHESTRATOR_FAILED",
                "error_message": error_msg,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
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

if __name__ == "__main__":
    from rq import Worker
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_heartbeat)
    
    logger.info(f"Starting RQ worker", extra={"operation": "startup", "worker_id": WORKER_ID, "queue": RQ_QUEUE_NAME, "redis_url": redis_url})
    
    heartbeat_thread = threading.Thread(target=update_worker_heartbeat, daemon=False, name="HeartbeatThread")
    heartbeat_thread.start()
    logger.info(f"Heartbeat monitoring enabled", extra={"operation": "startup", "worker_id": WORKER_ID, "ttl": 120, "interval": 30})
    
    try:
        worker = Worker(
            [q],
            connection=redis_client_rq,
            name=WORKER_ID,
            default_worker_ttl=600,
            default_result_ttl=86400
        )
        logger.info(f"Worker configuration complete", extra={"operation": "startup", "worker_id": WORKER_ID, "worker_ttl": 600, "result_ttl": 86400})
        worker.work()
    except KeyboardInterrupt:
        logger.info(f"KeyboardInterrupt received", extra={"operation": "shutdown", "worker_id": WORKER_ID})
    except Exception as e:
        logger.exception(f"Unexpected worker error", extra={"operation": "shutdown", "worker_id": WORKER_ID})
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise
    finally:
        cleanup_heartbeat()
        logger.info(f"Worker shutdown complete", extra={"operation": "shutdown", "worker_id": WORKER_ID})
