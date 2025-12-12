# Runtime Policy Enforcement

This document describes the runtime policy enforcement system implemented in Epic #2311.

## Overview

The RuntimePolicyEnforcer provides three-phase enforcement for all orchestrator operations:

1. **Block** - Prevent dangerous operations from executing
2. **Log** - Create audit trail for all policy checks
3. **Telemetry** - Emit events to Owner Console for monitoring

## Policy Categories

The system enforces policies across five categories with different fail-closed/fail-open behaviors:

| Category | Fail Mode | Rationale |
|----------|-----------|-----------|
| Shell Execution | fail-closed | Security-critical, dangerous commands must be blocked |
| Resource Access | fail-closed | File system access requires explicit validation |
| Cost/Budget | fail-closed | Prevent runaway costs, budget overruns |
| Network Access | fail-open | Non-critical, allow with logging for connectivity |
| Model Selection | fail-open | Graceful degradation preferred over blocking |

## Shell Command Parsing

The shell execution check uses a two-layer defense:

1. **Substring matching** - Fast first-pass check for known dangerous patterns like `rm -rf`, `sudo`, `chmod 777`
2. **shlex parsing** - Tokenize command to catch flag variants like `rm -f -r /` or `rm -Rf /`

For `rm` commands specifically, the system extracts all flags and checks for the presence of both recursive (`r`) and force (`f`) flags in any combination.

Unparseable commands (e.g., malformed shell syntax) are blocked under fail-closed policy.

## Cost Budget Enforcement

Cost checks validate estimated token usage against configured budgets:

- Per-task budget
- Daily budget
- USD limit

When cost check fails or encounters an error, the system returns `allowed=False` with `action=BLOCK` (fail-closed behavior).

## Thread-Safe Singleton

The global RuntimePolicyEnforcer instance uses thread-safe lazy initialization:

```python
_runtime_policy_enforcer: Optional[RuntimePolicyEnforcer] = None
_enforcer_lock = threading.Lock()

def get_runtime_policy_enforcer() -> RuntimePolicyEnforcer:
    global _runtime_policy_enforcer
    with _enforcer_lock:
        if _runtime_policy_enforcer is None:
            _runtime_policy_enforcer = RuntimePolicyEnforcer()
        return _runtime_policy_enforcer
```

Worker processes should call `get_runtime_policy_enforcer()` directly rather than maintaining their own global references.

## Configuration

Token estimation for policy checks is configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `META_AGENT_ESTIMATED_TOKENS` | 5000 | Estimated tokens for meta-agent tasks |
| `AUTO_FIX_ESTIMATED_TOKENS` | 2000 | Estimated tokens for auto-fix tasks |

## Integration Points

The RuntimePolicyEnforcer is integrated at these points:

1. **worker.py:run_meta_agent_task** - Cost check before meta-agent execution
2. **worker.py:run_auto_fix_task** - Cost check before auto-fix execution
3. **AutonomousExecutor** - Shell and resource access checks during execution

## Error Handling

All policy check methods follow consistent error handling:

- Security-critical categories (shell, resource, cost) use fail-closed
- Non-critical categories (network, model) use fail-open with logging
- All errors are logged with structured telemetry events
