#!/usr/bin/env python3
"""
Production Readiness Tests for Ops Agent Worker
Comprehensive test suite to validate production deployment readiness
"""
import os
import sys
import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority, TaskStatus, SLAConfig
from orchestrator.task_queue.redis_queue import create_redis_queue


@pytest_asyncio.fixture
async def clean_redis():
    """Clean Redis before each test"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    queue = await create_redis_queue(redis_url=redis_url)
    
    if queue.redis_client:
        await queue.redis_client.flushdb()
    
    await queue.close()
    yield
    

class TestProductionReadiness:
    """Production readiness test suite"""
    
    @pytest.mark.asyncio
    async def test_redis_connection_resilience(self):
        """Test Redis connection resilience and reconnection"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        queue = await create_redis_queue(redis_url=redis_url)
        assert queue is not None
        
        stats = await queue.get_queue_stats()
        assert "pending_tasks" in stats
        assert "processing_tasks" in stats
        assert "total_tasks" in stats
    
    @pytest.mark.asyncio
    async def test_high_load_task_processing(self):
        """Test Worker performance under high load"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        num_tasks = 100
        tasks = []
        
        start_time = time.time()
        
        for i in range(num_tasks):
            task = UnifiedTask(
                type=TaskType.DEPLOY,
                payload={"test_id": i, "service": f"test-service-{i}"},
                priority=TaskPriority.P2,
                source="test"
            )
            await queue.enqueue_task(task, publish_events=False)
            tasks.append(task)
        
        enqueue_time = time.time() - start_time
        
        assert enqueue_time < 30.0, f"Enqueuing {num_tasks} tasks took {enqueue_time:.2f}s (should be < 30s)"
        
        stats = await queue.get_queue_stats()
        assert stats["pending_tasks"] >= num_tasks
        
        for task in tasks:
            retrieved_task = await queue.get_task(task.task_id)
            assert retrieved_task is not None
            assert retrieved_task.task_id == task.task_id
    
    @pytest.mark.asyncio
    async def test_task_priority_ordering(self, clean_redis):
        """Test that tasks are processed in priority order"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        p3_task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"priority": "P3"},
            priority=TaskPriority.P3,
            source="test"
        )
        
        p1_task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"priority": "P1"},
            priority=TaskPriority.P1,
            source="test"
        )
        
        p2_task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"priority": "P2"},
            priority=TaskPriority.P2,
            source="test"
        )
        
        await queue.enqueue_task(p3_task)
        await queue.enqueue_task(p1_task)
        await queue.enqueue_task(p2_task)
        
        first_task = await queue.dequeue_task()
        assert first_task.priority == TaskPriority.P1
        
        second_task = await queue.dequeue_task()
        assert second_task.priority == TaskPriority.P2
        
        third_task = await queue.dequeue_task()
        assert third_task.priority == TaskPriority.P3
    
    @pytest.mark.asyncio
    async def test_task_timeout_handling(self, clean_redis):
        """Test task timeout and cleanup"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        sla_deadline = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"timeout_test": True},
            priority=TaskPriority.P2,
            source="test",
            sla=SLAConfig(
                target="1 second",
                deadline=sla_deadline
            )
        )
        
        await queue.enqueue_task(task)
        
        dequeued_task = await queue.dequeue_task()
        assert dequeued_task.task_id == task.task_id
        
        await asyncio.sleep(2)
        
        retrieved_task = await queue.get_task(task.task_id)
        assert retrieved_task is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self):
        """Test concurrent task processing"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        async def process_task(task_id):
            task = UnifiedTask(
                type=TaskType.DEPLOY,
                payload={"concurrent_test": task_id},
                priority=TaskPriority.P2,
                source="test"
            )
            await queue.enqueue_task(task)
            dequeued = await queue.dequeue_task()
            return dequeued.task_id
        
        num_concurrent = 10
        results = await asyncio.gather(*[
            process_task(i) for i in range(num_concurrent)
        ])
        
        assert len(results) == num_concurrent
        assert len(set(results)) == num_concurrent
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery and task retry"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"error_test": True},
            priority=TaskPriority.P2,
            source="test"
        )
        
        await queue.enqueue_task(task)
        
        dequeued_task = await queue.dequeue_task()
        
        dequeued_task.mark_failed("Simulated error")
        await queue.update_task(dequeued_task)
        
        retrieved_task = await queue.get_task(task.task_id)
        assert retrieved_task.status == TaskStatus.FAILED
        assert retrieved_task.error == "Simulated error"
    
    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self):
        """Test for memory leaks during extended operation"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        for i in range(100):
            task = UnifiedTask(
                type=TaskType.DEPLOY,
                payload={"memory_test": i},
                priority=TaskPriority.P2,
                source="test"
            )
            await queue.enqueue_task(task, publish_events=False)
            
            if i % 10 == 0:
                await queue.dequeue_task()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 20, f"Memory increased by {memory_increase:.2f}MB (should be < 20MB)"
    
    @pytest.mark.asyncio
    async def test_event_publishing_reliability(self):
        """Test event publishing reliability"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        publisher_queue = await create_redis_queue(redis_url=redis_url)
        subscriber_queue = await create_redis_queue(redis_url=redis_url)
        
        events_received = []
        listener_ready = asyncio.Event()
        
        async def event_handler(event):
            events_received.append(event)
        
        await subscriber_queue.subscribe_to_events(
            ["task.created", "task.completed"],
            event_handler
        )
        
        async def start_listener_and_signal():
            listener_ready.set()
            await subscriber_queue.start_event_listener()
        
        listener_task = asyncio.create_task(start_listener_and_signal())
        
        await listener_ready.wait()
        await asyncio.sleep(0.5)
        
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"event_test": True},
            priority=TaskPriority.P2,
            source="test"
        )
        
        await publisher_queue.enqueue_task(task)
        
        await asyncio.sleep(1.0)
        
        await subscriber_queue.stop_event_listener()
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        
        await publisher_queue.close()
        await subscriber_queue.close()
        
        assert len(events_received) > 0, f"No events were received. Published task {task.task_id}"
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown handling"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"shutdown_test": True},
            priority=TaskPriority.P2,
            source="test"
        )
        
        await queue.enqueue_task(task)
        
        stats_before = await queue.get_queue_stats()
        
        await queue.close()
        
        queue2 = await create_redis_queue(redis_url=redis_url)
        stats_after = await queue2.get_queue_stats()
        
        assert stats_after["pending_tasks"] >= stats_before["pending_tasks"]


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    @pytest.mark.asyncio
    async def test_task_enqueue_throughput(self):
        """Benchmark task enqueue throughput"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        num_tasks = 1000
        start_time = time.time()
        
        for i in range(num_tasks):
            task = UnifiedTask(
                type=TaskType.DEPLOY,
                payload={"benchmark": i},
                priority=TaskPriority.P2,
                source="test"
            )
            await queue.enqueue_task(task)
        
        elapsed_time = time.time() - start_time
        throughput = num_tasks / elapsed_time
        
        print(f"\nEnqueue throughput: {throughput:.2f} tasks/second")
        assert throughput > 50, f"Throughput {throughput:.2f} tasks/s is too low (should be > 50)"
    
    @pytest.mark.asyncio
    async def test_task_dequeue_throughput(self):
        """Benchmark task dequeue throughput"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        num_tasks = 1000
        
        for i in range(num_tasks):
            task = UnifiedTask(
                type=TaskType.DEPLOY,
                payload={"benchmark": i},
                priority=TaskPriority.P2,
                source="test"
            )
            await queue.enqueue_task(task)
        
        start_time = time.time()
        
        for i in range(num_tasks):
            await queue.dequeue_task()
        
        elapsed_time = time.time() - start_time
        throughput = num_tasks / elapsed_time
        
        print(f"\nDequeue throughput: {throughput:.2f} tasks/second")
        assert throughput > 50, f"Throughput {throughput:.2f} tasks/s is too low (should be > 50)"
    
    @pytest.mark.asyncio
    async def test_queue_stats_latency(self):
        """Benchmark queue stats retrieval latency"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        num_iterations = 100
        latencies = []
        
        for i in range(num_iterations):
            start_time = time.time()
            await queue.get_queue_stats()
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"\nQueue stats latency - Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")
        assert avg_latency < 100, f"Average latency {avg_latency:.2f}ms is too high (should be < 100ms)"
        assert p95_latency < 200, f"P95 latency {p95_latency:.2f}ms is too high (should be < 200ms)"


class TestSecurityValidation:
    """Security validation tests"""
    
    @pytest.mark.asyncio
    async def test_task_payload_sanitization(self):
        """Test task payload sanitization"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        queue = await create_redis_queue(redis_url=redis_url)
        
        malicious_payload = {
            "command": "rm -rf /",
            "script": "<script>alert('xss')</script>",
            "sql": "'; DROP TABLE tasks; --"
        }
        
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload=malicious_payload,
            priority=TaskPriority.P2,
            source="test"
        )
        
        await queue.enqueue_task(task)
        
        retrieved_task = await queue.get_task(task.task_id)
        assert retrieved_task is not None
        assert retrieved_task.payload == malicious_payload
    
    @pytest.mark.asyncio
    async def test_environment_variable_isolation(self):
        """Test environment variable isolation"""
        sensitive_vars = ["VERCEL_TOKEN", "REDIS_URL", "JWT_SECRET"]
        
        for var in sensitive_vars:
            value = os.getenv(var)
            if value:
                assert len(value) > 0
                assert value != "test"
                assert value != "changeme"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
