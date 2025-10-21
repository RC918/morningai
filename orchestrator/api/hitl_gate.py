#!/usr/bin/env python3
"""
HITL (Human-In-The-Loop) Gate
Provides manual approval gates for critical operations
"""
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
    """Human-In-The-Loop gate for critical operations"""
    
    CRITICAL_TASK_TYPES = [
        TaskType.DEPLOY,
        TaskType.FEATURE,
        TaskType.REFACTOR
    ]
    
    P0_P1_PRIORITIES = [
        TaskPriority.P0,
        TaskPriority.P1
    ]
    
    def __init__(self):
        """Initialize HITL gate"""
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
    
    def request_approval(
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
        
        logger.info(f"Approval requested for task {task.task_id}: {reason}")
        
        return approval_id
    
    def approve(self, approval_id: str, approver: str) -> bool:
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
        
        logger.info(f"Approval {approval_id} approved by {approver}")
        
        return True
    
    def reject(self, approval_id: str, approver: str, reason: Optional[str] = None) -> bool:
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
        
        logger.info(f"Approval {approval_id} rejected by {approver}: {reason}")
        
        return True
    
    def get_approval_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval status"""
        if approval_id in self.pending_approvals:
            return self.pending_approvals[approval_id]
        
        for approval in self.approval_history:
            if approval["approval_id"] == approval_id:
                return approval
        
        return None
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approvals"""
        return list(self.pending_approvals.values())
