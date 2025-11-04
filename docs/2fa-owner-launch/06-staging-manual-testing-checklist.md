# Staging Manual Testing Checklist - 2FA Integration

**Document Version**: 1.0  
**Date**: 2025-11-04  
**Environment**: Staging  
**Tester**: _________________  
**Test Date**: _________________

---

## Pre-Test Setup

### Environment Configuration

- [ ] **Staging URL**: https://staging-owner.morningai.com (or equivalent)
- [ ] **Feature Flags Enabled**:
  ```bash
  FEATURE_2FA_ENABLED=true
  FEATURE_2FA_OWNER_ENFORCEMENT=true  # For enforcement tests
  ```
- [ ] **Database Schema Verified**:
  - [ ] `user_2fa` table exists
  - [ ] `totp_backup_codes` table exists
  - [ ] `trusted_devices` table exists
- [ ] **Test Accounts Created**:
  - [ ] Owner account (for 2FA tests)
  - [ ] Non-Owner account (for non-2FA tests)
- [ ] **Authenticator App Installed**: Google Authenticator, Authy, or similar
- [ ] **Browser**: Chrome/Firefox/Safari (test on multiple)
- [ ] **Network**: Stable internet connection

---

## Test Suite 1: 2FA Setup Flow (Owner Account)

### Test 1.1: Enable 2FA - Happy Path ✅

**Objective**: Verify Owner can successfully enable 2FA

**Steps**:
1. Log in to staging as Owner user
   - Email: owner@example.com (or your test account)
   - Password: [test password]
2. Navigate to Settings → Security
3. Click "Enable Two-Factor Authentication"
4. Enter password to confirm
5. Scan QR code with authenticator app
6. Enter 6-digit TOTP code from app
7. Click "Verify and Enable"
8. Verify backup codes are displayed (8 codes)
9. Download backup codes

**Expected Results**:
- [ ] QR code displayed correctly
- [ ] TOTP code accepted
- [ ] Success message: "Two-factor authentication enabled"
- [ ] 8 backup codes displayed
- [ ] Backup codes downloadable as text file
- [ ] 2FA status shows "Enabled" in settings

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

**Screenshots**: _________________

---

### Test 1.2: Enable 2FA - Manual Entry Key

**Objective**: Verify manual entry key works when QR code cannot be scanned

**Steps**:
1. Log in to staging as Owner user
2. Navigate to Settings → Security
3. Click "Enable Two-Factor Authentication"
4. Click "Can't scan QR code?"
5. Copy manual entry key (32-character Base32 string)
6. Open authenticator app
7. Add account manually:
   - Account name: Morning AI (owner@example.com)
   - Key: [paste manual entry key]
   - Type: Time-based
8. Enter 6-digit TOTP code from app
9. Click "Verify and Enable"

**Expected Results**:
- [ ] Manual entry key displayed (32 characters, Base32)
- [ ] TOTP code from manual entry accepted
- [ ] 2FA enabled successfully

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 1.3: Enable 2FA - Invalid TOTP Code

**Objective**: Verify error handling for invalid TOTP code

**Steps**:
1. Log in to staging as Owner user
2. Navigate to Settings → Security
3. Click "Enable Two-Factor Authentication"
4. Scan QR code with authenticator app
5. Enter incorrect 6-digit code (e.g., "000000")
6. Click "Verify and Enable"

**Expected Results**:
- [ ] Error message: "Invalid TOTP code"
- [ ] 2FA NOT enabled
- [ ] User can retry with correct code

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 2: Login Flow with 2FA (Owner Account)

### Test 2.1: Login with TOTP - Happy Path ✅

**Objective**: Verify Owner can log in with TOTP code

**Prerequisites**: 2FA enabled for Owner account

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. Verify redirected to 2FA verification page
6. Open authenticator app
7. Enter current 6-digit TOTP code
8. Click "Verify"

**Expected Results**:
- [ ] After password: Redirected to 2FA verification page (NOT logged in yet)
- [ ] 2FA verification page shows: "Enter your 6-digit code"
- [ ] TOTP code accepted
- [ ] Logged in successfully
- [ ] Redirected to dashboard
- [ ] Session cookies set (access_token, refresh_token)

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

**Screenshots**: _________________

---

### Test 2.2: Login with Backup Code

**Objective**: Verify Owner can log in with backup code

**Prerequisites**: 2FA enabled, backup codes saved

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. On 2FA verification page, click "Use backup code instead"
6. Enter one unused backup code (8 characters)
7. Click "Verify"

**Expected Results**:
- [ ] "Use backup code instead" link visible
- [ ] Backup code input field displayed
- [ ] Backup code accepted
- [ ] Logged in successfully
- [ ] Backup code marked as used (cannot reuse)

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 2.3: Login with Invalid TOTP Code

**Objective**: Verify error handling for invalid TOTP code during login

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. Enter incorrect TOTP code (e.g., "000000")
6. Click "Verify"

**Expected Results**:
- [ ] Error message: "Invalid TOTP code"
- [ ] NOT logged in
- [ ] Can retry with correct code
- [ ] After 3 failed attempts: Suggest using backup code

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 2.4: Login with Expired TOTP Code

**Objective**: Verify expired TOTP codes are rejected

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. Open authenticator app and note current TOTP code
6. Wait 30+ seconds for code to refresh
7. Enter the OLD (expired) code
8. Click "Verify"

**Expected Results**:
- [ ] Error message: "Invalid TOTP code" (expired codes rejected)
- [ ] Can retry with new code

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 2.5: Login with Used Backup Code

**Objective**: Verify backup codes are single-use

**Prerequisites**: At least one backup code already used

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. Click "Use backup code instead"
6. Enter a PREVIOUSLY USED backup code
7. Click "Verify"

**Expected Results**:
- [ ] Error message: "Invalid backup code" (already used)
- [ ] NOT logged in
- [ ] Can retry with unused backup code

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 2.6: Remember This Device

**Objective**: Verify "Remember this device" functionality

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. Enter TOTP code
6. Check "Remember this device for 30 days"
7. Click "Verify"
8. Log out
9. Log in again with same email and password

**Expected Results**:
- [ ] First login: TOTP required
- [ ] "Remember this device" checkbox visible
- [ ] Second login (same browser): TOTP NOT required (skipped)
- [ ] Logged in directly after password

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

**Note**: Test in normal browsing mode (not incognito)

---

### Test 2.7: Remember Device - Different Browser

**Objective**: Verify trusted device is browser-specific

**Steps**:
1. Log in with Chrome, check "Remember this device"
2. Log out
3. Open Firefox (or Safari)
4. Log in with same account

**Expected Results**:
- [ ] Chrome: TOTP not required (trusted)
- [ ] Firefox: TOTP required (different browser)

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 2.8: Remember Device - Incognito Mode

**Objective**: Verify trusted device does NOT work in incognito mode

**Steps**:
1. Log in with normal Chrome, check "Remember this device"
2. Log out
3. Open Chrome Incognito window
4. Log in with same account

**Expected Results**:
- [ ] Normal mode: TOTP not required (trusted)
- [ ] Incognito mode: TOTP required (cookies not persisted)

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 3: Rate Limiting and Security

### Test 3.1: Rate Limiting - Too Many Failed TOTP Attempts

**Objective**: Verify rate limiting after 10 failed TOTP attempts

**Steps**:
1. Log out of staging
2. Navigate to login page
3. Enter email and password
4. Click "Log In"
5. Enter incorrect TOTP code 10 times
6. Attempt 11th time

**Expected Results**:
- [ ] After 10 failed attempts: Error message "Too many failed attempts. Please try again in 1 hour."
- [ ] Cannot attempt TOTP verification for 1 hour
- [ ] Backup codes still work (not rate-limited)

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 3.2: Session Timeout

**Objective**: Verify access token expires after 15 minutes

**Steps**:
1. Log in to staging
2. Note the time
3. Wait 16 minutes (or set system clock forward)
4. Attempt to access a protected page (e.g., Settings)

**Expected Results**:
- [ ] After 15 minutes: Access token expired
- [ ] Redirected to login page OR
- [ ] Refresh token automatically refreshes access token (if implemented)

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 4: 2FA Management

### Test 4.1: Regenerate Backup Codes

**Objective**: Verify Owner can regenerate backup codes

**Prerequisites**: 2FA enabled

**Steps**:
1. Log in to staging
2. Navigate to Settings → Security
3. Click "Regenerate Backup Codes"
4. Enter password to confirm
5. Verify new backup codes displayed (8 codes)
6. Download new backup codes
7. Attempt to use old backup code

**Expected Results**:
- [ ] New backup codes generated (8 codes)
- [ ] Old backup codes invalidated (cannot use)
- [ ] New backup codes work for login

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 4.2: Disable 2FA

**Objective**: Verify Owner can disable 2FA (if enforcement is OFF)

**Prerequisites**: 2FA enabled, `FEATURE_2FA_OWNER_ENFORCEMENT=false`

**Steps**:
1. Log in to staging
2. Navigate to Settings → Security
3. Click "Disable Two-Factor Authentication"
4. Enter password to confirm
5. Enter current TOTP code
6. Click "Disable"

**Expected Results**:
- [ ] Password required
- [ ] TOTP code required
- [ ] 2FA disabled successfully
- [ ] Backup codes deleted
- [ ] Trusted devices deleted
- [ ] Next login: No TOTP required

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

**Note**: If enforcement is ON, disable should be blocked with message "2FA is required for Owner accounts"

---

### Test 4.3: View 2FA Status

**Objective**: Verify Owner can view 2FA status and details

**Prerequisites**: 2FA enabled

**Steps**:
1. Log in to staging
2. Navigate to Settings → Security
3. View 2FA section

**Expected Results**:
- [ ] Status: "Enabled" (green badge)
- [ ] Last used: [timestamp]
- [ ] Backup codes remaining: X/8
- [ ] Trusted devices: X devices
- [ ] Options: "Regenerate Backup Codes", "Disable 2FA"

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 5: Non-Owner Account (2FA Optional)

### Test 5.1: Non-Owner Login Without 2FA

**Objective**: Verify non-Owner users are NOT required to use 2FA

**Prerequisites**: Non-Owner account (role: user, admin, etc.)

**Steps**:
1. Log in to staging as non-Owner user
2. Enter email and password
3. Click "Log In"

**Expected Results**:
- [ ] Logged in directly (no 2FA prompt)
- [ ] No redirect to 2FA verification page
- [ ] Session cookies set

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 5.2: Non-Owner Can Enable 2FA (Optional)

**Objective**: Verify non-Owner users CAN enable 2FA voluntarily

**Steps**:
1. Log in to staging as non-Owner user
2. Navigate to Settings → Security
3. Verify "Enable Two-Factor Authentication" option is available
4. Enable 2FA (follow Test 1.1 steps)

**Expected Results**:
- [ ] 2FA setup available for non-Owner users
- [ ] Setup process same as Owner
- [ ] After enabling: TOTP required on next login

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 6: Error Handling and Edge Cases

### Test 6.1: 2FA Feature Disabled

**Objective**: Verify behavior when 2FA feature is disabled

**Prerequisites**: `FEATURE_2FA_ENABLED=false`

**Steps**:
1. Log in to staging as Owner user
2. Navigate to Settings → Security
3. Attempt to enable 2FA

**Expected Results**:
- [ ] 2FA option hidden OR
- [ ] Error message: "2FA feature is not available"

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 6.2: Network Error During 2FA Setup

**Objective**: Verify error handling for network failures

**Steps**:
1. Log in to staging
2. Navigate to Settings → Security
3. Click "Enable Two-Factor Authentication"
4. Disconnect internet
5. Scan QR code and enter TOTP code
6. Click "Verify and Enable"

**Expected Results**:
- [ ] Error message: "Network error. Please try again."
- [ ] 2FA NOT enabled
- [ ] Can retry after reconnecting

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 6.3: Browser Back Button During 2FA Setup

**Objective**: Verify behavior when user clicks back during setup

**Steps**:
1. Log in to staging
2. Navigate to Settings → Security
3. Click "Enable Two-Factor Authentication"
4. QR code displayed
5. Click browser back button
6. Navigate back to Security settings

**Expected Results**:
- [ ] 2FA NOT enabled (setup cancelled)
- [ ] Can restart setup process

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 6.4: Multiple Browser Tabs

**Objective**: Verify behavior with multiple tabs open

**Steps**:
1. Log in to staging (Tab 1)
2. Open new tab (Tab 2) with same staging URL
3. In Tab 1: Enable 2FA
4. In Tab 2: Refresh page

**Expected Results**:
- [ ] Tab 2: Shows 2FA enabled (state synced)
- [ ] No errors or inconsistencies

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 7: Performance and Load

### Test 7.1: Login Performance with 2FA

**Objective**: Verify login performance is acceptable

**Steps**:
1. Log out of staging
2. Start timer
3. Enter email and password
4. Click "Log In"
5. Enter TOTP code
6. Click "Verify"
7. Stop timer when dashboard loads

**Expected Results**:
- [ ] Total login time < 5 seconds (p95)
- [ ] 2FA verification < 2 seconds
- [ ] No noticeable lag

**Actual Results**: _________________

**Login Time**: _________ seconds

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 7.2: Concurrent Logins

**Objective**: Verify system handles concurrent 2FA logins

**Steps**:
1. Open 5 browser windows (different browsers/incognito)
2. In each window: Log in with different Owner accounts simultaneously
3. All enter TOTP codes at the same time

**Expected Results**:
- [ ] All logins succeed
- [ ] No errors or timeouts
- [ ] No race conditions

**Actual Results**: _________________

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Test Suite 8: Cross-Browser and Mobile

### Test 8.1: Chrome

**Steps**: Run Test Suite 1 and 2 in Chrome

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 8.2: Firefox

**Steps**: Run Test Suite 1 and 2 in Firefox

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 8.3: Safari

**Steps**: Run Test Suite 1 and 2 in Safari

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 8.4: Mobile (iOS Safari)

**Steps**: Run Test Suite 1 and 2 on iPhone Safari

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

### Test 8.5: Mobile (Android Chrome)

**Steps**: Run Test Suite 1 and 2 on Android Chrome

**Status**: ⬜ Pass ⬜ Fail ⬜ Blocked

---

## Summary

### Test Results

**Total Tests**: 35  
**Passed**: _____  
**Failed**: _____  
**Blocked**: _____  

**Pass Rate**: _____% (Target: >95%)

### Critical Issues Found

1. _________________
2. _________________
3. _________________

### Non-Critical Issues Found

1. _________________
2. _________________
3. _________________

### Recommendations

1. _________________
2. _________________
3. _________________

### Sign-Off

**Tester Name**: _________________  
**Date**: _________________  
**Signature**: _________________

**Approved for Production**: ⬜ Yes ⬜ No ⬜ Conditional

**Conditions** (if conditional):
_________________

---

**Document Owner**: Devin AI  
**Last Updated**: 2025-11-04  
**Next Review**: After Staging Testing Complete
