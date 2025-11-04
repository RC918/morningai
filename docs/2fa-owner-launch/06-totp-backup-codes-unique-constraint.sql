-- ============================================================================
-- ============================================================================
--
-- Execute this in Supabase SQL Editor for Staging environment
-- ============================================================================

-- ============================================================================
-- ============================================================================

SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'totp_backup_codes'
  AND constraint_type = 'PRIMARY KEY';

SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'totp_backup_codes'
  AND constraint_type = 'UNIQUE';

SELECT user_id, code_hash, COUNT(*) as count
FROM totp_backup_codes
GROUP BY user_id, code_hash
HAVING COUNT(*) > 1;

-- ============================================================================
-- ============================================================================

/*
DELETE FROM totp_backup_codes
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY user_id, code_hash 
                   ORDER BY created_at ASC
               ) as rn
        FROM totp_backup_codes
    ) t
    WHERE t.rn > 1
);
*/

-- ============================================================================
-- ============================================================================

ALTER TABLE totp_backup_codes 
ADD CONSTRAINT unique_user_code_hash UNIQUE (user_id, code_hash);

-- ============================================================================
-- ============================================================================

SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'totp_backup_codes'
  AND constraint_type = 'UNIQUE';

SELECT kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name = 'totp_backup_codes'
  AND tc.constraint_type = 'UNIQUE'
  AND tc.constraint_name = 'unique_user_code_hash'
ORDER BY kcu.ordinal_position;

-- ============================================================================
-- ============================================================================

/*
INSERT INTO totp_backup_codes (user_id, code_hash, used, created_at)
VALUES (
    'test-user-id',
    'test-code-hash',
    false,
    NOW()
);
*/

/*
INSERT INTO totp_backup_codes (user_id, code_hash, used, created_at)
VALUES (
    'test-user-id',
    'test-code-hash',  -- Same user_id and code_hash
    false,
    NOW()
);
*/

/*
DELETE FROM totp_backup_codes 
WHERE user_id = 'test-user-id' 
  AND code_hash = 'test-code-hash';
*/

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  UNIQUE Constraint Added Successfully ✅                   ║
╠════════════════════════════════════════════════════════════╣
║  Table: totp_backup_codes                                  ║
║  Constraint: unique_user_code_hash                         ║
║  Columns: (user_id, code_hash)                             ║
╠════════════════════════════════════════════════════════════╣
║  Impact:                                                   ║
║  ✅ Prevents duplicate backup codes for same user          ║
║  ✅ Ensures data integrity                                 ║
║  ✅ Aligns with UPDATE logic in auth_enhanced.py           ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Test backup code generation                            ║
║  2. Test backup code usage (single-use enforcement)        ║
║  3. Apply same constraint to Production after testing      ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
