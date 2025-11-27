#!/usr/bin/env python3
"""
Phase 1 Staging Load Generator
================================

Generates diverse test tasks to collect LLM Planner data for Phase 1 monitoring.

Strategy:
- Generate task_ids that hash to < 5 (guaranteed canary routing)
- Submit diverse, realistic test goals covering multiple categories
- Mark tasks with [Phase1-Test] prefix for filtering

Target: 30-50 LLM Planner calls
"""

import os
import sys
import hashlib
import uuid
import time
import redis
from rq import Queue
from rq.serializers import JSONSerializer

# Configuration
REDIS_URL = os.environ.get('REDIS_URL')
if not REDIS_URL:
    print("ERROR: REDIS_URL environment variable not set")
    sys.exit(1)

QUEUE_NAME = "orchestrator-staging"
REPO = "RC918/morningai"
USE_LANGGRAPH_PERCENT = 5

# Diverse test goals covering different categories
TEST_GOALS = [
    # Code Generation - Python
    "[Phase1-Test] Create a Python function that validates email addresses using regex",
    "[Phase1-Test] Generate a Python CLI tool that converts JSON to YAML format",
    "[Phase1-Test] Write a Python class for managing a simple in-memory cache with TTL",
    "[Phase1-Test] Create a Python decorator that logs function execution time",
    "[Phase1-Test] Generate a Python script that reads CSV and outputs statistics",
    
    # Code Generation - TypeScript/JavaScript
    "[Phase1-Test] Create a TypeScript React component for a user profile card",
    "[Phase1-Test] Write a JavaScript function that debounces user input",
    "[Phase1-Test] Generate a Node.js Express middleware for request logging",
    "[Phase1-Test] Create a TypeScript utility for deep cloning objects",
    "[Phase1-Test] Write a React hook for managing form state with validation",
    
    # Code Generation - Other Languages
    "[Phase1-Test] Create a Go HTTP handler for health check endpoint",
    "[Phase1-Test] Write a SQL query to find duplicate records in users table",
    "[Phase1-Test] Generate a Rust function for parsing command line arguments",
    "[Phase1-Test] Create a Java method that sorts a list of custom objects",
    
    # Debugging
    "[Phase1-Test] Fix bug: Python function raises KeyError when accessing nested dict. Code: data['user']['email']",
    "[Phase1-Test] Debug: TypeScript async function not awaiting promise correctly. Getting 'Promise pending' error",
    "[Phase1-Test] Resolve: SQL query returning duplicate rows. Query: SELECT * FROM orders JOIN users ON orders.user_id = users.id",
    "[Phase1-Test] Fix: React component re-rendering infinitely. useEffect dependency array issue",
    
    # Refactoring
    "[Phase1-Test] Refactor this 200-line Python function into smaller, testable functions",
    "[Phase1-Test] Extract common logic from three similar TypeScript components into a shared hook",
    "[Phase1-Test] Simplify nested if-else statements in this JavaScript validation function",
    "[Phase1-Test] Convert callback-based Node.js code to async/await pattern",
    
    # Testing
    "[Phase1-Test] Write pytest tests for a user authentication module covering success and failure cases",
    "[Phase1-Test] Create Jest tests for a React form component with validation",
    "[Phase1-Test] Generate unit tests for a Python data processing pipeline",
    "[Phase1-Test] Write integration tests for a REST API endpoint using pytest",
    
    # Documentation
    "[Phase1-Test] Update README.md to document new authentication feature with examples",
    "[Phase1-Test] Generate API documentation for REST endpoints in OpenAPI format",
    "[Phase1-Test] Write inline docstrings for Python module following Google style",
    "[Phase1-Test] Create user guide for CLI tool with usage examples",
    
    # GitHub Issue Style (Noisy)
    "[Phase1-Test] Bug Report: Application crashes when uploading files > 10MB. Steps to reproduce: 1) Navigate to upload page 2) Select large file 3) Click upload. Expected: Success message. Actual: 500 error",
    "[Phase1-Test] Feature Request: Add dark mode toggle to settings page. Users have requested this feature. Should persist preference in localStorage",
    "[Phase1-Test] Issue: Login form not validating email format. Allows invalid emails like 'test@'. Should show error message for invalid format",
    
    # Jira Style
    "[Phase1-Test] [TASK-123] Implement user profile edit functionality. Acceptance criteria: 1) User can update name, email, bio 2) Changes saved to database 3) Success notification shown",
    "[Phase1-Test] [BUG-456] Dashboard loading slowly with large datasets. Performance issue. Need to optimize query or add pagination",
    "[Phase1-Test] [STORY-789] As a user, I want to export my data to CSV so that I can analyze it offline",
    
    # Multi-step Complex
    "[Phase1-Test] Add new feature: User can upload profile picture. Requirements: 1) Image upload with validation 2) Resize to 200x200 3) Store in S3 4) Update database 5) Show preview",
    "[Phase1-Test] Implement password reset flow: 1) User requests reset 2) Send email with token 3) Validate token 4) Allow password update 5) Invalidate old sessions",
    "[Phase1-Test] Create admin dashboard: 1) List all users with pagination 2) Search by name/email 3) Filter by status 4) Export to CSV 5) Bulk actions",
    
    # Edge Cases
    "[Phase1-Test] Handle edge case: What happens when user submits empty form? Need validation and error messages",
    "[Phase1-Test] Fix race condition: Two users editing same document simultaneously. Need conflict resolution",
    "[Phase1-Test] Handle timeout: API call takes > 30 seconds. Need retry logic with exponential backoff",
    
    # Ambiguous/Mixed
    "[Phase1-Test] The login page isn't working right. Sometimes it logs in, sometimes it doesn't. Can you help?",
    "[Phase1-Test] Need to add some kind of notification system. Users should know when something important happens",
    "[Phase1-Test] Performance is bad. Everything is slow. Fix it please",
    
    # Code Review Style
    "[Phase1-Test] Code review: This function has too many parameters (8+). Suggest refactoring to use config object",
    "[Phase1-Test] Security review: SQL query uses string concatenation. Vulnerable to SQL injection. Use parameterized queries",
    "[Phase1-Test] Review: No error handling in async function. Should wrap in try-catch and handle failures gracefully",
]


def calculate_task_percent(task_id: str) -> int:
    """Calculate canary bucket for task_id (matches worker.py logic)"""
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    return task_hash % 100


def generate_canary_task_id(prefix: str = "phase1-stg-test") -> str:
    """Generate a task_id that will trigger canary routing (< 5%)"""
    attempts = 0
    max_attempts = 1000
    
    while attempts < max_attempts:
        # Generate UUID-based task_id
        task_id = f"{prefix}-{uuid.uuid4()}"
        task_percent = calculate_task_percent(task_id)
        
        if task_percent < USE_LANGGRAPH_PERCENT:
            return task_id, task_percent
        
        attempts += 1
    
    raise RuntimeError(f"Failed to generate canary task_id after {max_attempts} attempts")


def submit_batch(batch_size: int, start_idx: int = 0, delay: float = 0.5):
    """Submit a batch of test tasks to staging queue"""
    print(f"\n{'='*80}")
    print(f"Submitting Batch: {batch_size} tasks (starting from index {start_idx})")
    print(f"{'='*80}\n")
    
    # Connect to Redis
    r = redis.from_url(REDIS_URL)
    q = Queue(QUEUE_NAME, connection=r, serializer=JSONSerializer())
    
    # Get job timeout from environment (matches worker.py)
    JOB_TIMEOUT = int(os.getenv("RQ_JOB_TIMEOUT", "600"))
    print(f"Using job timeout: {JOB_TIMEOUT} seconds\n")
    
    submitted = []
    
    for i in range(batch_size):
        goal_idx = (start_idx + i) % len(TEST_GOALS)
        goal = TEST_GOALS[goal_idx]
        
        # Generate task_id that will trigger canary
        task_id, task_percent = generate_canary_task_id()
        
        try:
            # Enqueue task with explicit timeout
            job = q.enqueue(
                'redis_queue.worker.run_orchestrator_task',
                task_id,
                goal,
                REPO,
                job_id=task_id,
                job_timeout=JOB_TIMEOUT
            )
            
            submitted.append({
                'task_id': task_id,
                'task_percent': task_percent,
                'job_id': job.id,
                'goal_preview': goal[:60] + '...' if len(goal) > 60 else goal
            })
            
            print(f"✅ [{i+1}/{batch_size}] Task submitted")
            print(f"   Task ID: {task_id}")
            print(f"   Task %: {task_percent} (< {USE_LANGGRAPH_PERCENT} ✓)")
            print(f"   Goal: {goal[:70]}...")
            print()
            
            # Small delay to avoid overwhelming the queue
            if delay > 0 and i < batch_size - 1:
                time.sleep(delay)
                
        except Exception as e:
            print(f"❌ [{i+1}/{batch_size}] Failed to submit task")
            print(f"   Error: {e}")
            print()
    
    return submitted


def main():
    print("=" * 80)
    print("Phase 1 Staging Load Generator")
    print("=" * 80)
    print()
    print(f"Queue: {QUEUE_NAME}")
    print(f"Repo: {REPO}")
    print(f"Canary threshold: {USE_LANGGRAPH_PERCENT}%")
    print(f"Available test goals: {len(TEST_GOALS)}")
    print()
    
    # Ask user for batch size
    print("How many tasks to submit?")
    print("  - For 30-50 planner calls: recommend 30-50 tasks (100% hit rate)")
    print("  - Start small: 10-20 tasks to verify")
    print()
    
    try:
        batch_size = int(input("Enter number of tasks (or press Enter for 30): ").strip() or "30")
    except ValueError:
        print("Invalid input. Using default: 30")
        batch_size = 30
    
    print()
    confirm = input(f"Submit {batch_size} tasks to {QUEUE_NAME}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Aborted.")
        return
    
    # Submit batch
    start_time = time.time()
    submitted = submit_batch(batch_size, delay=0.3)
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 80)
    print("Submission Complete!")
    print("=" * 80)
    print()
    print(f"✅ Submitted: {len(submitted)} tasks")
    print(f"⏱️  Time: {elapsed:.1f} seconds")
    print(f"📊 Expected LLM Planner calls: {len(submitted)} (100% hit rate)")
    print()
    print("=" * 80)
    print("Next Steps: Verify Data Collection")
    print("=" * 80)
    print()
    print("1. Wait 5-10 minutes for tasks to process")
    print()
    print("2. Check JSONL file for new entries:")
    print("   cd ~/repos/morningai")
    print("   grep -v '\"trace-123\"' tools/agent_eval/data/planner_runs.jsonl | wc -l")
    print("   tail -5 tools/agent_eval/data/planner_runs.jsonl")
    print()
    print("3. Run analysis script:")
    print("   python tools/monitoring/analyze_planner_data.py")
    print()
    print("4. Check Render logs for planner execution:")
    print("   Search: '[LLM Planner] Generated valid plan'")
    print()


if __name__ == "__main__":
    main()
