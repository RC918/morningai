# Week 5-6: Bug Fix Pilot & Knowledge Graph

## 🎯 目標

完成 Dev_Agent Phase 1 的最後階段，實現：
1. 知識圖譜與學習機制（使 Agent 具備代碼庫理解能力）
2. 自動 Bug 修復試點（從 GitHub Issue 到 PR 的完整工作流）
3. 達成 Devin AI 級別的工作能力

## 📋 工作範圍

### Part 1: 知識圖譜 (Week 5, 40 小時)

#### 1.1 pgvector 整合
- [ ] 安裝 pgvector 擴展到 Supabase
- [ ] 設計 Knowledge Graph Schema
- [ ] 實現 embedding 生成（OpenAI text-embedding-3-small）
- [ ] 實現向量相似度搜索

#### 1.2 代碼庫索引
- [ ] 實現代碼文件掃描
- [ ] 提取代碼實體（functions, classes, variables）
- [ ] LSP 工具整合（獲取引用關係）
- [ ] 建立依賴關係圖

#### 1.3 學習機制
- [ ] 實現編碼模式識別
- [ ] 儲存常見 bug patterns
- [ ] 儲存成功的 fix patterns
- [ ] 頻率統計與排序

#### 1.4 持久化層完善
- [ ] PostgreSQL schema migration
- [ ] Redis ↔ PostgreSQL 同步機制
- [ ] 知識圖譜 TTL 管理
- [ ] 查詢優化（索引、分區）

### Part 2: Bug 修復試點 (Week 6, 40 小時)

#### 2.1 Bug 修復工作流設計
- [ ] GitHub Issue webhook 整合
- [ ] Issue 解析與分類
- [ ] 任務優先級評估
- [ ] 工作流狀態機設計

#### 2.2 自動 Bug 重現
- [ ] 從 Issue 描述提取測試用例
- [ ] 自動運行相關測試
- [ ] 錯誤堆棧分析
- [ ] 定位問題代碼位置

#### 2.3 自動修復建議
- [ ] LSP 工具深度整合（定義跳轉、引用查找）
- [ ] 代碼模式匹配（從 learned_patterns）
- [ ] 生成修復候選方案
- [ ] 方案評分與排序

#### 2.4 PR 創建與提交
- [ ] Git_Tool 增強（branch, commit, push）
- [ ] 自動生成 PR description
- [ ] 關聯原始 Issue
- [ ] 添加測試結果

#### 2.5 HITL 審批整合
- [ ] Telegram Bot 通知
- [ ] 審批流程設計（approve/reject/modify）
- [ ] 修改建議反饋循環
- [ ] 審批記錄持久化

#### 2.6 驗證與測試
- [ ] 準備 20+ 個測試 Bug Issues
- [ ] 運行完整修復流程
- [ ] 計算成功率（目標 >85%）
- [ ] 分析失敗案例

## 🏗️ 技術架構

### Knowledge Graph Schema (PostgreSQL)

```sql
-- 啟用 pgvector 擴展
CREATE EXTENSION IF NOT EXISTS vector;

-- 代碼實體表
CREATE TABLE code_entities (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions(session_id),
    entity_type VARCHAR(50),  -- 'file', 'function', 'class', 'variable', 'import'
    entity_name VARCHAR(255),
    file_path TEXT,
    line_start INT,
    line_end INT,
    source_code TEXT,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB,  -- {language, framework, complexity, etc}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 實體關係表
CREATE TABLE entity_relationships (
    id SERIAL PRIMARY KEY,
    from_entity_id INT REFERENCES code_entities(id),
    to_entity_id INT REFERENCES code_entities(id),
    relationship_type VARCHAR(50),  -- 'calls', 'imports', 'inherits', 'uses'
    weight FLOAT DEFAULT 1.0,  -- 關係強度
    created_at TIMESTAMP DEFAULT NOW()
);

-- 學習模式表
CREATE TABLE learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50),  -- 'bug_pattern', 'fix_pattern', 'coding_style'
    pattern_name VARCHAR(255),
    pattern_data JSONB,  -- {trigger, solution, context}
    frequency INT DEFAULT 1,
    success_rate FLOAT DEFAULT 0.0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bug 修復記錄
CREATE TABLE bug_fix_history (
    id SERIAL PRIMARY KEY,
    github_issue_id INT,
    issue_title TEXT,
    issue_description TEXT,
    bug_type VARCHAR(100),
    root_cause TEXT,
    fix_strategy TEXT,
    pr_number INT,
    success BOOLEAN,
    execution_time_seconds INT,
    patterns_used JSONB,  -- [pattern_id, ...]
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引優化
CREATE INDEX idx_entities_embedding ON code_entities USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_entities_type_name ON code_entities(entity_type, entity_name);
CREATE INDEX idx_entities_file ON code_entities(file_path);
CREATE INDEX idx_relationships_from ON entity_relationships(from_entity_id);
CREATE INDEX idx_relationships_to ON entity_relationships(to_entity_id);
CREATE INDEX idx_patterns_type ON learned_patterns(pattern_type);
CREATE INDEX idx_patterns_frequency ON learned_patterns(frequency DESC);
```

### Knowledge Graph Manager

```python
# agents/dev_agent/knowledge/knowledge_graph.py
from typing import List, Dict, Optional
import openai
from pgvector.psycopg2 import register_vector

class KnowledgeGraphManager:
    """管理代碼庫知識圖譜"""
    
    def __init__(self, db_conn, openai_api_key: str):
        self.db = db_conn
        self.openai = openai.Client(api_key=openai_api_key)
        register_vector(db_conn)
    
    async def index_codebase(self, workspace_path: str, session_id: str):
        """掃描並索引整個代碼庫"""
        # 1. 掃描文件
        # 2. 使用 LSP 提取實體
        # 3. 生成 embeddings
        # 4. 儲存到 PostgreSQL
        pass
    
    async def semantic_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """基於語義的代碼搜索"""
        # 1. 生成 query embedding
        # 2. 向量相似度搜索
        # 3. 返回相關代碼片段
        pass
    
    async def find_related_code(self, entity_id: int, depth: int = 2) -> List[Dict]:
        """查找相關代碼（基於引用關係）"""
        # Graph traversal
        pass
    
    async def learn_pattern(self, pattern_type: str, pattern_data: Dict):
        """學習新的代碼模式"""
        # 儲存到 learned_patterns
        pass
    
    async def get_similar_patterns(self, description: str, top_k: int = 5) -> List[Dict]:
        """獲取相似的已知模式"""
        # 基於描述的相似度匹配
        pass
```

### Bug Fix Workflow

```python
# agents/dev_agent/workflows/bug_fix_workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class BugFixState(TypedDict):
    github_issue: Dict
    bug_description: str
    test_results: Optional[Dict]
    root_cause: Optional[str]
    fix_candidates: List[Dict]
    selected_fix: Optional[Dict]
    pr_info: Optional[Dict]
    approval_status: Optional[str]

class BugFixWorkflow:
    """自動 Bug 修復工作流"""
    
    def __init__(self, dev_agent):
        self.agent = dev_agent
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """構建 LangGraph 工作流"""
        workflow = StateGraph(BugFixState)
        
        # 節點
        workflow.add_node("parse_issue", self.parse_issue)
        workflow.add_node("reproduce_bug", self.reproduce_bug)
        workflow.add_node("analyze_root_cause", self.analyze_root_cause)
        workflow.add_node("generate_fixes", self.generate_fixes)
        workflow.add_node("apply_fix", self.apply_fix)
        workflow.add_node("create_pr", self.create_pr)
        workflow.add_node("request_approval", self.request_approval)
        
        # 邊
        workflow.add_edge("parse_issue", "reproduce_bug")
        workflow.add_edge("reproduce_bug", "analyze_root_cause")
        workflow.add_edge("analyze_root_cause", "generate_fixes")
        workflow.add_edge("generate_fixes", "apply_fix")
        workflow.add_edge("apply_fix", "create_pr")
        workflow.add_edge("create_pr", "request_approval")
        workflow.add_conditional_edges(
            "request_approval",
            self.check_approval,
            {
                "approved": END,
                "rejected": "generate_fixes",  # 重新生成
                "modify": "apply_fix"  # 修改後重試
            }
        )
        
        workflow.set_entry_point("parse_issue")
        return workflow.compile()
    
    async def parse_issue(self, state: BugFixState) -> BugFixState:
        """解析 GitHub Issue"""
        # 提取 bug 描述、重現步驟、預期行為
        pass
    
    async def reproduce_bug(self, state: BugFixState) -> BugFixState:
        """重現 Bug"""
        # 運行測試、分析錯誤堆棧
        pass
    
    async def analyze_root_cause(self, state: BugFixState) -> BugFixState:
        """根因分析"""
        # 使用 LSP + Knowledge Graph 定位問題
        pass
    
    async def generate_fixes(self, state: BugFixState) -> BugFixState:
        """生成修復方案"""
        # 查詢 learned_patterns + LLM 生成
        pass
    
    async def apply_fix(self, state: BugFixState) -> BugFixState:
        """應用修復"""
        # 修改代碼、運行測試
        pass
    
    async def create_pr(self, state: BugFixState) -> BugFixState:
        """創建 PR"""
        # Git commit + push + create PR
        pass
    
    async def request_approval(self, state: BugFixState) -> BugFixState:
        """請求 HITL 審批"""
        # 發送 Telegram 通知
        pass
    
    def check_approval(self, state: BugFixState) -> str:
        """檢查審批狀態"""
        return state.get("approval_status", "pending")
```

## 🎯 驗收標準

### Knowledge Graph
- [ ] 可索引 10,000+ 行代碼庫（<5 分鐘）
- [ ] 語義搜索準確率 >80%
- [ ] 關係圖深度支持 ≥3 層
- [ ] 查詢響應時間 <500ms

### Bug Fix Workflow
- [ ] Bug 修復成功率 >85%（至少 20 個測試案例）
- [ ] 平均修復時間 <15 分鐘
- [ ] PR 自動創建成功率 100%
- [ ] HITL 審批流程完整可用

### 整體系統
- [ ] 與 Devin AI 核心能力對齊 >95%
- [ ] 支持 100 並發 Session
- [ ] Session 恢復時間 <5 秒
- [ ] 代碼質量通過 lint & type check

## 📊 測試計劃

### 知識圖譜測試
1. **索引測試**: 測試不同規模代碼庫（100行、1K行、10K行）
2. **搜索測試**: 測試語義搜索準確性（準備 50 個查詢）
3. **關係測試**: 驗證引用關係正確性
4. **性能測試**: 壓測查詢性能（1000 QPS）

### Bug 修復測試
準備 20+ 個真實 Bug Issues，涵蓋：
- **語法錯誤** (5 個): 缺少括號、拼寫錯誤等
- **邏輯錯誤** (5 個): 條件判斷錯誤、循環問題等
- **類型錯誤** (5 個): 類型不匹配、None 檢查缺失等
- **集成錯誤** (5 個): API 調用錯誤、依賴問題等

每個測試包含：
- GitHub Issue 描述
- 預期的根因
- 預期的修復方案
- 驗證測試用例

## 🚨 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| pgvector 性能瓶頸 | 高 | 使用 ivfflat 索引、限制向量維度 |
| LLM 生成錯誤修復 | 高 | 強化 HITL 審批、自動測試驗證 |
| 知識圖譜不準確 | 中 | LSP 驗證、定期重建索引 |
| Bug 修復成功率不達標 | 高 | 擴大 learned_patterns 庫、優化算法 |
| Supabase 查詢慢 | 中 | Redis 快取、查詢優化 |

## 📈 成功指標 (KPI)

### 核心指標
- **Bug 修復成功率**: >85%
- **平均修復時間**: <15 分鐘
- **知識圖譜搜索準確率**: >80%
- **HITL 審批通過率**: >70%

### 性能指標
- **代碼庫索引時間**: <5 分鐘 (10K 行)
- **語義搜索響應時間**: <500ms
- **Bug 重現時間**: <3 分鐘
- **PR 創建時間**: <2 分鐘

### 系統指標
- **並發支持**: 100 Sessions
- **可用性**: >99.5%
- **錯誤率**: <5%

## 📚 相關資源

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [LangGraph Workflows](https://python.langchain.com/docs/langgraph)
- [Phase 1 Issue Template](./.github/issue_templates/phase1-session-state-ooda.md)

## 📅 里程碑

### Week 5 (40 小時)
- Day 1-2: pgvector 整合 + Schema 設計
- Day 3-4: 代碼庫索引實現
- Day 5: 學習機制實現

### Week 6 (40 小時)
- Day 1-2: Bug 修復工作流設計 + Issue 解析
- Day 3-4: 自動修復生成 + PR 創建
- Day 5: HITL 整合 + 完整測試

## 🎉 完成後的能力

完成 Week 5-6 後，Dev_Agent 將具備：

✅ **代碼理解能力** - 能夠理解代碼庫結構、依賴關係  
✅ **語義搜索能力** - 快速找到相關代碼  
✅ **學習能力** - 從過去的修復中學習模式  
✅ **自動修復能力** - 從 Issue 到 PR 的完整自動化  
✅ **協作能力** - HITL 審批機制確保質量  

**與 Devin AI 的能力對齊度將達到 95%+** 🚀

---

**負責人**: Backend Engineer + AI Engineer  
**預計完成時間**: 2 週（80 小時）  
**優先級**: P0 (Critical)
