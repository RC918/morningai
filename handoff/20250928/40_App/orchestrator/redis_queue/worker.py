#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks
Usage: rq worker orchestrator --url redis://localhost:6379/0
"""

import os
import sys
import time
import json
import socket
import threading
from datetime import datetime
from typing import Optional, List
from redis import Redis
from rq import Queue
from rq.decorators import job
from rq import Retry
import logging

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN and SENTRY_DSN.strip():
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "production"),
            traces_sample_rate=1.0,
        )
        logger.info("Sentry initialized in worker")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}. Continuing without Sentry integration.")
        SENTRY_DSN = None
else:
    SENTRY_DSN = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(redis_url, decode_responses=True)
q = Queue("orchestrator", connection=redis)

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
                    print(f"[Worker] Job with key {idempotency_key} already exists: {existing_job_ids}")
                    return existing_job_ids
            
            jobs = [q.enqueue(run_step, s) for s in steps]
            job_ids = [j.id for j in jobs]
            
            redis.setex(key, 3600, ','.join(job_ids))
            print(f"[Worker] Created idempotent job with key {idempotency_key}: {job_ids}")
            return job_ids
        else:
            jobs = [q.enqueue(run_step, s) for s in steps]
            return [j.id for j in jobs]
    except Exception as e:
        print(f"[Worker] Redis unavailable, running in demo mode: {e}")
        return [f"demo-job-{i}" for i in range(len(steps))]

@job('orchestrator', connection=redis, retry=Retry(max=3, interval=[10, 30, 60]))
def run_orchestrator_task(task_id: str, question: str, repo: str):
    """
    Execute orchestrator with retry logic (used by API for agent tasks)
    
    Args:
        task_id: Unique task identifier
        question: FAQ question or topic
        repo: GitHub repository (owner/repo format)
    """
    from graph import execute
    
    logger.info(f"Starting orchestrator task", extra={"task_id": task_id, "question": question})
    
    if SENTRY_DSN:
        sentry_sdk.add_breadcrumb(
            category='task',
            message=f'Starting orchestrator task',
            level='info',
            data={'task_id': task_id, 'question': question, 'repo': repo}
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
        
        redis.setex(
            redis_key,
            3600,
            json.dumps({
                "status": "running",
                "question": question,
                "trace_id": task_id,
                "updated_at": datetime.utcnow().isoformat()
            })
        )
        
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
        
        redis.setex(
            redis_key,
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
        
        logger.info(f"Task completed successfully", extra={"task_id": task_id, "pr_url": pr_url})
        return {"pr_url": pr_url, "trace_id": trace_id, "state": state}
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task failed: {error_msg}", extra={"task_id": task_id, "trace_id": task_id})
        
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

def start_heartbeat():
    """
    Start background heartbeat thread to update worker health status in Redis
    Key pattern: worker:health:{hostname}:{pid}
    TTL: 90 seconds, refresh every 30 seconds
    """
    hostname = socket.gethostname()
    pid = os.getpid()
    key = f"worker:health:{hostname}:{pid}"
    
    def heartbeat_loop():
        while True:
            try:
                heartbeat_data = json.dumps({
                    "ts": datetime.utcnow().isoformat(),
                    "hostname": hostname,
                    "pid": pid
                })
                redis.setex(key, 90, heartbeat_data)
                logger.info(f"Worker heartbeat updated", extra={"key": key, "hostname": hostname, "pid": pid})
            except Exception as e:
                logger.error(f"Failed to update worker heartbeat: {e}", extra={"key": key})
            time.sleep(30)
    
    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()
    logger.info(f"Worker started successfully / heartbeat started", extra={"key": key, "hostname": hostname, "pid": pid})

if __name__ == "__main__":
    from rq import Worker
    
    start_heartbeat()
    
    print("Starting RQ worker for 'orchestrator' queue...")
    worker = Worker([q], connection=redis)
    worker.work()
