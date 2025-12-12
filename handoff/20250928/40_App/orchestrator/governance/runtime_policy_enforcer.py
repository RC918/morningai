"""
Runtime Policy Enforcer - Safety Governor v2

This module provides runtime policy enforcement for the MorningAI orchestrator,
integrating PolicyGuard, CostTracker, and ExecutionPolicy into a unified
enforcement layer.

Epic #2311 Phase 2: Policy 執行驗證 - 在 runtime 執行政策 (deny writes, respect cost budgets)

Components:
1. RuntimePolicyEnforcer - Main enforcement class with block/log/telemetry
2. PolicyCheckResult - Result of policy checks
3. EnforcementAction - Actions to take on policy violations

Enforcement Points:
1. AutonomousExecutor - Before LLM generates actions (deny dangerous behaviors)
2. worker.py - Before actual execution (block harmful operations)

Flow: plan → check policy → approve → execute → check cost → complete
"""
import logging
import shlex
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from common.config.settings import Settings

logger = logging.getLogger(__name__)


class EnforcementAction(Enum):
    """Actions that can be taken when a policy check fails"""
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    DEGRADE_MODEL = "degrade_model"
    FALLBACK = "fallback"
    LOG_ONLY = "log_only"


class PolicyViolationType(Enum):
    """Types of policy violations"""
    RESOURCE_ACCESS = "resource_access"
    NETWORK_ACCESS = "network_access"
    SHELL_EXECUTION = "shell_execution"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    COST_BUDGET_EXCEEDED = "cost_budget_exceeded"
    TOKEN_BUDGET_EXCEEDED = "token_budget_exceeded"
    SANDBOX_BOUNDARY = "sandbox_boundary"
    TOOL_PERMISSION = "tool_permission"
    RISK_LEVEL = "risk_level"


@dataclass
class PolicyCheckResult:
    """Result of a policy check"""
    allowed: bool
    action: EnforcementAction
    reason: str
    violation_type: Optional[PolicyViolationType] = None
    context: Dict[str, Any] = field(default_factory=dict)
    telemetry_event: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "allowed": self.allowed,
            "action": self.action.value,
            "reason": self.reason,
            "violation_type": self.violation_type.value if self.violation_type else None,
            "context": self.context,
            "telemetry_event": self.telemetry_event,
        }


@dataclass
class CostCheckResult:
    """Result of a cost/budget check"""
    allowed: bool
    action: EnforcementAction
    reason: str
    current_tokens: int = 0
    max_tokens: int = 0
    current_usd: float = 0.0
    max_usd: float = 0.0
    budget_type: str = "task"
    suggested_model: Optional[str] = None
    telemetry_event: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "allowed": self.allowed,
            "action": self.action.value,
            "reason": self.reason,
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "current_usd": self.current_usd,
            "max_usd": self.max_usd,
            "budget_type": self.budget_type,
            "suggested_model": self.suggested_model,
            "telemetry_event": self.telemetry_event,
        }


@dataclass
class EnforcementResult:
    """Result of enforcement action"""
    enforced: bool
    action_taken: EnforcementAction
    original_check: PolicyCheckResult
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "enforced": self.enforced,
            "action_taken": self.action_taken.value,
            "original_check": self.original_check.to_dict(),
            "timestamp": self.timestamp,
        }


class RuntimePolicyEnforcer:
    """
    Runtime policy enforcement for MorningAI orchestrator.

    Integrates:
    - PolicyGuard: file/network/tool access checks
    - CostTracker: token/USD budget tracking
    - ExecutionPolicy: operation whitelist, approval settings

    Provides three-phase enforcement:
    1. Block - Prevent dangerous operations
    2. Log - Record all policy checks
    3. Telemetry - Send events for Owner Console Policy Dashboard
    """

    def __init__(self, settings: "Settings" = None):
        """
        Initialize RuntimePolicyEnforcer.

        Args:
            settings: Application settings. If None, uses global settings.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            settings = global_settings
        self.settings = settings

        self._policy_guard = None
        self._cost_tracker = None

    def reload_policies(self) -> None:
        """
        Reload runtime policies from settings / configuration source.

        This method:
        1. Reloads global settings via reload_settings()
        2. Resets PolicyGuard and CostTracker global singletons
        3. Resets this instance's lazy-loaded references

        Thread-safe when used with the global enforcer via _enforcer_lock.
        Note: Does NOT overwrite self.settings to preserve custom settings
        passed during initialization (e.g., in tests).

        Use cases:
        - Dynamic configuration updates without restart
        - Testing with different policy configurations
        - Hot-reloading after Owner Console policy changes
        """
        from common.config.settings import reload_settings
        import governance.policy_guard as policy_guard_module
        import governance.cost_tracker as cost_tracker_module

        reload_settings()

        policy_guard_module._policy_guard = None
        cost_tracker_module._cost_tracker = None

        self._policy_guard = None
        self._cost_tracker = None

        logger.info(
            "[RuntimePolicyEnforcer] Policies reloaded",
            extra={
                "operation": "reload_policies",
                "cost_exceeded_action": getattr(self.settings, "cost_exceeded_action", "block"),
            },
        )

    @property
    def policy_guard(self):
        """Lazy-load PolicyGuard"""
        if self._policy_guard is None:
            from governance.policy_guard import get_policy_guard
            self._policy_guard = get_policy_guard()
        return self._policy_guard

    @property
    def cost_tracker(self):
        """Lazy-load CostTracker"""
        if self._cost_tracker is None:
            from governance.cost_tracker import get_cost_tracker
            self._cost_tracker = get_cost_tracker()
        return self._cost_tracker

    def check_resource_access(
        self,
        operation: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyCheckResult:
        """
        Check if a resource access operation is allowed.

        Args:
            operation: Type of operation (read, write, delete, execute, network)
            resource: Resource path or identifier
            context: Additional context (task_id, trace_id, etc.)

        Returns:
            PolicyCheckResult with allowed status and enforcement action
        """
        context = context or {}
        telemetry_event = self._create_telemetry_event(
            "resource_access_check",
            operation=operation,
            resource=resource,
            context=context,
        )

        try:
            if operation == "write":
                return self._check_write_access(resource, context, telemetry_event)
            elif operation == "delete":
                return self._check_delete_access(resource, context, telemetry_event)
            elif operation == "network":
                return self._check_network_access(resource, context, telemetry_event)
            elif operation == "execute":
                return self._check_shell_execution(resource, context, telemetry_event)
            elif operation == "read":
                return self._check_read_access(resource, context, telemetry_event)
            else:
                return self._create_allowed_result(
                    f"Unknown operation '{operation}' allowed by default",
                    telemetry_event,
                )
        except Exception as e:
            logger.error(
                "[RuntimePolicyEnforcer] Error checking resource access: %s",
                str(e),
                extra={
                    "operation": "resource_access_check_error",
                    "error": str(e),
                    "resource": resource,
                }
            )
            return self._create_blocked_result(
                f"Error during policy check: {e}",
                PolicyViolationType.RESOURCE_ACCESS,
                telemetry_event,
            )

    def _check_write_access(
        self,
        resource: str,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Check if write access to a resource is allowed"""
        try:
            self.policy_guard.check_file_access(resource)

            risk_level = self.policy_guard.check_risk_level([resource])
            if risk_level == "high_risk":
                telemetry_event["risk_level"] = risk_level
                telemetry_event["action"] = "require_approval"
                self._log_policy_check("write_access", resource, "require_approval", context)
                self._emit_telemetry(telemetry_event)

                return PolicyCheckResult(
                    allowed=False,
                    action=EnforcementAction.REQUIRE_APPROVAL,
                    reason=f"Write to high-risk resource requires approval: {resource}",
                    violation_type=PolicyViolationType.FILE_WRITE,
                    context=context,
                    telemetry_event=telemetry_event,
                )

            telemetry_event["action"] = "allow"
            self._log_policy_check("write_access", resource, "allow", context)
            self._emit_telemetry(telemetry_event)

            return self._create_allowed_result(
                f"Write access allowed: {resource}",
                telemetry_event,
            )

        except Exception as e:
            telemetry_event["action"] = "block"
            telemetry_event["error"] = str(e)
            self._log_policy_check("write_access", resource, "block", context, str(e))
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                f"Write access denied: {e}",
                PolicyViolationType.FILE_WRITE,
                telemetry_event,
            )

    def _check_delete_access(
        self,
        resource: str,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Check if delete access to a resource is allowed"""
        telemetry_event["action"] = "require_approval"
        self._log_policy_check("delete_access", resource, "require_approval", context)
        self._emit_telemetry(telemetry_event)

        return PolicyCheckResult(
            allowed=False,
            action=EnforcementAction.REQUIRE_APPROVAL,
            reason=f"Delete operations always require approval: {resource}",
            violation_type=PolicyViolationType.FILE_DELETE,
            context=context,
            telemetry_event=telemetry_event,
        )

    def _check_network_access(
        self,
        domain: str,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Check if network access to a domain is allowed"""
        try:
            self.policy_guard.check_network_access(domain)

            telemetry_event["action"] = "allow"
            self._log_policy_check("network_access", domain, "allow", context)
            self._emit_telemetry(telemetry_event)

            return self._create_allowed_result(
                f"Network access allowed: {domain}",
                telemetry_event,
            )

        except Exception as e:
            telemetry_event["action"] = "block"
            telemetry_event["error"] = str(e)
            self._log_policy_check("network_access", domain, "block", context, str(e))
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                f"Network access denied: {e}",
                PolicyViolationType.NETWORK_ACCESS,
                telemetry_event,
            )

    def _check_shell_execution(
        self,
        command: str,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Check if shell command execution is allowed"""
        dangerous_substrings = ["rm -rf", "sudo", "chmod 777", "chown", "> /dev/", "mkfs", "dd if="]
        lower_cmd = command.lower()

        for pattern in dangerous_substrings:
            if pattern in lower_cmd:
                telemetry_event["action"] = "block"
                telemetry_event["dangerous_pattern"] = pattern
                self._log_policy_check("shell_execution", command, "block", context, f"Dangerous pattern: {pattern}")
                self._emit_telemetry(telemetry_event)

                return self._create_blocked_result(
                    f"Shell execution blocked: dangerous pattern '{pattern}' detected",
                    PolicyViolationType.SHELL_EXECUTION,
                    telemetry_event,
                )

        try:
            parts = shlex.split(command)
        except ValueError:
            telemetry_event["action"] = "block"
            telemetry_event["error"] = "Failed to parse shell command"
            self._log_policy_check("shell_execution", command, "block", context, "Unparseable command (fail-closed)")
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                "Shell execution blocked: unparseable command (fail-closed)",
                PolicyViolationType.SHELL_EXECUTION,
                telemetry_event,
            )

        if parts:
            base_cmd = parts[0].lower()
            if base_cmd == "rm":
                flags = [p for p in parts[1:] if p.startswith("-")]
                all_flags = "".join(flags).lower()
                if "r" in all_flags and "f" in all_flags:
                    telemetry_event["action"] = "block"
                    telemetry_event["dangerous_pattern"] = "rm with -r and -f flags"
                    self._log_policy_check("shell_execution", command, "block", context, "rm with recursive and force flags")
                    self._emit_telemetry(telemetry_event)

                    return self._create_blocked_result(
                        "Shell execution blocked: rm with recursive and force flags detected",
                        PolicyViolationType.SHELL_EXECUTION,
                        telemetry_event,
                    )

        telemetry_event["action"] = "allow"
        self._log_policy_check("shell_execution", command, "allow", context)
        self._emit_telemetry(telemetry_event)

        return self._create_allowed_result(
            f"Shell execution allowed: {command[:50]}...",
            telemetry_event,
        )

    def _check_read_access(
        self,
        resource: str,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Check if read access to a resource is allowed"""
        try:
            self.policy_guard.check_file_access(resource)

            telemetry_event["action"] = "allow"
            self._log_policy_check("read_access", resource, "allow", context)
            self._emit_telemetry(telemetry_event)

            return self._create_allowed_result(
                f"Read access allowed: {resource}",
                telemetry_event,
            )

        except Exception as e:
            telemetry_event["action"] = "block"
            telemetry_event["error"] = str(e)
            self._log_policy_check("read_access", resource, "block", context, str(e))
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                f"Read access denied: {e}",
                PolicyViolationType.RESOURCE_ACCESS,
                telemetry_event,
            )

    def check_cost(
        self,
        task_id: str,
        estimated_tokens: int,
        model: str = "gpt-4",
        context: Optional[Dict[str, Any]] = None,
    ) -> CostCheckResult:
        """
        Check if cost/token budget allows the operation.

        Args:
            task_id: Task identifier for tracking
            estimated_tokens: Estimated tokens for this operation
            model: Model to use (for cost estimation)
            context: Additional context

        Returns:
            CostCheckResult with allowed status and suggested actions
        """
        context = context or {}
        telemetry_event = self._create_telemetry_event(
            "cost_check",
            task_id=task_id,
            estimated_tokens=estimated_tokens,
            model=model,
            context=context,
        )

        try:
            task_check = self._check_task_budget(task_id, estimated_tokens, model, telemetry_event)
            if not task_check.allowed:
                return task_check

            daily_check = self._check_daily_budget(task_id, estimated_tokens, model, telemetry_event)
            if not daily_check.allowed:
                return daily_check

            telemetry_event["action"] = "allow"
            self._log_cost_check(task_id, estimated_tokens, model, "allow")
            self._emit_telemetry(telemetry_event)

            return CostCheckResult(
                allowed=True,
                action=EnforcementAction.ALLOW,
                reason="Cost check passed",
                current_tokens=daily_check.current_tokens,
                max_tokens=daily_check.max_tokens,
                current_usd=daily_check.current_usd,
                max_usd=daily_check.max_usd,
                budget_type="all",
                telemetry_event=telemetry_event,
            )

        except Exception as e:
            logger.error(
                "[RuntimePolicyEnforcer] Error checking cost: %s",
                str(e),
                extra={
                    "operation": "cost_check_error",
                    "error": str(e),
                    "task_id": task_id,
                }
            )
            telemetry_event["action"] = "block"
            telemetry_event["error"] = str(e)
            self._emit_telemetry(telemetry_event)

            return CostCheckResult(
                allowed=False,
                action=EnforcementAction.BLOCK,
                reason=f"Cost check failed (fail-closed): {e}",
                violation_type=PolicyViolationType.COST_BUDGET_EXCEEDED,
                telemetry_event=telemetry_event,
            )

    def _check_task_budget(
        self,
        task_id: str,
        estimated_tokens: int,
        model: str,
        telemetry_event: Dict[str, Any],
    ) -> CostCheckResult:
        """Check per-task token budget"""
        within_budget, metrics, budget = self.cost_tracker.check_budget(task_id, "task")

        max_tokens = budget.get("max_tokens", float("inf"))
        max_usd = budget.get("max_usd", float("inf"))

        projected_tokens = metrics.tokens + estimated_tokens
        estimated_cost = self.cost_tracker.estimate_cost(estimated_tokens, model)
        projected_usd = metrics.usd + estimated_cost

        if projected_tokens > max_tokens:
            action = self._determine_cost_action("token", projected_tokens, max_tokens)
            telemetry_event["action"] = action.value
            telemetry_event["budget_type"] = "task"
            telemetry_event["projected_tokens"] = projected_tokens
            telemetry_event["max_tokens"] = max_tokens
            self._log_cost_check(task_id, estimated_tokens, model, action.value, "task token budget exceeded")
            self._emit_telemetry(telemetry_event)

            return CostCheckResult(
                allowed=action == EnforcementAction.ALLOW,
                action=action,
                reason=f"Task token budget exceeded: {projected_tokens}/{max_tokens}",
                current_tokens=metrics.tokens,
                max_tokens=int(max_tokens) if max_tokens != float("inf") else 0,
                budget_type="task",
                suggested_model=self._suggest_cheaper_model(model) if action == EnforcementAction.DEGRADE_MODEL else None,
                telemetry_event=telemetry_event,
            )

        if projected_usd > max_usd:
            action = self._determine_cost_action("usd", projected_usd, max_usd)
            telemetry_event["action"] = action.value
            telemetry_event["budget_type"] = "task"
            telemetry_event["projected_usd"] = projected_usd
            telemetry_event["max_usd"] = max_usd
            self._log_cost_check(task_id, estimated_tokens, model, action.value, "task USD budget exceeded")
            self._emit_telemetry(telemetry_event)

            return CostCheckResult(
                allowed=action == EnforcementAction.ALLOW,
                action=action,
                reason=f"Task USD budget exceeded: ${projected_usd:.2f}/${max_usd:.2f}",
                current_usd=metrics.usd,
                max_usd=float(max_usd) if max_usd != float("inf") else 0.0,
                budget_type="task",
                suggested_model=self._suggest_cheaper_model(model) if action == EnforcementAction.DEGRADE_MODEL else None,
                telemetry_event=telemetry_event,
            )

        return CostCheckResult(
            allowed=True,
            action=EnforcementAction.ALLOW,
            reason="Task budget check passed",
            current_tokens=metrics.tokens,
            max_tokens=int(max_tokens) if max_tokens != float("inf") else 0,
            current_usd=metrics.usd,
            max_usd=float(max_usd) if max_usd != float("inf") else 0.0,
            budget_type="task",
            telemetry_event=telemetry_event,
        )

    def _check_daily_budget(
        self,
        task_id: str,
        estimated_tokens: int,
        model: str,
        telemetry_event: Dict[str, Any],
    ) -> CostCheckResult:
        """Check daily token/USD budget"""
        within_budget, metrics, budget = self.cost_tracker.check_budget(task_id, "daily")

        max_tokens = budget.get("max_tokens", float("inf"))
        max_usd = budget.get("max_usd", float("inf"))

        projected_tokens = metrics.tokens + estimated_tokens
        estimated_cost = self.cost_tracker.estimate_cost(estimated_tokens, model)
        projected_usd = metrics.usd + estimated_cost

        if projected_tokens > max_tokens:
            action = self._determine_cost_action("token", projected_tokens, max_tokens)
            telemetry_event["action"] = action.value
            telemetry_event["budget_type"] = "daily"
            telemetry_event["projected_tokens"] = projected_tokens
            telemetry_event["max_tokens"] = max_tokens
            self._log_cost_check(task_id, estimated_tokens, model, action.value, "daily token budget exceeded")
            self._emit_telemetry(telemetry_event)

            return CostCheckResult(
                allowed=action == EnforcementAction.ALLOW,
                action=action,
                reason=f"Daily token budget exceeded: {projected_tokens}/{max_tokens}",
                current_tokens=metrics.tokens,
                max_tokens=int(max_tokens) if max_tokens != float("inf") else 0,
                budget_type="daily",
                suggested_model=self._suggest_cheaper_model(model) if action == EnforcementAction.DEGRADE_MODEL else None,
                telemetry_event=telemetry_event,
            )

        if projected_usd > max_usd:
            action = self._determine_cost_action("usd", projected_usd, max_usd)
            telemetry_event["action"] = action.value
            telemetry_event["budget_type"] = "daily"
            telemetry_event["projected_usd"] = projected_usd
            telemetry_event["max_usd"] = max_usd
            self._log_cost_check(task_id, estimated_tokens, model, action.value, "daily USD budget exceeded")
            self._emit_telemetry(telemetry_event)

            return CostCheckResult(
                allowed=action == EnforcementAction.ALLOW,
                action=action,
                reason=f"Daily USD budget exceeded: ${projected_usd:.2f}/${max_usd:.2f}",
                current_usd=metrics.usd,
                max_usd=float(max_usd) if max_usd != float("inf") else 0.0,
                budget_type="daily",
                suggested_model=self._suggest_cheaper_model(model) if action == EnforcementAction.DEGRADE_MODEL else None,
                telemetry_event=telemetry_event,
            )

        return CostCheckResult(
            allowed=True,
            action=EnforcementAction.ALLOW,
            reason="Daily budget check passed",
            current_tokens=metrics.tokens,
            max_tokens=int(max_tokens) if max_tokens != float("inf") else 0,
            current_usd=metrics.usd,
            max_usd=float(max_usd) if max_usd != float("inf") else 0.0,
            budget_type="daily",
            telemetry_event=telemetry_event,
        )

    def _determine_cost_action(
        self,
        budget_type: str,
        current: float,
        limit: float,
    ) -> EnforcementAction:
        """
        Determine action based on budget overage.

        Args:
            budget_type: Type of budget exceeded ("token" or "usd")
            current: Current/projected value that exceeded the limit
            limit: The budget limit that was exceeded

        Actions based on settings:
        - block: Stop execution
        - degrade_model: Switch to cheaper model
        - require_approval: Request human approval
        - fallback: Use fallback mode
        """
        cost_exceeded_action = getattr(self.settings, "cost_exceeded_action", "block")

        overage_ratio: Optional[float] = None
        if limit > 0:
            overage_ratio = current / limit

        logger.debug(
            "[RuntimePolicyEnforcer] Cost budget exceeded, determining action",
            extra={
                "operation": "cost_action_decision",
                "budget_type": budget_type,
                "current": current,
                "limit": limit,
                "overage_ratio": overage_ratio,
                "configured_action": cost_exceeded_action,
            },
        )

        if cost_exceeded_action == "degrade":
            return EnforcementAction.DEGRADE_MODEL
        elif cost_exceeded_action == "approval":
            return EnforcementAction.REQUIRE_APPROVAL
        elif cost_exceeded_action == "fallback":
            return EnforcementAction.FALLBACK
        else:
            return EnforcementAction.BLOCK

    def _suggest_cheaper_model(self, current_model: str) -> Optional[str]:
        """Suggest a cheaper model alternative"""
        model_tiers = {
            "gpt-4": "gpt-3.5-turbo",
            "gpt-4-turbo": "gpt-3.5-turbo",
            "gpt-4o": "gpt-4o-mini",
            "claude-3-opus": "claude-3-sonnet",
            "claude-3-sonnet": "claude-3-haiku",
        }
        return model_tiers.get(current_model)

    def enforce(self, check_result: PolicyCheckResult) -> EnforcementResult:
        """
        Execute enforcement action based on policy check result.

        Args:
            check_result: Result from check_resource_access or similar

        Returns:
            EnforcementResult with action taken
        """
        if check_result.allowed:
            return EnforcementResult(
                enforced=False,
                action_taken=EnforcementAction.ALLOW,
                original_check=check_result,
            )

        logger.warning(
            "[RuntimePolicyEnforcer] Enforcing policy: %s",
            check_result.reason,
            extra={
                "operation": "policy_enforcement",
                "action": check_result.action.value,
                "violation_type": check_result.violation_type.value if check_result.violation_type else None,
            }
        )

        return EnforcementResult(
            enforced=True,
            action_taken=check_result.action,
            original_check=check_result,
        )

    def _create_allowed_result(
        self,
        reason: str,
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Create an allowed policy check result"""
        return PolicyCheckResult(
            allowed=True,
            action=EnforcementAction.ALLOW,
            reason=reason,
            telemetry_event=telemetry_event,
        )

    def _create_blocked_result(
        self,
        reason: str,
        violation_type: PolicyViolationType,
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """Create a blocked policy check result"""
        return PolicyCheckResult(
            allowed=False,
            action=EnforcementAction.BLOCK,
            reason=reason,
            violation_type=violation_type,
            telemetry_event=telemetry_event,
        )

    def _create_telemetry_event(
        self,
        event_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a telemetry event for Owner Console Policy Dashboard"""
        return {
            "event_type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "component": "RuntimePolicyEnforcer",
            **kwargs,
        }

    def _log_policy_check(
        self,
        check_type: str,
        resource: str,
        action: str,
        context: Dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        """Log policy check for audit trail"""
        log_extra = {
            "operation": f"policy_check_{check_type}",
            "resource": resource,
            "action": action,
            "context": context,
        }
        if error:
            log_extra["error"] = error

        if action == "block":
            logger.warning(
                "[RuntimePolicyEnforcer] Policy check blocked: %s on %s",
                check_type,
                resource,
                extra=log_extra,
            )
        elif action == "require_approval":
            logger.info(
                "[RuntimePolicyEnforcer] Policy check requires approval: %s on %s",
                check_type,
                resource,
                extra=log_extra,
            )
        else:
            logger.debug(
                "[RuntimePolicyEnforcer] Policy check allowed: %s on %s",
                check_type,
                resource,
                extra=log_extra,
            )

    def _log_cost_check(
        self,
        task_id: str,
        estimated_tokens: int,
        model: str,
        action: str,
        reason: Optional[str] = None,
    ) -> None:
        """Log cost check for audit trail"""
        log_extra = {
            "operation": "cost_check",
            "task_id": task_id,
            "estimated_tokens": estimated_tokens,
            "model": model,
            "action": action,
        }
        if reason:
            log_extra["reason"] = reason

        if action in ("block", "degrade_model", "require_approval"):
            logger.warning(
                "[RuntimePolicyEnforcer] Cost check %s: %s",
                action,
                reason or "budget exceeded",
                extra=log_extra,
            )
        else:
            logger.debug(
                "[RuntimePolicyEnforcer] Cost check passed for task %s",
                task_id,
                extra=log_extra,
            )

    def _emit_telemetry(self, event: Dict[str, Any]) -> None:
        """
        Emit telemetry event for Owner Console Policy Dashboard.

        This method sends events to the telemetry system for visualization
        in the Owner Console's Policy Dashboard.
        """
        logger.info(
            "[RuntimePolicyEnforcer] Telemetry event: %s",
            event.get("event_type", "unknown"),
            extra={
                "operation": "telemetry_emit",
                "telemetry_event": event,
            }
        )


_runtime_policy_enforcer: Optional[RuntimePolicyEnforcer] = None
_enforcer_lock = threading.Lock()


def get_runtime_policy_enforcer() -> RuntimePolicyEnforcer:
    """Get or create thread-safe global RuntimePolicyEnforcer instance"""
    global _runtime_policy_enforcer
    with _enforcer_lock:
        if _runtime_policy_enforcer is None:
            _runtime_policy_enforcer = RuntimePolicyEnforcer()
        return _runtime_policy_enforcer


def reload_runtime_policies() -> RuntimePolicyEnforcer:
    """
    Reload runtime policies for the global enforcer instance.

    Thread-safe helper that reloads policies on the global singleton.
    Creates the enforcer if it doesn't exist yet.

    Returns:
        The global RuntimePolicyEnforcer instance after reload
    """
    global _runtime_policy_enforcer
    with _enforcer_lock:
        if _runtime_policy_enforcer is None:
            _runtime_policy_enforcer = RuntimePolicyEnforcer()
        else:
            _runtime_policy_enforcer.reload_policies()
        return _runtime_policy_enforcer
