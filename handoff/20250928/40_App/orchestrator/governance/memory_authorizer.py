"""
Memory Authorizer - Authorization checks for Memory v2 operations

EPIC G: Memory v2 Security (Blueprint Section 4.7)
Issue: #3969 - Add authorization checks for Memory v2 search functions

This module implements authorization checks for Memory v2 search operations
to prevent unauthorized access to historical data across different users/organizations.

Blueprint Alignment:
- Section 4.1 (Safe by Design): Organizational data isolation
- Section 4.7 (Capability-Based Security): Access control via capabilities

Authorization Flow:
1. Check if caller has required capability (memory:read)
2. Apply scope-based filtering (GLOBAL, WORKFLOW, AGENT)
3. Log search operations for audit trail
4. Fail-closed on authorization errors
"""

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional, FrozenSet

from utils.sanitization import sanitize_for_log

logger = logging.getLogger(__name__)

DEFAULT_PERMISSION_LEVEL = "sandbox_only"


class MemoryCapability(str, Enum):
    """Capabilities for Memory v2 operations.

    Blueprint Reference: Section 4.7 - Capability-Based Security
    """
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    MEMORY_SEARCH_GLOBAL = "memory:search_global"
    MEMORY_SEARCH_WORKFLOW = "memory:search_workflow"
    MEMORY_SEARCH_AGENT = "memory:search_agent"


class MemorySearchScope(str, Enum):
    """Search scope for Memory v2 operations."""
    GLOBAL = "global"
    WORKFLOW = "workflow"
    AGENT = "agent"


# Default capabilities per permission level
# Maps to permission_levels from reputation_engine policies.yaml
MEMORY_CAPABILITIES_BY_LEVEL: dict = {
    "sandbox_only": frozenset({
        MemoryCapability.MEMORY_READ,
        MemoryCapability.MEMORY_SEARCH_AGENT,
    }),
    "staging_access": frozenset({
        MemoryCapability.MEMORY_READ,
        MemoryCapability.MEMORY_WRITE,
        MemoryCapability.MEMORY_SEARCH_AGENT,
        MemoryCapability.MEMORY_SEARCH_WORKFLOW,
    }),
    "prod_low_risk": frozenset({
        MemoryCapability.MEMORY_READ,
        MemoryCapability.MEMORY_WRITE,
        MemoryCapability.MEMORY_SEARCH_AGENT,
        MemoryCapability.MEMORY_SEARCH_WORKFLOW,
    }),
    "prod_full_access": frozenset({
        MemoryCapability.MEMORY_READ,
        MemoryCapability.MEMORY_WRITE,
        MemoryCapability.MEMORY_DELETE,
        MemoryCapability.MEMORY_SEARCH_AGENT,
        MemoryCapability.MEMORY_SEARCH_WORKFLOW,
        MemoryCapability.MEMORY_SEARCH_GLOBAL,
    }),
}


@dataclass
class MemoryAuthorizationResult:
    """Result of a memory authorization check."""
    authorized: bool
    reason: str
    allowed_scopes: FrozenSet[MemorySearchScope]
    audit_logged: bool = False

    def to_dict(self) -> dict:
        return {
            "authorized": self.authorized,
            "reason": self.reason,
            "allowed_scopes": [s.value for s in self.allowed_scopes],
            "audit_logged": self.audit_logged,
        }


class MemoryAuthorizer:
    """
    Authorization checker for Memory v2 operations.

    EPIC G: Memory v2 Security (Blueprint Section 4.7)
    Issue: #3969 - Add authorization checks for Memory v2 search functions

    This class provides authorization checks for memory search operations,
    ensuring only authorized agents can access historical data.

    Authorization Logic:
    1. Check if agent has memory:read capability
    2. Determine allowed search scopes based on permission level
    3. Filter results based on scope (GLOBAL, WORKFLOW, AGENT)
    4. Log all search operations for audit trail
    """

    def __init__(self):
        """Initialize Memory Authorizer."""
        logger.info("[MemoryAuthorizer] Initialized")

    def authorize_search(
        self,
        agent_id: Optional[str] = None,
        agent_type: str = "unknown",
        permission_level: str = "sandbox_only",
        requested_scope: Optional[MemorySearchScope] = None,
        trace_id: Optional[str] = None,
    ) -> MemoryAuthorizationResult:
        """
        Authorize a memory search operation.

        Args:
            agent_id: Agent UUID performing the search
            agent_type: Type of agent (dev_agent, ops_agent, etc.)
            permission_level: Agent's permission level
            requested_scope: Requested search scope
            trace_id: Workflow trace ID for filtering

        Returns:
            MemoryAuthorizationResult with authorization decision
        """
        capabilities = MEMORY_CAPABILITIES_BY_LEVEL.get(
            permission_level,
            MEMORY_CAPABILITIES_BY_LEVEL[DEFAULT_PERMISSION_LEVEL]
        )

        if MemoryCapability.MEMORY_READ not in capabilities:
            self._log_authorization_failure(
                agent_id=agent_id,
                agent_type=agent_type,
                reason="Missing memory:read capability",
                trace_id=trace_id,
            )
            return MemoryAuthorizationResult(
                authorized=False,
                reason="Missing memory:read capability",
                allowed_scopes=frozenset(),
            )

        allowed_scopes = self._get_allowed_scopes(capabilities)

        if requested_scope and requested_scope not in allowed_scopes:
            self._log_authorization_failure(
                agent_id=agent_id,
                agent_type=agent_type,
                reason=f"Scope {requested_scope.value} not allowed",
                trace_id=trace_id,
            )
            return MemoryAuthorizationResult(
                authorized=False,
                reason=f"Scope {requested_scope.value} not allowed for permission level {permission_level}",
                allowed_scopes=allowed_scopes,
            )

        self._log_authorization_success(
            agent_id=agent_id,
            agent_type=agent_type,
            allowed_scopes=allowed_scopes,
            trace_id=trace_id,
        )

        return MemoryAuthorizationResult(
            authorized=True,
            reason=f"Authorized with permission level: {permission_level}",
            allowed_scopes=allowed_scopes,
            audit_logged=True,
        )

    def _get_allowed_scopes(
        self,
        capabilities: FrozenSet[MemoryCapability],
    ) -> FrozenSet[MemorySearchScope]:
        """Determine allowed search scopes from capabilities."""
        scopes = set()

        if MemoryCapability.MEMORY_SEARCH_AGENT in capabilities:
            scopes.add(MemorySearchScope.AGENT)

        if MemoryCapability.MEMORY_SEARCH_WORKFLOW in capabilities:
            scopes.add(MemorySearchScope.WORKFLOW)

        if MemoryCapability.MEMORY_SEARCH_GLOBAL in capabilities:
            scopes.add(MemorySearchScope.GLOBAL)

        return frozenset(scopes)

    def _log_authorization_success(
        self,
        agent_id: Optional[str],
        agent_type: str,
        allowed_scopes: FrozenSet[MemorySearchScope],
        trace_id: Optional[str],
    ) -> None:
        """Log successful authorization for audit trail.

        Issue #4016, #3992: Sanitize externally-sourced data to prevent log injection.
        """
        logger.info(
            "[MemoryAuthorizer] Search authorized",
            extra={
                "operation": "memory_search_authorized",
                "agent_id": sanitize_for_log(agent_id),
                "agent_type": sanitize_for_log(agent_type),
                "allowed_scopes": [s.value for s in allowed_scopes],
                "trace_id": sanitize_for_log(trace_id),
            }
        )

    def _log_authorization_failure(
        self,
        agent_id: Optional[str],
        agent_type: str,
        reason: str,
        trace_id: Optional[str],
    ) -> None:
        """Log authorization failure for security monitoring.

        Issue #4016, #3992: Sanitize externally-sourced data to prevent log injection.
        """
        logger.warning(
            "[MemoryAuthorizer] Search denied",
            extra={
                "operation": "memory_search_denied",
                "agent_id": sanitize_for_log(agent_id),
                "agent_type": sanitize_for_log(agent_type),
                "reason": sanitize_for_log(reason),
                "trace_id": sanitize_for_log(trace_id),
            }
        )


_memory_authorizer: Optional[MemoryAuthorizer] = None
_memory_authorizer_lock = threading.Lock()


def get_memory_authorizer() -> MemoryAuthorizer:
    """Get or create global MemoryAuthorizer instance (thread-safe)."""
    global _memory_authorizer
    if _memory_authorizer is None:
        with _memory_authorizer_lock:
            if _memory_authorizer is None:
                _memory_authorizer = MemoryAuthorizer()
    return _memory_authorizer


def authorize_memory_search(
    agent_id: Optional[str] = None,
    agent_type: str = "unknown",
    permission_level: str = "sandbox_only",
    requested_scope: Optional[MemorySearchScope] = None,
    trace_id: Optional[str] = None,
) -> MemoryAuthorizationResult:
    """
    Convenience function to authorize a memory search operation.

    This is the main entry point for authorization checks in memory_integration.py.

    Args:
        agent_id: Agent UUID performing the search
        agent_type: Type of agent
        permission_level: Agent's permission level
        requested_scope: Requested search scope
        trace_id: Workflow trace ID

    Returns:
        MemoryAuthorizationResult with authorization decision
    """
    authorizer = get_memory_authorizer()
    return authorizer.authorize_search(
        agent_id=agent_id,
        agent_type=agent_type,
        permission_level=permission_level,
        requested_scope=requested_scope,
        trace_id=trace_id,
    )
