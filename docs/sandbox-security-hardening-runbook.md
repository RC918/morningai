# Agent Sandbox 安全強化 RUNBOOK

## 目錄
1. [安全概覽](#1-安全概覽)
2. [多層安全模型](#2-多層安全模型)
3. [Seccomp 配置](#3-seccomp-配置)
4. [AppArmor 配置](#4-apparmor-配置)
5. [Read-only Filesystem](#5-read-only-filesystem)
6. [Resource Limits (ulimit)](#6-resource-limits-ulimit)
7. [Network 隔離](#7-network-隔離)
8. [監控與告警](#8-監控與告警)
9. [事件響應](#9-事件響應)
10. [定期審計](#10-定期審計)

---

## 1. 安全概覽

### 1.1 安全目標
- 🛡️ **隔離性**：防止 Agent 存取 host 系統或其他容器
- 🔒 **最小權限**：僅授予完成任務所需的最小權限
- 🚨 **可觀測性**：所有安全事件可追蹤、可告警
- ⚡ **快速響應**：自動阻擋異常行為，HITL 審批高風險操作

### 1.2 威脅模型

| 威脅 | 風險等級 | 緩解措施 |
|------|---------|---------|
| **容器逃逸** | 🔴 High | seccomp + AppArmor + read-only FS |
| **資源耗盡** | 🟡 Medium | cgroups limits + ulimit |
| **網路攻擊** | 🟡 Medium | iptables + network policy |
| **惡意程式碼** | 🟡 Medium | 靜態掃描 + runtime monitoring |
| **憑證洩漏** | 🔴 High | Secrets manager + 環境變數隔離 |

---

## 2. 多層安全模型

```
Layer 1: Container Runtime (Docker)
  ├─ cgroups (CPU/Memory/Disk limits)
  ├─ namespaces (PID/Network/IPC/Mount isolation)
  └─ capabilities (drop ALL, add minimal)

Layer 2: Security Profiles
  ├─ Seccomp (系統調用過濾)
  └─ AppArmor (強制訪問控制)

Layer 3: Filesystem
  ├─ Read-only root filesystem
  ├─ Tmpfs for /tmp (1GB, noexec)
  └─ Named volume for /workspace (size-limited)

Layer 4: Network
  ├─ iptables egress filtering
  ├─ DNS whitelist (important-comment)
  └─ Rate limiting (important-comment)

Layer 5: Application
  ├─ MCP access control (important-comment)
  ├─ HITL approval gates (important-comment)
  └─ Audit logging (important-comment)
```

---

## 3. Seccomp 配置

### 3.1 什麼是 Seccomp？
Seccomp (Secure Computing Mode) 限制容器可呼叫的 Linux 系統調用，防止容器逃逸。

### 3.2 自定義 Seccomp Profile

建立 `handoff/20250928/40_App/orchestrator/sandbox/ops_agent/seccomp-profile.json`:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_X32"
  ],
  "syscalls": [
    {
      "names": [
        "accept",
        "accept4",
        "access",
        "arch_prctl",
        "bind",
        "brk",
        "capget",
        "capset",
        "chdir",
        "chmod",
        "chown",
        "clock_getres",
        "clock_gettime",
        "clock_nanosleep",
        "close",
        "connect",
        "dup",
        "dup2",
        "dup3",
        "epoll_create",
        "epoll_create1",
        "epoll_ctl",
        "epoll_wait",
        "execve",
        "exit",
        "exit_group",
        "fcntl",
        "fstat",
        "futex",
        "getcwd",
        "getdents",
        "getdents64",
        "getegid",
        "geteuid",
        "getgid",
        "getpid",
        "getppid",
        "getuid",
        "ioctl",
        "kill",
        "listen",
        "lseek",
        "madvise",
        "mkdir",
        "mmap",
        "mprotect",
        "munmap",
        "nanosleep",
        "open",
        "openat",
        "pipe",
        "pipe2",
        "poll",
        "pread64",
        "pwrite64",
        "read",
        "readlink",
        "recvfrom",
        "recvmsg",
        "rt_sigaction",
        "rt_sigprocmask",
        "rt_sigreturn",
        "sched_getaffinity",
        "sched_yield",
        "sendto",
        "sendmsg",
        "set_robust_list",
        "set_tid_address",
        "setgid",
        "setuid",
        "shutdown",
        "sigaltstack",
        "socket",
        "socketpair",
        "stat",
        "tgkill",
        "uname",
        "wait4",
        "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### 3.3 應用 Seccomp Profile

更新 `docker_sandbox.py`:

```python
container_config = {
    # ... 其他配置
    'security_opt': [
        'no-new-privileges:true',
        'seccomp=/path/to/seccomp-profile.json'  # 使用自定義 profile (important-comment)
    ],
}
```

### 3.4 驗證 Seccomp

```bash
# 檢查容器是否使用 seccomp (important-comment)
docker inspect sandbox-ops-agent | jq '.[0].HostConfig.SecurityOpt'

# 應看到: ["no-new-privileges:true", "seccomp=..."]
```

---

## 4. AppArmor 配置

### 4.1 什麼是 AppArmor？
AppArmor 提供強制訪問控制 (MAC)，限制程式可存取的檔案、網路等資源。

### 4.2 自定義 AppArmor Profile

建立 `/etc/apparmor.d/docker-ops-agent-sandbox`:

```apparmor
#include <tunables/global>

profile docker-ops-agent-sandbox flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # 允許網路存取 (important-comment)
  network inet stream,
  network inet6 stream,

  # 允許讀取系統資訊 (important-comment)
  /proc/cpuinfo r,
  /proc/meminfo r,
  /proc/stat r,
  /sys/fs/cgroup/** r,

  # 允許讀寫工作目錄 (important-comment)
  /workspace/** rw,
  /tmp/** rw,

  # 禁止存取 host 檔案系統 (important-comment)
  deny /etc/shadow r,
  deny /etc/passwd w,
  deny /root/** rw,
  deny /home/** rw,

  # 允許執行常用命令 (important-comment)
  /bin/** ix,
  /usr/bin/** ix,
  /usr/local/bin/** ix,

  # Python 相關 (important-comment)
  /usr/lib/python3.*/** r,
  /usr/local/lib/python3.*/** r,

  # 禁止載入核心模組 (important-comment)
  deny /sys/module/** w,
  deny /proc/sys/kernel/** w,
}
```

### 4.3 載入 AppArmor Profile

```bash
# 安裝 apparmor-utils (important-comment)
sudo apt-get install apparmor-utils

# 載入 profile (important-comment)
sudo apparmor_parser -r /etc/apparmor.d/docker-ops-agent-sandbox

# 驗證載入 (important-comment)
sudo aa-status | grep docker-ops-agent-sandbox
```

### 4.4 應用到 Docker 容器

更新 `docker_sandbox.py`:

```python
container_config = {
    # ... 其他配置
    'security_opt': [
        'no-new-privileges:true',
        'seccomp=/path/to/seccomp-profile.json',
        'apparmor=docker-ops-agent-sandbox'  # 使用自定義 AppArmor profile (important-comment)
    ],
}
```

---

## 5. Read-only Filesystem

### 5.1 為何使用 Read-only FS？
- 防止 Agent 修改系統檔案
- 防止惡意程式碼持久化
- 簡化審計（所有變更在 tmpfs/volume）

### 5.2 配置 Read-only FS

已在 `docker_sandbox.py` 實作:

```python
container_config = {
    'read_only': True,  # Root filesystem 唯讀 (important-comment)
    
    'tmpfs': {
        '/tmp': 'size=1G,mode=1777,noexec'  # 1GB tmpfs，禁止執行 (important-comment)
    },
    
    'volumes': {
        f'sandbox-{agent_id}-workspace': {
            'bind': '/workspace',
            'mode': 'rw'  # 僅 /workspace 可寫 (important-comment)
        }
    }
}
```

### 5.3 驗證 Read-only FS

```bash
# 進入容器測試 (important-comment)
docker exec -it sandbox-ops-agent sh

# 嘗試寫入根目錄（應失敗） (important-comment)
touch /test.txt
# 錯誤: touch: /test.txt: Read-only file system

# 嘗試寫入 /tmp（應成功） (important-comment)
touch /tmp/test.txt && echo "SUCCESS"

# 嘗試寫入 /workspace（應成功） (important-comment)
touch /workspace/test.txt && echo "SUCCESS"
```

---

## 6. Resource Limits (ulimit)

### 6.1 為何需要 ulimit？
- 防止單一 Agent 耗盡系統資源
- 防止 fork bomb 攻擊
- 限制檔案描述符數量

### 6.2 設定 ulimit

更新 `docker_sandbox.py`:

```python
container_config = {
    # ... 其他配置
    
    'ulimits': [
        # 最大進程數（防 fork bomb） (important-comment)
        docker.types.Ulimit(name='nproc', soft=100, hard=100),
        
        # 檔案描述符數量 (important-comment)
        docker.types.Ulimit(name='nofile', soft=1024, hard=2048),
        
        # 最大檔案大小 (10GB) (important-comment)
        docker.types.Ulimit(name='fsize', soft=10737418240, hard=10737418240),
        
        # CPU 時間（秒） (important-comment)
        docker.types.Ulimit(name='cpu', soft=3600, hard=3600),
    ],
    
    'pids_limit': 100,  # Docker 原生 PID limit (important-comment)
}
```

### 6.3 驗證 ulimit

```bash
# 進入容器檢查限制 (important-comment)
docker exec -it sandbox-ops-agent sh -c "ulimit -a"

# 應看到:
# -u: processes          100
# -n: file descriptors   1024
# -f: file size          10485760 blocks
# -t: cpu time           3600 seconds
```

---

## 7. Network 隔離

### 7.1 出站流量控制

建立 iptables 規則限制容器出站流量:

```bash
#!/bin/bash
# network-hardening.sh

# 建立自定義鏈 (important-comment)
sudo iptables -N SANDBOX_EGRESS

# 允許 DNS (important-comment)
sudo iptables -A SANDBOX_EGRESS -p udp --dport 53 -j ACCEPT

# 允許 HTTP/HTTPS (important-comment)
sudo iptables -A SANDBOX_EGRESS -p tcp --dport 80 -j ACCEPT
sudo iptables -A SANDBOX_EGRESS -p tcp --dport 443 -j ACCEPT

# 允許 MCP Server (important-comment)
sudo iptables -A SANDBOX_EGRESS -p tcp --dport 8080 -j ACCEPT

# 封鎖所有其他出站流量 (important-comment)
sudo iptables -A SANDBOX_EGRESS -j DROP

# 應用到 Docker bridge (important-comment)
sudo iptables -A FORWARD -i docker0 -j SANDBOX_EGRESS
```

### 7.2 DNS 白名單

建立 `/etc/dnsmasq.d/sandbox-whitelist.conf`:

```conf
# 僅允許存取以下域名 (important-comment)
address=/api.render.com/0.0.0.0
address=/sentry.io/0.0.0.0
address=/github.com/0.0.0.0

# 其他域名回傳 NXDOMAIN (important-comment)
address=/#/
```

### 7.3 Rate Limiting

使用 `tc` 限制網路速率:

```bash
# 限制容器網路速率為 10Mbps (important-comment)
sudo tc qdisc add dev docker0 root tbf rate 10mbit burst 32kbit latency 400ms
```

---

## 8. 監控與告警

### 8.1 Sentry 安全事件追蹤

在 `mcp/server.py` 新增安全事件記錄:

```python
import sentry_sdk

def log_security_event(event_type: str, details: dict):
    """記錄安全事件至 Sentry"""
    sentry_sdk.capture_message(
        f"Security Event: {event_type}",
        level="warning",
        extras=details
    )

# 使用範例 (important-comment)
log_security_event("high_risk_operation", {
    "tool": "shell",
    "command": "rm -rf /tmp/test",
    "agent_id": "ops-agent-001",
    "approved": False
})
```

### 8.2 CloudWatch/Prometheus Metrics

監控指標:

```python
# 容器資源使用 (important-comment)
- sandbox.cpu.usage
- sandbox.memory.usage
- sandbox.disk.usage
- sandbox.network.rx_bytes
- sandbox.network.tx_bytes

# 安全事件 (important-comment)
- sandbox.security.events.total
- sandbox.security.approvals.pending
- sandbox.security.approvals.rejected

# 性能指標 (important-comment)
- sandbox.tool_calls.duration
- sandbox.tool_calls.errors
```

### 8.3 告警規則

建立 Sentry Alert Rules:

1. **CPU 使用過高**
   - Condition: `sandbox.cpu.usage > 80%` for 5 minutes
   - Action: 通知 Ops team + 自動縮容

2. **記憶體洩漏**
   - Condition: `sandbox.memory.usage` 持續增長 15 minutes
   - Action: 重啟容器 + 記錄事件

3. **異常系統調用**
   - Condition: Seccomp 阻擋次數 > 10/min
   - Action: 暫停容器 + 人工審查

4. **高風險操作被拒**
   - Condition: `sandbox.security.approvals.rejected > 3` in 1 hour
   - Action: 通知安全團隊

---

## 9. 事件響應

### 9.1 安全事件分級

| 級別 | 描述 | 響應時間 | 處理流程 |
|------|------|---------|---------|
| 🔴 **Critical** | 容器逃逸、憑證洩漏 | < 5 min | 立即停止所有 Sandbox + 通知 CEO |
| 🟠 **High** | 異常系統調用、資源耗盡 | < 15 min | 停止問題 Sandbox + 調查 |
| 🟡 **Medium** | 高風險操作被拒 | < 1 hour | 記錄事件 + 通知 Ops team |
| 🟢 **Low** | 一般告警 | < 24 hours | 自動記錄 |

### 9.2 響應劇本

#### 劇本 1: 容器逃逸偵測

```bash
# 1. 立即停止所有 Sandbox (important-comment)
docker ps -a | grep sandbox | awk '{print $1}' | xargs docker stop

# 2. 收集日誌 (important-comment)
docker logs sandbox-ops-agent > /tmp/incident-$(date +%s).log

# 3. 檢查 host 系統 (important-comment)
sudo ausearch -m avc -ts recent  # AppArmor 拒絕事件 (important-comment)
sudo dmesg | grep seccomp  # Seccomp 阻擋事件 (important-comment)

# 4. 通知團隊 (important-comment)
# (使用預設的 PagerDuty/Slack webhook)

# 5. 開啟事故調查 Issue (important-comment)
gh issue create --repo RC918/morningai \
  --title "[SECURITY] Container Escape Detected" \
  --body "$(cat /tmp/incident-$(date +%s).log)" \
  --label security,incident
```

#### 劇本 2: 資源耗盡

```bash
# 1. 識別問題容器 (important-comment)
docker stats --no-stream | grep sandbox

# 2. 檢查資源限制 (important-comment)
docker inspect sandbox-ops-agent | jq '.HostConfig.Memory'

# 3. 重啟容器（釋放資源） (important-comment)
docker restart sandbox-ops-agent

# 4. 調整資源限制（如需要） (important-comment)
# 修改 SandboxConfig 並重新部署
```

---

## 10. 定期審計

### 10.1 每週檢查清單

- [ ] 檢查 Sentry 安全事件（過去 7 天）
- [ ] 審查高風險操作審批記錄
- [ ] 驗證容器資源使用未超標
- [ ] 檢查 Docker image 安全掃描結果
- [ ] 更新依賴套件（如有安全更新）

### 10.2 每月檢查清單

- [ ] 審查 Seccomp/AppArmor 設定是否需調整
- [ ] 驗證網路隔離規則是否有效
- [ ] 檢查日誌保留策略
- [ ] 進行滲透測試（模擬容器逃逸）
- [ ] 更新安全文檔

### 10.3 每季檢查清單

- [ ] 完整安全審計（外部顧問）
- [ ] 更新威脅模型
- [ ] 審查事件響應劇本
- [ ] 進行災難復原演練
- [ ] 更新合規文檔（SOC2/HIPAA）

---

## 附錄

### A. 相關檔案

- Dockerfile: `handoff/20250928/40_App/orchestrator/sandbox/ops_agent/Dockerfile`
- Docker Sandbox: `handoff/20250928/40_App/orchestrator/sandbox/docker_sandbox.py`
- Seccomp Profile: `handoff/20250928/40_App/orchestrator/sandbox/ops_agent/seccomp-profile.json`
- AppArmor Profile: `/etc/apparmor.d/docker-ops-agent-sandbox`
- Network Hardening: `scripts/sandbox/network-hardening.sh`

### B. 參考資源

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Seccomp Tutorial](https://docs.docker.com/engine/security/seccomp/)
- [AppArmor Documentation](https://gitlab.com/apparmor/apparmor/-/wikis/Documentation)
- [OWASP Container Security](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

---

**最後更新**：2025-10-09  
**負責人**：Devin AI  
**狀態**：✅ 完成
