"""
HITL Interceptor - Integrates semantic rules with action request workflow

This module provides the integration layer between:
- SemanticRulesValidator (high-risk action detection)
- ActionRequests (approval workflow)

When a high-risk operation is detected, this interceptor:
1. Creates an action request for human approval
2. Blocks execution until approved/rejected/timeout
3. Returns the approval status to the caller

Issue: #1816
Phase: Phase 3 - Autonomous Expansion
"""
import logging
from typing import Any, Dict, Optional, Tuple

from .action_requests import (
    ActionRequest,
    ActionRequestStatus,
    RiskLevel,
    create_action_request,
    get_request_status,
)

logger = logging.getLogger(__name__)

# Import semantic rules if available
# Note: PYTHONPATH should include orchestrator path, so direct import should work
# Fallback path setup only if direct import fails
try:
    from project_engineer.semantic_rules import (
        SemanticRulesValidator,
        HIGH_RISK_ACTIONS,
        SENSITIVE_FILE_PATTERNS,
    )
    SEMANTIC_RULES_AVAILABLE = True
except ImportError:
    # Fallback: try with explicit path setup
    # From hitl/ -> orchestrator -> 40_App -> 20250928 -> handoff -> repo_root (5 levels)
    try:
        import sys
        import os

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
        orchestrator_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
        if orchestrator_path not in sys.path:
            sys.path.insert(0, orchestrator_path)

        from project_engineer.semantic_rules import (
            SemanticRulesValidator,
            HIGH_RISK_ACTIONS,
            SENSITIVE_FILE_PATTERNS,
        )
        SEMANTIC_RULES_AVAILABLE = True
    except ImportError as e:
        logger.warning("Semantic rules not available: %s", e)
        SEMANTIC_RULES_AVAILABLE = False
        HIGH_RISK_ACTIONS = frozenset()
        SENSITIVE_FILE_PATTERNS = frozenset()


class HITLInterceptor:
    """
    Intercepts high-risk operations and routes them through the approval workflow.

    Usage:
        interceptor = HITLInterceptor(agent_id="dev_agent")

        # Check if action requires approval
        requires_approval, request = interceptor.check_action(
            action_type="DELETE_FILE",
            action_description="Delete .env.production file",
            affected_resources=[".env.production"]
        )

        if requires_approval:
            # Poll for approval status (callers should implement polling/async handling)
            status = interceptor.get_approval_status(request.request_id)
            if status != ActionRequestStatus.APPROVED:
                raise PermissionError("Action not approved")
    """

    def __init__(
        self,
        agent_id: str,
        trace_id: Optional[str] = None,
        require_hitl_for_high_risk: bool = True,
        timeout_hours: int = 24,
    ):
        """
        Initialize the HITL interceptor.

        Args:
            agent_id: ID of the agent performing actions
            trace_id: Optional trace ID for correlation
            require_hitl_for_high_risk: Whether to require approval for high-risk actions
            timeout_hours: Hours until approval request times out
        """
        self.agent_id = agent_id
        self.trace_id = trace_id
        self.require_hitl_for_high_risk = require_hitl_for_high_risk
        self.timeout_hours = timeout_hours

        if SEMANTIC_RULES_AVAILABLE:
            # Note: SemanticRulesValidator loads require_hitl_for_high_risk from settings internally.
            # The interceptor's own self.require_hitl_for_high_risk flag controls the approval workflow.
            self.validator = SemanticRulesValidator()
        else:
            self.validator = None

    def check_action(
        self,
        action_type: str,
        action_description: str,
        action_payload: Optional[Dict[str, Any]] = None,
        affected_resources: Optional[list] = None,
    ) -> Tuple[bool, Optional[ActionRequest]]:
        """
        Check if an action requires HITL approval.

        Args:
            action_type: Type of action (e.g., DELETE_FILE, DROP_TABLE)
            action_description: Human-readable description
            action_payload: Optional payload with action details
            affected_resources: Optional list of affected resources

        Returns:
            Tuple of (requires_approval, action_request)
            - If requires_approval is True, action_request contains the pending request
            - If requires_approval is False, action_request is None
        """
        if not self.require_hitl_for_high_risk:
            return False, None

        # Check using semantic rules validator if available
        if self.validator:
            is_valid, violation = self.validator.validate_action(action_description)

            if not is_valid and violation and violation.requires_approval:
                # Create action request for approval
                request = create_action_request(
                    agent_id=self.agent_id,
                    action_type=action_type,
                    action_description=action_description,
                    action_payload=action_payload,
                    affected_resources=affected_resources,
                    trace_id=self.trace_id,
                    risk_level=self._violation_to_risk_level(violation),
                    risk_reason=violation.message,
                    timeout_hours=self.timeout_hours,
                )

                if request:
                    logger.info(
                        "[HITLInterceptor] Action requires approval: %s (request_id=%s)",
                        action_type, request.request_id
                    )
                    return True, request

        # Fallback: Check against known high-risk patterns
        if self._is_high_risk_action(action_description):
            request = create_action_request(
                agent_id=self.agent_id,
                action_type=action_type,
                action_description=action_description,
                action_payload=action_payload,
                affected_resources=affected_resources,
                trace_id=self.trace_id,
                timeout_hours=self.timeout_hours,
            )

            if request:
                logger.info(
                    "[HITLInterceptor] High-risk action detected: %s (request_id=%s)",
                    action_type, request.request_id
                )
                return True, request

        return False, None

    def check_file_access(
        self,
        file_path: str,
        operation: str = "modify",
    ) -> Tuple[bool, Optional[ActionRequest]]:
        """
        Check if file access requires HITL approval.

        Args:
            file_path: Path to the file
            operation: Type of operation (read, modify, delete)

        Returns:
            Tuple of (requires_approval, action_request)
        """
        if not self.require_hitl_for_high_risk:
            return False, None

        # Check if file matches sensitive patterns
        if self._is_sensitive_file(file_path):
            request = create_action_request(
                agent_id=self.agent_id,
                action_type="SENSITIVE_FILE_%s" % operation.upper(),
                action_description="Attempting to %s sensitive file: %s" % (operation, file_path),
                affected_resources=[file_path],
                trace_id=self.trace_id,
                risk_level=RiskLevel.HIGH,
                risk_reason="File matches sensitive pattern",
                timeout_hours=self.timeout_hours,
            )

            if request:
                logger.info(
                    "[HITLInterceptor] Sensitive file access requires approval: %s",
                    file_path
                )
                return True, request

        return False, None

    def check_command(
        self,
        command: str,
    ) -> Tuple[bool, Optional[ActionRequest]]:
        """
        Check if a shell command requires HITL approval.

        Args:
            command: Shell command to execute

        Returns:
            Tuple of (requires_approval, action_request)
        """
        if not self.require_hitl_for_high_risk:
            return False, None

        # Check using semantic rules validator if available
        if self.validator:
            is_valid, violation = self.validator.validate_command(command)

            if not is_valid and violation and violation.requires_approval:
                request = create_action_request(
                    agent_id=self.agent_id,
                    action_type="SHELL_COMMAND",
                    action_description="Execute command: %s" % command[:200],
                    action_payload={"command": command},
                    trace_id=self.trace_id,
                    risk_level=self._violation_to_risk_level(violation),
                    risk_reason=violation.message,
                    timeout_hours=self.timeout_hours,
                )

                if request:
                    logger.info(
                        "[HITLInterceptor] Command requires approval: %s",
                        command[:100]
                    )
                    return True, request

        return False, None

    def get_approval_status(self, request_id: str) -> Optional[ActionRequestStatus]:
        """
        Get the current status of an approval request.

        Args:
            request_id: ID of the action request

        Returns:
            ActionRequestStatus if found, None otherwise
        """
        request_data = get_request_status(request_id)

        if request_data:
            status_str = request_data.get("status", "pending")
            try:
                return ActionRequestStatus(status_str)
            except ValueError:
                logger.warning("Unknown status: %s", status_str)
                return None

        return None

    def _violation_to_risk_level(self, violation) -> RiskLevel:
        """Convert violation severity to risk level"""
        severity = getattr(violation, 'severity', 'high')

        severity_map = {
            'critical': RiskLevel.CRITICAL,
            'high': RiskLevel.HIGH,
            'medium': RiskLevel.MEDIUM,
            'low': RiskLevel.LOW,
        }

        return severity_map.get(severity, RiskLevel.HIGH)

    def _is_high_risk_action(self, action_description: str) -> bool:
        """Check if action matches high-risk patterns"""
        action_lower = action_description.lower()

        for pattern in HIGH_RISK_ACTIONS:
            if pattern.lower() in action_lower:
                return True

        return False

    def _is_sensitive_file(self, file_path: str) -> bool:
        """Check if file matches sensitive patterns"""
        file_lower = file_path.lower()

        for pattern in SENSITIVE_FILE_PATTERNS:
            if pattern.lower() in file_lower:
                return True

        return False


def create_interceptor(
    agent_id: str,
    trace_id: Optional[str] = None,
    require_hitl: bool = True,
) -> HITLInterceptor:
    """
    Factory function to create an HITL interceptor.

    Args:
        agent_id: ID of the agent
        trace_id: Optional trace ID
        require_hitl: Whether to require HITL approval

    Returns:
        HITLInterceptor instance
    """
    return HITLInterceptor(
        agent_id=agent_id,
        trace_id=trace_id,
        require_hitl_for_high_risk=require_hitl,
    )
