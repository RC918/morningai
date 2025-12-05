# MorningAI Sessions UI Official Specification (SaaS Architecture Version)

This document serves as the official specification for the Sessions UI in MorningAI Owner Console. Engineers can implement directly from this spec without requiring Figma mockups.

All specifications are based on the existing `@morningai/shared-ui`, `tokens.json`, and `iotask` Layout System.

## Related Resources

| Resource | Description |
|----------|-------------|
| [UI/UX Standard](./standard.md) | Core UI/UX standards and guidelines |
| [Design System Quickstart](../DESIGN_SYSTEM_QUICKSTART.md) | 2-minute guide to get started |
| [Sessions.jsx](../../handoff/20250928/40_App/owner-console/src/pages/Sessions.jsx) | Current implementation |

## 0. Design Principles

All Session-related pages must follow these rules:

### 1. No Custom UI

Only use components from `@morningai/shared-ui` and `iotask` packages.

### 2. No Figma Mockups Required

If components can be composed from shared-ui, implement directly. No designer intervention needed.

### 3. Figma Only for New Components

Only create Figma mockups when a genuinely new component is needed (component-level, not page-level).

### 4. Spacing / Colors / Shadow from tokens.json

Never hardcode spacing (px), colors (#fff), shadows, or border-radius.

### 5. Pages Must Use AdminShell

Sidebar, topbar, and layout are provided by shared-ui.

## 1. Page Layout Architecture

Sessions UI uses a dual-pane layout:

### Left Pane: Sessions List (fixed width 280px)

### Right Pane: Session Detail (adaptive / main view)

```
+--------------------------------------------------------------+
|                      AdminShell Topbar                        |
+---------------+----------------------------------------------+
| Session List  | Session Detail                                |
| (Left Pane)   | (Main Content)                                |
+---------------+----------------------------------------------+
```

## 2. Left Pane - Sessions List Specification

### Component Base: Use shared-ui `<ListItem />` + iotask style

### A. Display Fields

Each Session List Item contains:

| Field | Type | Description |
|-------|------|-------------|
| sessionId (partial mask) | text | Ex: `sess_xxxxx123` |
| timestamp | text | Ex: `5 min ago` |
| status | badge | success / warn / error |
| agent type | tag | Ex: `LLM`, `Workflow`, `Planner` |

### B. UI Specification (Precise)

| Property | Value |
|----------|-------|
| Height | 56px |
| Left padding | 16px |
| Right padding | 16px |
| Gap | 8px |
| Font | text-sm (tokens) |
| hover | bg-[var(--surface-muted)] |
| active | border-left: 3px solid var(--brand-600) |

### C. Required Components

```tsx
import { ListItem, Badge, Tag } from "@morningai/shared-ui";
```

### D. Component Example

```tsx
<ListItem
  title="sess_9A18E3...21"
  subtitle="5 mins ago"
  active={selected}
  rightSection={
    <Badge variant="green" label="Active" />
  }
/>
```

## 3. Right Pane - Session Detail Specification

The right side content consists of three main sections:

### (1) Session Metadata (Basic Information)

### (2) Event Timeline

### (3) Debug / Raw Payload (Collapsible)

### (1) Session Metadata Specification

#### Component: `<SectionCard />`

#### Fields:

| Name | Format |
|------|--------|
| Session ID | monospaced text |
| Start Time | date + time |
| User | text |
| Agent Type | badge |
| Duration | text |

#### Example:

```tsx
<SectionCard title="Session Info">
  <MetadataRow label="Session ID" value="sess_12398ABCDEF" />
  <MetadataRow label="Started" value="2025/12/03 09:12:22" />
  <MetadataRow label="User" value="TaiwanUser_001" />
  <MetadataRow label="Agent Type" value={<Badge variant="blue" label="LLM" />} />
</SectionCard>
```

### (2) Event Timeline Specification

#### Components:

- `<Timeline />`
- `<TimelineItem />`
- Or use `<ActivityListItem />` variant if Timeline not available

#### Each Event Contains:

| Field | Type | Description |
|-------|------|-------------|
| timestamp | small text | Ex: 09:12:31 |
| event type | tag | Ex: user_input, model_response, error |
| payload summary | truncated text | First line highlighted |
| sequence | left dot | Color based on tokens |

#### Color Rules (from tokens)

| Event Type | Color |
|------------|-------|
| user_input | var(--brand-600) |
| model_response | var(--success-600) |
| tool_call | var(--warning-600) |
| error | var(--danger-600) |

#### Timeline Item Style (Precise)

```
+-------------------------------------------------------------+
| *  09:11:32                                                  |
|    user_input                                                 |
|    "Hello, I need help booking a flight..."                   |
+-------------------------------------------------------------+
```

#### Timeline Component Example:

```tsx
<SectionCard title="Events Timeline">
  <Timeline>
    {events.map((evt, index) => (
      <TimelineItem
        key={index}
        time={evt.time}
        color={evt.color}
        label={evt.type}
        content={evt.summary}
      />
    ))}
  </Timeline>
</SectionCard>
```

### (3) Debug Payload Specification

#### Components:

- `<CodeBlock />`
- `<Collapsible />` or `<Accordion />`

#### UI Specification:

- Default: collapsed
- Title: `Raw Payload`
- Use monospace font
- Copy button (already styled in shared-ui)

## 4. Sessions Page Organization (Complete Version)

```tsx
<AdminShell>

  <div className="flex h-full">

    {/* Left Pane */}
    <aside className="w-72 border-r border-[var(--border)] bg-[var(--surface)]">
      <SessionsSearchBar />
      <SessionList />
    </aside>

    {/* Main Pane */}
    <main className="flex-1 p-6 space-y-6">
      <SessionMetadata />
      <SessionTimeline />
      <SessionDebugPanel />
    </main>

  </div>

</AdminShell>
```

## 5. Engineering Implementation Guidelines

### Do Not Need Figma

Structure is entirely determined by this document + shared-ui.

### Do Not Add Custom CSS

If you need spacing / color, use tokens.

### Do Not Add Custom button / card / badge

Use everything from shared-ui.

### Any New UI Behavior Must Be Added to shared-ui

If existing components cannot be composed, you (product/owner) decide if Figma is needed.

### Left and Right Pane Layout Must Follow This Document

Do not redefine height / width / borders yourself.

## 6. Current Implementation Status

The Sessions UI has been implemented in `Sessions.jsx` (PR #1971) with the following features:

| Feature | Status | Notes |
|---------|--------|-------|
| Dual-pane layout | Implemented | Grid-based responsive layout |
| Session List | Implemented | With status filtering |
| Session Detail | Implemented | Plan, Tasks, Logs tabs |
| Mock Data | Implemented | 4 sample sessions |
| Status Indicators | Implemented | running/paused/completed/failed |
| i18n Support | Implemented | zh-TW and en-US |
| HITL Integration | Partial | Approval indicators shown |
| Real API Integration | Pending | PR 2 scope |
| Session Controls | Pending | PR 3 scope |

## 7. Future Enhancements (Roadmap)

### PR 2: Sessions API + Wiring

- Backend `GET /api/sessions`, `GET /api/sessions/{id}` endpoints
- Replace mock data with real API calls
- OpenAPI documentation

### PR 3: Sessions Controls + HITL Integration

- Pause/Resume/Cancel session controls
- Full HITL approval flow integration
- Real-time status updates

## Related Issues

- [#1823](https://github.com/RC918/morningai/issues/1823) - Sessions UI implementation
- [#1971](https://github.com/RC918/morningai/pull/1971) - Sessions UI PR (merged)
