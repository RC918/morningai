# Phase 3 Testing Guide

## Overview
This document provides testing guidelines for Phase 3 multi-tenant features. Engineers should implement comprehensive tests based on these patterns.

---

## Backend API Testing

### Tenant API Endpoints (`/api/tenant/*`)

#### Test Coverage Required:

**1. GET `/api/tenant/me`**
- ✅ Success: Authenticated user with tenant assignment
- ✅ Error: User not assigned to any tenant (404)
- ✅ Error: Invalid/expired JWT token (401)
- ✅ Error: Database connection failure (500)

**2. GET `/api/tenant/members`**
- ✅ Success: Return list of members for user's tenant
- ✅ Empty: Tenant has only one member (self)
- ✅ Permission: Cannot see members from other tenants
- ✅ Error: User not in tenant (403)

**3. PUT `/api/tenant/members/<id>`**
- ✅ Success: Owner/admin updates member role
- ✅ Forbidden: Member tries to update roles (403)
- ✅ Validation: Invalid role rejected (400)
- ✅ Cross-tenant: Cannot update users from other tenants (403)
- ✅ Self-demotion: Owner cannot demote themselves if last owner

**4. GET `/api/tenant/info`**
- ✅ Success: Return tenant stats (member count, task count)
- ✅ Accuracy: Counts match actual database records
- ✅ Isolation: Only show current tenant's data

### Tenant Isolation Testing

#### Database RLS Policies

**Test Patterns:**
```python
def test_rls_isolation():
    """Verify users can only access their tenant's data"""
    # Create two users in different tenants
    user_a = create_test_user(tenant='tenant-a')
    user_b = create_test_user(tenant='tenant-b')
    
    # Create task as user A
    task = create_task(user=user_a, question='test')
    
    # Verify user B cannot see task
    response = get_task(task_id, auth=user_b)
    assert response.status == 404 or len(response.data) == 0
    
    # Verify user A can see task
    response = get_task(task_id, auth=user_a)
    assert len(response.data) == 1
```

#### Tenant ID Resolution

**Test fail-loudly behavior:**
```python
def test_tenant_resolution_fails_loudly():
    """Verify no silent fallbacks to default tenant"""
    # User not in user_profiles table
    user_id = 'orphan-user-id'
    
    # Should raise exception, not default to tenant
    with pytest.raises(ValueError, match="No user_profile found"):
        fetch_user_tenant_id(user_id)
```

**Test error responses:**
```python
def test_faq_endpoint_without_tenant():
    """POST /api/agent/faq should fail if tenant not found"""
    # Mock user without tenant assignment
    response = client.post('/api/agent/faq', 
                          json={'question': 'test'},
                          headers={'Authorization': f'Bearer {orphan_user_token}'})
    
    assert response.status_code == 403
    assert 'not assigned to any organization' in response.json['error']['message']
```

---

## Frontend Component Testing

### TenantContext

**Test file:** `frontend-dashboard/src/tests/TenantContext.test.jsx`

**Required test cases:**

1. **Successful tenant fetch**
   ```jsx
   it('should load tenant info on mount', async () => {
     // Mock fetch to return tenant data
     // Verify loading → success transition
     // Verify tenant state populated correctly
   });
   ```

2. **Error handling**
   ```jsx
   it('should handle 404 not found', async () => {
     // Mock 404 response
     // Verify error state set correctly
     // Verify error message displayed to user
   });
   ```

3. **Token refresh**
   ```jsx
   it('should handle token expiration', async () => {
     // Mock 401 unauthorized
     // Verify redirects to login or refreshes token
   });
   ```

### TenantSettings Component

**Test file:** `frontend-dashboard/src/tests/TenantSettings.test.jsx`

**Required test cases:**

1. **Organization info display**
   ```jsx
   it('should display org name and stats', async () => {
     // Mock /api/tenant/info response
     // Verify org name rendered
     // Verify member count rendered
     // Verify task count rendered
   });
   ```

2. **Member list**
   ```jsx
   it('should display member list with roles', async () => {
     // Mock /api/tenant/members response
     // Verify each member rendered with correct role badge
     // Verify join dates formatted correctly
   });
   ```

3. **Role updates** (owner/admin only)
   ```jsx
   it('should allow owner to change member roles', async () => {
     // Mock current user as owner
     // Mock /api/tenant/members PUT success
     // Verify role dropdown appears for owners
     // Verify role update triggers API call
     // Verify success message displayed
   });
   ```

---

## Integration Testing

### End-to-End Tenant Flow

**Test scenario:**
1. New user signs up via Supabase
2. Backfill script creates user_profile entry
3. User logs in → Frontend fetches tenant via TenantContext
4. User creates FAQ task → API assigns to correct tenant
5. User navigates to /tenant-settings → Sees organization info
6. Owner invites new member (future feature)

**Manual test checklist:**
- [ ] Sign up new user in Supabase
- [ ] Verify user_profile row created with default tenant
- [ ] Login → Check tenant ID in browser localStorage
- [ ] Create FAQ task → Verify tenant_id in database
- [ ] Check `/tenant-settings` page loads
- [ ] Verify member list shows current user

---

## SQL Test Scripts

**Location:** `migrations/tests/`

### test_phase3_tenant_isolation.sql

Run this to verify RLS policies work correctly:
```bash
psql $DATABASE_URL -f migrations/tests/test_phase3_tenant_isolation.sql
```

**Expected output:**
- ✅ Users can only see their own tenant's tasks
- ✅ INSERT attempts to other tenants fail
- ✅ UPDATE attempts on other tenants' tasks fail
- ✅ DELETE limited to own tenant

### test_phase3_api_integration.sql

Tests API integration with database:
```bash
psql $DATABASE_URL -f migrations/tests/test_phase3_api_integration.sql
```

---

## Performance Testing

### Load Testing Tenant API

**Tool:** `locust` or `k6`

**Scenario:**
- 100 concurrent users
- Each user fetches `/api/tenant/me` 10 times
- Each user lists `/api/tenant/members` 5 times

**Success criteria:**
- P95 latency < 200ms
- No database deadlocks
- No cross-tenant data leakage under load

---

## Security Testing

### Penetration Testing Checklist

1. **JWT token manipulation**
   - [ ] Try to forge JWT with different `sub` (user_id)
   - [ ] Verify signature validation rejects forged tokens
   - [ ] Test expired token handling

2. **Tenant isolation bypass attempts**
   - [ ] Modify tenant_id in POST body (should be ignored)
   - [ ] Try to access other tenant's members list
   - [ ] Attempt SQL injection in tenant queries

3. **Authorization boundary testing**
   - [ ] Member tries to update other members' roles
   - [ ] Viewer tries to create tasks (if roles enforced)
   - [ ] Cross-tenant task access attempts

---

## Debugging Test Failures

### Common Issues

**Problem:** "User not found in user_profiles"
- **Cause:** Backfill script not run or user created after backfill
- **Fix:** Run backfill script: `psql $DATABASE_URL -f migrations/backfill_user_profiles.sql`

**Problem:** "403 Forbidden" on all API calls
- **Cause:** RLS policies blocking access
- **Debug:** Check if user_id matches auth.uid() in database session
- **Fix:** Verify JWT token has correct `sub` field

**Problem:** Tests pass locally but fail in CI
- **Cause:** Different database state or missing migrations
- **Fix:** Ensure CI runs migrations before tests

---

## Coverage Goals

**Backend:**
- Tenant API routes: 90%+ coverage
- fetch_user_tenant_id(): 100% coverage (critical security function)
- RLS policy logic: Manual SQL testing required

**Frontend:**
- TenantContext: 80%+ coverage
- TenantSettings component: 70%+ coverage
- Error boundary testing: Required

---

## Next Steps

**For Engineering Team:**
1. Implement unit tests following patterns above
2. Run SQL test scripts in staging environment
3. Execute manual E2E test checklist
4. Set up CI to run tests on every PR
5. Add performance benchmarks to CI pipeline

**Recommended Testing Framework:**
- Backend: `pytest` + `pytest-cov` (already in use)
- Frontend: `vitest` + `@testing-library/react`
- E2E: `playwright` or `cypress`

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025  
**Maintained By:** Engineering Team
