#!/usr/bin/env python3
"""
HITL (Human-In-The-Loop) Gate
Provides manual approval gates for critical operations
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

from orchestrator.schemas.task_schema import UnifiedTask, TaskPriority, TaskType

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class HITLGate:
    """Human-In-The-Loop gate for critical operations with Redis persistence"""
    
    CRITICAL_TASK_TYPES = [
        TaskType.DEPLOY,
        TaskType.FEATURE,
        TaskType.REFACTOR
    ]
    
    P0_P1_PRIORITIES = [
        TaskPriority.P0,
        TaskPriority.P1
    ]
    
    PENDING_KEY_PREFIX = "hitl:pending:"
    HISTORY_KEY_PREFIX = "hitl:history:"
    HISTORY_LIST_KEY = "hitl:history:list"
    
    def __init__(self, redis_queue=None):
        """
        Initialize HITL gate with Redis persistence
        
        Args:
            redis_queue: RedisQueue instance for persistence (optional)
        """
        self.redis_queue = redis_queue
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_history: List[Dict[str, Any]] = []
    
    def requires_approval(self, task: UnifiedTask) -> bool:
        """
        Check if task requires manual approval
        
        Approval required for:
        - P0/P1 priority tasks
        - Deploy tasks
        - Feature/Refactor tasks in production
        
        Args:
            task: UnifiedTask to check
        
        Returns:
            bool: True if approval required
        """
        if task.priority in self.P0_P1_PRIORITIES:
            return True
        
        if task.type in self.CRITICAL_TASK_TYPES:
            target_env = task.payload.get('environment', 'production')
            if target_env == 'production':
                return True
        
        feature_flag_change = task.metadata.get('feature_flag_change', False)
        if feature_flag_change:
            return True
        
        return False
    
    async def request_approval(
        self,
        task: UnifiedTask,
        reason: str,
        approver: Optional[str] = None
    ) -> str:
        """
        Request manual approval for a task
        
        Args:
            task: UnifiedTask requiring approval
            reason: Reason for approval requirement
            approver: Optional specific approver
        
        Returns:
            str: Approval request ID
        """
        approval_id = f"approval_{task.task_id}"
        
        approval_request = {
            "approval_id": approval_id,
            "task_id": task.task_id,
            "task_type": task.type.value,
            "priority": task.priority.value,
            "reason": reason,
            "approver": approver,
            "status": ApprovalStatus.PENDING.value,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": None,
            "approved_by": None
        }
        
        self.pending_approvals[approval_id] = approval_request
        
        if self.redis_queue and self.redis_queue.redis_client:
            try:
                redis_key = f"{self.PENDING_KEY_PREFIX}{approval_id}"
                await self.redis_queue.redis_client.set(
                    redis_key,
                    json.dumps(approval_request),
                    ex=86400
                )
                logger.debug(f"Persisted approval {approval_id} to Redis")
            except Exception as e:
                logger.error(f"Failed to persist approval to Redis: {e}")
        
        logger.info(f"Approval requested for task {task.task_id}: {reason}")
        
        return approval_id
    
    async def approve(self, approval_id: str, approver: str) -> bool:
        """
        Approve a pending request
        
        Args:
            approval_id: Approval request ID
            approver: Person approving
        
        Returns:
            bool: True if successful
        """
        if approval_id not in self.pending_approvals:
            logger.warning(f"Approval {approval_id} not found")
            return False
        
        approval = self.pending_approvals[approval_id]
        approval["status"] = ApprovalStatus.APPROVED.value
        approval["approved_at"] = datetime.now(timezone.utc).isoformat()
        approval["approved_by"] = approver
        
        self.approval_history.append(approval.copy())
        del self.pending_approvals[approval_id]
        
        if self.redis_queue and self.redis_queue.redis_client:
            try:
                pending_key = f"{self.PENDING_KEY_PREFIX}{approval_id}"
                await self.redis_queue.redis_client.delete(pending_key)
                
                history_key = f"{self.HISTORY_KEY_PREFIX}{approval_id}"
                await self.redis_queue.redis_client.set(
                    history_key,
                    json.dumps(approval),
                    ex=2592000
                )
                
                await self.redis_queue.redis_client.lpush(
                    self.HISTORY_LIST_KEY,
                    approval_id
                )
                await self.redis_queue.redis_client.ltrim(self.HISTORY_LIST_KEY, 0, 999)
                
                logger.debug(f"Persisted approval history for {approval_id} to Redis")
            except Exception as e:
                logger.error(f"Failed to persist approval history to Redis: {e}")
        
        logger.info(f"Approval {approval_id} approved by {approver}")
        
        return True
    
    async def reject(self, approval_id: str, approver: str, reason: Optional[str] = None) -> bool:
        """
        Reject a pending request
        
        Args:
            approval_id: Approval request ID
            approver: Person rejecting
            reason: Rejection reason
        
        Returns:
            bool: True if successful
        """
        if approval_id not in self.pending_approvals:
            logger.warning(f"Approval {approval_id} not found")
            return False
        
        approval = self.pending_approvals[approval_id]
        approval["status"] = ApprovalStatus.REJECTED.value
        approval["approved_at"] = datetime.now(timezone.utc).isoformat()
        approval["approved_by"] = approver
        approval["rejection_reason"] = reason
        
        self.approval_history.append(approval.copy())
        del self.pending_approvals[approval_id]
        
        if self.redis_queue and self.redis_queue.redis_client:
            try:
                pending_key = f"{self.PENDING_KEY_PREFIX}{approval_id}"
                await self.redis_queue.redis_client.delete(pending_key)
                
                history_key = f"{self.HISTORY_KEY_PREFIX}{approval_id}"
                await self.redis_queue.redis_client.set(
                    history_key,
                    json.dumps(approval),
                    ex=2592000
                )
                
                await self.redis_queue.redis_client.lpush(
                    self.HISTORY_LIST_KEY,
                    approval_id
                )
                await self.redis_queue.redis_client.ltrim(self.HISTORY_LIST_KEY, 0, 999)
                
                logger.debug(f"Persisted rejection history for {approval_id} to Redis")
            except Exception as e:
                logger.error(f"Failed to persist rejection history to Redis: {e}")
        
        logger.info(f"Approval {approval_id} rejected by {approver}: {reason}")
        
        return True
    
    async def get_approval_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval status from memory or Redis"""
        if approval_id in self.pending_approvals:
            return self.pending_approvals[approval_id]
        
        for approval in self.approval_history:
            if approval["approval_id"] == approval_id:
                return approval
        
        if self.redis_queue and self.redis_queue.redis_client:
            try:
                pending_key = f"{self.PENDING_KEY_PREFIX}{approval_id}"
                pending_data = await self.redis_queue.redis_client.get(pending_key)
                if pending_data:
                    return json.loads(pending_data)
                
                history_key = f"{self.HISTORY_KEY_PREFIX}{approval_id}"
                history_data = await self.redis_queue.redis_client.get(history_key)
                if history_data:
                    return json.loads(history_data)
            except Exception as e:
                logger.error(f"Failed to get approval status from Redis: {e}")
        
        return None
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approvals from memory and Redis"""
        approvals = list(self.pending_approvals.values())
        
        if self.redis_queue and self.redis_queue.redis_client:
            try:
                keys = []
                async for key in self.redis_queue.redis_client.scan_iter(f"{self.PENDING_KEY_PREFIX}*"):
                    keys.append(key)
                
                for key in keys:
                    data = await self.redis_queue.redis_client.get(key)
                    if data:
                        approval = json.loads(data)
                        if approval["approval_id"] not in self.pending_approvals:
                            approvals.append(approval)
            except Exception as e:
                logger.error(f"Failed to get pending approvals from Redis: {e}")
        
        return approvals
    
    async def get_approval_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get approval history from memory and Redis"""
        history = list(self.approval_history)
        
        if self.redis_queue and self.redis_queue.redis_client:
            try:
                approval_ids = await self.redis_queue.redis_client.lrange(
                    self.HISTORY_LIST_KEY,
                    0,
                    limit - 1
                )
                
                for approval_id in approval_ids:
                    history_key = f"{self.HISTORY_KEY_PREFIX}{approval_id}"
                    data = await self.redis_queue.redis_client.get(history_key)
                    if data:
                        approval = json.loads(data)
                        if approval not in history:
                            history.append(approval)
            except Exception as e:
                logger.error(f"Failed to get approval history from Redis: {e}")
        
        return history[:limit]
