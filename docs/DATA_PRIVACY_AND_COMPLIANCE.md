# Data Privacy and Compliance Guide

**Version**: 1.0  
**Last Updated**: 2025-12-16  
**Status**: Active  
**Owner**: Engineering Team

## Overview

This document outlines MorningAI's data privacy practices, compliance requirements, and implementation guidelines. MorningAI is a multi-tenant AI agent orchestration platform that processes sensitive business data, requiring strict adherence to data protection principles.

## Data Classification

MorningAI handles four categories of data, each with specific handling requirements:

**Tier 1 - Critical (Highest Protection)**: Authentication credentials, API keys, service role keys, encryption keys, and JWT secrets. These are never logged, stored in environment variables only, and rotated on a defined schedule per SECRET_ROTATION_POLICY.md.

**Tier 2 - Sensitive**: Tenant business data, agent task outputs, user PII (email, name), and session data. Protected by Row Level Security (RLS), encrypted at rest, and access-logged.

**Tier 3 - Internal**: System metrics, agent reputation scores, cost tracking data, and audit logs. Available to platform operators with appropriate roles.

**Tier 4 - Public**: Documentation, API schemas, and public-facing configuration. No special handling required.

## Multi-Tenant Data Isolation

MorningAI implements defense-in-depth for tenant isolation through multiple layers.

### Database Layer (Supabase/PostgreSQL)

Row Level Security (RLS) enforces tenant isolation at the database level. Every table containing tenant data includes a `tenant_id` column with RLS policies that restrict access based on the authenticated user's tenant membership. The implementation details are documented in RLS_IMPLEMENTATION_GUIDE.md.

Key tables with RLS enforcement include `agent_tasks`, `tenants`, `users`, `platform_bindings`, `external_integrations`, and `memory`. Service role access bypasses RLS for backend operations but is never exposed to client applications.

### Application Layer

The API backend validates tenant context on every request through middleware that extracts tenant_id from JWT claims and injects it into the request context. All database queries automatically scope to the authenticated tenant. Cross-tenant access attempts are logged to the audit system and trigger alerts.

### Network Layer

Tenant data flows through isolated channels with API endpoints scoped by tenant context, Redis keys prefixed with tenant identifiers, and separate Vercel deployments for Owner Console (admin.gm365.me) and Tenant Dashboard (app.gm365.me).

## Authentication and Authorization

### JWT-Based Authentication

MorningAI uses JWT tokens for authentication with the following security measures: tokens expire after a configurable period (default 1 hour), refresh tokens enable session continuity without re-authentication, token revocation is supported via a blocklist in Redis, and all tokens are signed with RS256 algorithm.

### Role-Based Access Control (RBAC)

Three primary roles govern access: Owner (platform administrators with full system access), Admin (tenant administrators who can manage their tenant's users and settings), and User (standard tenant users with access to assigned features).

Permission checks occur at both API gateway and service layers. The governance framework (GOVERNANCE_FRAMEWORK.md) provides additional fine-grained controls for agent operations.

## Data Processing Principles

### Purpose Limitation

Data collected for a specific purpose is not repurposed without explicit consent. Agent task data is used only for task execution and audit purposes. User analytics are anonymized before aggregation.

### Data Minimization

The platform collects only data necessary for operation. PII collection is limited to authentication requirements. Agent outputs are sanitized to remove unnecessary sensitive information. Logs exclude sensitive data patterns (detected via regex).

### Storage Limitation

Data retention follows defined policies: active session data is retained for 30 days, completed task data for 90 days (configurable per tenant), audit logs for 1 year, and deleted data is purged within 30 days of deletion request.

### Accuracy

Users can update their profile information at any time. Tenant admins can correct organizational data. Data synchronization ensures consistency across services.

## Compliance Framework

### GDPR Alignment

For users in the European Economic Area, MorningAI supports the following rights.

**Right to Access**: Users can export their data via the API or request a data package from support.

**Right to Rectification**: Profile and organizational data can be updated through the application.

**Right to Erasure**: Account deletion triggers cascading deletion of all associated data within 30 days.

**Right to Data Portability**: Data export is available in JSON format.

**Right to Object**: Users can opt out of non-essential data processing.

### SOC 2 Type II Considerations

MorningAI's architecture supports SOC 2 compliance through access controls (RBAC, RLS, audit logging), change management (Git-based workflows, PR reviews, CI/CD), risk assessment (governance framework, reputation system), and monitoring (Sentry integration, metrics endpoints, alerting).

### Data Processing Agreements

When MorningAI processes data on behalf of tenants, the relationship is governed by a Data Processing Agreement (DPA) that specifies processing purposes, data categories, security measures, and sub-processor obligations.

## Security Controls

### Encryption

**At Rest**: All data in Supabase is encrypted using AES-256. Redis data uses TLS connections.

**In Transit**: All API communications use TLS 1.3. Internal service communication uses mTLS where supported.

### Secret Management

Secrets are managed according to SECRET_ROTATION_POLICY.md with environment-based configuration (never in code), automated rotation schedules, and immediate rotation on suspected compromise.

### Vulnerability Management

The platform maintains security through dependency scanning (Dependabot, npm audit), secret scanning (Gitleaks, TruffleHog), SAST in CI pipeline, and regular penetration testing.

## Audit and Monitoring

### Audit Trail

All significant actions are logged with timestamp, actor (user_id, tenant_id), action type, resource affected, and outcome (success/failure). Audit logs are immutable and retained for compliance periods.

### Real-Time Monitoring

Sentry captures errors and performance data. Custom metrics track API latency, error rates, and resource usage. Alerts notify operators of anomalies.

### Incident Response

Security incidents follow a defined process: detection (automated or reported), containment (isolate affected systems), investigation (root cause analysis), remediation (fix and verify), and notification (inform affected parties per legal requirements).

## Data Subject Requests

### Request Handling Process

Data subject requests (access, deletion, portability) are handled through a standardized process. Requests are submitted via support channel or in-app. Identity verification confirms the requester's authority. Requests are fulfilled within 30 days (GDPR requirement). Confirmation is provided to the requester.

### Technical Implementation

The API provides endpoints for data export (`GET /api/users/{id}/export`), account deletion (`DELETE /api/users/{id}`), and consent management (`PUT /api/users/{id}/preferences`).

## Third-Party Data Sharing

### Sub-Processors

MorningAI uses the following sub-processors: Supabase (database hosting, US/EU regions), Vercel (frontend hosting, global CDN), Render (backend hosting, US region), Redis Cloud (caching, configurable region), and Sentry (error tracking, US region).

### AI Model Providers

When AI features are enabled, data may be sent to LLM providers (OpenAI, Anthropic, etc.). Tenant configuration controls which providers are enabled. Sensitive data patterns are filtered before transmission. No training on customer data without explicit consent.

## Compliance Checklist

For new features or integrations, verify the following: data classification is documented, RLS policies cover new tables, audit logging captures relevant actions, PII handling follows minimization principles, retention policies are defined, third-party data sharing is disclosed, and security controls are implemented.

## Related Documentation

- GOVERNANCE_FRAMEWORK.md - Agent governance and policy enforcement
- RLS_IMPLEMENTATION_GUIDE.md - Database-level tenant isolation
- SECRET_ROTATION_POLICY.md - Credential management
- SECURITY_JWT_RBAC.md - Authentication and authorization
- MULTI_TENANT_GOVERNANCE.md - Tenant management policies

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-16 | Engineering | Initial release |

## Contact

For privacy-related inquiries, contact the Data Protection team through the appropriate internal channels.
