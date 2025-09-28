import os, time
from redis import Redis
from rq import Queue

redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
q = Queue("orchestrator", connection=redis)

def run_step(step: str):
    print(f"[Worker] running step: {step}")
    time.sleep(2)
    # simulate a failure on first try of 'check CI'
    if step == "check CI":
        return {"ok": False, "error": "build failed"}
    return {"ok": True}

def enqueue(steps):
    jobs = [q.enqueue(run_step, s) for s in steps]
    return [j.id for j in jobs]
