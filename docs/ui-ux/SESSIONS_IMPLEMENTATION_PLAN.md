# Sessions UI Implementation Plan

This document outlines the phased implementation plan for the Sessions UI feature in MorningAI Owner Console.

## Overview

The Sessions UI allows Owner Console users to monitor and manage AI Agent task execution sessions. The implementation follows a 4-PR approach to ensure incremental delivery and maintainability.

## Current Status

| Phase | PR | Status | Description |
|-------|-----|--------|-------------|
| PR 0 | This document | Completed | Sessions Spec & Implementation Plan |
| PR 1 | #1971 | Merged | Sessions UI Skeleton (Mock Data) |
| PR 2 | TBD | Pending | Sessions API + Wiring |
| PR 3 | TBD | Pending | Sessions Controls + HITL Integration |

## Existing Infrastructure

### Target Application: `owner-console`

- Has `ApprovalQueue.jsx` page handling HITL approval flows
- Has complete API integration patterns (`apiClientWithMeta`)
- Has i18n support (`zh-TW.json`, `en-US.json`)

### Existing Reusable Components

- `@morningai/shared-ui`: Badge, Tabs, Skeleton, Dialog, Card, etc.
- `iotask/`: task-row, activity-list-panel, timeline-list
- `dashboard/`: stat-card, section-card, progress-track

### Existing HITL Infrastructure

- `orchestrator/hitl/action_requests.py`: Complete approval request API
- `api-backend/src/routes/action_requests.py`: REST endpoints
- `ApprovalQueue.jsx`: Reference template for Sessions UI

### Existing Session State Infrastructure

- `orchestrator/dev_agent_v2.py`: `SessionState` + `SessionStore` (Redis)
- Tracks: session_id, task_id, goal, observations, decisions, actions, conversation_history

## Design System Constraints (Must Follow)

| Rule | Description |
|------|-------------|
| Design Tokens | All colors/spacing/fonts must come from `tokens.json`, no hardcoding |
| Component Architecture | Use Radix UI + class-variance-authority + forwardRef |
| i18n | All user-visible text must use `t()` |
| Accessibility | WCAG AAA (7:1 contrast), keyboard navigation, ARIA patterns |
| Animation | Must support `prefers-reduced-motion`, only animate transform/opacity |
| Performance | JS < 500KB gzipped, CSS < 100KB gzipped |

## Implementation Phases

### PR 1: Sessions UI Skeleton (Mock Data) - COMPLETED

**Scope:**
- Add `/sessions` page in `owner-console`
- Use existing shared-ui components
- Left side session list + right side detail panel
- 100% follow design system rules
- Use mock data, no backend required

**Acceptance Criteria:**
- Sessions UI displays with sample data
- Passes lint/CI checks
- Follows `docs/ui-ux/standard.md`

**Implementation:** `handoff/20250928/40_App/owner-console/src/pages/Sessions.jsx`

### PR 2: Backend API Integration

**Scope:**
- Add `/api/sessions` endpoints
- Connect to `ExecutionResult`, `TaskPlan`, `AuditLog`
- Replace mock data with real API calls

**Backend Tasks:**
- Design and implement REST endpoints:
  - `GET /api/sessions` - List all sessions with filtering
  - `GET /api/sessions/{id}` - Get session detail
- Update `docs/openapi.yaml` and regenerate TS client
- Map existing `SessionState` model to API response

**Frontend Tasks:**
- Replace mock fetch with real API calls via `apiClientWithMeta`
- Keep UI contract identical to PR 1

**Acceptance Criteria:**
- `/sessions` page shows real sessions from staging/dev
- API documented in OpenAPI
- Wired into generated client

**Estimated Effort:** 3-4 days

### PR 3: Interactive Controls

**Scope:**
- Pause/Resume/Cancel session controls
- Confidence score display and approval flow
- HITL system integration

**Backend Tasks:**
- Add endpoints for session lifecycle control:
  - `POST /api/sessions/{id}/pause`
  - `POST /api/sessions/{id}/resume`
  - `POST /api/sessions/{id}/cancel`
- Integrate with orchestrator to honor pause/cancel states
- Connect with existing HITL flows (`action_requests.py`)

**Frontend Tasks:**
- Add control buttons in Session Detail view
- Surface HITL state when session awaits human approval
- Link or embed patterns from `ApprovalQueue.jsx`

**Acceptance Criteria:**
- Owner can control sessions from UI
- State changes reflected in real-time
- No regressions in existing HITL flows

**Estimated Effort:** 2-3 days

## Dependencies

```
PR 0 (docs) --> PR 1 (UI Mock) --> PR 2 (API + Integration) --> PR 3 (Controls + HITL)
```

## API Design (Draft)

### GET /api/sessions

```json
{
  "sessions": [
    {
      "id": "session_001",
      "title": "Implement user authentication flow",
      "goal": "Add OAuth2 login with Google and GitHub providers",
      "status": "running",
      "confidence": 0.87,
      "started_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:45:00Z",
      "progress": 65,
      "current_task": "Writing integration tests"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

### GET /api/sessions/{id}

```json
{
  "id": "session_001",
  "title": "Implement user authentication flow",
  "goal": "Add OAuth2 login with Google and GitHub providers",
  "status": "running",
  "confidence": 0.87,
  "started_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "progress": 65,
  "current_task": "Writing integration tests",
  "plan": {
    "total_tasks": 8,
    "completed_tasks": 5,
    "tasks": [
      {
        "id": 1,
        "name": "Analyze existing auth code",
        "status": "completed",
        "type": "ANALYZE_CODE"
      }
    ]
  },
  "logs": [
    {
      "timestamp": "2024-01-15T11:45:00Z",
      "message": "Starting integration test implementation",
      "level": "info"
    }
  ],
  "requires_approval": false,
  "approval_reason": null,
  "pr_url": null,
  "error_message": null
}
```

## Related Documents

- [Sessions UI Specification](./SESSIONS_UI_SPEC.md)
- [UI/UX Standard](./standard.md)
- [Design System Quickstart](../DESIGN_SYSTEM_QUICKSTART.md)

## Related Issues

- [#1823](https://github.com/RC918/morningai/issues/1823) - Sessions UI implementation
- [#1971](https://github.com/RC918/morningai/pull/1971) - Sessions UI PR (merged)
