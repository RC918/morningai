# 2FA Owner Migration and Rollback Plan

**Document Version**: 1.0  
**Date**: 2025-11-04  
**Priority**: P0 (Deployment Blocker)  
**Status**: 📋 Ready for Execution

---

## Executive Summary

This document outlines the migration plan for enforcing 2FA on all Owner accounts, including risk mitigation strategies, rollback procedures, and emergency response protocols. The migration will be executed in phases to minimize disruption and ensure business continuity.

**Key Dates**:
- **Phase 1 (Staging)**: November 5-8, 2025
- **Phase 2 (Production Soft Launch)**: November 11-15, 2025
- **Phase 3 (Enforcement)**: November 18, 2025
- **Phase 4 (Monitoring)**: November 18-25, 2025

---

## Pre-Migration Checklist

### ✅ Technical Prerequisites

- [x] **Database Schema Deployed**
  - Tables: `user_2fa`, `totp_backup_codes`, `trusted_devices`
  - Migration file: `handoff/20250928/40_App/api-backend/migrations/add_2fa_totp_tables.sql`
  - RLS policies enabled
  - Indexes created

- [x] **Code Deployed to Staging**
  - PR #1093 merged to staging branch
  - All CI checks passing (31/31)
  - Test coverage ≥74%

- [ ] **Feature Flags Configured**
  - `FEATURE_2FA_ENABLED=true` (staging)
  - `FEATURE_2FA_OWNER_ENFORCEMENT=false` (staging, will enable in Phase 2)
  - `FEATURE_2FA_PREAUTH=false` (not yet implemented)

- [ ] **Monitoring and Alerts**
  - Datadog/CloudWatch dashboards created
  - Error rate alerts configured (threshold: >1%)
  - Login success rate alerts configured (threshold: <99%)
  - 2FA setup rate tracking

- [ ] **Owner Account Inventory**
  - Run SQL queries from `03-owner-inventory-template.sql`
  - Identify all Owner accounts (expected: ~10-50)
  - Identify active vs inactive owners
  - Export to CSV for tracking

### ✅ Communication Prerequisites

- [ ] **Internal Communication**
  - Notify all Owner users via email (7 days before enforcement)
  - Create internal Slack announcement
  - Update internal wiki/docs

- [ ] **Support Team Training**
  - Train support team on 2FA setup process
  - Provide troubleshooting guide (see `05-support-runbook.md`)
  - Set up dedicated Slack channel (#2fa-support)

- [ ] **Emergency Contacts**
  - CTO: [Contact Info]
  - DevOps Lead: [Contact Info]
  - Support Lead: [Contact Info]
  - On-Call Engineer: [Contact Info]

---

## Migration Phases

### Phase 1: Staging Deployment and Testing (Nov 5-8, 2025)

**Objective**: Validate 2FA implementation in staging environment

**Tasks**:
1. ✅ Deploy PR #1093 to staging
2. ✅ Verify database schema deployed
3. [ ] Run smoke tests
   - Owner login without 2FA (should work)
   - Owner 2FA setup flow
   - Owner login with TOTP
   - Owner login with backup code
   - Remember device functionality
4. [ ] Load testing (100 concurrent logins)
5. [ ] Security testing (penetration test)
6. [ ] Performance testing (p95 latency < 500ms)

**Success Criteria**:
- ✅ All smoke tests pass
- ✅ No errors in logs
- ✅ Performance within acceptable limits
- ✅ Security audit passed

**Rollback**: Revert staging deployment if any critical issues found

---

### Phase 2: Production Soft Launch (Nov 11-15, 2025)

**Objective**: Deploy 2FA to production with voluntary adoption

**Configuration**:
```bash
FEATURE_2FA_ENABLED=true
FEATURE_2FA_OWNER_ENFORCEMENT=false  # Voluntary, not enforced
```

**Tasks**:
1. [ ] Deploy PR #1093 to production
2. [ ] Verify database schema deployed (run `03-owner-inventory-template.sql` Query 1)
3. [ ] Send email to all Owner users:
   ```
   Subject: Action Required: Enable Two-Factor Authentication (2FA)
   
   Dear [Owner Name],
   
   We're enhancing the security of your Owner account with Two-Factor 
   Authentication (2FA). Starting November 18, 2025, 2FA will be required 
   for all Owner accounts.
   
   Please enable 2FA now to avoid disruption:
   1. Log in to Owner Console
   2. Go to Settings → Security
   3. Click "Enable 2FA"
   4. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
   5. Save your backup codes in a secure location
   
   Need help? Contact support@morningai.com or see our guide: [Link]
   
   Thank you for helping us keep your account secure.
   
   - The Morning AI Team
   ```
4. [ ] Monitor adoption rate daily
   - Target: 80% adoption within 7 days
   - Send reminder emails on Day 3 and Day 5
5. [ ] Provide 1-on-1 support for owners who need help

**Success Criteria**:
- ✅ 80%+ of active owners enable 2FA voluntarily
- ✅ No critical bugs reported
- ✅ Support tickets < 10
- ✅ Login success rate > 99%

**Rollback**: If adoption < 50% or critical bugs found, delay enforcement

---

### Phase 3: Enforcement (Nov 18, 2025)

**Objective**: Enforce 2FA for all Owner accounts

**Configuration**:
```bash
FEATURE_2FA_ENABLED=true
FEATURE_2FA_OWNER_ENFORCEMENT=true  # Enforced
```

**Tasks**:
1. [ ] Enable enforcement flag at 9:00 AM UTC (low traffic time)
2. [ ] Monitor login attempts in real-time (first 2 hours)
3. [ ] Send final reminder email to owners without 2FA (before enforcement)
4. [ ] Have support team on standby for urgent requests

**Expected Behavior**:
- Owners without 2FA: Redirected to 2FA setup on login
- Owners with 2FA: Normal login flow (password → TOTP)
- Non-Owner users: No change (2FA optional)

**Success Criteria**:
- ✅ All active owners able to log in
- ✅ No lockouts (owners unable to access accounts)
- ✅ Error rate < 1%
- ✅ Support tickets < 5

**Rollback**: See "Emergency Rollback Procedure" below

---

### Phase 4: Monitoring and Optimization (Nov 18-25, 2025)

**Objective**: Monitor system stability and optimize UX

**Tasks**:
1. [ ] Monitor metrics daily:
   - Login success rate (target: >99%)
   - 2FA verification success rate (target: >95%)
   - Average login time (target: <3 seconds)
   - Error rate (target: <0.5%)
2. [ ] Collect user feedback
3. [ ] Identify UX improvements
4. [ ] Plan Pre-Auth Token implementation (Week 2)

**Success Criteria**:
- ✅ System stable for 7 days
- ✅ No critical bugs
- ✅ User satisfaction > 80%

---

## Database Schema Confirmation

### Migration File Location
**Path**: `handoff/20250928/40_App/api-backend/migrations/add_2fa_totp_tables.sql`

**GitHub Link**: https://github.com/RC918/morningai/blob/devin/week0-2fa-integration/handoff/20250928/40_App/api-backend/migrations/add_2fa_totp_tables.sql

### Tables Created

#### 1. `user_2fa`
```sql
CREATE TABLE IF NOT EXISTS user_2fa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT FALSE,
    secret_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE(user_id)
);
```

**Indexes**:
- `idx_user_2fa_user_id` on `user_id`
- `idx_user_2fa_enabled` on `enabled`

**RLS Policies**: Deny all access to `anon` and `authenticated` roles (service role only)

---

#### 2. `totp_backup_codes`
```sql
CREATE TABLE IF NOT EXISTS totp_backup_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes**:
- `idx_backup_codes_user_id` on `user_id`
- `idx_backup_codes_used` on `used`
- `idx_backup_codes_user_unused` on `(user_id, used) WHERE used = FALSE`

**RLS Policies**: Deny all access to `anon` and `authenticated` roles (service role only)

---

#### 3. `trusted_devices`
```sql
CREATE TABLE IF NOT EXISTS trusted_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_fingerprint TEXT NOT NULL,
    device_name TEXT,
    trusted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP,
    UNIQUE(user_id, device_fingerprint)
);
```

**Indexes**:
- `idx_trusted_devices_user_id` on `user_id`
- `idx_trusted_devices_expires` on `expires_at`
- `idx_trusted_devices_fingerprint` on `device_fingerprint`

**RLS Policies**: Deny all access to `anon` and `authenticated` roles (service role only)

---

### Verification Queries

**Check if tables exist**:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('user_2fa', 'totp_backup_codes', 'trusted_devices');
```

**Expected Output**:
```
 table_name        
-------------------
 user_2fa
 totp_backup_codes
 trusted_devices
(3 rows)
```

**Check table structure**:
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_2fa'
ORDER BY ordinal_position;
```

---

## Risk Assessment and Mitigation

### High-Risk Scenarios

#### Risk 1: Owner Lockout (Cannot Access Account)
**Likelihood**: Medium  
**Impact**: Critical  
**Mitigation**:
- Provide backup codes during 2FA setup (8 codes, single-use)
- Support team can disable 2FA for specific user (requires CTO approval)
- Emergency break-glass procedure (see below)

#### Risk 2: Lost Authenticator Device
**Likelihood**: Medium  
**Impact**: High  
**Mitigation**:
- Backup codes (8 codes, regenerate anytime)
- Support team can verify identity and disable 2FA
- Document recovery process in support runbook

#### Risk 3: Mass Lockout (System Bug)
**Likelihood**: Low  
**Impact**: Critical  
**Mitigation**:
- Feature flag `FEATURE_2FA_OWNER_ENFORCEMENT` for instant rollback
- Staging testing before production
- Gradual rollout with monitoring

#### Risk 4: Performance Degradation
**Likelihood**: Low  
**Impact**: Medium  
**Mitigation**:
- Load testing before production
- Redis caching for TOTP validation
- Rate limiting to prevent abuse

#### Risk 5: Security Vulnerability
**Likelihood**: Low  
**Impact**: Critical  
**Mitigation**:
- Security audit before production
- Penetration testing
- Bug bounty program
- Incident response plan

---

## Emergency Rollback Procedure

### Scenario 1: Critical Bug (System-Wide)

**Trigger**: Error rate > 5% OR Login success rate < 95%

**Procedure**:
1. **Immediate Action** (< 5 minutes):
   ```bash
   # Disable 2FA enforcement
   export FEATURE_2FA_OWNER_ENFORCEMENT=false
   
   # Restart API servers
   kubectl rollout restart deployment/api-backend
   ```

2. **Verify Rollback** (< 10 minutes):
   - Check error rate drops to < 1%
   - Check login success rate > 99%
   - Test Owner login without 2FA

3. **Communication** (< 15 minutes):
   - Post in #incidents Slack channel
   - Notify CTO and DevOps lead
   - Update status page

4. **Root Cause Analysis** (< 24 hours):
   - Review logs and metrics
   - Identify bug
   - Create hotfix PR
   - Test in staging
   - Re-deploy to production

**Rollback Impact**: Owners can log in without 2FA (temporary security downgrade)

---

### Scenario 2: Individual Owner Lockout

**Trigger**: Owner cannot log in due to lost device/backup codes

**Procedure**:
1. **Verify Identity** (< 30 minutes):
   - Support team verifies owner identity (email, phone, security questions)
   - Escalate to CTO if high-value account

2. **Disable 2FA** (< 5 minutes):
   ```sql
   -- Run in Supabase SQL Editor (requires service role)
   UPDATE user_2fa 
   SET enabled = FALSE 
   WHERE user_id = '<user_id>';
   
   -- Delete backup codes and trusted devices
   DELETE FROM totp_backup_codes WHERE user_id = '<user_id>';
   DELETE FROM trusted_devices WHERE user_id = '<user_id>';
   ```

3. **Notify Owner** (< 10 minutes):
   - Email owner: "Your 2FA has been temporarily disabled. Please re-enable it immediately after logging in."
   - Provide setup instructions

4. **Follow-Up** (< 24 hours):
   - Verify owner re-enabled 2FA
   - Document incident in support ticket

**Rollback Impact**: Single owner can log in without 2FA (temporary)

---

### Scenario 3: Mass Lockout (Multiple Owners)

**Trigger**: >3 owners locked out within 1 hour

**Procedure**:
1. **Immediate Action** (< 5 minutes):
   - Disable enforcement (same as Scenario 1)
   - Page on-call engineer

2. **Triage** (< 15 minutes):
   - Identify common pattern (bug, config issue, user error)
   - Determine if system-wide or user-specific

3. **Resolution**:
   - If system bug: Follow Scenario 1
   - If user error: Provide support to each owner individually

4. **Post-Mortem** (< 48 hours):
   - Document incident
   - Identify improvements
   - Update runbook

---

## Break-Glass Procedure

**Purpose**: Emergency access for CTO/DevOps in case of catastrophic failure

**Trigger**: All normal procedures failed, business-critical access needed

**Procedure**:
1. **Authorization** (< 5 minutes):
   - CTO approval required
   - Document reason in incident log

2. **Database Override** (< 10 minutes):
   ```sql
   -- Disable 2FA for all owners (EMERGENCY ONLY)
   UPDATE user_2fa 
   SET enabled = FALSE 
   WHERE user_id IN (
       SELECT id FROM auth.users 
       WHERE raw_user_meta_data->>'role' = 'owner'
   );
   ```

3. **Feature Flag Override** (< 5 minutes):
   ```bash
   # Disable 2FA feature entirely
   export FEATURE_2FA_ENABLED=false
   kubectl rollout restart deployment/api-backend
   ```

4. **Communication** (< 15 minutes):
   - Notify all stakeholders
   - Post in #incidents
   - Update status page: "2FA temporarily disabled for maintenance"

5. **Recovery** (< 24 hours):
   - Fix root cause
   - Test thoroughly in staging
   - Re-enable 2FA with phased rollout

**Impact**: All owners can log in without 2FA (major security downgrade)

**Post-Incident**: Mandatory security audit and post-mortem

---

## Monitoring and Metrics

### Key Metrics

**Login Metrics**:
- `login_attempts_total` (counter)
- `login_success_total` (counter)
- `login_failure_total` (counter)
- `login_duration_seconds` (histogram)

**2FA Metrics**:
- `2fa_setup_total` (counter)
- `2fa_verification_attempts_total` (counter)
- `2fa_verification_success_total` (counter)
- `2fa_verification_failure_total` (counter)
- `2fa_backup_code_used_total` (counter)

**Error Metrics**:
- `2fa_errors_total` (counter, by error_type)
- `2fa_lockouts_total` (counter)

### Dashboards

**Datadog Dashboard**: "2FA Owner Migration"
- Login success rate (target: >99%)
- 2FA adoption rate (target: 100%)
- Error rate (target: <1%)
- Average login time (target: <3s)
- Active owners without 2FA (target: 0)

### Alerts

**Critical Alerts** (Page on-call):
- Login success rate < 95% for 5 minutes
- Error rate > 5% for 5 minutes
- >3 lockouts within 1 hour

**Warning Alerts** (Slack notification):
- Login success rate < 99% for 10 minutes
- Error rate > 1% for 10 minutes
- 2FA adoption rate < 80% (Day 5 of soft launch)

---

## Success Criteria

### Phase 1 (Staging)
- ✅ All smoke tests pass
- ✅ No errors in logs
- ✅ Performance within limits

### Phase 2 (Soft Launch)
- ✅ 80%+ adoption rate
- ✅ <10 support tickets
- ✅ Login success rate >99%

### Phase 3 (Enforcement)
- ✅ 100% of active owners have 2FA
- ✅ 0 lockouts
- ✅ Error rate <1%

### Phase 4 (Monitoring)
- ✅ System stable for 7 days
- ✅ User satisfaction >80%
- ✅ No critical bugs

---

## Post-Migration Tasks

**Week 2** (Nov 18-25, 2025):
- [ ] Monitor metrics daily
- [ ] Collect user feedback
- [ ] Identify UX improvements
- [ ] Plan Pre-Auth Token implementation

**Week 3** (Nov 25-Dec 2, 2025):
- [ ] Implement Pre-Auth Token (PR #2)
- [ ] Deploy to staging
- [ ] Test and validate

**Week 4** (Dec 2-9, 2025):
- [ ] Deploy Pre-Auth Token to production
- [ ] Monitor adoption
- [ ] Deprecate password re-transmission

**Month 2** (Dec 2025):
- [ ] Add automated tests for edge cases
- [ ] Implement rate limiting improvements
- [ ] Add audit logging
- [ ] Security audit

---

## Appendix: Contact Information

**Emergency Contacts**:
- **CTO**: [Name, Email, Phone]
- **DevOps Lead**: [Name, Email, Phone]
- **Support Lead**: [Name, Email, Phone]
- **On-Call Engineer**: [Pagerduty Link]

**Slack Channels**:
- `#incidents` - Critical incidents
- `#2fa-support` - User support
- `#engineering` - General engineering

**Documentation**:
- Support Runbook: `05-support-runbook.md`
- Pre-Auth Token Design: `02-pre-auth-token-design.md`
- Security Logging Review: `01-security-logging-review.md`

---

**Document Owner**: Devin AI  
**Approval Required**: CTO  
**Last Updated**: 2025-11-04  
**Next Review**: After Phase 1 Completion
