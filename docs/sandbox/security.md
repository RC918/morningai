# Agent Sandbox Security Summary

## Overview
Multi-layer security architecture for isolating AI agent execution environments.

## Security Layers

### Layer 1: Container Runtime
**File:** <ref_file file="/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator/sandbox/docker_sandbox.py" />

- **Non-root user:** All processes run as `sandbox` user (UID 1000)
- **Capabilities:** Drop ALL, add only NET_BIND_SERVICE
- **No-new-privileges:** Prevents privilege escalation
- **Resource limits:** 
  - CPU: 1 core (configurable)
  - Memory: 2GB (configurable)
  - Disk: 10GB (configurable)
  - Max processes: 100 (ulimit + pids_limit)

### Layer 2: Security Profiles

#### Seccomp Profile
**File:** <ref_file file="/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator/sandbox/ops_agent/seccomp-profile.json" />

Syscall whitelist approach:
- Default action: SCMP_ACT_ERRNO (block)
- Allowed syscalls: ~80 essential syscalls for Python/Node.js
- Blocked: kernel module loading, mount, chroot, reboot

#### AppArmor Profile  
**File:** <ref_file file="/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator/sandbox/ops_agent/apparmor-profile" />

Mandatory Access Control:
- Read-only: system files, binaries
- Read-write: /workspace, /tmp only
- Denied: /etc/shadow, /root, /home, kernel modules

### Layer 3: Filesystem Isolation

**Configuration:** <ref_file file="/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator/sandbox/docker_sandbox.py" />

```python
container_config = {
    'read_only': True,  # Root filesystem read-only
    'tmpfs': {
        '/tmp': 'size=1G,mode=1777,noexec'  # 1GB tmpfs, no execution
    },
    'volumes': {
        f'sandbox-{agent_id}-workspace': {
            'bind': '/workspace',
            'mode': 'rw'  # Only /workspace is writable
        }
    }
}
```

### Layer 4: Network Isolation
- Configurable network access (enabled/disabled)
- Can be fully isolated with `network_mode=none`
- Egress filtering via iptables (see runbook)

### Layer 5: Application-Level Security

#### MCP Access Control
**File:** <ref_file file="/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator/mcp/server.py" />

- Whitelist-based tool access
- Permission checks per tool
- HITL approval gates for high-risk operations

#### HITL Approval System
**File:** <ref_file file="/home/ubuntu/repos/morningai/hitl_approval_system.py" />

- High-risk operations require human approval
- Dual-channel notifications (console + Telegram)
- Priority-based timeout (Critical: 2h, High: 8h, Medium: 24h, Low: 72h)
- Audit trail for all approvals/rejections

## Threat Mitigation

| Threat | Mitigation | Implementation |
|--------|-----------|----------------|
| **Container Escape** | seccomp + AppArmor + read-only FS | Layers 2-3 |
| **Resource Exhaustion** | cgroups + ulimit + pids_limit | Layer 1 |
| **Network Attacks** | iptables + network policy | Layer 4 |
| **Malicious Code** | Sandbox isolation + HITL gates | Layers 1-5 |
| **Credential Leakage** | Secrets manager + env isolation | Layer 5 |

## Deployment Checklist

- [ ] **Dockerfile** uses non-root user
- [ ] **Seccomp profile** applied via `security_opt`
- [ ] **AppArmor profile** loaded and applied
- [ ] **Read-only FS** enabled with tmpfs for /tmp
- [ ] **Resource limits** configured (CPU/memory/disk/processes)
- [ ] **Network isolation** configured as needed
- [ ] **MCP whitelist** reviewed and approved
- [ ] **HITL gates** configured for high-risk operations
- [ ] **Sentry integration** enabled for security events
- [ ] **Audit logging** enabled with trace_id

## Verification Commands

```bash
# Check non-root user
docker exec sandbox-ops-agent whoami  # Should output: agentuser

# Check read-only filesystem
docker exec sandbox-ops-agent touch /test.txt  # Should fail
docker exec sandbox-ops-agent touch /tmp/test.txt  # Should succeed
docker exec sandbox-ops-agent touch /workspace/test.txt  # Should succeed

# Check seccomp
docker inspect sandbox-ops-agent | jq '.[0].HostConfig.SecurityOpt'

# Check resource limits
docker stats sandbox-ops-agent --no-stream

# Check process limits
docker exec sandbox-ops-agent sh -c "ulimit -a"
```

## Monitoring & Alerts

**Sentry Integration:** <ref_file file="/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator/mcp/server.py" />

Security events logged:
- High-risk operations (approved/rejected)
- Sandbox creation/destruction
- MCP tool invocations
- Resource limit violations
- Security profile violations (seccomp/AppArmor blocks)

**Alert Rules:**
- CPU > 80% for 5 minutes
- Memory growth > 15 minutes  
- Seccomp blocks > 10/min
- High-risk operations rejected > 3/hour

## References

- **Comprehensive Guide:** <ref_file file="/home/ubuntu/repos/morningai/docs/sandbox-security-hardening-runbook.md" />
- **Architecture:** <ref_file file="/home/ubuntu/repos/morningai/docs/agent-sandbox-architecture.md" />
- **Platform POC:** <ref_file file="/home/ubuntu/repos/morningai/docs/sandbox-platform-poc.md" />

## Compliance

- **OWASP Top 10:** Container security best practices
- **CIS Docker Benchmark:** 4.1-4.6 (seccomp, AppArmor, read-only FS)
- **NIST 800-190:** Container security recommendations
