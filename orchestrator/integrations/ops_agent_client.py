#!/usr/bin/env python3
"""
Ops Agent Integration Client
Connects Ops Agent to the Orchestrator
"""
import logging
import asyncio
from typing import Dict, Any, Optional

from orchestrator import RedisQueue, UnifiedTask, TaskType, create_task
from orchestrator.schemas.event_schema import EventType

logger = logging.getLogger(__name__)


class OpsAgentClient:
    """Client for integrating Ops Agent with Orchestrator"""
    
    def __init__(self, redis_queue: RedisQueue, agent_name: str = "ops_agent"):
        """
        Initialize Ops Agent client
        
        Args:
            redis_queue: RedisQueue instance
            agent_name: Name of this agent
        """
        self.redis_queue = redis_queue
        self.agent_name = agent_name
        self.is_running = False
        
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register handlers for relevant events"""
        self.redis_queue.register_event_handler("deploy.*", self._handle_deploy_event)
        self.redis_queue.register_event_handler("alert.*", self._handle_alert_event)
        self.redis_queue.register_event_handler("pr.merged", self._handle_pr_merged)
    
    async def start(self):
        """Start listening for tasks and events"""
        logger.info(f"{self.agent_name} client started")
        self.is_running = True
        
        await self.redis_queue.subscribe_to_events([
            "deploy.started",
            "deploy.succeeded", 
            "deploy.failed",
            "alert.triggered",
            "pr.merged"
        ])
        
        event_listener = asyncio.create_task(self.redis_queue.start_event_listener())
        task_processor = asyncio.create_task(self._process_tasks())
        
        await asyncio.gather(event_listener, task_processor)
    
    async def stop(self):
        """Stop the client"""
        logger.info(f"{self.agent_name} client stopping")
        self.is_running = False
        await self.redis_queue.stop_event_listener()
    
    async def _process_tasks(self):
        """Process tasks from the queue"""
        while self.is_running:
            try:
                task = await self.redis_queue.dequeue_task()
                
                if not task:
                    await asyncio.sleep(1)
                    continue
                
                if task.assigned_to != self.agent_name:
                    continue
                
                await self._execute_task(task)
                
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: UnifiedTask):
        """Execute a task"""
        logger.info(f"Executing task {task.task_id} (type={task.type.value})")
        
        task.mark_in_progress()
        await self.redis_queue.update_task(task)
        
        try:
            if task.type == TaskType.DEPLOY:
                await self._handle_deploy_task(task)
            elif task.type == TaskType.MONITOR:
                await self._handle_monitor_task(task)
            elif task.type == TaskType.ALERT:
                await self._handle_alert_task(task)
            else:
                logger.warning(f"Unknown task type: {task.type.value}")
                task.mark_failed(f"Unknown task type: {task.type.value}")
                await self.redis_queue.update_task(task)
                return
            
            task.mark_completed()
            await self.redis_queue.update_task(task)
            
            logger.info(f"Task {task.task_id} completed")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.mark_failed(str(e))
            await self.redis_queue.update_task(task)
    
    async def _handle_deploy_task(self, task: UnifiedTask):
        """Handle deployment task"""
        from agents.ops_agent.tools.deployment_tool import create_deployment_tool
        import os
        
        vercel_token = os.getenv("VERCEL_TOKEN")
        if not vercel_token:
            raise ValueError("VERCEL_TOKEN not set")
        
        deployment_tool = create_deployment_tool(token=vercel_token)
        
        project = task.payload.get("project")
        environment = task.payload.get("environment", "production")
        git_branch = task.payload.get("branch")
        
        await self.redis_queue.publish_event(
            event_type="deploy.started",
            source_agent=self.agent_name,
            task_id=task.task_id,
            payload={
                "project": project,
                "environment": environment,
                "branch": git_branch
            },
            trace_id=task.trace_id
        )
        
        result = await deployment_tool.deploy(
            project=project,
            environment=environment,
            git_source={"ref": git_branch} if git_branch else None
        )
        
        if result['success']:
            await self.redis_queue.publish_event(
                event_type="deploy.succeeded",
                source_agent=self.agent_name,
                task_id=task.task_id,
                payload={
                    "deployment_id": result['deployment_id'],
                    "url": result['url']
                },
                trace_id=task.trace_id
            )
        else:
            await self.redis_queue.publish_event(
                event_type="deploy.failed",
                source_agent=self.agent_name,
                task_id=task.task_id,
                payload={"error": result.get('error')},
                trace_id=task.trace_id
            )
            raise Exception(result.get('error', 'Deployment failed'))
    
    async def _handle_monitor_task(self, task: UnifiedTask):
        """Handle monitoring task"""
        from agents.ops_agent.tools.monitoring_tool import create_monitoring_tool
        
        monitoring_tool = create_monitoring_tool()
        
        metrics = await monitoring_tool.get_system_metrics()
        
        if metrics['success']:
            cpu_percent = metrics['metrics']['cpu']['percent']
            memory_percent = metrics['metrics']['memory']['percent']
            
            if cpu_percent > 80 or memory_percent > 90:
                alert_task = create_task(
                    task_type="alert",
                    payload={
                        "severity": "high" if cpu_percent > 90 or memory_percent > 95 else "medium",
                        "message": f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%",
                        "metrics": metrics['metrics']
                    },
                    priority="P1" if cpu_percent > 90 or memory_percent > 95 else "P2",
                    source="ops"
                )
                await self.redis_queue.enqueue_task(alert_task)
    
    async def _handle_alert_task(self, task: UnifiedTask):
        """Handle alert task"""
        from agents.ops_agent.tools.alert_management_tool import create_alert_management_tool
        from agents.ops_agent.tools.notification_service import NotificationService
        import os
        
        notification_service = NotificationService(
            mailtrap_api_token=os.getenv("MAILTRAP_API_TOKEN"),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL")
        )
        
        alert_tool = create_alert_management_tool(
            notification_service=notification_service,
            default_email_recipient=os.getenv("ALERT_EMAIL"),
            default_slack_channel=os.getenv("ALERT_SLACK_CHANNEL")
        )
        
        severity = task.payload.get("severity", "medium")
        message = task.payload.get("message", "Alert triggered")
        
        rule_result = await alert_tool.create_alert_rule(
            name=f"Task {task.task_id} Alert",
            condition=message,
            severity=severity,
            channels=["email", "slack"]
        )
        
        if rule_result['success']:
            await alert_tool.trigger_alert(
                rule_id=rule_result['rule']['id'],
                message=message,
                metadata=task.payload
            )
    
    async def _handle_deploy_event(self, event):
        """Handle deploy events"""
        logger.info(f"Deploy event: {event.event_type.value}")
    
    async def _handle_alert_event(self, event):
        """Handle alert events"""
        logger.info(f"Alert event: {event.event_type.value}")
    
    async def _handle_pr_merged(self, event):
        """Handle PR merged event - trigger deployment"""
        pr_url = event.payload.get("pr_url")
        branch = event.payload.get("branch", "main")
        repo = event.payload.get("repo")
        
        logger.info(f"PR merged: {pr_url}, triggering deployment")
        
        deploy_task = create_task(
            task_type="deploy",
            payload={
                "project": repo,
                "environment": "production",
                "branch": branch,
                "pr_url": pr_url
            },
            priority="P1",
            source="ops",
            trace_id=event.trace_id
        )
        
        await self.redis_queue.enqueue_task(deploy_task)


async def start_ops_agent_client(redis_url: str = "redis://localhost:6379"):
    """Start Ops Agent client"""
    from orchestrator import create_redis_queue
    
    queue = await create_redis_queue(redis_url)
    client = OpsAgentClient(queue)
    
    try:
        await client.start()
    except KeyboardInterrupt:
        await client.stop()
    finally:
        await queue.disconnect()
