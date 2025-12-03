# Owner Console UI Refactor Specification

## Executive Summary

This specification defines a comprehensive UI refactoring roadmap for the Owner Console application. The goal is to upgrade the current MVP-level UI to a professional SaaS admin dashboard, fully integrated with the `@morningai/shared-ui` design system, adopting the **iotask** visual style (clean white background, soft shadows, modern aesthetics).

**Target**: Transform Owner Console into a world-class SaaS management dashboard with consistent design language and engineering maintainability.

---

## Current State Analysis

### Problems Identified

1. **Design System Disconnect**: Owner Console does not fully utilize `@morningai/shared-ui` design tokens and components
2. **Inconsistent Styling**: Layout, spacing, colors, and typography are inconsistent (MVP-level)
3. **Mixed UI Approaches**: Tailwind hand-coded + Apple UI experiments + legacy JSX
4. **Visual System Fragmentation**: Disconnected from Tenant Dashboard and Shared UI visual systems

### Existing Infrastructure (Strengths)

- `packages/shared-ui/src/tokens.json` - Centralized design tokens
- `packages/shared-ui/src/components/ui/` - 60+ UI components
- Three-tier Storybook architecture (shared-ui, owner-console, frontend-dashboard)
- i18n infrastructure with 100% coverage
- CI/CD quality gates for a11y, i18n, and import compliance

---

## Refactoring Roadmap

The refactoring is divided into **4 PRs**, each completing a distinct phase.

---

## PR1: Design Token Integration

### Objective

Ensure Owner Console UI uses 100% shared-ui tokens (no custom colors or spacing).

### Scope

1. Import `packages/shared-ui/dist/tokens.css` in owner-console
2. Update Tailwind config:
   ```javascript
   content: [
     "../../packages/shared-ui/src/**/*",
     "../../packages/shared-ui/dist/**/*",
     "./src/**/*.{js,jsx,ts,tsx}"
   ]
   ```
3. Replace all hardcoded color values:
   - `#f2f3f5` -> `var(--surface-muted)`
   - `#1f2937` -> `var(--text-primary)`
   - `rgba(...)` -> semantic tokens
4. Use token-based classes:
   ```css
   bg-[var(--surface-muted)]
   text-[var(--text-primary)]
   border-[var(--border)]
   rounded-[var(--radius-lg)]
   ```
5. Remove unnecessary resets/styles from owner-console `index.css`

### iotask Design Tokens

```json
{
  "color-surface": "#ffffff",
  "color-surface-muted": "#f8fafc",
  "color-border": "#e2e8f0",
  "color-text-primary": "#0f172a",
  "color-text-secondary": "#64748b",
  "brand-50": "#eff6ff",
  "brand-100": "#dbeafe",
  "brand-500": "#3b82f6",
  "brand-600": "#2563eb",
  "brand-700": "#1d4ed8",
  "success-50": "#ecfdf5",
  "success-600": "#16a34a",
  "warning-50": "#fffbeb",
  "warning-600": "#d97706",
  "danger-50": "#fef2f2",
  "danger-600": "#dc2626"
}
```

### Definition of Done

- [ ] Owner Console colors are fully consistent
- [ ] Lint rules prohibit hardcoded color values
- [ ] PR includes Before/After color comparison screenshots

---

## PR2: AdminShell Layout Components

### Objective

Create a unified SaaS admin layout in `@morningai/shared-ui` for Owner Console.

### New Components (in shared-ui)

```
packages/shared-ui/src/components/admin/
├── AdminShell.tsx
├── AdminSidebar.tsx
└── AdminTopbar.tsx
```

### AdminShell API

```tsx
<AdminShell
  navItems={[
    { label: "Dashboard", href: "/dashboard", icon: Home, active: true },
    { label: "Agents", href: "/agents" },
    { label: "Tenants", href: "/tenants" },
    { label: "Monitoring", href: "/monitoring" },
    { label: "Governance", href: "/governance" },
  ]}
  user={{
    name: "Platform Owner",
    role: "owner",
    avatar: "/avatar.png"
  }}
>
  {children}
</AdminShell>
```

### Component Specifications

#### AdminShell.tsx
```tsx
"use client";

import { AdminSidebar } from "./AdminSidebar";
import { AdminTopbar } from "./AdminTopbar";

export function AdminShell({ navItems, user, children }) {
  return (
    <div className="min-h-screen bg-[var(--surface-muted)] text-[var(--text-primary)]">
      <div className="flex">
        <AdminSidebar navItems={navItems} user={user} />
        <div className="flex-1 flex flex-col">
          <AdminTopbar user={user} />
          <main className="p-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
```

#### AdminSidebar.tsx
```tsx
"use client";

import Link from "next/link";

export function AdminSidebar({ navItems, user }) {
  return (
    <aside className="w-64 border-r border-[var(--border)] bg-[var(--surface)] shadow-soft">
      <div className="px-6 py-5 border-b border-[var(--border)]">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-[var(--brand-500)] text-white flex items-center justify-center font-semibold">
            M
          </div>
          <div>
            <div className="text-sm font-semibold">MorningAI</div>
            <div className="text-xs text-[var(--text-secondary)]">Owner Console</div>
          </div>
        </div>
      </div>
      <nav className="px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block px-3 py-2.5 rounded-lg text-sm transition ${
              item.active
                ? "bg-[var(--brand-50)] text-[var(--brand-700)] font-medium"
                : "text-[var(--text-secondary)] hover:bg-[var(--surface-muted)]"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

#### AdminTopbar.tsx
```tsx
"use client";

export function AdminTopbar({ user }) {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-[var(--border)] bg-[var(--surface)]">
      <div className="text-sm text-[var(--text-secondary)]">
        Platform Overview
      </div>
      <div className="flex items-center gap-4">
        <input
          placeholder="Search tenants, events, agents..."
          className="h-9 w-64 px-3 rounded-full border border-[var(--border)] bg-[var(--surface-muted)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--brand-100)]"
        />
        <div className="h-8 w-8 rounded-full bg-[var(--surface-muted)]"></div>
      </div>
    </header>
  );
}
```

> **Note**: Use `bg-[var(--surface-muted)]` instead of `bg-slate-200` to maintain token consistency.

> **Note**: AdminSidebar uses `next/link` - for Owner Console (which uses react-router-dom), replace with `import { Link } from 'react-router-dom'`.

### Definition of Done

- [ ] Sidebar + Topbar match SaaS template style
- [ ] Owner Console no longer uses internal hand-coded Sidebar
- [ ] PR includes Before/After Sidebar/Topbar screenshots

---

## PR3: Dashboard Component Library

### Objective

Modularize all dashboard cards with unified styling.

### New Components (in shared-ui)

```
packages/shared-ui/src/components/dashboard/
├── StatCard.tsx
├── SectionCard.tsx
├── TimelineList.tsx
├── SystemStatusList.tsx
└── ProgressTrack.tsx
```

### Component Specifications

#### StatCard.tsx
```tsx
type StatCardProps = {
  label: string;
  value: string;
  trend?: string;
  badge?: string;
};

export function StatCard({ label, value, trend, badge }: StatCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-card">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--text-secondary)] font-medium">{label}</span>
        {badge && (
          <span className="px-2 py-0.5 text-[11px] rounded-full bg-[var(--brand-50)] text-[var(--brand-700)]">
            {badge}
          </span>
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold">{value}</span>
        {trend && <span className="text-xs text-[var(--success-600)]">{trend}</span>}
      </div>
    </div>
  );
}
```

#### SectionCard.tsx
```tsx
type SectionCardProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
};

export function SectionCard({ title, subtitle, action, children }: SectionCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
      <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
        <div>
          <h2 className="text-sm font-semibold">{title}</h2>
          {subtitle && (
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">{subtitle}</p>
          )}
        </div>
        {action && <div className="text-xs">{action}</div>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}
```

#### TimelineList.tsx
```tsx
type TimelineItem = {
  id: string;  // Add unique id for proper React key
  title: string;
  desc: string;
  time: string;
};

export function TimelineList({ items }: { items: TimelineItem[] }) {
  return (
    <ul className="space-y-4 text-sm">
      {items.map((item) => (
        <li key={item.id} className="flex justify-between">
          <div>
            <div className="font-medium">{item.title}</div>
            <div className="text-xs text-[var(--text-secondary)]">{item.desc}</div>
          </div>
          <span className="text-xs text-[var(--text-secondary)]">{item.time}</span>
        </li>
      ))}
    </ul>
  );
}
```

#### SystemStatusList.tsx
```tsx
type StatusItem = {
  service: string;  // Used as unique key (assuming service names are unique)
  status: string;
  latency: string;
};

export function SystemStatusList({ items }: { items: StatusItem[] }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.service}
          className="flex items-center justify-between px-3 py-2 rounded-lg bg-[var(--surface-muted)]"
        >
          <div>
            <div className="text-xs font-medium">{item.service}</div>
            <div className="text-[11px] text-[var(--text-secondary)]">{item.latency}</div>
          </div>
          <span className="text-[11px] font-medium rounded-full px-2 py-0.5 bg-[var(--success-50)] text-[var(--success-600)]">
            {item.status}
          </span>
        </div>
      ))}
    </div>
  );
}
```

> **Note**: Use `item.service` as key (assuming unique). Use `text-[11px]` (Caption) instead of `text-[10px]`.

#### ProgressTrack.tsx
```tsx
type ProgressItem = {
  label: string;  // Used as unique key (assuming labels are unique)
  value: number; // 0-100
  hint?: string;
};

export function ProgressTrack({ items }: { items: ProgressItem[] }) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.label} className="space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-[var(--text-primary)]">
                {item.label}
              </span>
              {item.hint && (
                <span className="text-[11px] text-[var(--text-secondary)]">
                  {item.hint}
                </span>
              )}
            </div>
            <span className="text-xs font-medium text-[var(--text-secondary)]">
              {item.value}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-muted)]">
            <div
              className="h-full rounded-full bg-[var(--brand-500)] transition-all"
              style={{ width: `${item.value}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Definition of Done

- [ ] Owner Console Dashboard no longer uses hand-coded divs
- [ ] All stat cards have unified styling
- [ ] All list cards have unified styling
- [ ] PR includes 2 screenshots: new cards vs old cards
- [ ] Storybook stories created for all new components

---

## PR4: Owner Console Dashboard Rewrite

### Objective

Rebuild the dashboard page to achieve professional SaaS dashboard quality.

### New Dashboard Structure

```tsx
"use client";

import {
  StatCard,
  SectionCard,
  TimelineList,
  SystemStatusList,
  ProgressTrack,
} from "@morningai/shared-ui";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Total Tenants" value="12" trend="+2 this month" />
        <StatCard label="Active Agents" value="45" badge="Cross-tenant" />
        <StatCard label="Monthly Cost" value="$1,234" />
        <StatCard label="System Health" value="98.5%" />
      </div>

      {/* Main Content */}
      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard
          title="Platform Progress"
          subtitle="Track core development tasks"
        >
          <ProgressTrack
            items={[
              { label: "Agent Deployment", value: 85, hint: "Core workflow integrated with Orchestrator" },
              { label: "Data Integration", value: 60, hint: "RLS Phase 3 complete, reports in progress" },
              { label: "Security Audit", value: 45, hint: "2FA/TOTP live, RLS testing ongoing" },
              { label: "Performance Optimization", value: 30, hint: "LangGraph canary, Redis Checkpointer tuning" },
            ]}
          />
        </SectionCard>

        <SectionCard
          title="Recent Activity"
          subtitle="Latest platform events"
        >
          <TimelineList
            items={[
              { title: "New Tenant Registered", desc: "Acme Corp", time: "5 min ago" },
              { title: "Agent Updated", desc: "FAQ-Agent v1.3", time: "30 min ago" },
            ]}
          />
        </SectionCard>

        <SectionCard
          title="System Status"
          subtitle="Service health overview"
        >
          <SystemStatusList
            items={[
              { service: "API Backend", status: "Healthy", latency: "220ms" },
              { service: "Database", status: "Healthy", latency: "18ms" },
              { service: "Redis", status: "Healthy", latency: "4ms" },
            ]}
          />
        </SectionCard>
      </div>
    </div>
  );
}
```

### Definition of Done

- [ ] New Dashboard visually matches professional SaaS template
- [ ] No API logic changes, no backend impact
- [ ] Before/After video or screenshots provided
- [ ] Lighthouse Rating >= 90 (desktop)

---

## Common Guidelines for All PRs

### Must Follow

- **Only use shared-ui components** (no new custom Button/Card)
- **No hardcoded CSS tokens**
- **No API logic changes**
- **All UI changes require Before/After screenshots**
- **Storybook stories required for new components**

### Prohibited

- Do not bring Apple UI components to Owner Console
- Do not mix old index.css with new tokens
- No hardcoded color values (`#xxxxxx`)

---

## Visual Style Reference: iotask

The target visual style is based on the iotask web UI kit:

- **Background**: Clean white (#ffffff) with muted surface (#f8fafc)
- **Shadows**: Soft card shadows (`0 18px 45px rgba(15, 23, 42, 0.08)`)
- **Colors**: Neutral slate grays + blue primary (#3b82f6)
- **Radius**: Larger card radius (12px / 16px / 24px)
- **Typography**: 
  - H1: 20px / 600
  - H2: 16px / 600
  - H3: 14px / 600
  - Body: 14-15px / normal
  - Label: 12px / 500
  - Caption: 11px / 400
- **Information Density**: Higher density, closer to SaaS Dashboard standards

---

## Final Deliverables

After completing all 4 PRs:

1. **New Admin Layout** (AdminShell) - Unified Sidebar + Topbar
2. **New Dashboard** - Page + Components
3. **Consistent Design Tokens** - Aligned with Tenant Dashboard
4. **Full shared-ui Integration** - Maintainable and extensible
5. **Professional SaaS UI** - 90-95% match to iotask reference

---

## Related Resources

- **UI/UX Architecture Report**: `docs/UI_UX_ARCHITECTURE_REPORT.md` (to be created)
- **Design Tokens**: `packages/shared-ui/src/tokens.json`
- **Shared UI Components**: `packages/shared-ui/src/components/ui/`
- **Recent PRs**: #1796, #1801, #1802 (iotask design system upgrades)

---

*Specification Version: 1.0*
*Created: December 3, 2025*
*Author: Devin AI (CTO Role)*
