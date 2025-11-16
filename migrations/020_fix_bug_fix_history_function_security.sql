--
--

-- ============================================================================
-- ============================================================================
DO $$ 
BEGIN 
    RAISE NOTICE 'Migration 010: Fix update_bug_fix_history_modtime function security';
    RAISE NOTICE 'Target: public.update_bug_fix_history_modtime()';
    RAISE NOTICE 'Changes: Add SECURITY DEFINER + SET search_path TO public, pg_temp';
END $$;

-- ============================================================================
-- ============================================================================

DROP FUNCTION IF EXISTS public.update_bug_fix_history_modtime() CASCADE;

CREATE OR REPLACE FUNCTION public.update_bug_fix_history_modtime()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public, pg_temp
AS $function$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$function$;

COMMENT ON FUNCTION public.update_bug_fix_history_modtime() IS 
'Trigger function to update updated_at timestamp. SECURITY DEFINER with safe search_path to prevent search_path injection attacks.';

-- ============================================================================
-- ============================================================================

DO $$ 
DECLARE
    trigger_info RECORD;
BEGIN
    FOR trigger_info IN 
        SELECT DISTINCT 
            event_object_schema,
            event_object_table,
            trigger_name
        FROM information_schema.triggers
        WHERE action_statement LIKE '%update_bug_fix_history_modtime%'
    LOOP
        RAISE NOTICE 'Found trigger: %.% on %.%', 
            trigger_info.event_object_schema,
            trigger_info.trigger_name,
            trigger_info.event_object_schema,
            trigger_info.event_object_table;
    END LOOP;
    
END $$;

DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'bug_fix_history'
    ) THEN
        DROP TRIGGER IF EXISTS update_bug_fix_history_modtime_trigger ON public.bug_fix_history;
        
        CREATE TRIGGER update_bug_fix_history_modtime_trigger
        BEFORE UPDATE ON public.bug_fix_history
        FOR EACH ROW
        EXECUTE FUNCTION public.update_bug_fix_history_modtime();
        
        RAISE NOTICE 'Recreated trigger on public.bug_fix_history';
    ELSE
        RAISE NOTICE 'Table public.bug_fix_history does not exist, skipping trigger creation';
    END IF;
END $$;

-- ============================================================================
-- ============================================================================

DO $$ 
DECLARE
    func_secdef BOOLEAN;
    func_config TEXT;
BEGIN
    SELECT 
        p.prosecdef,
        array_to_string(p.proconfig, ', ')
    INTO func_secdef, func_config
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.proname = 'update_bug_fix_history_modtime';
    
    IF func_secdef IS NULL THEN
        RAISE EXCEPTION 'Function public.update_bug_fix_history_modtime() not found!';
    END IF;
    
    IF NOT func_secdef THEN
        RAISE EXCEPTION 'Function is not SECURITY DEFINER!';
    END IF;
    
    IF func_config NOT LIKE '%search_path=public, pg_temp%' THEN
        RAISE EXCEPTION 'Function does not have safe search_path! Current: %', func_config;
    END IF;
    
    RAISE NOTICE '✓ Function verification passed';
    RAISE NOTICE '  - SECURITY DEFINER: %', func_secdef;
    RAISE NOTICE '  - search_path: %', func_config;
END $$;

-- ============================================================================
-- ============================================================================

DO $$ 
BEGIN 
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Migration 010 completed successfully!';
    RAISE NOTICE 'Fixed: public.update_bug_fix_history_modtime()';
    RAISE NOTICE 'Expected result: Supabase Security Advisor = 0 warnings';
    RAISE NOTICE '============================================================';
END $$;
