# MorningAI 資料庫 Schema 深度解析

**生成時間**: 2025-10-24  
**資料庫**: Supabase PostgreSQL + pgvector  
**Migrations**: 25 個 SQL migrations

---

## 📋 執行摘要

MorningAI 使用 **Supabase PostgreSQL** 作為主資料庫，實作了完整的 **Row Level Security (RLS)** 保護所有 multi-tenant tables。資料庫包含 **9 個核心 table groups**，涵蓋 FAQ 管理、Vector 搜尋、效能追蹤、Agent reputation 等功能。

### 關鍵指標
- **Migrations**: 25 個 SQL migrations
- **RLS Protected Tables**: 9+ tables
- **RLS Policies**: 18+ policies (service_role + authenticated)
- **Extensions**: pgvector, pg_stat_statements, pg_trgm
- **Materialized Views**: 2 個 (daily_cost_summary, vector_visualization)

---

## 🗄️ Database Schema 總覽

### Schema 結構

```
public schema
├── Multi-tenant Core Tables
│   ├── tenants
│   ├── users
│   ├── strategies
│   ├── decisions
│   ├── costs
│   └── audit_logs
│
├── FAQ System Tables
│   ├── faqs
│   ├── faq_search_history
│   └── faq_categories
│
├── Vector Search Tables
│   ├── embeddings
│   └── vector_queries
│
├── Performance Monitoring Tables
│   ├── trace_metrics
│   └── alerts
│
├── Agent Reputation Tables
│   ├── agent_reputation
│   └── reputation_events
│
├── Materialized Views
│   ├── daily_cost_summary
│   └── vector_visualization
│
└── Functions
    ├── match_faqs()
    ├── update_agent_reputation()
    ├── calculate_test_pass_rate()
    ├── record_reputation_event()
    ├── get_agent_reputation_summary()
    └── refresh_daily_cost_summary()
```

---

## 📊 Table Groups 詳細說明

### 1. Multi-tenant Core Tables

#### tenants
**用途**: 租戶元資料

```sql
CREATE TABLE public.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    
    -- Billing
    plan VARCHAR(50) DEFAULT 'free',
    mrr DECIMAL(10,2) DEFAULT 0,
    
    -- Limits
    max_users INTEGER DEFAULT 5,
    max_strategies INTEGER DEFAULT 10,
    max_executions_per_month INTEGER DEFAULT 100
);

-- RLS Policies
CREATE POLICY "owner_access" ON public.tenants
    FOR ALL
    USING (
        current_setting('app.current_role') = 'owner'
        OR id = current_setting('app.current_tenant_id')::uuid
    );
```

**欄位說明**:
- `id`: 租戶唯一識別碼
- `slug`: URL-friendly 識別碼 (例如: `acme-corp`)
- `settings`: 租戶配置 (JSONB)
- `plan`: 訂閱方案 (free, pro, enterprise)
- `mrr`: 月經常性收入

#### users
**用途**: 使用者帳號

```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    
    -- Profile
    display_name VARCHAR(255),
    avatar_url TEXT,
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    email_verified BOOLEAN DEFAULT FALSE
);

-- RLS Policies
CREATE POLICY "tenant_isolation" ON public.users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "owner_access" ON public.users
    FOR ALL
    USING (current_setting('app.current_role') = 'owner');
```

**角色層級**:
- `owner`: 平台管理員 (跨租戶存取)
- `admin`: 租戶管理員
- `user`: 標準使用者

#### strategies
**用途**: 自動化策略定義

```sql
CREATE TABLE public.strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    created_by UUID REFERENCES public.users(id),
    
    -- Strategy definition
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSONB DEFAULT '{}',
    
    -- Agent configuration
    agent_type VARCHAR(50) NOT NULL,
    agent_config JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    enabled BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_executed_at TIMESTAMPTZ
);

-- RLS Policies
CREATE POLICY "tenant_isolation" ON public.strategies
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**trigger_type 選項**:
- `manual`: 手動觸發
- `schedule`: 定時觸發 (cron)
- `event`: 事件觸發 (webhook)
- `ci_failure`: CI 失敗觸發

**agent_type 選項**:
- `dev_agent`: 開發 Agent
- `ops_agent`: 運維 Agent
- `pm_agent`: 專案管理 Agent (計劃中)

#### decisions
**用途**: Agent 決策記錄

```sql
CREATE TABLE public.decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES public.strategies(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL,
    
    -- Decision details
    decision_type VARCHAR(50) NOT NULL,
    description TEXT,
    reasoning TEXT,
    confidence DECIMAL(3,2),
    
    -- Approval workflow
    status VARCHAR(50) DEFAULT 'pending',
    requires_approval BOOLEAN DEFAULT TRUE,
    approved_by UUID REFERENCES public.users(id),
    approved_at TIMESTAMPTZ,
    
    -- Execution
    executed_at TIMESTAMPTZ,
    result JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
CREATE POLICY "tenant_isolation" ON public.decisions
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**decision_type 選項**:
- `code_change`: 程式碼變更
- `deployment`: 部署決策
- `rollback`: 回滾決策
- `config_change`: 配置變更

**status 選項**:
- `pending`: 等待審批
- `approved`: 已批准
- `rejected`: 已拒絕
- `executed`: 已執行
- `failed`: 執行失敗

#### costs
**用途**: 使用量和成本追蹤

```sql
CREATE TABLE public.costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    execution_id UUID,
    
    -- Cost breakdown
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    amount DECIMAL(10,4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Details
    details JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    billing_period VARCHAR(7)
);

-- RLS Policies
CREATE POLICY "tenant_isolation" ON public.costs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Indexes
CREATE INDEX idx_costs_tenant_period ON public.costs(tenant_id, billing_period);
CREATE INDEX idx_costs_resource ON public.costs(resource_type, resource_id);
```

**resource_type 選項**:
- `llm_api`: LLM API 呼叫 (OpenAI, Anthropic)
- `agent_execution`: Agent 執行時間
- `storage`: 儲存空間
- `compute`: 運算資源 (Fly.io)
- `api_calls`: API 呼叫次數

#### audit_logs
**用途**: 合規審計日誌

```sql
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id),
    
    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
CREATE POLICY "tenant_isolation" ON public.audit_logs
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY "owner_access" ON public.audit_logs
    FOR ALL
    USING (current_setting('app.current_role') = 'owner');

-- Indexes
CREATE INDEX idx_audit_logs_tenant_created ON public.audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON public.audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_resource ON public.audit_logs(resource_type, resource_id);
```

**action 範例**:
- `user.login`, `user.logout`
- `strategy.create`, `strategy.update`, `strategy.delete`
- `decision.approve`, `decision.reject`
- `tenant.settings.update`

---

### 2. FAQ System Tables

#### faqs
**用途**: FAQ 內容儲存

```sql
CREATE TABLE public.faqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category_id UUID REFERENCES public.faq_categories(id),
    
    -- Metadata
    language VARCHAR(10) DEFAULT 'en',
    tags TEXT[],
    
    -- Vector embedding
    embedding VECTOR(1536),
    
    -- Status
    status VARCHAR(50) DEFAULT 'published',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Analytics
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0
);

-- RLS Policies (Migration 014)
ALTER TABLE public.faqs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_faqs_all" ON public.faqs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_faqs_read" ON public.faqs
    FOR SELECT
    TO authenticated
    USING (true);

-- Vector search index
CREATE INDEX idx_faqs_embedding ON public.faqs 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search
CREATE INDEX idx_faqs_search ON public.faqs 
    USING gin(to_tsvector('english', question || ' ' || answer));
```

**Vector Search Function**:
```sql
CREATE OR REPLACE FUNCTION match_faqs(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    filter_language VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        faqs.id,
        faqs.question,
        faqs.answer,
        1 - (faqs.embedding <=> query_embedding) AS similarity
    FROM public.faqs
    WHERE 
        (filter_language IS NULL OR faqs.language = filter_language)
        AND faqs.status = 'published'
        AND 1 - (faqs.embedding <=> query_embedding) > match_threshold
    ORDER BY faqs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION match_faqs TO service_role;
GRANT EXECUTE ON FUNCTION match_faqs TO authenticated;
```

#### faq_search_history
**用途**: 搜尋歷史追蹤

```sql
CREATE TABLE public.faq_search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Query
    query TEXT NOT NULL,
    query_embedding VECTOR(1536),
    
    -- Results
    results_count INTEGER,
    top_result_id UUID REFERENCES public.faqs(id),
    
    -- User feedback
    user_feedback VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE public.faq_search_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_faq_search_history_all" ON public.faq_search_history
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_faq_search_history_read" ON public.faq_search_history
    FOR SELECT
    TO authenticated
    USING (true);
```

#### faq_categories
**用途**: FAQ 分類

```sql
CREATE TABLE public.faq_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES public.faq_categories(id),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE public.faq_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_faq_categories_all" ON public.faq_categories
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_faq_categories_read" ON public.faq_categories
    FOR SELECT
    TO authenticated
    USING (true);
```

---

### 3. Vector Search Tables

#### embeddings
**用途**: 通用 vector embeddings 儲存

```sql
CREATE TABLE public.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    
    -- Content
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(source_type, source_id)
);

-- RLS Policies (Migration 014)
ALTER TABLE public.embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_embeddings_all" ON public.embeddings
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_embeddings_read" ON public.embeddings
    FOR SELECT
    TO authenticated
    USING (true);

-- Vector search index
CREATE INDEX idx_embeddings_vector ON public.embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Source lookup
CREATE INDEX idx_embeddings_source ON public.embeddings(source_type, source_id);
```

**source_type 範例**:
- `faq`: FAQ 內容
- `documentation`: 文檔
- `code`: 程式碼片段
- `issue`: GitHub Issues
- `pr`: Pull Requests

#### vector_queries
**用途**: Vector 查詢記錄

```sql
CREATE TABLE public.vector_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Query
    query_text TEXT NOT NULL,
    query_embedding VECTOR(1536) NOT NULL,
    
    -- Results
    results_count INTEGER,
    top_results JSONB,
    
    -- Performance
    execution_time_ms INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE public.vector_queries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_vector_queries_all" ON public.vector_queries
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_vector_queries_read" ON public.vector_queries
    FOR SELECT
    TO authenticated
    USING (true);
```

---

### 4. Performance Monitoring Tables

#### trace_metrics
**用途**: 效能追蹤指標

```sql
CREATE TABLE public.trace_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Trace info
    trace_id VARCHAR(255) NOT NULL,
    span_id VARCHAR(255),
    parent_span_id VARCHAR(255),
    
    -- Operation
    operation_name VARCHAR(255) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    
    -- Timing
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time)) * 1000
    ) STORED,
    
    -- Status
    status VARCHAR(50) DEFAULT 'ok',
    error_message TEXT,
    
    -- Metadata
    tags JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies (Migration 014)
ALTER TABLE public.trace_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_trace_metrics_all" ON public.trace_metrics
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_trace_metrics_read" ON public.trace_metrics
    FOR SELECT
    TO authenticated
    USING (true);

-- Indexes
CREATE INDEX idx_trace_metrics_trace_id ON public.trace_metrics(trace_id);
CREATE INDEX idx_trace_metrics_service_time ON public.trace_metrics(service_name, start_time DESC);
CREATE INDEX idx_trace_metrics_operation ON public.trace_metrics(operation_name, start_time DESC);
```

**operation_name 範例**:
- `api.request`: API 請求
- `db.query`: 資料庫查詢
- `agent.execute`: Agent 執行
- `llm.call`: LLM API 呼叫
- `vector.search`: Vector 搜尋

#### alerts
**用途**: 系統告警

```sql
CREATE TABLE public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Source
    source_service VARCHAR(100),
    source_metric VARCHAR(100),
    
    -- Threshold
    threshold_value DECIMAL(10,2),
    actual_value DECIMAL(10,2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'open',
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES public.users(id),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_alerts_all" ON public.alerts
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_alerts_read" ON public.alerts
    FOR SELECT
    TO authenticated
    USING (true);

-- Indexes
CREATE INDEX idx_alerts_status_created ON public.alerts(status, created_at DESC);
CREATE INDEX idx_alerts_severity ON public.alerts(severity, created_at DESC);
```

**severity 層級**:
- `critical`: P0 - 立即處理
- `high`: P1 - 1 小時內處理
- `medium`: P2 - 24 小時內處理
- `low`: P3 - 本週內處理

---

### 5. Agent Reputation Tables

#### agent_reputation
**用途**: Agent 表現評分

```sql
CREATE TABLE public.agent_reputation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent info
    agent_id UUID NOT NULL UNIQUE,
    agent_type VARCHAR(50) NOT NULL,
    
    -- Reputation scores
    overall_score INTEGER DEFAULT 100,
    reliability_score INTEGER DEFAULT 100,
    quality_score INTEGER DEFAULT 100,
    efficiency_score INTEGER DEFAULT 100,
    
    -- Statistics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    
    -- Performance
    avg_execution_time_ms INTEGER,
    avg_cost_per_execution DECIMAL(10,4),
    
    -- Permission level
    permission_level VARCHAR(50) DEFAULT 'standard',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies (Migration 014)
ALTER TABLE public.agent_reputation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_agent_reputation_all" ON public.agent_reputation
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_agent_reputation_read" ON public.agent_reputation
    FOR SELECT
    TO authenticated
    USING (true);

-- Indexes
CREATE INDEX idx_agent_reputation_score ON public.agent_reputation(overall_score DESC);
CREATE INDEX idx_agent_reputation_type ON public.agent_reputation(agent_type, overall_score DESC);
```

**permission_level 選項**:
- `restricted`: 受限權限 (score < 50)
- `standard`: 標準權限 (50 ≤ score < 80)
- `elevated`: 提升權限 (80 ≤ score < 95)
- `trusted`: 信任權限 (score ≥ 95)

**Reputation Update Function**:
```sql
CREATE OR REPLACE FUNCTION update_agent_reputation(
    p_agent_id UUID,
    p_score_delta INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.agent_reputation
    SET 
        overall_score = GREATEST(0, LEAST(100, overall_score + p_score_delta)),
        updated_at = NOW()
    WHERE agent_id = p_agent_id;
    
    -- Update permission level based on new score
    PERFORM update_permission_level(p_agent_id);
END;
$$;

GRANT EXECUTE ON FUNCTION update_agent_reputation TO service_role;
```

#### reputation_events
**用途**: Reputation 變更事件

```sql
CREATE TABLE public.reputation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent
    agent_id UUID NOT NULL,
    
    -- Event
    event_type VARCHAR(50) NOT NULL,
    score_delta INTEGER NOT NULL,
    reason TEXT,
    
    -- Context
    execution_id UUID,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE public.reputation_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_reputation_events_all" ON public.reputation_events
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_reputation_events_read" ON public.reputation_events
    FOR SELECT
    TO authenticated
    USING (true);

-- Indexes
CREATE INDEX idx_reputation_events_agent ON public.reputation_events(agent_id, created_at DESC);
CREATE INDEX idx_reputation_events_type ON public.reputation_events(event_type, created_at DESC);
```

**event_type 範例**:
- `execution_success`: 執行成功 (+5)
- `execution_failure`: 執行失敗 (-10)
- `test_pass`: 測試通過 (+3)
- `test_fail`: 測試失敗 (-5)
- `ci_break`: CI 破壞 (-20)
- `ci_fix`: CI 修復 (+15)
- `cost_overrun`: 成本超支 (-8)
- `cost_efficient`: 成本節省 (+5)

---

### 6. Materialized Views

#### daily_cost_summary
**用途**: 每日成本彙總

```sql
CREATE MATERIALIZED VIEW public.daily_cost_summary AS
SELECT
    tenant_id,
    DATE(created_at) AS date,
    resource_type,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM public.costs
GROUP BY tenant_id, DATE(created_at), resource_type;

-- RLS Policies (Migration 017)
ALTER MATERIALIZED VIEW public.daily_cost_summary ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_daily_cost_summary_all" ON public.daily_cost_summary
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_daily_cost_summary_read" ON public.daily_cost_summary
    FOR SELECT
    TO authenticated
    USING (true);

-- Indexes
CREATE UNIQUE INDEX idx_daily_cost_summary_unique 
    ON public.daily_cost_summary(tenant_id, date, resource_type);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_daily_cost_summary()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.daily_cost_summary;
END;
$$;

GRANT EXECUTE ON FUNCTION refresh_daily_cost_summary TO service_role;
```

**Refresh Schedule**: 每日 00:00 UTC (cron job)

#### vector_visualization
**用途**: Vector 搜尋視覺化

```sql
CREATE MATERIALIZED VIEW public.vector_visualization AS
SELECT
    id,
    source_type,
    source_id,
    content,
    -- PCA dimensionality reduction (simplified)
    embedding[1:3] AS embedding_3d,
    metadata,
    created_at
FROM public.embeddings
WHERE embedding IS NOT NULL;

-- RLS Policies (Migration 017)
ALTER MATERIALIZED VIEW public.vector_visualization ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_vector_visualization_all" ON public.vector_visualization
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "authenticated_vector_visualization_read" ON public.vector_visualization
    FOR SELECT
    TO authenticated
    USING (true);
```

---

## 🔒 Row Level Security (RLS) 架構

### RLS Policy 模式

MorningAI 實作了 **兩層 RLS 保護**:

1. **Service Role**: 完整存取 (backend services)
2. **Authenticated**: 唯讀存取 (dashboard users)
3. **Anonymous**: 無存取 (blocked by RLS)

### Policy 範本

```sql
-- Pattern 1: Service Role Full Access
CREATE POLICY "service_role_<table>_all" ON public.<table>
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Pattern 2: Authenticated Read-Only
CREATE POLICY "authenticated_<table>_read" ON public.<table>
    FOR SELECT
    TO authenticated
    USING (true);

-- Pattern 3: Tenant Isolation (for multi-tenant tables)
CREATE POLICY "tenant_isolation" ON public.<table>
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Pattern 4: Owner Bypass (for platform admin)
CREATE POLICY "owner_access" ON public.<table>
    FOR ALL
    USING (
        current_setting('app.current_role') = 'owner'
        OR tenant_id = current_setting('app.current_tenant_id')::uuid
    );
```

### RLS Protected Tables (Migration 014-017)

**完整保護的 Tables** (18 policies):

1. ✅ `faqs` - 2 policies (service_role + authenticated)
2. ✅ `faq_search_history` - 2 policies
3. ✅ `faq_categories` - 2 policies
4. ✅ `embeddings` - 2 policies
5. ✅ `vector_queries` - 2 policies
6. ✅ `trace_metrics` - 2 policies
7. ✅ `alerts` - 2 policies
8. ✅ `agent_reputation` - 2 policies
9. ✅ `reputation_events` - 2 policies
10. ✅ `daily_cost_summary` (materialized view) - 2 policies
11. ✅ `vector_visualization` (materialized view) - 2 policies

**待補充的 Tables** (需要 tenant_id isolation):
- ⚠️ `tenants` - 需要 owner_access policy
- ⚠️ `users` - 需要 tenant_isolation + owner_access
- ⚠️ `strategies` - 需要 tenant_isolation
- ⚠️ `decisions` - 需要 tenant_isolation
- ⚠️ `costs` - 需要 tenant_isolation
- ⚠️ `audit_logs` - 需要 tenant_isolation + owner_access

---

## 🔍 Database Functions

### Vector Search Functions

#### match_faqs()
**用途**: FAQ 語義搜尋

```sql
CREATE OR REPLACE FUNCTION match_faqs(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    filter_language VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    similarity FLOAT
)
```

**使用範例**:
```sql
-- Search for FAQs similar to a query
SELECT * FROM match_faqs(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_threshold := 0.75,
    match_count := 10,
    filter_language := 'en'
);
```

### Reputation Functions

#### update_agent_reputation()
**用途**: 更新 agent reputation score

```sql
CREATE OR REPLACE FUNCTION update_agent_reputation(
    p_agent_id UUID,
    p_score_delta INTEGER
)
RETURNS VOID
```

#### record_reputation_event()
**用途**: 記錄 reputation 變更事件

```sql
CREATE OR REPLACE FUNCTION record_reputation_event(
    p_agent_id UUID,
    p_event_type TEXT,
    p_score_delta INTEGER,
    p_reason TEXT DEFAULT NULL,
    p_execution_id UUID DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID
```

#### get_agent_reputation_summary()
**用途**: 取得 agent reputation 摘要

```sql
CREATE OR REPLACE FUNCTION get_agent_reputation_summary(
    p_agent_id UUID
)
RETURNS TABLE (
    agent_id UUID,
    agent_type VARCHAR,
    overall_score INTEGER,
    permission_level VARCHAR,
    total_executions INTEGER,
    success_rate DECIMAL,
    recent_events JSONB
)
```

### Utility Functions

#### refresh_daily_cost_summary()
**用途**: 刷新成本彙總 materialized view

```sql
CREATE OR REPLACE FUNCTION refresh_daily_cost_summary()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.daily_cost_summary;
END;
$$;
```

---

## 📈 Indexes 策略

### Vector Indexes (IVFFlat)

```sql
-- FAQ embeddings
CREATE INDEX idx_faqs_embedding ON public.faqs 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- General embeddings
CREATE INDEX idx_embeddings_vector ON public.embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

**IVFFlat 參數**:
- `lists = 100`: 適合 10,000-100,000 rows
- `lists = 1000`: 適合 100,000-1,000,000 rows

### B-tree Indexes

```sql
-- Tenant isolation
CREATE INDEX idx_users_tenant ON public.users(tenant_id);
CREATE INDEX idx_strategies_tenant ON public.strategies(tenant_id);
CREATE INDEX idx_decisions_tenant ON public.decisions(tenant_id);
CREATE INDEX idx_costs_tenant ON public.costs(tenant_id);

-- Time-series queries
CREATE INDEX idx_costs_tenant_period ON public.costs(tenant_id, billing_period);
CREATE INDEX idx_audit_logs_tenant_created ON public.audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_trace_metrics_service_time ON public.trace_metrics(service_name, start_time DESC);

-- Lookups
CREATE INDEX idx_embeddings_source ON public.embeddings(source_type, source_id);
CREATE INDEX idx_trace_metrics_trace_id ON public.trace_metrics(trace_id);
```

### Full-Text Search Indexes (GIN)

```sql
-- FAQ full-text search
CREATE INDEX idx_faqs_search ON public.faqs 
    USING gin(to_tsvector('english', question || ' ' || answer));

-- JSONB indexes
CREATE INDEX idx_strategies_config ON public.strategies USING gin(agent_config);
CREATE INDEX idx_costs_details ON public.costs USING gin(details);
```

---

## 🔧 Database Extensions

### pgvector
**用途**: Vector similarity search

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Vector operations
-- <=> : Cosine distance
-- <-> : L2 distance
-- <#> : Inner product

-- Example: Find similar embeddings
SELECT id, content, 1 - (embedding <=> query_embedding) AS similarity
FROM embeddings
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

### pg_stat_statements
**用途**: Query performance monitoring

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT 
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

### pg_trgm
**用途**: Fuzzy text search

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Fuzzy search on FAQ questions
SELECT question, similarity(question, 'how to deploy') AS sim
FROM faqs
WHERE question % 'how to deploy'
ORDER BY sim DESC;
```

---

## 📊 Migration History

### Migration Timeline

```
001-003: Initial RLS setup (agent_tasks, multi-tenant tables)
004-006: RLS policy refinement (tenant isolation)
007-008: Function and extension security fixes
009: Dev agent tables RLS
010: Embeddings tables (pgvector)
011: Trace metrics tables
012: Agent reputation system + vector visualization
013: Supabase AI extensions
014: Enable RLS for all public tables (9 tables, 18 policies) ✅
015: Fix Security Advisor warnings (anon access)
016: Fix remaining security warnings
017: Enable RLS for materialized views ✅
```

### Migration 014 Impact

**Before**:
- 10 Supabase Security Advisor errors
- Tables without RLS protection
- Anonymous access allowed

**After**:
- 0 Security Advisor errors ✅
- 9 tables with RLS enabled
- 18 policies created
- Anonymous access blocked

**Protected Tables**:
1. faqs
2. faq_search_history
3. faq_categories
4. embeddings
5. vector_queries
6. trace_metrics
7. alerts
8. agent_reputation
9. reputation_events

### Migration 017 Impact

**Before**:
- Materialized views without RLS
- Security Advisor warnings

**After**:
- 2 materialized views with RLS ✅
- 4 policies created
- Security warnings resolved

**Protected Views**:
1. daily_cost_summary
2. vector_visualization

---

## 🎯 Database 效能優化

### Query Optimization

**1. Use Indexes**:
```sql
-- Bad: Full table scan
SELECT * FROM costs WHERE tenant_id = '...';

-- Good: Index scan
-- (already has idx_costs_tenant)
```

**2. Limit Result Sets**:
```sql
-- Bad: Return all rows
SELECT * FROM audit_logs WHERE tenant_id = '...';

-- Good: Paginate
SELECT * FROM audit_logs 
WHERE tenant_id = '...'
ORDER BY created_at DESC
LIMIT 50 OFFSET 0;
```

**3. Use Materialized Views**:
```sql
-- Bad: Aggregate on every request
SELECT DATE(created_at), SUM(amount)
FROM costs
WHERE tenant_id = '...'
GROUP BY DATE(created_at);

-- Good: Use materialized view
SELECT date, total_amount
FROM daily_cost_summary
WHERE tenant_id = '...';
```

### Connection Pooling

**Recommended**: PgBouncer or Supabase connection pooling

```
Application → Connection Pool (100 connections) → PostgreSQL (20 connections)
```

**Benefits**:
- Reduce connection overhead
- Handle connection spikes
- Improve latency

### Vacuum and Analyze

```sql
-- Regular maintenance
VACUUM ANALYZE public.costs;
VACUUM ANALYZE public.audit_logs;

-- Auto-vacuum settings (postgresql.conf)
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
```

---

## 🚨 Security Best Practices

### 1. Always Use RLS

```sql
-- Enable RLS on all tables
ALTER TABLE public.<table> ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "service_role_all" ON public.<table>
    FOR ALL TO service_role USING (true);
```

### 2. Validate Input

```sql
-- Use parameterized queries
SELECT * FROM users WHERE email = $1;  -- Good
SELECT * FROM users WHERE email = 'user@example.com';  -- Bad (SQL injection risk)
```

### 3. Audit Sensitive Operations

```sql
-- Log all changes to audit_logs
CREATE TRIGGER audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.strategies
FOR EACH ROW EXECUTE FUNCTION log_audit();
```

### 4. Encrypt Sensitive Data

```sql
-- Use pgcrypto for sensitive fields
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt API keys
INSERT INTO secrets (key, value)
VALUES ('api_key', pgp_sym_encrypt('secret_value', 'encryption_key'));
```

### 5. Limit Permissions

```sql
-- Grant minimal permissions
GRANT SELECT ON public.faqs TO authenticated;
GRANT ALL ON public.faqs TO service_role;

-- Revoke unnecessary permissions
REVOKE ALL ON public.users FROM anon;
```

---

## 📝 總結

MorningAI 的資料庫架構展現了**生產級 SaaS 平台**的完整設計:

### 優勢 ✅

1. **完整的 RLS 保護**
   - 9+ tables with RLS enabled
   - 18+ policies (service_role + authenticated)
   - Materialized views 也有 RLS

2. **Vector Search 能力**
   - pgvector extension
   - IVFFlat indexes
   - Semantic search functions

3. **效能監控**
   - Trace metrics
   - Alerts system
   - Materialized views for aggregations

4. **Agent Reputation**
   - Reputation scoring
   - Permission levels
   - Event tracking

5. **Audit & Compliance**
   - Comprehensive audit logs
   - GDPR-ready data model
   - Tenant isolation

### 待改進 ⚠️

1. **Multi-tenant Tables RLS**
   - `tenants`, `users`, `strategies` 等需要 tenant_isolation policies
   - 目前只有 FAQ/Vector/Monitoring tables 有完整 RLS

2. **Connection Pooling**
   - 需要設定 PgBouncer 或 Supabase pooling
   - 避免 connection exhaustion

3. **Backup & Recovery**
   - 需要自動化備份策略
   - Point-in-time recovery (PITR)

4. **Read Replicas**
   - 考慮設定 read replicas
   - 分離讀寫流量

5. **Monitoring**
   - 設定 pg_stat_statements
   - 監控 slow queries
   - Alert on connection limits

---

**文檔版本**: v1.0  
**最後更新**: 2025-10-24  
**維護者**: Devin AI
