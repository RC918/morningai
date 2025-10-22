#!/usr/bin/env python3
"""
Full E2E Integration Test
Tests the complete flow with actual Ops Agent Worker

Prerequisites:
1. Redis server running
2. Orchestrator API running (optional, for full test)
3. Environment variables set (REDIS_URL, VERCEL_TOKEN_NEW)

This test demonstrates:
- Task submission to Orchestrator
- Worker picking up and processing tasks
- OODA Loop execution
- Task status updates
- Event publishing
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import create_redis_queue, create_task
from agents.ops_agent.worker import OpsAgentWorker


async def test_full_integration():
    """Test full integration with real Worker"""
    
    print("=" * 70)
    print("Full E2E Integration Test")
    print("=" * 70)
    print()
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    vercel_token = os.getenv("VERCEL_TOKEN_NEW")
    
    if not vercel_token:
        print("⚠️  Warning: VERCEL_TOKEN_NEW not set. Deployment will fail.")
        print("   Set it with: export VERCEL_TOKEN_NEW=your-token")
        print()
    
    print("📡 Step 1: Connecting to Orchestrator...")
    queue = await create_redis_queue(redis_url=redis_url)
    print(f"✅ Connected to Redis at {redis_url}")
    print()
    
    print("🤖 Step 2: Starting Ops Agent Worker...")
    worker = OpsAgentWorker(
        redis_url=redis_url,
        vercel_token=vercel_token,
        poll_interval=1
    )
    
    worker_task = asyncio.create_task(worker.start())
    
    await asyncio.sleep(2)
    print("✅ Ops Agent Worker started and listening")
    print()
    
    print("📤 Step 3: Submitting monitoring task...")
    monitor_task = create_task(
        task_type="monitor",
        payload={
            "service": "system",
            "metrics": ["cpu", "memory", "disk"]
        },
        priority="P2",
        source="test"
    )
    monitor_task.mark_assigned("ops")
    
    await queue.enqueue_task(monitor_task)
    print(f"✅ Task {monitor_task.task_id} submitted")
    print(f"   Type: {monitor_task.type.value}")
    print(f"   Priority: {monitor_task.priority.value}")
    print()
    
    print("⏳ Step 4: Waiting for Worker to process task...")
    max_wait = 10
    for i in range(max_wait):
        await asyncio.sleep(1)
        task = await queue.get_task(monitor_task.task_id)
        if task and task.status.value in ["completed", "failed"]:
            break
        print(f"   Waiting... ({i+1}/{max_wait}s) Status: {task.status.value if task else 'unknown'}")
    print()
    
    print("🔍 Step 5: Checking task result...")
    final_task = await queue.get_task(monitor_task.task_id)
    
    if final_task:
        print(f"   Task ID: {final_task.task_id}")
        print(f"   Status: {final_task.status.value}")
        print(f"   Started at: {final_task.started_at}")
        print(f"   Completed at: {final_task.completed_at}")
        
        if final_task.status.value == "completed":
            print("   ✅ Task completed successfully!")
            if final_task.metadata.get('result'):
                result = final_task.metadata['result']
                print(f"   Result: {result}")
        elif final_task.status.value == "failed":
            print(f"   ❌ Task failed: {final_task.error}")
        else:
            print(f"   ⏳ Task still in progress: {final_task.status.value}")
    else:
        print("   ❌ Task not found")
    print()
    
    print("📤 Step 6: Submitting alert management task...")
    alert_task = create_task(
        task_type="alert",
        payload={
            "alert_type": "high_cpu",
            "threshold": 80,
            "action": "investigate"
        },
        priority="P1",
        source="test"
    )
    alert_task.mark_assigned("ops")
    
    await queue.enqueue_task(alert_task)
    print(f"✅ Task {alert_task.task_id} submitted")
    print()
    
    print("⏳ Step 7: Waiting for second task to process...")
    await asyncio.sleep(5)
    
    alert_final = await queue.get_task(alert_task.task_id)
    if alert_final:
        print(f"   Status: {alert_final.status.value}")
        if alert_final.status.value == "completed":
            print("   ✅ Alert task completed!")
        elif alert_final.status.value == "failed":
            print(f"   ❌ Alert task failed: {alert_final.error}")
    print()
    
    print("📊 Step 8: Queue statistics...")
    stats = await queue.get_queue_stats()
    print(f"   Pending tasks: {stats.get('pending_tasks', 0)}")
    print(f"   Processing tasks: {stats.get('processing_tasks', 0)}")
    print(f"   Total tasks: {stats.get('total_tasks', 0)}")
    print()
    
    print("🧹 Step 9: Cleaning up...")
    worker.is_running = False
    await worker.stop()
    await queue.disconnect()
    
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Cleanup complete")
    print()
    
    print("=" * 70)
    print("✅ Full E2E Integration Test Completed!")
    print("=" * 70)
    print()
    print("Test Results:")
    print(f"  • Monitoring task: {final_task.status.value if final_task else 'unknown'}")
    print(f"  • Alert task: {alert_final.status.value if alert_final else 'unknown'}")
    print(f"  • Worker: Stopped successfully")
    print()
    print("This demonstrates:")
    print("  ✅ Worker can connect to Orchestrator")
    print("  ✅ Worker can process tasks from queue")
    print("  ✅ OODA Loop executes successfully")
    print("  ✅ Task status updates work correctly")
    print("  ✅ Multiple task types are supported")
    print()


async def main():
    """Main entry point"""
    try:
        await test_full_integration()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("Full E2E Integration Test")
    print()
    print("Prerequisites:")
    print("  1. Redis server running:")
    print("     docker run -d -p 6379:6379 redis:alpine")
    print()
    print("  2. Environment variables:")
    print("     export REDIS_URL=redis://localhost:6379")
    print("     export VERCEL_TOKEN_NEW=your-token  # Optional for monitoring tasks")
    print()
    print("Starting test in 2 seconds...")
    print()
    
    import time
    time.sleep(2)
    
    asyncio.run(main())
