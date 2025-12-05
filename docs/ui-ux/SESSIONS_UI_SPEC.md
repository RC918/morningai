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

### Left Pane: Sessions List (fixed width w-72 / 288px)

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

The right side content uses a **Tabs-based layout** with two main tabs:

### Tab 1: Task Plan (default)

### Tab 2: Activity Log

### Session Header (Above Tabs)

The header section displays session metadata and action buttons:

#### Fields:

| Name | Format |
|------|--------|
| Title | text (session title) |
| Goal | text (session goal description) |
| Status | Badge (running/paused/completed/failed) |
| User | text (triggering user) |
| Agent Type | badge (LLM/Workflow/Planner) |

#### Action Buttons (contextual based on status):

- **Running**: Pause, Cancel
- **Paused**: Resume, Cancel
- **Requires Approval**: Approve button

### Tab 1: Task Plan Specification

#### Components:

- `<Tabs />`, `<TabsList />`, `<TabsTrigger />`, `<TabsContent />`
- `<Progress />`
- `<Badge />`

#### Content Sections:

1. **Progress Summary**: Shows completed/total tasks and confidence percentage
2. **Approval Banner** (conditional): Displays when session requires approval
3. **Error Banner** (conditional): Displays when session has failed
4. **Task List**: Sequential list of tasks with status indicators

#### Task Item Fields:

| Field | Type | Description |
|-------|------|-------------|
| index | number | Task sequence number |
| name | text | Task description |
| status | icon | running/completed/failed/pending/waiting_approval |
| type | tag | Ex: research, code, review, deploy |

#### Task Status Colors (from tokens):

| Status | Border/Background |
|--------|-------------------|
| running | border-calm, bg-calm-10 |
| completed | border-growth-20, bg-growth-10 |
| failed | border-energy, bg-energy-10 |
| waiting_approval | border-wisdom, bg-wisdom-10 |
| pending | border-[var(--border)] |

### Tab 2: Activity Log Specification

#### Components:

- Log entries with level-based styling

#### Each Log Entry Contains:

| Field | Type | Description |
|-------|------|-------------|
| timestamp | small text | Ex: 09:12:31 |
| level | indicator | info/warning/error/success |
| message | text | Log message content |

#### Level Color Rules (from tokens):

| Level | Dot Color | Background |
|-------|-----------|------------|
| info | bg-neutral-400 | bg-neutral-50 |
| warning | bg-wisdom | bg-wisdom-10 |
| error | bg-energy | bg-energy-10 |
| success | bg-growth | bg-growth-10 |

#### Log Entry Style:

```
+-------------------------------------------------------------+
| *  "Analyzing repository structure..."                       |
|    09:11:32                                                   |
+-------------------------------------------------------------+
```

#### Activity Log Component Example:

```tsx
<TabsContent value="logs" className="p-5">
  <div className="space-y-3">
    {selectedSession.logs.map((log, index) => (
      <div
        key={index}
        className={`flex items-start gap-3 p-3 rounded-lg ${
          log.level === 'error' ? 'bg-energy-10'
          : log.level === 'warning' ? 'bg-wisdom-10'
          : log.level === 'success' ? 'bg-growth-10'
          : 'bg-neutral-50 dark:bg-neutral-800'
        }`}
      >
        <div className={`w-2 h-2 rounded-full mt-2 ${
          log.level === 'error' ? 'bg-energy'
          : log.level === 'warning' ? 'bg-wisdom'
          : log.level === 'success' ? 'bg-growth'
          : 'bg-neutral-400'
        }`} />
        <div className="flex-1">
          <p className="text-sm text-[var(--text-primary)]">{log.message}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            {formatTimestamp(log.timestamp)}
          </p>
        </div>
      </div>
    ))}
  </div>
</TabsContent>
```

### Session Footer

Displays session start time and optional PR link.

## 4. Sessions Page Organization (Complete Version)

```tsx
<AdminShell>
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

    {/* Left Pane - Sessions List (w-72 / 288px equivalent) */}
    <aside className="lg:col-span-1 space-y-3">
      <SessionsFilterTabs /> {/* All / Running / Needs Approval */}
      <SessionList />
    </aside>

    {/* Main Pane - Session Detail */}
    <main className="lg:col-span-2">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        {/* Session Header */}
        <SessionHeader />
        
        {/* Tabs: Plan / Logs */}
        <Tabs defaultValue="plan">
          <TabsList>
            <TabsTrigger value="plan">Task Plan</TabsTrigger>
            <TabsTrigger value="logs">Activity Log</TabsTrigger>
          </TabsList>
          <TabsContent value="plan">
            <TaskPlanView />
          </TabsContent>
          <TabsContent value="logs">
            <ActivityLogView />
          </TabsContent>
        </Tabs>
        
        {/* Session Footer */}
        <SessionFooter />
      </div>
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
