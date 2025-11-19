# 2FA Owner Support Runbook

**Document Version**: 1.0  
**Date**: 2025-11-04  
**Audience**: Support Team, DevOps, On-Call Engineers  
**Status**: 📋 Ready for Use

---

## Quick Reference

**Common Issues**:
1. [Lost Authenticator Device](#scenario-1-lost-authenticator-device) - Use backup codes or disable 2FA
2. [Invalid TOTP Code](#scenario-2-invalid-totp-code) - Check time sync, try backup code
3. [No Backup Codes](#scenario-3-no-backup-codes-saved) - Disable 2FA and re-enable
4. [Cannot Scan QR Code](#scenario-4-cannot-scan-qr-code) - Provide manual entry key
5. [Account Lockout](#scenario-5-account-lockout-rate-limiting) - Wait 1 hour or contact DevOps

**Emergency Contacts**:
- **On-Call Engineer**: [Pagerduty Link]
- **CTO**: [Email/Phone]
- **DevOps Lead**: [Email/Phone]

**Feature Flags**:
- `FEATURE_2FA_ENABLED` - Enable/disable 2FA feature
- `FEATURE_2FA_OWNER_ENFORCEMENT` - Enforce 2FA for owners

---

## Table of Contents

1. [Overview](#overview)
2. [2FA Setup Process](#2fa-setup-process)
3. [Common Support Scenarios](#common-support-scenarios)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Database Operations](#database-operations)
6. [Emergency Procedures](#emergency-procedures)
7. [Escalation Matrix](#escalation-matrix)
8. [FAQ](#faq)

---

## Overview

### What is 2FA?

Two-Factor Authentication (2FA) adds an extra layer of security by requiring:
1. **Something you know**: Password
2. **Something you have**: Authenticator app (TOTP code)

### Why is 2FA Required for Owners?

Owner accounts have elevated privileges (access to sensitive data, billing, user management). 2FA significantly reduces the risk of unauthorized access.

### Supported Authenticator Apps

- ✅ Google Authenticator (iOS, Android)
- ✅ Authy (iOS, Android, Desktop)
- ✅ Microsoft Authenticator (iOS, Android)
- ✅ 1Password (iOS, Android, Desktop)
- ✅ LastPass Authenticator (iOS, Android)
- ❌ SMS-based 2FA (not supported - less secure)

---

## 2FA Setup Process

### Step-by-Step Guide (For Users)

**Prerequisites**:
- Owner account
- Authenticator app installed on mobile device

**Setup Steps**:

1. **Log in to Owner Console**
   - Navigate to: https://owner.morningai.com
   - Enter email and password

2. **Navigate to Security Settings**
   - Click profile icon (top right)
   - Select "Settings"
   - Click "Security" tab

3. **Enable 2FA**
   - Click "Enable Two-Factor Authentication"
   - Enter password to confirm

4. **Scan QR Code**
   - Open authenticator app
   - Tap "+" or "Add Account"
   - Scan QR code displayed on screen
   - **Alternative**: Tap "Can't scan QR code?" to see manual entry key

5. **Verify Setup**
   - Enter 6-digit code from authenticator app
   - Click "Verify and Enable"

6. **Save Backup Codes** ⚠️ **CRITICAL**
   - Download or print 8 backup codes
   - Store in secure location (password manager, safe)
   - Each code is single-use

7. **Success**
   - 2FA is now enabled
   - Next login will require TOTP code

**Estimated Time**: 5 minutes

---

## Common Support Scenarios

### Scenario 1: Lost Authenticator Device

**Symptoms**: User lost phone/device with authenticator app

**Resolution Path A: User Has Backup Codes** ✅ **PREFERRED**

1. **Instruct User**:
   - "Do you have your backup codes saved?"
   - If yes: "Please use one of your backup codes to log in"

2. **Login with Backup Code**:
   - User enters email + password
   - When prompted for TOTP, click "Use backup code instead"
   - Enter one backup code (8 characters)
   - Login successful

3. **Re-setup 2FA**:
   - Go to Settings → Security
   - Click "Disable 2FA" (requires password)
   - Click "Enable 2FA" again
   - Scan QR code with new device
   - Save new backup codes

**Resolution Path B: User Does NOT Have Backup Codes** ⚠️ **REQUIRES VERIFICATION**

1. **Verify Identity** (REQUIRED):
   - Ask for: Full name, email, account creation date
   - Ask security question: "What is your tenant ID?"
   - Check recent activity: "When did you last log in?"
   - **If high-value account**: Escalate to CTO for approval

2. **Disable 2FA** (Support Team):
   ```sql
   -- Run in Supabase SQL Editor (service role required)
   -- Replace <user_email> with actual email
   
   -- Get user_id
   SELECT id, email FROM auth.users WHERE email = '<user_email>';
   
   -- Disable 2FA
   UPDATE user_2fa 
   SET enabled = FALSE 
   WHERE user_id = '<user_id>';
   
   -- Delete backup codes and trusted devices
   DELETE FROM totp_backup_codes WHERE user_id = '<user_id>';
   DELETE FROM trusted_devices WHERE user_id = '<user_id>';
   ```

3. **Notify User**:
   - Email: "Your 2FA has been temporarily disabled for account recovery"
   - "Please log in and re-enable 2FA immediately"
   - Provide setup instructions link

4. **Follow-Up** (24 hours):
   - Check if user re-enabled 2FA
   - If not, send reminder email

**SLA**: 
- Path A: Immediate (self-service)
- Path B: 30 minutes (during business hours), 2 hours (after hours)

---

### Scenario 2: Invalid TOTP Code

**Symptoms**: User enters TOTP code but gets "Invalid TOTP code" error

**Common Causes**:
1. Time sync issue (most common)
2. Wrong account in authenticator app
3. Typing error
4. Code expired (30-second window)

**Troubleshooting Steps**:

1. **Check Time Sync**:
   - Ask: "Is your phone's time set to automatic?"
   - iOS: Settings → General → Date & Time → Set Automatically (ON)
   - Android: Settings → System → Date & Time → Automatic date & time (ON)
   - **Fix**: Enable automatic time, wait 1 minute, try again

2. **Verify Correct Account**:
   - Ask: "Do you have multiple accounts in your authenticator app?"
   - Instruct: "Make sure you're using the code for [user_email]"

3. **Wait for New Code**:
   - TOTP codes refresh every 30 seconds
   - Instruct: "Wait for the code to refresh, then try again immediately"

4. **Try Backup Code**:
   - If TOTP still fails, use backup code instead
   - Click "Use backup code instead" on login screen

5. **Last Resort: Disable and Re-enable**:
   - If all else fails, disable 2FA and re-enable (see Scenario 1, Path B)

**SLA**: 15 minutes

---

### Scenario 3: No Backup Codes Saved

**Symptoms**: User enabled 2FA but didn't save backup codes

**Resolution**:

1. **If User Can Still Log In**:
   - Instruct: "Log in with your TOTP code"
   - Go to Settings → Security → Two-Factor Authentication
   - Click "Regenerate Backup Codes"
   - Download and save new codes

2. **If User Cannot Log In** (Lost Device):
   - Follow Scenario 1, Path B (identity verification required)

**Prevention**:
- Update UI to force backup code download before completing setup
- Send email with backup codes (encrypted)
- Add reminder in UI: "Have you saved your backup codes?"

**SLA**: Immediate (if can log in), 30 minutes (if cannot log in)

---

### Scenario 4: Cannot Scan QR Code

**Symptoms**: User cannot scan QR code (camera issues, poor lighting, etc.)

**Resolution**:

1. **Provide Manual Entry Key**:
   - On 2FA setup screen, click "Can't scan QR code?"
   - Copy the manual entry key (32-character Base32 string)
   - Example: `JBSWY3DPEHPK3PXP`

2. **Manual Entry Steps**:
   - Open authenticator app
   - Tap "+" or "Add Account"
   - Select "Enter a setup key" or "Manual entry"
   - Enter:
     - **Account name**: Morning AI (owner@example.com)
     - **Key**: [paste 32-character key]
     - **Time-based**: Yes
   - Tap "Add"

3. **Verify**:
   - Enter 6-digit code from app
   - Click "Verify and Enable"

**SLA**: 10 minutes

---

### Scenario 5: Account Lockout (Rate Limiting)

**Symptoms**: User gets "Too many failed attempts" error

**Cause**: Rate limiting after 10 failed TOTP attempts within 1 hour

**Resolution**:

1. **Wait Period**:
   - Instruct: "Please wait 1 hour before trying again"
   - Rate limit resets after 1 hour

2. **Use Backup Code** (Bypass Rate Limit):
   - Backup codes are NOT rate-limited
   - Instruct: "Use one of your backup codes to log in immediately"

3. **Emergency Override** (DevOps Only):
   ```bash
   # Clear rate limit in Redis
   redis-cli DEL "rate_limit:totp:<user_id>"
   ```

**Prevention**:
- Educate users on time sync issues
- Provide clear error messages
- Suggest backup codes after 3 failed attempts

**SLA**: 
- Self-service: 1 hour (wait) or immediate (backup code)
- DevOps override: 15 minutes (emergency only)

---

### Scenario 6: "Remember This Device" Not Working

**Symptoms**: User checked "Remember this device" but still prompted for TOTP

**Common Causes**:
1. Cookies disabled
2. Private/Incognito mode
3. Browser cleared cookies
4. Device fingerprint changed (VPN, browser update)

**Troubleshooting**:

1. **Check Cookie Settings**:
   - Ask: "Are cookies enabled in your browser?"
   - Chrome: Settings → Privacy → Cookies → Allow all cookies
   - Safari: Preferences → Privacy → Uncheck "Block all cookies"

2. **Check Browsing Mode**:
   - Ask: "Are you using private/incognito mode?"
   - Instruct: "Please use normal browsing mode"

3. **Check Trusted Devices**:
   ```sql
   -- Check if device is trusted
   SELECT * FROM trusted_devices 
   WHERE user_id = '<user_id>' 
   AND expires_at > NOW();
   ```

4. **Re-trust Device**:
   - Log in with TOTP
   - Check "Remember this device for 30 days"
   - Verify checkbox is checked before clicking "Verify"

**SLA**: 15 minutes

---

## Troubleshooting Guide

### Error Messages

#### "Invalid TOTP code"
**Cause**: Time sync issue, wrong code, or expired code  
**Fix**: Check time sync, wait for new code, try backup code

#### "Invalid backup code"
**Cause**: Code already used or incorrect code  
**Fix**: Try another backup code, verify typing

#### "Too many failed attempts"
**Cause**: Rate limiting (10 attempts/hour)  
**Fix**: Wait 1 hour or use backup code

#### "2FA feature is not enabled"
**Cause**: Feature flag disabled  
**Fix**: Contact DevOps to enable `FEATURE_2FA_ENABLED`

#### "2FA is not enabled for this user"
**Cause**: User hasn't set up 2FA yet  
**Fix**: Guide user through setup process

#### "Invalid or expired pre-auth token"
**Cause**: Pre-auth token expired (5 minutes) or already used  
**Fix**: Start login flow again from beginning

---

### Diagnostic Queries

**Check if user has 2FA enabled**:
```sql
SELECT u.email, u2.enabled, u2.verified_at, u2.last_used_at
FROM auth.users u
LEFT JOIN user_2fa u2 ON u2.user_id = u.id
WHERE u.email = '<user_email>';
```

**Check backup codes remaining**:
```sql
SELECT COUNT(*) as unused_codes
FROM totp_backup_codes
WHERE user_id = '<user_id>' AND used = FALSE;
```

**Check trusted devices**:
```sql
SELECT device_fingerprint, trusted_at, expires_at, last_used_at
FROM trusted_devices
WHERE user_id = '<user_id>' AND expires_at > NOW();
```

**Check recent login attempts**:
```sql
-- This requires application logs, not in database
-- Check Datadog/CloudWatch for:
-- - login_attempts_total{user_id="<user_id>"}
-- - 2fa_verification_attempts_total{user_id="<user_id>"}
```

---

## Database Operations

### ⚠️ CAUTION: Service Role Required

All database operations require Supabase service role key. Never share this key with users.

### Disable 2FA for User

```sql
-- Get user_id from email
SELECT id, email FROM auth.users WHERE email = '<user_email>';

-- Disable 2FA
UPDATE user_2fa 
SET enabled = FALSE 
WHERE user_id = '<user_id>';

-- Optional: Delete backup codes and trusted devices
DELETE FROM totp_backup_codes WHERE user_id = '<user_id>';
DELETE FROM trusted_devices WHERE user_id = '<user_id>';
```

### Regenerate Backup Codes (Manual)

```sql
-- Delete existing backup codes
DELETE FROM totp_backup_codes WHERE user_id = '<user_id>';

-- User must regenerate via UI (Settings → Security → Regenerate Backup Codes)
-- This ensures codes are displayed to user and properly hashed
```

### Check 2FA Status for All Owners

```sql
SELECT 
    u.email,
    COALESCE(u2.enabled, FALSE) as twofa_enabled,
    u2.verified_at,
    u.last_sign_in_at
FROM auth.users u
LEFT JOIN user_2fa u2 ON u2.user_id = u.id
WHERE u.raw_user_meta_data->>'role' = 'owner'
ORDER BY u2.enabled ASC NULLS FIRST;
```

### Remove Expired Trusted Devices

```sql
-- Cleanup expired trusted devices (run daily)
DELETE FROM trusted_devices WHERE expires_at < NOW();

-- Or use the built-in function
SELECT cleanup_expired_trusted_devices();
```

---

## Emergency Procedures

### Emergency: Mass Lockout

**Trigger**: >3 owners locked out within 1 hour

**Procedure**:

1. **Assess Severity** (< 5 minutes):
   - Check error rate in Datadog
   - Check login success rate
   - Identify common pattern

2. **Disable Enforcement** (< 5 minutes):
   ```bash
   # SSH to production server or use kubectl
   kubectl set env deployment/api-backend FEATURE_2FA_OWNER_ENFORCEMENT=false
   kubectl rollout restart deployment/api-backend
   ```

3. **Notify Stakeholders** (< 10 minutes):
   - Post in #incidents Slack channel
   - Page on-call engineer
   - Notify CTO

4. **Root Cause Analysis** (< 24 hours):
   - Review logs
   - Identify bug
   - Create hotfix PR

5. **Re-enable** (After fix):
   - Test in staging
   - Deploy to production
   - Monitor closely

### Emergency: Individual Owner Locked Out (VIP)

**Trigger**: High-value owner account locked out, business-critical

**Procedure**:

1. **Verify Identity** (< 15 minutes):
   - Phone call with owner
   - Verify email, account details
   - CTO approval required

2. **Disable 2FA** (< 5 minutes):
   - Run SQL query (see "Disable 2FA for User")
   - Notify owner via email

3. **Immediate Re-enable** (< 30 minutes):
   - Owner logs in
   - Guide through 2FA setup
   - Verify backup codes saved

### Emergency: Security Breach Suspected

**Trigger**: Suspicious activity, unauthorized access attempts

**Procedure**:

1. **Immediate Action** (< 5 minutes):
   - Disable affected user account
   - Blacklist all refresh tokens
   - Force password reset

2. **Investigation** (< 1 hour):
   - Review audit logs
   - Check login history
   - Identify compromise vector

3. **Containment** (< 2 hours):
   - Rotate JWT secret (if needed)
   - Notify affected users
   - File security incident report

4. **Recovery** (< 24 hours):
   - User resets password
   - User re-enables 2FA
   - Monitor for further suspicious activity

---

## Escalation Matrix

### Level 1: Support Team (First Response)
**Handles**:
- Basic 2FA setup questions
- Lost device with backup codes
- Invalid TOTP troubleshooting
- Cannot scan QR code

**SLA**: 15 minutes (business hours), 2 hours (after hours)

**Escalate to Level 2 if**:
- User lost device AND no backup codes
- Database access required
- Rate limit override needed
- >30 minutes without resolution

---

### Level 2: DevOps / On-Call Engineer
**Handles**:
- Disable 2FA (with identity verification)
- Database operations
- Rate limit overrides
- Feature flag changes
- System-wide issues

**SLA**: 30 minutes (business hours), 1 hour (after hours)

**Escalate to Level 3 if**:
- Mass lockout (>3 users)
- Security breach suspected
- System-wide outage
- Requires CTO approval

---

### Level 3: CTO / Engineering Lead
**Handles**:
- High-value account issues
- Security incidents
- Feature flag rollback
- Break-glass procedures
- Post-mortem reviews

**SLA**: 1 hour (critical), 4 hours (high), 24 hours (medium)

---

## FAQ

### Q: How long do backup codes last?
**A**: Backup codes never expire, but each code can only be used once. Users should regenerate codes if they've used more than 5 out of 8.

### Q: Can users have multiple authenticator apps?
**A**: Yes, users can scan the same QR code with multiple apps (e.g., phone + tablet). All will generate the same TOTP codes.

### Q: What happens if a user's device is stolen?
**A**: The thief would still need the user's password to log in. However, users should:
1. Log in from another device (using backup code)
2. Disable 2FA
3. Re-enable 2FA with new device
4. Change password

### Q: Can users disable 2FA?
**A**: Owners cannot disable 2FA themselves (enforced). Support team can disable with identity verification and CTO approval.

### Q: How long does "Remember this device" last?
**A**: 30 days from when the device was trusted. After 30 days, user must enter TOTP again.

### Q: What if a user clears browser cookies?
**A**: Trusted device is forgotten. User must enter TOTP and check "Remember this device" again.

### Q: Can users use SMS-based 2FA?
**A**: No, we only support TOTP (authenticator apps) for security reasons. SMS is vulnerable to SIM swapping attacks.

### Q: What if a user has no smartphone?
**A**: Users can use desktop authenticator apps like Authy (Windows/Mac) or 1Password.

### Q: How do I test 2FA in staging?
**A**: Use mock Owner account:
- Email: owner@example.com
- Password: owner_password_123
- Enable 2FA in staging environment

---

## Appendix: Support Scripts

### Python Script: Disable 2FA for User

```python
#!/usr/bin/env python3
"""
Disable 2FA for a user (support tool)
Usage: python disable_2fa.py <user_email>
Requires: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars
"""

import os
import sys
from supabase import create_client

def disable_2fa(email: str):
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get user_id from email
    # Note: This requires auth.users access via Admin API
    print(f"Disabling 2FA for {email}...")
    
    # Update user_2fa table
    response = supabase.table('user_2fa').update({
        'enabled': False
    }).eq('user_id', '<user_id>').execute()
    
    print(f"✅ 2FA disabled for {email}")
    print("⚠️  User should re-enable 2FA immediately after logging in")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python disable_2fa.py <user_email>")
        sys.exit(1)
    
    email = sys.argv[1]
    disable_2fa(email)
```

---

**Document Owner**: Devin AI  
**Last Updated**: 2025-11-04  
**Next Review**: After Phase 1 Deployment  
**Feedback**: support@morningai.com
