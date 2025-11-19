# Deprecated API Endpoints

This document tracks deprecated API endpoints, their replacement endpoints, and removal timelines.

---

## Active Deprecations

### 1. `/api/auth/v2/totp/verify-login` (POST)

**Status**: ⚠️ DEPRECATED (November 2025)  
**Removal Date**: Q2 2026  
**Replacement**: `/api/auth/v2/2fa/challenge` (POST)

**Reason for Deprecation**:
The old endpoint required password re-transmission during 2FA verification, creating unnecessary security risk:
- Password transmitted twice over the network
- Increased attack surface for password interception
- Password stored in browser memory longer
- Violates principle of least privilege

**Migration Guide**:

**Old Flow (Deprecated)**:
```
1. POST /api/auth/v2/login
   Request: {email, password}
   Response: {requires_2fa: true, user: {...}}

2. POST /api/auth/v2/totp/verify-login
   Request: {email, password, totp_code}
   Response: {success: true, user: {...}} + Set-Cookie: access_token, refresh_token
```

**New Flow (Recommended)**:
```
1. POST /api/auth/v2/login
   Request: {email, password}
   Response: {requires_2fa: true, tmp_login_token: "jwt-token", user: {...}}

2. POST /api/auth/v2/2fa/challenge
   Headers: Authorization: Bearer {tmp_login_token}
   Request: {totp_code: "123456"}
   Response: {success: true, user: {...}} + Set-Cookie: access_token, refresh_token
```

**Key Differences**:
- ✅ Password transmitted only once (during initial login)
- ✅ JWT-based pre-auth token (short-lived, one-time-use)
- ✅ Token transmitted via Authorization header (not in request body)
- ✅ Atomic token consumption prevents replay attacks
- ✅ Scope enforcement (enroll vs challenge)

**Code Changes Required**:

**Frontend (TypeScript/JavaScript)**:
```typescript
// OLD (Deprecated)
const response = await fetch('/api/auth/v2/totp/verify-login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: userEmail,
    password: userPassword,  // ❌ Password sent again
    totp_code: totpCode
  })
});

// NEW (Recommended)
// Step 1: Login
const loginResponse = await fetch('/api/auth/v2/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email: userEmail, password: userPassword})
});
const {tmp_login_token} = await loginResponse.json();

// Step 2: 2FA Challenge
const response = await fetch('/api/auth/v2/2fa/challenge', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${tmp_login_token}`  // ✅ JWT token
  },
  body: JSON.stringify({totp_code: totpCode})
});
```

**Backend (Python)**:
```python
# OLD (Deprecated)
@totp_bp.route('/verify-login', methods=['POST'])
def verify_totp_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')  # ❌ Password received again
    totp_code = data.get('totp_code')
    # ... verify password and TOTP

# NEW (Recommended)
@auth_2fa_bp.route('/challenge', methods=['POST'])
@pre_auth_required  # ✅ Validates JWT token from Authorization header
@pre_auth_scope_required('challenge')  # ✅ Enforces scope
def challenge_2fa():
    data = request.get_json()
    totp_code = data.get('totp_code')
    # ... verify TOTP only (no password needed)
```

**Documentation**:
- Design Document: `docs/2fa-owner-launch/02-pre-auth-token-design.md`
- Implementation: `handoff/20250928/40_App/api-backend/src/routes/auth_2fa.py`
- Tests: `handoff/20250928/40_App/api-backend/tests/test_preauth_*.py`

**Support**:
- The deprecated endpoint will continue to work until Q2 2026
- Backward compatibility is maintained (fallback to password flow)
- Deprecation warnings are logged when the old endpoint is used

---

## Removed Deprecations

None yet.

---

## Deprecation Policy

**Deprecation Timeline**:
1. **Announcement**: Endpoint marked as deprecated in documentation and code
2. **Warning Period**: 6 months minimum (deprecation warnings logged)
3. **Removal Notice**: 3 months before removal, send email notifications
4. **Removal**: Endpoint removed from codebase

**Backward Compatibility**:
- Deprecated endpoints continue to function during warning period
- Breaking changes are avoided when possible
- Migration guides provided for all deprecations

**Communication Channels**:
- API documentation (this file)
- Release notes
- Email notifications to API consumers
- Deprecation warnings in API responses (via headers)

---

**Last Updated**: November 8, 2025  
**Maintained By**: Engineering Team
