
DO $$
DECLARE
    default_tenant_id UUID := '00000000-0000-0000-0000-000000000001';
    user_record RECORD;
    inserted_count INTEGER := 0;
    skipped_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Starting user_profiles backfill process...';
    RAISE NOTICE 'Default tenant ID: %', default_tenant_id;
    
    FOR user_record IN 
        SELECT id, email, raw_user_meta_data->>'full_name' AS full_name
        FROM auth.users
        WHERE deleted_at IS NULL
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM user_profiles WHERE id = user_record.id
        ) THEN
            INSERT INTO user_profiles (id, tenant_id, display_name, role)
            VALUES (
                user_record.id,
                default_tenant_id,
                COALESCE(user_record.full_name, split_part(user_record.email, '@', 1)),
                'member'
            );
            
            inserted_count := inserted_count + 1;
            RAISE NOTICE 'Created profile for user: % (email: %)', user_record.id, user_record.email;
        ELSE
            skipped_count := skipped_count + 1;
            RAISE NOTICE 'Skipped user % (profile already exists)', user_record.id;
        END IF;
    END LOOP;
    
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Backfill complete!';
    RAISE NOTICE 'Users assigned to default tenant: %', inserted_count;
    RAISE NOTICE 'Users skipped (already had profile): %', skipped_count;
    RAISE NOTICE '===========================================';
END $$;

SELECT 
    'Verification Results' AS section,
    COUNT(DISTINCT u.id) AS total_auth_users,
    COUNT(DISTINCT up.id) AS total_user_profiles,
    COUNT(DISTINCT CASE WHEN up.tenant_id = '00000000-0000-0000-0000-000000000001' THEN up.id END) AS profiles_in_default_tenant
FROM auth.users u
LEFT JOIN user_profiles up ON u.id = up.id
WHERE u.deleted_at IS NULL;
