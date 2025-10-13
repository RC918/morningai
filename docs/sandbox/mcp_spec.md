# MCP (Model Context Protocol) Tool Specification

## Overview
The MCP system provides controlled access to tools for AI agents running in sandboxes. All tool invocations go through permission checks and HITL approval gates for high-risk operations.

## API Endpoints

### GET /api/mcp/tools
List all available MCP tools with their permissions.

**Response:**
```json
{
  "tools": [
    {
      "name": "shell",
      "description": "Execute bash commands in sandbox",
      "permissions": ["execute_commands"],
      "approval_required_patterns": ["rm -rf", "dd if=", ...],
      "implementation": "path/to/shell_tool.py"
    },
    ...
  ],
  "total_count": 4
}
```

### GET /api/mcp/tools/{tool_name}
Get details for a specific tool.

**Response:** Tool configuration object

### POST /api/mcp/tools/{tool_name}/validate
Validate if a tool invocation requires HITL approval.

**Request:**
```json
{
  "command": "rm -rf /tmp/test"
}
```

**Response:**
```json
{
  "tool_name": "shell",
  "requires_approval": true,
  "matched_pattern": "rm -rf",
  "invocation": {...}
}
```

### GET /api/mcp/whitelist (Auth Required)
Get permission whitelist configuration.

**Authentication:** JWT token with analyst/admin role

**Response:**
```json
{
  "whitelisted_tools": ["shell", "browser", "render", "sentry"],
  "total_tools": 4,
  "permission_model": "explicit_whitelist",
  "approval_gate": "hitl_required_for_high_risk"
}
```

### POST /api/mcp/register (Admin Only)
Document tool registration endpoint. Currently returns existing tools; dynamic registration planned for future sprint.

**Authentication:** JWT token with admin role

## Available Tools

### 1. Shell Tool
**File:** `handoff/20250928/40_App/orchestrator/mcp/tools/shell_tool.py`

**Capabilities:**
- Execute bash commands in sandbox environment
- 30-second timeout per command
- Captures stdout, stderr, and return code

**High-Risk Patterns (require approval):**
- `rm -rf` - Recursive deletion
- `dd if=` - Disk imaging
- `mkfs` - Filesystem formatting
- `:(){:|:&};:` - Fork bomb
- `chmod 777` - Permission changes
- `chown root` - Ownership changes

**Example:**
```python
from mcp.client import MCPClient
client = MCPClient("http://mcp-server:8080", "ops-agent-001")
result = await client.execute_shell("ls -la /workspace")
```

### 2. Browser Tool
**File:** `handoff/20250928/40_App/orchestrator/mcp/tools/browser_tool.py`

**Capabilities:**
- Navigate to URLs
- Click elements
- Fill forms
- Take screenshots
- Powered by Playwright

**Permissions:** web_access, browser_automation

### 3. Render Tool
**File:** `handoff/20250928/40_App/orchestrator/mcp/tools/render_tool.py`

**Capabilities:**
- Query service status
- Trigger deployments (requires approval)
- Restart services (requires approval)
- Scale services (requires approval)

**Permissions:** api_access, deployment_control

### 4. Sentry Tool
**File:** `handoff/20250928/40_App/orchestrator/mcp/tools/sentry_tool.py`

**Capabilities:**
- Query error events
- Get error trends
- Retrieve stack traces

**Permissions:** api_access, error_monitoring

## Permission Model

### Whitelist-Based Access
- Only tools in `TOOL_REGISTRY` are accessible
- Each tool declares required permissions
- No tool execution outside the whitelist

### HITL Approval Gates
High-risk operations trigger HITL approval workflow:
1. Tool detects high-risk pattern in `requires_approval()`
2. Approval request created via `hitl_approval_system.py`
3. Admin receives notification (console + Telegram)
4. Tool execution paused until approval/rejection
5. If approved, operation proceeds; if rejected, operation cancelled

### Security Layers
1. **MCP Protocol** - JSON-RPC 2.0 with validation
2. **Permission Whitelist** - Explicit tool allowlist
3. **HITL Gates** - Human approval for dangerous operations
4. **Sandbox Isolation** - All tools run in isolated containers

## Testing

**Demo Script:**
```bash
# List tools
curl http://localhost:5000/api/mcp/tools

# Validate shell command
curl -X POST http://localhost:5000/api/mcp/tools/shell/validate \
  -H "Content-Type: application/json" \
  -d '{"command": "rm -rf /tmp/test"}'

# Get whitelist (requires auth)
curl http://localhost:5000/api/mcp/whitelist \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## References
- `handoff/20250928/40_App/orchestrator/mcp/server.py` - MCP Server Implementation
- `handoff/20250928/40_App/orchestrator/mcp/client.py` - MCP Client Implementation
- `docs/sandbox-security-hardening-runbook.md` - Security Hardening Guide
