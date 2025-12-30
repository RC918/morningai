-- ============================================================================
-- CI Bootstrap SQL for RLS Audit Testing
-- ============================================================================
--
-- This script creates a minimal test schema for validating the RLS audit script.
-- It includes:
-- 1. Supabase-compatible auth infrastructure (schema, roles, functions)
-- 2. Sample tables with various RLS configurations for testing audit logic
--
-- NOTE: This is NOT a production schema. It's designed to test the audit script's
-- ability to detect RLS issues (missing RLS, missing policies, overly permissive
-- policies, etc.)
--
-- Usage:
--   psql $DATABASE_URL -f scripts/ci/bootstrap_rls_test_db.sql
--
-- ============================================================================

-- Create extensions schema
CREATE SCHEMA IF NOT EXISTS extensions;

-- Create auth schema (Supabase compatibility)
CREATE SCHEMA IF NOT EXISTS auth;

-- ============================================================================
-- Supabase auth functions (stubs)
-- ============================================================================

CREATE OR REPLACE FUNCTION auth.uid()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$
  SELECT NULLIF(current_setting('request.jwt.claims.sub', true), '')::uuid
$$;

CREATE OR REPLACE FUNCTION auth.role()
RETURNS text
LANGUAGE sql
STABLE
AS $$
  SELECT current_setting('request.jwt.claims.role', true)
$$;

CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS json
LANGUAGE sql
STABLE
AS $$
  SELECT '{}'::json
$$;

-- ============================================================================
-- Supabase roles
-- ============================================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN BYPASSRLS;
  END IF;
END
$$;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA extensions TO anon, authenticated, service_role;

-- Grant execute on auth functions
GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.role() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.jwt() TO anon, authenticated, service_role;

-- ============================================================================
-- Sample tables for RLS audit testing
-- ============================================================================

-- Table 1: tenants (RLS enabled with proper policies)
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    created_at timestamptz DEFAULT now()
);
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all_tenants" ON tenants FOR ALL TO service_role USING (true);

-- Table 2: users (RLS enabled with tenant isolation)
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id),
    email text UNIQUE NOT NULL,
    created_at timestamptz DEFAULT now()
);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all_users" ON users FOR ALL TO service_role USING (true);
CREATE POLICY "users_true_tenant_isolation" ON users FOR SELECT TO authenticated
    USING (tenant_id = current_user_tenant_id());

-- Table 3: agent_tasks (RLS enabled with tenant isolation)
CREATE TABLE IF NOT EXISTS agent_tasks (
    task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id),
    trace_id uuid,
    question text,
    status text DEFAULT 'pending',
    created_at timestamptz DEFAULT now()
);
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all_agent_tasks" ON agent_tasks FOR ALL TO service_role USING (true);
CREATE POLICY "agent_tasks_true_tenant_isolation" ON agent_tasks FOR SELECT TO authenticated
    USING (tenant_id = current_user_tenant_id());

-- Table 4: user_profiles (RLS enabled with proper policies)
CREATE TABLE IF NOT EXISTS user_profiles (
    id uuid PRIMARY KEY REFERENCES users(id),
    is_platform_admin boolean DEFAULT false,
    created_at timestamptz DEFAULT now()
);
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all_user_profiles" ON user_profiles FOR ALL TO service_role USING (true);

-- Helper function: current_user_tenant_id()
CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
  RETURN (SELECT tenant_id FROM public.users WHERE id = auth.uid());
EXCEPTION
  WHEN undefined_table THEN
    RETURN NULL;
END;
$$;

GRANT EXECUTE ON FUNCTION current_user_tenant_id() TO authenticated;

-- Grant table access to roles
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- ============================================================================
-- Bootstrap complete
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '
============================================================================
  CI Bootstrap Complete (RLS Audit Test Schema)
============================================================================
  Created:
  - auth schema with uid(), role(), jwt() stubs
  - Supabase roles: anon, authenticated, service_role
  - Sample tables: tenants, users, agent_tasks, user_profiles
  - All tables have RLS enabled with proper policies
  - current_user_tenant_id() helper function

  Ready for RLS audit testing.
============================================================================
';
END $$;
