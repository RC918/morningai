#!/usr/bin/env python3
"""
RQ Worker for orchestrator tasks
Usage: rq worker orchestrator --url redis://localhost:6379/0
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional
from redis import Redis
from rq.decorators import job
from rq import Retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(redis_url, decode_responses=True)

@job('orchestrator', connection=redis, retry=Retry(max=3, interval=[10, 30, 60]))
def run_orchestrator_task(task_id: str, topic: str, repo: str):
    """
    Execute orchestrator with retry logic
    
    Args:
        task_id: Unique task identifier
        topic: FAQ topic or question
        repo: GitHub repository (owner/repo format)
    """
    from graph import execute
    
    try:
        redis.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "running",
                "topic": topic,
                "trace_id": task_id,
                "updated_at": datetime.utcnow().isoformat()
            })
        )
        
        pr_url, state, trace_id = execute(topic, repo, trace_id=task_id)
        
        redis.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "done",
                "topic": topic,
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
                "topic": topic,
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
    print("RQ Worker started. Listening for orchestrator tasks...")
