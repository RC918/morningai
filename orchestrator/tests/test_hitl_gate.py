#!/usr/bin/env python3
"""Tests for HITL gate"""
import pytest

from orchestrator.api.hitl_gate import HITLGate, ApprovalStatus
from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority


class TestHITLGate:
    """Test HITLGate"""
    
    @pytest.fixture
    def gate(self):
        """Create HITL gate instance"""
        return HITLGate()
    
    def test_requires_approval_p0(self, gate):
        """Test P0 task requires approval"""
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            priority=TaskPriority.P0
        )
        assert gate.requires_approval(task)
    
    def test_requires_approval_p1(self, gate):
        """Test P1 task requires approval"""
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            priority=TaskPriority.P1
        )
        assert gate.requires_approval(task)
    
    def test_no_approval_p2(self, gate):
        """Test P2 task does not require approval by default"""
        task = UnifiedTask(
            type=TaskType.FAQ,
            priority=TaskPriority.P2
        )
        assert not gate.requires_approval(task)
    
    def test_requires_approval_production_deploy(self, gate):
        """Test production deploy requires approval"""
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            priority=TaskPriority.P2,
            payload={"environment": "production"}
        )
        assert gate.requires_approval(task)
    
    def test_no_approval_staging_deploy(self, gate):
        """Test staging deploy does not require approval"""
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            priority=TaskPriority.P2,
            payload={"environment": "staging"}
        )
        assert not gate.requires_approval(task)
    
    def test_requires_approval_feature_flag(self, gate):
        """Test feature flag change requires approval"""
        task = UnifiedTask(
            type=TaskType.FEATURE,
            priority=TaskPriority.P2,
            metadata={"feature_flag_change": True}
        )
        assert gate.requires_approval(task)
    
    def test_request_approval(self, gate):
        """Test requesting approval"""
        task = UnifiedTask(type=TaskType.DEPLOY, priority=TaskPriority.P0)
        
        approval_id = gate.request_approval(
            task=task,
            reason="P0 production deployment",
            approver="admin"
        )
        
        assert approval_id.startswith("approval_")
        assert approval_id in gate.pending_approvals
        
        approval = gate.pending_approvals[approval_id]
        assert approval["task_id"] == task.task_id
        assert approval["status"] == ApprovalStatus.PENDING.value
    
    def test_approve_request(self, gate):
        """Test approving a request"""
        task = UnifiedTask(type=TaskType.DEPLOY, priority=TaskPriority.P0)
        approval_id = gate.request_approval(task, "Test approval")
        
        result = gate.approve(approval_id, "admin@example.com")
        
        assert result is True
        assert approval_id not in gate.pending_approvals
        assert len(gate.approval_history) == 1
        
        approval = gate.approval_history[0]
        assert approval["status"] == ApprovalStatus.APPROVED.value
        assert approval["approved_by"] == "admin@example.com"
    
    def test_reject_request(self, gate):
        """Test rejecting a request"""
        task = UnifiedTask(type=TaskType.DEPLOY, priority=TaskPriority.P0)
        approval_id = gate.request_approval(task, "Test approval")
        
        result = gate.reject(approval_id, "admin@example.com", "Not ready")
        
        assert result is True
        assert approval_id not in gate.pending_approvals
        
        approval = gate.approval_history[0]
        assert approval["status"] == ApprovalStatus.REJECTED.value
        assert approval["rejection_reason"] == "Not ready"
    
    def test_approve_nonexistent(self, gate):
        """Test approving non-existent request"""
        result = gate.approve("invalid-id", "admin")
        assert result is False
    
    def test_get_approval_status_pending(self, gate):
        """Test getting approval status for pending request"""
        task = UnifiedTask(type=TaskType.DEPLOY, priority=TaskPriority.P0)
        approval_id = gate.request_approval(task, "Test")
        
        status = gate.get_approval_status(approval_id)
        
        assert status is not None
        assert status["status"] == ApprovalStatus.PENDING.value
    
    def test_get_approval_status_approved(self, gate):
        """Test getting approval status for approved request"""
        task = UnifiedTask(type=TaskType.DEPLOY, priority=TaskPriority.P0)
        approval_id = gate.request_approval(task, "Test")
        gate.approve(approval_id, "admin")
        
        status = gate.get_approval_status(approval_id)
        
        assert status is not None
        assert status["status"] == ApprovalStatus.APPROVED.value
    
    def test_get_pending_approvals(self, gate):
        """Test getting all pending approvals"""
        task1 = UnifiedTask(type=TaskType.DEPLOY, priority=TaskPriority.P0)
        task2 = UnifiedTask(type=TaskType.FEATURE, priority=TaskPriority.P1)
        
        gate.request_approval(task1, "Deploy approval")
        gate.request_approval(task2, "Feature approval")
        
        pending = gate.get_pending_approvals()
        
        assert len(pending) == 2
        assert all(a["status"] == ApprovalStatus.PENDING.value for a in pending)
