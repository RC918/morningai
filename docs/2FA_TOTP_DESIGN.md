# 2FA/TOTP Implementation Design (PR E)

**Status**: Design Phase  
**Priority**: P1 (High - Security Feature)  
**Target**: Q4 2025  
**Owner**: Engineering Team

---

## Executive Summary

This document outlines the design for implementing Two-Factor Authentication (2FA) using Time-based One-Time Passwords (TOTP) for MorningAI's authentication system. This feature will enhance security by requiring users to provide a second factor of authentication beyond their password.

**Key Benefits**:
- Enhanced account security against credential theft
- Industry-standard TOTP implementation (RFC 6238)
- Backup recovery codes for account recovery
- Optional per-user enrollment (not mandatory initially)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Endpoints](#api-endpoints)
3. [Data Model](#data-model)
4. [Security Considerations](#security-considerations)
5. [User Flows](#user-flows)
6. [Implementation Plan](#implementation-plan)
7. [Testing Strategy](#testing-strategy)
8. [Rollout Strategy](#rollout-strategy)

---

## Architecture Overview

### System Components

```
┌─────────────────┐
│  Frontend Apps  │
│  (React/Vite)   │
└────────┬────────┘
         │
         │ HTTPS + Cookies
         │
┌────────▼────────┐
│   API Backend   │
│   (FastAPI)     │
├─────────────────┤
│ • TOTP Setup    │
│ • TOTP Verify   │
│ • Backup Codes  │
│ • Device Memory │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│   PostgreSQL    │
│   (Supabase)    │
├─────────────────┤
│ • user_2fa      │
│ • backup_codes  │
│ • trusted_devs  │
└─────────────────┘
```

### Technology Stack

- **TOTP Library**: `pyotp` (Python) - RFC 6238 compliant
- **QR Code Generation**: `qrcode` (Python)
- **Frontend**: React with existing auth context
- **Storage**: PostgreSQL with encrypted secrets
- **Backup Codes**: Argon2 hashed, 8 codes per user

---

## API Endpoints

### 1. Setup TOTP (Enrollment)

**Endpoint**: `POST /api/auth/v2/totp/setup`

**Request**:
```json
{
  "password": "user_password_for_confirmation"
}
```

**Response**:
```json
{
  "secret": "BASE32_ENCODED_SECRET",
  "qr_code": "data:image/png;base64,...",
  "backup_codes": [
    "XXXX-XXXX-XXXX-XXXX",
    "YYYY-YYYY-YYYY-YYYY",
    ...
  ]
}
```

**Security**:
- Requires authenticated session
- Password confirmation required
- Secret stored encrypted in database
- Backup codes hashed with Argon2
- Rate limited: 3 attempts per hour

---

### 2. Verify TOTP (Complete Enrollment)

**Endpoint**: `POST /api/auth/v2/totp/verify-setup`

**Request**:
```json
{
  "code": "123456"
}
```

**Response**:
```json
{
  "success": true,
  "enabled": true
}
```

**Security**:
- Verifies TOTP code before enabling 2FA
- Prevents accidental lockout
- Time window: ±1 period (30 seconds)

---

### 3. Login with TOTP

**Endpoint**: `POST /api/auth/v2/login`

**Request** (when 2FA enabled):
```json
{
  "email": "user@example.com",
  "password": "password",
  "totp_code": "123456",
  "remember_device": false
}
```

**Response**:
```json
{
  "success": true,
  "user": { ... },
  "requires_2fa": false
}
```

**Flow**:
1. User submits email + password
2. If 2FA enabled, return `requires_2fa: true`
3. Frontend prompts for TOTP code
4. User submits TOTP code
5. Backend verifies and issues session

---

### 4. Disable TOTP

**Endpoint**: `POST /api/auth/v2/totp/disable`

**Request**:
```json
{
  "password": "user_password_for_confirmation",
  "totp_code": "123456"
}
```

**Response**:
```json
{
  "success": true,
  "enabled": false
}
```

---

### 5. Regenerate Backup Codes

**Endpoint**: `POST /api/auth/v2/totp/backup-codes/regenerate`

**Request**:
```json
{
  "password": "user_password_for_confirmation"
}
```

**Response**:
```json
{
  "backup_codes": [
    "XXXX-XXXX-XXXX-XXXX",
    ...
  ]
}
```

---

### 6. Use Backup Code

**Endpoint**: `POST /api/auth/v2/login/backup-code`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password",
  "backup_code": "XXXX-XXXX-XXXX-XXXX"
}
```

**Response**:
```json
{
  "success": true,
  "user": { ... },
  "remaining_codes": 7
}
```

**Security**:
- Backup code is single-use
- Marked as used in database
- User warned when < 3 codes remain

---

## Data Model

### Table: `user_2fa`

```sql
CREATE TABLE user_2fa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT FALSE,
    secret_encrypted TEXT NOT NULL,  -- AES-256 encrypted TOTP secret
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_user_2fa_user_id ON user_2fa(user_id);
```

### Table: `totp_backup_codes`

```sql
CREATE TABLE totp_backup_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,  -- Argon2 hash
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, code_hash)
);

CREATE INDEX idx_backup_codes_user_id ON totp_backup_codes(user_id);
CREATE INDEX idx_backup_codes_used ON totp_backup_codes(used);
```

### Table: `trusted_devices` (Optional - Remember Device)

```sql
CREATE TABLE trusted_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint TEXT NOT NULL,
    device_name TEXT,
    trusted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,  -- 30 days from trusted_at
    last_used_at TIMESTAMP,
    UNIQUE(user_id, device_fingerprint)
);

CREATE INDEX idx_trusted_devices_user_id ON trusted_devices(user_id);
CREATE INDEX idx_trusted_devices_expires ON trusted_devices(expires_at);
```

---

## Security Considerations

### 1. Secret Storage

**Encryption**:
- TOTP secrets encrypted with AES-256-GCM
- Encryption key stored in environment variable `TOTP_ENCRYPTION_KEY`
- Key rotation supported via migration script

**Key Management**:
```python
from cryptography.fernet import Fernet

# Generate key (one-time setup)
key = Fernet.generate_key()

# Encrypt secret
f = Fernet(key)
encrypted_secret = f.encrypt(secret.encode())

# Decrypt secret
decrypted_secret = f.decrypt(encrypted_secret).decode()
```

---

### 2. Backup Code Storage

**Hashing**:
- Backup codes hashed with Argon2id
- Parameters: memory=65536, iterations=3, parallelism=4
- Salt automatically generated per code

**Generation**:
```python
import secrets
import argon2

# Generate 8 backup codes
codes = [
    f"{secrets.token_hex(4)}-{secrets.token_hex(4)}-{secrets.token_hex(4)}-{secrets.token_hex(4)}"
    for _ in range(8)
]

# Hash each code
ph = argon2.PasswordHasher()
hashed_codes = [ph.hash(code) for code in codes]
```

---

### 3. Rate Limiting

**TOTP Verification**:
- 5 failed attempts per 15 minutes per user
- Exponential backoff after 3 failures
- Account lockout after 10 consecutive failures

**Setup Endpoint**:
- 3 setup attempts per hour per user
- Prevents brute force secret generation

**Backup Code Usage**:
- 3 failed attempts per hour per user
- Prevents backup code enumeration

---

### 4. Time Skew Tolerance

**Configuration**:
- Accept codes from ±1 time window (30 seconds)
- Total acceptance window: 90 seconds
- Prevents clock drift issues

**Implementation**:
```python
import pyotp

totp = pyotp.TOTP(secret)
# Check current, previous, and next time windows
valid = totp.verify(code, valid_window=1)
```

---

### 5. Device Fingerprinting (Remember Device)

**Fingerprint Components**:
- User-Agent header
- IP address (hashed)
- Browser capabilities
- Screen resolution
- Timezone

**Privacy**:
- Fingerprint hashed before storage
- No PII stored in fingerprint
- User can revoke trusted devices

---

## User Flows

### Flow 1: Enable 2FA

```
1. User navigates to Settings > Security
2. Click "Enable Two-Factor Authentication"
3. Enter password for confirmation
4. Backend generates TOTP secret and QR code
5. User scans QR code with authenticator app
6. User enters 6-digit code to verify
7. Backend verifies code and enables 2FA
8. Display 8 backup codes (download/print)
9. User confirms they saved backup codes
10. 2FA enabled ✓
```

**UI Components**:
- Password confirmation modal
- QR code display
- Manual entry option (for secret)
- Backup codes display with download button
- Confirmation checkbox

---

### Flow 2: Login with 2FA

```
1. User enters email + password
2. Backend validates credentials
3. If 2FA enabled, return requires_2fa: true
4. Frontend shows TOTP code input
5. User enters 6-digit code from authenticator
6. Backend verifies TOTP code
7. If valid, issue session cookie
8. If invalid, show error and retry (max 5 attempts)
9. Option to use backup code instead
```

**UI Components**:
- TOTP code input (6 digits, auto-submit)
- "Use backup code instead" link
- "Remember this device for 30 days" checkbox
- Error messages with retry count

---

### Flow 3: Use Backup Code

```
1. User clicks "Use backup code instead"
2. Frontend shows backup code input
3. User enters backup code (format: XXXX-XXXX-XXXX-XXXX)
4. Backend verifies and marks code as used
5. If valid, issue session cookie
6. Show warning if < 3 codes remaining
7. Prompt to regenerate backup codes
```

---

### Flow 4: Disable 2FA

```
1. User navigates to Settings > Security
2. Click "Disable Two-Factor Authentication"
3. Enter password for confirmation
4. Enter current TOTP code
5. Backend verifies both password and TOTP
6. Disable 2FA and delete secret
7. Delete all backup codes
8. Revoke all trusted devices
9. 2FA disabled ✓
```

---

### Flow 5: Lost Device Recovery

```
1. User cannot access authenticator app
2. User clicks "I lost my device" on login
3. Frontend shows backup code input
4. User enters one of their backup codes
5. Backend verifies backup code
6. If valid, issue session cookie
7. Prompt user to:
   a. Regenerate backup codes
   b. Re-setup 2FA with new device
   c. Or disable 2FA
```

---

## Implementation Plan

### Phase 1: Backend API (Week 1-2)

**Tasks**:
- [ ] Install dependencies: `pyotp`, `qrcode`, `argon2-cffi`
- [ ] Create database migrations for `user_2fa`, `totp_backup_codes`, `trusted_devices`
- [ ] Implement TOTP secret encryption/decryption utilities
- [ ] Implement backup code generation and hashing
- [ ] Create API endpoints:
  - `POST /api/auth/v2/totp/setup`
  - `POST /api/auth/v2/totp/verify-setup`
  - `POST /api/auth/v2/totp/disable`
  - `POST /api/auth/v2/totp/backup-codes/regenerate`
- [ ] Update login endpoint to handle TOTP verification
- [ ] Implement rate limiting for TOTP endpoints
- [ ] Add unit tests for TOTP logic

**Dependencies**:
```python
# requirements.txt
pyotp==2.9.0
qrcode[pil]==7.4.2
argon2-cffi==23.1.0
cryptography==41.0.7
```

---

### Phase 2: Frontend UI (Week 2-3)

**Tasks**:
- [ ] Create 2FA settings page component
- [ ] Implement QR code display modal
- [ ] Create TOTP code input component (6 digits)
- [ ] Create backup codes display/download component
- [ ] Update login flow to handle 2FA prompts
- [ ] Add "Remember this device" checkbox
- [ ] Implement backup code input flow
- [ ] Add 2FA status indicator in user menu
- [ ] Create device management UI (trusted devices list)
- [ ] Add unit tests for 2FA components

**Components**:
```
src/components/2FA/
├── TwoFactorSetup.tsx
├── TwoFactorVerify.tsx
├── BackupCodes.tsx
├── TotpInput.tsx
├── QRCodeDisplay.tsx
├── TrustedDevices.tsx
└── __tests__/
    ├── TwoFactorSetup.test.tsx
    ├── TotpInput.test.tsx
    └── BackupCodes.test.tsx
```

---

### Phase 3: Testing & QA (Week 3-4)

**Tasks**:
- [ ] Write integration tests for complete 2FA flows
- [ ] Test time skew scenarios (±30 seconds)
- [ ] Test rate limiting and lockout scenarios
- [ ] Test backup code usage and regeneration
- [ ] Test device fingerprinting and "remember device"
- [ ] Security audit of encryption and hashing
- [ ] Performance testing (TOTP verification latency)
- [ ] Cross-browser testing
- [ ] Mobile responsiveness testing

**Test Coverage Goals**:
- Backend: 90%+ coverage for 2FA modules
- Frontend: 80%+ coverage for 2FA components
- E2E: Complete user flows tested

---

### Phase 4: Feature Flag & Rollout (Week 4)

**Tasks**:
- [ ] Implement feature flag: `FEATURE_2FA_ENABLED`
- [ ] Deploy to staging environment
- [ ] Internal team testing (dogfooding)
- [ ] Beta rollout to 10% of users
- [ ] Monitor error rates and user feedback
- [ ] Gradual rollout to 50%, then 100%
- [ ] Update documentation and help center

**Feature Flag Configuration**:
```python
# config.py
FEATURE_2FA_ENABLED = os.getenv("FEATURE_2FA_ENABLED", "false").lower() == "true"

# Usage
if FEATURE_2FA_ENABLED:
    # Show 2FA setup option
    pass
```

---

## Testing Strategy

### Unit Tests

**Backend**:
```python
# tests/test_totp.py
def test_generate_totp_secret():
    secret = generate_totp_secret()
    assert len(secret) == 32  # Base32 encoded
    assert secret.isalnum()

def test_verify_totp_code_valid():
    secret = "JBSWY3DPEHPK3PXP"
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code) == True

def test_verify_totp_code_invalid():
    secret = "JBSWY3DPEHPK3PXP"
    assert verify_totp_code(secret, "000000") == False

def test_backup_code_generation():
    codes = generate_backup_codes()
    assert len(codes) == 8
    for code in codes:
        assert len(code) == 19  # XXXX-XXXX-XXXX-XXXX
```

**Frontend**:
```typescript
// TotpInput.test.tsx
describe('TotpInput', () => {
  it('should accept 6-digit codes only', () => {
    render(<TotpInput onSubmit={mockSubmit} />);
    const input = screen.getByRole('textbox');
    
    fireEvent.change(input, { target: { value: '123456' } });
    expect(input).toHaveValue('123456');
    
    fireEvent.change(input, { target: { value: '1234567' } });
    expect(input).toHaveValue('123456'); // Truncated
  });
  
  it('should auto-submit when 6 digits entered', async () => {
    render(<TotpInput onSubmit={mockSubmit} />);
    const input = screen.getByRole('textbox');
    
    fireEvent.change(input, { target: { value: '123456' } });
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith('123456');
    });
  });
});
```

---

### Integration Tests

```python
# tests/test_2fa_flow.py
async def test_complete_2fa_setup_flow(client, test_user):
    # 1. Setup TOTP
    response = await client.post(
        "/api/auth/v2/totp/setup",
        json={"password": "test_password"}
    )
    assert response.status_code == 200
    data = response.json()
    secret = data["secret"]
    backup_codes = data["backup_codes"]
    
    # 2. Verify setup
    totp = pyotp.TOTP(secret)
    code = totp.now()
    response = await client.post(
        "/api/auth/v2/totp/verify-setup",
        json={"code": code}
    )
    assert response.status_code == 200
    assert response.json()["enabled"] == True
    
    # 3. Login with 2FA
    response = await client.post(
        "/api/auth/v2/login",
        json={
            "email": test_user.email,
            "password": "test_password",
            "totp_code": totp.now()
        }
    )
    assert response.status_code == 200
    assert "session_token" in response.cookies
```

---

### E2E Tests (Playwright)

```typescript
// e2e/2fa-setup.spec.ts
test('user can enable 2FA', async ({ page }) => {
  await page.goto('/settings/security');
  await page.click('text=Enable Two-Factor Authentication');
  
  // Enter password
  await page.fill('[name="password"]', 'test_password');
  await page.click('text=Continue');
  
  // QR code should be displayed
  await expect(page.locator('img[alt="QR Code"]')).toBeVisible();
  
  // Simulate scanning QR code and entering code
  const secret = await page.getAttribute('[data-secret]', 'data-secret');
  const totp = new TOTP(secret);
  const code = totp.now();
  
  await page.fill('[name="totp_code"]', code);
  await page.click('text=Verify');
  
  // Backup codes should be displayed
  await expect(page.locator('text=Backup Codes')).toBeVisible();
  await page.click('text=I have saved my backup codes');
  
  // 2FA should be enabled
  await expect(page.locator('text=Two-Factor Authentication: Enabled')).toBeVisible();
});
```

---

## Rollout Strategy

### Phase 1: Internal Testing (Week 1)

**Audience**: Engineering team (5-10 users)  
**Goal**: Validate core functionality and UX  
**Metrics**:
- Setup success rate: >95%
- Login success rate with 2FA: >98%
- Average setup time: <2 minutes

---

### Phase 2: Beta Rollout (Week 2)

**Audience**: 10% of users (opt-in)  
**Goal**: Gather feedback and identify edge cases  
**Feature Flag**: `FEATURE_2FA_BETA=true`  
**Metrics**:
- Adoption rate: Track % of users who enable 2FA
- Support tickets: Monitor 2FA-related issues
- Backup code usage: Track how often users need recovery

---

### Phase 3: General Availability (Week 3-4)

**Audience**: All users (opt-in)  
**Goal**: Full rollout with monitoring  
**Feature Flag**: `FEATURE_2FA_ENABLED=true`  
**Metrics**:
- Overall adoption rate
- Login failure rate (should not increase)
- Account lockout rate
- Support ticket volume

---

### Phase 4: Mandatory 2FA (Future)

**Audience**: Admin users first, then all users  
**Timeline**: Q1 2026  
**Requirements**:
- 90-day notice to all users
- Grace period for enrollment
- Support resources and documentation
- Account recovery process

---

## Risk Mitigation

### Risk 1: User Lockout

**Scenario**: User loses device and backup codes  
**Mitigation**:
- Prominent backup code download during setup
- Email reminder to save backup codes
- Support process for account recovery (identity verification)
- Admin override capability (with audit log)

---

### Risk 2: Time Sync Issues

**Scenario**: User's device clock is incorrect  
**Mitigation**:
- Accept codes from ±1 time window (90 seconds total)
- Display helpful error message suggesting time sync
- Backup code option always available

---

### Risk 3: Adoption Resistance

**Scenario**: Users don't want to enable 2FA  
**Mitigation**:
- Clear communication of security benefits
- Optional initially (not mandatory)
- Smooth UX with minimal friction
- Incentives for early adopters (e.g., security badge)

---

### Risk 4: Performance Impact

**Scenario**: TOTP verification adds latency to login  
**Mitigation**:
- Optimize TOTP verification (<50ms)
- Cache encrypted secrets in Redis
- Monitor P95 latency for login endpoint
- Load testing before rollout

---

## Success Metrics

### Adoption Metrics

- **Target**: 30% of users enable 2FA within 3 months
- **Measurement**: Track `user_2fa.enabled = true` count
- **Goal**: Increase security posture across user base

### Performance Metrics

- **TOTP Verification Latency**: <50ms P95
- **Login Success Rate**: >98% (no degradation)
- **Setup Completion Rate**: >90% (users who start setup complete it)

### Support Metrics

- **2FA-Related Tickets**: <5% of total support volume
- **Account Recovery Requests**: <1% of 2FA users per month
- **Average Resolution Time**: <24 hours

---

## Future Enhancements

### Phase 2 Features (Q1 2026)

1. **SMS/Email Backup**:
   - Send backup codes via SMS or email
   - Useful for users who lose backup codes

2. **WebAuthn/FIDO2 Support**:
   - Hardware security keys (YubiKey, etc.)
   - Biometric authentication (Face ID, Touch ID)

3. **Multiple Authenticator Apps**:
   - Allow users to register multiple TOTP devices
   - Useful for backup devices

4. **Admin Dashboard**:
   - View 2FA adoption rates
   - Manage user 2FA status
   - Audit logs for 2FA events

5. **Risk-Based Authentication**:
   - Skip 2FA for trusted devices/locations
   - Require 2FA for high-risk actions (e.g., changing email)

---

## References

- [RFC 6238: TOTP](https://tools.ietf.org/html/rfc6238)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Google Authenticator Specification](https://github.com/google/google-authenticator/wiki/Key-Uri-Format)
- [pyotp Documentation](https://pyauth.github.io/pyotp/)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-02  
**Next Review**: After Phase 1 completion
