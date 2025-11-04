# RLS Security Assessment - Anon Key Public Access Review

**Date**: 2025-10-23  
**Reviewer**: Devin AI  
**Context**: PR #626 - RLS Policy Testing for PR #618

## Executive Summary

**Current Status**: ⚠️ **MODERATE RISK** - Anon key provides public read access to 9 tables containing operational and business intelligence data.

**Recommendation**: 🔴 **RESTRICT ACCESS** - Most tables should NOT be publicly accessible via anon key.

## Tables with Public Read Access (via anon key)

### 🔴 HIGH RISK - Should NOT be public

#### 1. `trace_metrics` - Performance & Cost Monitoring
**Sensitivity**: HIGH
- Contains: API traces, LLM usage, costs, errors, user agents
- Fields expose:
  - `llm_cost`: Business cost data
  - `llm_tokens`: Usage patterns
  - `error`: Internal error messages (potential security info)
  - `url`, `method`: API endpoint structure
  - `user_agent`: User tracking data

**Risk**: 
- Competitors can analyze your LLM costs and usage patterns
- Error messages may leak internal implementation details
- API structure exposure aids in attack planning

**Recommendation**: ❌ **REMOVE public access** - Only service_role should access

---

#### 2. `alerts` - System Monitoring Alerts
**Sensitivity**: HIGH
- Contains: System alerts, error conditions, operational issues
- Fields expose:
  - `message`: Internal error/alert details
  - `severity`: System health indicators
  - `value`: Alert metadata (may contain sensitive data)
  - `acknowledged_by`: Internal user identifiers

**Risk**:
- Attackers can monitor system health and identify vulnerabilities
- Alert patterns reveal infrastructure weaknesses
- Timing of alerts can indicate attack success

**Recommendation**: ❌ **REMOVE public access** - Only service_role should access

---

#### 3. `agent_reputation` - AI Agent Governance
**Sensitivity**: MEDIUM-HIGH
- Contains: Agent performance metrics, permission levels, reputation scores
- Fields expose:
  - `permission_level`: Security access levels
  - `reputation_score`: Agent trust metrics
  - `test_pass_rate`: Quality metrics
  - `violation_count`: Security incident counts

**Risk**:
- Reveals internal AI agent architecture and capabilities
- Exposes security model (permission levels)
- Competitive intelligence on AI system maturity

**Recommendation**: ❌ **REMOVE public access** - Dashboard only (authenticated users)

---

#### 4. `reputation_events` - Agent Audit Log
**Sensitivity**: MEDIUM-HIGH
- Contains: Detailed audit trail of agent actions and reputation changes
- Fields expose:
  - `event_type`: Agent behavior patterns
  - `delta`: Reputation change amounts
  - `reason`: Detailed event explanations
  - `trace_id`: Links to trace_metrics

**Risk**:
- Complete audit trail of AI agent behavior
- Can be used to reverse-engineer governance rules
- Reveals system reliability and incident frequency

**Recommendation**: ❌ **REMOVE public access** - Dashboard only (authenticated users)

---

#### 5. `faq_search_history` - User Search Behavior
**Sensitivity**: MEDIUM
- Contains: User search queries, session tracking, user IDs
- Fields expose:
  - `query`: User search terms (may contain PII or sensitive questions)
  - `user_id`: User identifiers
  - `session_id`: Session tracking
  - `user_feedback`: User behavior data

**Risk**:
- Privacy violation - user search behavior is personal data
- May violate GDPR/privacy regulations
- Competitive intelligence on user needs and pain points

**Recommendation**: ❌ **REMOVE public access** - Dashboard only (authenticated users)

---

### 🟡 MEDIUM RISK - Consider restricting

#### 6. `embeddings` - Vector Embeddings
**Sensitivity**: MEDIUM
- Contains: Vector embeddings and metadata
- Fields expose:
  - `embedding`: 1536-dimensional vectors
  - `metadata`: May contain source text, categories, etc.

**Risk**:
- Metadata may contain sensitive information depending on what's embedded
- Embeddings can be reverse-engineered to approximate original text
- Reveals AI/ML model architecture

**Recommendation**: ⚠️ **REVIEW metadata** - If metadata contains sensitive info, restrict access

---

#### 7. `vector_queries` - Vector Search History
**Sensitivity**: MEDIUM
- Contains: Vector query history and similarity scores
- Links to embeddings table

**Risk**:
- Reveals search patterns and AI behavior
- Can be used to understand system capabilities

**Recommendation**: ⚠️ **CONSIDER restricting** - Limited value for public access

---

### ✅ LOW RISK - Public access acceptable

#### 8. `faqs` - FAQ Content
**Sensitivity**: LOW
- Contains: Public FAQ questions and answers
- Designed for public consumption

**Risk**: Minimal - This is public content by design

**Recommendation**: ✅ **KEEP public access** - This is appropriate for anon key

---

#### 9. `faq_categories` - FAQ Categories
**Sensitivity**: LOW
- Contains: Category names and descriptions
- Public organizational structure

**Risk**: Minimal - Public metadata

**Recommendation**: ✅ **KEEP public access** - This is appropriate for anon key

---

## Recommended RLS Policy Changes

### Option A: Strict Security (Recommended)

**Remove anon key access from 7 tables**:
```sql
-- Remove authenticated policies for sensitive tables
DROP POLICY "authenticated_trace_metrics_read" ON trace_metrics;
DROP POLICY "authenticated_alerts_read" ON alerts;
DROP POLICY "authenticated_agent_reputation_read" ON agent_reputation;
DROP POLICY "authenticated_reputation_events_read" ON reputation_events;
DROP POLICY "authenticated_faq_search_history_read" ON faq_search_history;
DROP POLICY "authenticated_embeddings_read" ON embeddings;
DROP POLICY "authenticated_vector_queries_read" ON vector_queries;

-- Keep only FAQs and categories public
-- (authenticated_faqs_read and authenticated_faq_categories_read remain)
```

**Result**:
- ✅ Public can read FAQs (appropriate)
- ✅ Dashboard users need proper authentication (not just anon key)
- ✅ Sensitive operational data protected
- ✅ Compliance with privacy regulations

---

### Option B: Dashboard-Only Access

**Create separate policies for real authenticated users vs anon**:
```sql
-- This requires distinguishing between:
-- 1. anon role (public, unauthenticated)
-- 2. authenticated role (logged-in Dashboard users)

-- Currently both use the same policy because anon is part of authenticated group
-- Would need to use auth.uid() IS NOT NULL to distinguish real users
```

**Example**:
```sql
-- Replace authenticated policies with user-authenticated policies
DROP POLICY "authenticated_trace_metrics_read" ON trace_metrics;

CREATE POLICY "user_authenticated_trace_metrics_read" ON trace_metrics
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);  -- Only real logged-in users
```

**Result**:
- ✅ Dashboard users (logged in) can see operational data
- ✅ Anon key (public) cannot access sensitive data
- ✅ FAQs remain public

---

### Option C: Keep Current (NOT Recommended)

**Do nothing** - Accept that anon key provides public read access to all 9 tables.

**Risks**:
- 🔴 Business intelligence leakage (costs, usage patterns)
- 🔴 Security information disclosure (errors, alerts, system health)
- 🔴 Privacy violations (user search history)
- 🔴 Competitive disadvantage (agent performance metrics)

---

## Implementation Priority

### P0 (Immediate - Security Risk)
1. **Remove anon access to `trace_metrics`** - Cost/usage data exposure
2. **Remove anon access to `alerts`** - Security vulnerability disclosure
3. **Remove anon access to `faq_search_history`** - Privacy violation

### P1 (High Priority - Business Risk)
4. **Remove anon access to `agent_reputation`** - Competitive intelligence
5. **Remove anon access to `reputation_events`** - Audit trail exposure

### P2 (Medium Priority - Data Protection)
6. **Review and restrict `embeddings`** - Check metadata sensitivity
7. **Review and restrict `vector_queries`** - Search pattern exposure

### P3 (Low Priority - Already Acceptable)
8. **Keep `faqs` public** - Designed for public access ✅
9. **Keep `faq_categories` public** - Public metadata ✅

---

## Migration Script (Option A - Recommended)

```sql
-- Migration: Restrict RLS policies to remove anon key access

BEGIN;

-- Remove authenticated (includes anon) policies for sensitive tables
DROP POLICY IF EXISTS "authenticated_trace_metrics_read" ON trace_metrics;
DROP POLICY IF EXISTS "authenticated_alerts_read" ON alerts;
DROP POLICY IF EXISTS "authenticated_agent_reputation_read" ON agent_reputation;
DROP POLICY IF EXISTS "authenticated_reputation_events_read" ON reputation_events;
DROP POLICY IF EXISTS "authenticated_faq_search_history_read" ON faq_search_history;
DROP POLICY IF EXISTS "authenticated_embeddings_read" ON embeddings;
DROP POLICY IF EXISTS "authenticated_vector_queries_read" ON vector_queries;

-- Create new policies that require real authentication (not anon key)
CREATE POLICY "user_authenticated_trace_metrics_read" ON trace_metrics
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_authenticated_alerts_read" ON alerts
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_authenticated_agent_reputation_read" ON agent_reputation
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_authenticated_reputation_events_read" ON reputation_events
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_authenticated_faq_search_history_read" ON faq_search_history
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_authenticated_embeddings_read" ON embeddings
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "user_authenticated_vector_queries_read" ON vector_queries
    FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

-- FAQs and categories remain public (keep existing policies)
-- authenticated_faqs_read and authenticated_faq_categories_read unchanged

COMMIT;

-- Verification
DO $$
BEGIN
    RAISE NOTICE 'RLS Policy Update Complete';
    RAISE NOTICE 'Public access (anon key): faqs, faq_categories only';
    RAISE NOTICE 'Dashboard access (authenticated users): All tables';
    RAISE NOTICE 'Service role: Full access (unchanged)';
END $$;
```

---

## Testing After Changes

After implementing the recommended changes, update tests:

```python
# tests/test_rls_policies_comprehensive.py

# Anon key should only access FAQs
TABLES_PUBLIC_ANON = ['faqs', 'faq_categories']

# Authenticated users need real JWT (not anon key)
TABLES_AUTHENTICATED_ONLY = [
    'faq_search_history',
    'embeddings', 
    'vector_queries',
    'trace_metrics',
    'alerts',
    'agent_reputation',
    'reputation_events'
]
```

---

## Compliance Considerations

### GDPR / Privacy
- ✅ User search history (`faq_search_history`) should NOT be public
- ✅ User IDs and session tracking require protection
- ✅ Right to be forgotten requires access control

### Security Best Practices
- ✅ Operational metrics should not be publicly accessible
- ✅ Error messages and alerts should be internal only
- ✅ Cost data is business confidential

### Business Intelligence Protection
- ✅ Agent performance metrics are competitive advantage
- ✅ Usage patterns reveal business strategy
- ✅ System architecture should not be publicly documented

---

## Conclusion

**Current State**: Migration 014 provides overly permissive public access via anon key.

**Recommended Action**: Implement Option A (Strict Security) to:
1. Protect sensitive operational data
2. Comply with privacy regulations
3. Prevent competitive intelligence leakage
4. Maintain appropriate public access to FAQs

**Next Steps**:
1. Review and approve this security assessment
2. Create migration to implement recommended RLS changes
3. Update tests to reflect new security model
4. Verify Dashboard authentication works with real user JWTs
5. Test that anon key only accesses FAQs (as intended)
