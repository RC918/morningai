-- ============================================================================
-- Migration 026: Create AI Policies Table
-- Phase 6 PR-1: AI Governance Policies
-- ============================================================================
-- This migration creates the ai_policies table for tenant-specific AI usage
-- policies including capability whitelist/blacklist, content filtering,
-- usage limits, and model restrictions.
-- ============================================================================

-- Create enum types for policy management
DO $$ BEGIN
    CREATE TYPE policy_type AS ENUM (
        'capability_whitelist',
        'capability_blacklist',
        'content_filter',
        'usage_limit',
        'rate_limit',
        'model_restriction'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE policy_scope AS ENUM (
        'platform',
        'tenant',
        'user'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE policy_status AS ENUM (
        'active',
        'inactive',
        'draft'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Create ai_policies table
CREATE TABLE IF NOT EXISTS ai_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    policy_type policy_type NOT NULL,
    scope policy_scope NOT NULL DEFAULT 'tenant',
    rules JSONB NOT NULL DEFAULT '{}',
    priority INTEGER NOT NULL DEFAULT 0,
    status policy_status NOT NULL DEFAULT 'draft',
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ai_policies_tenant_id ON ai_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ai_policies_policy_type ON ai_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_ai_policies_status ON ai_policies(status);
CREATE INDEX IF NOT EXISTS idx_ai_policies_priority ON ai_policies(priority DESC);
CREATE INDEX IF NOT EXISTS idx_ai_policies_tenant_status ON ai_policies(tenant_id, status);

-- Enable RLS
ALTER TABLE ai_policies ENABLE ROW LEVEL SECURITY;

-- RLS Policies for tenant isolation
-- Policy: Users can only view policies for their own tenant
CREATE POLICY ai_policies_select_policy ON ai_policies
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_profiles WHERE id = auth.uid()
        )
        OR scope = 'platform'
    );

-- Policy: Only admins and owners can insert policies
CREATE POLICY ai_policies_insert_policy ON ai_policies
    FOR INSERT
    WITH CHECK (
        tenant_id IN (
            SELECT tenant_id FROM user_profiles 
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- Policy: Only admins and owners can update policies
CREATE POLICY ai_policies_update_policy ON ai_policies
    FOR UPDATE
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_profiles 
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- Policy: Only owners can delete policies
CREATE POLICY ai_policies_delete_policy ON ai_policies
    FOR DELETE
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_profiles 
            WHERE id = auth.uid() AND role = 'owner'
        )
    );

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_ai_policies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS ai_policies_updated_at_trigger ON ai_policies;
CREATE TRIGGER ai_policies_updated_at_trigger
    BEFORE UPDATE ON ai_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_policies_updated_at();

-- Add comment for documentation
COMMENT ON TABLE ai_policies IS 'Phase 6: Tenant-specific AI usage policies for governance';
COMMENT ON COLUMN ai_policies.policy_type IS 'Type of policy: whitelist, blacklist, filter, limit, rate_limit, model_restriction';
COMMENT ON COLUMN ai_policies.scope IS 'Scope of application: platform (global), tenant, or user level';
COMMENT ON COLUMN ai_policies.rules IS 'JSON configuration for policy rules';
COMMENT ON COLUMN ai_policies.priority IS 'Priority for conflict resolution (higher = more important)';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Migration 026 Complete                                     ║
║                                                                              ║
║  Created: ai_policies table with RLS policies                                ║
║  - Tenant isolation via RLS                                                  ║
║  - Role-based access control (owner/admin for write, all for read)          ║
║  - Indexes for common query patterns                                         ║
║  - Auto-update trigger for updated_at                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
';
END $$;
