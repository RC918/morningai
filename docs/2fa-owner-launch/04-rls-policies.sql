-- RLS Policies for 2FA Tables
-- Execute this in Supabase SQL Editor for both Staging and Production

-- Enable RLS on all 2FA tables
ALTER TABLE user_2fa ENABLE ROW LEVEL SECURITY;
ALTER TABLE totp_backup_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE trusted_devices ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role full access
-- This allows the backend (using SUPABASE_SERVICE_ROLE_KEY) to perform all operations

-- user_2fa policies
CREATE POLICY "Service role has full access to user_2fa"
ON user_2fa
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- totp_backup_codes policies
CREATE POLICY "Service role has full access to totp_backup_codes"
ON totp_backup_codes
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- trusted_devices policies
CREATE POLICY "Service role has full access to trusted_devices"
ON trusted_devices
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Optional: Add policies for authenticated users to view their own data
-- (if you want to allow direct Supabase client access from frontend)

CREATE POLICY "Users can view their own 2FA status"
ON user_2fa
FOR SELECT
TO authenticated
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own backup codes"
ON totp_backup_codes
FOR SELECT
TO authenticated
USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own trusted devices"
ON trusted_devices
FOR SELECT
TO authenticated
USING (auth.uid()::text = user_id);

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('user_2fa', 'totp_backup_codes', 'trusted_devices');

-- Verify policies are created
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE tablename IN ('user_2fa', 'totp_backup_codes', 'trusted_devices')
ORDER BY tablename, policyname;
