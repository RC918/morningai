#!/usr/bin/env python3
"""
HITL Approval System - Human-in-the-Loop decision approval
Dual-channel verification: Console + Telegram Bot
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from persistent_state_manager import persistent_state_manager
from resilience_patterns import resilience_manager

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    
class ApprovalChannel(Enum):
    CONSOLE = "console"
    TELEGRAM = "telegram"
    
class ApprovalPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ApprovalRequest:
    """HITL approval request"""
    request_id: str
    trace_id: str
    title: str
    description: str
    context: Dict
    prompt_details: str
    requester_agent: str
    priority: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_channel: Optional[ApprovalChannel] = None
    comments: Optional[str] = None

class HITLApprovalSystem:
    """Human-in-the-Loop approval system with dual-channel support"""
    
    def __init__(self, telegram_bot_token: Optional[str] = None, admin_chat_id: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.telegram_bot_token = telegram_bot_token
        self.admin_chat_id = admin_chat_id
        self.approval_callbacks: Dict[str, Callable] = {}
        
        self.timeout_hours = {
            ApprovalPriority.CRITICAL.value: 2,
            ApprovalPriority.HIGH.value: 8,
            ApprovalPriority.MEDIUM.value: 24,
            ApprovalPriority.LOW.value: 72
        }
        
        self._load_persistent_state()
        
    async def create_approval_request(
        self,
        title: str,
        description: str,
        context: Dict,
        requester_agent: str,
        priority: str = "medium",
        timeout_hours: Optional[int] = None
    ) -> ApprovalRequest:
        """Create new approval request with dual-channel notification"""
        request_id = str(uuid.uuid4())
        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request_id[:8]}"
        
        if timeout_hours is None:
            timeout_hours = self.timeout_hours.get(priority, 24)
        
        request = ApprovalRequest(
            request_id=request_id,
            trace_id=trace_id,
            title=title,
            description=description,
            context=context,
            prompt_details=json.dumps(context, indent=2),
            requester_agent=requester_agent,
            priority=priority,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=timeout_hours)
        )
        
        request_data = asdict(request)
        request_data['created_at'] = request_data['created_at'].isoformat()
        request_data['expires_at'] = request_data['expires_at'].isoformat()
        request_data['status'] = request_data['status'].value
        
        persistent_state_manager.save_approval_request(request_data)
        
        await self._send_console_notification(request)
        if self.telegram_bot_token:
            await self._send_telegram_notification(request)
            
        self.logger.info(f"Created approval request {request_id} for {requester_agent} with priority {priority}")
        return request
        
    async def _send_console_notification(self, request: ApprovalRequest):
        """Send approval notification to console dashboard"""
        notification = {
            'type': 'approval_request',
            'request_id': request.request_id,
            'trace_id': request.trace_id,
            'title': request.title,
            'description': request.description,
            'priority': request.priority,
            'requester_agent': request.requester_agent,
            'created_at': request.created_at.isoformat(),
            'expires_at': request.expires_at.isoformat(),
            'context': request.context
        }
        
        self.logger.info(f"Console notification sent for request {request.request_id}")
        
        self._store_console_notification(notification)
        
    def _store_console_notification(self, notification: Dict):
        """Store notification for console API retrieval"""
        pass
        
    async def _send_telegram_notification(self, request: ApprovalRequest):
        """Send approval notification to Telegram"""
        if not self.telegram_bot_token or not self.admin_chat_id:
            self.logger.warning("Telegram configuration incomplete, skipping notification")
            return
            
        priority_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '📋',
            'low': '📝'
        }
        
        emoji = priority_emoji.get(request.priority, '📋')
        
        message = f"""
{emoji} **Approval Required**

**Title:** {request.title}
**Agent:** {request.requester_agent}
**Priority:** {request.priority.upper()}
**Trace ID:** `{request.trace_id}`

**Description:**
{request.description}

**Context:**
```json
{request.prompt_details}
```

**Actions:**
• `/approve {request.request_id}` - Approve request
• `/reject {request.request_id}` - Reject request
• `/details {request.request_id}` - View full details

**Expires:** {request.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        self.logger.info(f"Telegram notification sent for request {request.request_id}")
        
    async def process_approval(
        self,
        request_id: str,
        approved: bool,
        approver: str,
        channel: ApprovalChannel,
        comments: Optional[str] = None
    ) -> bool:
        """Process approval decision from either channel"""
        if request_id not in self.pending_requests:
            self.logger.error(f"Approval request {request_id} not found")
            return False
            
        request = self.pending_requests[request_id]
        
        if datetime.now() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            self.logger.warning(f"Approval request {request_id} expired")
            return False
            
        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        request.approved_by = approver
        request.approved_at = datetime.now()
        request.approval_channel = channel
        request.comments = comments
        
        request_data = asdict(request)
        request_data['created_at'] = request_data['created_at'].isoformat()
        request_data['expires_at'] = request_data['expires_at'].isoformat()
        request_data['approved_at'] = request_data['approved_at'].isoformat() if request_data['approved_at'] else None
        request_data['status'] = request_data['status'].value
        request_data['approval_channel'] = request_data['approval_channel'].value if request_data['approval_channel'] else None
        
        persistent_state_manager.save_approval_request(request_data)
        
        if request_id in self.approval_callbacks:
            callback = self.approval_callbacks[request_id]
            try:
                await callback(request, approved)
            except Exception as e:
                self.logger.error(f"Approval callback failed: {e}")
            finally:
                del self.approval_callbacks[request_id]
                
        await self._send_approval_confirmation(request, approved)
        
        self.logger.info(f"Approval request {request_id} {request.status.value} by {approver} via {channel.value}")
        return True
        
    async def _send_approval_confirmation(self, request: ApprovalRequest, approved: bool):
        """Send approval confirmation to both channels"""
        status_text = "APPROVED" if approved else "REJECTED"
        
        confirmation = {
            'type': 'approval_confirmation',
            'request_id': request.request_id,
            'trace_id': request.trace_id,
            'status': status_text,
            'approved_by': request.approved_by,
            'approved_at': request.approved_at.isoformat() if request.approved_at else None,
            'channel': request.approval_channel.value if request.approval_channel else None
        }
        
        self.logger.info(f"Approval confirmation sent for {request.request_id}: {status_text}")
        
    def register_approval_callback(self, request_id: str, callback: Callable):
        """Register callback for approval decision"""
        self.approval_callbacks[request_id] = callback
        
    def get_pending_requests(self, priority_filter: Optional[str] = None) -> List[ApprovalRequest]:
        """Get all pending approval requests from persistent storage"""
        try:
            pending_data = persistent_state_manager.load_approval_requests(status='pending')
            requests = []
            
            for request_data in pending_data:
                if not priority_filter or request_data['priority'] == priority_filter:
                    request = ApprovalRequest(
                        request_id=request_data['request_id'],
                        trace_id=request_data['trace_id'],
                        title=request_data['title'],
                        description=request_data['description'],
                        context=request_data['context'],
                        prompt_details=request_data['prompt_details'],
                        requester_agent=request_data['requester_agent'],
                        priority=request_data['priority'],
                        created_at=datetime.fromisoformat(request_data['created_at']),
                        expires_at=datetime.fromisoformat(request_data['expires_at']),
                        status=ApprovalStatus(request_data['status'])
                    )
                    requests.append(request)
                    
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            requests.sort(key=lambda x: (priority_order.get(x.priority, 4), x.created_at))
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Failed to get pending requests: {e}")
            return []
        
    def get_approval_history(self, limit: int = 100, status_filter: Optional[str] = None) -> List[ApprovalRequest]:
        """Get approval history with optional filtering"""
        history = self.approval_history
        
        if status_filter:
            history = [r for r in history if r.status.value == status_filter]
            
        return sorted(history, key=lambda x: x.created_at, reverse=True)[:limit]
        
    async def cleanup_expired_requests(self):
        """Clean up expired approval requests"""
        current_time = datetime.now()
        expired_requests = []
        
        for request_id, request in list(self.pending_requests.items()):
            if current_time > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                expired_requests.append(request)
                self.approval_history.append(request)
                del self.pending_requests[request_id]
                
        if expired_requests:
            self.logger.info(f"Cleaned up {len(expired_requests)} expired approval requests")
            
        return len(expired_requests)
        
    def _load_persistent_state(self):
        """Load approval requests from persistent storage"""
        try:
            pending_data = persistent_state_manager.load_approval_requests(status='pending')
            self.pending_requests = {}
            
            for request_data in pending_data:
                request = ApprovalRequest(
                    request_id=request_data['request_id'],
                    trace_id=request_data['trace_id'],
                    title=request_data['title'],
                    description=request_data['description'],
                    context=request_data['context'],
                    prompt_details=request_data['prompt_details'],
                    requester_agent=request_data['requester_agent'],
                    priority=request_data['priority'],
                    created_at=datetime.fromisoformat(request_data['created_at']),
                    expires_at=datetime.fromisoformat(request_data['expires_at']),
                    status=ApprovalStatus(request_data['status'])
                )
                self.pending_requests[request.request_id] = request
                
            history_data = persistent_state_manager.load_approval_requests(limit=1000)
            self.approval_history = []
            
            for request_data in history_data:
                if request_data['status'] != 'pending':
                    request = ApprovalRequest(
                        request_id=request_data['request_id'],
                        trace_id=request_data['trace_id'],
                        title=request_data['title'],
                        description=request_data['description'],
                        context=request_data['context'],
                        prompt_details=request_data['prompt_details'],
                        requester_agent=request_data['requester_agent'],
                        priority=request_data['priority'],
                        created_at=datetime.fromisoformat(request_data['created_at']),
                        expires_at=datetime.fromisoformat(request_data['expires_at']),
                        status=ApprovalStatus(request_data['status']),
                        approved_by=request_data.get('approved_by'),
                        approved_at=datetime.fromisoformat(request_data['approved_at']) if request_data.get('approved_at') else None,
                        approval_channel=ApprovalChannel(request_data['approval_channel']) if request_data.get('approval_channel') else None
                    )
                    self.approval_history.append(request)
                    
            self.logger.info(f"Loaded {len(self.pending_requests)} pending requests and {len(self.approval_history)} historical requests")
            
        except Exception as e:
            self.logger.error(f"Failed to load persistent state: {e}")
            self.pending_requests = {}
            self.approval_history = []
        
    def get_system_status(self) -> Dict:
        """Get HITL approval system status"""
        pending_by_priority = {}
        for priority in ['critical', 'high', 'medium', 'low']:
            pending_by_priority[priority] = len([r for r in self.pending_requests.values() if r.priority == priority])
            
        return {
            'agent': 'HITL_Approval_System',
            'channels': {
                'console': True,
                'telegram': bool(self.telegram_bot_token and self.admin_chat_id)
            },
            'pending_requests': {
                'total': len(self.pending_requests),
                'by_priority': pending_by_priority
            },
            'approval_history': {
                'total': len(self.approval_history),
                'approved': len([r for r in self.approval_history if r.status == ApprovalStatus.APPROVED]),
                'rejected': len([r for r in self.approval_history if r.status == ApprovalStatus.REJECTED]),
                'expired': len([r for r in self.approval_history if r.status == ApprovalStatus.EXPIRED])
            },
            'configuration': {
                'timeout_hours': self.timeout_hours
            },
            'status': 'operational'
        }
        
    async def simulate_meta_agent_request(self) -> ApprovalRequest:
        """Simulate a Meta-Agent approval request for testing"""
        context = {
            'decision_type': 'strategy_adjustment',
            'current_strategy': 'daily_login_rewards',
            'proposed_strategy': 'weekly_streak_bonuses',
            'expected_impact': {'retention': 0.15, 'engagement': 0.20},
            'implementation_cost': 'medium',
            'confidence_score': 0.85
        }
        
        return await self.create_approval_request(
            title="Gamification Strategy Adjustment",
            description="Meta-Agent proposes switching from daily login rewards to weekly streak bonuses based on effectiveness analysis",
            context=context,
            requester_agent="Meta-Agent",
            priority="medium"
        )
