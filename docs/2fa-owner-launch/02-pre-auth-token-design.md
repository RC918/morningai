# Pre-Auth Token (Challenge Token) Design Document

**Document Version**: 1.0  
**Date**: 2025-11-04  
**Priority**: P0 (Security Enhancement)  
**Target Delivery**: Week 1 (November 11, 2025)  
**Status**: 📋 Design Phase - Awaiting CTO Approval

---

## Executive Summary

This document proposes a Pre-Auth Token (Challenge Token) mechanism to eliminate password re-transmission during 2FA verification. Currently, the `/api/auth/v2/totp/verify-login` endpoint requires users to send their password again along with the TOTP code, creating unnecessary security risk.

**Problem**: Password transmitted twice (login + 2FA verification)  
**Solution**: Issue short-lived, one-time-use challenge token after initial authentication  
**Impact**: Reduces password exposure window by 50%, improves security posture

---

## Problem Statement

### Current Flow (Insecure)
```
1. User → POST /api/auth/v2/login {email, password}
   ← Response: {requires_2fa: true, user: {...}}

2. User → POST /api/auth/v2/totp/verify-login {email, password, totp_code}
   ← Response: {success: true, user: {...}} + Set-Cookie: access_token, refresh_token
```

**Security Issues**:
- Password transmitted twice over the network
- Increased attack surface for password interception
- Password stored in browser memory longer
- Violates principle of least privilege (password not needed after initial auth)

### Proposed Flow (Secure)
```
1. User → POST /api/auth/v2/login {email, password}
   ← Response: {requires_2fa: true, user: {...}} + Set-Cookie: pre_auth_token

2. User → POST /api/auth/v2/totp/verify-login {totp_code}
   (pre_auth_token sent automatically via HttpOnly cookie)
   ← Response: {success: true, user: {...}} + Set-Cookie: access_token, refresh_token
   (pre_auth_token deleted)
```

**Security Improvements**:
- Password transmitted only once
- Pre-auth token is short-lived (2-5 minutes)
- Pre-auth token is one-time-use (deleted after verification)
- Pre-auth token stored in HttpOnly cookie (not accessible to JavaScript)

---

## Goals and Non-Goals

### Goals
- ✅ Eliminate password re-transmission during 2FA verification
- ✅ Maintain backward compatibility with existing frontend
- ✅ Support graceful degradation (fallback to password if pre_auth missing)
- ✅ Implement one-time-use tokens (prevent replay attacks)
- ✅ Short TTL (2-5 minutes) to minimize attack window
- ✅ Feature flag controlled (FEATURE_2FA_PREAUTH)

### Non-Goals
- ❌ Replace refresh token mechanism
- ❌ Support multi-device 2FA setup (out of scope)
- ❌ Implement biometric authentication
- ❌ Change existing JSON response shapes (frontend compatibility)

---

## Threat Model and Risk Analysis

### Threats Mitigated
1. **Password Interception**: Reduces password transmission by 50%
2. **Man-in-the-Middle (MITM)**: Pre-auth token useless without TOTP code
3. **Replay Attacks**: One-time-use tokens prevent replay
4. **Session Fixation**: Token tied to user_id + nonce

### Residual Risks
1. **Token Theft**: If pre_auth cookie stolen, attacker still needs TOTP code
   - **Mitigation**: Short TTL (2-5 minutes), SameSite=Lax, HttpOnly, Secure
2. **Timing Attacks**: Token validation timing could leak information
   - **Mitigation**: Constant-time comparison for token validation
3. **Rate Limiting**: Brute force TOTP with stolen pre_auth token
   - **Mitigation**: Existing rate limiting on /verify-login (10 attempts/hour)

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Token Theft | Low | Medium | HttpOnly, Secure, SameSite=Lax, Short TTL |
| Replay Attack | Low | Low | One-time-use, Redis tracking |
| TOTP Brute Force | Medium | Medium | Rate limiting (existing) |
| CSRF | Low | Low | SameSite=Lax (sufficient for login flows) |

**Overall Risk**: ✅ **LOW** (with mitigations)

---

## Design Details

### Token Format

**Option 1: Opaque Random Token (Recommended)**
```python
pre_auth_token = secrets.token_urlsafe(32)  # 256-bit entropy
```

**Storage**: Redis
```
Key: preauth:{user_id}:{nonce}
Value: {
    "issued_at": "2025-11-04T08:45:12Z",
    "attempts": 0,
    "device_fingerprint": "sha256(...)",
    "email": "owner@example.com"
}
TTL: 300 seconds (5 minutes)
```

**Advantages**:
- Easy to revoke (delete Redis key)
- No signature verification overhead
- Opaque (no information leakage)
- Stateful (can track attempts)

**Option 2: Signed JWT (Not Recommended)**
```python
pre_auth_token = jwt.encode({
    "user_id": "...",
    "nonce": "...",
    "exp": datetime.utcnow() + timedelta(minutes=5)
}, JWT_SECRET_KEY, algorithm='HS256')
```

**Disadvantages**:
- Cannot revoke without blacklist (defeats purpose)
- Signature verification overhead
- Larger token size
- Stateless (cannot track attempts)

**Decision**: Use **Option 1 (Opaque Random Token)** for simplicity and revocability.

---

### Token Lifecycle

#### 1. Issuance (Login Endpoint)
**Endpoint**: `POST /api/auth/v2/login`

**When**: Only when `requires_2fa: true`

**Implementation**:
```python
# In auth_enhanced.py:login()
if check_2fa_required(user['id']):
    # Generate pre-auth token
    pre_auth_token = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(16)
    
    # Store in Redis
    redis_client = get_redis_client()
    redis_key = f"preauth:{user['id']}:{nonce}"
    redis_client.setex(
        redis_key,
        300,  # 5 minutes TTL
        json.dumps({
            "issued_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "email": user['email'],
            "nonce": nonce
        })
    )
    
    # Set HttpOnly cookie
    response_data = {
        'requires_2fa': True,
        'user': {
            'id': user['id'],
            'email': user['email']
        }
    }
    response = make_response(jsonify(response_data), 200)
    response.set_cookie(
        'pre_auth_token',
        pre_auth_token,
        max_age=300,  # 5 minutes
        httponly=True,
        secure=COOKIE_SECURE,
        samesite='Lax',
        path='/api/auth/v2/totp'
    )
    return response
```

#### 2. Consumption (Verify Endpoint)
**Endpoint**: `POST /api/auth/v2/totp/verify-login`

**Implementation**:
```python
# In totp.py:verify_totp_login()
def verify_totp_login():
    if not is_2fa_feature_enabled():
        return jsonify({'error': '2FA feature is not enabled'}), 403
    
    try:
        data = request.get_json()
        totp_code = data.get('totp_code', '').strip()
        backup_code = data.get('backup_code', '').strip()
        
        # Try pre-auth token first (new flow)
        pre_auth_token = request.cookies.get('pre_auth_token')
        
        if pre_auth_token:
            # New flow: Use pre-auth token
            user = validate_and_consume_preauth_token(pre_auth_token)
            if not user:
                return jsonify({'error': 'Invalid or expired pre-auth token'}), 401
        else:
            # Fallback: Use email + password (backward compatibility)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'error': 'Pre-auth token or email/password required'}), 400
            
            from ..services.auth_service import authenticate_user
            user = authenticate_user(email, password)
            if not user:
                return jsonify({'error': 'Invalid email or password'}), 401
        
        user_id = user['id']
        
        # Verify TOTP/backup code (existing logic)
        if backup_code:
            is_valid, remaining = verify_backup_code_for_login(user_id, backup_code)
            if not is_valid:
                return jsonify({'error': 'Invalid backup code'}), 401
        elif totp_code:
            if len(totp_code) != 6 or not totp_code.isdigit():
                return jsonify({'error': 'Invalid TOTP code format'}), 400
            
            is_valid = verify_totp_for_login(user_id, totp_code)
            if not is_valid:
                return jsonify({'error': 'Invalid TOTP code'}), 401
        else:
            return jsonify({'error': 'TOTP code or backup code required'}), 400
        
        # Generate session tokens (existing logic)
        access_token, access_expiry_ms = generate_access_token(
            user_id, user['email'], user['role']
        )
        refresh_token = generate_refresh_token(user_id, user['email'])
        
        response_data = {
            'success': True,
            'user_id': user_id,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'tenantId': user['tenant_id']
            },
            'tokens': {
                'expiresAt': access_expiry_ms
            }
        }
        
        response = make_response(jsonify(response_data), 200)
        set_auth_cookies(response, access_token, refresh_token, access_expiry_ms)
        
        # Clear pre-auth cookie
        response.set_cookie(
            'pre_auth_token',
            '',
            max_age=0,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite='Lax',
            path='/api/auth/v2/totp'
        )
        
        return response
```

#### 3. Validation Helper
```python
def validate_and_consume_preauth_token(token: str) -> Optional[Dict]:
    """
    Validate and consume pre-auth token (one-time-use)
    
    Returns:
        User dict or None if invalid/expired
    """
    redis_client = get_redis_client()
    
    # Find matching Redis key (scan for preauth:*:*)
    for key in redis_client.scan_iter(match="preauth:*:*"):
        stored_data = redis_client.get(key)
        if not stored_data:
            continue
        
        data = json.loads(stored_data)
        
        # Constant-time comparison to prevent timing attacks
        if secrets.compare_digest(token, key.split(':')[-1]):
            # Extract user_id from key
            user_id = key.split(':')[1]
            
            # Delete token (one-time-use)
            redis_client.delete(key)
            
            # Get user data
            from ..services.auth_service import get_user_by_id
            user = get_user_by_id(user_id)
            
            if user:
                logger.info(f"Pre-auth token consumed for user {user_id}")
                return user
    
    logger.warning("Invalid or expired pre-auth token")
    return None
```

---

## API Changes

### Login Endpoint (`POST /api/auth/v2/login`)

**Request**: No changes
```json
{
  "email": "owner@example.com",
  "password": "SecurePassword123!"
}
```

**Response**: No JSON changes, adds cookie
```json
{
  "requires_2fa": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "owner@example.com"
  }
}
```

**New Cookie**:
```
Set-Cookie: pre_auth_token=<token>; Max-Age=300; HttpOnly; Secure; SameSite=Lax; Path=/api/auth/v2/totp
```

---

### Verify Login Endpoint (`POST /api/auth/v2/totp/verify-login`)

**Request (New Flow - Preferred)**:
```json
{
  "totp_code": "123456"
}
```
+ Cookie: `pre_auth_token=<token>`

**Request (Fallback - Backward Compatible)**:
```json
{
  "email": "owner@example.com",
  "password": "SecurePassword123!",
  "totp_code": "123456"
}
```

**Response**: No changes
```json
{
  "success": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "owner@example.com",
    "name": "Owner User",
    "role": "owner",
    "tenantId": "tenant-001"
  },
  "tokens": {
    "expiresAt": 1730710512000
  }
}
```

**Cookie Cleared**:
```
Set-Cookie: pre_auth_token=; Max-Age=0; HttpOnly; Secure; SameSite=Lax; Path=/api/auth/v2/totp
```

---

## Configuration

### Environment Variables

```bash
# Feature flag (default: false)
FEATURE_2FA_PREAUTH=true

# Pre-auth token TTL in seconds (default: 300 = 5 minutes)
PREAUTH_TOKEN_TTL=300

# Maximum verification attempts per pre-auth token (default: 3)
PREAUTH_MAX_ATTEMPTS=3
```

### Feature Flag Strategy

**Phase 1: Disabled by Default** (Week 1)
- `FEATURE_2FA_PREAUTH=false`
- All users use password + TOTP flow
- Code deployed but inactive

**Phase 2: Staging Enabled** (Week 1)
- `FEATURE_2FA_PREAUTH=true` (staging only)
- Test with internal Owner accounts
- Monitor logs for errors

**Phase 3: Canary Rollout** (Week 2)
- `FEATURE_2FA_PREAUTH=true` (10% of production users)
- Monitor metrics: success rate, error rate, latency
- Rollback if error rate > 1%

**Phase 4: Full Rollout** (Week 2)
- `FEATURE_2FA_PREAUTH=true` (100% of production users)
- Deprecate password fallback after 30 days
- Remove fallback code in Week 6

---

## Logging and Metrics

### Log Events
```python
# Issuance
logger.info(f"Pre-auth token issued for user {user_id}, expires in {ttl}s")

# Consumption (success)
logger.info(f"Pre-auth token consumed for user {user_id}")

# Consumption (failure)
logger.warning(f"Invalid or expired pre-auth token")

# Fallback to password
logger.info(f"Pre-auth token not found, using password fallback for user {user_id}")
```

### Metrics (Prometheus/CloudWatch)
```python
# Counters
preauth_tokens_issued_total
preauth_tokens_consumed_total
preauth_tokens_expired_total
preauth_tokens_invalid_total
preauth_fallback_to_password_total

# Histograms
preauth_token_lifetime_seconds
preauth_verification_duration_seconds
```

### Alerts
```yaml
- alert: PreAuthTokenHighFailureRate
  expr: rate(preauth_tokens_invalid_total[5m]) > 0.1
  for: 5m
  annotations:
    summary: "High pre-auth token failure rate (>10%)"
    
- alert: PreAuthTokenNotUsed
  expr: rate(preauth_fallback_to_password_total[5m]) > 0.5
  for: 10m
  annotations:
    summary: "Pre-auth tokens not being used (>50% fallback)"
```

---

## Rollout Plan

### Week 1: Implementation and Staging
**Dates**: November 4-8, 2025

**Tasks**:
- [ ] Implement pre-auth token issuance in `auth_enhanced.py:login()`
- [ ] Implement pre-auth token validation in `totp.py:verify_totp_login()`
- [ ] Add `validate_and_consume_preauth_token()` helper function
- [ ] Add feature flag `FEATURE_2FA_PREAUTH` (default: false)
- [ ] Write unit tests (token issuance, validation, expiry, one-time-use)
- [ ] Write integration tests (full login → verify flow)
- [ ] Deploy to staging with `FEATURE_2FA_PREAUTH=true`
- [ ] Manual testing on staging (Owner accounts)
- [ ] Create PR #2 (separate from current 2FA PR)

**Acceptance Criteria**:
- ✅ All tests pass (unit + integration)
- ✅ Code review approved by CTO
- ✅ Staging deployment successful
- ✅ Manual testing completed (5 test cases)

---

### Week 2: Canary Rollout and Monitoring
**Dates**: November 11-15, 2025

**Tasks**:
- [ ] Deploy to production with `FEATURE_2FA_PREAUTH=false` (code present, feature off)
- [ ] Enable for 10% of users (canary group)
- [ ] Monitor metrics for 48 hours
  - Success rate > 99%
  - Error rate < 1%
  - Latency < 200ms (p95)
- [ ] If metrics good: increase to 50%
- [ ] Monitor for another 48 hours
- [ ] If metrics good: increase to 100%

**Rollback Criteria**:
- Error rate > 1%
- Success rate < 99%
- User complaints > 5
- Security incident detected

**Rollback Procedure**:
1. Set `FEATURE_2FA_PREAUTH=false` in production
2. Deploy config change (< 5 minutes)
3. Verify fallback to password flow working
4. Investigate root cause
5. Fix and re-deploy to staging

---

## Test Plan

### Unit Tests

**File**: `tests/test_preauth_token.py`

```python
class TestPreAuthToken:
    def test_preauth_token_issuance(self):
        """Test that pre-auth token is issued when 2FA required"""
        # Login with Owner account
        # Assert pre_auth_token cookie is set
        # Assert Redis key exists
        
    def test_preauth_token_consumption(self):
        """Test that pre-auth token can be consumed once"""
        # Issue pre-auth token
        # Verify with TOTP using pre-auth token
        # Assert success
        # Assert Redis key deleted (one-time-use)
        
    def test_preauth_token_expiry(self):
        """Test that pre-auth token expires after TTL"""
        # Issue pre-auth token
        # Wait for TTL + 1 second
        # Attempt to verify with expired token
        # Assert 401 error
        
    def test_preauth_token_replay_attack(self):
        """Test that pre-auth token cannot be reused"""
        # Issue pre-auth token
        # Verify with TOTP (success)
        # Attempt to verify again with same token
        # Assert 401 error
        
    def test_preauth_fallback_to_password(self):
        """Test fallback to password when pre-auth token missing"""
        # Verify with email + password + TOTP (no pre-auth token)
        # Assert success (backward compatibility)
```

### Integration Tests

**File**: `tests/test_2fa_integration.py`

```python
class Test2FAIntegrationWithPreAuth:
    def test_full_login_flow_with_preauth(self):
        """Test complete login flow: login → verify with pre-auth token"""
        # 1. Login with Owner account
        # 2. Assert requires_2fa=true and pre_auth_token cookie set
        # 3. Verify with TOTP code (pre-auth token sent automatically)
        # 4. Assert success and session cookies set
        # 5. Assert pre_auth_token cookie cleared
        
    def test_full_login_flow_without_preauth(self):
        """Test complete login flow: login → verify with password (fallback)"""
        # 1. Login with Owner account
        # 2. Clear pre_auth_token cookie (simulate missing)
        # 3. Verify with email + password + TOTP
        # 4. Assert success (backward compatibility)
```

### Manual Testing Checklist

**Environment**: Staging

**Test Cases**:
1. ✅ Owner login with TOTP (pre-auth token flow)
2. ✅ Owner login with backup code (pre-auth token flow)
3. ✅ Owner login with TOTP (password fallback, no pre-auth token)
4. ✅ Pre-auth token expiry (wait 5 minutes, attempt verify)
5. ✅ Pre-auth token replay attack (use same token twice)
6. ✅ Non-Owner login (no 2FA, no pre-auth token)
7. ✅ Invalid TOTP with pre-auth token (rate limiting)
8. ✅ Remember device with pre-auth token

---

## Timeline and Milestones

| Milestone | Date | Owner | Status |
|-----------|------|-------|--------|
| Design Document Approval | Nov 4, 2025 | CTO | 📋 Pending |
| Implementation Start | Nov 5, 2025 | Devin AI | ⏳ Waiting |
| Unit Tests Complete | Nov 6, 2025 | Devin AI | ⏳ Waiting |
| Integration Tests Complete | Nov 7, 2025 | Devin AI | ⏳ Waiting |
| Staging Deployment | Nov 8, 2025 | Devin AI | ⏳ Waiting |
| Manual Testing Complete | Nov 8, 2025 | QA Team | ⏳ Waiting |
| PR #2 Created | Nov 8, 2025 | Devin AI | ⏳ Waiting |
| Code Review Approval | Nov 9-10, 2025 | CTO | ⏳ Waiting |
| Production Deployment (Flag Off) | Nov 11, 2025 | DevOps | ⏳ Waiting |
| Canary Rollout (10%) | Nov 12, 2025 | DevOps | ⏳ Waiting |
| Full Rollout (100%) | Nov 14, 2025 | DevOps | ⏳ Waiting |
| Deprecate Password Fallback | Dec 14, 2025 | Devin AI | ⏳ Waiting |

**Target Delivery**: ✅ **November 11, 2025** (Week 1 Complete)

---

## Appendix: Sequence Diagrams

### Current Flow (Password Re-transmission)
```
┌──────┐                  ┌────────┐                  ┌─────────┐
│Client│                  │Backend │                  │Database │
└──┬───┘                  └───┬────┘                  └────┬────┘
   │                          │                            │
   │ POST /login              │                            │
   │ {email, password}        │                            │
   ├─────────────────────────>│                            │
   │                          │ Verify password            │
   │                          ├───────────────────────────>│
   │                          │<───────────────────────────┤
   │                          │ Check 2FA required         │
   │                          ├───────────────────────────>│
   │                          │<───────────────────────────┤
   │ {requires_2fa: true}     │                            │
   │<─────────────────────────┤                            │
   │                          │                            │
   │ POST /verify-login       │                            │
   │ {email, password, totp}  │                            │
   ├─────────────────────────>│                            │
   │                          │ Verify password AGAIN      │
   │                          ├───────────────────────────>│
   │                          │<───────────────────────────┤
   │                          │ Verify TOTP                │
   │                          ├───────────────────────────>│
   │                          │<───────────────────────────┤
   │ {success: true}          │                            │
   │ + session cookies        │                            │
   │<─────────────────────────┤                            │
```

### Proposed Flow (Pre-Auth Token)
```
┌──────┐                  ┌────────┐                  ┌─────────┐  ┌─────┐
│Client│                  │Backend │                  │Database │  │Redis│
└──┬───┘                  └───┬────┘                  └────┬────┘  └──┬──┘
   │                          │                            │          │
   │ POST /login              │                            │          │
   │ {email, password}        │                            │          │
   ├─────────────────────────>│                            │          │
   │                          │ Verify password            │          │
   │                          ├───────────────────────────>│          │
   │                          │<───────────────────────────┤          │
   │                          │ Check 2FA required         │          │
   │                          ├───────────────────────────>│          │
   │                          │<───────────────────────────┤          │
   │                          │ Store pre-auth token       │          │
   │                          ├────────────────────────────┼─────────>│
   │ {requires_2fa: true}     │                            │          │
   │ + pre_auth_token cookie  │                            │          │
   │<─────────────────────────┤                            │          │
   │                          │                            │          │
   │ POST /verify-login       │                            │          │
   │ {totp}                   │                            │          │
   │ + pre_auth_token cookie  │                            │          │
   ├─────────────────────────>│                            │          │
   │                          │ Validate pre-auth token    │          │
   │                          ├────────────────────────────┼─────────>│
   │                          │<───────────────────────────┼──────────┤
   │                          │ Delete pre-auth token      │          │
   │                          ├────────────────────────────┼─────────>│
   │                          │ Verify TOTP                │          │
   │                          ├───────────────────────────>│          │
   │                          │<───────────────────────────┤          │
   │ {success: true}          │                            │          │
   │ + session cookies        │                            │          │
   │ - pre_auth_token cookie  │                            │          │
   │<─────────────────────────┤                            │          │
```

---

## Approval

**Prepared By**: Devin AI (Week 0 Sprint - Task 1)  
**Review Required**: CTO  
**Approval Status**: 📋 **PENDING**

**Approval Checklist**:
- [ ] Design approach approved
- [ ] Security risks acceptable
- [ ] Timeline feasible
- [ ] Resource allocation confirmed
- [ ] Feature flag strategy approved

**Approved By**: _________________  
**Date**: _________________  
**Signature**: _________________

---

**Document Owner**: Devin AI  
**Next Review**: After CTO Approval  
**Implementation PR**: TBD (Week 1)
