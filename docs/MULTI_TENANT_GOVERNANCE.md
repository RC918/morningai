# Multi-Tenant Governance Guide

**Version**: 1.0  
**Last Updated**: 2025-12-16  
**Status**: Active  
**Owner**: Engineering Team

## Overview

MorningAI operates as a multi-tenant platform where multiple organizations (tenants) share infrastructure while maintaining strict data isolation and independent configuration. This document defines the governance model, isolation boundaries, and operational policies for multi-tenant operations.

## Tenant Model

### Tenant Definition

A tenant in MorningAI represents an independent organization with its own users, data, configurations, and billing relationship. Each tenant operates in logical isolation from other tenants while sharing the underlying platform infrastructure.

### Tenant Hierarchy

The platform supports a two-level hierarchy. At the platform level, the Owner Console (admin.gm365.me) provides platform-wide administration including tenant provisioning, system monitoring, and global policy management. At the tenant level, each tenant has its own Tenant Dashboard (app.gm365.me) with tenant-specific users, agent configurations, task history, and integrations.

### Tenant Lifecycle

**Provisioning**: New tenants are created through the Owner Console. The provisioning process creates a tenant record in the database, generates initial admin credentials, applies default policies and quotas, and sets up billing integration.

**Active Operation**: During normal operation, tenants manage their own users and permissions, configure agent behaviors within platform limits, execute tasks and view results, and manage integrations with external systems.

**Suspension**: Tenants may be suspended for billing issues, policy violations, or security concerns. Suspended tenants retain data but lose API access.

**Termination**: Tenant termination triggers data export opportunity (30 days), cascading deletion of all tenant data, and audit log retention per compliance requirements.

## Isolation Boundaries

### Data Isolation

MorningAI implements multiple layers of data isolation to ensure tenant data remains separate and secure.

**Database Level**: Row Level Security (RLS) in PostgreSQL enforces tenant boundaries at the database layer. Every query from authenticated users automatically filters by tenant_id. Service role access (used by backend services) bypasses RLS but is never exposed to client applications. Implementation details are in RLS_IMPLEMENTATION_GUIDE.md.

**Application Level**: The API backend validates tenant context on every request. JWT tokens include user_id claims; the backend queries the user_profiles table to retrieve the associated tenant_id. RLS policies use `auth.uid()` to look up tenant membership from user_profiles. Cross-tenant access attempts are blocked and logged.

**Cache Level**: Redis keys are prefixed with tenant identifiers to prevent cache pollution between tenants. Key format follows the pattern `tenant:{tenant_id}:{resource_type}:{resource_id}`.

**Storage Level**: File uploads and artifacts are stored in tenant-specific paths. Access controls prevent cross-tenant file access.

### Compute Isolation

Agent task execution maintains tenant isolation through task queue separation (tenant-specific Redis queues), resource quotas per tenant, and isolated execution contexts for agent operations.

### Network Isolation

While tenants share infrastructure, network-level controls include rate limiting per tenant, separate API keys per tenant, and audit logging of all cross-boundary access attempts.

## Governance Policies

### Resource Quotas

Each tenant operates within defined resource limits that can be configured based on subscription tier.

**Compute Quotas**: Maximum concurrent agent tasks (default 5), daily task execution limit (default 100), and maximum task duration (default 5 minutes / 300 seconds).

**Storage Quotas**: Database storage limit (default 1GB), maximum documents (default 1000), maximum embeddings (default 10000), and log retention period (default 90 days).

**API Quotas**: Requests per minute (default 60), requests per hour (default 1000), requests per day (default 10000), and LLM tokens per day (default 100000).

### Cost Controls

The governance framework (GOVERNANCE_FRAMEWORK.md) provides cost tracking and budget enforcement at the tenant level. Daily and hourly budget limits can be configured. Cost overruns trigger alerts and optional task blocking. Usage reports are available per tenant.

### Policy Inheritance

Policies follow a hierarchical model where platform defaults provide baseline configuration, tenant overrides allow customization within platform limits, and user-level settings enable personal preferences where allowed.

## Access Control

### Platform Roles

**Owner**: Platform administrators with access to all tenants, system configuration, and global policies. Owners access the platform through the Owner Console.

**Tenant Admin**: Administrators for a specific tenant who can manage tenant users, configure tenant settings, and view tenant-wide reports.

**Tenant User**: Standard users within a tenant with access to assigned features and their own data.

### Permission Model

Permissions are evaluated in order: platform policies (cannot be overridden), tenant policies (can restrict but not expand platform policies), and user permissions (can restrict but not expand tenant policies).

### Cross-Tenant Access

Cross-tenant access is prohibited by default. The only exceptions are platform Owners accessing tenant data for support purposes (logged), automated compliance checks (system-initiated), and explicit data sharing agreements between tenants (future feature).

## Agent Governance

### Agent Reputation

The reputation system (GOVERNANCE_FRAMEWORK.md) tracks agent behavior across tenants while maintaining tenant isolation. Reputation scores are tenant-specific. Permission levels gate access to sensitive operations. Violations affect only the tenant's agents.

### Policy Enforcement

Agent operations are governed by the PolicyGuard middleware which enforces file access restrictions (allow/deny patterns), network access controls (domain allowlists), tool permission requirements, and risk-based routing for high-impact operations.

### Human-in-the-Loop (HITL)

High-risk operations require human approval based on configurable thresholds. HITL decisions are scoped to the tenant. Approval workflows respect tenant admin hierarchies.

## Compliance and Audit

### Audit Requirements

All tenant operations are logged with tenant_id, user_id, timestamp, action type, resource affected, and outcome. Audit logs are immutable and retained per compliance requirements (minimum 1 year).

### Compliance Reporting

Tenants can generate compliance reports including access logs for their tenant, data processing records, security event summaries, and configuration change history.

### Regulatory Alignment

The multi-tenant architecture supports GDPR requirements through tenant-level data export and deletion, SOC 2 controls through access logging and change management, and HIPAA considerations through audit trails and access controls (when applicable).

## Operational Procedures

### Tenant Onboarding

The standard onboarding process includes tenant record creation in database, admin user provisioning, default policy application, integration setup (if applicable), and welcome communication.

### Tenant Support

Support requests are handled with tenant context. Support staff access tenant data only when necessary and all access is logged. Tenants can view support access logs.

### Incident Response

Security incidents affecting multiple tenants follow the platform incident response process. Tenant-specific incidents are handled with tenant notification. All incidents are documented in the audit trail.

### Maintenance Windows

Platform maintenance is communicated in advance. Tenant-specific maintenance (data migrations, etc.) is coordinated with tenant admins. Emergency maintenance follows the runbook procedures.

## Configuration Reference

### Tenant Settings

Tenants can configure the following settings through the Tenant Dashboard or API.

**General**: Tenant name and display settings, timezone and locale preferences, and notification preferences.

**Security**: Password policies, session timeout settings, and IP allowlists (optional).

**Agents**: Default agent configurations, cost budget limits, and HITL thresholds.

**Integrations**: External service connections, webhook endpoints, and API key management.

### Platform Settings (Owner Only)

Platform administrators can configure global rate limits, default tenant quotas, feature flags, and system-wide policies.

## Monitoring and Alerting

### Tenant Health Metrics

The platform monitors per-tenant metrics including API request rates and latency, task execution success rates, resource utilization, and error rates.

### Alerting

Alerts are configured at both platform and tenant levels. Platform alerts notify Owners of system-wide issues. Tenant alerts notify tenant admins of tenant-specific issues.

### Dashboards

The Owner Console provides platform-wide dashboards. Tenant Dashboards show tenant-specific metrics. Both support custom dashboard creation.

## Best Practices

### For Platform Operators

Regularly review tenant resource utilization. Monitor for unusual cross-tenant access patterns. Keep tenant quotas aligned with subscription tiers. Document all manual tenant interventions.

### For Tenant Administrators

Implement least-privilege access for users. Regularly review user permissions. Configure appropriate cost budgets. Enable HITL for high-risk operations.

### For Developers

Always include tenant_id in database queries. Never bypass RLS without explicit justification. Log tenant context in all operations. Test features with multi-tenant scenarios.

## Related Documentation

- GOVERNANCE_FRAMEWORK.md - Agent governance and policy enforcement
- RLS_IMPLEMENTATION_GUIDE.md - Database-level tenant isolation
- DATA_PRIVACY_AND_COMPLIANCE.md - Privacy and compliance requirements
- SECURITY_JWT_RBAC.md - Authentication and authorization
- SECRET_ROTATION_POLICY.md - Credential management

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-16 | Engineering | Initial release |

## Appendix: Tenant Data Model

### Core Tables

```
tenants
├── id (UUID, PK)
├── name (TEXT)
├── slug (TEXT, unique)
├── settings (JSONB)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

users
├── id (UUID, PK)
├── tenant_id (UUID, FK → tenants)
├── email (TEXT)
├── role (TEXT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

agent_tasks
├── task_id (TEXT, PK)
├── tenant_id (UUID, FK → tenants)
├── trace_id (UUID)
├── status (TEXT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### RLS Policy Pattern

All tenant-scoped tables follow this RLS pattern:

```sql
-- Service role bypasses RLS
CREATE POLICY "service_role_all_access" ON table_name
    FOR ALL TO service_role USING (true);

-- Authenticated users see only their tenant's data
CREATE POLICY "users_tenant_isolation" ON table_name
    FOR ALL TO authenticated
    USING (tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid()))
    WITH CHECK (tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid()));

-- Anonymous users have no access
CREATE POLICY "anon_no_access" ON table_name
    FOR ALL TO anon USING (false);
```
