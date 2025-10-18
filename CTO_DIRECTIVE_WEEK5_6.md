# CTO 技術指令：Week 5-6 Knowledge Graph & Bug Fix Pilot

**發送對象**: Backend Engineer + AI Engineer  
**優先級**: P0 (Critical - Phase 1 核心里程碑)  
**預計工時**: 80 小時（2 週）  
**截止日期**: 2025-11-01

---

## 📋 背景與目標

根據我們的技術戰略規劃，Phase 1 的核心使命是**使 Dev_Agent 達到與 Devin AI 相同水平的工作能力與智能**。

Week 4 已完成 Session State 管理和 OODA 循環，Week 5-6 是 Phase 1 的**最後關鍵階段**，需實現以下核心能力：

### 戰略目標
1. **代碼庫理解能力** - 使 Agent 能理解代碼結構、依賴關係
2. **學習能力** - 從過去的修復中學習，不斷改進
3. **自動修復能力** - 完整的 Issue → PR 自動化工作流
4. **與 Devin AI 對齊度達到 95%+**

---

## 🎯 技術要求清單

### Part 1: Knowledge Graph 實現 (Week 5, 40 小時)

#### 1.1 PostgreSQL + pgvector 整合 ⭐⭐⭐
**負責人**: Backend Engineer  
**優先級**: P0

**任務**:
- [ ] 在 Supabase 安裝 pgvector 擴展
- [ ] 執行 migration script: `agents/dev_agent/migrations/001_knowledge_graph_schema.sql`
- [ ] 驗證 4 個新表創建成功：
  - `code_entities`
  - `entity_relationships`
  - `learned_patterns`
  - `bug_fix_history`
- [ ] 驗證 vector index 正常工作
- [ ] 配置 database connection pooling（避免連接耗盡）

**驗收標準**:
```sql
-- 檢查 pgvector 安裝
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 檢查表創建
\dt

-- 檢查索引
\di

-- 測試 vector 查詢
SELECT embedding <=> '[0,0,0,...]'::vector FROM code_entities LIMIT 1;
```

**風險提示**:
- ⚠️ pgvector 需要 PostgreSQL 擴展權限
- ⚠️ IVFFlat index 創建可能需要幾分鐘（大型表）
- ⚠️ 需確認 Supabase tier 支持 pgvector

---

#### 1.2 Knowledge Graph Manager 實現 ⭐⭐⭐
**負責人**: Backend Engineer  
**優先級**: P0

**參考實現**: 我已提供初步實現在 PR #291，請以此為基礎進行完善

**必須實現的功能**:
```python
class KnowledgeGraphManager:
    def initialize_schema()  # ✅ 已實現
    def add_entity()  # ✅ 已實現
    def add_relationship()  # ✅ 已實現
    def semantic_search()  # ✅ 已實現（需測試）
    def find_related_entities()  # ✅ 已實現（需測試）
    def get_session_stats()  # ✅ 已實現
```

**需要完善的部分**:
- [ ] 添加 connection pooling（使用 psycopg2.pool）
- [ ] 添加 OpenAI API rate limiting（避免超限）
- [ ] 添加 embedding cache（Redis）減少 API 調用
- [ ] 添加錯誤重試機制（網絡問題、API timeout）
- [ ] 添加成本追蹤（記錄 API 調用次數）

**驗收標準**:
```python
# 測試腳本
kg = KnowledgeGraphManager()
kg.initialize_schema()

# 測試添加實體
entity_id = kg.add_entity(
    session_id="test",
    entity_type="function",
    entity_name="test_func",
    file_path="/test.py",
    line_start=1,
    line_end=5,
    source_code="def test_func(): pass"
)

# 測試語義搜索
results = kg.semantic_search("authentication", top_k=5)
assert len(results) > 0
assert 'similarity' in results[0]

print("✅ Knowledge Graph 測試通過")
```

---

#### 1.3 Code Indexer 實現 ⭐⭐
**負責人**: Backend Engineer + AI Engineer  
**優先級**: P0

**參考實現**: PR #291 中的 `code_indexer.py`

**必須實現的功能**:
```python
class CodeIndexer:
    def scan_directory()  # ✅ 已實現
    def index_file()  # ✅ 已實現
    def index_python_file()  # ✅ 已實現（AST parsing）
```

**需要完善的部分**:
- [ ] 添加並發處理（使用 asyncio 或 ThreadPoolExecutor）
- [ ] 添加進度追蹤（顯示索引進度）
- [ ] 添加增量索引（只索引變更的文件）
- [ ] 優化 AST 解析（捕獲所有異常，記錄失敗文件）
- [ ] 添加 file hash 檢查（避免重複索引）

**性能要求**:
- 10K 行代碼索引時間 < 5 分鐘
- 支持至少 1000 個文件
- 記憶體佔用 < 2GB

**驗收標準**:
```python
indexer = CodeIndexer(kg)

# 測試索引小型項目
stats = indexer.scan_directory(
    directory="/workspace/test_project",
    session_id="test"
)

assert stats['files_indexed'] > 0
assert stats['entities_created'] > 0
assert len(stats['errors']) == 0

print(f"✅ 索引了 {stats['files_indexed']} 個文件")
print(f"✅ 創建了 {stats['entities_created']} 個實體")
```

---

#### 1.4 Pattern Learner 實現 ⭐⭐
**負責人**: AI Engineer  
**優先級**: P1

**參考實現**: PR #291 中的 `pattern_learner.py`

**必須實現的功能**:
```python
class PatternLearner:
    def learn_bug_pattern()  # ✅ 已實現
    def learn_fix_pattern()  # ✅ 已實現
    def get_similar_bug_patterns()  # ✅ 已實現
    def get_similar_fix_patterns()  # ✅ 已實現
    def record_bug_fix()  # ✅ 已實現
```

**需要完善的部分**:
- [ ] 改進相似度匹配算法（目前只是簡單的字符串匹配）
- [ ] 添加模式推薦評分機制
- [ ] 添加模式過期機制（老舊模式降權）
- [ ] 添加模式分類統計（按 bug_type 分組）

**驗收標準**:
```python
learner = PatternLearner(kg)

# 學習 bug pattern
pattern_id = learner.learn_bug_pattern(
    bug_description="NoneType error",
    root_cause="Missing null check",
    affected_code="user.name",
    bug_type="type"
)

# 查找相似 pattern
patterns = learner.get_similar_bug_patterns(
    bug_description="AttributeError",
    bug_type="type"
)

assert len(patterns) > 0
print("✅ Pattern Learning 測試通過")
```

---

### Part 2: Bug Fix Workflow 實現 (Week 6, 40 小時)

#### 2.1 LangGraph Workflow 架構 ⭐⭐⭐
**負責人**: AI Engineer  
**優先級**: P0

**參考實現**: PR #291 中的 `bug_fix_workflow.py`

**關鍵改進需求**:
- [ ] **添加最大重試次數**（防止無限循環）
  ```python
  max_retries = 3
  retry_count = state.get('retry_count', 0)
  if retry_count >= max_retries:
      return "handle_error"
  ```

- [ ] **改進錯誤處理**（每個節點都要 try-catch）
  ```python
  async def parse_issue(self, state):
      try:
          # ... existing code
      except Exception as e:
          state['error_message'] = str(e)
          return state
  ```

- [ ] **添加超時控制**（防止單個階段卡住）
  ```python
  import asyncio
  result = await asyncio.wait_for(
      self.some_long_operation(),
      timeout=300  # 5 minutes
  )
  ```

- [ ] **改進 state 轉換邏輯**
  - `check_reproduction`: 明確 `reproduced=True` 才進入下一步
  - `check_approval`: 處理 `pending` 狀態（設置默認超時）

**驗收標準**:
- [ ] 可以處理完整的 bug fix 流程（mock 環境）
- [ ] 異常不會導致 workflow 崩潰
- [ ] 有明確的錯誤日誌和狀態追蹤

---

#### 2.2 工具介面整合 ⭐⭐⭐
**負責人**: Backend Engineer  
**優先級**: P0 (CRITICAL)

**問題**: Workflow 假設 dev_agent 有以下工具，需驗證介面是否存在且相容：

```python
# 需要驗證的工具介面
dev_agent.fs_tool.read_file(file_path)
dev_agent.fs_tool.write_file(file_path, content)
dev_agent.git_tool.create_branch(branch_name)
dev_agent.git_tool.commit(message)
dev_agent.git_tool.create_pr(title, body, base, head)
dev_agent.test_tool.run_tests(test_pattern)
dev_agent.hitl_client.request_approval(message, timeout)
dev_agent.llm.generate(prompt)
```

**任務**:
- [ ] 檢查 `agents/dev_agent/tools/` 下的工具類
- [ ] 驗證方法簽名與返回值格式
- [ ] 如果不存在，需要實現這些工具（或調整 workflow）
- [ ] 創建 adapter layer 處理介面不一致

**驗收標準**:
```python
# 測試所有工具介面
from agents.dev_agent.tools import get_filesystem_tool, get_git_tool

fs_tool = get_filesystem_tool('http://localhost:8080')
result = await fs_tool.write_file('/workspace/test.py', 'print("hello")')
assert result['success'] == True

git_tool = get_git_tool('http://localhost:8080')
result = await git_tool.create_branch('test-branch')
assert result['success'] == True

print("✅ 所有工具介面測試通過")
```

---

#### 2.3 HITL 整合 (Human-in-the-Loop) ⭐⭐
**負責人**: Backend Engineer  
**優先級**: P1

**需求**: 整合 Telegram Bot 用於審批流程

**任務**:
- [ ] 創建 `agents/dev_agent/hitl/telegram_client.py`
- [ ] 實現 `request_approval(message, timeout)` 方法
- [ ] 支持 3 種反應：✅ approve, ❌ reject, 🔄 modify
- [ ] 實現超時機制（預設 1 小時後自動 approve）
- [ ] 記錄所有審批決策到數據庫

**驗收標準**:
```python
hitl_client = TelegramClient(bot_token=TELEGRAM_BOT_TOKEN)

result = await hitl_client.request_approval(
    message="Bug fix ready for review",
    timeout_seconds=3600
)

assert result['status'] in ['approved', 'rejected', 'modify']
print(f"✅ HITL 測試通過，狀態: {result['status']}")
```

---

#### 2.4 End-to-End 測試 ⭐⭐⭐
**負責人**: QA + Backend Engineer  
**優先級**: P0

**任務**: 創建至少 5 個真實 bug 測試案例

**測試案例範例**:
```python
# Test Case 1: 語法錯誤
test_cases = [
    {
        "issue": {
            "number": 1,
            "title": "SyntaxError in main.py",
            "body": "Missing closing parenthesis on line 42"
        },
        "expected_fix": "Add closing parenthesis",
        "expected_success": True
    },
    # ... 更多測試案例
]

# 執行測試
for test in test_cases:
    result = await workflow.execute(test['issue'])
    assert result['approval_status'] == 'approved'
    assert result['pr_info']['created'] == True
```

**驗收標準**:
- [ ] 至少 5 個測試案例（涵蓋不同 bug 類型）
- [ ] 成功率 ≥ 60%（Week 6 結束時）
- [ ] 所有測試有詳細日誌
- [ ] 失敗案例有根因分析

---

## 🚨 CTO 關注的關鍵風險

### 風險 1: OpenAI API 成本失控 ⚠️ HIGH
**問題**: 大型代碼庫可能產生大量 API 調用

**緩解措施**（必須實現）:
- [ ] 添加 API 調用計數器
- [ ] 設置每日調用上限（例如 1000 次）
- [ ] 實現 embedding cache（Redis）
- [ ] 添加成本預估功能（索引前顯示預估費用）

**驗收**:
```python
# 顯示成本統計
stats = kg.get_cost_stats()
print(f"今日 API 調用: {stats['calls_today']}")
print(f"預估費用: ${stats['estimated_cost']:.2f}")
```

---

### 風險 2: 工具介面不相容 ⚠️ CRITICAL
**問題**: Workflow 假設的工具介面可能不存在

**緩解措施**（必須在 Week 5 完成）:
- [ ] Week 5 Day 1: 驗證所有工具介面
- [ ] 如介面不存在，立即創建或調整 workflow
- [ ] 創建 integration test 驗證工具鏈

---

### 風險 3: 數據庫性能瓶頸 ⚠️ MEDIUM
**問題**: pgvector 查詢可能較慢

**緩解措施**:
- [ ] 使用 IVFFlat index（已在 migration 中）
- [ ] 限制每次查詢的 top_k（≤ 20）
- [ ] 添加查詢時間監控（> 1 秒告警）
- [ ] 考慮 Redis cache 熱門查詢

---

## 📊 驗收標準（CTO Sign-off）

### Phase 1: 基礎功能（Week 5 結束）
- [ ] PostgreSQL + pgvector 安裝成功
- [ ] 4 個表創建成功，索引正常
- [ ] Knowledge Graph 可以索引 1000 行代碼
- [ ] 語義搜索返回相關結果
- [ ] 所有 unit tests 通過

### Phase 2: 工作流整合（Week 6 中期）
- [ ] 工具介面驗證完成
- [ ] Bug Fix Workflow 可以執行（mock 環境）
- [ ] HITL 整合完成（Telegram）
- [ ] 至少 3 個測試案例通過

### Phase 3: 完整驗收（Week 6 結束）
- [ ] E2E 測試 ≥ 5 個案例
- [ ] Bug 修復成功率 ≥ 60%
- [ ] 代碼庫索引 < 5 分鐘（10K 行）
- [ ] 語義搜索 < 500ms
- [ ] API 成本控制在 $5/day 以下
- [ ] 所有文檔完整（README、API docs）

### Phase 4: Production Ready（可選，Week 7）
- [ ] 成功率 ≥ 85%
- [ ] 在 staging 環境運行 1 週無重大問題
- [ ] 監控和告警配置完成
- [ ] Rollback 手冊完成

---

## 📅 時間表與里程碑

### Week 5（2025-10-21 - 2025-10-27）

**Day 1-2**: Database & Knowledge Graph
- 安裝 pgvector
- 執行 migration
- 實現 KnowledgeGraphManager（基於 PR #291）
- 驗收：可以添加實體並搜索

**Day 3-4**: Code Indexer
- 實現 CodeIndexer（基於 PR #291）
- 添加並發處理
- 測試索引小型項目
- 驗收：可以索引 1000 行代碼

**Day 5**: Pattern Learner + 整合測試
- 實現 PatternLearner
- 整合測試 Knowledge Graph 全功能
- 驗收：Week 5 Sign-off

---

### Week 6（2025-10-28 - 2025-11-03）

**Day 1-2**: 工具介面 & Workflow 架構
- 驗證所有工具介面
- 實現 BugFixWorkflow（基於 PR #291）
- 添加錯誤處理和重試邏輯
- 驗收：Workflow 可以執行（mock）

**Day 3**: HITL 整合
- 實現 Telegram Bot 整合
- 測試審批流程
- 驗收：可以接收並處理審批

**Day 4-5**: E2E 測試 & 優化
- 創建 5+ 測試案例
- 執行完整測試
- 修復發現的問題
- 驗收：Week 6 Sign-off

---

## 💬 溝通與報告

### 日常站會（Daily Standup）
- 每日 10:00 AM 簡短同步（15 分鐘）
- 報告：昨日完成、今日計劃、遇到的阻礙
- CTO 需要知道所有 blocker

### 週中檢查（Mid-week Check-in）
- Week 5 Day 3: Knowledge Graph 進度檢查
- Week 6 Day 3: Workflow 進度檢查
- CTO 決定是否需要調整計劃

### 週末驗收（End of Week Sign-off）
- Week 5 結束：Knowledge Graph 功能驗收
- Week 6 結束：完整 Bug Fix Pilot 驗收
- 需要提供 DEMO 和測試報告

---

## 🛠️ 開發環境與工具

### 必備環境變量
```bash
# PostgreSQL (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-password

# OpenAI
OPENAI_API_KEY=sk-...

# Telegram (HITL)
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_CHAT_ID=your-chat-id

# Dev Agent Sandbox
DEV_AGENT_ENDPOINT=http://localhost:8080
```

### 開發流程
1. **基於 PR #291 開發** - 我已提供初步實現
2. **Feature Branch** - 每個功能一個 branch
3. **PR Review** - 所有 PR 需要 CTO review
4. **CI/CD** - 必須通過所有檢查
5. **文檔同步更新** - README、API docs、測試文檔

---

## 📚 參考資源

- **PR #291**: https://github.com/RC918/morningai/pull/291（初步實現）
- **Issue 文檔**: `.github/ISSUE_WEEK5_6.md`
- **Migration 指南**: `agents/dev_agent/migrations/README.md`
- **pgvector 文檔**: https://github.com/pgvector/pgvector
- **LangGraph 文檔**: https://python.langchain.com/docs/langgraph

---

## ✅ 最終交付物

Week 6 結束時需要提交：

1. **代碼**（合併到 main）
   - 所有功能完整實現
   - 通過 CI/CD
   - Code review 完成

2. **測試報告**
   - Unit test coverage report
   - E2E test results（≥ 5 案例）
   - 成功率統計

3. **文檔**
   - API 文檔更新
   - 使用指南（for other teams）
   - Troubleshooting 指南

4. **DEMO**
   - 完整的 bug fix workflow 演示
   - Knowledge graph 查詢演示
   - 性能數據展示

5. **部署計劃**
   - Staging 部署步驟
   - Production 部署檢查清單
   - Rollback 計劃

---

## 🎯 成功定義

Week 5-6 成功的標準：

✅ **技術指標**:
- Bug 修復成功率 ≥ 60%（Week 6 結束）
- 代碼庫索引 < 5 分鐘（10K 行）
- 語義搜索 < 500ms
- API 成本 < $5/day

✅ **質量指標**:
- 所有測試通過（unit + E2E）
- CI/CD 綠燈
- Code review approved
- 文檔完整

✅ **業務指標**:
- Dev_Agent 與 Devin AI 對齊度 ≥ 95%
- 可以演示完整的 Issue → PR 流程
- CTO 驗收通過

---

**CTO 簽名**: ________________  
**日期**: 2025-10-16

**工程團隊確認**: ________________  
**預計開始日期**: 2025-10-21
