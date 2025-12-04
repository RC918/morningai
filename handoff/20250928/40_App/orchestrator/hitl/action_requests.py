"""
Action Requests - Human-in-the-Loop (HITL) for High-Risk Operations

This module provides the Python interface for managing action requests
that require human approval before execution.

High-risk operations include:
- DROP TABLE / DELETE operations
- Sensitive file modifications (.env, secrets, credentials)
- Production deployments
- Database schema changes
- Permission changes

Issue: #1816
Phase: Phase 3 - Autonomous Expansion
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ActionRequestStatus(Enum):
    """Status of an action request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk level of an action"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# High-risk action patterns that require HITL approval
HIGH_RISK_PATTERNS = {
    "database": [
        "DROP TABLE",
        "DROP DATABASE",
        "DELETE FROM",
        "TRUNCATE",
        "ALTER TABLE",
    ],
    "filesystem": [
        "rm -rf",
        "rm -r",
        "sudo rm",
        "chmod 777",
        "chown",
    ],
    "deployment": [
        "deploy production",
        "deploy prod",
        "fly deploy",
        "render deploy",
    ],
    "secrets": [
        ".env",
        "credentials",
        "secrets",
        "private_key",
        "api_key",
    ],
}


@dataclass
class ActionRequest:
    """Represents a high-risk action request requiring human approval"""
    request_id: str
    agent_id: str
    action_type: str
    action_description: str
    risk_level: RiskLevel = RiskLevel.HIGH
    risk_reason: Optional[str] = None
    action_payload: Optional[Dict[str, Any]] = None
    affected_resources: Optional[List[str]] = None
    trace_id: Optional[str] = None
    status: ActionRequestStatus = ActionRequestStatus.PENDING
    timeout_hours: int = 24
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    @property
    def timeout_at(self) -> datetime:
        """Calculate timeout timestamp"""
        return self.created_at + timedelta(hours=self.timeout_hours)

    @property
    def is_expired(self) -> bool:
        """Check if request has expired"""
        return datetime.now(timezone.utc) > self.timeout_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "risk_level": self.risk_level.value,
            "risk_reason": self.risk_reason,
            "action_payload": self.action_payload,
            "affected_resources": self.affected_resources,
            "trace_id": self.trace_id,
            "status": self.status.value,
            "timeout_at": self.timeout_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "approved_by": self.approved_by,
            "rejection_reason": self.rejection_reason,
        }


def _get_supabase():
    """Get Supabase client"""
    try:
        from supabase import create_client
        from common.config.settings import settings

        url = settings.supabase_url
        key = settings.supabase_service_role_key

        if not url or not key:
            logger.warning("[ActionRequests] Supabase credentials not configured")
            return None

        return create_client(url, key)
    except Exception as e:
        logger.error("[ActionRequests] Failed to create Supabase client: %s", e)
        return None


def detect_risk_level(action_type: str, action_description: str) -> tuple:
    """
    Detect risk level based on action type and description.

    Returns:
        Tuple of (RiskLevel, risk_reason)
    """
    action_lower = action_description.lower()
    action_type_lower = action_type.lower()

    # Check for critical patterns
    for pattern in HIGH_RISK_PATTERNS.get("database", []):
        if pattern.lower() in action_lower:
            return RiskLevel.CRITICAL, "Database destructive operation: %s" % pattern

    # Check for high-risk patterns
    for pattern in HIGH_RISK_PATTERNS.get("filesystem", []):
        if pattern.lower() in action_lower:
            return RiskLevel.HIGH, "Dangerous filesystem operation: %s" % pattern

    for pattern in HIGH_RISK_PATTERNS.get("deployment", []):
        if pattern.lower() in action_lower:
            return RiskLevel.HIGH, "Production deployment: %s" % pattern

    for pattern in HIGH_RISK_PATTERNS.get("secrets", []):
        if pattern.lower() in action_lower:
            return RiskLevel.HIGH, "Sensitive file access: %s" % pattern

    # Default based on action type
    if "delete" in action_type_lower or "drop" in action_type_lower:
        return RiskLevel.HIGH, "Destructive action type"

    if "deploy" in action_type_lower or "production" in action_type_lower:
        return RiskLevel.MEDIUM, "Deployment action"

    return RiskLevel.LOW, None


def create_action_request(
    agent_id: str,
    action_type: str,
    action_description: str,
    action_payload: Optional[Dict[str, Any]] = None,
    affected_resources: Optional[List[str]] = None,
    trace_id: Optional[str] = None,
    risk_level: Optional[RiskLevel] = None,
    risk_reason: Optional[str] = None,
    timeout_hours: int = 24,
) -> Optional[ActionRequest]:
    """
    Create a new action request requiring human approval.

    Args:
        agent_id: ID of the agent requesting the action
        action_type: Type of action (e.g., DROP_TABLE, DELETE_FILE)
        action_description: Human-readable description of the action
        action_payload: Optional payload with action details
        affected_resources: Optional list of affected resources
        trace_id: Optional trace ID for correlation
        risk_level: Optional risk level (auto-detected if not provided)
        risk_reason: Optional reason for risk level
        timeout_hours: Hours until auto-timeout (default 24)

    Returns:
        ActionRequest if created successfully, None otherwise
    """
    request_id = "ar_%s" % uuid.uuid4().hex[:12]

    # Auto-detect risk level if not provided
    if risk_level is None:
        risk_level, detected_reason = detect_risk_level(action_type, action_description)
        if risk_reason is None:
            risk_reason = detected_reason

    request = ActionRequest(
        request_id=request_id,
        agent_id=agent_id,
        action_type=action_type,
        action_description=action_description,
        action_payload=action_payload,
        affected_resources=affected_resources,
        trace_id=trace_id,
        risk_level=risk_level,
        risk_reason=risk_reason,
        timeout_hours=timeout_hours,
    )

    # Persist to database
    supabase = _get_supabase()
    if supabase:
        try:
            supabase.rpc(
                "create_action_request",
                {
                    "p_request_id": request.request_id,
                    "p_trace_id": request.trace_id,
                    "p_agent_id": request.agent_id,
                    "p_action_type": request.action_type,
                    "p_action_description": request.action_description,
                    "p_action_payload": request.action_payload,
                    "p_risk_level": request.risk_level.value,
                    "p_risk_reason": request.risk_reason,
                    "p_affected_resources": request.affected_resources,
                    "p_timeout_duration": "%d hours" % request.timeout_hours,
                }
            ).execute()

            logger.info(
                "[ActionRequests] Created request %s for agent %s: %s",
                request.request_id, agent_id, action_type
            )
            return request
        except Exception as e:
            logger.error("[ActionRequests] Failed to create request: %s", e)
            return None
    else:
        # Return None when DB unavailable to indicate HITL is not functional
        # This is a fail-open design: callers should treat None as "HITL unavailable"
        logger.warning("[ActionRequests] Database not available, HITL request not persisted")
        return None


def approve_action_request(request_id: str, approved_by: str) -> bool:
    """
    Approve a pending action request.

    Args:
        request_id: ID of the request to approve
        approved_by: ID/name of the approver

    Returns:
        True if approved successfully, False otherwise
    """
    supabase = _get_supabase()
    if not supabase:
        logger.error("[ActionRequests] Database not available")
        return False

    try:
        response = supabase.rpc(
            "approve_action_request",
            {
                "p_request_id": request_id,
                "p_approved_by": approved_by,
            }
        ).execute()

        success = response.data if response.data else False
        if success:
            logger.info(
                "[ActionRequests] Request %s approved by %s",
                request_id, approved_by
            )
        else:
            logger.warning(
                "[ActionRequests] Failed to approve request %s (not found or not pending)",
                request_id
            )
        return success
    except Exception as e:
        logger.error("[ActionRequests] Failed to approve request %s: %s", request_id, e)
        return False


def reject_action_request(
    request_id: str,
    rejected_by: str,
    reason: Optional[str] = None
) -> bool:
    """
    Reject a pending action request.

    Args:
        request_id: ID of the request to reject
        rejected_by: ID/name of the rejector
        reason: Optional rejection reason

    Returns:
        True if rejected successfully, False otherwise
    """
    supabase = _get_supabase()
    if not supabase:
        logger.error("[ActionRequests] Database not available")
        return False

    try:
        response = supabase.rpc(
            "reject_action_request",
            {
                "p_request_id": request_id,
                "p_rejected_by": rejected_by,
                "p_reason": reason,
            }
        ).execute()

        success = response.data if response.data else False
        if success:
            logger.info(
                "[ActionRequests] Request %s rejected by %s: %s",
                request_id, rejected_by, reason or "No reason provided"
            )
        else:
            logger.warning(
                "[ActionRequests] Failed to reject request %s (not found or not pending)",
                request_id
            )
        return success
    except Exception as e:
        logger.error("[ActionRequests] Failed to reject request %s: %s", request_id, e)
        return False


def get_pending_requests(
    limit: int = 50,
    risk_level_filter: Optional[RiskLevel] = None
) -> List[Dict[str, Any]]:
    """
    Get pending action requests.

    Args:
        limit: Maximum number of requests to return
        risk_level_filter: Optional filter by risk level

    Returns:
        List of pending action requests
    """
    supabase = _get_supabase()
    if not supabase:
        logger.error("[ActionRequests] Database not available")
        return []

    try:
        response = supabase.rpc(
            "get_pending_action_requests",
            {
                "p_limit": limit,
                "p_risk_level_filter": risk_level_filter.value if risk_level_filter else None,
            }
        ).execute()

        return response.data if response.data else []
    except Exception as e:
        logger.error("[ActionRequests] Failed to get pending requests: %s", e)
        return []


def get_request_status(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of an action request.

    Args:
        request_id: ID of the request

    Returns:
        Request details if found, None otherwise
    """
    supabase = _get_supabase()
    if not supabase:
        logger.error("[ActionRequests] Database not available")
        return None

    try:
        response = supabase.table("action_requests") \
            .select("*") \
            .eq("request_id", request_id) \
            .single() \
            .execute()

        return response.data if response.data else None
    except Exception as e:
        logger.error("[ActionRequests] Failed to get request status: %s", e)
        return None


def process_timed_out_requests() -> int:
    """
    Process and auto-reject timed out requests.

    Returns:
        Number of requests that were timed out
    """
    supabase = _get_supabase()
    if not supabase:
        logger.error("[ActionRequests] Database not available")
        return 0

    try:
        response = supabase.rpc("process_timed_out_requests").execute()
        count = response.data if response.data else 0

        if count > 0:
            logger.info("[ActionRequests] Processed %d timed out requests", count)

        return count
    except Exception as e:
        logger.error("[ActionRequests] Failed to process timed out requests: %s", e)
        return 0


def get_action_request_statistics() -> Dict[str, Any]:
    """
    Get statistics about action requests using SQL aggregation.

    Returns:
        Dictionary with pending_count and by_risk_level breakdown
    """
    supabase = _get_supabase()
    if not supabase:
        logger.error("[ActionRequests] Database not available")
        return {
            'pending_count': 0,
            'by_risk_level': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }

    try:
        response = supabase.rpc("get_action_request_statistics").execute()
        data = response.data if response.data else {}

        return {
            'pending_count': data.get('pending_count', 0),
            'by_risk_level': {
                'critical': data.get('critical_count', 0),
                'high': data.get('high_count', 0),
                'medium': data.get('medium_count', 0),
                'low': data.get('low_count', 0)
            }
        }
    except Exception as e:
        logger.error("[ActionRequests] Failed to get statistics: %s", e)
        return {
            'pending_count': 0,
            'by_risk_level': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
