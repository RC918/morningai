
CREATE TABLE IF NOT EXISTS user_2fa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT FALSE,
    secret_encrypted TEXT NOT NULL,  -- Fernet encrypted TOTP secret (AES-128-CBC + HMAC-SHA256)
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_2fa_user_id ON user_2fa(user_id);
CREATE INDEX IF NOT EXISTS idx_user_2fa_enabled ON user_2fa(enabled);

COMMENT ON TABLE user_2fa IS 'Stores TOTP secrets and 2FA configuration for users';
COMMENT ON COLUMN user_2fa.secret_encrypted IS 'Fernet encrypted TOTP secret (AES-128-CBC + HMAC-SHA256, Base32)';
COMMENT ON COLUMN user_2fa.enabled IS 'Whether 2FA is enabled and verified for this user';
COMMENT ON COLUMN user_2fa.verified_at IS 'When the user successfully verified their TOTP setup';
COMMENT ON COLUMN user_2fa.last_used_at IS 'Last time user successfully used TOTP to login';

CREATE TABLE IF NOT EXISTS totp_backup_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,  -- Argon2id hash
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backup_codes_user_id ON totp_backup_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_backup_codes_used ON totp_backup_codes(used);
CREATE INDEX IF NOT EXISTS idx_backup_codes_user_unused ON totp_backup_codes(user_id, used) WHERE used = FALSE;

COMMENT ON TABLE totp_backup_codes IS 'Stores backup recovery codes for 2FA (single-use, Argon2 hashed)';
COMMENT ON COLUMN totp_backup_codes.code_hash IS 'Argon2id hash of backup code (memory=65536, iterations=3, parallelism=4)';
COMMENT ON COLUMN totp_backup_codes.used IS 'Whether this backup code has been used (single-use only)';

CREATE TABLE IF NOT EXISTS trusted_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint TEXT NOT NULL,
    device_name TEXT,
    trusted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,  -- 30 days from trusted_at
    last_used_at TIMESTAMP,
    UNIQUE(user_id, device_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_trusted_devices_user_id ON trusted_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_trusted_devices_expires ON trusted_devices(expires_at);
CREATE INDEX IF NOT EXISTS idx_trusted_devices_fingerprint ON trusted_devices(device_fingerprint);

COMMENT ON TABLE trusted_devices IS 'Stores trusted devices for "Remember this device" feature (30-day expiry)';
COMMENT ON COLUMN trusted_devices.device_fingerprint IS 'Browser/device fingerprint (user agent + IP + other factors)';
COMMENT ON COLUMN trusted_devices.expires_at IS 'When this trusted device token expires (30 days from trusted_at)';

CREATE OR REPLACE FUNCTION cleanup_expired_trusted_devices()
RETURNS void AS $$
BEGIN
    DELETE FROM trusted_devices WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_trusted_devices IS 'Removes expired trusted device entries (should be run periodically)';
