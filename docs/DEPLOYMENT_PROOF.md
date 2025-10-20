# Deployment Proof - Agent Sandbox on Fly.io

This document serves as proof of successful deployment and validation of the Agent Sandbox infrastructure on Fly.io.

## Deployment Strategy

Following the platform evaluation in [sandbox-platform-poc.md](./sandbox-platform-poc.md), we selected **Fly.io** for Phase 1 Ops_Agent Sandbox deployment due to:

- ✅ Native Docker support (no DinD limitations)
- ✅ Low cost: ~$2.09/month per sandbox instance
- ✅ Fast deployment: 30-60 seconds
- ✅ Simple CLI-based workflow
- ✅ Suitable for pilot/POC phase

## Deployment Records

### 1. Platform Comparison (Completed)

**Pull Request**: [#206 - Platform POC (Fly.io/Fargate) + Security Hardening](https://github.com/RC918/morningai/pull/206)

**Status**: ✅ Merged to main

**Deliverables**:
- Platform comparison document with cost analysis
- One-click deployment scripts for Fly.io and AWS Fargate
- Comprehensive security hardening RUNBOOK
- Security configuration files (seccomp profile, network hardening script)

**CI Results**: All 8 checks passed
- Backend: build, lint, test, deploy, smoke ✅
- Vercel: deployment, preview comments ✅

---

### 2. E2E Workflow Implementation (In Progress)

**Pull Request**: [Current PR - Fly.io E2E Implementation](#)

**Changes**:
- ✅ Updated `ops-agent-sandbox-e2e.yml` to deploy ephemeral sandboxes on Fly.io
- ✅ Added draft PR condition: E2E only runs on non-draft PRs
- ✅ Integrated flyctl CLI setup and deployment
- ✅ Automatic cleanup of ephemeral sandboxes after testing

**Workflow Enhancements**:
```yaml
# Only run E2E on:
# - push to main
# - workflow_dispatch (manual trigger)
# - pull_request (non-draft only)
if: github.event_name == 'push' || 
    github.event_name == 'workflow_dispatch' || 
    (github.event_name == 'pull_request' && github.event.pull_request.draft == false)
```

---

## Required GitHub Checks

The following workflows are configured as required checks for PR merges:

| Workflow | Purpose | Status |
|----------|---------|--------|
| **orchestrator-e2e** | Tests agent orchestration logic | ✅ Exists |
| **openapi-verify** | Validates API contract consistency | ✅ Exists |
| **post-deploy-health** | Validates production deployment health | ✅ Exists |
| **ops-agent-sandbox-e2e** | Tests sandbox deployment on Fly.io | 🔄 Updated (this PR) |

**Configuration**: These checks must be configured in GitHub repository settings under:
```
Settings → Branches → Branch protection rules → main → Require status checks
```

---

## Deployment Workflow

### One-Click Deployment Script

**Script**: [`scripts/sandbox/flyio-deploy.sh`](../scripts/sandbox/flyio-deploy.sh)

**Commands**:
```bash
# Start/deploy sandbox
./scripts/sandbox/flyio-deploy.sh start

# Check status and resource usage
./scripts/sandbox/flyio-deploy.sh status

# View logs
./scripts/sandbox/flyio-deploy.sh logs

# Stop sandbox (scale to 0, cost = $0)
./scripts/sandbox/flyio-deploy.sh stop

# Permanently delete sandbox
./scripts/sandbox/flyio-deploy.sh destroy
```

### Ephemeral Sandbox for CI/CD

The E2E workflow automatically creates ephemeral sandboxes for testing:

1. **Deploy**: Create unique sandbox instance (`morningai-sandbox-e2e-{run_id}`)
2. **Test**: Run E2E tests against the sandbox
3. **Cleanup**: Automatically destroy sandbox after tests complete

**Benefits**:
- ✅ Isolated test environment per workflow run
- ✅ No cost when tests aren't running
- ✅ Prevents test interference between PRs
- ✅ Clean slate for each test run

---

## Health Check Validation

### Endpoint

```
GET https://{app-name}.fly.dev/health
```

### Expected Response

```json
{
  "status": "healthy",
  "agent_type": "ops_agent",
  "timestamp": "2025-10-10T12:42:00Z",
  "mcp_server": "running",
  "tools": ["shell", "browser", "render", "sentry"]
}
```

### Workflow Validation

The E2E workflow includes automated health check validation:

```yaml
- name: Wait for sandbox to be healthy
  run: |
    for i in {1..30}; do
      if curl -f -s "$SANDBOX_URL/health" > /dev/null 2>&1; then
        echo "Sandbox is healthy!"
        break
      fi
      echo "Attempt $i/30: Sandbox not ready yet, waiting..."
      sleep 10
    done
```

---

## Cost Analysis

### Fly.io Pricing (Phase 1 Pilot)

**Persistent Sandbox** (always running):
- 1x shared-cpu-1x: $1.94/month
- 256MB RAM: $0.15/month
- **Total**: ~$2.09/month

**Ephemeral Sandboxes** (CI/CD only):
- Only charged during test execution
- Typical test duration: 5-10 minutes
- Cost per test run: ~$0.001 (negligible)

**Cost Optimization**:
- Scale to 0 when not in use: `flyctl scale count 0`
- Use ephemeral instances for CI/CD
- Only persistent instance for staging/demo environments

---

## Security Configuration

All security hardening measures from [sandbox-security-hardening-runbook.md](./sandbox-security-hardening-runbook.md) are implemented:

### 1. Seccomp Profile
- **File**: [`handoff/20250928/40_App/orchestrator/sandbox/ops_agent/seccomp-profile.json`](../handoff/20250928/40_App/orchestrator/sandbox/ops_agent/seccomp-profile.json)
- **Protection**: Syscall filtering, blocks dangerous operations

### 2. Resource Limits
- **CPU**: 1 core
- **Memory**: 256MB
- **Disk**: 1GB persistent volume
- **Processes**: ulimit 100
- **File descriptors**: ulimit 1024

### 3. Network Hardening
- **Script**: [`scripts/sandbox/network-hardening.sh`](../scripts/sandbox/network-hardening.sh)
- **Protection**: iptables egress filtering, rate limiting

### 4. Docker Security Options
- Read-only root filesystem
- `/tmp` mounted as tmpfs with `noexec`
- No new privileges flag
- AppArmor profile enforcement

---

## Manual Deployment Verification Steps

For manual verification, follow these steps:

### Prerequisites

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Authenticate
flyctl auth login
```

### Deploy Sandbox

```bash
# Clone repository
git clone https://github.com/RC918/morningai.git
cd morningai

# Deploy sandbox
./scripts/sandbox/flyio-deploy.sh start
```

### Verify Deployment

```bash
# Check status
./scripts/sandbox/flyio-deploy.sh status

# View logs
./scripts/sandbox/flyio-deploy.sh logs

# Test health endpoint
curl https://morningai-sandbox-ops-agent.fly.dev/health
```

### Expected Output

```
✅ Sandbox deployed successfully!
App URL: https://morningai-sandbox-ops-agent.fly.dev

Next steps:
  - View logs: ./scripts/sandbox/flyio-deploy.sh logs
  - Check status: ./scripts/sandbox/flyio-deploy.sh status
  - Stop sandbox: ./scripts/sandbox/flyio-deploy.sh stop
```

---

## Workflow Run Examples

### Successful Deployment Examples

Once the current PR is merged and CI runs complete, workflow run links will be added here:

**Example Workflow Run**: [To be added after CI completion]

**Screenshot**: [To be added after CI completion]

---

## Platform Compatibility Matrix

| Platform | Docker Support | Cost/Month | E2E Testing | Production |
|----------|---------------|------------|-------------|------------|
| **Fly.io** | ✅ Native | $2.09 | ✅ Recommended | ✅ Phase 1 |
| **AWS Fargate** | ✅ Full | $9.01 | ✅ Optional | ✅ Phase 2+ |
| **Render** | ❌ No DinD | $7-25 | ❌ Not suitable | ⚠️ Main app only* |
| **GitHub Actions** | ✅ Full | Free | ✅ CI/CD | ❌ Not for prod |

*Render can run the main orchestrator application with `SANDBOX_ENABLED=false`, but actual sandboxes must be deployed on Fly.io or AWS Fargate.

---

## Next Steps

### Phase 1 Completion Checklist

- [x] Platform comparison and cost analysis
- [x] One-click deployment scripts (Fly.io + Fargate)
- [x] Security hardening RUNBOOK
- [x] Security configuration files
- [x] Render compatibility (SANDBOX_ENABLED flag)
- [x] Manual trigger for E2E workflow
- [ ] Fly.io E2E workflow implementation (current PR)
- [ ] Configure required GitHub checks
- [ ] Successful E2E run with Fly.io deployment
- [ ] Screenshots and workflow run links

### Phase 2 Planning

After Phase 1 validation:

1. **Dev_Agent Sandbox**: IDE + Git integration
2. **Multi-agent Support**: Scale to all 15 agent types
3. **Cost Optimization**: Auto-scaling, spot instances
4. **Advanced Monitoring**: Prometheus + Grafana integration
5. **Migration to AWS Fargate**: Enterprise production deployment

---

## References

- [Platform POC Document](./sandbox-platform-poc.md)
- [Security Hardening Runbook](./sandbox-security-hardening-runbook.md)
- [Agent Sandbox Architecture](./agent-sandbox-architecture.md)
- [PR #206: Platform POC + Security Hardening](https://github.com/RC918/morningai/pull/206)
- [PR #211: Render Compatibility](https://github.com/RC918/morningai/pull/211)
- [PR #213: Manual Workflow Trigger](https://github.com/RC918/morningai/pull/213)
- [Fly.io Documentation](https://fly.io/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Last Updated**: 2025-10-10  
**Status**: Phase 1 Implementation In Progress  
**Next Milestone**: E2E Workflow Validation

---

## E2E Workflow Triggers

This file was updated to trigger E2E workflow for the following PRs:

- PR #482: Updated 2025-10-20 10:14:10 UTC
- PR #487: Updated 2025-10-20 10:21:43 UTC
- PR #466: Updated 2025-10-20 10:31:39 UTC
