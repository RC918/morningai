import os, time
from typing import Optional, List
from redis import Redis
from rq import Queue

redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
q = Queue("orchestrator", connection=redis)

def run_step(step: str):
    print(f"[Worker] running step: {step}")
    time.sleep(2)
    if step == "check CI":
        return {"ok": False, "error": "build failed"}
    return {"ok": True}

def enqueue(steps, idempotency_key: Optional[str] = None) -> List[str]:
    try:
        if idempotency_key:
            key = f"orchestrator:job:{idempotency_key}"
            if redis.exists(key):
                result = redis.get(key)
                if result:
                    existing_job_ids = result.decode('utf-8').split(',')
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
