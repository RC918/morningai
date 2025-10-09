# 🏗️ Morning AI Agent Sandbox 技術架構設計

**版本**: 1.0
**日期**: 2025-10-08
**作者**: Devin AI (CTO)
**狀態**: 提案階段 (Proposal)

---

## 📋 執行摘要

本文檔提供完整的 Agent Sandbox 技術架構，目標是為 Morning AI 的 15 個 AI Agent 配備 Devin 級的通用軟體工程能力（完整 IDE、Shell、瀏覽器存取），使其能夠獨立調查、規劃、執行複雜任務。

---

## 🔍 一、現況分析

### 1.1 現有 Agent 實作狀態

經過深度代碼庫調查，以下是現有 Agent 的實際實作狀態：

| Agent | 實作檔案 | 程式碼行數 | 核心能力 | Devin 級能力 |
|-------|---------|-----------|---------|-------------|
| **Ops_Agent** | `ops_agent.py` | 171 | 性能監控、容量分析、自動擴縮容 | ❌ 無 |
| **PM_Agent** | `pm_agent.py` | 271 | Beta 用戶管理、用戶反饋分析、故事生成 | ❌ 無 |
| **Meta-Agent** | `meta_agent_decision_hub.py` | 558 | OODA 循環決策、Agent 協調 | ❌ 無 |
| **Dev_Agent** | ❌ 不存在 | 0 | - | ❌ 無 |
| **其他 Agent** | ❌ 僅文檔提及 | 0 | - | ❌ 無 |

**關鍵發現**:
- ✅ **Ops_Agent** 和 **PM_Agent** 已實作，但僅為簡單的 Python 類別
- ❌ **Dev_Agent** 完全不存在（儘管文檔中多次提及）
- ⚠️ 所有現有 Agent 都缺乏：
  - 獨立的執行環境（VM/Container）
  - IDE/Shell/Browser 存取能力
  - 長期記憶與上下文管理
  - 工具呼叫能力（MCP 整合）

### 1.2 現有編排架構

```
Meta-Agent (OODA Loop)
    ↓
LangGraph Orchestrator (handoff/40_App/orchestrator/graph.py)
    ↓
Redis Queue (RQ Worker)
    ↓
Simple Python Agents (ops_agent.py, pm_agent.py)
```

**限制**:
- Agent 只是普通的 Python 函數/類別
- 無沙箱隔離
- 無持久化執行環境
- 無工具存取能力

---

## 🎯 二、試點 Agent 建議

### 2.1 推薦：優先實作 **Ops_Agent**

**理由**:

| 評估維度 | Ops_Agent | Dev_Agent (不存在) | PM_Agent |
|---------|-----------|-------------------|----------|
| **實作基礎** | ✅ 已有 171 行代碼 | ❌ 從零開始 | ✅ 已有 271 行代碼 |
| **技術複雜度** | 🟡 中等 | 🔴 高 | 🟢 低 |
| **業務影響** | 🔴 高 (系統穩定性) | 🔴 高 (開發效率) | 🟡 中等 (產品規劃) |
| **工具需求** | Shell、監控工具 | IDE、Git、Shell、Browser | 較少工具需求 |
| **學習曲線** | 🟡 DevOps 知識 | 🔴 完整開發技能 | 🟢 產品管理 |
| **風險等級** | 🟡 中等 | 🔴 高 | 🟢 低 |

**選擇 Ops_Agent 的關鍵優勢**:

1. **已有實作基礎** ✅
   - 171 行現有代碼可擴展
   - 明確的功能邊界（監控、擴縮容、告警）
   - 與 Meta-Agent OODA 循環已整合

2. **工具需求明確** 🛠️
   - Shell 存取：執行 `kubectl`, `docker`, `curl` 等指令
   - 監控整合：Sentry、Prometheus、Grafana API
   - 雲端 API：Render、AWS、Vercel API

3. **價值立即可見** 💰
   - 自動化事件響應（5xx 錯誤 → 自動重啟服務）
   - 智能擴縮容決策（根據負載自動調整）
   - 成本優化（閒置資源自動縮減）

4. **風險可控** 🛡️
   - Ops 操作可設定 HITL（Human-in-the-Loop）審批
   - 有明確的回滾機制
   - 影響範圍清晰

### 2.2 第二階段：Dev_Agent

**為何不優先 Dev_Agent**:
- ❌ 目前完全不存在，需從零開始
- 🔴 技術複雜度極高（需要完整的 IDE、Git、測試環境）
- ⚠️ 錯誤影響範圍大（可能破壞代碼庫）

**建議時程**:
- **Phase 1** (Q4 2025): Ops_Agent Sandbox 試點
- **Phase 2** (Q1 2026): Dev_Agent Sandbox 實作

---

## 🏗️ 三、Agent Sandbox 技術架構

### 3.1 核心架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Meta-Agent OODA Loop                      │
│         (決策中樞 - meta_agent_decision_hub.py)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Sandbox Manager (新增)                    │
│  - Sandbox 生命週期管理                                       │
│  - 資源分配與回收                                             │
│  - 安全策略執行                                               │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Ops_Agent   │  │  Dev_Agent   │  │  PM_Agent    │
│   Sandbox    │  │   Sandbox    │  │   Sandbox    │
│              │  │              │  │              │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │  Shell   │ │  │ │   IDE    │ │  │ │ Browser  │ │
│ │ Browser  │ │  │ │  Shell   │ │  │ │  Shell   │ │
│ │ MCP SDK  │ │  │ │  Git     │ │  │ │ MCP SDK  │ │
│ └──────────┘ │  │ │ Browser  │ │  │ └──────────┘ │
│              │  │ │ MCP SDK  │ │  │              │
│ Container/VM │  │ └──────────┘ │  │ Container/VM │
└──────────────┘  │              │  └──────────────┘
                  │ Container/VM │
                  └──────────────┘
```

### 3.2 技術棧選擇

#### 3.2.1 沙箱環境：容器 vs 虛擬機

| 方案 | 優點 | 缺點 | 推薦度 |
|------|------|------|--------|
| **Docker Container** | 🟢 啟動快 (1-3s)<br/>🟢 資源效率高<br/>🟢 易於編排 (K8s) | 🔴 隔離性較弱<br/>🔴 難以執行特權操作 | ⭐⭐⭐ |
| **Firecracker microVM** | 🟢 隔離性強<br/>🟢 啟動快 (125ms)<br/>🟢 資源效率高 | 🔴 配置複雜<br/>🔴 生態較小 | ⭐⭐⭐⭐⭐ |
| **Full VM (QEMU/KVM)** | 🟢 最強隔離性<br/>🟢 完整 OS 環境 | 🔴 啟動慢 (30s+)<br/>🔴 資源消耗大 | ⭐⭐ |

**推薦方案**: **Firecracker microVM** 🎯

**理由**:
- AWS Lambda 和 Fargate 使用的同款技術
- 啟動速度接近容器，安全性接近 VM
- 每個 Agent 可擁有完整的 Linux 環境
- 支援 Render、Fly.io 等平台部署

#### 3.2.2 Docker 安全配置

**Dockerfile 範例（Ops_Agent Sandbox）**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl git bash jq ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright for browser automation
RUN pip install playwright==1.40.0 && \
    playwright install chromium && \
    playwright install-deps chromium

# Create non-root user
RUN useradd -m -u 1001 agentuser && \
    mkdir -p /workspace && \
    chown agentuser:agentuser /workspace

WORKDIR /home/agentuser

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP client code
COPY mcp_client.py .
COPY ops_agent_sandbox.py .

USER agentuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "mcp_client.py"]
```

**Docker 資源限制配置**:
```yaml
services:
  ops-agent-sandbox:
    build: ./sandbox/ops_agent
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2048M
          pids: 100
    
    # Security options
    security_opt:
      - no-new-privileges:true
      - seccomp=default
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp:size=1G,mode=1777
    
    volumes:
      - agent-workspace:/workspace:rw
    
    environment:
      - AGENT_ID=ops-agent-001
      - MCP_SERVER_URL=http://mcp-server:8080
```

#### 3.2.3 MCP (Model Context Protocol) 整合

**MCP Client 架構（Agent 端）**:
```python
class MCPClient:
    """MCP client for agent-side tool access"""
    
    async def call_tool(self, tool_name: str, params: dict):
        """Call a tool via MCP protocol (JSON-RPC 2.0)"""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
            "id": self.agent_id
        }
        # Send to MCP server...
```

**MCP Server 架構（Host 端）**:
```
Docker Host
    ↓
MCP Server (aiohttp)
    ├─ JSON-RPC 2.0 Protocol Handler
    ├─ HITL Gate (高風險操作審批)
    └─ Tool Implementations:
        ├─ ShellTool: 執行 bash 指令
        ├─ BrowserTool: Playwright 瀏覽器控制
        ├─ RenderTool: Render API 整合
        └─ SentryTool: Sentry API 整合
```

### 3.3 安全模型

#### 3.3.1 多層防禦

```
Layer 1: Network Isolation (VPC/Firewall)
    ↓
Layer 2: Resource Limits (CPU/Memory/Disk)
    ↓
Layer 3: Capability-based Security (seccomp/AppArmor)
    ↓
Layer 4: Audit Logging (所有操作記錄)
    ↓
Layer 5: HITL Gates (高風險操作需人工審批)
```

#### 3.3.2 資源限制

```yaml
# 每個 Agent Sandbox 的資源配額
resources:
  cpu: "1.0"          # 1 vCPU
  memory: "2Gi"       # 2GB RAM
  disk: "10Gi"        # 10GB 臨時儲存
  network:
    egress: "100Mbps" # 出站頻寬
  timeout:
    idle: "30m"       # 閒置 30 分鐘自動回收
    max: "2h"         # 最長執行 2 小時
```

#### 3.3.3 HITL (Human-in-the-Loop) 策略

```python
# 高風險操作需要人工審批
HITL_REQUIRED_OPERATIONS = {
    'ops_agent': [
        'delete_resource',      # 刪除資源
        'scale_down_to_zero',   # 縮容至 0
        'modify_production_db', # 修改生產資料庫
    ],
    'dev_agent': [
        'merge_to_main',        # 合併至主分支
        'force_push',           # 強制推送
        'delete_branch',        # 刪除分支
    ]
}
```

---

## 💰 四、成本分析

### 4.1 基礎設施成本

#### 方案 A：Firecracker on Render/Fly.io

| 資源類型 | 單位成本 | 數量 (15 Agents) | 月成本 |
|---------|---------|-----------------|--------|
| **Compute (1 vCPU, 2GB)** | $7/mo | 15 | $105 |
| **Storage (10GB)** | $0.15/GB/mo | 150GB | $22.50 |
| **Network (100GB egress)** | $0.10/GB | 100GB/agent | $150 |
| **Redis (Orchestration)** | $15/mo | 1 | $15 |
| **PostgreSQL (State)** | $25/mo | 1 | $25 |
| **Load Balancer** | $10/mo | 1 | $10 |
| **總計** | - | - | **$327.50/月** |

#### 方案 B：僅試點 Ops_Agent (單一 Agent)

| 資源類型 | 月成本 |
|---------|--------|
| Ops_Agent Sandbox (1 vCPU, 2GB) | $7 |
| Storage (10GB) | $1.50 |
| Network (10GB egress) | $1 |
| **總計** | **$9.50/月** |

**建議**: 從方案 B 開始 (單一 Ops_Agent 試點)，驗證架構後再擴展至全部 15 個 Agent。

### 4.2 開發成本估算

| 階段 | 工作項 | 預估工時 | 優先級 |
|------|--------|---------|--------|
| **Phase 1: Ops_Agent 試點** | | | |
| 1.1 Agent Sandbox Manager | 40h | P0 |
| 1.2 Firecracker 環境配置 | 24h | P0 |
| 1.3 MCP Client/Server 實作 | 32h | P0 |
| 1.4 Shell/Browser 工具整合 | 24h | P0 |
| 1.5 安全策略與資源限制 | 16h | P0 |
| 1.6 HITL 審批機制 | 20h | P1 |
| 1.7 監控與告警 | 16h | P1 |
| 1.8 測試與文檔 | 24h | P1 |
| **Phase 1 小計** | **196h (~5 週)** | |
| | | |
| **Phase 2: Dev_Agent 擴展** | | | |
| 2.1 IDE 環境 (VS Code Server) | 32h | P0 |
| 2.2 Git 整合與 GitHub API | 24h | P0 |
| 2.3 測試環境 (Jest, Pytest) | 20h | P1 |
| 2.4 CI/CD 整合 | 16h | P1 |
| **Phase 2 小計** | **92h (~2.5 週)** | |
| | | |
| **Phase 3: 全面推廣 (15 Agents)** | | | |
| 3.1 Sandbox Manager 擴展 | 24h | P0 |
| 3.2 資源調度優化 | 20h | P1 |
| 3.3 成本監控與優化 | 16h | P1 |
| **Phase 3 小計** | **60h (~1.5 週)** | |
| | | |
| **總計** | **348h (~9 週)** | |

---

## 🛠️ 五、實作路徑

### 5.1 Phase 1: Ops_Agent Sandbox 試點 (6 週)

#### Week 1-2: 基礎設施

```
✅ 任務 1.1: Agent Sandbox Manager 核心
  - 設計 Sandbox 生命週期 API
  - 實作 create_sandbox(), destroy_sandbox()
  - Docker 容器管理與資源限制

✅ 任務 1.2: Docker 環境配置
  - 建立 Ops_Agent Dockerfile
  - 配置安全策略 (seccomp, AppArmor, capabilities)
  - 資源限制 (cgroups: CPU, memory, disk, network)
  - 網路隔離設置
```

#### Week 3-4: MCP 整合

```
✅ 任務 1.3: MCP Protocol 實作
  - MCP Client (Agent 端)
  - MCP Server (工具提供端)
  - JSON-RPC 通訊層

✅ 任務 1.4: 工具實作
  - ShellTool (bash 指令執行)
  - BrowserTool (Playwright)
  - RenderTool (Render API)
  - SentryTool (Sentry API)
```

#### Week 5-6: 安全與測試

```
✅ 任務 1.5: 安全策略
  - Resource limits (cgroups)
  - Network isolation (iptables)
  - Seccomp profiles

✅ 任務 1.6: HITL 機制
  - 高風險操作識別
  - Slack 審批流程
  - 超時處理

✅ 任務 1.7: E2E 測試
  - Ops_Agent 自動化事件響應測試
  - 資源限制驗證
  - 安全策略驗證
```

### 5.2 Phase 2: Dev_Agent 擴展 (3 週)

```
Week 7-8: IDE 與 Git 整合
  - VS Code Server 整合
  - Git 指令與 GitHub API
  - Code review 自動化

Week 9: 測試與文檔
  - Dev_Agent E2E 測試
  - 開發者文檔
  - 最佳實踐指南
```

### 5.3 Phase 3: 全面推廣 (2 週)

```
Week 10: 擴展至其他 Agent
  - PM_Agent Sandbox
  - Support_Agent Sandbox
  - 其他 Agent 逐步上線

Week 11: 優化與監控
  - 成本監控儀表板
  - 性能優化
  - SLA 定義
```

---

## 📊 六、技術債務與風險

### 6.1 技術債務

| 債務項目 | 影響 | 緩解策略 |
|---------|------|---------|
| **Dev_Agent 缺失** | 🔴 高 | Phase 2 優先實作 |
| **缺乏 Agent 長期記憶** | 🟡 中 | 整合 pgvector (已有) |
| **簡易的 LangGraph 編排** | 🟡 中 | 擴展 graph.py 功能 |
| **無 Agent 監控儀表板** | 🟡 中 | 使用 Sentry + Grafana |

### 6.2 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|---------|
| **Docker 隔離性較弱** | 🟡 中 | 🟡 中 | 多層安全策略 + HITL 審批 |
| **資源成本超支** | 🟡 中 | 🟡 中 | 資源限制 + 自動回收 |
| **Agent 操作錯誤** | 🟢 低 | 🔴 高 | HITL + 審計日誌 |
| **性能瓶頸** | 🟡 中 | 🟡 中 | Pre-warmed pool + 快取 |

---

## 🎯 七、關鍵決策點

### 決策 1: 試點 Agent 選擇
**建議**: ✅ **Ops_Agent**
**理由**: 已有實作基礎、工具需求明確、風險可控

### 決策 2: 沙箱技術選擇
**建議**: ✅ **Docker Container + 嚴格安全策略**
**理由**: Render 平台相容性、成熟生態、足夠安全性

### 決策 3: MCP 整合方式
**建議**: ✅ **自建 MCP Server**
**理由**: 完全控制、易於擴展、符合現有架構

### 決策 4: 推廣策略
**建議**: ✅ **逐步推廣 (Ops → Dev → 其他)**
**理由**: 降低風險、持續驗證、成本可控

---

## 📚 八、參考資料

### 8.1 技術文檔
- [Firecracker GitHub](https://github.com/firecracker-microvm/firecracker)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Devin Technical Blog](https://www.cognition.ai/blog)

### 8.2 現有系統文檔
- `ops_agent.py` - Ops_Agent 現有實作
- `meta_agent_decision_hub.py` - Meta-Agent OODA 循環
- `handoff/40_App/orchestrator/graph.py` - LangGraph 編排器
- `render.yaml` - 現有部署配置

---

## 🤝 九、下一步行動

### 立即行動 (本週)
1. ✅ **獲得架構批准** - 與 Ryan 討論並確認技術方案
2. ⏳ **組建團隊** - 分配 Phase 1 任務
3. ⏳ **環境準備** - 配置 Firecracker 開發環境

### 近期行動 (2 週內)
4. ⏳ **實作 Agent Sandbox Manager** - 核心基礎設施
5. ⏳ **MCP 協議整合** - Client/Server 實作
6. ⏳ **Ops_Agent 試點** - 第一個具備 Devin 級能力的 Agent

### 中期目標 (6 週內)
7. ⏳ **Phase 1 完成** - Ops_Agent Sandbox 上線
8. ⏳ **啟動 Phase 2** - Dev_Agent 開發

---

## 📞 聯絡資訊

**技術負責人**: Devin AI (CTO)
**Devin Session**: https://app.devin.ai/sessions/fa70d2a68be34ac8bd0570d284d4515a
**GitHub**: @RC918
**日期**: 2025-10-08

---

**結語**:

這份架構設計提供了從試點到全面推廣的完整路徑。通過 Ops_Agent 作為試點，我們可以在 6 週內驗證核心技術棧，並為後續的 Dev_Agent 和其他 Agent 奠定堅實基礎。

關鍵成功因素：
- ✅ 選擇已有實作基礎的 Ops_Agent 作為試點
- ✅ 使用 Firecracker microVM 平衡安全與性能
- ✅ 自建 MCP Server 完全掌控工具生態
- ✅ HITL 機制確保高風險操作安全
- ✅ 逐步推廣策略控制成本與風險

建議 Ryan 優先審閱以下關鍵章節：
1. **第二章 - 試點 Agent 建議**: 為何選擇 Ops_Agent
2. **第三章 - 技術架構**: Firecracker + MCP 整合方案
3. **第四章 - 成本分析**: 試點僅需 $9.50/月
4. **第五章 - 實作路徑**: 6 週完成 Phase 1

期待您的反饋與批准，讓我們開始這個激動人心的技術升級！🚀
