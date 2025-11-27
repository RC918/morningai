#!/usr/bin/env python3
"""
Phase 1 Canary Final Validation Test
=====================================

This script tests the complete Phase 1 5% canary deployment with:
- Valid UUID format (no DB errors)
- Guaranteed canary routing (task_percent=3 < 5)
- Full validation of LLM Planner + JSONL recording

Expected Results:
1. Canary routing log: "Canary deployment: task_percent=3, threshold=5, use_langgraph=True"
2. LLM Planner execution: "[LLM Planner] Generated valid plan with X steps"
3. JSONL recording: "[LLM Planner] Recorded planner event to .../planner_runs.jsonl"
4. Task completion without 429 errors
"""

import os
import redis
from rq import Queue
from rq.serializers import JSONSerializer

# Configuration
REDIS_URL = os.environ['REDIS_URL']
QUEUE_NAME = "orchestrator-staging"

# Test UUID that will trigger canary (task_percent=3 < 5)
TASK_ID = "dd85a361-a6d1-46c1-aebe-9705423a75f4"

# Test parameters
GOAL = "Phase 1 Canary Final Validation Test - Create a simple Python function that adds two numbers"
REPO = "RC918/morningai"

print("=" * 80)
print("Phase 1 Canary Final Validation Test")
print("=" * 80)
print()
print(f"Task ID: {TASK_ID}")
print(f"Expected task_percent: 3 (< 5 threshold)")
print(f"Expected routing: LangGraph (5% canary)")
print(f"Queue: {QUEUE_NAME}")
print(f"Goal: {GOAL}")
print()
print("Submitting task to Redis queue...")
print()

# Connect to Redis and enqueue task
r = redis.from_url(REDIS_URL)
q = Queue(QUEUE_NAME, connection=r, serializer=JSONSerializer())

job = q.enqueue(
    'redis_queue.worker.run_orchestrator_task',
    TASK_ID,
    GOAL,
    REPO,
    job_id=TASK_ID
)

print(f"✅ Task submitted successfully!")
print(f"   Job ID: {job.id}")
print(f"   Queue: {QUEUE_NAME}")
print()
print("=" * 80)
print("Next Steps: Verify in Render Logs")
print("=" * 80)
print()
print("1. Go to Render Dashboard → morningai-backend-v2-stg-worker → Logs")
print()
print("2. Search for these logs (in order):")
print()
print("   a) Canary routing decision:")
print(f'      Search: "Canary deployment: task_percent=3"')
print(f'      Expected: "Canary deployment: task_percent=3, threshold=5, use_langgraph=True"')
print()
print("   b) LLM Planner execution:")
print(f'      Search: "[LLM Planner] Generated valid plan"')
print(f'      Expected: "[LLM Planner] Generated valid plan with X steps"')
print()
print("   c) JSONL recording:")
print(f'      Search: "[LLM Planner] Recorded planner event"')
print(f'      Expected: "[LLM Planner] Recorded planner event to .../planner_runs.jsonl"')
print()
print("3. Verify NO 429 errors:")
print(f'   Search: "Error code: 429"')
print(f'   Expected: No results (credit balance is now positive)')
print()
print("=" * 80)
print("Success Criteria")
print("=" * 80)
print()
print("✅ All 3 logs present (canary routing, LLM planner, JSONL recording)")
print("✅ No 429 quota errors")
print("✅ Task completes successfully")
print()
print("If all criteria met: Phase 1 Canary is FULLY VALIDATED! 🎉")
print()
