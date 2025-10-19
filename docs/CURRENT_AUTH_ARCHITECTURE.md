# Current Authentication Architecture

**Document Version**: 1.0  
**Created**: October 18, 2025  
**Last Updated**: October 18, 2025  
**Status**: Production

---

## 📋 Executive Summary

MorningAI currently uses a **custom JWT-based authentication system** with Flask backend. The system does NOT use Supabase Auth - instead, it implements a standalone authentication layer with mock users for development/testing.

**Key Characteristics**:
- Custom JWT implementation (not Supabase Auth)
- Mock user database (not production-ready)
- Role-based access control (RBAC)
- No integration with `auth.users` table
- Stateless authentication via JWT tokens

---

## 🏗️ Architecture Overview

### Authentication Flow

```
┌─────────┐      ┌──────────────┐      ┌──────────────┐
│ Frontend│─────>│ Flask Backend│─────>│ Mock Users DB│
│ (React) │      │  /auth/login │      │ (In-Memory)  │
└─────────┘      └──────────────┘      └──────────────┘
     │                   │                      │
     │  1. POST /login   │                      │
     │  {username, pw}   │                      │
     ├──────────────────>│                      │
     │                   │  2. Verify password  │
     │                   │────────────────────> │
     │                   │<────────────────────┤
     │                   │  3. Generate JWT     │
     │  4. Return JWT    │                      │
     │<──────────────────┤                      │
     │                   │                      │
     │  5. API calls     │                      │
     │  Authorization:   │  6. Verify JWT       │
     │  Bearer <token>   │  decode + validate   │
     ├──────────────────>│──────────────────>  │
     │  7. Response      │                      │
     │<──────────────────┤                      │
```

---

## 🗄️ Database Tables

### Current State

**Tables in Use**:
- ❌ `auth.users` - **NOT USED** (Supabase Auth not enabled)
- ✅ `public.users` - **EXISTS** but may be empty or unused for auth
- ✅ `public.tenants` - **EXISTS** (from RLS Phase 2)
- ✅ `public.agent_tasks` - **EXISTS** with `tenant_id` column

**Current User Count**:
- Production: Unknown (likely 0, using mock users)
- Mock Users (Development): 3 users (admin, operator, viewer)

### Mock Users Configuration

Located in: `api-backend/src/routes/auth.py`

```python
MOCK_USERS = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'password_hash': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123')),
        'role': 'admin'
    },
    'operator': {
        'id': 2,
        'username': 'operator',
        'password_hash': generate_password_hash('operator123'),
        'role': 'operator'  # Normalized to 'analyst'
    },
    'viewer': {
        'id': 3,
        'username': 'viewer',
        'password_hash': generate_password_hash('viewer123'),
        'role': 'viewer'  # Normalized to 'user'
    }
}
```

**⚠️ WARNING**: This is in-memory mock data. Not suitable for production!

---

## 🔐 Authentication Implementation

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | Flask | Latest |
| **JWT Library** | PyJWT | Latest |
| **Password Hashing** | Werkzeug | Latest |
| **Token Storage** | Client-side (LocalStorage/SessionStorage) | N/A |

### JWT Token Structure

**JWT Payload**:
```json
{
  "user_id": 1,
  "username": "admin",
  "role": "admin",
  "exp": 1697654400,
  "iat": 1697568000
}
```

**Token Lifetime**: 24 hours (configurable)

**Secret Key**: Environment variable `JWT_SECRET_KEY` (default: `'your-secret-key'`)

---

## 🛡️ Authorization (RBAC)

### Role Hierarchy

```
admin (超級管理員)
  └─> analyst (分析師, formerly 'operator')
      └─> user (查看者, formerly 'viewer')
```

### Role Permissions

| Role | Permissions | Endpoints |
|------|-------------|-----------|
| **admin** | Full access | All endpoints |
| **analyst** | Data analysis, limited admin | Most endpoints except admin-only |
| **user** | Read-only access | View-only endpoints |

### Role Normalization

The system normalizes legacy role names:

```python
role_mapping = {
    'operator': 'analyst',    # Legacy
    'viewer': 'user',         # Legacy
    'admin': 'admin',
    '超級管理員': 'admin',   # Chinese
    '分析師': 'analyst',      # Chinese
    '操作員': 'analyst',      # Chinese (legacy)
    '查看者': 'user'          # Chinese (legacy)
}
```

---

## 🔗 API Endpoints

### Authentication Endpoints

#### 1. Login
```
POST /auth/login
Body: { "username": "admin", "password": "admin123" }
Response: { "user": {...}, "token": "eyJ..." }
```

#### 2. Verify Token
```
GET /auth/verify
Headers: { "Authorization": "Bearer <token>" }
Response: { "id": 1, "username": "admin", "role": "admin" }
```

#### 3. Logout
```
POST /auth/logout
Response: { "message": "登出成功" }
```
**Note**: Currently a no-op (stateless JWT, no server-side session invalidation)

---

## 🔨 Middleware & Decorators

### Available Decorators

Located in: `api-backend/src/middleware/auth_middleware.py`

1. **`@jwt_required`** - Requires valid JWT token
2. **`@admin_required`** - Requires admin role
3. **`@analyst_required`** - Requires analyst or admin role
4. **`@roles_required('admin', 'analyst')`** - Custom role requirements

**Usage Example**:
```python
from src.middleware.auth_middleware import jwt_required

@app.route('/protected')
@jwt_required
def protected_endpoint():
    user = request.current_user  # Available after auth
    return jsonify({'user_id': user['user_id']})
```

---

## 🖥️ Frontend Integration

### Framework

**Unknown** - Frontend code not found in `handoff/20250928/40_App/frontend-dashboard/`

**Likely Technologies** (based on dependencies):
- React (based on npm package structure)
- TypeScript (based on @types/* packages)
- Radix UI components
- Tailwind CSS

### Auth State Management

**Unknown** - Requires frontend code review

**Expected Flow**:
1. User submits login form
2. Frontend calls `POST /auth/login`
3. JWT token stored in LocalStorage/SessionStorage
4. Token included in `Authorization: Bearer <token>` header
5. On token expiry, user redirected to login

---

## 🚨 Critical Issues & Limitations

### 1. Mock User System (P0 - CRITICAL)

**Issue**: Users are hardcoded in memory  
**Impact**: Not production-ready, loses data on restart  
**Risk**: High - No real user database  

**Recommendation**: 
- Migrate to `public.users` table in Supabase
- OR integrate Supabase Auth (`auth.users`)

---

### 2. No Tenant Awareness (P1 - HIGH)

**Issue**: JWT does not include `tenant_id`  
**Impact**: Cannot enforce tenant isolation at auth layer  
**Risk**: High - Phase 3 requires tenant-aware auth  

**Current JWT Payload**:
```json
{
  "user_id": 1,
  "username": "admin",
  "role": "admin"
  // ❌ Missing: "tenant_id"
}
```

**Required for Phase 3**:
```json
{
  "user_id": 1,
  "username": "admin",
  "role": "admin",
  "tenant_id": "00000000-0000-0000-0000-000000000001"  // ✅ Added
}
```

---

### 3. Weak Secret Key (P0 - CRITICAL)

**Issue**: Default secret is `'your-secret-key'`  
**Impact**: JWT tokens can be forged  
**Risk**: Critical - Anyone can create admin tokens  

**Recommendation**: 
```bash
# Generate strong secret
openssl rand -hex 32

# Set in environment
export JWT_SECRET_KEY="<generated-secret>"
```

---

### 4. No Token Refresh (P2 - MEDIUM)

**Issue**: Tokens expire after 24 hours, no refresh mechanism  
**Impact**: Users must re-login daily  
**Risk**: Medium - Poor UX  

**Recommendation**: Implement refresh token flow

---

### 5. No Password Reset (P2 - MEDIUM)

**Issue**: No `/forgot-password` or `/reset-password` endpoints  
**Impact**: Users cannot recover accounts  
**Risk**: Medium - Manual intervention required  

---

## 🎯 Migration Path to Production

### Option A: Supabase Auth (Recommended)

**Pros**:
- Built-in user management
- Email verification
- Password reset
- OAuth providers (Google, GitHub, etc.)
- RLS integration (`auth.uid()`)

**Cons**:
- Requires frontend migration
- Need to migrate existing mock users

**Effort**: 12-16 hours

---

### Option B: Custom User Table

**Pros**:
- Full control over user schema
- Can add custom fields (tenant_id, etc.)
- No vendor lock-in

**Cons**:
- Must implement email verification
- Must implement password reset
- More code to maintain

**Effort**: 20-24 hours

---

## 📊 Phase 3 Requirements

For Phase 3 (Full Tenant Isolation), authentication must:

1. **Include `tenant_id` in JWT payload**
2. **Auto-fetch user's tenant on login**
3. **Validate tenant membership on protected endpoints**
4. **Support multi-tenant user assignment**

**Proposed JWT Payload (Phase 3)**:
```json
{
  "user_id": "auth-uuid-here",
  "username": "john@example.com",
  "role": "analyst",
  "tenant_id": "tenant-uuid-here",
  "tenant_name": "Acme Corp",
  "exp": 1697654400,
  "iat": 1697568000
}
```

**Backend Changes Required**:
```python
# In auth.py login endpoint
def login():
    # ... existing code ...
    
    # NEW: Fetch user's tenant_id from database
    user_record = supabase.table("users").select("tenant_id").eq("id", user_id).execute()
    tenant_id = user_record.data[0]['tenant_id'] if user_record.data else None
    
    # Add to JWT payload
    token = jwt.encode({
        'user_id': user_data['id'],
        'username': username,
        'role': user_data['role'],
        'tenant_id': tenant_id,  # NEW
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    }, jwt_secret, algorithm='HS256')
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `JWT_SECRET_KEY` | ✅ | `'your-secret-key'` | JWT signing secret |
| `ADMIN_PASSWORD` | ⚠️ | `'admin123'` | Admin user password |
| `SUPABASE_URL` | ❌ | N/A | Supabase project URL (not used in auth) |
| `SUPABASE_SERVICE_ROLE_KEY` | ❌ | N/A | Supabase service key (not used in auth) |

---

## 📚 Code Locations

| Component | File Path |
|-----------|-----------|
| **Auth Routes** | `api-backend/src/routes/auth.py` |
| **Auth Middleware** | `api-backend/src/middleware/auth_middleware.py` |
| **User Model** | `api-backend/src/models/user.py` (if exists) |
| **Tests** | `api-backend/tests/test_auth_endpoints.py` |

---

## ✅ Recommendations for Engineering Team

### Immediate (This Week)

1. **Set strong JWT secret in production**
   ```bash
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Add `tenant_id` to JWT payload** (Phase 3 preparation)

3. **Document current user count**
   ```sql
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM auth.users;
   ```

### Short-term (Phase 3)

4. **Migrate from mock users to real database**
   - Create `public.users` table OR use `auth.users`
   - Add `tenant_id` column
   - Migrate 3 mock users

5. **Integrate tenant-aware auth**
   - Fetch user's tenant on login
   - Include in JWT
   - Validate on protected endpoints

### Long-term (Post Phase 3)

6. **Implement token refresh mechanism**
7. **Add password reset flow**
8. **Consider Supabase Auth migration**

---

## 🎓 Testing

### Manual Testing

```bash
# 1. Login as admin
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. Extract token from response
TOKEN="<paste-token-here>"

# 3. Verify token
curl -X GET http://localhost:5000/auth/verify \
  -H "Authorization: Bearer $TOKEN"

# 4. Access protected endpoint
curl -X GET http://localhost:5000/api/protected \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Tests

Located in: `api-backend/tests/test_auth_endpoints.py`

```bash
cd api-backend
pytest tests/test_auth_endpoints.py -v
```

---

## 📝 Changelog

### v1.0 - October 18, 2025
- Initial documentation
- Documented current mock user system
- Identified P0/P1 issues
- Proposed migration paths
- Phase 3 requirements analysis

---

## 🙋 Questions & Answers

**Q: Do we use Supabase Auth?**  
A: No. Custom JWT-based auth with mock users.

**Q: Where are users stored?**  
A: In-memory mock data (not production-ready).

**Q: How many users in production?**  
A: Unknown, likely 0. Using 3 mock users (admin, operator, viewer).

**Q: Is `auth.users` table used?**  
A: No. Not integrated with Supabase Auth.

**Q: Does JWT include `tenant_id`?**  
A: No. Must be added for Phase 3.

**Q: What's the migration priority?**  
A: P0 - Move from mock users to real database before Phase 3.

---

**Next Steps**: Review this document in architecture meeting, then proceed with Phase 3 planning.
