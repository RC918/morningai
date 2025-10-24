# Security & RLS Implementation Guide

**Priority: P0 - Critical**  
**Timeline:** Week 1-2 (Immediate)  
**Goal:** Enterprise-grade security with complete multi-tenant data isolation

---

## 🚨 Critical Security Gap: Row Level Security (RLS)

### Current State Assessment

**Severity: CRITICAL**

The MorningAI platform currently has **minimal RLS implementation**, which poses a **P0 security risk** for a multi-tenant SaaS platform. This must be addressed immediately before any production scale-up.

**Findings:**
- ❌ Only 1 reference to RLS in codebase (`orchestrator/persistence/db_client.py`)
- ❌ No RLS policies visible in repository
- ❌ Supabase multi-tenant data isolation not enforced at database level
- ❌ SERVICE_ROLE_KEY used for "RLS bypass" (dangerous in production)
- ⚠️ Potential for cross-tenant data access

**Risk Impact:**
- **Data Breach:** Tenant A could access Tenant B's data
- **Compliance Violation:** GDPR, SOC2 requirements not met
- **Reputation Damage:** Security incident would destroy trust
- **Legal Liability:** Potential lawsuits from affected tenants

---

## 🎯 RLS Implementation Strategy

### Phase 1: Immediate Actions (Days 1-3)

#### Step 1.1: Audit Current Database Schema

```bash
# Connect to Supabase and audit all tables
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
"
```

**Expected Tables Requiring RLS:**
- `tenants` - Tenant master data
- `users` - User accounts
- `agents` - Agent instances
- `agent_reputation` - Reputation scores
- `agent_reputation_events` - Reputation history
- `governance_violations` - Compliance violations
- `strategies` - Business strategies
- `decisions` - Decision history
- `costs` - Cost tracking
- `sessions` - Agent sessions
- `knowledge_graph` - Semantic knowledge
- `learned_patterns` - ML patterns

#### Step 1.2: Enable RLS on All Tables

```sql
-- Enable RLS on all tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_reputation ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_reputation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE governance_violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE costs ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_graph ENABLE ROW LEVEL SECURITY;
ALTER TABLE learned_patterns ENABLE ROW LEVEL SECURITY;
```

#### Step 1.3: Create RLS Policies

**Policy 1: Owner Full Access**
```sql
-- Owner can access ALL tenant data (for platform management)
CREATE POLICY "owner_all_access" ON tenants
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'Owner'
    )
  );

-- Repeat for all tables
CREATE POLICY "owner_all_access" ON users FOR ALL
  USING (EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.role = 'Owner'));

CREATE POLICY "owner_all_access" ON agents FOR ALL
  USING (EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.role = 'Owner'));

-- ... (repeat for all tables)
```

**Policy 2: Tenant Isolation**
```sql
-- Tenants can only access their own data
CREATE POLICY "tenant_own_data" ON agents
  FOR ALL
  USING (
    tenant_id = (
      SELECT tenant_id FROM users
      WHERE users.id = auth.uid()
    )
  );

-- Repeat for all tenant-scoped tables
CREATE POLICY "tenant_own_data" ON agent_reputation FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON agent_reputation_events FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON governance_violations FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON strategies FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON decisions FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON costs FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON sessions FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON knowledge_graph FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));

CREATE POLICY "tenant_own_data" ON learned_patterns FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM users WHERE users.id = auth.uid()));
```

**Policy 3: Admin Role (Tenant-Scoped)**
```sql
-- Admins can manage users within their tenant
CREATE POLICY "admin_manage_tenant_users" ON users
  FOR ALL
  USING (
    tenant_id = (
      SELECT tenant_id FROM users
      WHERE users.id = auth.uid()
      AND users.role IN ('Owner', 'Admin')
    )
  );
```

**Policy 4: Read-Only for Regular Users**
```sql
-- Regular users can read but not modify
CREATE POLICY "user_read_own_tenant" ON agents
  FOR SELECT
  USING (
    tenant_id = (
      SELECT tenant_id FROM users
      WHERE users.id = auth.uid()
    )
  );

-- Repeat for other tables where read-only access is appropriate
```

---

### Phase 2: Testing & Validation (Days 4-5)

#### Test 1: Cross-Tenant Access Prevention

```python
# tests/security/test_rls_isolation.py
import pytest
from supabase import create_client

def test_tenant_isolation():
    """Test that Tenant A cannot access Tenant B's data"""
    
    # Setup: Create two tenants
    tenant_a_client = create_client(SUPABASE_URL, tenant_a_jwt)
    tenant_b_client = create_client(SUPABASE_URL, tenant_b_jwt)
    
    # Tenant A creates an agent
    agent_a = tenant_a_client.table('agents').insert({
        'tenant_id': 'tenant-a',
        'name': 'Agent A',
        'type': 'dev'
    }).execute()
    
    # Tenant B tries to access Tenant A's agent
    result = tenant_b_client.table('agents').select('*').eq(
        'id', agent_a.data[0]['id']
    ).execute()
    
    # Assert: Tenant B should NOT see Tenant A's agent
    assert len(result.data) == 0, "RLS VIOLATION: Cross-tenant access detected!"

def test_owner_can_access_all_tenants():
    """Test that Owner can access all tenant data"""
    
    owner_client = create_client(SUPABASE_URL, owner_jwt)
    
    # Owner queries all agents across all tenants
    result = owner_client.table('agents').select('*').execute()
    
    # Assert: Owner should see agents from multiple tenants
    tenant_ids = set(agent['tenant_id'] for agent in result.data)
    assert len(tenant_ids) > 1, "Owner should access multiple tenants"

def test_admin_cannot_access_other_tenants():
    """Test that Admin can only manage their own tenant"""
    
    admin_a_client = create_client(SUPABASE_URL, admin_a_jwt)
    
    # Admin A tries to access Tenant B's data
    result = admin_a_client.table('agents').select('*').eq(
        'tenant_id', 'tenant-b'
    ).execute()
    
    # Assert: Admin A should NOT see Tenant B's data
    assert len(result.data) == 0, "RLS VIOLATION: Admin cross-tenant access!"

def test_user_read_only_access():
    """Test that regular users have read-only access"""
    
    user_client = create_client(SUPABASE_URL, user_jwt)
    
    # User tries to delete an agent
    with pytest.raises(Exception) as exc_info:
        user_client.table('agents').delete().eq('id', agent_id).execute()
    
    # Assert: Should fail with permission error
    assert "permission denied" in str(exc_info.value).lower()
```

#### Test 2: Service Role Key Usage Audit

```python
# tests/security/test_service_role_usage.py
def test_service_role_key_not_exposed():
    """Ensure SERVICE_ROLE_KEY is never exposed to clients"""
    
    # Check all API endpoints
    endpoints = [
        '/api/agents',
        '/api/governance/agents',
        '/api/dashboard/stats',
        # ... all endpoints
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        
        # Assert: Response should not contain SERVICE_ROLE_KEY
        assert "SERVICE_ROLE_KEY" not in response.text
        assert os.getenv("SUPABASE_SERVICE_ROLE_KEY") not in response.text

def test_rls_bypass_only_in_admin_operations():
    """Ensure RLS bypass is only used for legitimate admin operations"""
    
    # Audit all uses of SERVICE_ROLE_KEY in codebase
    import subprocess
    result = subprocess.run(
        ['grep', '-r', 'SERVICE_ROLE_KEY', 'handoff/'],
        capture_output=True,
        text=True
    )
    
    # Parse results and verify each usage
    usages = result.stdout.split('\n')
    
    for usage in usages:
        if 'SERVICE_ROLE_KEY' in usage:
            # Assert: Only in admin/system operations
            assert any(keyword in usage for keyword in [
                'admin', 'system', 'migration', 'seed'
            ]), f"Suspicious SERVICE_ROLE_KEY usage: {usage}"
```

---

### Phase 3: Migration & Deployment (Days 6-7)

#### Migration Script

```sql
-- migrations/001_enable_rls.sql
BEGIN;

-- Step 1: Enable RLS on all tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT IN ('schema_migrations')
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
END $$;

-- Step 2: Create Owner policies
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT IN ('schema_migrations')
    LOOP
        EXECUTE format('
            CREATE POLICY "owner_all_access" ON %I
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1 FROM users
                    WHERE users.id = auth.uid()
                    AND users.role = ''Owner''
                )
            )
        ', t);
    END LOOP;
END $$;

-- Step 3: Create Tenant isolation policies
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT IN ('schema_migrations', 'tenants')
        AND EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = t
            AND column_name = 'tenant_id'
        )
    LOOP
        EXECUTE format('
            CREATE POLICY "tenant_own_data" ON %I
            FOR ALL
            USING (
                tenant_id = (
                    SELECT tenant_id FROM users
                    WHERE users.id = auth.uid()
                )
            )
        ', t);
    END LOOP;
END $$;

-- Step 4: Verify RLS is enabled
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND rowsecurity = false;

-- Should return 0 rows

COMMIT;
```

#### Deployment Checklist

- [ ] **Backup Database:** Full backup before migration
- [ ] **Test in Staging:** Run migration on staging environment
- [ ] **Validate RLS Tests:** All tests pass in staging
- [ ] **Monitor Performance:** Check query performance impact
- [ ] **Deploy to Production:** Run migration during low-traffic window
- [ ] **Verify in Production:** Run smoke tests
- [ ] **Monitor Errors:** Watch for RLS-related errors
- [ ] **Rollback Plan:** Prepared if issues arise

---

## 🔒 Additional Security Enhancements

### 1. Secrets Management

**Current State:**
- 53 environment variables
- No secrets rotation policy
- No secret scanning in CI

**Implementation:**

```yaml
# .github/workflows/secret-scanning.yml
name: Secret Scanning

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: TruffleHog Secret Scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --debug --only-verified
      
      - name: Fail on Secrets Found
        if: steps.scan.outputs.secrets_found == 'true'
        run: |
          echo "::error::Secrets detected in commit history!"
          exit 1
```

**Secrets Rotation Policy:**
```markdown
# Secrets Rotation Schedule

## Critical Secrets (Rotate every 30 days)
- JWT_SECRET_KEY
- MASTER_ENCRYPTION_KEY
- SUPABASE_SERVICE_ROLE_KEY

## High-Priority Secrets (Rotate every 90 days)
- OPENAI_API_KEY
- GITHUB_TOKEN
- TELEGRAM_BOT_TOKEN

## Standard Secrets (Rotate every 180 days)
- SENTRY_AUTH_TOKEN
- CLOUDFLARE_API_TOKEN
- VERCEL_TOKEN

## Rotation Process
1. Generate new secret
2. Update in secret store (GitHub Secrets, Render, Vercel)
3. Deploy with new secret
4. Verify functionality
5. Revoke old secret
6. Document rotation in audit log
```

---

### 2. API Rate Limiting

**Implementation:**

```python
# middleware/rate_limiter.py
from redis import Redis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    def check_rate_limit(
        self,
        tenant_id: str,
        endpoint: str,
        limit: int = 100,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit
        
        Args:
            tenant_id: Tenant identifier
            endpoint: API endpoint
            limit: Max requests per window
            window: Time window in seconds
        
        Returns:
            (allowed, remaining): Whether request is allowed and remaining quota
        """
        key = f"rate_limit:{tenant_id}:{endpoint}"
        
        # Get current count
        current = self.redis.get(key)
        
        if current is None:
            # First request in window
            self.redis.setex(key, window, 1)
            return True, limit - 1
        
        current = int(current)
        
        if current >= limit:
            # Rate limit exceeded
            return False, 0
        
        # Increment counter
        self.redis.incr(key)
        return True, limit - current - 1

# Apply to all API endpoints
@app.before_request
def check_rate_limit():
    tenant_id = get_tenant_id_from_jwt()
    endpoint = request.endpoint
    
    rate_limiter = RateLimiter(redis_client)
    allowed, remaining = rate_limiter.check_rate_limit(
        tenant_id,
        endpoint,
        limit=100,  # 100 requests per minute
        window=60
    )
    
    if not allowed:
        return jsonify({
            "error": "Rate limit exceeded",
            "retry_after": 60
        }), 429
    
    # Add rate limit headers
    response.headers['X-RateLimit-Limit'] = '100'
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(int(time.time()) + 60)
```

---

### 3. Audit Logging

**Implementation:**

```python
# middleware/audit_logger.py
import logging
from datetime import datetime
from typing import Optional

class AuditLogger:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.logger = logging.getLogger('audit')
    
    def log_event(
        self,
        event_type: str,
        user_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        result: str,
        metadata: Optional[dict] = None
    ):
        """
        Log security-relevant event to audit trail
        
        Args:
            event_type: Type of event (auth, data_access, config_change, etc.)
            user_id: User who performed action
            tenant_id: Tenant context
            resource_type: Type of resource (agent, user, strategy, etc.)
            resource_id: Specific resource ID
            action: Action performed (create, read, update, delete)
            result: Result (success, failure, denied)
            metadata: Additional context
        """
        audit_entry = {
            'event_type': event_type,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'result': result,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        
        # Store in database
        self.supabase.table('audit_log').insert(audit_entry).execute()
        
        # Also log to structured logger
        self.logger.info('Audit event', extra=audit_entry)

# Apply to all sensitive operations
@app.after_request
def log_audit_trail(response):
    if request.method in ['POST', 'PUT', 'DELETE']:
        audit_logger.log_event(
            event_type='api_request',
            user_id=get_user_id_from_jwt(),
            tenant_id=get_tenant_id_from_jwt(),
            resource_type=request.endpoint,
            resource_id=request.view_args.get('id', 'N/A'),
            action=request.method,
            result='success' if response.status_code < 400 else 'failure',
            metadata={
                'status_code': response.status_code,
                'request_body': request.get_json() if request.is_json else None
            }
        )
    
    return response
```

---

## 📊 Security Metrics & Monitoring

### Key Metrics to Track

1. **RLS Effectiveness**
   - Cross-tenant access attempts (should be 0)
   - RLS policy violations (should be 0)
   - Query performance impact (<10% overhead)

2. **Authentication**
   - Failed login attempts
   - JWT token validation failures
   - Session hijacking attempts

3. **Rate Limiting**
   - Rate limit hits per tenant
   - Abuse patterns detected
   - API usage by endpoint

4. **Audit Trail**
   - Sensitive operations logged (100%)
   - Audit log retention (90 days)
   - Compliance report generation

### Monitoring Dashboard

```python
# monitoring/security_dashboard.py
def get_security_metrics():
    return {
        "rls": {
            "cross_tenant_attempts": count_cross_tenant_attempts(),
            "policy_violations": count_policy_violations(),
            "query_overhead": measure_rls_overhead()
        },
        "auth": {
            "failed_logins": count_failed_logins(),
            "jwt_failures": count_jwt_failures(),
            "active_sessions": count_active_sessions()
        },
        "rate_limiting": {
            "rate_limit_hits": count_rate_limit_hits(),
            "top_abusers": get_top_abusers(),
            "api_usage": get_api_usage_by_endpoint()
        },
        "audit": {
            "events_logged": count_audit_events(),
            "retention_status": check_retention_status(),
            "compliance_score": calculate_compliance_score()
        }
    }
```

---

## 🚀 Deployment Plan

### Week 1: RLS Implementation
- **Day 1-2:** Audit schema, create policies
- **Day 3-4:** Write and run tests
- **Day 5:** Deploy to staging
- **Day 6:** Validate in staging
- **Day 7:** Deploy to production

### Week 2: Additional Security
- **Day 8-9:** Secret scanning and rotation
- **Day 10-11:** Rate limiting implementation
- **Day 12-13:** Audit logging system
- **Day 14:** Security dashboard and monitoring

---

## ✅ Success Criteria

- [ ] RLS enabled on all tables
- [ ] 100% test coverage for RLS policies
- [ ] Zero cross-tenant access in tests
- [ ] Secret scanning in CI
- [ ] Rate limiting on all endpoints
- [ ] Audit logging for all sensitive operations
- [ ] Security dashboard operational
- [ ] Documentation complete

---

*Document Version: 1.0*  
*Last Updated: 2025-10-24*  
*Priority: P0 - Critical*  
*Owner: CTO*
