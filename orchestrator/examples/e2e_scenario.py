#!/usr/bin/env python3
"""
E2E Scenario: Alert → Dev Fix → Ops Deploy → FAQ Update

Demonstrates the complete workflow:
1. Ops Agent detects an alert
2. Creates a bugfix task for Dev Agent
3. Dev Agent creates a PR
4. PR is merged, triggering deployment
5. Ops Agent deploys to production
6. FAQ Agent updates knowledge base
"""
import asyncio
import logging
from orchestrator import create_redis_queue, create_task
from orchestrator.schemas.event_schema import EventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_e2e_scenario():
    """Run complete E2E scenario"""
    
    logger.info("=== Starting E2E Scenario ===")
    
    queue = await create_redis_queue()
    
    logger.info("Step 1: Ops Agent detects system alert")
    alert_task = create_task(
        task_type="alert",
        payload={
            "severity": "high",
            "message": "API response time > 2s",
            "metrics": {
                "avg_response_time": 2.5,
                "p95_response_time": 4.2
            }
        },
        priority="P1",
        source="ops"
    )
    await queue.enqueue_task(alert_task)
    logger.info(f"✓ Alert task created: {alert_task.task_id}")
    
    await asyncio.sleep(1)
    
    logger.info("\nStep 2: Create bugfix task for Dev Agent")
    bugfix_task = create_task(
        task_type="bugfix",
        payload={
            "issue": "Optimize API response time",
            "repo": "morningai",
            "description": "API response time exceeded 2s threshold",
            "related_alert": alert_task.task_id
        },
        priority="P1",
        source="ops",
        parent_task_id=alert_task.task_id
    )
    await queue.enqueue_task(bugfix_task)
    logger.info(f"✓ Bugfix task created: {bugfix_task.task_id}")
    
    await asyncio.sleep(1)
    
    logger.info("\nStep 3: Simulate PR creation and merge")
    await queue.publish_event(
        event_type="pr.opened",
        source_agent="dev_agent",
        payload={
            "pr_number": 123,
            "pr_url": "https://github.com/morningai/pull/123",
            "title": "Fix: Optimize API response time",
            "branch": "fix/api-performance"
        },
        task_id=bugfix_task.task_id,
        trace_id=bugfix_task.trace_id
    )
    logger.info("✓ PR opened event published")
    
    await asyncio.sleep(1)
    
    await queue.publish_event(
        event_type="pr.merged",
        source_agent="dev_agent",
        payload={
            "pr_number": 123,
            "pr_url": "https://github.com/morningai/pull/123",
            "branch": "main",
            "repo": "morningai"
        },
        task_id=bugfix_task.task_id,
        trace_id=bugfix_task.trace_id
    )
    logger.info("✓ PR merged event published (triggers deployment)")
    
    await asyncio.sleep(1)
    
    logger.info("\nStep 4: Create deployment task")
    deploy_task = create_task(
        task_type="deploy",
        payload={
            "project": "morningai",
            "environment": "production",
            "branch": "main",
            "pr_number": 123
        },
        priority="P1",
        source="ops",
        parent_task_id=bugfix_task.task_id
    )
    await queue.enqueue_task(deploy_task)
    logger.info(f"✓ Deployment task created: {deploy_task.task_id}")
    
    await asyncio.sleep(1)
    
    logger.info("\nStep 5: Simulate successful deployment")
    await queue.publish_event(
        event_type="deploy.succeeded",
        source_agent="ops_agent",
        payload={
            "deployment_id": "dep-456",
            "url": "https://morningai.vercel.app",
            "environment": "production"
        },
        task_id=deploy_task.task_id,
        trace_id=deploy_task.trace_id
    )
    logger.info("✓ Deployment succeeded event published")
    
    await asyncio.sleep(1)
    
    logger.info("\nStep 6: Create FAQ update task")
    kb_update_task = create_task(
        task_type="kb_update",
        payload={
            "type": "release_notes",
            "title": "API Performance Optimization",
            "content": "Improved API response time from 2.5s to 0.8s through query optimization",
            "related_pr": 123,
            "related_deployment": "dep-456"
        },
        priority="P2",
        source="ops",
        parent_task_id=deploy_task.task_id
    )
    await queue.enqueue_task(kb_update_task)
    logger.info(f"✓ KB update task created: {kb_update_task.task_id}")
    
    await asyncio.sleep(1)
    
    logger.info("\nStep 7: Simulate KB update completion")
    await queue.publish_event(
        event_type="kb.updated",
        source_agent="faq_agent",
        payload={
            "document_id": "doc-789",
            "title": "API Performance Optimization",
            "url": "https://morningai.com/kb/api-performance"
        },
        task_id=kb_update_task.task_id,
        trace_id=kb_update_task.trace_id
    )
    logger.info("✓ KB updated event published")
    
    logger.info("\n=== E2E Scenario Complete ===")
    logger.info("\nWorkflow Summary:")
    logger.info(f"1. Alert detected: {alert_task.task_id}")
    logger.info(f"2. Bugfix task: {bugfix_task.task_id}")
    logger.info(f"3. PR opened & merged: #123")
    logger.info(f"4. Deployment: {deploy_task.task_id}")
    logger.info(f"5. KB updated: {kb_update_task.task_id}")
    logger.info("\nAll tasks routed through Orchestrator with event bus coordination!")
    
    stats = await queue.get_queue_stats()
    logger.info(f"\nQueue stats: {stats}")
    
    await queue.disconnect()


if __name__ == "__main__":
    asyncio.run(run_e2e_scenario())
