#!/usr/bin/env python3
"""
Redis Queue and Event Bus for Multi-Agent Orchestration
Handles task queuing and event pub/sub
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
import redis.asyncio as redis
from datetime import datetime, timezone

from orchestrator.schemas.task_schema import UnifiedTask, TaskStatus, TaskPriority
from orchestrator.schemas.event_schema import AgentEvent, EventType

logger = logging.getLogger(__name__)


class RedisQueue:
    """Redis-based task queue and event bus"""
    
    TASK_QUEUE_KEY = "orchestrator:tasks"
    TASK_PROCESSING_KEY = "orchestrator:tasks:processing"
    EVENT_CHANNEL_PREFIX = "orchestrator:events:"
    TASK_STORAGE_PREFIX = "orchestrator:task:"
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db: int = 0
    ):
        """
        Initialize Redis Queue
        
        Args:
            redis_url: Redis connection URL
            db: Redis database number
        """
        self.redis_url = redis_url
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.is_running = False
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def close(self):
        """Alias for disconnect() for compatibility"""
        await self.disconnect()
    
    async def enqueue_task(self, task: UnifiedTask, publish_events: bool = True) -> bool:
        """
        Add task to queue
        
        Args:
            task: UnifiedTask to enqueue
        
        Returns:
            bool: True if successful
        """
        try:
            task_data = json.dumps(task.to_dict())
            priority_score = self._get_priority_score(task.priority.value if isinstance(task.priority, TaskPriority) else task.priority)
            
            pipeline = self.redis_client.pipeline()
            pipeline.hset(
                f"{self.TASK_STORAGE_PREFIX}{task.task_id}",
                mapping={
                    "data": task_data,
                    "status": task.status.value if hasattr(task.status, 'value') else task.status,
                    "created_at": task.created_at,
                    "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority
                }
            )
            pipeline.zadd(
                self.TASK_QUEUE_KEY,
                {task.task_id: priority_score}
            )
            await pipeline.execute()
            
            logger.info(f"Enqueued task {task.task_id} with priority {task.priority.value if hasattr(task.priority, 'value') else task.priority}")
            
            if publish_events:
                await self.publish_event(
                    event_type="task.created",
                    source_agent="orchestrator",
                    task_id=task.task_id,
                    payload={
                        "task_type": task.type.value if hasattr(task.type, 'value') else task.type,
                        "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                        "assigned_to": task.assigned_to
                    },
                    trace_id=task.trace_id
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.task_id}: {e}")
            return False
    
    async def dequeue_task(self) -> Optional[UnifiedTask]:
        """
        Get next task from queue (highest priority first)
        
        Returns:
            UnifiedTask or None
        """
        try:
            result = await self.redis_client.zpopmin(self.TASK_QUEUE_KEY, 1)
            
            if not result:
                return None
            
            task_id, _ = result[0]
            
            task_data = await self.redis_client.hget(
                f"{self.TASK_STORAGE_PREFIX}{task_id}",
                "data"
            )
            
            if not task_data:
                logger.warning(f"Task {task_id} not found in storage")
                return None
            
            task = UnifiedTask.from_dict(json.loads(task_data))
            
            await self.redis_client.sadd(self.TASK_PROCESSING_KEY, task_id)
            
            logger.info(f"Dequeued task {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None
    
    async def get_task(self, task_id: str) -> Optional[UnifiedTask]:
        """Get task by ID"""
        try:
            task_data = await self.redis_client.hget(
                f"{self.TASK_STORAGE_PREFIX}{task_id}",
                "data"
            )
            
            if not task_data:
                return None
            
            return UnifiedTask.from_dict(json.loads(task_data))
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def update_task(self, task: UnifiedTask) -> bool:
        """Update task in storage"""
        try:
            task_data = json.dumps(task.to_dict())
            
            await self.redis_client.hset(
                f"{self.TASK_STORAGE_PREFIX}{task.task_id}",
                mapping={
                    "data": task_data,
                    "status": task.status.value,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                await self.redis_client.srem(self.TASK_PROCESSING_KEY, task.task_id)
            
            logger.info(f"Updated task {task.task_id} status to {task.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task {task.task_id}: {e}")
            return False
    
    async def publish_event(
        self,
        event_type: str,
        source_agent: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        priority: str = "medium"
    ) -> bool:
        """
        Publish event to event bus
        
        Args:
            event_type: Type of event (e.g., 'task.created', 'deploy.started')
            source_agent: Agent that published the event
            payload: Event payload
            task_id: Related task ID
            trace_id: Trace ID for correlation
            priority: Event priority
        
        Returns:
            bool: True if successful
        """
        try:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                event_type_enum = None
                for et in EventType:
                    if et.value == event_type:
                        event_type_enum = et
                        break
                if event_type_enum is None:
                    logger.error(f"Unknown event type '{event_type}', defaulting to TASK_CREATED. Valid types: {[e.value for e in EventType]}")
                    event_type_enum = EventType.TASK_CREATED
            
            event = AgentEvent(
                event_type=event_type_enum,
                source_agent=source_agent,
                task_id=task_id,
                trace_id=trace_id,
                payload=payload
            )
            
            event_data = json.dumps(event.to_dict())
            
            channel = f"{self.EVENT_CHANNEL_PREFIX}{event_type}"
            await self.redis_client.publish(channel, event_data)
            
            wildcard_channel = f"{self.EVENT_CHANNEL_PREFIX}*"
            await self.redis_client.publish(wildcard_channel, event_data)
            
            logger.debug(f"Published event {event_type} from {source_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """
        Register a handler for specific event type
        
        Args:
            event_type: Event type to handle (e.g., 'task.created', '*' for all)
            handler: Async function to call when event is received
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")
    
    async def subscribe_to_events(self, event_types: List[str], handler: Optional[Callable] = None):
        """
        Subscribe to specific event types
        
        Args:
            event_types: List of event types to subscribe to
            handler: Optional event handler function to register for these event types
        """
        try:
            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()
            
            channels = [f"{self.EVENT_CHANNEL_PREFIX}{et}" for et in event_types]
            await self.pubsub.subscribe(*channels)
            
            logger.info(f"Subscribed to events: {event_types}")
            
            if handler:
                for event_type in event_types:
                    self.register_event_handler(event_type, handler)
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            raise
    
    async def start_event_listener(self):
        """Start listening for events"""
        self.is_running = True
        
        try:
            async for message in self.pubsub.listen():
                if not self.is_running:
                    break
                
                if message['type'] != 'message':
                    continue
                
                try:
                    event_data = json.loads(message['data'])
                    event = AgentEvent.from_dict(event_data)
                    
                    await self._handle_event(event)
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Event listener cancelled")
        finally:
            self.is_running = False
    
    async def stop_event_listener(self):
        """Stop event listener"""
        self.is_running = False
    
    async def _handle_event(self, event: AgentEvent):
        """Handle received event"""
        event_type = event.event_type.value
        
        handlers = self.event_handlers.get(event_type, [])
        all_handlers = self.event_handlers.get('*', [])
        
        for handler in handlers + all_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")
    
    def _get_priority_score(self, priority: str) -> float:
        """Get numeric score for priority (lower = higher priority)"""
        priority_scores = {
            "P0": 1.0,
            "P1": 2.0,
            "P2": 3.0,
            "P3": 4.0
        }
        return priority_scores.get(priority, 3.0)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            pending_count = await self.redis_client.zcard(self.TASK_QUEUE_KEY)
            processing_count = await self.redis_client.scard(self.TASK_PROCESSING_KEY)
            
            return {
                "pending_tasks": pending_count,
                "processing_tasks": processing_count,
                "total_tasks": pending_count + processing_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}


async def create_redis_queue(redis_url: str = "redis://localhost:6379") -> RedisQueue:
    """Factory function to create and connect Redis queue"""
    queue = RedisQueue(redis_url=redis_url)
    await queue.connect()
    return queue
