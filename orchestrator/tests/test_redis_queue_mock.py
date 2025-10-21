#!/usr/bin/env python3
"""Tests for Redis queue (mocked)"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from orchestrator.queue.redis_queue import RedisQueue
from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority, TaskStatus
from orchestrator.schemas.event_schema import AgentEvent, EventType


class TestRedisQueue:
    """Test RedisQueue with mocked Redis"""
    
    @pytest.fixture
    def queue(self):
        """Create queue with mocked Redis"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        
        queue = RedisQueue()
        queue.redis_client = mock_client
        
        return queue
    
    @pytest.mark.asyncio
    async def test_enqueue_task(self, queue):
        """Test enqueueing a task"""
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            priority=TaskPriority.P1,
            payload={"issue": "123"}
        )
        
        queue.redis_client.hset = AsyncMock()
        queue.redis_client.zadd = AsyncMock()
        queue.redis_client.publish = AsyncMock()
        
        result = await queue.enqueue_task(task)
        
        assert result is True
        queue.redis_client.hset.assert_called_once()
        queue.redis_client.zadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dequeue_task(self, queue):
        """Test dequeueing a task"""
        task = UnifiedTask(
            task_id="task-123",
            type=TaskType.BUGFIX,
            priority=TaskPriority.P1
        )
        
        queue.redis_client.zpopmin = AsyncMock(return_value=[("task-123", 2.0)])
        queue.redis_client.hget = AsyncMock(return_value=json.dumps(task.to_dict()))
        queue.redis_client.sadd = AsyncMock()
        
        result = await queue.dequeue_task()
        
        assert result is not None
        assert result.task_id == "task-123"
        queue.redis_client.zpopmin.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, queue):
        """Test dequeueing from empty queue"""
        queue.redis_client.zpopmin = AsyncMock(return_value=[])
        
        result = await queue.dequeue_task()
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_task(self, queue):
        """Test getting a task by ID"""
        task = UnifiedTask(
            task_id="task-123",
            type=TaskType.BUGFIX
        )
        
        queue.redis_client.hget = AsyncMock(return_value=json.dumps(task.to_dict()))
        
        result = await queue.get_task("task-123")
        
        assert result is not None
        assert result.task_id == "task-123"
    
    @pytest.mark.asyncio
    async def test_update_task(self, queue):
        """Test updating a task"""
        task = UnifiedTask(
            task_id="task-123",
            type=TaskType.BUGFIX
        )
        task.mark_completed()
        
        queue.redis_client.hset = AsyncMock()
        queue.redis_client.srem = AsyncMock()
        
        result = await queue.update_task(task)
        
        assert result is True
        queue.redis_client.hset.assert_called_once()
        queue.redis_client.srem.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_event(self, queue):
        """Test publishing an event"""
        queue.redis_client.publish = AsyncMock()
        
        result = await queue.publish_event(
            event_type="task.created",
            source_agent="dev_agent",
            payload={"task_id": "123"},
            task_id="task-123"
        )
        
        assert result is True
        assert queue.redis_client.publish.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self, queue):
        """Test getting queue statistics"""
        queue.redis_client.zcard = AsyncMock(return_value=5)
        queue.redis_client.scard = AsyncMock(return_value=3)
        
        stats = await queue.get_queue_stats()
        
        assert stats["pending_tasks"] == 5
        assert stats["processing_tasks"] == 3
        assert stats["total_tasks"] == 8
    
    def test_get_priority_score(self, queue):
        """Test priority score calculation"""
        assert queue._get_priority_score("P0") == 1.0
        assert queue._get_priority_score("P1") == 2.0
        assert queue._get_priority_score("P2") == 3.0
        assert queue._get_priority_score("P3") == 4.0
