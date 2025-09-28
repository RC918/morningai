-- Phase 3 Migration: 增強多租戶與平台整合相關功能

-- 1. 在 tenants 表中增加更多元數據，用於個性化和分析
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS industry VARCHAR(255);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS region VARCHAR(100);
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) DEFAULT 'standard';

-- 2. 創建 platform_bindings 表來管理多平台整合
CREATE TABLE IF NOT EXISTS platform_bindings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- e.g., 'telegram', 'line', 'messenger'
    platform_user_id VARCHAR(255), -- e.g., Bot ID
    access_token TEXT NOT NULL, -- 加密存儲
    webhook_url TEXT,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL, -- e.g., 'pending', 'active', 'failed'
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, platform)
);

-- 3. 創建一個 trigger 自動更新 updated_at 時間戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_platform_bindings_updated_at
BEFORE UPDATE ON platform_bindings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 4. 在 users 表中增加最後活躍時間，用於用戶行為分析
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ;

-- 5. 創建 integrations 表，用於支持 Zapier/IFTTT 等外部自動化
CREATE TABLE IF NOT EXISTS external_integrations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL, -- e.g., 'zapier', 'ifttt', 'slack'
    api_key TEXT, -- 加密存儲
    config JSONB, -- 存儲特定整合的配置
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_external_integrations_updated_at
BEFORE UPDATE ON external_integrations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 6. 增加索引以優化查詢性能
CREATE INDEX IF NOT EXISTS idx_platform_bindings_tenant_id ON platform_bindings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_external_integrations_tenant_id ON external_integrations(tenant_id);

-- End of Phase 3 Migration


