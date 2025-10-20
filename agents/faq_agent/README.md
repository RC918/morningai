# FAQ Agent - 智能問答代理

## 概述

FAQ Agent 是 Morning AI 生態系統中的智能問答代理，專門處理常見問題並提供準確、上下文相關的答案。

## 核心功能

### 1. 問答系統
- 語義搜索：基於向量相似度的問題匹配
- 上下文理解：理解問題背景和意圖
- 多語言支持：支援中文、英文
- 動態學習：從用戶反饋中學習

### 2. 知識庫管理
- FAQ 創建和更新
- 分類管理
- 版本控制
- 搜索優化

### 3. 整合能力
- Supabase 數據存儲
- OpenAI Embeddings
- Redis 緩存
- Slack/Email 通知

## 架構設計

```
agents/faq_agent/
├── faq_agent_ooda.py          # OODA Loop 核心
├── tools/
│   ├── __init__.py
│   ├── faq_search_tool.py     # FAQ 搜索工具
│   ├── faq_management_tool.py # FAQ 管理工具
│   └── embedding_tool.py      # 嵌入生成工具
├── tests/
│   ├── test_faq_search.py
│   ├── test_faq_management.py
│   └── test_faq_agent_e2e.py
└── examples/
    └── faq_example.py
```

## 快速開始

### 1. 安裝依賴

```bash
cd agents/faq_agent
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
export OPENAI_API_KEY="your-openai-key"
export REDIS_URL="your-redis-url"  # 可選
```

### 3. 運行示例

```python
from agents.faq_agent.faq_agent_ooda import create_faq_agent

# 創建 FAQ Agent
agent = create_faq_agent()

# 搜索 FAQ
result = await agent.execute_task(
    "如何使用 Ops Agent 監控系統？",
    task_type="search"
)

print(result['answer'])
```

## 數據庫架構

### FAQ 表格

```sql
-- FAQ 問答表
CREATE TABLE faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0
);

-- FAQ 搜索歷史
CREATE TABLE faq_search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    query_embedding VECTOR(1536),
    matched_faq_id UUID REFERENCES faqs(id),
    similarity_score FLOAT,
    user_feedback VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- FAQ 分類
CREATE TABLE faq_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES faq_categories(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API 端點

### 搜索 FAQ

```python
POST /api/faq/search
Body: {
    "query": "如何使用 Ops Agent？",
    "limit": 5,
    "threshold": 0.7
}

Response: {
    "success": true,
    "results": [
        {
            "question": "如何使用 Ops Agent 監控系統？",
            "answer": "...",
            "similarity": 0.95,
            "category": "ops_agent"
        }
    ]
}
```

### 創建 FAQ

```python
POST /api/faq/create
Body: {
    "question": "問題",
    "answer": "答案",
    "category": "分類",
    "tags": ["標籤1", "標籤2"]
}
```

### 更新 FAQ

```python
PUT /api/faq/{id}
Body: {
    "question": "更新的問題",
    "answer": "更新的答案"
}
```

## 工具說明

### FAQ Search Tool

語義搜索功能：

```python
from agents.faq_agent.tools import FAQSearchTool

search_tool = FAQSearchTool()

result = await search_tool.search(
    query="如何使用 Vercel 部署？",
    limit=5,
    threshold=0.7
)
```

### FAQ Management Tool

FAQ 管理功能：

```python
from agents.faq_agent.tools import FAQManagementTool

mgmt_tool = FAQManagementTool()

# 創建 FAQ
result = await mgmt_tool.create_faq(
    question="如何檢查系統健康？",
    answer="使用 MonitoringTool...",
    category="monitoring",
    tags=["ops", "monitoring"]
)

# 更新 FAQ
result = await mgmt_tool.update_faq(
    faq_id="uuid",
    answer="更新後的答案"
)

# 刪除 FAQ
result = await mgmt_tool.delete_faq(faq_id="uuid")
```

### Embedding Tool

生成問題嵌入：

```python
from agents.faq_agent.tools import EmbeddingTool

emb_tool = EmbeddingTool()

result = await emb_tool.generate_embedding(
    text="如何使用 Ops Agent？"
)

embedding = result['embedding']  # 1536 維向量
```

## OODA Loop 整合

FAQ Agent 使用 OODA（Observe, Orient, Decide, Act）循環：

### 階段

1. **Observe（觀察）**: 分析用戶問題，提取關鍵詞
2. **Orient（定位）**: 搜索相關 FAQ，評估相似度
3. **Decide（決策）**: 選擇最佳答案或生成新答案
4. **Act（行動）**: 返回答案，記錄搜索歷史

### 使用示例

```python
from agents.faq_agent.faq_agent_ooda import create_faq_agent

agent = create_faq_agent()

result = await agent.execute_task(
    "如何使用 Ops Agent 監控 Vercel 部署？",
    task_type="search",
    context={
        "user_id": "user123",
        "session_id": "session456"
    }
)

print(f"答案: {result['answer']}")
print(f"相似度: {result['similarity']}")
print(f"來源: {result['source_faq_id']}")
```

## 性能指標

### 目標

- 搜索延遲: <100ms
- 嵌入生成: <200ms
- 緩存命中率: >80%
- 答案準確率: >90%

### 優化策略

1. **緩存**: Redis 緩存常見問題嵌入
2. **批量處理**: 批量生成嵌入
3. **索引優化**: pgvector 索引優化
4. **預計算**: 預計算常見問題嵌入

## 測試

### 運行測試

```bash
# 運行所有測試
pytest agents/faq_agent/tests/ -v

# 運行特定測試
pytest agents/faq_agent/tests/test_faq_search.py -v

# 運行 E2E 測試
pytest agents/faq_agent/tests/test_faq_agent_e2e.py -v
```

### 測試覆蓋率

```bash
pytest agents/faq_agent/tests/ --cov=agents/faq_agent
```

## 部署

### 本地開發

```bash
# 啟動開發服務器
cd agents/faq_agent
python -m uvicorn faq_agent_api:app --reload
```

### 生產部署

```bash
# 使用 Docker
cd agents/faq_agent
docker build -t faq-agent .
docker run -p 8000:8000 faq-agent
```

## 配置

### 環境變數

- `SUPABASE_URL`: Supabase 項目 URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase 服務密鑰
- `OPENAI_API_KEY`: OpenAI API 密鑰
- `REDIS_URL`: Redis 連接 URL（可選）
- `FAQ_CACHE_TTL`: 緩存過期時間（秒，預設 3600）
- `FAQ_SIMILARITY_THRESHOLD`: 相似度閾值（預設 0.7）

### FAQ Agent 參數

- `max_results`: 最大返回結果數（預設 5）
- `enable_cache`: 啟用緩存（預設 True）
- `enable_feedback`: 啟用反饋收集（預設 True）

## 安全性

1. **權限控制**: Row Level Security (RLS)
2. **輸入驗證**: 防止 SQL 注入
3. **速率限制**: 防止濫用
4. **數據加密**: 敏感數據加密存儲

## 監控

### 關鍵指標

- 搜索請求數
- 平均響應時間
- 緩存命中率
- 用戶反饋分數

### 告警規則

- 搜索延遲 > 500ms
- 錯誤率 > 5%
- 緩存命中率 < 70%

## 維護

### 定期任務

1. **更新 FAQ**: 每週審查和更新
2. **重建索引**: 每月重建向量索引
3. **清理歷史**: 每季度清理舊搜索歷史
4. **性能優化**: 每月分析慢查詢

## 路線圖

### Phase 1 (當前)
- ✅ 基本架構設計
- 🔄 核心工具實現
- 🔄 OODA Loop 整合
- 🔄 測試和文檔

### Phase 2 (下週)
- ⬜ 自動分類
- ⬜ 多語言支持增強
- ⬜ A/B 測試框架
- ⬜ 用戶反饋分析

### Phase 3 (下個月)
- ⬜ 知識圖譜整合
- ⬜ 主動推薦
- ⬜ 對話式問答
- ⬜ 多輪對話支持

## 常見問題

### Q: FAQ Agent 與 Dev Agent 的區別？

FAQ Agent 專注於問答，Dev Agent 專注於開發任務。

### Q: 如何添加新 FAQ？

使用 FAQManagementTool 的 `create_faq` 方法。

### Q: 支持哪些語言？

目前支持中文和英文，未來將支持更多語言。

### Q: 如何提高搜索準確率？

1. 使用更準確的問題描述
2. 添加更多相關 FAQ
3. 調整相似度閾值

## 聯繫

有問題或建議？請聯繫開發團隊。

---

**版本**: 1.0.0  
**最後更新**: 2025-10-19
