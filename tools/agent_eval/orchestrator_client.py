#!/usr/bin/env python3
"""
Orchestrator Client for Agent Evaluation

Provides interface to submit tasks to the orchestrator and monitor execution.
"""

import time
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from redis import Redis, ConnectionError as RedisConnectionError
from redis.retry import Retry as RedisRetry
from redis.backoff import ExponentialBackoff

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """Client for interacting with the orchestrator via Redis."""
    
    def __init__(self, redis_url: str, queue_name: str = "orchestrator"):
        """
        Initialize orchestrator client.
        
        Args:
            redis_url: Redis connection URL
            queue_name: RQ queue name (default: orchestrator)
        """
        self.redis_url = redis_url
        self.queue_name = queue_name
        
        redis_retry = RedisRetry(ExponentialBackoff(base=1, cap=10), retries=5)
        self.redis = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=10,
            retry=redis_retry,
            retry_on_timeout=True
        )
        
        logger.info(f"Orchestrator client initialized", extra={
            "redis_url": redis_url[:30] + "...",
            "queue_name": queue_name
        })
    
    def submit_task(
        self,
        task_id: str,
        description: str,
        repo: str,
        timeout: int = 600
    ) -> bool:
        """
        Submit a task to the orchestrator.
        
        Args:
            task_id: Unique task identifier
            description: Task description/question
            repo: GitHub repository (owner/repo format)
            timeout: Task timeout in seconds (default: 600)
        
        Returns:
            bool: True if submission successful, False otherwise
        """
        try:
            from rq import Queue
            from rq.serializers import JSONSerializer
            
            redis_client_rq = Redis.from_url(
                self.redis_url,
                decode_responses=False,
                socket_connect_timeout=10
            )
            q = Queue(self.queue_name, connection=redis_client_rq, serializer=JSONSerializer())
            
            job = q.enqueue(
                'redis_queue.worker.run_orchestrator_task',
                task_id,
                description,
                repo,
                job_id=task_id,
                ttl=timeout,
                result_ttl=86400,
                failure_ttl=3600
            )
            
            logger.info(f"Task submitted to orchestrator", extra={
                "task_id": task_id,
                "job_id": job.id,
                "description": description[:50]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}", extra={
                "task_id": task_id,
                "error": str(e)
            })
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Get current task status from Redis.
        
        Args:
            task_id: Task identifier
        
        Returns:
            dict: Task status data or None if not found
        """
        try:
            redis_key = f"agent:task:{task_id}"
            data = self.redis.hgetall(redis_key)
            
            if not data:
                return None
            
            return {
                "status": data.get("status", "unknown"),
                "question": data.get("question", ""),
                "trace_id": data.get("trace_id", task_id),
                "job_id": data.get("job_id", ""),
                "pr_url": data.get("pr_url", ""),
                "ci_state": data.get("ci_state", "unknown"),
                "updated_at": data.get("updated_at", ""),
                "error": data.get("error", "")
            }
            
        except RedisConnectionError as e:
            logger.error(f"Redis connection error: {e}", extra={"task_id": task_id})
            return None
        except Exception as e:
            logger.error(f"Failed to get task status: {e}", extra={"task_id": task_id})
            return None
    
    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 600,
        poll_interval: int = 10
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Wait for task to complete, polling status periodically.
        
        Args:
            task_id: Task identifier
            timeout: Maximum wait time in seconds (default: 600)
            poll_interval: Status check interval in seconds (default: 10)
        
        Returns:
            tuple: (success: bool, result: dict or None)
        """
        start_time = time.time()
        last_status = None
        
        logger.info(f"Waiting for task completion", extra={
            "task_id": task_id,
            "timeout": timeout,
            "poll_interval": poll_interval
        })
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            if status and status["status"] != last_status:
                logger.info(f"Task status update", extra={
                    "task_id": task_id,
                    "status": status["status"],
                    "elapsed": int(time.time() - start_time)
                })
                last_status = status["status"]
            
            if status and status["status"] in ["done", "failed", "error"]:
                elapsed = time.time() - start_time
                logger.info(f"Task completed", extra={
                    "task_id": task_id,
                    "status": status["status"],
                    "elapsed": int(elapsed),
                    "pr_url": status.get("pr_url", "")
                })
                
                return (status["status"] == "done", status)
            
            time.sleep(poll_interval)
        
        elapsed = time.time() - start_time
        logger.warning(f"Task timeout", extra={
            "task_id": task_id,
            "timeout": timeout,
            "elapsed": int(elapsed)
        })
        
        return (False, {"status": "timeout", "error": f"Task exceeded timeout of {timeout}s"})
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        Get final task result.
        
        Args:
            task_id: Task identifier
        
        Returns:
            dict: Task result or None if not available
        """
        status = self.get_task_status(task_id)
        
        if not status:
            return None
        
        return {
            "task_id": task_id,
            "status": status["status"],
            "pr_url": status.get("pr_url", ""),
            "ci_state": status.get("ci_state", "unknown"),
            "trace_id": status.get("trace_id", task_id),
            "error": status.get("error", "")
        }
    
    def cleanup_task(self, task_id: str):
        """
        Clean up task data from Redis.
        
        Args:
            task_id: Task identifier
        """
        try:
            redis_key = f"agent:task:{task_id}"
            self.redis.delete(redis_key)
            logger.debug(f"Cleaned up task data", extra={"task_id": task_id})
        except Exception as e:
            logger.warning(f"Failed to cleanup task: {e}", extra={"task_id": task_id})


class MockOrchestratorClient(OrchestratorClient):
    """Mock orchestrator client for testing without Redis."""
    
    def __init__(self):
        """Initialize mock client without Redis connection."""
        self.redis_url = "mock://localhost"
        self.queue_name = "orchestrator"
        self.tasks = {}
        
        logger.info("Mock orchestrator client initialized")
    
    def submit_task(
        self,
        task_id: str,
        description: str,
        repo: str,
        timeout: int = 600
    ) -> bool:
        """Mock task submission."""
        self.tasks[task_id] = {
            "status": "running",
            "description": description,
            "repo": repo,
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Mock task submitted", extra={"task_id": task_id})
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Mock task status retrieval."""
        if task_id not in self.tasks:
            return None
        
        return {
            "status": self.tasks[task_id]["status"],
            "question": self.tasks[task_id]["description"],
            "trace_id": task_id,
            "job_id": f"mock-job-{task_id}",
            "pr_url": f"https://github.com/mock/repo/pull/{hash(task_id) % 1000}",
            "ci_state": "success",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "error": ""
        }
    
    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 600,
        poll_interval: int = 10
    ) -> Tuple[bool, Optional[Dict]]:
        """Mock task completion wait."""
        if task_id not in self.tasks:
            return (False, None)
        
        time.sleep(2)
        
        self.tasks[task_id]["status"] = "done"
        
        result = self.get_task_status(task_id)
        return (True, result)
    
    def cleanup_task(self, task_id: str):
        """Mock task cleanup."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.debug(f"Mock task cleaned up", extra={"task_id": task_id})
