"""
Routing Authorizer - Authorization checks for Routing Policy operations

EPIC I: Runtime Governance (Blueprint Section 4.4)
Issue: #3960 - Add authorization checks for routing policy change approval methods

This module implements authorization checks for routing policy change operations
to ensure only authorized users/services can approve, reject, or rollback changes.

Blueprint Alignment:
- Section 4.4 (Governance Layer): Safe by Design guarantees
- Section 4.7 (Capability-Based Security): Role-based access control

Authorization Flow:
1. Check if caller has required role (routing_admin, system_operator)
2. Verify caller identity against allowlist or permission system
3. Log all authorization attempts for audit trail
4. Fail-closed on authorization errors
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set, FrozenSet

logger = logging.getLogger(__name__)


class RoutingRole(str, Enum):
    """Roles for routing policy operations.

    Blueprint Reference: Section 4.4 - Governance Layer
    """
    ROUTING_ADMIN = "routing_admin"
    SYSTEM_OPERATOR = "system_operator"
    ROUTING_VIEWER = "routing_viewer"


class RoutingOperation(str, Enum):
    """Operations on routing policy."""
    APPROVE_CHANGE = "approve_change"
    REJECT_CHANGE = "reject_change"
    ROLLBACK_CHANGE = "rollback_change"
    VIEW_PENDING = "view_pending"
    VIEW_APPLIED = "view_applied"


# Operations allowed per role
ROUTING_OPERATIONS_BY_ROLE: dict = {
    RoutingRole.ROUTING_ADMIN: frozenset({
        RoutingOperation.APPROVE_CHANGE,
        RoutingOperation.REJECT_CHANGE,
        RoutingOperation.ROLLBACK_CHANGE,
        RoutingOperation.VIEW_PENDING,
        RoutingOperation.VIEW_APPLIED,
    }),
    RoutingRole.SYSTEM_OPERATOR: frozenset({
        RoutingOperation.APPROVE_CHANGE,
        RoutingOperation.REJECT_CHANGE,
        RoutingOperation.ROLLBACK_CHANGE,
        RoutingOperation.VIEW_PENDING,
        RoutingOperation.VIEW_APPLIED,
    }),
    RoutingRole.ROUTING_VIEWER: frozenset({
        RoutingOperation.VIEW_PENDING,
        RoutingOperation.VIEW_APPLIED,
    }),
}

# Permission levels that map to routing roles
ROUTING_ROLES_BY_PERMISSION_LEVEL: dict = {
    "sandbox_only": frozenset({RoutingRole.ROUTING_VIEWER}),
    "staging_access": frozenset({RoutingRole.ROUTING_VIEWER}),
    "prod_low_risk": frozenset({RoutingRole.ROUTING_VIEWER, RoutingRole.SYSTEM_OPERATOR}),
    "prod_full_access": frozenset({
        RoutingRole.ROUTING_VIEWER,
        RoutingRole.SYSTEM_OPERATOR,
        RoutingRole.ROUTING_ADMIN,
    }),
}


class RoutingAuthorizationError(Exception):
    """Raised when routing authorization fails."""

    def __init__(self, message: str, operation: str, caller: str):
        super().__init__(message)
        self.operation = operation
        self.caller = caller


@dataclass
class RoutingAuthorizationResult:
    """Result of a routing authorization check."""
    authorized: bool
    reason: str
    roles: FrozenSet[RoutingRole]
    allowed_operations: FrozenSet[RoutingOperation]

    def to_dict(self) -> dict:
        return {
            "authorized": self.authorized,
            "reason": self.reason,
            "roles": [r.value for r in self.roles],
            "allowed_operations": [op.value for op in self.allowed_operations],
        }


class RoutingAuthorizer:
    """
    Authorization checker for routing policy operations.

    EPIC I: Runtime Governance (Blueprint Section 4.4)
    Issue: #3960 - Add authorization checks for routing policy change approval methods

    This class provides authorization checks for routing policy change operations,
    ensuring only authorized users can approve, reject, or rollback changes.

    Authorization Logic:
    1. Resolve caller's roles from permission level or explicit role assignment
    2. Check if any role allows the requested operation
    3. Log all authorization attempts for audit trail
    4. Fail-closed on errors (deny if can't verify)
    """

    def __init__(self, allowlist: Optional[Set[str]] = None):
        """
        Initialize Routing Authorizer.

        Args:
            allowlist: Optional set of usernames that are always authorized
                      (break-glass for emergency access)
        """
        self._allowlist = allowlist or set()
        logger.info(
            "[RoutingAuthorizer] Initialized",
            extra={
                "allowlist_size": len(self._allowlist),
            }
        )

    def authorize(
        self,
        operation: RoutingOperation,
        caller: str,
        permission_level: str = "sandbox_only",
        explicit_roles: Optional[Set[RoutingRole]] = None,
    ) -> RoutingAuthorizationResult:
        """
        Authorize a routing policy operation.

        Args:
            operation: The operation being performed
            caller: Identifier of the caller (username or service name)
            permission_level: Caller's permission level
            explicit_roles: Optional explicit role assignment (overrides permission level)

        Returns:
            RoutingAuthorizationResult with authorization decision
        """
        if caller in self._allowlist:
            self._log_authorization_success(
                operation=operation,
                caller=caller,
                reason="Allowlist (break-glass)",
            )
            return RoutingAuthorizationResult(
                authorized=True,
                reason="Authorized via allowlist (break-glass)",
                roles=frozenset({RoutingRole.ROUTING_ADMIN}),
                allowed_operations=ROUTING_OPERATIONS_BY_ROLE[RoutingRole.ROUTING_ADMIN],
            )

        if explicit_roles:
            roles = frozenset(explicit_roles)
        else:
            roles = ROUTING_ROLES_BY_PERMISSION_LEVEL.get(
                permission_level,
                ROUTING_ROLES_BY_PERMISSION_LEVEL["sandbox_only"]
            )

        allowed_operations = self._get_allowed_operations(roles)

        if operation not in allowed_operations:
            self._log_authorization_failure(
                operation=operation,
                caller=caller,
                reason=f"Operation {operation.value} not allowed for roles: {[r.value for r in roles]}",
            )
            return RoutingAuthorizationResult(
                authorized=False,
                reason=f"Operation {operation.value} requires routing_admin or system_operator role",
                roles=roles,
                allowed_operations=allowed_operations,
            )

        self._log_authorization_success(
            operation=operation,
            caller=caller,
            reason=f"Authorized with roles: {[r.value for r in roles]}",
        )

        return RoutingAuthorizationResult(
            authorized=True,
            reason=f"Authorized with permission level: {permission_level}",
            roles=roles,
            allowed_operations=allowed_operations,
        )

    def require_authorization(
        self,
        operation: RoutingOperation,
        caller: str,
        permission_level: str = "sandbox_only",
        explicit_roles: Optional[Set[RoutingRole]] = None,
    ) -> None:
        """
        Require authorization for an operation, raising exception if denied.

        Args:
            operation: The operation being performed
            caller: Identifier of the caller
            permission_level: Caller's permission level
            explicit_roles: Optional explicit role assignment

        Raises:
            RoutingAuthorizationError if authorization fails
        """
        result = self.authorize(
            operation=operation,
            caller=caller,
            permission_level=permission_level,
            explicit_roles=explicit_roles,
        )

        if not result.authorized:
            raise RoutingAuthorizationError(
                message=result.reason,
                operation=operation.value,
                caller=caller,
            )

    def _get_allowed_operations(
        self,
        roles: FrozenSet[RoutingRole],
    ) -> FrozenSet[RoutingOperation]:
        """Get all operations allowed by any of the given roles."""
        operations: Set[RoutingOperation] = set()
        for role in roles:
            role_ops = ROUTING_OPERATIONS_BY_ROLE.get(role, frozenset())
            operations.update(role_ops)
        return frozenset(operations)

    def _log_authorization_success(
        self,
        operation: RoutingOperation,
        caller: str,
        reason: str,
    ) -> None:
        """Log successful authorization for audit trail."""
        logger.info(
            "[RoutingAuthorizer] Operation authorized",
            extra={
                "operation_type": "routing_policy_authorized",
                "routing_operation": operation.value,
                "caller": caller,
                "reason": reason,
            }
        )

    def _log_authorization_failure(
        self,
        operation: RoutingOperation,
        caller: str,
        reason: str,
    ) -> None:
        """Log authorization failure for security monitoring."""
        logger.warning(
            "[RoutingAuthorizer] Operation denied",
            extra={
                "operation_type": "routing_policy_denied",
                "routing_operation": operation.value,
                "caller": caller,
                "reason": reason,
            }
        )

    def add_to_allowlist(self, caller: str) -> None:
        """Add a caller to the allowlist (break-glass)."""
        self._allowlist.add(caller)
        logger.info(
            "[RoutingAuthorizer] Added to allowlist",
            extra={"caller": caller}
        )

    def remove_from_allowlist(self, caller: str) -> None:
        """Remove a caller from the allowlist."""
        self._allowlist.discard(caller)
        logger.info(
            "[RoutingAuthorizer] Removed from allowlist",
            extra={"caller": caller}
        )


_routing_authorizer: Optional[RoutingAuthorizer] = None


def get_routing_authorizer() -> RoutingAuthorizer:
    """Get or create global RoutingAuthorizer instance."""
    global _routing_authorizer
    if _routing_authorizer is None:
        _routing_authorizer = RoutingAuthorizer()
    return _routing_authorizer


def authorize_routing_operation(
    operation: RoutingOperation,
    caller: str,
    permission_level: str = "sandbox_only",
) -> RoutingAuthorizationResult:
    """
    Convenience function to authorize a routing policy operation.

    This is the main entry point for authorization checks in routing_policy_evolver.py.

    Args:
        operation: The operation being performed
        caller: Identifier of the caller
        permission_level: Caller's permission level

    Returns:
        RoutingAuthorizationResult with authorization decision
    """
    authorizer = get_routing_authorizer()
    return authorizer.authorize(
        operation=operation,
        caller=caller,
        permission_level=permission_level,
    )


def require_routing_authorization(
    operation: RoutingOperation,
    caller: str,
    permission_level: str = "sandbox_only",
) -> None:
    """
    Require authorization for a routing operation, raising exception if denied.

    Args:
        operation: The operation being performed
        caller: Identifier of the caller
        permission_level: Caller's permission level

    Raises:
        RoutingAuthorizationError if authorization fails
    """
    authorizer = get_routing_authorizer()
    authorizer.require_authorization(
        operation=operation,
        caller=caller,
        permission_level=permission_level,
    )
