#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks with heartbeat monitoring
Usage: rq worker orchestrator --url redis://localhost:6379/0
"""

import os
import sys
import time
import json
import threading
import signal
import atexit
from datetime import datetime
from typing import Optional, List
from redis import Redis, ConnectionError as RedisConnectionError
from rq import Queue
from rq.decorators import job
from rq import Retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(redis_url, decode_responses=True)
q = Queue("orchestrator", connection=redis)

WORKER_ID = os.getenv("RENDER_INSTANCE_ID", os.getenv("HOSTNAME", "worker-local"))
shutdown_event = threading.Event()
heartbeat_thread = None

def update_worker_heartbeat():
    """
    Background thread to update worker heartbeat in Redis with TTL.
    Runs until shutdown_event is set.
    """
    print(f"[Worker] Heartbeat thread started for worker_id={WORKER_ID}")
    
    while not shutdown_event.is_set():
        try:
            if redis:
                heartbeat_key = f"worker:health:{WORKER_ID}"
                redis.setex(
                    heartbeat_key,
                    120,
                    json.dumps({
                        "last_heartbeat": datetime.utcnow().isoformat() + "Z",
                        "worker_id": WORKER_ID,
                        "status": "healthy",
                        "timestamp": int(time.time())
                    })
                )
            
            shutdown_event.wait(30)
        except RedisConnectionError as e:
            print(f"[Worker] Heartbeat Redis connection error: {e}")
            shutdown_event.wait(30)
        except Exception as e:
            print(f"[Worker] Heartbeat update failed: {e}")
            shutdown_event.wait(30)
    
    print(f"[Worker] Heartbeat thread stopped for worker_id={WORKER_ID}")

def cleanup_heartbeat():
    """
    Cleanup function to gracefully shutdown heartbeat thread.
    Called on worker shutdown or exit.
    """
    global heartbeat_thread
    
    print(f"[Worker] Initiating graceful shutdown for worker_id={WORKER_ID}")
    shutdown_event.set()
    
    if heartbeat_thread and heartbeat_thread.is_alive():
        heartbeat_thread.join(timeout=5)
        if heartbeat_thread.is_alive():
            print(f"[Worker] Warning: Heartbeat thread did not stop within timeout")
        else:
            print(f"[Worker] Heartbeat thread stopped successfully")
    
    try:
        if redis:
            heartbeat_key = f"worker:health:{WORKER_ID}"
            redis.delete(heartbeat_key)
            print(f"[Worker] Cleaned up heartbeat key: {heartbeat_key}")
    except Exception as e:
        print(f"[Worker] Failed to cleanup heartbeat key: {e}")

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    print(f"[Worker] Received signal {signum}, shutting down gracefully...")
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
    
    try:
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
        
        return {"pr_url": pr_url, "trace_id": trace_id, "state": state}
        
    except Exception as e:
        error_msg = str(e)
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
    from rq import Worker
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_heartbeat)
    
    print(f"[Worker] Starting RQ worker for 'orchestrator' queue (worker_id={WORKER_ID})")
    
    heartbeat_thread = threading.Thread(target=update_worker_heartbeat, daemon=False, name="HeartbeatThread")
    heartbeat_thread.start()
    print(f"[Worker] Heartbeat monitoring enabled with 120s TTL")
    
    try:
        worker = Worker([q], connection=redis)
        worker.work()
    except KeyboardInterrupt:
        print(f"[Worker] KeyboardInterrupt received")
    except Exception as e:
        print(f"[Worker] Unexpected error: {e}")
    finally:
        cleanup_heartbeat()
