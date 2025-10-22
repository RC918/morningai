#!/usr/bin/env python3
"""
Task Router - Routes tasks to appropriate agents
"""
import logging
from typing import Dict, Any

from orchestrator.schemas.task_schema import UnifiedTask, TaskType
from orchestrator.task_queue.redis_queue import RedisQueue

logger = logging.getLogger(__name__)


class OrchestratorRouter:
    """Routes tasks to appropriate agents based on task type"""
    
    def __init__(self, redis_queue: RedisQueue):
        """
        Initialize router
        
        Args:
            redis_queue: Redis queue instance for publishing routing events
        """
        self.redis_queue = redis_queue
        
        self.routing_rules = {
            TaskType.FAQ: "faq_agent",
            TaskType.KB_UPDATE: "faq_agent",
            
            TaskType.BUGFIX: "dev_agent",
            TaskType.REFACTOR: "dev_agent",
            TaskType.FEATURE: "dev_agent",
            TaskType.INVESTIGATE: "dev_agent",
            
            TaskType.DEPLOY: "ops_agent",
            TaskType.MONITOR: "ops_agent",
            TaskType.ALERT: "ops_agent",
        }
    
    def route_task(self, task: UnifiedTask) -> str:
        """
        Route task to appropriate agent
        
        Args:
            task: UnifiedTask to route
        
        Returns:
            str: Agent name to handle the task
        """
        agent = self.routing_rules.get(task.type, "dev_agent")
        
        logger.info(f"Routing task {task.task_id} (type={task.type.value}) to {agent}")
        
        return agent
    
    def register_custom_rule(self, task_type: TaskType, agent: str):
        """
        Register a custom routing rule
        
        Args:
            task_type: TaskType to route
            agent: Agent name to route to
        """
        self.routing_rules[task_type] = agent
        logger.info(f"Registered custom routing rule: {task_type.value} -> {agent}")
    
    def get_routing_rules(self) -> Dict[str, str]:
        """Get all routing rules"""
        return {
            task_type.value: agent
            for task_type, agent in self.routing_rules.items()
        }
