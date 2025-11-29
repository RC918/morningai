# MorningAI 專案深度分析與整合路線圖

**日期**: 2025-11-18  
**版本**: 1.0  
**作者**: Devin AI (CTO Technical Assessment)

---

## 🔄 2025-11-29 狀態更新：Phase 2-4 已完成

> **重要**：本報告撰寫於 2025-11-18，以下為截至 2025-11-29 的最新狀態更新。

### 當前 LangGraph Orchestrator 架構（9 節點工作流）

**檔案**: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py` (1191 行)

```text
planner → security_advisor → governance_advisor → executor → ci_monitor → reviewer → decision → fixer → finalizer
```

| 節點 | 功能 | Phase | 狀態 |
|------|------|-------|------|
| `planner` | LLM 動態計畫生成 (USE_LLM_PLANNER) | Phase 1 | ✅ 完成 |
| `security_advisor` | SecurityAgent 安全分析 (advisory-only) | Phase 4 PR-2 | ✅ 完成 |
| `governance_advisor` | GovernanceAgent 治理合規分析 (advisory-only) | Phase 4 PR-3 | ✅ 完成 |
| `executor` | 代碼生成執行 (調用 graph.execute()) | Phase 1 | ✅ 完成 |
| `ci_monitor` | CI 狀態監控 | Phase 1 | ✅ 完成 |
| `reviewer` | ReviewerAgent 代碼審查 | Phase 3 | ✅ 完成 |
| `decision` | 合併決策 (approve/request_changes/needs_fix) | Phase 3 | ✅ 完成 |
| `fixer` | AutoFixer 自動修復 (整合 ReviewerAgent) | Phase 2 | ✅ 完成 |
| `finalizer` | 整理最終結果 | Phase 1 | ✅ 完成 |

### 已完成的關鍵 PRs

**Phase 2 (Fixer Node + Safety Rules)**:
- PR #1660: Phase 2 Step A infrastructure - ProjectEngineerAgent, Safe Tasks, PR Review CLI
- PR #1667: Phase 2 Step C Fixer Node - AutoFixer integration with ReviewerAgent
- PR #1668: LangGraph E2E integration tests for fixer_node
- PR #1669: Safety rules enforcement + failure fallback logging

**Phase 3 (Multi-Agent Flow)**:
- PR #1681: Core orchestrator multi-agent flow
- PR #1682: Metrics for orchestrator multi-agent flow
- PR #1683: ProjectEngineerAgent human entry point
- PR #1685: Code-Audit Pipeline - timeout, semantic rules, E2E tests
- PR #1686: Staging rollout & monitoring

**Phase 4 (Security/Governance)**:
- PR #1688: Semantic Rules v2 - directory + task type restrictions
- PR #1689: SecurityAgent skeleton + integration
- PR #1690: GovernanceAgent skeleton + integration

**LLM 抽象層**:
- PR #1672: LLMClient abstraction layer for multi-provider support
- PR #1680: Gemini Provider support

### 原報告狀態對照

| 原報告狀態 (2025-11-18) | 當前狀態 (2025-11-29) |
|------------------------|----------------------|
| ❌ Phase 1.5 偏離路線圖 | ✅ 已整合進 Phase 3 multi-agent flow |
| ❌ Phase 2 方法錯誤 | ✅ 已重建為整合方法 (PRs #1660-1669) |
| ⚠️ planner_node 靜態計畫 | ✅ 已整合 LLM Planner (USE_LLM_PLANNER) |
| ⚠️ fixer_node 缺少 ReviewerAgent | ✅ 已整合 ReviewerAgent |
| ❌ 缺少 SecurityAgent | ✅ 已實現 (PR #1689) |
| ❌ 缺少 GovernanceAgent | ✅ 已實現 (PR #1690) |

---

> **以下為原報告內容（2025-11-18 撰寫），保留作為歷史參考。**

---

## 📊 執行摘要

本報告深度分析 MorningAI 專案當前狀態、架構與資源，並整合 4 條路線（成功指標、優化策略、當前狀態、原始路線圖）為一條完整可執行的路線圖。

**關鍵發現**（2025-11-18 狀態，已過時）：
- ✅ Phase 0 部分完成（金絲雀邏輯完整，但測試覆蓋率不足）
- ⚠️ Phase 1 部分完成（基礎設施就緒，但 LLM 未整合進 planner_node）
- ❌ Phase 1.5 偏離路線圖（監控儀表板不在原定計畫內）
- ❌ Phase 2 方法錯誤（PR #1347 建立平行系統而非整合 LangGraph）

**整合路線圖時程**（2025-11-18 預估，已完成）：
- Phase 0 補完：2-3 天（測試覆蓋率 → 25-30%）
- Phase 1 完成：3-5 天（LLM 整合 + 金絲雀啟用）
- Phase 2 重建：5-7 天（整合方法，非平行系統）
- Phase 3-6：按原定路線圖執行

---

## 🏗️ 當前架構深度分析

### 1. 核心編排系統 (Orchestration)

#### LangGraph Orchestrator
**檔案**: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py` (422 行)

**5 節點工作流**：

```
┌─────────────┐
│ planner_node│ (lines 57-92)
│  靜態計畫   │ ❌ 需要 LLM 整合
└──────┬──────┘
       │
       ▼
┌─────────────┐
│executor_node│ (lines 94-144)
│ 執行任務    │ ✅ 調用 graph.execute()
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ci_monitor   │
│ 監控 CI     │ ✅ 功能完整
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ fixer_node  │ (lines 199-226)
│ 修復失敗    │ ⚠️ 需要 ReviewerAgent 整合
└──────┬──────┘
       │
       ▼
┌─────────────┐
│finalizer    │ (lines 228-259)
│ 完成任務    │ ⚠️ 需要報告 Phase 2 指標
└─────────────┘
```

**關鍵發現**：
- `planner_node` 使用靜態計畫（lines 63-72），需要整合 GPT-4 LLM 動態生成
- `executor_node` 調用 `graph.execute()`，可以整合代碼生成邏輯
- `fixer_node` 有重試邏輯，但缺少 ReviewerAgent 整合
- 節點介面穩定，適合 adapter 模式整合

#### RQ Worker 與金絲雀部署
**檔案**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`

**金絲雀邏輯** (lines 337-355)：
```python
use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)

if not use_langgraph and use_langgraph_percent > 0:
    import hashlib
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100
    use_langgraph = task_percent < use_langgraph_percent
    
    logger.info(
        f"Canary deployment: task_percent={task_percent}, threshold={use_langgraph_percent}, use_langgraph={use_langgraph}",
        extra={
            "operation": "canary_selection",
            "task_id": task_id,
            "task_percent": task_percent,
            "use_langgraph_percent": use_langgraph_percent,
            "use_langgraph": use_langgraph
        }
    )
```

**狀態**：
- ✅ 金絲雀邏輯完整實作（MD5 hash 路由，確定性分配）
- ✅ 7 個完整單元測試（`tests/test_worker.py:291-451`）
  - 0% 金絲雀測試
  - 100% 金絲雀測試
  - 5% 分佈測試（2-8 個任務預期）
  - 50% 邊界測試
  - 確定性測試（相同 task_id 總是相同路由）
  - Kill switch 測試（USE_LANGGRAPH=true 覆蓋百分比）
- ❌ 未啟用（`USE_LANGGRAPH_PERCENT=0`）

### 2. LLM 使用

#### FAQ Generator
**檔案**: `handoff/20250928/40_App/orchestrator/llm/faq_generator.py`

**模型配置** (line 58):
```python
def generate_faq_content(
    question: str,
    trace_id: str,
    repo: str = "RC918/morningai",
    model: str = "gpt-4-turbo-preview"  # ← 當前使用模型
) -> str:
```

**關鍵發現**：
- 使用 `gpt-4-turbo-preview` 模型
- 有 fallback 機制（LLM 失敗時使用模板）
- 有快取機制（`_faq_cache`）
- 可作為 planner_node LLM 整合的參考模式

### 3. 配置與測試

#### 環境配置
**檔案**: `config/env.schema.yaml` (1135 行)

**金絲雀相關配置** (lines 14, 112-115):
```yaml
notes: 'Added 51 missing variables found in codebase:
  - USE_LANGGRAPH, USE_LANGGRAPH_PERCENT (orchestrator control)
```

**測試驗證** (`common/config/test_settings.py:110-115`):
```python
def test_integer_fields_converted_correctly(self):
    """Integer fields should convert string values correctly"""
    with patch.dict(os.environ, {'USE_LANGGRAPH_PERCENT': '75'}):
        instance = Settings()
        assert instance.use_langgraph_percent == 75
        assert isinstance(instance.use_langgraph_percent, int)
```

**狀態**：
- ✅ 環境變數架構完整
- ✅ 整數轉換測試通過
- ❌ 缺少 `USE_LLM_PLANNER` 和 `USE_CODEGEN_WORKFLOW_PERCENT` 標誌

#### 部署配置
**檔案**: `render.yaml`

**Production 配置** (lines 48-49, 76-77):
```yaml
# Backend service (line 48)
- key: USE_LANGGRAPH
  value: false

# Worker service (line 76)
- key: ENVIRONMENT
  value: production
```

**狀態**：
- ✅ Production 環境配置完整
- ❌ 缺少 staging 環境配置
- ❌ 未設定 `USE_LANGGRAPH_PERCENT`

### 4. 指標系統

#### Agent Eval Metrics
**檔案**: `tools/agent_eval/metrics.py`

**當前指標**：
- `planner_accuracy` - 已定義但未實作
- `self_healing_rate` - 已定義但未實作
- 其他基礎指標已實作

**狀態**：
- ✅ 指標架構存在
- ❌ `planner_accuracy` 未實作（Phase 1 需要）
- ❌ Phase 2 指標未定義

### 5. 測試覆蓋率分析

#### Orchestrator 模組覆蓋率
**來源**: `handoff/20250928/40_App/orchestrator/coverage.json`

**總體覆蓋率**: 61% (1936/3190 行)

**低覆蓋率高風險檔案**：

| 檔案 | 覆蓋率 | 風險等級 | 優先級 |
|------|--------|----------|--------|
| `dev_agent_v2.py` | 0% (0/194) | 🔴 Critical | P0 |
| `governance/policy_guard.py` | 17% (23/139) | 🔴 High | P0 |
| `governance/violation_detector.py` | 19% (15/78) | 🔴 High | P1 |
| `memory/pgvector_store.py` | 23% (11/48) | 🟡 Medium | P1 |
| `governance/permission_checker.py` | 26% (12/47) | 🟡 Medium | P1 |
| `governance/reputation_engine.py` | 28% (57/204) | 🟡 Medium | P2 |
| `persistence/db_writer.py` | 32% (24/75) | 🟡 Medium | P2 |
| `utils/retry.py` | 41% (22/54) | 🟡 Medium | P2 |
| `utils/rate_limit.py` | 44% (15/34) | 🟡 Medium | P2 |

**高覆蓋率檔案（參考標準）**：
- ✅ `llm/faq_generator.py`: 100% (40/40)
- ✅ `tests/test_faq_generator.py`: 100% (187/187)
- ✅ `tests/test_graph.py`: 100% (215/215)
- ✅ `tests/test_langgraph_ci.py`: 100% (96/96)
- ✅ `tests/test_worker.py`: 96% (282/294)

**Phase 0 目標**：
- 當前：61% (orchestrator 模組)
- 目標：25-30% (全專案)
- 策略：優先測試高風險低覆蓋率模組

---

## 🔍 資源盤點

### 現有資產 (可直接使用)

#### ✅ 完整可用
1. **LangGraph Orchestrator** (422 行)
   - 5 節點工作流完整
   - 節點介面穩定
   - 適合 adapter 整合

2. **金絲雀部署系統**
   - Worker 路由邏輯 (lines 337-355)
   - 7 個完整單元測試
   - 環境變數支援

3. **LLM 整合模式**
   - FAQ Generator 作為參考
   - OpenAI client 封裝
   - Fallback 機制

4. **環境配置架構**
   - env.schema.yaml (1135 行)
   - Settings 類別與驗證
   - 單元測試覆蓋

5. **指標系統架構**
   - tools/agent_eval/metrics.py
   - tools/agent_eval/runner.py
   - Dataset 擴展 (10→50+)

#### ⚠️ 部分可用（需要增強）
1. **planner_node**
   - 靜態計畫存在
   - 需要 LLM 整合
   - 需要 ContextManager

2. **fixer_node**
   - 重試邏輯存在
   - 需要 ReviewerAgent 整合

3. **測試覆蓋率**
   - Orchestrator: 61%
   - 全專案: ~8%
   - 需要提升至 25-30%

### 缺失資源 (需要建立)

#### ❌ Phase 0 缺失
1. **測試覆蓋率**
   - 需要新增 17-22% 覆蓋率
   - 優先模組：governance, memory, persistence

#### ❌ Phase 1 缺失
1. **LLM Planner Adapter**
   - TaskClassifier 整合
   - ContextManager 整合
   - LLM 調用邏輯
   - 計畫驗證邏輯

2. **Feature Flags**
   - `USE_LLM_PLANNER` (boolean)
   - 環境變數定義
   - 單元測試

3. **Planner Accuracy Metric**
   - 指標實作
   - CI 整合
   - Dataset 標註

4. **Staging 金絲雀啟用**
   - `USE_LANGGRAPH_PERCENT=5`
   - Staging 環境配置

#### ❌ Phase 2 缺失
1. **Feature Flag**
   - `USE_CODEGEN_WORKFLOW_PERCENT` (integer)

2. **Integration Adapters**
   - executor_node 代碼生成整合
   - fixer_node ReviewerAgent 整合
   - finalizer_node 指標報告

3. **Phase 2 Metrics**
   - 代碼生成成功率
   - CI 通過率
   - Reviewer 採納率

### PR #1347 資源評估

#### 可salvage的組件 (2,572 行)

**✅ 可重用**：
1. **TaskClassifier** (`agents/dev_agent/workflows/task_classifier.py`, 240 行)
   - 任務分類邏輯完整
   - 可整合進 planner_node
   - 需要調整為 adapter 模式

2. **ReviewerAgent v1** (`agents/reviewer_agent/reviewer_agent.py`, 495 行)
   - Lint 檢查完整
   - A11y 檢查完整
   - 基礎安全檢查完整
   - 可整合進 fixer_node

3. **LLMTestGenerator** (`agents/dev_agent/testing/llm_test_generator.py`, 394 行)
   - GPT-4 測試生成邏輯
   - 可作為 Phase 2 測試生成基礎
   - 需要限制在穩定 fixtures 模組

4. **Generation Primitives** (從 CodeGenerationWorkflow 提取)
   - 代碼生成函式
   - 驗證邏輯
   - 應用邏輯

**❌ 需要廢棄**：
1. **CodeGenerationWorkflow** (593 行)
   - 建立平行編排系統
   - 違反整合原則
   - 不應作為獨立工作流

**Salvage 策略**：
1. 關閉 PR #1347（按用戶要求）
2. 提取可重用組件
3. 重構為 adapter 模式
4. 整合進 LangGraph 節點
5. 建立新的小型 PR 系列

---

## 📋 4 條路線整合分析

### 路線 1：成功指標 (Success Metrics)

**來源**: `Nov+18+2025+08-47-43+PM+Markdown+Content.md`

**階段性指標**：
- **Phase 0**: agent_eval CI 穩定，覆蓋率 25-30%，RLS 驗證通過，CI >90%
- **Phase 1**: LLM 準確率 ≥70%，金絲雀 5-10%，規劃 3-7 步 <30 秒，可用性 >99.5%
- **Phase 2**: 代碼生成 ≥60%，CI 通過 ≥80%，Reviewer 採納 ≥40%
- **Phase 3**: 任務分配 ≥95%，Agent 完成 ≥50%，協調開銷 <10%
- **Phase 4**: 失敗收集 ≥90%，自我修復 ≥50%，修復準確 ≥60%
- **Phase 5**: 訂閱完成 ≥80%，支付成功 ≥95%，流失 <10%/月
- **Phase 6**: 儀表板載入 <2 秒，資料新鮮 <5 分鐘，互動 ≥60%

**整合方式**: 作為每個 Phase 的驗收標準 (Acceptance Criteria)

### 路線 2：優化策略 (Optimization Strategy)

**來源**: `Nov+18+2025+08-47-26+PM+Markdown+Content.md` 等

**核心策略**：
1. **壓縮 Phase 0**: 5 天完成審計與增強
2. **利用現有資產**: 不重建，直接增強
3. **金絲雀部署**: 5%→10%→25%→50%→100%
4. **分階段風險控制**: 限制範圍，逐步擴展

**整合方式**: 作為執行策略和時程壓縮指導

### 路線 3：當前狀態 (Current State)

**來源**: 本次深度分析

**現狀**：
- Phase 0: 部分完成（金絲雀就緒，覆蓋率不足）
- Phase 1: 部分完成（基礎設施就緒，LLM 未整合）
- Phase 1.5: 完成但偏離路線圖
- Phase 2: 方法錯誤（平行系統）

**整合方式**: 作為 Gap Analysis 和優先級排序依據

### 路線 4：原始路線圖 (Original Roadmap)

**來源**: `MorningAI_Planning_Report_2025-11-17.md`

**階段劃分**：
- Phase 0 (5 天)
- Phase 1 (14 天)
- Phase 2 (14 天)
- Phase 3 (21 天)
- Phase 4 (21 天)
- Phase 5 (28+14 天)
- Phase 6 (平行)

**整合方式**: 作為基礎結構和時程框架

---

## 🎯 整合路線圖 (Integrated Roadmap)

### 整合原則

1. **結構**: 使用原始路線圖的 Phase 劃分
2. **驗收**: 使用成功指標作為每個 Phase 的驗收標準
3. **策略**: 應用優化策略壓縮時程和控制風險
4. **現實**: 基於當前狀態識別 Gap 和優先級

### Phase 0: 基線與安全 (2-3 天)

#### 目標
- 測試覆蓋率：8% → 25-30%
- agent_eval CI 穩定運行
- RLS 驗證腳本通過
- CI 通過率 >90%

#### 工作項目

**1. 測試覆蓋率提升** (2 天)
- **優先模組**（按風險排序）：
  1. `governance/policy_guard.py` (17% → 60%)
  2. `governance/violation_detector.py` (19% → 60%)
  3. `memory/pgvector_store.py` (23% → 60%)
  4. `persistence/db_writer.py` (32% → 60%)
  5. `utils/retry.py` (41% → 70%)
  6. `utils/rate_limit.py` (44% → 70%)

- **測試策略**：
  - 快速、確定性測試（無網路/LLM 調用）
  - 使用 mock 隔離依賴
  - 每個檔案新增 3-5 個測試
  - 覆蓋錯誤路徑和邊界情況

- **預期增加**：+17-22% 覆蓋率

**2. CI 軟閘門** (0.5 天)
- 新增覆蓋率閘門（初始 ≥20%）
- 本地通過後提升至 ≥25%
- 最終目標 ≥30%

**3. RLS 驗證** (0.5 天)
- 確認 RLS 腳本在 CI 通過
- Staging 驗證保持手動（需要憑證）

#### 交付物
- [ ] 6-8 個模組測試覆蓋率提升至 60-70%
- [ ] 全專案覆蓋率達 25-30%
- [ ] CI 軟閘門配置
- [ ] RLS 腳本 CI 通過

#### 驗收標準
- ✅ 測試覆蓋率 ≥25%
- ✅ agent_eval CI 穩定（多次運行綠燈）
- ✅ RLS 腳本通過
- ✅ CI 通過率 >90%

#### 風險與緩解
- **風險**: 測試編寫耗時超過預期
- **緩解**: 優先高風險模組，使用 mock 加速

---

### Phase 1: LLM Planner 與金絲雀 (3-5 天)

#### 目標
- LLM 規劃器準確率 ≥70%
- 金絲雀部署穩定，流量 5-10%
- 平均規劃步數 3-7
- 規劃生成時間 <30 秒
- 系統可用性 >99.5%

#### 工作項目

**1. Feature Flags** (0.5 天)
- **新增環境變數**：
  ```yaml
  USE_LLM_PLANNER:
    type: boolean
    required: false
    default: false
    description: Enable LLM-based dynamic planning in planner_node
    category: Feature Flags
  ```

- **單元測試** (`common/config/test_settings.py`):
  ```python
  def test_use_llm_planner_boolean_conversion(self):
      with patch.dict(os.environ, {'USE_LLM_PLANNER': 'true'}):
          instance = Settings()
          assert instance.use_llm_planner is True
  ```

**2. Planner Adapter 整合** (2-3 天)

**檔案**: `langgraph_orchestrator.py:57-92`

**整合架構**：
```python
def planner_node(state: AgentState) -> AgentState:
    """Planning node: Analyzes the goal and creates a plan"""
    goal = state["goal"]
    repo = state.get("repo", "RC918/morningai")
    trace_id = state.get("trace_id", "unknown")
    
    # Feature flag 控制
    if settings.use_llm_planner:
        try:
            # 1. 任務分類
            from agents.dev_agent.workflows.task_classifier import classify_task
            task_type = classify_task(goal)
            
            # 2. 代碼上下文
            from context_manager import get_code_context
            code_context = get_code_context(repo, goal, max_files=5)
            
            # 3. LLM 規劃
            plan = generate_llm_plan(
                goal=goal,
                task_type=task_type,
                code_context=code_context,
                trace_id=trace_id
            )
            
            # 4. 驗證
            if validate_plan(plan):
                state["plan"] = plan
                state["planner_type"] = "llm"
                return state
        except Exception as e:
            logger.warning(f"LLM planning failed, falling back to static: {e}")
    
    # Fallback: 靜態計畫
    plan = get_static_plan(task_type if 'task_type' in locals() else "default")
    state["plan"] = plan
    state["planner_type"] = "static"
    return state

def generate_llm_plan(goal, task_type, code_context, trace_id):
    """Generate dynamic plan using GPT-4"""
    client = _get_openai_client()
    
    system_prompt = """你是資深軟體工程師，生成 3-7 步可執行計畫。
    
    輸出格式（嚴格 JSON）：
    [
      {"step": "步驟描述", "rationale": "原因", "risk": "low|medium|high"},
      ...
    ]
    """
    
    user_prompt = f"""
    **目標**: {goal}
    **任務類型**: {task_type}
    **代碼上下文**:
    {code_context[:1000]}  # 截斷
    
    生成 3-7 步計畫。
    """
    
    start_time = time.time()
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000,
        timeout=25  # 留 5 秒緩衝
    )
    
    planning_time_ms = (time.time() - start_time) * 1000
    
    # 記錄指標
    from tools.agent_eval.metrics import record_planning_time
    record_planning_time(trace_id, planning_time_ms)
    
    # 解析 JSON
    plan = json.loads(response.choices[0].message.content)
    
    return plan

def validate_plan(plan):
    """Validate plan structure and constraints"""
    if not isinstance(plan, list):
        return False
    if not (3 <= len(plan) <= 7):
        return False
    for step in plan:
        if not all(k in step for k in ["step", "rationale", "risk"]):
            return False
    return True
```

**3. ContextManager 實作** (1 天)
- 提取相關檔案（top-K 相似度）
- 提取函式簽名
- 限制大小（<2000 tokens）

**4. Planner Accuracy Metric** (1 天)

**檔案**: `tools/agent_eval/metrics.py`

```python
def calculate_planner_accuracy(trace_id: str, plan: list, expected_steps: list) -> float:
    """Calculate planner accuracy against expected steps"""
    # 實作評分邏輯
    # 比對計畫步驟與預期步驟
    # 返回準確率 (0.0-1.0)
    pass

def record_planner_accuracy(trace_id: str, accuracy: float):
    """Record planner accuracy metric"""
    # 記錄到 agent_eval 系統
    pass
```

**5. CI 整合** (0.5 天)
- 新增 CI job 運行 `tools/agent_eval/runner.py`
- 初始為軟閘門（報告模式）
- 穩定後轉為硬閘門（≥70%）

**6. 金絲雀啟用** (0.5 天)

**Staging 配置** (`render.yaml` 或 Render Dashboard):
```yaml
- key: USE_LANGGRAPH_PERCENT
  value: "5"
- key: USE_LANGGRAPH
  value: "false"  # 讓百分比邏輯生效
```

**監控**：
- 觀察 24-48 小時
- 檢查 `canary_selection` 日誌
- 驗證確定性路由
- 監控錯誤率無顯著增長

#### 交付物
- [ ] `USE_LLM_PLANNER` feature flag + 測試
- [ ] Planner adapter 整合進 `planner_node`
- [ ] ContextManager 實作
- [ ] Planner accuracy metric 實作
- [ ] CI 軟閘門配置
- [ ] Staging 金絲雀啟用（5%）

#### 驗收標準
- ✅ LLM 規劃器準確率 ≥70%（CI dataset）
- ✅ 金絲雀穩定運行 5-10%
- ✅ 平均規劃步數 3-7
- ✅ 規劃生成時間 <30 秒
- ✅ 系統可用性 >99.5%（無錯誤率增長）

#### 風險與緩解
- **風險**: LLM 調用超時或失敗
- **緩解**: Fallback 靜態計畫，超時設定 25 秒
- **風險**: 金絲雀導致錯誤率增長
- **緩解**: Kill switch (`USE_LANGGRAPH=true`)，快速回滾

---

### Phase 2: 代碼生成品質（整合方法）(5-7 天)

#### 目標
- 代碼生成成功率 ≥60%
- CI 通過率 ≥80%
- Reviewer_agent 建議採納率 ≥40%
- 無安全漏洞
- 測試覆蓋率提升
- 支援 3-5 個任務類型

#### 工作項目

**1. PR #1347 Salvage Plan** (1 天)

**關閉 PR #1347**：
- 記錄關閉原因：「建立平行系統而非整合 LangGraph」
- 建立 salvage 文件記錄可重用組件

**可重用組件**：
1. **TaskClassifier** (240 行)
   - 提取到 `langgraph_orchestrator.py` 或獨立模組
   - 重構為 adapter 函式
   
2. **ReviewerAgent v1** (495 行)
   - 整合進 `fixer_node`
   - 保持輕量級（lint + 基礎安全）
   
3. **LLMTestGenerator** (394 行)
   - 限制在穩定 fixtures 模組
   - 整合進 executor_node
   
4. **Generation Primitives**
   - 從 CodeGenerationWorkflow 提取函式
   - 作為 executor_node 可調用函式

**廢棄組件**：
- CodeGenerationWorkflow (593 行) - 平行編排系統

**2. Feature Flag** (0.5 天)

```yaml
USE_CODEGEN_WORKFLOW_PERCENT:
  type: integer
  required: false
  default: 0
  description: Percentage of tasks to use code generation workflow (sub-canary)
  category: Feature Flags
```

**3. Executor Node 整合** (2 天)

**檔案**: `langgraph_orchestrator.py:94-144`

```python
def executor_node(state: AgentState) -> AgentState:
    """Executor node: Executes the current step in the plan"""
    goal = state["goal"]
    repo = state["repo"]
    trace_id = state.get("trace_id", "unknown")
    
    # Sub-canary for code generation
    use_codegen = should_use_codegen(trace_id, state)
    
    if use_codegen:
        try:
            # 使用代碼生成 primitives
            result = execute_with_codegen(goal, repo, trace_id, state)
            state["execution_result"] = result
            state["executor_type"] = "codegen"
            return state
        except Exception as e:
            logger.warning(f"Codegen execution failed, falling back: {e}")
    
    # Fallback: 原有執行邏輯
    from graph import execute
    pr_url, ci_state, trace_id = execute(goal, repo, trace_id=trace_id)
    state["pr_url"] = pr_url
    state["ci_state"] = ci_state
    state["executor_type"] = "legacy"
    return state
```

**4. Fixer Node 整合** (1-2 天)

**檔案**: `langgraph_orchestrator.py:199-226`

```python
def fixer_node(state: AgentState) -> AgentState:
    """Fixer node: Attempts to fix CI failures"""
    retry_count = state.get("retry_count", 0)
    
    if retry_count >= 3:
        state["error"] = "Max retries exceeded"
        return state
    
    # 整合 ReviewerAgent v1
    from agents.reviewer_agent.reviewer_agent import ReviewerAgent
    reviewer = ReviewerAgent(lightweight=True)  # lint + 基礎安全
    
    # 分析失敗原因
    ci_logs = state.get("ci_logs", "")
    suggestions = reviewer.analyze_failure(ci_logs)
    
    # 應用修復建議
    if suggestions:
        state["fix_suggestions"] = suggestions
        # 記錄採納率指標
        from tools.agent_eval.metrics import record_reviewer_adoption
        record_reviewer_adoption(state["trace_id"], suggestions)
    
    state["retry_count"] = retry_count + 1
    return state
```

**5. Phase 2 Metrics** (1 天)

**檔案**: `tools/agent_eval/metrics.py`

```python
def record_codegen_success(trace_id: str, success: bool):
    """Record code generation success metric"""
    pass

def record_ci_pass_rate(trace_id: str, passed: bool):
    """Record CI pass rate metric"""
    pass

def record_reviewer_adoption(trace_id: str, suggestions: list):
    """Record reviewer suggestion adoption rate"""
    pass
```

**6. 任務類型限制** (0.5 天)

**支援的 3-5 個任務類型**：
1. 小型 bug 修復（單一檔案，<50 行變更）
2. 為現有函式新增單元測試
3. 小型重構（不改變 API）
4. 文檔更新
5. 配置調整

**7. 測試生成限制** (0.5 天)

**穩定 fixtures 模組**（需要用戶確認）：
- `tests/fixtures/`
- `handoff/20250928/40_App/api-backend/tests/fixtures/`
- 其他穩定測試模組

**8. Sub-Canary 啟用** (0.5 天)

**Staging 配置**：
```yaml
- key: USE_CODEGEN_WORKFLOW_PERCENT
  value: "5"
```

**前提條件**：
- Phase 1 金絲雀穩定運行
- 觀察 24-48 小時

#### 交付物
- [ ] PR #1347 關閉 + salvage 文件
- [ ] `USE_CODEGEN_WORKFLOW_PERCENT` feature flag + 測試
- [ ] Executor node 代碼生成整合
- [ ] Fixer node ReviewerAgent 整合
- [ ] Phase 2 metrics 實作
- [ ] 任務類型限制實作
- [ ] 測試生成限制實作
- [ ] Sub-canary 啟用（5%）

#### 驗收標準
- ✅ 代碼生成成功率 ≥60%
- ✅ CI 通過率 ≥80%
- ✅ Reviewer 採納率 ≥40%
- ✅ 無安全漏洞
- ✅ 測試覆蓋率提升（5-10%）

#### 風險與緩解
- **風險**: 代碼生成品質不穩定
- **緩解**: 限制任務類型，嚴格驗證
- **風險**: ReviewerAgent 拖慢 CI
- **緩解**: 保持輕量級（僅 lint + 基礎安全）

---

### Phase 3-6: 高階功能（按原定路線圖）

#### Phase 3: Meta+Dev 協調 (21 天)
- 任務分配成功率 ≥95%
- Agent 任務完成率 ≥50%
- 協調開銷 <10%

#### Phase 4: 失敗知識庫 (21 天)
- 失敗案例收集率 ≥90%
- 自我修復率 ≥50%
- 修復建議準確率 ≥60%

#### Phase 5: Stripe 整合 (28+14 天)
- 訂閱流程完成率 ≥80%
- 支付成功率 ≥95%
- 客戶流失率 <10%/月

#### Phase 6: 儀表板整合 (平行)
- 儀表板載入時間 <2 秒
- 資料新鮮度 <5 分鐘
- 使用者互動率 ≥60%

---

## 📅 執行時程與里程碑

### 總時程
- **Phase 0**: 2-3 天（11/19-11/21）
- **Phase 1**: 3-5 天（11/22-11/26）
- **Phase 2**: 5-7 天（11/27-12/03）
- **Phase 3**: 21 天（12/04-12/24）
- **Phase 4**: 21 天（12/25-01/14）
- **Phase 5**: 42 天（01/15-02/25）
- **Phase 6**: 平行執行

### 每日里程碑

#### Phase 0 (Day 1-3)
- **Day 1**: 
  - ✅ 運行覆蓋率報告
  - ✅ 識別優先模組
  - ✅ 開始測試編寫（governance 模組）
  
- **Day 2**:
  - ✅ 完成 governance 模組測試
  - ✅ 開始 memory/persistence 模組測試
  - ✅ 覆蓋率達 20%
  
- **Day 3**:
  - ✅ 完成所有優先模組測試
  - ✅ 覆蓋率達 25-30%
  - ✅ CI 軟閘門配置
  - ✅ RLS 驗證通過

#### Phase 1 (Day 4-8)
- **Day 4**:
  - ✅ Feature flag 實作 + 測試
  - ✅ ContextManager 設計
  
- **Day 5-6**:
  - ✅ Planner adapter 實作
  - ✅ LLM 整合 + 驗證邏輯
  
- **Day 7**:
  - ✅ Planner accuracy metric 實作
  - ✅ CI 軟閘門配置
  
- **Day 8**:
  - ✅ Staging 金絲雀啟用（5%）
  - ✅ 監控 24 小時

#### Phase 2 (Day 9-15)
- **Day 9**:
  - ✅ 關閉 PR #1347
  - ✅ Salvage plan 文件
  - ✅ Feature flag 實作
  
- **Day 10-11**:
  - ✅ Executor node 整合
  - ✅ Generation primitives 提取
  
- **Day 12-13**:
  - ✅ Fixer node 整合
  - ✅ ReviewerAgent 整合
  
- **Day 14**:
  - ✅ Phase 2 metrics 實作
  - ✅ 任務類型限制
  
- **Day 15**:
  - ✅ Sub-canary 啟用（5%）
  - ✅ 監控 24 小時

### 每週檢查點

#### Week 1 (Phase 0 + Phase 1 開始)
- **目標**: Phase 0 完成，Phase 1 進行中
- **檢查項目**:
  - 測試覆蓋率 ≥25%
  - Feature flags 實作完成
  - Planner adapter 設計完成

#### Week 2 (Phase 1 完成 + Phase 2 開始)
- **目標**: Phase 1 完成，Phase 2 進行中
- **檢查項目**:
  - 金絲雀穩定運行 5%
  - Planner accuracy ≥70%
  - PR #1347 關閉 + salvage 完成

#### Week 3 (Phase 2 完成)
- **目標**: Phase 2 完成
- **檢查項目**:
  - 代碼生成成功率 ≥60%
  - CI 通過率 ≥80%
  - Reviewer 採納率 ≥40%

---

## 🚨 風險管理

### 高風險項目

#### 1. 測試覆蓋率提升耗時 (Phase 0)
- **風險等級**: 🟡 Medium
- **影響**: 延遲 Phase 1 開始
- **緩解**:
  - 優先高風險模組
  - 使用 mock 加速測試編寫
  - 並行編寫測試（多個模組同時）

#### 2. LLM 規劃器準確率不達標 (Phase 1)
- **風險等級**: 🔴 High
- **影響**: 無法啟用金絲雀
- **緩解**:
  - Fallback 靜態計畫
  - 調整 prompt 和溫度參數
  - 使用更強大的模型（gpt-4o）

#### 3. 金絲雀導致錯誤率增長 (Phase 1)
- **風險等級**: 🔴 High
- **影響**: 需要回滾，延遲進度
- **緩解**:
  - Kill switch (`USE_LANGGRAPH=true`)
  - 詳細日誌監控
  - 快速回滾機制

#### 4. 代碼生成品質不穩定 (Phase 2)
- **風險等級**: 🟡 Medium
- **影響**: 無法達成成功率目標
- **緩解**:
  - 限制任務類型（3-5 個）
  - 嚴格驗證邏輯
  - 人工審查機制

### 回滾計畫

#### Phase 1 回滾
**觸發條件**：
- 錯誤率增長 >10%
- 系統可用性 <99%
- 規劃時間 >30 秒（持續）

**回滾步驟**：
1. 設定 `USE_LANGGRAPH=false`（立即生效）
2. 或設定 `USE_LANGGRAPH_PERCENT=0`
3. 監控錯誤率恢復
4. 分析日誌找出根因
5. 修復後重新啟用

#### Phase 2 回滾
**觸發條件**：
- 代碼生成成功率 <40%
- CI 通過率 <60%
- 安全漏洞檢測

**回滾步驟**：
1. 設定 `USE_CODEGEN_WORKFLOW_PERCENT=0`
2. 監控指標恢復
3. 分析失敗案例
4. 修復後重新啟用

---

## 📊 監控與報告

### 日常監控

#### 每日檢查項目
1. **CI 狀態**
   - 通過率 >90%
   - 失敗原因分析
   
2. **錯誤率**
   - Sentry 錯誤追蹤
   - 錯誤率無顯著增長
   
3. **效能指標**
   - 規劃時間 <30 秒
   - 系統可用性 >99.5%

#### 每週檢查項目
1. **Phase 進度**
   - 里程碑達成情況
   - 延遲風險評估
   
2. **指標趨勢**
   - 覆蓋率趨勢
   - 準確率趨勢
   - 成功率趨勢

### 報告格式

#### 週報
```markdown
# MorningAI 週報 (Week X)

## 完成項目
- [ ] 項目 1
- [ ] 項目 2

## 指標
- 測試覆蓋率: X%
- Planner 準確率: X%
- 代碼生成成功率: X%

## 風險
- 風險 1: 描述 + 緩解措施
- 風險 2: 描述 + 緩解措施

## 下週計畫
- 計畫 1
- 計畫 2
```

#### 月報
```markdown
# MorningAI 月報 (Month X)

## Phase 完成度
- Phase 0: ✅ 完成
- Phase 1: 🔄 進行中
- Phase 2: ⏳ 待開始

## 進度分析
- 按時完成: X 個 Phase
- 延遲: X 個 Phase
- 原因分析

## 預算與資源
- LLM API 成本: $X
- 開發時間: X 天
- 資源使用率: X%

## 效能分析
- 系統可用性: X%
- 平均響應時間: X 秒
- 錯誤率: X%
```

---

## 🎯 成功標準總結

### Phase 0-2 成功標準

| Phase | 指標 | 目標 | 測量方式 |
|-------|------|------|----------|
| **Phase 0** | 測試覆蓋率 | ≥25-30% | pytest --cov |
| | CI 通過率 | >90% | GitHub Actions |
| | RLS 驗證 | 通過 | CI job |
| **Phase 1** | Planner 準確率 | ≥70% | agent_eval CI |
| | 金絲雀流量 | 5-10% | Worker logs |
| | 規劃步數 | 3-7 | LLM output |
| | 規劃時間 | <30s | Timer |
| | 系統可用性 | >99.5% | Sentry |
| **Phase 2** | 代碼生成成功率 | ≥60% | agent_eval |
| | CI 通過率 | ≥80% | GitHub Actions |
| | Reviewer 採納率 | ≥40% | Metrics |
| | 安全漏洞 | 0 | ReviewerAgent |
| | 測試覆蓋率提升 | 5-10% | pytest --cov |

### 整體專案成功標準

#### 技術成熟度
- ✅ 測試覆蓋率 ≥74%（最終目標）
- ✅ CI 通過率 ≥95%
- ✅ 代碼審查 100%
- ✅ 系統可用性 ≥99.5%
- ✅ 故障恢復時間 <30 分鐘
- ✅ 錯誤率 <0.1%

#### 商業成功
- ✅ 完整 SaaS 功能
- ✅ 多租戶支援
- ✅ 訂閱與計費系統
- ✅ 完整監控治理
- ✅ 安全合規

---

## 📝 下一步行動

### 立即行動（今天）

1. **確認執行方向**
   - [ ] 用戶確認整合路線圖
   - [ ] 確認 staging 環境配置位置
   - [ ] 確認穩定 fixtures 模組定義
   - [ ] 確認 3-5 個任務類型清單

2. **Phase 0 啟動**
   - [ ] 運行完整覆蓋率報告
   - [ ] 建立優先模組清單
   - [ ] 開始測試編寫

3. **PR #1347 處理**
   - [ ] 關閉 PR #1347
   - [ ] 建立 salvage plan 文件
   - [ ] 記錄可重用組件

### 本週行動

1. **Phase 0 完成**
   - [ ] 測試覆蓋率達 25-30%
   - [ ] CI 軟閘門配置
   - [ ] RLS 驗證通過

2. **Phase 1 準備**
   - [ ] Feature flag 設計
   - [ ] Planner adapter 架構設計
   - [ ] ContextManager 設計

---

## 📚 附錄

### A. 檔案清單

#### 核心檔案
- `langgraph_orchestrator.py` (422 行) - LangGraph 5 節點工作流
- `redis_queue/worker.py` (667 行) - RQ Worker 與金絲雀邏輯
- `llm/faq_generator.py` (294 行) - LLM 整合參考
- `tools/agent_eval/metrics.py` - 指標系統
- `config/env.schema.yaml` (1135 行) - 環境配置

#### 測試檔案
- `tests/test_worker.py` (466 行) - Worker 與金絲雀測試
- `tests/test_faq_generator.py` (187 行) - LLM 測試參考
- `common/config/test_settings.py` (377 行) - 配置測試

#### PR #1347 檔案
- `agents/dev_agent/workflows/task_classifier.py` (240 行) - 可重用
- `agents/reviewer_agent/reviewer_agent.py` (495 行) - 可重用
- `agents/dev_agent/testing/llm_test_generator.py` (394 行) - 可重用
- `agents/dev_agent/workflows/code_generation_workflow.py` (593 行) - 廢棄

### B. 參考文件
- 原始路線圖: `MorningAI_Planning_Report_2025-11-17.md`
- 成功指標: `Nov+18+2025+08-47-43+PM+Markdown+Content.md`
- 優化策略: `Nov+18+2025+08-47-26+PM+Markdown+Content.md`

### C. 聯絡資訊
- GitHub Repo: https://github.com/RC918/morningai
- PR #1347: https://github.com/RC918/morningai/pull/1347
- Devin Run: https://app.devin.ai/sessions/46a89ed46ea745d5bd53bf07d7b74d44

---

**報告結束**

此報告提供完整的專案狀態分析、架構評估、資源盤點與整合路線圖。建議立即開始執行 Phase 0，並按照整合路線圖逐步完成 Phase 1-6。
