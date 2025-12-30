-- ============================================================================
-- CI Bootstrap SQL for RLS Testing
-- ============================================================================
--
-- This script creates the necessary Supabase-like infrastructure in a vanilla
-- PostgreSQL database for CI testing. It provides ONLY Supabase primitives:
-- 1. auth schema with uid(), role(), jwt() stub functions
-- 2. auth.users table (minimal, for migrations that reference it)
-- 3. Supabase roles (anon, authenticated, service_role)
-- 4. Helper functions used by RLS policies
--
-- IMPORTANT: This script does NOT create application tables or policies.
-- Those are created by migrations to ensure SSOT (Single Source of Truth).
--
-- Usage:
--   psql $DATABASE_URL -f scripts/ci/bootstrap_rls_test_db.sql
--
-- ============================================================================

-- Create extensions schema (for pgvector and other extensions)
CREATE SCHEMA IF NOT EXISTS extensions;

-- Create auth schema (Supabase compatibility)
CREATE SCHEMA IF NOT EXISTS auth;

-- ============================================================================
-- auth.users table (minimal stub for migrations that reference it)
-- ============================================================================
-- This is a minimal version of Supabase's auth.users table.
-- Only includes columns that migrations actually SELECT from.

CREATE TABLE IF NOT EXISTS auth.users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text,
    raw_user_meta_data jsonb DEFAULT '{}'::jsonb,
    deleted_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- ============================================================================
-- Supabase auth functions (stubs)
-- ============================================================================

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

-- Grant schema usage to roles
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA extensions TO anon, authenticated, service_role;

-- Grant execute on auth functions
GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.role() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.jwt() TO anon, authenticated, service_role;

-- Grant SELECT on auth.users (some migrations reference it)
GRANT SELECT ON auth.users TO anon, authenticated, service_role;

-- ============================================================================
-- Helper function: current_user_tenant_id()
-- ============================================================================
-- This function is used by RLS policies to get the tenant_id of the current user.
-- Create a placeholder that returns NULL (will work once 'users' table exists).

CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
  -- Try to get tenant_id from users table if it exists
  RETURN (
    SELECT tenant_id FROM public.users WHERE id = auth.uid()
  );
EXCEPTION
  WHEN undefined_table THEN
    RETURN NULL;
END;
$$;

-- Grant execute on helper function
GRANT EXECUTE ON FUNCTION current_user_tenant_id() TO authenticated;

-- ============================================================================
-- Extension stubs (for migrations that CREATE EXTENSION IF NOT EXISTS)
-- ============================================================================
-- Note: pgvector must be installed in the PostgreSQL image.
-- Use pgvector/pgvector:pg15 image in CI.

-- Try to create vector extension (will fail gracefully if not available)
DO $$
BEGIN
  CREATE EXTENSION IF NOT EXISTS vector SCHEMA extensions;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'pgvector extension not available, skipping...';
END
$$;

-- Create other common extensions
DO $$
BEGIN
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'pg_trgm extension not available, skipping...';
END
$$;

-- ============================================================================
-- Bootstrap complete
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '
============================================================================
  CI Bootstrap Complete (Supabase Primitives Only)
============================================================================
  Created:
  - auth schema with uid(), role(), jwt() stubs
  - auth.users table (minimal stub)
  - Supabase roles: anon, authenticated, service_role
  - current_user_tenant_id() placeholder function
  - extensions schema

  Application tables and RLS policies will be created by migrations.
============================================================================
';
END $$;
