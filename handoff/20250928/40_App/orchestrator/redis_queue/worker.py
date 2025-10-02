#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks with health check, lifecycle logging, and fallback support
Usage: rq worker orchestrator --url redis://localhost:6379/0
"""

import os
import sys
import time
import json
import threading
from datetime import datetime
from typing import Optional, List
from redis import Redis, ConnectionError as RedisConnectionError
from rq import Queue
from rq.decorators import job
from rq import Retry
from rq.worker import Worker
from .logger_util import log_structured

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("ENVIRONMENT", "production"),
        traces_sample_rate=1.0,
    )
    log_structured("INFO", "Sentry initialized", "startup", sentry_dsn=SENTRY_DSN[:20] + "...")
else:
    log_structured("INFO", "Sentry not configured", "startup")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
WORKER_ID = os.getenv("RENDER_INSTANCE_ID", os.getenv("HOSTNAME", "worker-local"))

try:
    redis = Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
    redis.ping()
    q = Queue("orchestrator", connection=redis)
    log_structured("INFO", f"Redis connected successfully", "startup", worker_id=WORKER_ID, redis_url=redis_url[:20] + "...")
except (RedisConnectionError, Exception) as e:
    log_structured("WARNING", f"Redis unavailable at module import", "startup", error=str(e), worker_id=WORKER_ID, demo_mode=DEMO_MODE)
    redis = None
    q = None

def update_worker_heartbeat():
    """Background thread to update worker heartbeat in Redis"""
    while True:
        try:
            if redis:
                heartbeat_key = f"worker:health:{WORKER_ID}"
                redis.setex(
                    heartbeat_key,
                    60,
                    json.dumps({
                        "last_heartbeat": datetime.utcnow().isoformat() + "Z",
                        "worker_id": WORKER_ID,
                        "status": "healthy",
                        "demo_mode": DEMO_MODE
                    })
                )
            time.sleep(30)
        except Exception as e:
            log_structured("ERROR", "Heartbeat update failed", "heartbeat", error=str(e), worker_id=WORKER_ID)
            if SENTRY_DSN:
                sentry_sdk.add_breadcrumb(
                    category='worker',
                    message=f'Heartbeat failed: {str(e)}',
                    level='error'
                )
            time.sleep(30)

def check_worker_health() -> dict:
    """Check worker health by pinging Redis"""
    try:
        if redis:
            redis.ping()
            return {
                "status": "healthy",
                "redis": "connected",
                "worker_id": WORKER_ID,
                "demo_mode": DEMO_MODE,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        elif DEMO_MODE:
            return {
                "status": "healthy",
                "redis": "disconnected",
                "worker_id": WORKER_ID,
                "demo_mode": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            return {
                "status": "unhealthy",
                "redis": "disconnected",
                "worker_id": WORKER_ID,
                "demo_mode": False,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    except Exception as e:
        log_structured("ERROR", "Health check failed", "health_check", error=str(e), worker_id=WORKER_ID)
        return {
            "status": "unhealthy",
            "redis": f"error: {str(e)}",
            "worker_id": WORKER_ID,
            "demo_mode": DEMO_MODE,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

def run_step(step: str):
    """Demo function for testing worker with steps"""
    log_structured("INFO", f"Running step: {step}", "process", step=step)
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
    start_time = time.time()
    
    try:
        if not redis and not DEMO_MODE:
            raise RedisConnectionError("Redis not available")
        
        if redis and idempotency_key:
            key = f"orchestrator:job:{idempotency_key}"
            if redis.exists(key):
                result = redis.get(key)
                if result:
                    existing_job_ids = result.split(',')
                    elapsed_ms = (time.time() - start_time) * 1000
                    log_structured("INFO", f"Job with idempotency key already exists", "enqueue", 
                                 idempotency_key=idempotency_key, job_ids=existing_job_ids, elapsed_ms=elapsed_ms)
                    return existing_job_ids
            
            jobs = [q.enqueue(run_step, s) for s in steps]
            job_ids = [j.id for j in jobs]
            
            redis.setex(key, 3600, ','.join(job_ids))
            elapsed_ms = (time.time() - start_time) * 1000
            log_structured("INFO", f"Created idempotent job", "enqueue", 
                         idempotency_key=idempotency_key, job_ids=job_ids, elapsed_ms=elapsed_ms)
            return job_ids
        elif redis:
            jobs = [q.enqueue(run_step, s) for s in steps]
            job_ids = [j.id for j in jobs]
            elapsed_ms = (time.time() - start_time) * 1000
            log_structured("INFO", f"Enqueued {len(jobs)} jobs", "enqueue", job_ids=job_ids, elapsed_ms=elapsed_ms)
            return job_ids
        else:
            job_ids = [f"demo-job-{i}" for i in range(len(steps))]
            elapsed_ms = (time.time() - start_time) * 1000
            log_structured("INFO", f"DEMO_MODE: Mocked job enqueue", "enqueue", job_ids=job_ids, elapsed_ms=elapsed_ms, demo_mode=True)
            return job_ids
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        log_structured("ERROR", f"Failed to enqueue jobs", "enqueue", error=str(e), elapsed_ms=elapsed_ms)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        
        if DEMO_MODE:
            job_ids = [f"demo-job-{i}" for i in range(len(steps))]
            log_structured("WARNING", f"DEMO_MODE: Fallback to mock jobs", "enqueue", job_ids=job_ids, elapsed_ms=elapsed_ms)
            return job_ids
        raise

def custom_exception_handler(job, exc_type, exc_value, traceback):
    """Custom exception handler for RQ worker failures"""
    task_id = job.id
    elapsed_ms = (time.time() - job.started_at.timestamp()) * 1000 if job.started_at else 0
    
    log_structured(
        "ERROR",
        f"Job failed: {exc_value}",
        "fail",
        task_id=task_id,
        trace_id=job.kwargs.get('task_id') if hasattr(job, 'kwargs') else None,
        elapsed_ms=elapsed_ms,
        exc_type=exc_type.__name__,
        exc_value=str(exc_value)
    )
    
    if SENTRY_DSN:
        sentry_sdk.capture_exception(exc_value)
    
    return True


@job('orchestrator', connection=redis, retry=Retry(max=3, interval=[10, 30, 60]))
def run_orchestrator_task(task_id: str, question: str, repo: str):
    """
    Execute orchestrator with retry logic (used by API for agent tasks)
    
    Args:
        task_id: Unique task identifier
        question: FAQ question or topic
        repo: GitHub repository (owner/repo format)
    """
    start_time = time.time()
    from graph import execute
    
    log_structured("INFO", f"Starting orchestrator task", "process", task_id=task_id, trace_id=task_id, question=question)
    
    try:
        if redis:
            redis.setex(
                f"agent:task:{task_id}",
                3600,
                json.dumps({
                    "status": "running",
                    "question": question,
                    "trace_id": task_id,
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
        
        pr_url, state, trace_id = execute(question, repo, trace_id=task_id)
        elapsed_ms = (time.time() - start_time) * 1000
        
        if redis:
            redis.setex(
                f"agent:task:{task_id}",
                3600,
                json.dumps({
                    "status": "done",
                    "question": question,
                    "trace_id": trace_id,
                    "pr_url": pr_url,
                    "state": state,
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
        
        log_structured("INFO", f"Task completed successfully", "complete", 
                     task_id=task_id, trace_id=trace_id, pr_url=pr_url, elapsed_ms=elapsed_ms)
        
        return {"pr_url": pr_url, "trace_id": trace_id, "state": state}
        
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        log_structured("ERROR", f"Task failed: {error_msg}", "fail", 
                     task_id=task_id, trace_id=task_id, elapsed_ms=elapsed_ms, error=error_msg)
        
        if SENTRY_DSN:
            sentry_sdk.add_breadcrumb(
                category='task',
                message=f'Task {task_id} failed',
                level='error',
                data={'question': question, 'repo': repo, 'elapsed_ms': elapsed_ms}
            )
            sentry_sdk.capture_exception(e)
        
        if redis:
            redis.setex(
                f"agent:task:{task_id}",
                3600,
                json.dumps({
                    "status": "error",
                    "question": question,
                    "trace_id": task_id,
                    "error": {
                        "code": "ORCHESTRATOR_FAILED",
                        "message": error_msg
                    },
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
        raise

if __name__ == "__main__":
    log_structured("INFO", "RQ Worker starting", "startup", worker_id=WORKER_ID, demo_mode=DEMO_MODE)
    
    if redis:
        heartbeat_thread = threading.Thread(target=update_worker_heartbeat, daemon=True)
        heartbeat_thread.start()
        log_structured("INFO", "Heartbeat thread started", "startup", worker_id=WORKER_ID)
    
    health = check_worker_health()
    log_structured("INFO", "Worker health check", "health_check", **health)
    
    print("RQ Worker started. Listening for orchestrator tasks...")
