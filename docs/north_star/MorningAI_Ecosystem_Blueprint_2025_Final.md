# MorningAI — 全生態系 Blueprint（2025 Final 版）

## Multi-Agent Operating System for AI-Driven Autonomous Software Engineering

### Version: 2025-Q4 Final Enterprise Edition

MorningAI 生態系是一個 **多代理、自主規劃、自動建置、自主驗收、自我治理、自我修復** 的完整 AI Operating System。

它包含：

* 9 大核心引擎
* 13 種代理角色
* 8 套治理與安全機制（詳見 Section 4）
* 4 層架構（Model → Intelligence → Governance → Infrastructure）
* 多模型 / 多 Provider / 多 Cloud 的完整協作
* 自動 Provisioning + Drift 監控
* Simulation Suite（完整自動 QA 系統）
* Telemetry、Memory、Logs—完整軌跡可重建

MorningAI 的目標：

**讓 AI 自己規劃、自己寫程式、自己審查、自己測試、自己部屬、自己監控、自己修復。**

---

# 1. High-Level Architecture（高階架構總覽）

```
┌────────────────────────────────────────────────────────────┐
│                      MorningAI Operating System             │
├───────────────────────────────┬────────────────────────────┤
│   Intelligence Layer          │   Governance & Safety Layer │
│   (Planner / Flow / Agents)   │   (Safety / Compliance /    │
│                               │    Governance / Provisioning│
├───────────────────────────────┴────────────────────────────┤
│              Infrastructure Layer (Memory / Telemetry)      │
├────────────────────────────────────────────────────────────┤
│         Model Layer (Gemini-First Multi-Provider)           │
└────────────────────────────────────────────────────────────┘
```

MorningAI 生態系共分為 **4 個層級**：

1. **Model Layer（模型層）**
2. **Intelligence Layer（智慧層：Planner / Flow / Agents）**
3. **Governance Layer（治理層：Safety / Compliance / Governance）**
4. **Infrastructure Layer（基礎層：Memory / Telemetry / Simulation）**

---

# 2. Model Layer（模型層）

MorningAI 2025 Final 採用 **Gemini-First Multi-Provider 架構**（routing_policy.json v1.3）：

| Tier       | Primary Model      | Secondary Model | Tertiary Model | 用途                        |
| ---------- | ------------------ | --------------- | -------------- | ------------------------- |
| **Tier 0** | gemini-2.0-flash   | qwen-max        | gpt-4o         | Critical reasoning, Judge, Planning |
| **Tier 1** | gemini-2.0-flash   | qwen-plus       | gpt-4o-mini    | Deep reasoning, Coding, Review |
| **Tier 2** | gemini-2.0-flash   | qwen-turbo      | gpt-4o-mini    | Translation, Summarization, Chat |
| **Tier 3** | gemini-2.0-flash   | qwen-turbo      | gpt-4o-mini    | UI 文案 / Basic tasks (ux_copy) |

### Task Type 到 Tier 的映射

| Task Type      | Tier | Fallback Tier |
| -------------- | ---- | ------------- |
| planning       | 0    | 1             |
| coding         | 1    | 2             |
| review         | 1    | 2             |
| routing        | 1    | 2             |
| analysis       | 1    | 2             |
| translation    | 2    | 3             |
| summarization  | 2    | 3             |
| chat           | 2    | 3             |
| ux_copy        | 3    | 2             |

### Multi-Provider 支援

* **Google Gemini**（Primary - 最佳品質與速度平衡）
* **AliCloud DashScope**（Secondary - qwen-max/plus/turbo）
* **OpenAI**（Tertiary - gpt-4o/gpt-4o-mini fallback）

> **Note**: 此架構於 2026-01 更新，反映實際 Production 配置（[審計報告](https://app.devin.ai/sessions/1e2806264a294d24a361f67ddb70a487)）。原 Qwen3 Multi-Tier 架構及 OpenRouter 整合保留作為未來擴展方向（參見 Wish Pool v2）。

---

# 3. Intelligence Layer（智慧層）

包含 3 大引擎與 13 類 Agents。

---

## 3.1 Planner v3 — 智能規劃器

Planner v3 的任務：

* 解析使用者意圖
* 自動分解為任務樹
* 指派代理角色
* 選擇適合的 Flow 模板
* 決定模型 Tier
* 多步驟任務轉換成 pipeline

Planner v3 支援：

* 思考步驟（Thinking Tokens）
* Memory v2 上下文回溯
* Routing v2 模型策略
* 自主調整計畫（self-refinement）
* Debate Engine v2 協作決策

---

## 3.2 Flow Controller v3 — 智能動態狀態機

Flow v3 的核心：

* **動態路徑規劃（Dynamic Pathing）**
* **多代理分支（Multi-Agent Branching）**
* **自動合併（Auto-Merge）**
* **Fail-Fast Recovery（快速回復）**
* **Safety/Compliance-aware Routing**

Flow Controller 代表整個 MorningAI 的 **Runtime Engine**。

---

## 3.3 Agent Catalog V2 — 代理角色全集

你的生態系包含 13 種角色：

### Core Engineering Agents

* **Planner Agent**
* **Coding Agent**
* **Reviewer Agent**
* **Test Agent v2**
* **Debugger Agent**

### UX / UI Agents

* **UI Consistency Agent**
* **UX Heuristic Agent**
* **Visual Regression Agent**
* **Design Token Governance Agent**

### Governance / Reasoning Agents

* **Judge Agent（Debate Engine v2）**
* **Debate Agent（Left / Right）**
* **Risk Analyzer Agent**

### Implementation Notes

> **Issue #4118**: AgentType Enum Extension
>
> 所有 13 種 Agent 角色已在 `governance/principal_context.py::AgentType` enum 中定義：
>
> | Blueprint 名稱 | AgentType Enum | 值 |
> |---------------|----------------|-----|
> | Planner Agent | `PLANNER` | `"planner"` |
> | Coding Agent | `CODING` | `"coding"` |
> | Reviewer Agent | `REVIEWER` | `"reviewer"` |
> | Test Agent v2 | `TEST` | `"test"` |
> | Debugger Agent | `DEBUGGER` | `"debugger"` |
> | UI Consistency Agent | `UI_CONSISTENCY` | `"ui_consistency"` |
> | UX Heuristic Agent | `UX_HEURISTIC` | `"ux_heuristic"` |
> | Visual Regression Agent | `VISUAL_REGRESSION` | `"visual_regression"` |
> | Design Token Governance | `DESIGN_TOKEN_GOVERNANCE` | `"design_token_governance"` |
> | Judge Agent | `JUDGE` | `"judge"` |
> | Debate Agent (Left) | `DEBATE_LEFT` | `"debate_left"` |
> | Debate Agent (Right) | `DEBATE_RIGHT` | `"debate_right"` |
> | Risk Analyzer Agent | `RISK_ANALYZER` | `"risk_analyzer"` |

每個 Agent 都遵守：

* **Agent Interaction Protocol v2（AIP v2）**
* **Safety/Compliance layer gating**
* **Memory v2 的寫入規範**

---

## 3.4 BrowserNode v2 — 瀏覽器自動化與自癒系統

BrowserNode 是 MorningAI 中具有最高「不確定性」的組件，因為它依賴不可控的第三方 UI。

### 核心能力

* **Browser Automation**: Playwright-based 瀏覽器自動化
  - Navigate, Click, Type, Screenshot
  - Headless/Headed mode support
  - Multi-tab management
  - iframe / shadow DOM navigation

* **CLI Executor**: Shell command execution
  - Sandboxed execution environment
  - Output capture and parsing

### Self-Heal Engine（5 階段自癒管線）

1. **Failure Detection**: DOM snapshot + error string + screenshot 封存
2. **Failure Classification**: Missing/Weak/Ambiguous Selector, Layout Shift, Timing Issue
3. **Reproduction Engine**: 在 sandbox 中重現行為，生成 Minimal Reproduction Case (MRE)
4. **Self-Heal Engine**: Selector Strengthening, Fallback Chain, Timing Auto-Adjust
5. **Regression & Learning**: 自動建立 regression test，更新 Knowledge Base

### Selector Knowledge Base

```json
{
  "element": "submit_button",
  "selectors": ["button[data-testid='submit']", "button[aria-label='Submit']", "text='Submit'"],
  "fallback_chain": ["aria-label", "data-testid", "text match", "semantic DOM match"],
  "confidence": 0.92
}
```

BrowserNode v2 啟動時會載入 Knowledge Base，實現「越用越準、越跑越穩」。

---

## 3.5 Diagnostic Agent — 錯誤診斷與重現

Diagnostic Agent 負責錯誤的診斷、重現與根因分析：

* **Error Reproduction**: 在隔離環境中重現錯誤
* **MRE Generation**: 生成 Minimal Reproducible Example
* **Root Cause Analysis**: 識別錯誤根因
* **Blast Radius Assessment**: 評估影響範圍

Diagnostic Agent 與 Test Agent v2 協作，將錯誤轉換為 regression test。

---

# 4. Governance & Safety Layer（治理與安全層）

八大治理與安全機制：

1. **Safety Governor v2** (Section 4.1) - 風險掃描、Prompt Injection 防護
2. **Compliance Radar v2** (Section 4.2) - PII 掃描、法規遵循
3. **Model Governance Framework v2** (Section 4.3) - Drift 監測、Provider 健康
4. **Autonomous Provisioning v2** (Section 4.4) - 自動模型管理
5. **Agent Interaction Protocol v2 (AIP v2)** - Agent 間通訊規範（詳見 Section 4.5）
6. **Memory v2 Write Policies** - 記憶寫入規範（詳見 Section 5.1）
7. **Evidence Ledger** - 決策證據鏈（詳見 Section 4.6）
8. **Capability-Based Security** - 基於能力的安全模型（詳見 Section 4.7）

---

**核心治理模組（4.1-4.4）**

---

## 4.1 Safety Governor v2

MorningAI 的主要安全引擎：

* 雙層風險模型：Risk Scan + Risk Override
* Prompt Injection 防護
* Jailbreak 防護
* Harmful Content 攔截
* Tier-0 專用復審機制（critical tasks）

---

## 4.2 Compliance Radar v2

處理法規、隱私、金融、醫療等：

* PII 掃描
* 法律風險
* 醫療風險
* 財務風險
* 政治敏感度政策
* 著作權判定

每一個 Flow v3 的 transition 都會通過 Compliance 層。

---

## 4.3 Model Governance Framework v2

治理所有模型選擇與健康：

* Drift 監測
* Provider 健康監控
* 成本治理
* Routing 權重調整
* 模型效能趨勢分析
* 自動模型降級 / 升級

---

## 4.4 Autonomous Provisioning v2

自動模型管理：

* 週期性評估模型品質
* 健康過低自動降低優先權
* 不佳的 Provider 自動降級
* 路由權重自動更新
* 自動更新 Benchmark 值

MorningAI 具備自我演化能力。

---

## 4.5 Agent Interaction Protocol v2 (AIP v2)

定義所有 Agent 間的通訊規範：

* **Message Schema**: 統一的 AgentMessage 格式（sender, receiver, payload, trace_id）
* **Handshake Protocol**: Agent 啟動時的能力宣告與驗證
* **Error Propagation**: 標準化的錯誤傳遞與回復機制
* **Context Passing**: 跨 Agent 的上下文傳遞規範
* **Priority Levels**: 訊息優先級（CRITICAL, HIGH, NORMAL, LOW）

所有 Agent 必須實作 AIP v2 介面才能加入 MorningAI 生態系。

---

## 4.6 Evidence Ledger

記錄所有決策的證據鏈：

* **Decision Record**: 每個重要決策的完整記錄
* **Reasoning Chain**: 決策推理過程的追蹤
* **Audit Trail**: 可審計的決策歷史
* **Rollback Support**: 支援決策回滾的證據保存

用於：
* 事後分析與除錯
* 合規審計
* 模型行為分析
* 持續改進

---

## 4.7 Capability-Based Security

基於能力的安全模型：

* **Capability Tokens**: Agent 執行特定操作的權限令牌
* **Least Privilege**: 最小權限原則
* **Dynamic Revocation**: 動態撤銷能力
* **Scope Limitation**: 操作範圍限制

安全層級：
* **Level 0**: 唯讀操作（Read-Only）
* **Level 1**: 本地修改（Local Modification）
* **Level 2**: 外部 API 呼叫（External API）
* **Level 3**: 部署操作（Deployment）
* **Level 4**: 系統配置（System Configuration）

---

# 5. Infrastructure Layer（基礎層）

---

## 5.1 Memory v2 — 多層記憶體系統

4 層記憶：

### 1. 即時任務記憶（Short-Term）

### 2. 代理互動記憶（Agent Interaction）

### 3. 長期知識記憶（Knowledge Base）

### 4. 治理記憶（Governance Memory）

用途：

* Flow v3 回復能力
* Planner v3 長期規劃
* Debate context
* Drift 分析
* Safety/Compliance pattern tracking

---

## 5.2 Telemetry & Logs v2 — 完整運行軌跡

Telemetry v2 能：

* 重建整個 Flow v3 的執行
* 回放整個多代理推理
* 產生故障報告
* 計算模型健康
* 提供 Simulation Suite 所需資料

---

## 5.3 Multi-Agent Simulation Suite v1

你的生態系 QA 系統：

* 多代理端到端測試
* Flow v3 分支測試
* routing 測試
* safety/compliance 測試
* drift 測試
* provider fallback 測試
* 可回放、可視覺化

這是 MorningAI「品質」的根基。

---

## 5.4 Regression Pipeline v1 — 自動回歸測試管線

將任何錯誤轉換為永不再犯的 regression test：

### Error Sources（錯誤來源）

* **Runtime Errors**: Node backend / Python orchestrator logs
* **BrowserNode Failures**: selector 找不到、DOM 結構變動
* **Sentry / Datadog Alerts**: stack trace + breadcrumbs
* **Diagnostic Agent Reports**: root cause + 重現步驟

### Regression Candidate Selection

```
priority = severity*0.5 + frequency*0.3 + blast_radius*0.2
```

* **P0**: 立即建立 regression
* **P1**: 排入 nightly regression cycle
* **P2**: 觀察是否重複再建立

### Regression Test Generation Flow

```
Error → Diagnostic Agent → MRE → Test Agent v2 → Regression Test → CI Validation
```

### CI Enforcement

* 若 regression 測試失敗 → 阻擋 PR
* 若 regression 測試被修改 → 需要 reviewer 強制審查
* 若 regression 測試被刪除 → Safety Governor 擋下

### Weekly Regression Cycle

Flow Controller v2 每週執行：
* 搜集新錯誤
* 自動生成 regression
* 重新計算 regression coverage
* 更新 Risk Heatmap

Regression Pipeline 讓整個系統「越用越穩、越跑越強」。

---

# 6. Core Runtime Pipeline（核心執行生命週期）

以下為 MorningAI 任務從開始到結束的完整生命週期：

```
User Input
   ↓
Planner v3 → 任務分解、決策、路由策略
   ↓
Flow Controller v3 → 動態狀態機
   ↓
Agent Chain（Coding / Review / Test / UX …）
   ↓
Safety Governor v2
   ↓
Compliance Radar v2
   ↓
Memory v2 + Telemetry v2 寫入
   ↓
Output 給使用者
   ↓
Governance Engine 分析運行結果
```

---

# 7. Cross-Agent Collaboration Model（跨代理協作模型）

MorningAI 採用 **三層協作模型**：

### 1. Sequential Collaboration（順序協作）

Coding → Reviewer → Test → Deploy

### 2. Parallel Collaboration（並行協作）

UX Agent + UI Agent + Visual Regression Agent 同步運作

### 3. Adversarial Collaboration（對抗協作）

Debate Engine v2
→ Left Agent vs Right Agent
→ Judge Agent 做決策

適用於：

* 高風險任務
* 架構選型
* 成本最佳化策略
* 隱私議題
* 推理困難任務

---

# 8. System-Level Diagram（總架構圖・文字版）

```
                           ┌────────────────────┐
                           │     User Request    │
                           └─────────┬──────────┘
                                     ▼
                           ┌────────────────────┐
                           │     Planner v3      │
                           └─────────┬──────────┘
                                     ▼
                           ┌────────────────────┐
                           │  Flow Controller v3 │
                           └───────┬────────────┘
         ┌─────────────────────────┼───────────────────────────────┐
         ▼                         ▼                               ▼
  Coding Agent              Reviewer Agent                    UX / UI Agents
         ▼                         ▼                               ▼
  Test Agent v2             Debugger Agent                    Visual Regression
         └───────────────┬────────┴────────┬──────────────────────┘
                         ▼                 ▼
              Safety Governor v2   Compliance Radar v2
                         ▼                 ▼
                    Memory v2        Telemetry v2
                         ▼                 ▼
                     Governance Engine（MGFv2）
                         ▼
                Autonomous Provisioning v2
                         ▼
                      Final Output
```

---

# 9. Ecosystem Guarantees（生態系保證）

MorningAI 2025 Final 保證：

### **1. 可預測性（Deterministic）**

所有行為都能透過 Telemetry + Memory 還原。

### **2. 安全性（Safe by Design）**

所有輸出必須通過 safety/compliance。

### **3. 可維護性（Self-Governed）**

模型、Provider、Flow、Routing 都能自動管理。

### **4. 可擴展性（Modular）**

新 Agents、新 Providers、新模型都能無縫加入。

---

# 10. Future Evolution（2026 進化方向）

* Planner v4（Meta-cognitive Planning）
* Safety Governor v3（多代理安全推理）
* Compliance Radar v3（政策自動更新）
* Debate Engine v3（三方辯論）
* Autonomous Refactoring（自動大型重構）
* Deep Memory v3（超長期知識 + Embedding decay control）
* Full-Auto PR Lifecycle（AI 全自動發 PR + 合併 + 修復）

MorningAI 的最終目標：

**打造一個能自我改善、自我演化的 AI Software Engineering Factory。**

---

## ChangeLog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2025-Q4 Final | 2025-12-21 | Ryan Chen (@RC918) | Initial version imported from Ecosystem Wish Pool v2 |
| 2025-Q4 Final | 2025-12-30 | Ryan Chen (@RC918) with Devin AI | Added EPIC I mapping for Blueprint 4.3 (Model Governance Framework v2) + 4.4 (Autonomous Provisioning v2) implementation. See [EPIC I #3342](https://github.com/RC918/morningai/issues/3342). |
| 2025-Q4 Final | 2026-01-12 | Ryan Chen (@RC918) with Devin AI | **Architecture Gap Fix**: (1) Fixed 4/5 layer inconsistency → unified to 4 layers. (2) Enumerated all 8 governance mechanisms explicitly. (3) Added Section 4.5 AIP v2, Section 4.6 Evidence Ledger, Section 4.7 Capability-Based Security. (4) Added Section 3.4 BrowserNode v2 with Self-Heal Engine. (5) Added Section 3.5 Diagnostic Agent. (6) Added Section 5.4 Regression Pipeline v1. |
| 2025-Q4 Final | 2026-01-17 | Ryan Chen (@RC918) with Devin AI | **Model Layer Update**: Updated Section 2 to reflect actual Gemini-First Multi-Provider architecture (routing_policy.json v1.3). Changed from theoretical Qwen3 Multi-Tier to production Gemini-first + AliCloud + OpenAI configuration. Added Task Type to Tier mapping table. Based on [comprehensive ecosystem audit](https://app.devin.ai/sessions/1e2806264a294d24a361f67ddb70a487). Fixed Chat tier assignment (Tier 2, not Tier 3). Removed unimplemented OpenRouter reference. |

