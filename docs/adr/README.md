# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the MorningAI project. ADRs document significant architectural decisions, their context, alternatives considered, and consequences.

## ADR Index

| Number | Title | Status | Date | Summary |
|--------|-------|--------|------|---------|
| [001](./001-pnpm-turborepo-migration.md) | pnpm + Turborepo Migration | Accepted | 2025-10-28 | Migration from npm to pnpm and adoption of Turborepo for monorepo management |
| [002](./002-producer-consumer-architecture.md) | Producer-Consumer Architecture for Orchestrator | Accepted | 2025-10-29 | Redis + RQ based producer-consumer pattern separating API and worker layers |
| [003](./003-backend-of-record.md) | Backend of Record for MorningAI | Accepted | 2025-10-29 | Designation of `handoff/.../api-backend` as the canonical backend application |
| [004](./004-shared-core-executor-pattern.md) | Shared Core Executor Pattern | Accepted | 2025-11-24 | Simple mode and LangGraph mode share `graph.execute()` as common execution engine |
| [005](./005-dual-orchestrator-architecture.md) | Dual Orchestrator Architecture | Accepted (Interim) | 2025-11-03 | API Orchestrator vs Worker Orchestrator separation with consolidation plan for 2026 Q1 |

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

### ADR Structure

Each ADR should include:

- **Title**: Short noun phrase describing the decision
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Date**: When the decision was made
- **Deciders**: Who was involved in the decision
- **Context**: What is the issue that we're seeing that is motivating this decision?
- **Decision**: What is the change that we're proposing and/or doing?
- **Alternatives Considered**: What other options were evaluated?
- **Consequences**: What becomes easier or more difficult to do because of this change?
- **Related Documentation**: Links to relevant docs, code, or other ADRs

## When to Create an ADR

Create an ADR when making decisions about:

- System architecture and component boundaries
- Technology choices (frameworks, databases, services)
- Deployment and infrastructure patterns
- Security and compliance approaches
- API design and integration patterns
- Data models and persistence strategies
- Development workflows and tooling

## How to Create an ADR

1. Copy the template from an existing ADR
2. Assign the next sequential number (e.g., 004)
3. Fill in all sections with clear, concise information
4. Include links to related documentation and code
5. Submit as part of a pull request
6. Update this index after the ADR is accepted

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [Architecture Decision Records (Martin Fowler)](https://martinfowler.com/articles/scaling-architecture-conversationally.html)
