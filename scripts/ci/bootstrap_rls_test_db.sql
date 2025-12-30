-- ============================================================================
-- CI Bootstrap SQL for RLS Testing
-- ============================================================================
-- 
-- This script creates the necessary Supabase-like infrastructure in a vanilla
-- PostgreSQL database for CI testing. It provides:
-- 1. auth schema with uid() and role() stub functions
-- 2. Supabase roles (anon, authenticated, service_role)
-- 3. Helper functions used by RLS policies (current_user_tenant_id)
--
-- Usage:
--   psql $DATABASE_URL -f scripts/ci/bootstrap_rls_test_db.sql
--
-- ============================================================================

-- Create auth schema (Supabase compatibility)
CREATE SCHEMA IF NOT EXISTS auth;

-- Create stub for auth.uid() - returns the JWT sub claim
CREATE OR REPLACE FUNCTION auth.uid() 
RETURNS uuid 
LANGUAGE sql 
STABLE
AS $$
  SELECT NULLIF(current_setting('request.jwt.claims.sub', true), '')::uuid
$$;

-- Create stub for auth.role() - returns the current role
CREATE OR REPLACE FUNCTION auth.role() 
RETURNS text 
LANGUAGE sql 
STABLE
AS $$
  SELECT current_setting('request.jwt.claims.role', true)
$$;

-- Create stub for auth.jwt() - returns empty JSON (not used in most policies)
CREATE OR REPLACE FUNCTION auth.jwt() 
RETURNS json 
LANGUAGE sql 
STABLE
AS $$
  SELECT '{}'::json
$$;

-- Create Supabase roles if they don't exist
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

-- Grant schema usage to roles
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;

-- Grant execute on auth functions
GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.role() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.jwt() TO anon, authenticated, service_role;

-- Create current_user_tenant_id() helper function
-- This is used by RLS policies to get the tenant_id of the current user
CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT tenant_id FROM users WHERE id = auth.uid()
$$;

-- Grant execute on helper function
GRANT EXECUTE ON FUNCTION current_user_tenant_id() TO authenticated;

-- ============================================================================
-- Minimal table structure for RLS testing
-- ============================================================================

-- Create tenants table if not exists
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- Create users table if not exists
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id),
    email text UNIQUE NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- Create user_profiles table if not exists
CREATE TABLE IF NOT EXISTS user_profiles (
    id uuid PRIMARY KEY REFERENCES users(id),
    is_platform_admin boolean DEFAULT false,
    created_at timestamptz DEFAULT now()
);

-- Create agent_tasks table if not exists
CREATE TABLE IF NOT EXISTS agent_tasks (
    task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id),
    trace_id uuid,
    question text,
    status text DEFAULT 'pending',
    created_at timestamptz DEFAULT now()
);

-- Create planner_events table if not exists
CREATE TABLE IF NOT EXISTS planner_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id uuid,
    goal text,
    planner_type text,
    task_type text,
    actual_plan_steps jsonb,
    num_steps integer,
    planning_time_ms numeric,
    timestamp timestamptz DEFAULT now()
);

-- Create memory table if not exists
CREATE TABLE IF NOT EXISTS memory (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key text,
    text text,
    created_at timestamptz DEFAULT now()
);

-- Create error_fix_pairs table if not exists
CREATE TABLE IF NOT EXISTS error_fix_pairs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    error_text text,
    fix_text text,
    created_at timestamptz DEFAULT now()
);

-- Create failure_memory table if not exists
CREATE TABLE IF NOT EXISTS failure_memory (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    text text,
    metadata jsonb,
    created_at timestamptz DEFAULT now()
);

-- Grant table access to roles
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- ============================================================================
-- Enable RLS on all tables (policies will be added by migrations)
-- ============================================================================

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE planner_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_fix_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE failure_memory ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Basic RLS policies for service_role (bypass)
-- ============================================================================

CREATE POLICY "service_role_all_tenants" ON tenants FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_users" ON users FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_user_profiles" ON user_profiles FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_agent_tasks" ON agent_tasks FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_planner_events" ON planner_events FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_memory" ON memory FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_error_fix_pairs" ON error_fix_pairs FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all_failure_memory" ON failure_memory FOR ALL TO service_role USING (true);

-- ============================================================================
-- Bootstrap complete
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '
============================================================================
  CI Bootstrap Complete
============================================================================
  Created:
  - auth schema with uid(), role(), jwt() stubs
  - Supabase roles: anon, authenticated, service_role
  - current_user_tenant_id() helper function
  - Core tables with RLS enabled
  - service_role bypass policies
  
  Ready for migration testing.
============================================================================
';
END $$;
