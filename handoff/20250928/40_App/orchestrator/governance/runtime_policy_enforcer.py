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
    from governance.principal_context import PrincipalContext

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
    # Phase E-5: Content Safety violations
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    HARMFUL_CONTENT = "harmful_content"
    PII_DETECTED = "pii_detected"


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
        principal: Optional["PrincipalContext"] = None,
    ) -> PolicyCheckResult:
        """
        Check if a resource access operation is allowed.

        Args:
            operation: Type of operation (read, write, delete, execute, network)
            resource: Resource path or identifier
            context: Additional context (task_id, trace_id, etc.)
            principal: Agent identity context for capability-based checks (Phase E-2)

        Returns:
            PolicyCheckResult with allowed status and enforcement action
        """
        context = context or {}

        # Phase E-2: Extract or create principal context
        if principal is None:
            from governance.principal_context import get_principal_from_context
            principal = get_principal_from_context(context)

        # Add principal to context for downstream use
        context["principal"] = principal.to_dict() if hasattr(principal, 'to_dict') else principal

        telemetry_event = self._create_telemetry_event(
            "resource_access_check",
            operation=operation,
            resource=resource,
            context=context,
            principal=context.get("principal"),
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

    # Allowlist of safe commands for shell execution (Security Fix #3717)
    # Blueprint Alignment: Section 3.3 Agent Catalog V2 "Safety/Compliance layer gating"
    # Only these commands are permitted - all others are blocked by default
    ALLOWED_SHELL_COMMANDS = frozenset({
        # Version control
        "git",
        # Package managers
        "npm", "npx", "yarn", "pnpm", "pip", "pip3", "poetry", "cargo", "go",
        # Build tools
        "make", "cmake", "gradle", "mvn",
        # Language runtimes
        "python", "python3", "node", "deno", "bun", "ruby", "java", "javac",
        # Testing tools
        "pytest", "jest", "mocha", "vitest", "cargo-test",
        # Linting/formatting
        "eslint", "prettier", "black", "ruff", "flake8", "mypy", "tsc",
        # File operations (read-only or safe)
        "ls", "cat", "head", "tail", "grep", "rg", "find", "wc", "diff",
        "pwd", "echo", "env", "which", "whoami", "date", "uname",
        # Directory navigation and file management
        "cd", "mkdir", "touch", "rm", "cp", "mv",
        # Process inspection
        "ps", "top", "htop",
        # Network diagnostics (read-only)
        "curl", "wget", "ping", "dig", "nslookup", "host",
        # Docker (read-only operations)
        "docker",
        # Misc safe utilities (xargs/sed/awk removed - can execute arbitrary commands)
        "jq", "yq", "sort", "uniq", "tr", "cut",
    })

    # Commands that are always blocked regardless of allowlist
    BLOCKED_SHELL_COMMANDS = frozenset({
        "sudo", "su", "chown", "chmod", "chgrp",
        "mkfs", "fdisk", "parted", "mount", "umount",
        "dd", "shred", "wipefs",
        "iptables", "ip6tables", "nft", "firewall-cmd",
        "systemctl", "service", "init",
        "useradd", "userdel", "usermod", "groupadd", "groupdel",
        "passwd", "chpasswd",
        "reboot", "shutdown", "halt", "poweroff",
        "kill", "killall", "pkill",
        "nc", "netcat", "ncat",
        "eval", "exec", "source",
    })

    # Note: Dangerous flag patterns for rm/chmod/docker are now validated
    # in _validate_command_args() with proper argument parsing instead of
    # substring matching (which can be bypassed). See gemini-code-assist review.

    def _check_shell_execution(
        self,
        command: str,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> PolicyCheckResult:
        """
        Check if shell command execution is allowed using allowlist-based validation.

        Security Fix #3717: Replaced denylist with allowlist approach.
        Blueprint Alignment: Section 3.3 Agent Catalog V2 "Safety/Compliance layer gating"

        Validation Pipeline:
        1. Parse command using shlex (fail-closed on parse error)
        2. Check if base command is in blocklist (always block)
        3. Check if base command is in allowlist (block if not)
        4. Check for dangerous flag combinations
        5. Additional validation for specific commands (rm, docker, etc.)
        """
        try:
            parts = shlex.split(command)
        except ValueError:
            telemetry_event["action"] = "block"
            telemetry_event["error"] = "Failed to parse shell command"
            telemetry_event["security_reason"] = "unparseable_command"
            self._log_policy_check(
                "shell_execution", command, "block", context,
                "Unparseable command (fail-closed)"
            )
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                "Shell execution blocked: unparseable command (fail-closed)",
                PolicyViolationType.SHELL_EXECUTION,
                telemetry_event,
            )

        if not parts:
            telemetry_event["action"] = "block"
            telemetry_event["security_reason"] = "empty_command"
            self._log_policy_check(
                "shell_execution", command, "block", context,
                "Empty command"
            )
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                "Shell execution blocked: empty command",
                PolicyViolationType.SHELL_EXECUTION,
                telemetry_event,
            )

        base_cmd = parts[0].split("/")[-1].lower()

        if base_cmd in self.BLOCKED_SHELL_COMMANDS:
            telemetry_event["action"] = "block"
            telemetry_event["blocked_command"] = base_cmd
            telemetry_event["security_reason"] = "blocklisted_command"
            self._log_policy_check(
                "shell_execution", command, "block", context,
                f"Blocklisted command: {base_cmd}"
            )
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                f"Shell execution blocked: '{base_cmd}' is not permitted",
                PolicyViolationType.SHELL_EXECUTION,
                telemetry_event,
            )

        if base_cmd not in self.ALLOWED_SHELL_COMMANDS:
            telemetry_event["action"] = "block"
            telemetry_event["unknown_command"] = base_cmd
            telemetry_event["security_reason"] = "not_in_allowlist"
            self._log_policy_check(
                "shell_execution", command, "block", context,
                f"Command not in allowlist: {base_cmd}"
            )
            self._emit_telemetry(telemetry_event)

            return self._create_blocked_result(
                f"Shell execution blocked: '{base_cmd}' is not in the allowed commands list",
                PolicyViolationType.SHELL_EXECUTION,
                telemetry_event,
            )

        # Validate command-specific dangerous flag combinations
        # (using proper argument parsing instead of substring matching)
        validation_result = self._validate_command_args(base_cmd, parts[1:], context, telemetry_event)
        if validation_result is not None:
            return validation_result

        telemetry_event["action"] = "allow"
        telemetry_event["allowed_command"] = base_cmd
        self._log_policy_check("shell_execution", command, "allow", context)
        self._emit_telemetry(telemetry_event)

        return self._create_allowed_result(
            f"Shell execution allowed: {command[:50]}{'...' if len(command) > 50 else ''}",
            telemetry_event,
        )

    def _validate_command_args(
        self,
        base_cmd: str,
        args: list,
        context: Dict[str, Any],
        telemetry_event: Dict[str, Any],
    ) -> Optional[PolicyCheckResult]:
        """
        Additional validation for specific commands.

        Returns PolicyCheckResult if blocked, None if allowed.
        """
        if base_cmd == "rm":
            flags = [a for a in args if a.startswith("-")]
            all_flags = "".join(flags).lower()
            has_recursive = "r" in all_flags or "--recursive" in [f.lower() for f in flags]
            has_force = "f" in all_flags or "--force" in [f.lower() for f in flags]

            if has_recursive and has_force:
                telemetry_event["action"] = "block"
                telemetry_event["dangerous_pattern"] = "rm with -r and -f flags"
                telemetry_event["security_reason"] = "dangerous_rm"
                self._log_policy_check(
                    "shell_execution", f"rm {' '.join(args)}", "block", context,
                    "rm with recursive and force flags"
                )
                self._emit_telemetry(telemetry_event)

                return self._create_blocked_result(
                    "Shell execution blocked: rm with recursive and force flags is not permitted",
                    PolicyViolationType.SHELL_EXECUTION,
                    telemetry_event,
                )

        if base_cmd == "docker":
            args_lower = [a.lower() for a in args]
            if "run" in args_lower or "exec" in args_lower:
                # Check for --privileged flag
                if "--privileged" in args_lower:
                    telemetry_event["action"] = "block"
                    telemetry_event["dangerous_pattern"] = "docker --privileged"
                    telemetry_event["security_reason"] = "privileged_docker"
                    self._log_policy_check(
                        "shell_execution", f"docker {' '.join(args)}", "block", context,
                        "docker with --privileged flag"
                    )
                    self._emit_telemetry(telemetry_event)

                    return self._create_blocked_result(
                        "Shell execution blocked: docker with --privileged is not permitted",
                        PolicyViolationType.SHELL_EXECUTION,
                        telemetry_event,
                    )

                # Check for dangerous volume mounts (root filesystem access)
                # Handles both "-v /:/host" and "-v=/:/host" syntax patterns
                for i, arg in enumerate(args):
                    arg_lower = arg.lower()
                    # Check for -v=/:/... or --volume=/:/... patterns
                    if arg_lower.startswith("-v=") or arg_lower.startswith("--volume="):
                        volume_spec = arg.split("=", 1)[1] if "=" in arg else ""
                        if volume_spec.startswith("/:/"):
                            telemetry_event["action"] = "block"
                            telemetry_event["dangerous_pattern"] = "docker root volume mount"
                            telemetry_event["security_reason"] = "root_volume_mount"
                            self._log_policy_check(
                                "shell_execution", f"docker {' '.join(args)}", "block", context,
                                "docker with root filesystem volume mount"
                            )
                            self._emit_telemetry(telemetry_event)

                            return self._create_blocked_result(
                                "Shell execution blocked: docker with root filesystem volume mount is not permitted",
                                PolicyViolationType.SHELL_EXECUTION,
                                telemetry_event,
                            )
                    # Check for -v /:/... or --volume /:/... patterns (space-separated)
                    elif arg_lower in ("-v", "--volume") and i + 1 < len(args):
                        next_arg = args[i + 1]
                        if next_arg.startswith("/:/"):
                            telemetry_event["action"] = "block"
                            telemetry_event["dangerous_pattern"] = "docker root volume mount"
                            telemetry_event["security_reason"] = "root_volume_mount"
                            self._log_policy_check(
                                "shell_execution", f"docker {' '.join(args)}", "block", context,
                                "docker with root filesystem volume mount"
                            )
                            self._emit_telemetry(telemetry_event)

                            return self._create_blocked_result(
                                "Shell execution blocked: docker with root filesystem volume mount is not permitted",
                                PolicyViolationType.SHELL_EXECUTION,
                                telemetry_event,
                            )

        return None

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

    def check_content_safety(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        principal: Optional["PrincipalContext"] = None,
        scan_pii: bool = True,
        scan_content_safety: bool = True,
    ) -> PolicyCheckResult:
        """
        Check content for safety violations (Phase E-5).

        Integrates ContentSafetyScanner and PIIScanner into unified safety check.
        Emits telemetry events for Safety Dashboard metrics and audit trail.

        Blueprint Reference: Section 4.1 (Safety Governor v2), Section 4.2 (Compliance Radar v2)

        Args:
            content: Content to scan for safety violations
            context: Additional context (task_id, trace_id, etc.)
            principal: Agent identity context for capability-based checks
            scan_pii: Whether to scan for PII (default: True)
            scan_content_safety: Whether to scan for prompt injection/jailbreak (default: True)

        Returns:
            PolicyCheckResult with safety scan results and enforcement action
        """
        import time as time_module
        start_time = time_module.time()
        context = context or {}

        # Phase E-2: Extract or create principal context
        if principal is None:
            from governance.principal_context import get_principal_from_context
            principal = get_principal_from_context(context)

        context["principal"] = principal.to_dict() if hasattr(principal, 'to_dict') else principal

        telemetry_event = self._create_telemetry_event(
            "content_safety_check",
            content_length=len(content),
            scan_pii=scan_pii,
            scan_content_safety=scan_content_safety,
            context=context,
            principal=context.get("principal"),
        )

        findings = []
        highest_risk = "none"
        action = EnforcementAction.ALLOW
        violation_type = None
        reason = "Content safety check passed"

        try:
            # Content Safety Scan (Prompt Injection, Jailbreak, Harmful Content)
            if scan_content_safety:
                content_result = self._scan_content_safety(content, context)
                if content_result:
                    findings.extend(content_result.get("findings", []))
                    if content_result.get("risk_level", "none") in ("critical", "high"):
                        highest_risk = content_result["risk_level"]
                        action = self._map_safety_action(content_result.get("action", "allow"))
                        violation_type = self._map_content_violation_type(content_result)
                        reason = content_result.get("summary", "Content safety violation detected")

            # PII Scan
            if scan_pii and action == EnforcementAction.ALLOW:
                pii_result = self._scan_pii(content, context)
                if pii_result:
                    findings.extend(pii_result.get("findings", []))
                    # PIIScanResult uses "overall_risk" not "risk_level"
                    pii_risk = pii_result.get("overall_risk", "none")
                    if pii_risk in ("critical", "high") or (
                        pii_risk == "medium" and highest_risk == "none"
                    ):
                        highest_risk = pii_risk
                        action = self._map_safety_action(pii_result.get("action", "allow"))
                        if action != EnforcementAction.ALLOW:
                            violation_type = PolicyViolationType.PII_DETECTED
                            reason = pii_result.get("summary", "PII detected in content")

            # Calculate scan duration
            scan_duration_ms = (time_module.time() - start_time) * 1000

            # Update telemetry event
            telemetry_event["action"] = action.value
            telemetry_event["risk_level"] = highest_risk
            telemetry_event["findings_count"] = len(findings)
            telemetry_event["scan_duration_ms"] = scan_duration_ms
            telemetry_event["scan_pii_enabled"] = scan_pii
            telemetry_event["scan_content_safety_enabled"] = scan_content_safety

            # Log and emit telemetry
            self._log_safety_check(content, action.value, highest_risk, len(findings), context)
            self._emit_telemetry(telemetry_event)

            # Emit SSOT telemetry for Safety Dashboard
            self._emit_safety_telemetry(telemetry_event, findings, context)

            if action == EnforcementAction.ALLOW:
                return self._create_allowed_result(reason, telemetry_event)
            else:
                return PolicyCheckResult(
                    allowed=False,
                    action=action,
                    reason=reason,
                    violation_type=violation_type,
                    context={"findings": findings, "risk_level": highest_risk},
                    telemetry_event=telemetry_event,
                )

        except Exception as e:
            scan_duration_ms = (time_module.time() - start_time) * 1000
            telemetry_event["action"] = "allow"
            telemetry_event["error"] = str(e)
            telemetry_event["scan_duration_ms"] = scan_duration_ms
            self._log_safety_check(content, "allow", "error", 0, context, str(e))
            self._emit_telemetry(telemetry_event)

            logger.warning(
                "[RuntimePolicyEnforcer] Content safety check failed, allowing by default: %s",
                e,
                extra={"operation": "content_safety_check", "error": str(e)},
            )
            return self._create_allowed_result(
                f"Content safety check failed (fail-open): {e}",
                telemetry_event,
            )

    def _scan_content_safety(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Scan content for prompt injection, jailbreak, and harmful content."""
        try:
            from governance.content_safety_scanner import get_content_safety_scanner
            scanner = get_content_safety_scanner()
            result = scanner.scan(content)
            return result.to_dict()
        except ImportError:
            logger.debug("[RuntimePolicyEnforcer] ContentSafetyScanner not available")
            return None
        except Exception as e:
            logger.warning(
                "[RuntimePolicyEnforcer] Content safety scan failed: %s",
                e,
                extra={"operation": "content_safety_scan", "error": str(e)},
            )
            return None

    def _scan_pii(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Scan content for PII."""
        try:
            from governance.pii_scanner import get_pii_scanner
            scanner = get_pii_scanner()
            result = scanner.scan(content)
            return result.to_dict()
        except ImportError:
            logger.debug("[RuntimePolicyEnforcer] PIIScanner not available")
            return None
        except Exception as e:
            logger.warning(
                "[RuntimePolicyEnforcer] PII scan failed: %s",
                e,
                extra={"operation": "pii_scan", "error": str(e)},
            )
            return None

    def _map_safety_action(self, action_str: str) -> EnforcementAction:
        """Map safety scanner action string to EnforcementAction."""
        action_map = {
            "allow": EnforcementAction.ALLOW,
            "block": EnforcementAction.BLOCK,
            "require_approval": EnforcementAction.REQUIRE_APPROVAL,
            "redact": EnforcementAction.BLOCK,  # Redact maps to block for now
            "log_only": EnforcementAction.LOG_ONLY,
        }
        return action_map.get(action_str.lower(), EnforcementAction.ALLOW)

    def _map_content_violation_type(
        self,
        result: Dict[str, Any],
    ) -> Optional[PolicyViolationType]:
        """Map content safety result to PolicyViolationType."""
        findings = result.get("findings", [])
        if not findings:
            return None

        # Check for specific violation types in findings
        for finding in findings:
            category = finding.get("category", "")
            if category == "prompt_injection":
                return PolicyViolationType.PROMPT_INJECTION
            elif category == "jailbreak":
                return PolicyViolationType.JAILBREAK
            elif category == "harmful_content":
                return PolicyViolationType.HARMFUL_CONTENT

        # Return None if no specific category matches (avoid misleading default)
        return None

    def _log_safety_check(
        self,
        content: str,
        action: str,
        risk_level: str,
        findings_count: int,
        context: Dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        """Log safety check for audit trail."""
        log_extra = {
            "operation": "content_safety_check",
            "content_length": len(content),
            "action": action,
            "risk_level": risk_level,
            "findings_count": findings_count,
            "context": context,
        }
        if error:
            log_extra["error"] = error

        if action == "block":
            logger.warning(
                "[RuntimePolicyEnforcer] Content safety check blocked: %s findings, risk=%s",
                findings_count,
                risk_level,
                extra=log_extra,
            )
        elif action == "require_approval":
            logger.info(
                "[RuntimePolicyEnforcer] Content safety check requires approval: %s findings, risk=%s",
                findings_count,
                risk_level,
                extra=log_extra,
            )
        else:
            logger.debug(
                "[RuntimePolicyEnforcer] Content safety check passed: risk=%s",
                risk_level,
                extra=log_extra,
            )

    def _emit_safety_telemetry(
        self,
        telemetry_event: Dict[str, Any],
        findings: list,
        context: Dict[str, Any],
    ) -> None:
        """
        Emit SSOT TelemetryRecordV3 span for Safety Dashboard.

        Phase E-5: Creates structured telemetry for safety scan results,
        enabling Safety Dashboard metrics and audit trail visualization.
        """
        if not self.settings.enable_ssot_telemetry:
            return

        try:
            from core.telemetry import (
                TelemetryRecordV3,
                SpanKind,
                StatusCode,
                create_span_context,
            )

            trace_id = context.get("trace_id")
            if not trace_id:
                return

            parent_span_id = context.get("current_span_id") or context.get("parent_span_id")
            span_context = create_span_context(
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

            action = telemetry_event.get("action", "allow")
            action_to_status = {
                "allow": StatusCode.OK,
                "block": StatusCode.ERROR,
                "require_approval": StatusCode.SKIPPED,
                "log_only": StatusCode.OK,
            }
            status_code = action_to_status.get(action, StatusCode.UNSET)

            # Create metrics from telemetry event
            metrics = {
                "content_length": float(telemetry_event.get("content_length", 0)),
                "findings_count": float(telemetry_event.get("findings_count", 0)),
                "scan_duration_ms": float(telemetry_event.get("scan_duration_ms", 0)),
            }

            # Create attributes with finding categories
            finding_categories = list(set(
                f.get("category", "unknown") for f in findings
            )) if findings else []

            attributes = {
                "risk_level": telemetry_event.get("risk_level", "none"),
                "scan_pii_enabled": telemetry_event.get("scan_pii_enabled", True),
                "scan_content_safety_enabled": telemetry_event.get("scan_content_safety_enabled", True),
                "finding_categories": finding_categories,
            }

            record = TelemetryRecordV3.create(
                name="governance.content_safety_check",
                span_context=span_context,
                component="RuntimePolicyEnforcer",
                kind=SpanKind.INTERNAL,
                status_code=status_code,
                epic_tag="EPIC-E",
                metrics=metrics,
                attributes=attributes,
            )
            record.emit()

        except ImportError as import_err:
            logger.debug(
                "[RuntimePolicyEnforcer] core.telemetry not available for safety telemetry: %s",
                import_err
            )
        except Exception as emit_err:
            logger.debug(
                "[RuntimePolicyEnforcer] Failed to emit safety telemetry: %s",
                emit_err,
                exc_info=True
            )

    def check_cost(
        self,
        task_id: str,
        estimated_tokens: int,
        model: str = "qwen-plus",
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
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a telemetry event for Owner Console Policy Dashboard.

        Issue #3578 Phase 2: Extracts trace_id and parent_span_id from context
        to enable SSOT span hierarchy when ENABLE_SSOT_TELEMETRY is enabled.

        Args:
            event_type: Type of event (e.g., "resource_access_check", "cost_check")
            context: Optional context dict containing trace_id and parent_span_id
            **kwargs: Additional event attributes

        Returns:
            Dict containing the telemetry event
        """
        event = {
            "event_type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "component": "RuntimePolicyEnforcer",
            **kwargs,
        }
        # Issue #3578 Phase 2: Extract trace_id and parent_span_id from context
        # Priority: current_span_id > parent_span_id
        # current_span_id comes from node_metrics decorator (Phase 1) and represents
        # the current node's span. Policy spans should be children of node spans,
        # so current_span_id becomes the parent_span_id for policy events.
        if context:
            if "trace_id" in context:
                event["trace_id"] = context["trace_id"]
            if "current_span_id" in context:
                event["parent_span_id"] = context["current_span_id"]
            elif "parent_span_id" in context:
                event["parent_span_id"] = context["parent_span_id"]
        return event

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

        Issue #3578 Phase 2: When ENABLE_SSOT_TELEMETRY is enabled, also emits
        TelemetryRecordV3 spans using the from_policy_telemetry_event adapter.
        """
        logger.info(
            "[RuntimePolicyEnforcer] Telemetry event: %s",
            event.get("event_type", "unknown"),
            extra={
                "operation": "telemetry_emit",
                "telemetry_event": event,
            }
        )

        # Issue #3578 Phase 2: Emit SSOT TelemetryRecordV3 span
        if self.settings.enable_ssot_telemetry:
            try:
                from core.telemetry import from_policy_telemetry_event
                trace_id = event.get("trace_id")
                parent_span_id = event.get("parent_span_id")
                if trace_id:
                    record = from_policy_telemetry_event(
                        event_dict=event,
                        trace_id=trace_id,
                        parent_span_id=parent_span_id,
                    )
                    record.emit()
            except ImportError as import_err:
                logger.debug(
                    f"[RuntimePolicyEnforcer] core.telemetry not available, skipping SSOT spans: {import_err}"
                )
            except Exception as emit_err:
                logger.debug(
                    f"[RuntimePolicyEnforcer] Failed to emit SSOT span: {emit_err}",
                    exc_info=True
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
