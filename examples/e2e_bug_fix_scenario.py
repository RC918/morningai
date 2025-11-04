#!/usr/bin/env python3
"""
E2E Scenario: Bug Fix Closure Loop
Demonstrates Dev Agent → Ops Agent collaboration through Orchestrator

Scenario Flow:
1. Dev Agent detects a bug (simulated)
2. Dev Agent creates a fix and opens PR
3. Dev Agent submits deployment task to Orchestrator
4. Orchestrator routes task to Ops Agent
5. Ops Agent deploys the fix
6. Ops Agent monitors deployment status
7. Ops Agent reports back to Orchestrator
8. Dev Agent receives completion notification
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import create_redis_queue, create_task


async def simulate_bug_fix_scenario():
    """Simulate a complete bug fix closure loop"""
    
    print("=" * 70)
    print("E2E Scenario: Bug Fix Closure Loop")
    print("=" * 70)
    print()
    
    print("📡 Step 1: Connecting to Orchestrator...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    queue = await create_redis_queue(redis_url=redis_url)
    print(f"✅ Connected to Redis at {redis_url}")
    print()
    
    print("🐛 Step 2: Dev Agent detects bug...")
    bug_info = {
        "issue_id": "BUG-123",
        "title": "Login page crashes on invalid credentials",
        "severity": "high",
        "detected_at": datetime.now(timezone.utc).isoformat()
    }
    print(f"   Issue: {bug_info['title']}")
    print(f"   Severity: {bug_info['severity']}")
    print()
    
    print("🔧 Step 3: Dev Agent creates fix...")
    fix_info = {
        "pr_number": "456",
        "branch": "fix/bug-123-login-crash",
        "commit": "abc123def456",
        "files_changed": ["src/auth/login.ts", "tests/auth.test.ts"],
        "tests_passed": True
    }
    print(f"   PR: #{fix_info['pr_number']}")
    print(f"   Branch: {fix_info['branch']}")
    print(f"   Tests: {'✅ Passed' if fix_info['tests_passed'] else '❌ Failed'}")
    print()
    
    print("📤 Step 4: Dev Agent submits deployment task to Orchestrator...")
    deploy_task = create_task(
        task_type="deploy",
        payload={
            "project": "morningai",
            "environment": "production",
            "pr_number": fix_info['pr_number'],
            "branch": fix_info['branch'],
            "commit": fix_info['commit'],
            "reason": f"Deploy fix for {bug_info['issue_id']}: {bug_info['title']}"
        },
        priority="P1",
        source="dev",
        metadata={
            "bug_info": bug_info,
            "fix_info": fix_info
        }
    )
    
    deploy_task.mark_assigned("ops")
    
    success = await queue.enqueue_task(deploy_task)
    if success:
        print(f"✅ Task {deploy_task.task_id} created and assigned to Ops Agent")
        print(f"   Priority: {deploy_task.priority.value}")
        print(f"   Type: {deploy_task.type.value}")
    else:
        print("❌ Failed to create task")
        return
    print()
    
    print("⏳ Step 5: Waiting for Ops Agent to process task...")
    print("   (In production, Ops Agent Worker would pick this up automatically)")
    print()
    
    await asyncio.sleep(2)
    
    print("🔍 Step 6: Checking task status...")
    task = await queue.get_task(deploy_task.task_id)
    if task:
        print(f"   Task ID: {task.task_id}")
        print(f"   Status: {task.status.value}")
        print(f"   Assigned to: {task.assigned_to}")
    print()
    
    print("🚀 Step 7: Simulating Ops Agent deployment...")
    task.mark_in_progress()
    await queue.update_task(task)
    print("   Status: in_progress")
    
    await asyncio.sleep(2)
    
    task.mark_completed()
    task.metadata['result'] = {
        "success": True,
        "deployment_id": "dpl_xyz789",
        "url": "https://morningai-abc123.vercel.app",
        "state": "READY",
        "deployed_at": datetime.now(timezone.utc).isoformat()
    }
    await queue.update_task(task)
    print("   Status: completed ✅")
    print(f"   Deployment URL: {task.metadata['result']['url']}")
    print()
    
    print("📢 Step 8: Publishing deployment completion event...")
    await queue.publish_event(
        event_type="deploy.succeeded",
        source_agent="ops",
        task_id=task.task_id,
        payload={
            "deployment_id": task.metadata['result']['deployment_id'],
            "url": task.metadata['result']['url'],
            "bug_fixed": bug_info['issue_id'],
            "pr_number": fix_info['pr_number']
        },
        trace_id=task.trace_id
    )
    print("✅ Event published to event bus")
    print()
    
    print("📬 Step 9: Dev Agent receives completion notification...")
    print(f"   Bug {bug_info['issue_id']} fix deployed successfully!")
    print(f"   PR #{fix_info['pr_number']} is now live in production")
    print(f"   Deployment URL: {task.metadata['result']['url']}")
    print()
    
    print("=" * 70)
    print("✅ Bug Fix Closure Loop Completed Successfully!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  • Bug detected: {bug_info['issue_id']}")
    print(f"  • Fix created: PR #{fix_info['pr_number']}")
    print(f"  • Task submitted: {task.task_id}")
    print(f"  • Deployed by: Ops Agent")
    print(f"  • Status: {task.status.value}")
    print(f"  • Deployment: {task.metadata['result']['url']}")
    print()
    print("Key Benefits:")
    print("  ✅ Automated deployment pipeline")
    print("  ✅ Multi-agent collaboration")
    print("  ✅ Event-driven architecture")
    print("  ✅ Full traceability (trace_id: {})".format(task.trace_id))
    print()
    
    await queue.disconnect()


async def main():
    """Main entry point"""
    try:
        await simulate_bug_fix_scenario()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scenario interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("Prerequisites:")
    print("  1. Redis server running (docker run -d -p 6379:6379 redis:alpine)")
    print("  2. REDIS_URL environment variable set (default: redis://localhost:6379)")
    print()
    print("Starting scenario in 2 seconds...")
    print()
    
    import time
    time.sleep(2)
    
    asyncio.run(main())
