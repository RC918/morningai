
SELECT 
    u.id AS user_id,
    u.email,
    u.raw_user_meta_data->>'role' AS role,
    u.created_at AS account_created,
    u.last_sign_in_at AS last_login,
    COALESCE(u2.enabled, FALSE) AS twofa_enabled,
    u2.verified_at AS twofa_verified_at,
    u2.last_used_at AS twofa_last_used,
    CASE 
        WHEN u2.enabled = TRUE THEN '✅ Enabled'
        ELSE '❌ Not Enabled'
    END AS status,
    EXTRACT(DAY FROM (NOW() - u.last_sign_in_at)) AS days_since_last_login,
    CASE 
        WHEN u2.enabled = TRUE THEN 'LOW'
        WHEN u.last_sign_in_at > NOW() - INTERVAL '7 days' THEN 'HIGH'
        WHEN u.last_sign_in_at > NOW() - INTERVAL '30 days' THEN 'MEDIUM'
        ELSE 'LOW (Inactive)'
    END AS risk_level
FROM 
    auth.users u
LEFT JOIN 
    public.user_2fa u2 ON u2.user_id = u.id
WHERE 
    u.raw_user_meta_data->>'role' = 'owner'
    AND u.deleted_at IS NULL  -- Exclude soft-deleted users
ORDER BY 
    u2.enabled ASC NULLS FIRST,  -- Not enabled first
    u.last_sign_in_at DESC NULLS LAST;  -- Most active first

SELECT 
    COUNT(*) AS total_owners,
    SUM(CASE WHEN COALESCE(u2.enabled, FALSE) = TRUE THEN 1 ELSE 0 END) AS owners_with_2fa,
    SUM(CASE WHEN COALESCE(u2.enabled, FALSE) = FALSE THEN 1 ELSE 0 END) AS owners_without_2fa,
    ROUND(
        100.0 * SUM(CASE WHEN COALESCE(u2.enabled, FALSE) = TRUE THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS percent_with_2fa,
    SUM(CASE 
        WHEN u.last_sign_in_at > NOW() - INTERVAL '30 days' 
        AND COALESCE(u2.enabled, FALSE) = FALSE 
        THEN 1 ELSE 0 
    END) AS active_owners_without_2fa,
    SUM(CASE 
        WHEN u.last_sign_in_at < NOW() - INTERVAL '90 days' 
        OR u.last_sign_in_at IS NULL
        THEN 1 ELSE 0 
    END) AS inactive_owners
FROM 
    auth.users u
LEFT JOIN 
    public.user_2fa u2 ON u2.user_id = u.id
WHERE 
    u.raw_user_meta_data->>'role' = 'owner'
    AND u.deleted_at IS NULL;

SELECT 
    u.id AS user_id,
    u.email,
    u.last_sign_in_at AS last_login,
    EXTRACT(DAY FROM (NOW() - u.last_sign_in_at)) AS days_since_last_login,
    u.created_at AS account_age,
    'HIGH RISK: Active owner without 2FA' AS alert
FROM 
    auth.users u
LEFT JOIN 
    public.user_2fa u2 ON u2.user_id = u.id
WHERE 
    u.raw_user_meta_data->>'role' = 'owner'
    AND u.deleted_at IS NULL
    AND COALESCE(u2.enabled, FALSE) = FALSE
    AND u.last_sign_in_at > NOW() - INTERVAL '30 days'
ORDER BY 
    u.last_sign_in_at DESC;

SELECT 
    DATE(u2.verified_at) AS date_enabled,
    COUNT(*) AS owners_enabled_on_date,
    SUM(COUNT(*)) OVER (ORDER BY DATE(u2.verified_at)) AS cumulative_owners_with_2fa
FROM 
    public.user_2fa u2
JOIN 
    auth.users u ON u.id = u2.user_id
WHERE 
    u.raw_user_meta_data->>'role' = 'owner'
    AND u2.enabled = TRUE
    AND u2.verified_at IS NOT NULL
GROUP BY 
    DATE(u2.verified_at)
ORDER BY 
    date_enabled DESC;

SELECT 
    u.id AS user_id,
    u.email,
    COUNT(bc.id) AS total_backup_codes,
    SUM(CASE WHEN bc.used = FALSE THEN 1 ELSE 0 END) AS unused_backup_codes,
    SUM(CASE WHEN bc.used = TRUE THEN 1 ELSE 0 END) AS used_backup_codes,
    MAX(bc.created_at) AS last_regenerated
FROM 
    auth.users u
JOIN 
    public.user_2fa u2 ON u2.user_id = u.id
LEFT JOIN 
    public.totp_backup_codes bc ON bc.user_id = u.id
WHERE 
    u.raw_user_meta_data->>'role' = 'owner'
    AND u2.enabled = TRUE
GROUP BY 
    u.id, u.email
ORDER BY 
    unused_backup_codes ASC;

SELECT 
    u.id AS user_id,
    u.email,
    COUNT(td.id) AS trusted_devices_count,
    MAX(td.trusted_at) AS last_device_trusted,
    MAX(td.last_used_at) AS last_device_used,
    SUM(CASE WHEN td.expires_at > NOW() THEN 1 ELSE 0 END) AS active_trusted_devices,
    SUM(CASE WHEN td.expires_at <= NOW() THEN 1 ELSE 0 END) AS expired_trusted_devices
FROM 
    auth.users u
JOIN 
    public.user_2fa u2 ON u2.user_id = u.id
LEFT JOIN 
    public.trusted_devices td ON td.user_id = u.id
WHERE 
    u.raw_user_meta_data->>'role' = 'owner'
    AND u2.enabled = TRUE
GROUP BY 
    u.id, u.email
ORDER BY 
    trusted_devices_count DESC;

--
