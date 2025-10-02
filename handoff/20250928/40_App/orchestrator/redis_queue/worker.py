#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks
Usage: rq worker orchestrator --url redis://localhost:6379/0
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Optional, List
from redis import Redis
from rq import Queue
from rq.decorators import job
from rq import Retry

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
    print("Starting RQ worker for 'orchestrator' queue...")
    with Worker([q], connection=redis) as worker:
        worker.work()
