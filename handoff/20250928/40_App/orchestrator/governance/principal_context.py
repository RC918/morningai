"""
Principal Context - EPIC E Phase E-2 Agent Identity Propagation

Blueprint Reference: Section 4.1 (Safety Governor v2)
Issue: Part of EPIC E Safety Governor v2

This module implements the PrincipalContext for agent identity propagation
through the safety enforcement pipeline. It enables:
- Agent-specific policy enforcement
- Capability-based access control (future)
- Audit trail with agent attribution
- Integration with ReputationEngine for trust-based decisions

Design Principles:
- Immutable context object for thread safety
- Default "unknown" principal for backward compatibility
- Integration with existing ReputationEngine/PermissionChecker
- Hook for future Agent-Specific Sandboxing (capability_set)
"""
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, FrozenSet

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Valid agent types as defined in Blueprint Section 3.3 (Agent Catalog V2).

    Blueprint Reference: Section 3.3 - 13 Agent Types
    Issue: #4118 (EPIC K P0: AgentType Enum Extension)

    Categories:
    - Core Engineering Agents (5): Planner, Coding, Reviewer, Test, Debugger
    - UX/UI Agents (4): UI Consistency, UX Heuristic, Visual Regression, Design Token
    - Governance/Reasoning Agents (3): Judge, Debate (Left/Right), Risk Analyzer
    - Legacy/Compatibility (6): dev_agent, ops_agent, pm_agent, etc.
    """
    # === Core Engineering Agents (Blueprint 3.3) ===
    PLANNER = "planner"
    CODING = "coding"
    REVIEWER = "reviewer"
    TEST = "test"
    DEBUGGER = "debugger"

    # === UX/UI Agents (Blueprint 3.3) ===
    UI_CONSISTENCY = "ui_consistency"
    UX_HEURISTIC = "ux_heuristic"
    VISUAL_REGRESSION = "visual_regression"
    DESIGN_TOKEN_GOVERNANCE = "design_token_governance"

    # === Governance/Reasoning Agents (Blueprint 3.3) ===
    JUDGE = "judge"
    DEBATE_LEFT = "debate_left"
    DEBATE_RIGHT = "debate_right"
    RISK_ANALYZER = "risk_analyzer"

    # === Legacy Agent Types (backward compatibility) ===
    DEV_AGENT = "dev_agent"
    OPS_AGENT = "ops_agent"
    PM_AGENT = "pm_agent"
    GROWTH_STRATEGIST = "growth_strategist"
    META_AGENT = "meta_agent"
    UNKNOWN = "unknown"  # Default for backward compatibility


class CapabilityType(str, Enum):
    """Capability types for future Agent-Specific Sandboxing.

    Blueprint Reference: Section 4.1 - Capability-Based Security
    These capabilities define what actions an agent is permitted to perform.
    """
    # File operations
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"

    # Network operations
    NETWORK_READ = "network:read"
    NETWORK_WRITE = "network:write"

    # Shell operations
    SHELL_EXECUTE = "shell:execute"
    SHELL_EXECUTE_DANGEROUS = "shell:execute_dangerous"

    # GitHub operations
    GITHUB_READ = "github:read"
    GITHUB_WRITE = "github:write"
    GITHUB_PR_CREATE = "github:pr_create"
    GITHUB_PR_MERGE = "github:pr_merge"

    # LLM operations
    LLM_INVOKE = "llm:invoke"
    LLM_INVOKE_EXPENSIVE = "llm:invoke_expensive"

    # Database operations
    DB_READ = "db:read"
    DB_WRITE = "db:write"

    # Deployment operations
    DEPLOY_SANDBOX = "deploy:sandbox"
    DEPLOY_STAGING = "deploy:staging"
    DEPLOY_PRODUCTION = "deploy:production"


# Default capability sets per permission level
# Maps to permission_levels from reputation_engine policies.yaml
DEFAULT_CAPABILITIES: Dict[str, FrozenSet[CapabilityType]] = {
    "sandbox_only": frozenset({
        CapabilityType.FILE_READ,
        CapabilityType.FILE_WRITE,
        CapabilityType.NETWORK_READ,
        CapabilityType.SHELL_EXECUTE,
        CapabilityType.GITHUB_READ,
        CapabilityType.LLM_INVOKE,
        CapabilityType.DB_READ,
        CapabilityType.DEPLOY_SANDBOX,
    }),
    "staging_access": frozenset({
        CapabilityType.FILE_READ,
        CapabilityType.FILE_WRITE,
        CapabilityType.NETWORK_READ,
        CapabilityType.NETWORK_WRITE,
        CapabilityType.SHELL_EXECUTE,
        CapabilityType.GITHUB_READ,
        CapabilityType.GITHUB_WRITE,
        CapabilityType.GITHUB_PR_CREATE,
        CapabilityType.LLM_INVOKE,
        CapabilityType.DB_READ,
        CapabilityType.DB_WRITE,
        CapabilityType.DEPLOY_SANDBOX,
        CapabilityType.DEPLOY_STAGING,
    }),
    "prod_low_risk": frozenset({
        CapabilityType.FILE_READ,
        CapabilityType.FILE_WRITE,
        CapabilityType.NETWORK_READ,
        CapabilityType.NETWORK_WRITE,
        CapabilityType.SHELL_EXECUTE,
        CapabilityType.GITHUB_READ,
        CapabilityType.GITHUB_WRITE,
        CapabilityType.GITHUB_PR_CREATE,
        CapabilityType.LLM_INVOKE,
        CapabilityType.LLM_INVOKE_EXPENSIVE,
        CapabilityType.DB_READ,
        CapabilityType.DB_WRITE,
        CapabilityType.DEPLOY_SANDBOX,
        CapabilityType.DEPLOY_STAGING,
    }),
    "prod_full_access": frozenset({
        CapabilityType.FILE_READ,
        CapabilityType.FILE_WRITE,
        CapabilityType.FILE_DELETE,
        CapabilityType.NETWORK_READ,
        CapabilityType.NETWORK_WRITE,
        CapabilityType.SHELL_EXECUTE,
        CapabilityType.SHELL_EXECUTE_DANGEROUS,
        CapabilityType.GITHUB_READ,
        CapabilityType.GITHUB_WRITE,
        CapabilityType.GITHUB_PR_CREATE,
        CapabilityType.GITHUB_PR_MERGE,
        CapabilityType.LLM_INVOKE,
        CapabilityType.LLM_INVOKE_EXPENSIVE,
        CapabilityType.DB_READ,
        CapabilityType.DB_WRITE,
        CapabilityType.DEPLOY_SANDBOX,
        CapabilityType.DEPLOY_STAGING,
        CapabilityType.DEPLOY_PRODUCTION,
    }),
}


@dataclass(frozen=True)
class PrincipalContext:
    """
    Immutable context representing the agent making a request.

    Blueprint Reference: Section 4.1 (Safety Governor v2)
    - SafetyDecision.principal field for agent identity
    - Enables Agent-Specific Sandboxing via capability_set

    This context is propagated through the enforcement pipeline to enable:
    - Agent-specific policy decisions
    - Capability-based access control
    - Audit trail attribution
    - Trust score integration (via ReputationEngine)

    Attributes:
        agent_id: Unique identifier for the agent (UUID)
        agent_type: Type of agent (dev_agent, ops_agent, etc.)
        capability_set: Set of capabilities this agent has
        permission_level: Current permission level from ReputationEngine
        trust_score: Current reputation score (0-200, default 100)
        session_id: Optional session identifier for tracing
        metadata: Additional context metadata
    """
    agent_id: str
    agent_type: str = "unknown"
    capability_set: FrozenSet[str] = field(default_factory=frozenset)
    permission_level: str = "sandbox_only"
    trust_score: int = 100
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize the principal context."""
        # Ensure capability_set is a frozenset for immutability
        if not isinstance(self.capability_set, frozenset):
            object.__setattr__(
                self, 'capability_set', frozenset(self.capability_set)
            )
        # Ensure metadata is shallow-copied for immutability at the top level
        if self.metadata and not isinstance(self.metadata, dict):
            object.__setattr__(self, 'metadata', dict(self.metadata))

    def has_capability(self, capability: str) -> bool:
        """Check if this principal has a specific capability.

        Args:
            capability: Capability string to check (e.g., "file:write")

        Returns:
            True if the principal has the capability
        """
        return capability in self.capability_set

    def has_any_capability(self, capabilities: List[str]) -> bool:
        """Check if this principal has any of the specified capabilities.

        Args:
            capabilities: List of capability strings to check

        Returns:
            True if the principal has at least one capability
        """
        return bool(self.capability_set.intersection(capabilities))

    def has_all_capabilities(self, capabilities: List[str]) -> bool:
        """Check if this principal has all of the specified capabilities.

        Args:
            capabilities: List of capability strings to check

        Returns:
            True if the principal has all capabilities
        """
        return all(cap in self.capability_set for cap in capabilities)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization and telemetry."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capability_set": list(self.capability_set),
            "permission_level": self.permission_level,
            "trust_score": self.trust_score,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrincipalContext":
        """Create PrincipalContext from dictionary.

        Args:
            data: Dictionary with principal context fields

        Returns:
            PrincipalContext instance
        """
        capability_set = data.get("capability_set", [])
        if isinstance(capability_set, (list, set, frozenset)):
            # Handle both string values and CapabilityType enum members
            capability_set = frozenset(
                cap.value if isinstance(cap, Enum) else cap
                for cap in capability_set
            )

        return cls(
            agent_id=data.get("agent_id", str(uuid.uuid4())),
            agent_type=data.get("agent_type", "unknown"),
            capability_set=capability_set,
            permission_level=data.get("permission_level", "sandbox_only"),
            trust_score=data.get("trust_score", 100),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {}),
        )


# Default unknown principal for backward compatibility
# Convert CapabilityType enum values to strings for consistent has_capability() checks
UNKNOWN_PRINCIPAL = PrincipalContext(
    agent_id="00000000-0000-0000-0000-000000000000",
    agent_type="unknown",
    capability_set=frozenset(cap.value for cap in DEFAULT_CAPABILITIES["sandbox_only"]),
    permission_level="sandbox_only",
    trust_score=100,
)


def create_principal_context(
    agent_id: Optional[str] = None,
    agent_type: str = "unknown",
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> PrincipalContext:
    """
    Create a PrincipalContext with automatic capability resolution.

    This function integrates with ReputationEngine to resolve:
    - Permission level based on agent reputation
    - Trust score from reputation system
    - Capability set based on permission level

    Args:
        agent_id: Agent UUID (generated if not provided)
        agent_type: Type of agent (must be valid AgentType)
        session_id: Optional session identifier
        metadata: Additional context metadata

    Returns:
        PrincipalContext with resolved capabilities and trust score
    """
    # Generate agent_id if not provided
    if not agent_id:
        agent_id = str(uuid.uuid4())

    # Default values
    permission_level = "sandbox_only"
    trust_score = 100

    # Try to resolve from ReputationEngine
    try:
        from .reputation_engine import get_reputation_engine
        engine = get_reputation_engine()

        # Resolve agent UUID if agent_type provided
        resolved_id = engine.resolve_agent_uuid(agent_type)
        if resolved_id:
            agent_id = resolved_id
            permission_level = engine.get_permission_level(agent_id)
            trust_score = engine.get_reputation_score(agent_id)
            logger.debug(
                "[PrincipalContext] Resolved agent %s: level=%s, score=%d",
                agent_type, permission_level, trust_score
            )
    except Exception as e:
        logger.debug(
            "[PrincipalContext] ReputationEngine unavailable, using defaults: %s",
            e
        )

    # Get capability set for permission level
    capability_set = DEFAULT_CAPABILITIES.get(
        permission_level,
        DEFAULT_CAPABILITIES["sandbox_only"]
    )

    return PrincipalContext(
        agent_id=agent_id,
        agent_type=agent_type,
        capability_set=frozenset(cap.value for cap in capability_set),
        permission_level=permission_level,
        trust_score=trust_score,
        session_id=session_id,
        metadata=metadata or {},
    )


def get_principal_from_context(
    context: Optional[Dict[str, Any]] = None
) -> PrincipalContext:
    """
    Extract or create PrincipalContext from a context dictionary.

    This is a convenience function for extracting principal information
    from existing context dictionaries (e.g., from Flow v3 transitions).

    Args:
        context: Optional context dictionary that may contain principal info

    Returns:
        PrincipalContext (UNKNOWN_PRINCIPAL if no context provided)
    """
    if not context:
        return UNKNOWN_PRINCIPAL

    # Check if principal is already in context
    if "principal" in context:
        principal_data = context["principal"]
        if isinstance(principal_data, PrincipalContext):
            return principal_data
        if isinstance(principal_data, dict):
            return PrincipalContext.from_dict(principal_data)

    # Try to extract agent info from context
    agent_id = context.get("agent_id")
    agent_type = context.get("agent_type", "unknown")
    session_id = context.get("session_id")

    if agent_id or agent_type != "unknown":
        return create_principal_context(
            agent_id=agent_id,
            agent_type=agent_type,
            session_id=session_id,
            metadata={"source": "context_extraction"},
        )

    return UNKNOWN_PRINCIPAL


class PrincipalContextManager:
    """
    Thread-local manager for PrincipalContext propagation.

    This manager enables automatic principal context propagation
    through the call chain without explicit parameter passing.

    Usage:
        with PrincipalContextManager.set_context(principal):
            # All calls within this block will have access to principal
            enforcer.check_resource_access(...)
    """

    import threading
    _local = threading.local()

    @classmethod
    def get_current(cls) -> PrincipalContext:
        """Get the current principal context for this thread."""
        return getattr(cls._local, 'principal', UNKNOWN_PRINCIPAL)

    @classmethod
    def set_current(cls, principal: PrincipalContext) -> None:
        """Set the current principal context for this thread."""
        cls._local.principal = principal

    @classmethod
    def clear(cls) -> None:
        """Clear the current principal context."""
        cls._local.principal = UNKNOWN_PRINCIPAL

    @classmethod
    def set_context(cls, principal: PrincipalContext):
        """Context manager for setting principal context.

        Usage:
            with PrincipalContextManager.set_context(principal):
                # principal is available via get_current()
                pass
        """
        return _PrincipalContextScope(principal)


class _PrincipalContextScope:
    """Context manager scope for PrincipalContext."""

    def __init__(self, principal: PrincipalContext):
        self.principal = principal
        self.previous: Optional[PrincipalContext] = None

    def __enter__(self) -> PrincipalContext:
        self.previous = PrincipalContextManager.get_current()
        PrincipalContextManager.set_current(self.principal)
        return self.principal

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.previous is not None:
            PrincipalContextManager.set_current(self.previous)
        else:
            PrincipalContextManager.clear()
