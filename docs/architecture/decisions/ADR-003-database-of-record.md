# ADR-003: Database-of-Record Decision

**Status**: Proposed  
**Date**: 2025-10-28  
**Decision Maker**: CTO  
**Stakeholders**: Engineering Team, DevOps, Product, CEO

---

## Context

The MorningAI backend currently has ambiguous database configuration with SQLite hardcoded but PostgreSQL dependencies present:

### Current State:

**Code Configuration** (`handoff/20250928/40_App/api-backend/src/main.py:236`):
```python
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{...}/database/app.db"
```

**Render Configuration** (`render.yaml:18-19`):
```yaml
envVars:
  - key: DATABASE_URL
    value: sqlite:///database/app.db
```

**Dependencies Present** (`handoff/20250928/40_App/api-backend/requirements.txt`):
- `psycopg2-binary` - PostgreSQL adapter
- `supabase==2.6.0` - Supabase client (PostgreSQL-based)
- `SQLAlchemy==2.0.41` - ORM (supports both SQLite and PostgreSQL)

**Environment Variables** (`.env.example`):
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Public API key
- `SUPABASE_SERVICE_ROLE_KEY` - Admin API key (critical)
- `DATABASE_URL` - Database connection string

**Problem**:
1. **Production Risk**: SQLite is not suitable for production SaaS
   - No concurrent write support
   - No replication/backup
   - Single file = single point of failure
   - No Row Level Security (RLS) for multi-tenancy

2. **Configuration Confusion**: Code ignores `DATABASE_URL` environment variable
   - Hardcoded SQLite path in main.py
   - PostgreSQL dependencies installed but unused
   - Unclear if Supabase is intended for production

3. **Multi-tenant Security**: No RLS implementation visible
   - Critical gap for SaaS platform (identified in CTO assessment as P0 risk)
   - Tenant data isolation not enforced at database level

4. **Scalability**: SQLite limits growth
   - No horizontal scaling
   - Limited to single server
   - Performance degrades with data growth

---

## Decision

**We adopt Supabase PostgreSQL as the production database-of-record.**

**SQLite remains available as a fallback for local development only.**

---

## Rationale

### Why PostgreSQL (Supabase):

1. **Production-Ready**:
   - ✅ ACID compliance with concurrent writes
   - ✅ Automatic backups and point-in-time recovery
   - ✅ High availability with replication
   - ✅ Proven at scale (powers thousands of SaaS apps)

2. **Multi-tenant Security**:
   - ✅ Row Level Security (RLS) built-in
   - ✅ Fine-grained access control
   - ✅ Tenant isolation at database level
   - ✅ Audit logging capabilities

3. **Already Integrated**:
   - ✅ Supabase client already in dependencies
   - ✅ Environment variables already defined
   - ✅ `SUPABASE_SERVICE_ROLE_KEY` present in secrets
   - ✅ Orchestrator uses Supabase for pgvector (memory/embeddings)

4. **Feature-Rich**:
   - ✅ pgvector extension for AI embeddings (already used by orchestrator)
   - ✅ Real-time subscriptions (future feature potential)
   - ✅ PostgREST API (alternative to Flask if needed)
   - ✅ Built-in authentication (can complement JWT)

5. **Cost-Effective**:
   - ✅ Free tier: 500MB database, 2GB bandwidth
   - ✅ Pro tier: $25/month for 8GB database
   - ✅ No infrastructure management overhead

6. **Developer Experience**:
   - ✅ Web-based SQL editor
   - ✅ Table editor UI
   - ✅ Migration management
   - ✅ Comprehensive documentation

### Why NOT SQLite in Production:

**SQLite Limitations**:
- ❌ No concurrent write support (locks entire database)
- ❌ No replication or high availability
- ❌ No Row Level Security
- ❌ Limited to single server (no horizontal scaling)
- ❌ File-based (vulnerable to corruption, hard to backup)
- ❌ Not suitable for multi-tenant SaaS

**Industry Standard**:
- All major SaaS platforms use PostgreSQL or similar
- SQLite is for embedded/local use cases only

### Why Keep SQLite for Development:

1. **Zero Configuration**: Works out of the box for local dev
2. **Fast Iteration**: No network latency
3. **Offline Development**: No internet required
4. **CI/CD**: Fast test execution without external dependencies

---

## Implementation Plan

### Phase 1: Code Changes (Week 1)

**1.1 Update main.py to Honor DATABASE_URL** (2 hours):

```python
# handoff/20250928/40_App/api-backend/src/main.py:236
import os

# Honor DATABASE_URL if present, fallback to SQLite for local dev
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and not DATABASE_URL.startswith('sqlite'):
    # Production: Use provided DATABASE_URL (PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Verify connections before using
    }
    print(f"✅ Using PostgreSQL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
else:
    # Development: Fallback to SQLite
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    print(f"⚠️  Using SQLite for development: {db_path}")
```

**1.2 Update render.yaml** (1 hour):

```yaml
# render.yaml:18-19
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: morningai-postgres
      property: connectionString
```

**1.3 Add Database Migration Framework** (4 hours):

Install Alembic:
```bash
# handoff/20250928/40_App/api-backend/requirements.txt
alembic==1.13.0
```

Initialize Alembic:
```bash
cd handoff/20250928/40_App/api-backend
alembic init alembic
```

Configure `alembic.ini`:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
# Will be overridden by env.py to use DATABASE_URL
```

Update `alembic/env.py`:
```python
import os
from sqlalchemy import engine_from_config, pool

config.set_main_option('sqlalchemy.url', os.environ.get('DATABASE_URL', 'sqlite:///database/app.db'))
```

### Phase 2: Database Setup (Week 1)

**2.1 Create Supabase Database** (1 hour):
- Use existing Supabase project (SUPABASE_URL already configured)
- Or create new project if needed
- Note connection string

**2.2 Create Initial Migration** (2 hours):
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**2.3 Implement RLS Policies** (8 hours):

Example RLS policy for multi-tenancy:
```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own tenant's data
CREATE POLICY tenant_isolation ON users
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation ON dashboards
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation ON reports
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Service role can bypass RLS (for admin operations)
CREATE POLICY service_role_bypass ON users
  TO service_role
  USING (true);
```

**2.4 Update Application Code** (4 hours):

Set tenant context in Flask middleware:
```python
@app.before_request
def set_tenant_context():
    if request.endpoint and 'static' not in request.endpoint:
        tenant_id = get_tenant_from_jwt(request.headers.get('Authorization'))
        if tenant_id:
            db.session.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
```

### Phase 3: Testing & Validation (Week 2)

**3.1 Unit Tests** (4 hours):
- Test DATABASE_URL parsing
- Test SQLite fallback
- Test connection pooling
- Test RLS policies

**3.2 Integration Tests** (4 hours):
- Test multi-tenant data isolation
- Test concurrent writes
- Test connection recovery
- Test migration rollback

**3.3 Load Testing** (4 hours):
- Simulate 100 concurrent users
- Verify no database locks
- Measure query performance
- Identify slow queries

**3.4 Security Audit** (4 hours):
- Verify RLS policies work
- Test tenant isolation
- Check for SQL injection vulnerabilities
- Validate service role key usage

### Phase 4: Deployment (Week 2)

**4.1 Staging Deployment** (2 hours):
- Deploy to staging environment
- Run smoke tests
- Verify health checks pass

**4.2 Data Migration** (4 hours):
- Export existing SQLite data (if any)
- Import to PostgreSQL
- Verify data integrity
- Test application functionality

**4.3 Production Deployment** (2 hours):
- Update Render environment variables
- Deploy new backend version
- Monitor error rates
- Verify health checks

**4.4 Rollback Plan** (1 hour):
- Document rollback procedure
- Keep SQLite backup
- Test rollback in staging

---

## Consequences

### Positive:

1. **Production-Ready**: Suitable for SaaS at scale
2. **Security**: RLS enables proper multi-tenant isolation
3. **Reliability**: Automatic backups and high availability
4. **Scalability**: Can handle growth without architectural changes
5. **Feature-Rich**: pgvector, real-time, PostgREST available
6. **Developer Experience**: Better tooling and debugging

### Negative:

1. **Migration Effort**: ~40 hours of engineering work
   - Mitigation: Phased approach over 2 weeks
   
2. **Operational Complexity**: Need to manage PostgreSQL
   - Mitigation: Supabase handles infrastructure
   
3. **Cost**: $25/month for Pro tier (vs free SQLite)
   - Mitigation: Essential for production SaaS, cost is minimal
   
4. **Local Development**: Requires network connection
   - Mitigation: SQLite fallback for offline development

### Risks & Mitigations:

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Low | Critical | Full backup before migration, test in staging |
| RLS misconfiguration | Medium | Critical | Comprehensive testing, security audit |
| Performance degradation | Low | High | Load testing, query optimization |
| Connection pool exhaustion | Medium | High | Proper pool configuration, monitoring |
| Increased latency | Low | Medium | Connection pooling, query optimization |

---

## Compliance

This decision aligns with:
- **CTO Responsibility 1**: Technical Strategy (production-ready architecture)
- **CTO Responsibility 4**: Security & Infrastructure Governance (RLS, backups, HA)
- **Risk Mitigation**: Addresses ARCH-003 in Risk Register (HIGH priority)
- **Risk Mitigation**: Addresses SEC-002 (RLS implementation, P0 security risk)
- **Phase 10 Goals**: Compliance readiness (audit logging, data retention)

---

## Success Criteria

**Week 1**:
- [ ] Code changes deployed to staging
- [ ] Initial migration created and tested
- [ ] RLS policies implemented
- [ ] Unit tests passing

**Week 2**:
- [ ] Integration tests passing
- [ ] Load testing completed
- [ ] Security audit completed
- [ ] Production deployment successful

**Week 4**:
- [ ] No database-related incidents
- [ ] Query performance meets SLA (<200ms p95)
- [ ] RLS verified working in production
- [ ] Team trained on new database workflow

---

## References

- `handoff/20250928/40_App/api-backend/src/main.py:236` - Current SQLite configuration
- `render.yaml:18-19` - Current DATABASE_URL configuration
- `handoff/20250928/40_App/api-backend/requirements.txt` - PostgreSQL dependencies
- `.env.example` - Supabase environment variables
- CTO Technical Assessment Report (2025-10-28) - Database ambiguity and RLS gap
- Supabase Documentation: https://supabase.com/docs/guides/database
- PostgreSQL RLS Documentation: https://www.postgresql.org/docs/current/ddl-rowsecurity.html

---

## Alternative Considered

**Option B: Continue with SQLite**
- Rejected because:
  - Not production-ready for SaaS
  - No RLS for multi-tenant security
  - No high availability
  - Blocks scaling and Phase 9 commercialization
  - Industry anti-pattern for web applications

**Option C: Self-hosted PostgreSQL**
- Rejected because:
  - Requires DevOps overhead
  - Need to manage backups, monitoring, scaling
  - Supabase provides same features with less complexity
  - Higher operational cost

---

## Approval

- [ ] CTO Review
- [ ] Engineering Lead Review
- [ ] DevOps Review
- [ ] Security Review
- [ ] CEO Approval (budget impact: +$25/month)
- [ ] Documented in team wiki

**Target Approval Date**: 2025-10-30  
**Implementation Start**: Upon approval  
**Target Completion**: 2025-11-14 (2 weeks)  
**Review Date**: 2025-12-14 (reassess performance and costs)

---

## Future Considerations

### Potential Enhancements (3-6 months):

1. **Read Replicas**: For analytics queries
2. **Connection Pooling Service**: PgBouncer for better connection management
3. **Database Monitoring**: Datadog or New Relic for query performance
4. **Automated Backups**: Daily backups with 30-day retention
5. **Multi-region**: For global latency optimization

### Migration to Other Databases (12+ months):

If Supabase becomes limiting:
- **Option A**: AWS RDS PostgreSQL (more control, higher cost)
- **Option B**: Google Cloud SQL (similar to Supabase)
- **Option C**: Self-hosted PostgreSQL (maximum control)

All options use PostgreSQL, so migration would be straightforward (dump/restore).
