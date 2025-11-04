-- 


CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = 'pg_temp'
AS $$
BEGIN
    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.update_updated_at_column IS 'Trigger function to auto-update updated_at column (search_path secured)';

CREATE OR REPLACE FUNCTION public.cleanup_expired_trusted_devices()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'pg_temp'
AS $$
BEGIN
    DELETE FROM public.trusted_devices WHERE expires_at < now();
END;
$$;

COMMENT ON FUNCTION public.cleanup_expired_trusted_devices IS 'Removes expired trusted device entries (search_path secured)';


ALTER TABLE public.agents ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."user" ENABLE ROW LEVEL SECURITY;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'agents' 
        AND policyname = 'deny_all_anon_agents'
    ) THEN
        CREATE POLICY deny_all_anon_agents ON public.agents 
        FOR ALL TO anon 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'agents' 
        AND policyname = 'deny_all_auth_agents'
    ) THEN
        CREATE POLICY deny_all_auth_agents ON public.agents 
        FOR ALL TO authenticated 
        USING (false) 
        WITH CHECK (false);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'tasks' 
        AND policyname = 'deny_all_anon_tasks'
    ) THEN
        CREATE POLICY deny_all_anon_tasks ON public.tasks 
        FOR ALL TO anon 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'tasks' 
        AND policyname = 'deny_all_auth_tasks'
    ) THEN
        CREATE POLICY deny_all_auth_tasks ON public.tasks 
        FOR ALL TO authenticated 
        USING (false) 
        WITH CHECK (false);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user' 
        AND policyname = 'deny_all_anon_user'
    ) THEN
        CREATE POLICY deny_all_anon_user ON public."user" 
        FOR ALL TO anon 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user' 
        AND policyname = 'deny_all_auth_user'
    ) THEN
        CREATE POLICY deny_all_auth_user ON public."user" 
        FOR ALL TO authenticated 
        USING (false) 
        WITH CHECK (false);
    END IF;
END $$;


COMMENT ON TABLE public.agents IS 'Agent Registry - RLS enabled, backend service_role access only';
COMMENT ON TABLE public.tasks IS 'Task Router - RLS enabled, backend service_role access only';
COMMENT ON TABLE public."user" IS 'User table - RLS enabled, backend service_role access only';
