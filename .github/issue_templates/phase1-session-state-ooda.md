## 目標

實現 Dev_Agent 的長期記憶和智能決策能力，使其能夠跨 Session 保持上下文，並整合到 Meta-Agent OODA 循環中。

## 背景

Dev_Agent 基礎沙箱已完成（PR #278），包含 VSCode Server、LSP、Git 等工具。但缺少：
- 長期記憶（Session 結束後上下文丟失）
- 智能決策（與 Meta-Agent 未整合）
- 知識積累（無法學習編碼模式）

## 工作範圍

### Week 3: OODA 循環整合
- [ ] 設計 Dev_Agent State Schema（與 meta_agent_decision_hub.py 對齊）
- [ ] 實現 Observe 節點（代碼探索、問題識別）
- [ ] 實現 Orient 節點（任務分析、策略評估）
- [ ] 實現 Decide 節點（策略選擇、工具規劃）
- [ ] 實現 Act 節點（工具執行、結果驗證）
- [ ] 整合到現有 Orchestrator（handoff/20250928/40_App/orchestrator/）

### Week 4: Session State 管理
- [ ] 設計 Session State 資料結構（Redis + PostgreSQL）
- [ ] 實現 Context Window 管理（滑動窗口，保留最近 N 個操作）
- [ ] 實現知識圖譜（代碼庫結構索引，使用 pgvector）
- [ ] 實現學習機制（編碼模式識別，儲存到 PostgreSQL）
- [ ] 持久化層設計（Redis 快取 + PostgreSQL 長期儲存）

### Week 5-6: Bug 修復試點
- [ ] 設計 Bug 修復工作流（從 GitHub Issue 到 PR）
- [ ] 實現自動 Bug 重現（基於 Issue 描述）
- [ ] 實現自動修復建議（使用 LSP + Git 工具）
- [ ] 實現 PR 創建與提交（Git_Tool integration）
- [ ] HITL 審批整合（使用現有 Telegram HITL 系統）
- [ ] 成功率驗證（目標 >85%）

## 技術架構

### Session State Schema (PostgreSQL)
```sql
CREATE TABLE agent_sessions (
  session_id UUID PRIMARY KEY,
  agent_type VARCHAR(50),
  created_at TIMESTAMP,
  last_activity TIMESTAMP,
  context_window JSONB,  -- 最近 N 個操作
  metadata JSONB
);

CREATE TABLE knowledge_graph (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES agent_sessions(session_id),
  entity_type VARCHAR(50),  -- 'file', 'function', 'class', 'variable'
  entity_name VARCHAR(255),
  relationships JSONB,  -- 引用關係
  embedding VECTOR(1536),  -- pgvector for semantic search
  created_at TIMESTAMP
);

CREATE TABLE learned_patterns (
  id SERIAL PRIMARY KEY,
  pattern_type VARCHAR(50),  -- 'coding_style', 'bug_pattern', 'fix_pattern'
  pattern_data JSONB,
  frequency INT,
  last_used TIMESTAMP
);
```

### Redis Cache Schema
```python
# Session context (短期快取)
redis_key = f"session:{session_id}:context"
# TTL: 1 hour

# Recent operations (滑動窗口)
redis_key = f"session:{session_id}:operations"
# LPUSH + LTRIM to maintain size

# Active tools state
redis_key = f"session:{session_id}:tools"
# Hash of tool states
```

### OODA Integration
- 繼承 `meta_agent_decision_hub.py` 的 OODA 框架
- Dev_Agent 成為 Meta-Agent 的一個專業 Agent
- 決策優先級：CRITICAL → HIGH → MEDIUM → LOW
- 整合現有 Agent Registry

## 驗收標準

- [ ] Session State 可在 Dev_Agent 重啟後恢復
- [ ] 知識圖譜可正確索引代碼庫結構
- [ ] OODA 循環可完整執行（Observe → Orient → Decide → Act）
- [ ] Bug 修復成功率 >85%（至少 20 個測試案例）
- [ ] Session 恢復時間 <5 秒
- [ ] 100 並發 Session 壓測通過

## 相關資源

- [Meta-Agent Decision Hub](../meta_agent_decision_hub.py)
- [Dev Agent Work Ticket](../docs/dev-agent-work-ticket.md)
- [Devin-Level Agents Roadmap](../docs/devin-level-agents-roadmap.md)
- [Persistent State Manager](../persistent_state_manager.py)

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| Redis 記憶體不足 | 高 | 實施 LRU eviction，限制 context window 大小 |
| PostgreSQL 查詢慢 | 中 | pgvector index 優化，Redis 快取 |
| OODA 決策錯誤 | 高 | 強化 HITL 審批，記錄所有決策 |
| 知識圖譜不準確 | 中 | LSP 驗證，定期重建索引 |

## 估計工時

- Week 3: 40 小時（OODA 整合）
- Week 4: 40 小時（Session State）
- Week 5-6: 80 小時（Bug 修復試點 + 驗證）
- **總計**: 160 小時

## 負責人

- Backend Engineer
- DevOps Engineer（Redis/PostgreSQL 配置）
- AI Engineer（知識圖譜、OODA 邏輯）
