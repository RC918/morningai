# Terminal Access Capability Authorization Flow

This document describes the authorization flow for terminal access in the VS Code IDE integration service.

## Overview

Terminal access is a privileged capability that allows execution of arbitrary shell commands in task VMs. Due to the security implications, this capability is disabled by default and must be explicitly granted by trusted services or administrators.

## Capability Constant

The capability is defined as a module-level constant in `meta_agent/vscode_ide.py`:

```python
TERMINAL_ACCESS_CAPABILITY = "terminal_access_enabled"
```

This constant should be used consistently across all code that checks or sets the terminal access capability.

## Authorization Flow

### 1. Session Creation (Default: Disabled)

When an IDE session is created via `VSCodeIDEService.create_session()`, the session's metadata dictionary is initialized empty. Terminal access is disabled by default:

```python
session = IDESession(
    session_id=session_id,
    vm_id=vm_id,
    task_id=task_id,
    status=IDESessionStatus.INITIALIZING,
    created_at=datetime.now(),
    metadata={},  # Empty - terminal access disabled
)
```

### 2. Capability Grant (Trusted Services Only)

Terminal access must be explicitly granted by setting the capability in the session metadata. This should only be done by trusted, authenticated services:

```python
from meta_agent.vscode_ide import TERMINAL_ACCESS_CAPABILITY

# Grant terminal access (trusted service only)
session.metadata[TERMINAL_ACCESS_CAPABILITY] = True
```

### 3. Capability Check (Before Command Execution)

Before executing any terminal command, the `execute_terminal_command()` method checks for the capability:

```python
def _has_terminal_capability(self, session: IDESession) -> bool:
    return bool(session.metadata.get(TERMINAL_ACCESS_CAPABILITY, False))
```

If the capability is not granted, the command is denied with a warning log and error response.

### 4. Command Execution (If Authorized)

Only if the capability check passes, the command is forwarded to the VM's shell via MCP:

```
User/Service → execute_terminal_command() → _has_terminal_capability() → _execute_shell_command() → MCP → VM Shell
```

## Environment Settings Guide

The following table provides recommended settings for terminal access capability across different deployment environments:

| Environment | Recommended Setting | Description |
|-------------|---------------------|-------------|
| Development | Can be enabled | For local development and testing. Developers can freely enable terminal access for debugging. |
| Staging | Restricted | Requires review before enabling. Use for integration testing with limited scope. |
| Production | Strictly controlled | Only enable for specific, audited use cases. Requires explicit authorization and logging. |

### Environment-Specific Configuration

**Development:**
- Terminal access can be enabled by default for developer convenience
- No additional authorization checks required
- Useful for debugging and rapid iteration

**Staging:**
- Terminal access should be disabled by default
- Enable only for specific test scenarios
- Log all terminal access grants for review

**Production:**
- Terminal access must be disabled by default
- Require explicit user authorization before granting
- Implement audit logging for all terminal commands
- Consider time-limited access grants

## Security Considerations

### Who Can Grant Terminal Access

Terminal access should only be granted by:

1. Trusted, authenticated users via the IDE UI
2. Highly privileged internal components (e.g., orchestrator services)
3. Administrative tools with proper authorization checks

### Who Must NOT Grant Terminal Access

Terminal access must NOT be:

1. Wired directly to untrusted HTTP request parameters
2. Granted based on user-supplied input without proper authorization
3. Enabled by default for any session

### Logging and Auditing

All terminal access denials are logged at WARNING level:

```
[VSCodeIDEService] Denied terminal command for task {task_id}: terminal_access_enabled capability not granted
```

This enables security auditing and detection of unauthorized access attempts.

## Usage Examples

### Granting Access in Orchestrator

```python
from meta_agent.vscode_ide import (
    VSCodeIDEService,
    TERMINAL_ACCESS_CAPABILITY,
)

async def setup_privileged_session(vm_id: str, task_id: str, mcp_endpoint: str):
    service = VSCodeIDEService()
    session = await service.create_session(vm_id, task_id, mcp_endpoint)
    
    # Only grant if user is authorized (implement your auth check)
    if user_has_terminal_permission(task_id):
        session.metadata[TERMINAL_ACCESS_CAPABILITY] = True
    
    return session
```

### Executing Commands (With Capability)

```python
# Session with terminal access enabled
result = await service.execute_terminal_command(session, "npm install")
# result["success"] == True

# Session without terminal access
result = await service.execute_terminal_command(unprivileged_session, "npm install")
# result["success"] == False
# result["error"] contains capability denial message
```

## Related Issues

- Issue #2023: Capability gate for terminal access
- Issue #2044: Document terminal capability authorization flow and environment settings
- Issue #1822: VS Code IDE integration

## Related Files

- `meta_agent/vscode_ide.py`: VSCodeIDEService implementation
- `meta_agent/tests/test_vscode_ide.py`: Unit tests including capability tests
