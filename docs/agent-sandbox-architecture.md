# Agent Sandbox Architecture

## Overview

The Agent Sandbox provides isolated execution environments for AI agents to safely run code, access tools, and interact with external services through the Model Context Protocol (MCP).

## Architecture

```
Meta-Agent OODA Loop
    ↓
Agent Sandbox Manager
    ↓
┌─────────────────────────────────────┐
│ Docker Container (when enabled)     │
│  ├─ Resource Limits (CPU/Memory)    │
│  ├─ Security (seccomp/AppArmor)     │
│  ├─ Read-only Filesystem            │
│  └─ MCP Client ─→ MCP Server        │
│       ├─ Shell Tool                 │
│       ├─ Browser Tool (Playwright)  │
│       ├─ Render API Tool            │
│       └─ Sentry API Tool            │
└─────────────────────────────────────┘
```

## Platform Compatibility

### Render Platform Limitations

**Important**: Render's standard deployment platform does **not support Docker-in-Docker (DinD)**. This means:

- ❌ Cannot run Docker containers within the Render deployment
- ❌ Cannot use Docker Compose
- ❌ Cannot build Docker images at runtime

### SANDBOX_ENABLED Flag

To handle platform differences, we use the `SANDBOX_ENABLED` environment variable:

```bash
# On platforms that support Docker (GitHub Runners, local dev)
export SANDBOX_ENABLED=true

# On Render or platforms without Docker support
export SANDBOX_ENABLED=false  # (default)
```

**Behavior**:
- **When `SANDBOX_ENABLED=true`**: Full Docker-based sandbox isolation is used
- **When `SANDBOX_ENABLED=false`**: Sandbox operations are simulated without Docker

### Deployment Strategy by Platform

| Platform | SANDBOX_ENABLED | Notes |
|----------|----------------|-------|
| **Render** | `false` (default) | No DinD support - sandbox simulated |
| **GitHub Actions** | `true` | Full Docker support for E2E tests |
| **Fly.io** | `true` | Native Docker support, recommended for Phase 1 pilot |
| **AWS Fargate** | `true` | Full container support, recommended for Phase 2+ |
| **Local Development** | `true` | Full Docker support |

## Components

### 1. Agent Sandbox Manager (`sandbox/manager.py`)

Manages the lifecycle of agent sandboxes:
- Creates sandboxes with specified resource limits
- Tracks sandbox status (CREATING, READY, RUNNING, STOPPED, ERROR)
- Handles cleanup of idle/expired sandboxes
- Respects `SANDBOX_ENABLED` flag for platform compatibility

### 2. Docker Sandbox (`sandbox/docker_sandbox.py`)

Docker-based isolation implementation (when `SANDBOX_ENABLED=true`):
- Creates Docker containers with security constraints
- Enforces resource limits (CPU, memory, disk, processes)
- Configures read-only filesystem with writable `/tmp` and `/workspace`
- Sets up network isolation
- Applies security profiles (seccomp, AppArmor)

### 3. MCP Server (`mcp/server.py`)

JSON-RPC 2.0 server that provides tools to agents:
- **ShellTool**: Execute bash commands in sandbox
- **BrowserTool**: Automated browser interactions via Playwright
- **RenderTool**: Interact with Render deployment API
- **SentryTool**: Query and manage Sentry error tracking

### 4. MCP Client (`mcp/client.py`)

Client library for agents to communicate with MCP server:
- Sends tool invocation requests
- Handles responses and errors
- Maintains connection to MCP server

## Security Model

### Multi-Layer Isolation

1. **Resource Limits**
   - CPU: 1 core (configurable)
   - Memory: 2GB (configurable)
   - Disk: 10GB (configurable)
   - Max processes: 100

2. **Filesystem Security**
   - Root filesystem: read-only
   - `/tmp`: 1GB tmpfs with `noexec`
   - `/workspace`: writable volume for agent work

3. **Network Isolation**
   - Configurable network access
   - Can be fully disabled (`network_mode=none`)

4. **Security Profiles**
   - Seccomp: Syscall filtering
   - AppArmor: Mandatory Access Control
   - Capabilities: Drop ALL, add only NET_BIND_SERVICE

5. **Process Isolation**
   - `no-new-privileges` flag
   - PID limits to prevent fork bombs

## Testing

### E2E Tests (`tests/test_ops_agent_sandbox.py`)

Tests the full sandbox lifecycle:
1. Create sandbox via Manager
2. Verify sandbox is READY
3. Test MCP tool invocations
4. Cleanup sandbox

### Running Tests

```bash
# With Docker (local development or GitHub Actions)
export SANDBOX_ENABLED=true
cd handoff/20250928/40_App/orchestrator
python -m pytest tests/test_ops_agent_sandbox.py -v

# Without Docker (Render compatibility mode)
export SANDBOX_ENABLED=false
cd handoff/20250928/40_App/orchestrator
python -m pytest tests/test_ops_agent_sandbox.py -v
```

### CI/CD Workflow

The `ops-agent-sandbox-e2e.yml` workflow:
- Runs on GitHub Actions runners (Docker support available)
- Sets `SANDBOX_ENABLED=false` to test Render compatibility mode
- Installs Playwright browsers with system dependencies
- Uploads test logs as artifacts for debugging
- Extends timeout to 30 minutes for comprehensive testing

## Future Enhancements

### Phase 1 (Current) ✅ **已完成基礎部署**
- ✅ Dev_Agent sandbox deployed to Fly.io (https://morningai-sandbox-dev-agent.fly.dev/)
  - VSCode Server (code-server) integrated
  - LSP Servers (Python, TypeScript, YAML, Dockerfile)
  - Git, IDE, FileSystem tools implemented
  - Port 8080 (MCP server), Port 8443 (VSCode Server)
- ✅ Ops_Agent sandbox deployed to Fly.io (https://morningai-sandbox-ops-agent.fly.dev/)
  - Shell, Browser, Render, Sentry tools
  - Performance monitoring (CPU, memory, disk)
  - Port 8000 (MCP server)
- ✅ Docker-based isolation with security profiles
- ✅ MCP protocol implementation
- ✅ Auto-scaling to 0 machines when idle ($0 cost)
- 🔄 **Pending**: Session State management (Redis + PostgreSQL)
- 🔄 **Pending**: OODA Loop integration with Meta-Agent

### Phase 2 (Planned) 📋 **下一階段**
- 📋 Ops_Agent enhancement: LogAnalysis, Incident, Prometheus tools
- 📋 Root cause analysis algorithm
- 📋 Predictive auto-scaling
- 📋 Anomaly detection (ML-based)
- 📋 Cost optimization engine

### Phase 3 (Partially Complete) ⚡ **安全與文檔**
- ✅ Fly.io deployment (COMPLETED - both agents live)
- 📋 OWASP security audit
- 📋 Secrets management (Vault integration)
- 📋 Disaster recovery runbook
- 📋 Technical documentation
- 📋 Team training materials

## Deployment Recommendations

For production deployment of Agent Sandbox:

1. **Phase 1 Pilot (Ops_Agent)**
   - **Recommended**: Fly.io
   - **Reason**: Native Docker support, low cost ($2/month), fast deployment
   - **Alternative**: AWS Fargate (higher cost but enterprise features)

2. **Phase 2+ Production**
   - **Recommended**: AWS Fargate
   - **Reason**: Enterprise security, mature monitoring, scalability
   - **Cost**: ~$9/month per sandbox instance

3. **Render Deployment**
   - Use `SANDBOX_ENABLED=false` for main application
   - Deploy actual sandboxes on Fly.io or AWS Fargate
   - Keep main orchestrator logic on Render

## Troubleshooting

### Common Issues

**Issue**: `docker.errors.DockerException: Error while fetching server API version`
- **Cause**: Docker daemon not running or `SANDBOX_ENABLED=true` on unsupported platform
- **Solution**: Set `SANDBOX_ENABLED=false` or ensure Docker is available

**Issue**: Playwright browser not found
- **Cause**: Playwright browsers not installed with system dependencies
- **Solution**: Run `npx playwright install --with-deps chromium`

**Issue**: Test timeout in CI
- **Cause**: Default timeout too short for cold starts
- **Solution**: Extend `timeout-minutes` in workflow (current: 30 minutes)

## References

- [Platform POC Comparison](./sandbox-platform-poc.md)
- [Security Hardening Runbook](./sandbox-security-hardening-runbook.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## Deployment Summary

### Current Production Status (2025-10-16)

**Dev_Agent Sandbox**:
- **URL**: https://morningai-sandbox-dev-agent.fly.dev/
- **Region**: Singapore (sin)
- **Cost**: ~$2/month (shared-cpu-1x, 1GB RAM), $0 when idle
- **Features**: Full IDE, LSP, Git, Browser, Shell
- **Status**: ✅ Production, all CI checks passing

**Ops_Agent Sandbox**:
- **URL**: https://morningai-sandbox-ops-agent.fly.dev/
- **Region**: Singapore (sin)
- **Cost**: ~$2/month (shared-cpu-1x, 1GB RAM), $0 when idle
- **Features**: Performance monitoring, capacity analysis, system operations
- **Status**: ✅ Production, all CI checks passing

**Total Infrastructure Cost**: ~$4/month (auto-scales to $0 when idle)
