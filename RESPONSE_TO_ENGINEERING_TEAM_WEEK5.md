# Week 5 開發指令

**From**: CTO (Devin)  
**To**: Backend Engineer + AI Engineer  
**Date**: 2025-10-16  
**Subject**: Week 5-6 Knowledge Graph & Bug Fix Pilot - 技術指令

---

## 一、Week 4 驗收結果

感謝團隊完成 Week 4！經過我的審查與測試，Week 4 的成果完全符合驗收標準：

✅ Session State Management  
✅ Decision Trace 機制  
✅ 路徑白名單安全機制  
✅ 統一錯誤處理  
✅ 所有 CI 檢查通過  

**我已經代表專案擁有者批准合併 Week 4 的成果。**

---

## 二、Week 5-6 戰略目標

根據我們的技術路線圖，Week 5-6 是 **Phase 1 的最後階段**，目標非常明確：

### 核心使命
**使 Dev_Agent 具備與 Devin AI 相同水平的工作能力與智能**

具體來說，需要實現：
1. 🧠 **代碼理解能力** - 能理解代碼庫結構和依賴關係
2. 📚 **學習能力** - 從過去的修復中學習並改進
3. 🤖 **自動修復能力** - 完整的 GitHub Issue → PR 自動化
4. 🎯 **與 Devin AI 對齊度達到 95%+**

---

## 三、技術方案概述

我已經完成技術方案設計並提供了參考實現（PR #291）。現在需要你們基於這個方案進行**完整的實作、測試和優化**。

### 架構設計

```
Week 5-6 Architecture:

┌─────────────────────────────────────────────────┐
│         Bug Fix Workflow (LangGraph)            │
│  Parse → Reproduce → Analyze → Fix → Test → PR │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│ Knowledge Graph│   │ Pattern Learner│
│  - Semantic    │   │  - Bug Patterns│
│    Search      │   │  - Fix Patterns│
│  - Code Index  │   │  - Learning    │
└────────┬───────┘   └────────┬───────┘
         │                    │
    ┌────▼────────────────────▼────┐
    │  PostgreSQL + pgvector        │
    │  - code_entities              │
    │  - entity_relationships       │
    │  - learned_patterns           │
    │  - bug_fix_history            │
    └───────────────────────────────┘
```

---

## 四、Week 5 優先任務清單

### 🔴 Priority 0 (本週必須完成)

#### Task 1: Database Setup & Migration
**負責人**: Backend Engineer  
**時間**: Day 1-2

**具體任務**:
1. 在 Supabase 安裝 pgvector 擴展
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. 執行我準備的 migration script
   ```bash
   psql -h your-db-host -U postgres -d morningai \
     -f agents/dev_agent/migrations/001_knowledge_graph_schema.sql
   ```

3. 驗證 4 個表創建成功：
   - `code_entities`
   - `entity_relationships`
   - `learned_patterns`
   - `bug_fix_history`

4. 測試 vector index 運作
   ```sql
   -- 測試 vector 查詢
   SELECT * FROM pg_extension WHERE extname = 'vector';
   \di  -- 檢查索引
   ```

**驗收標準**:
- [ ] pgvector 擴展安裝成功
- [ ] 4 個表都創建成功
- [ ] 所有索引創建成功
- [ ] 提供測試截圖

**預計時間**: 4 小時

---

#### Task 2: Knowledge Graph Manager 實現
**負責人**: Backend Engineer  
**時間**: Day 2-3

**具體任務**:
1. 基於 PR #291 的 `knowledge_graph.py` 進行實現
2. **必須添加以下功能**（我的方案中缺少的）:
   - Connection pooling（使用 `psycopg2.pool.SimpleConnectionPool`）
   - OpenAI API rate limiting（每分鐘最多 60 次）
   - Embedding cache（使用 Redis 快取）
   - 錯誤重試機制（最多重試 3 次）
   - API 調用計數器（追蹤成本）

3. 實現核心方法（參考 PR #291）:
   ```python
   class KnowledgeGraphManager:
       def initialize_schema()
       def add_entity()
       def add_relationship()
       def semantic_search()
       def find_related_entities()
       def get_session_stats()
       def get_cost_stats()  # 新增：成本追蹤
   ```

**驗收標準**:
- [ ] 可以添加實體到數據庫
- [ ] 可以執行語義搜索（使用 OpenAI embeddings）
- [ ] 可以追蹤關係圖
- [ ] 有成本統計功能
- [ ] 通過 unit tests
- [ ] 提供測試報告

**預計時間**: 12 小時

---

#### Task 3: Code Indexer 實現
**負責人**: Backend Engineer + AI Engineer  
**時間**: Day 3-4

**具體任務**:
1. 基於 PR #291 的 `code_indexer.py` 進行實現
2. **必須優化**:
   - 添加並發處理（使用 `ThreadPoolExecutor` 或 `asyncio`）
   - 添加進度顯示（tqdm progress bar）
   - 優化 AST 解析（捕獲所有異常）
   - 添加文件 hash 檢查（避免重複索引）

3. 實現核心方法:
   ```python
   class CodeIndexer:
       def scan_directory()  # 掃描整個目錄
       def index_file()      # 索引單個文件
       def index_python_file()  # Python AST 解析
       def get_file_structure()  # 獲取結構化視圖
   ```

**性能要求**:
- 10K 行代碼索引時間 < 5 分鐘
- 支持至少 1000 個文件
- 記憶體佔用 < 2GB

**驗收標準**:
- [ ] 可以索引 Python 代碼庫
- [ ] 提取 functions, classes, imports
- [ ] 建立關係圖（calls, imports）
- [ ] 性能達標
- [ ] 通過 tests
- [ ] 提供性能測試報告

**預計時間**: 12 小時

---

#### Task 4: Pattern Learner 實現
**負責人**: AI Engineer  
**時間**: Day 4-5

**具體任務**:
1. 基於 PR #291 的 `pattern_learner.py` 進行實現
2. 實現核心方法:
   ```python
   class PatternLearner:
       def learn_bug_pattern()
       def learn_fix_pattern()
       def get_similar_bug_patterns()
       def get_similar_fix_patterns()
       def record_bug_fix()
       def get_pattern_stats()
       def get_success_metrics()
   ```

**驗收標準**:
- [ ] 可以記錄 bug patterns
- [ ] 可以記錄 fix patterns
- [ ] 可以查找相似 patterns
- [ ] 追蹤成功率
- [ ] 通過 tests

**預計時間**: 8 小時

---

#### Task 5: 整合測試與文檔
**負責人**: QA + Backend Engineer  
**時間**: Day 5

**具體任務**:
1. 創建整合測試腳本
2. 測試完整流程：索引 → 搜索 → 學習
3. 更新 README 文檔
4. 準備 Week 5 驗收報告

**驗收標準**:
- [ ] 整合測試通過
- [ ] 文檔更新完整
- [ ] 驗收報告準備好

**預計時間**: 4 小時

---

## 五、Week 5 時間表

| Day | 任務 | 負責人 | 驗收點 |
|-----|------|--------|--------|
| Day 1-2 | Database Setup + KG Manager 開始 | Backend | DB 遷移完成 |
| Day 3 | KG Manager 完成 + Code Indexer 開始 | Backend + AI | KG 功能測試通過 |
| Day 4 | Code Indexer 完成 + Pattern Learner | Backend + AI | 索引功能測試通過 |
| Day 5 | Pattern Learner 完成 + 整合測試 | All | Week 5 完整驗收 |

---

## 六、關鍵風險與注意事項

### ⚠️ 風險 1: OpenAI API 成本
**問題**: 大型代碼庫可能產生大量 API 調用

**你們必須實現**:
- API 調用計數器
- 每日上限（1000 次）
- Embedding cache（Redis）
- 成本預估功能

**驗證方法**:
```python
stats = kg.get_cost_stats()
print(f"今日調用: {stats['calls_today']}")
print(f"預估費用: ${stats['cost']:.2f}")
```

---

### ⚠️ 風險 2: pgvector 性能
**問題**: Vector 查詢可能較慢

**緩解措施**:
- 使用 IVFFlat index（已在 migration 中）
- 限制 top_k ≤ 20
- 監控查詢時間（> 1 秒告警）

---

### ⚠️ 風險 3: 記憶體佔用
**問題**: 索引大型代碼庫可能 OOM

**緩解措施**:
- 使用流式處理
- 分批處理文件
- 設置記憶體上限

---

## 七、驗收標準（CTO Sign-off）

Week 5 結束時，我會檢查以下項目：

### 功能驗收
- [ ] PostgreSQL + pgvector 安裝並運作正常
- [ ] Knowledge Graph 可以索引 1000+ 行代碼
- [ ] 語義搜索返回相關結果（相似度 > 0.7）
- [ ] Pattern Learning 可以記錄並查找模式
- [ ] 所有 unit tests 通過（coverage > 80%）

### 性能驗收
- [ ] 10K 行代碼索引 < 5 分鐘
- [ ] 語義搜索響應 < 500ms
- [ ] 記憶體佔用 < 2GB

### 質量驗收
- [ ] Code review 完成（我會親自 review）
- [ ] CI/CD 全綠
- [ ] 文檔完整
- [ ] 無明顯 security issues

### 成本驗收
- [ ] API 調用有計數
- [ ] 有 rate limiting
- [ ] 有 cache 機制
- [ ] 每日成本 < $5

---

## 八、交付物清單

Week 5 結束（2025-10-27）前，需要提交：

1. **代碼** (Pull Request)
   - 所有功能實現完成
   - 通過 CI/CD
   - Code review approved by CTO

2. **測試報告**
   - Unit test results
   - Integration test results
   - Performance benchmark

3. **文檔**
   - README 更新
   - API 文檔
   - 使用範例

4. **驗收報告**
   - 功能完成度
   - 性能數據
   - 已知問題清單
   - Week 6 規劃

---

## 九、溝通機制

### 日常溝通
- **每日站會**: 每天 10:00 AM（15 分鐘）
  - 昨日完成
  - 今日計劃
  - 遇到的問題

- **即時溝通**: 遇到 blocker 立即告知我
  - 技術問題
  - 資源不足
  - 時程風險

### 週中檢查
- **Day 3 Check-in** (2025-10-23)
  - Knowledge Graph 進度審查
  - 決定是否需要調整計劃

### 週末驗收
- **Day 5 Sign-off** (2025-10-27)
  - 完整功能驗收
  - 決定是否可以進入 Week 6

---

## 十、參考資源

我已經提供以下資源供你們參考：

1. **PR #291**: https://github.com/RC918/morningai/pull/291
   - 包含初步實現（參考用）
   - 你們需要基於此進行完善

2. **Issue 文檔**: `.github/ISSUE_WEEK5_6.md`
   - 詳細需求說明
   - 397 行完整規格

3. **Migration Script**: `agents/dev_agent/migrations/001_knowledge_graph_schema.sql`
   - 數據庫 schema
   - 直接執行即可

4. **外部文檔**:
   - pgvector: https://github.com/pgvector/pgvector
   - OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings

---

## 十一、環境配置

確保你們有以下環境變量：

```bash
# PostgreSQL (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-password

# OpenAI
OPENAI_API_KEY=sk-...

# Dev Agent Sandbox
DEV_AGENT_ENDPOINT=http://localhost:8080

# Redis (for cache)
REDIS_URL=your-redis-url
```

---

## 十二、開始前確認

請在 **2025-10-21 開始前** 回覆我以下問題：

1. ✅ 是否理解所有技術要求？
2. ✅ 是否有足夠的資源（人力、時間）？
3. ✅ 環境配置是否完成（Supabase、OpenAI API Key）？
4. ✅ 是否有任何 blocker 或疑問？

如果有任何問題，請立即告知我，我會協助解決。

---

## 總結

**Week 5 的核心目標**: 實現 Knowledge Graph 系統，使 Dev_Agent 具備代碼理解和學習能力。

**我的期望**:
- 高質量的代碼（可維護、可擴展）
- 完整的測試覆蓋
- 清晰的文檔
- 按時交付

**我會提供的支持**:
- 技術問題解答
- 架構建議
- Code review
- 驗收把關

Let's make Week 5 a success! 💪

---

**CTO**: Devin  
**Date**: 2025-10-16  
**Next Check-in**: 2025-10-21 (Week 5 Day 1)
