#!/usr/bin/env python3
"""
Ops Agent Worker - Connects to Orchestrator and processes tasks
Consumes tasks from Redis queue and executes them using Ops Agent OODA Loop
"""
import logging
import asyncio
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

ops_agent_dir = os.path.dirname(os.path.abspath(__file__))
if ops_agent_dir not in sys.path:
    sys.path.insert(0, ops_agent_dir)

api_backend_path = os.path.join(project_root, 'handoff/20250928/40_App/api-backend/src')
if api_backend_path not in sys.path:
    sys.path.insert(0, api_backend_path)

from utils.redis_config import get_secure_redis_url
from orchestrator import RedisQueue, create_redis_queue, UnifiedTask
from ops_agent_ooda import OpsAgentOODA

governance_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
if governance_path not in sys.path:
    sys.path.insert(0, governance_path)

from governance import (
    get_cost_tracker,
    get_reputation_engine,
    get_permission_checker,
    CostBudgetExceeded,
    PermissionDenied
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpsAgentWorker:
    """
    Worker that connects Ops Agent to Orchestrator
    
    Responsibilities:
    - Poll Redis queue for tasks assigned to 'ops' agent
    - Execute tasks using Ops Agent OODA Loop
    - Update task status in Orchestrator
    - Publish events for task lifecycle
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        vercel_token: Optional[str] = None,
        team_id: Optional[str] = None,
        poll_interval: int = 2
    ):
        """
        Initialize Ops Agent Worker
        
        Args:
            redis_url: Redis connection URL
            vercel_token: Vercel API token
            team_id: Vercel team ID
            poll_interval: Polling interval in seconds
        """
        if redis_url:
            self.redis_url = redis_url
        else:
            self.redis_url = get_secure_redis_url(allow_local=os.getenv("TESTING") == "true")
        self.vercel_token = vercel_token or os.getenv("VERCEL_TOKEN_NEW")
        self.team_id = team_id or os.getenv("VERCEL_TEAM_ID")
        self.poll_interval = poll_interval
        
        self.queue: Optional[RedisQueue] = None
        self.ops_agent: Optional[OpsAgentOODA] = None
        self.is_running = False
        
        self.cost_tracker = get_cost_tracker()
        self.reputation_engine = get_reputation_engine()
        self.permission_checker = get_permission_checker()
        self.agent_id: Optional[str] = None
        
        logger.info(f"Initialized Ops Agent Worker (Redis: {self.redis_url})")
        logger.info("✅ Governance modules initialized")
    
    async def start(self):
        """Start the worker"""
        try:
            logger.info("Starting Ops Agent Worker...")
            
            self.queue = await create_redis_queue(redis_url=self.redis_url)
            logger.info("✅ Connected to Orchestrator Redis queue")
            
            self.ops_agent = OpsAgentOODA(
                vercel_token=self.vercel_token,
                team_id=self.team_id,
                enable_monitoring=True,
                enable_alerts=True
            )
            logger.info("✅ Initialized Ops Agent OODA Loop")
            
            self.agent_id = self.reputation_engine.get_or_create_agent('ops_agent')
            if self.agent_id:
                logger.info(f"✅ Registered with Governance (agent_id: {self.agent_id})")
                permission_level = self.reputation_engine.get_permission_level(self.agent_id)
                score = self.reputation_engine.get_reputation_score(self.agent_id)
                logger.info(f"   Permission Level: {permission_level}, Reputation Score: {score}")
            else:
                logger.warning("⚠️ Could not register with Governance (degraded mode)")
            
            await self.queue.subscribe_to_events([
                "task.created",
                "deploy.started",
                "alert.triggered"
            ])
            logger.info("✅ Subscribed to Orchestrator events")
            
            asyncio.create_task(self._event_listener())
            
            self.is_running = True
            logger.info("🚀 Ops Agent Worker started successfully")
            
            await self._process_tasks()
            
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            raise
    
    async def stop(self):
        """Stop the worker"""
        logger.info("Stopping Ops Agent Worker...")
        self.is_running = False
        
        if self.queue:
            await self.queue.stop_event_listener()
            await self.queue.disconnect()
        
        logger.info("✅ Ops Agent Worker stopped")
    
    async def _process_tasks(self):
        """Main task processing loop"""
        logger.info("Starting task processing loop...")
        
        while self.is_running:
            try:
                task = await self.queue.dequeue_task()
                
                if not task:
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                if task.assigned_to != "ops":
                    logger.warning(f"Task {task.task_id} not assigned to ops (assigned to {task.assigned_to})")
                    await self.queue.enqueue_task(task)
                    continue
                
                logger.info(f"📥 Processing task {task.task_id} (type: {task.type.value}, priority: {task.priority.value})")
                
                await self._execute_task(task)
                
            except asyncio.CancelledError:
                logger.info("Task processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _execute_task(self, task: UnifiedTask):
        """
        Execute a task using Ops Agent
        
        Args:
            task: UnifiedTask to execute
        """
        try:
            if self.agent_id:
                try:
                    self.cost_tracker.enforce_budget(task.trace_id, period='daily')
                    self.cost_tracker.enforce_budget(task.trace_id, period='hourly')
                    logger.info(f"✅ Budget check passed for task {task.task_id}")
                except CostBudgetExceeded as e:
                    logger.error(f"❌ Budget exceeded: {e}")
                    task.mark_failed(f"Budget exceeded: {e}")
                    await self.queue.update_task(task)
                    if self.agent_id:
                        self.reputation_engine.record_event(
                            self.agent_id,
                            'budget_exceeded',
                            trace_id=task.trace_id,
                            reason=str(e)
                        )
                    return
                
                operation = self._map_task_to_operation(task)
                try:
                    self.permission_checker.check_permission(self.agent_id, operation)
                    logger.info(f"✅ Permission check passed for operation: {operation}")
                except PermissionDenied as e:
                    logger.error(f"❌ Permission denied: {e}")
                    task.mark_failed(f"Permission denied: {e}")
                    await self.queue.update_task(task)
                    self.reputation_engine.record_event(
                        self.agent_id,
                        'permission_denied',
                        trace_id=task.trace_id,
                        reason=str(e)
                    )
                    return
            
            task.mark_in_progress()
            await self.queue.update_task(task)
            
            await self.queue.publish_event(
                event_type="task.started",
                source_agent="ops",
                task_id=task.task_id,
                payload={
                    "task_type": task.type.value,
                    "started_at": task.started_at
                },
                trace_id=task.trace_id
            )
            
            logger.info(f"⚙️ Executing task {task.task_id}...")
            
            task_description = self._map_task_to_description(task)
            
            result = await self.ops_agent.execute_task(
                task=task_description,
                priority=task.priority.value.lower(),
                context={
                    "task_id": task.task_id,
                    "payload": task.payload,
                    "trace_id": task.trace_id
                }
            )
            
            if result.get('success'):
                task.mark_completed()
                task.metadata['result'] = result.get('result', {})
                
                if self.agent_id:
                    tokens_used = result.get('tokens_used', 1000)
                    cost_usd = self.cost_tracker.estimate_cost(tokens_used)
                    self.cost_tracker.track_usage(
                        trace_id=task.trace_id,
                        tokens=tokens_used,
                        cost_usd=cost_usd,
                        model='gpt-4',
                        operation=task.type.value
                    )
                    
                    self.reputation_engine.record_event(
                        self.agent_id,
                        'task_success',
                        trace_id=task.trace_id,
                        reason=f"Successfully completed {task.type.value} task",
                        metadata={'task_id': task.task_id, 'task_type': task.type.value}
                    )
                    logger.info(f"✅ Recorded reputation event: task_success")
                
                await self.queue.update_task(task)
                
                await self.queue.publish_event(
                    event_type="task.completed",
                    source_agent="ops",
                    task_id=task.task_id,
                    payload={
                        "task_type": task.type.value,
                        "completed_at": task.completed_at,
                        "result": result.get('result', {})
                    },
                    trace_id=task.trace_id
                )
                
                logger.info(f"✅ Task {task.task_id} completed successfully")
            else:
                error = result.get('error', 'Unknown error')
                task.mark_failed(error)
                
                if self.agent_id:
                    self.reputation_engine.record_event(
                        self.agent_id,
                        'task_failure',
                        trace_id=task.trace_id,
                        reason=f"Task failed: {error}",
                        metadata={'task_id': task.task_id, 'task_type': task.type.value}
                    )
                
                await self.queue.update_task(task)
                
                await self.queue.publish_event(
                    event_type="task.failed",
                    source_agent="ops",
                    task_id=task.task_id,
                    payload={
                        "task_type": task.type.value,
                        "error": error
                    },
                    trace_id=task.trace_id
                )
                
                logger.error(f"❌ Task {task.task_id} failed: {error}")
        
        except Exception as e:
            logger.error(f"Exception executing task {task.task_id}: {e}")
            
            task.mark_failed(str(e))
            
            if self.agent_id:
                self.reputation_engine.record_event(
                    self.agent_id,
                    'task_failure',
                    trace_id=task.trace_id,
                    reason=f"Exception: {str(e)}",
                    metadata={'task_id': task.task_id, 'task_type': task.type.value}
                )
            
            await self.queue.update_task(task)
            
            await self.queue.publish_event(
                event_type="task.failed",
                source_agent="ops",
                task_id=task.task_id,
                payload={
                    "task_type": task.type.value,
                    "error": str(e)
                },
                trace_id=task.trace_id
            )
    
    def _map_task_to_operation(self, task: UnifiedTask) -> str:
        """
        Map UnifiedTask to governance operation name
        
        Args:
            task: UnifiedTask
        
        Returns:
            str: Operation name for permission checking
        """
        task_type = task.type.value
        payload = task.payload
        
        if task_type == "deploy":
            environment = payload.get("environment", "production")
            if environment == "production":
                return "deploy_prod"
            elif environment == "staging":
                return "deploy_staging"
            else:
                return "deploy_sandbox"
        
        elif task_type == "monitor":
            return "monitor_system"
        
        elif task_type == "alert":
            return "manage_alerts"
        
        elif task_type == "investigate":
            return "investigate_issues"
        
        else:
            return "execute_task"
    
    def _map_task_to_description(self, task: UnifiedTask) -> str:
        """
        Map UnifiedTask to Ops Agent task description
        
        Args:
            task: UnifiedTask
        
        Returns:
            str: Task description for Ops Agent
        """
        task_type = task.type.value
        payload = task.payload
        
        if task_type == "deploy":
            project = payload.get("project", "morningai")
            environment = payload.get("environment", "production")
            return f"Deploy {project} to {environment}"
        
        elif task_type == "monitor":
            service = payload.get("service", "system")
            return f"Monitor {service} metrics and health"
        
        elif task_type == "alert":
            alert_type = payload.get("alert_type", "system")
            return f"Manage {alert_type} alert"
        
        elif task_type == "investigate":
            issue = payload.get("issue", "system issue")
            return f"Troubleshoot and investigate {issue}"
        
        else:
            return f"Execute {task_type} task: {payload.get('description', 'No description')}"
    
    async def _event_listener(self):
        """Listen for events from other agents"""
        try:
            logger.info("Starting event listener...")
            await self.queue.start_event_listener()
        except asyncio.CancelledError:
            logger.info("Event listener cancelled")
        except Exception as e:
            logger.error(f"Event listener error: {e}")


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Ops Agent Worker - Orchestrator Integration")
    logger.info("=" * 60)
    
    worker = OpsAgentWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal")
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
