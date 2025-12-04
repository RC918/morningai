# MorningAI UI/UX Standard

This document serves as the unified entry point for all UI/UX standards, guidelines, and resources in the MorningAI project.

## Quick Links

| Resource | Description |
|----------|-------------|
| [Design System Quickstart](../DESIGN_SYSTEM_QUICKSTART.md) | 2-minute guide to get started |
| [Design System Enforcement](../DESIGN_SYSTEM_ENFORCEMENT.md) | CI/CD enforcement rules |
| [UI/UX Quickstart](../UI_UX_QUICKSTART.md) | UI/UX development guide |
| [UI/UX Cheatsheet](../UI_UX_CHEATSHEET.md) | Quick reference for common patterns |

## Core Principles

### 1. Use `@morningai/shared-ui` Components

All UI must be built using components from `@morningai/shared-ui`. Direct imports from third-party UI libraries are prohibited.

**Allowed imports:**
- `@morningai/shared-ui` (preferred)
- `lucide-react` (icons only)
- `recharts` (charts only)
- `date-fns` (date utilities only)

**Prohibited imports:**
- `@radix-ui/react-*`
- `@mui/*`
- `@headlessui/*`
- `@chakra-ui/*`

### 2. Use Semantic Design Tokens

Never use hardcoded Tailwind colors. Always use semantic tokens.

**Prohibited:**
```tsx
// Bad - hardcoded colors
<div className="bg-slate-100 text-gray-500 border-blue-500">
```

**Required:**
```tsx
// Good - semantic tokens
<div className="bg-[var(--surface)] text-[var(--text-primary)] border-[var(--primary)]">
```

**Semantic token mapping:**
| Purpose | Token | Example |
|---------|-------|---------|
| Error states | `error` | `text-error`, `bg-error` |
| Success states | `success` | `text-success`, `bg-success` |
| Warning states | `warning` | `text-warning`, `bg-warning` |
| Info states | `info` | `text-info`, `bg-info` |
| Primary actions | `primary` | `text-primary`, `bg-primary` |
| Neutral/gray | `neutral` | `text-neutral`, `bg-neutral` |

### 3. Use Standardized Spacing

Use consistent spacing values from the design system.

**Recommended spacing:**
- Section spacing: `space-y-8`
- Card padding: `p-5` or `p-6`
- Gap in flex/grid: `gap-4`, `gap-6`, `gap-8`
- Margins: `mt-4`, `mt-8`, `mb-4`, `mb-8`

### 4. Internationalization (i18n)

All user-visible strings must use the translation function.

**Prohibited:**
```tsx
// Bad - hardcoded string
<h1>Dashboard</h1>
```

**Required:**
```tsx
// Good - translated string
<h1>{t("dashboard.title")}</h1>
```

## Page Structure Standard

All pages should use the `PageScaffold` component to enforce consistent structure:

```tsx
<PageScaffold
  title={t("page.title")}
  subtitle={t("page.subtitle")}
  titleIcon={<Shield className="w-6 h-6" />}
  actions={
    <Button onClick={handleRefresh}>
      <Activity className="w-4 h-4 mr-2" />
      {t("common.refresh")}
    </Button>
  }
  banner={error && (
    <AppleErrorBanner
      title={t("common.error")}
      message={error}
      onRetry={handleRetry}
    />
  )}
  kpis={
    <>
      <StatCard label={t("stats.total")} value="100" icon={<Users />} />
      <StatCard label={t("stats.active")} value="85" icon={<Activity />} variant="green" />
    </>
  }
>
  <SectionCard title={t("section.title")}>
    ...content...
  </SectionCard>
</PageScaffold>
```

### PageScaffold Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `ReactNode` | Yes | Page title (rendered as h1) |
| `subtitle` | `ReactNode` | No | Subtitle below the title |
| `titleIcon` | `ReactNode` | No | Icon displayed before the title |
| `actions` | `ReactNode` | No | Action buttons aligned to the right |
| `banner` | `ReactNode` | No | Banner/alert content below header |
| `kpis` | `ReactNode` | No | KPI row content (StatCard components) |
| `className` | `string` | No | Custom class for root container |
| `headerClassName` | `string` | No | Custom class for header section |
| `kpiClassName` | `string` | No | Custom class for KPI section |
| `bodyClassName` | `string` | No | Custom class for content section |

### Migration Example

**Before (manual structure):**
```tsx
<div className="space-y-8">
  <div className="flex items-center justify-between">
    <h1>{t("governance.title")}</h1>
    <Button>Refresh</Button>
  </div>
  {error && <ErrorBanner error={error} />}
  <div className="grid grid-cols-4 gap-5">
    <StatCard ... />
  </div>
  <Tabs>...</Tabs>
</div>
```

**After (using PageScaffold):**
```tsx
<PageScaffold
  title={t("governance.title")}
  actions={<Button>Refresh</Button>}
  banner={error && <ErrorBanner error={error} />}
  kpis={<><StatCard ... /></>}
>
  <Tabs>...</Tabs>
</PageScaffold>
```

## Section Structure Standard

Use `SectionTemplate` to create consistent content sections within pages. It works inside `PageScaffold` to create a hierarchical page layout.

### When to Use SectionTemplate vs SectionCard

`SectionTemplate` and `SectionCard` serve different purposes:

- **SectionTemplate** is a structural/semantic component that provides consistent section layout with title, description, and actions. Use it when you need a semantic `<section>` element with proper heading hierarchy.
- **SectionCard** is a visual component that provides card styling (border, shadow, background). Use it directly when you only need the card visual treatment.
- **SectionTemplate with `variant="card"`** combines both: semantic structure that delegates visual rendering to SectionCard. Use this when you want both semantic structure and card styling.

### SectionTemplate Usage

```tsx
// Plain section (default) - semantic section with h2 title
<SectionTemplate
  title={t("section.activeTenants")}
  description={t("section.activeTenants.description")}
  actions={<Button size="sm">View All</Button>}
>
  <TenantList tenants={activeTenants} />
</SectionTemplate>

// Card-based section - delegates to SectionCard
<SectionTemplate
  variant="card"
  title={t("section.systemStatus")}
  description={t("section.systemStatus.description")}
  actions={<Button size="sm">Refresh</Button>}
>
  <SystemStatusList items={statusItems} />
</SectionTemplate>
```

### SectionTemplate Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `string` | Yes | Section title (rendered as h2 for plain variant) |
| `description` | `ReactNode` | No | Description below the title (must be a string for `card` variant) |
| `actions` | `ReactNode` | No | Action buttons aligned to the right |
| `variant` | `"plain" \| "card"` | No | Section variant (default: "plain") |
| `className` | `string` | No | Custom class for section container |
| `headerClassName` | `string` | No | Custom class for header (plain variant only) |
| `bodyClassName` | `string` | No | Custom class for body/content section |

### Complete Page Example

```tsx
<PageScaffold
  title={t("tenantManagement.title")}
  subtitle={t("tenantManagement.subtitle")}
  titleIcon={<Users className="w-6 h-6" />}
  actions={<Button>Add Tenant</Button>}
  kpis={
    <>
      <StatCard label={t("stats.total")} value="12" />
      <StatCard label={t("stats.active")} value="10" variant="green" />
    </>
  }
>
  {/* Plain section for custom layouts */}
  <SectionTemplate
    title={t("section.activeTenants")}
    description={t("section.activeTenants.description")}
    actions={<Button variant="ghost" size="sm">View All</Button>}
  >
    <TenantList tenants={activeTenants} />
  </SectionTemplate>

  {/* Card section for visual grouping */}
  <SectionTemplate
    variant="card"
    title={t("section.pendingApprovals")}
    description={t("section.pendingApprovals.description")}
  >
    <ApprovalList items={pendingApprovals} />
  </SectionTemplate>
</PageScaffold>
```

## Available Components

### Layout Components
- `PageScaffold` - Standardized page layout with header, banner, KPIs, and content slots
- `SectionTemplate` - Standardized section layout with title, description, and actions (plain or card variant)
- `AdminShell` - Main application shell with sidebar and topbar
- `AdminSidebar` - Navigation sidebar
- `AdminTopbar` - Top navigation bar

### Dashboard Components
- `StatCard` - KPI/metric display card
- `SectionCard` - Content section container
- `ProgressTrack` - Progress indicator
- `SystemStatusList` - System status display
- `TimelineList` - Timeline/activity list

### UI Primitives
See the full list in [Storybook](https://storybook.gm365.me) or `packages/shared-ui/src/components/ui/`.

## CI Enforcement

The following CI checks enforce these standards:

| Check | Workflow | Blocking |
|-------|----------|----------|
| Shared-UI imports | `enforce-shared-ui.yml` | Yes (Stage 3) |
| Hardcoded colors | ESLint `no-hardcoded-colors` | Yes |
| i18n strings | `i18n-check-required.yml` | Yes |
| Design system audit | `design-system-audit.yml` | No (relaxed mode) |

## PR Checklist

Before submitting a PR with UI changes, verify:

- [ ] All UI components from `@morningai/shared-ui`
- [ ] No hardcoded colors (use semantic tokens)
- [ ] No hardcoded strings (use `t()` function)
- [ ] Consistent spacing (use design tokens)
- [ ] Screenshots attached for UI changes
- [ ] Storybook stories added for new components

## Design System Documentation

### Tokens & Systems
- [Color System](../UX/COLOR_SYSTEM.md)
- [Spacing System](../UX/SPACING_SYSTEM.md)
- [Typography System](../UX/TYPOGRAPHY_SYSTEM.md)
- [Shadow System](../UX/SHADOW_SYSTEM.md)

### Components
- [Design System Components](../UX/Design%20System/Components.md)
- [Design System Tokens](../UX/Design%20System/Tokens.md)
- [Design System Animation](../UX/Design%20System/Animation.md)
- [Design System Accessibility](../UX/Design%20System/Accessibility.md)

### Guides
- [Apple Button Migration](../UX/APPLE_BUTTON_MIGRATION_PLAN.md)
- [Apple Input Migration](../UX/APPLE_INPUT_MIGRATION_PLAN.md)
- [Typography Migration](../UX/TYPOGRAPHY_MIGRATION_GUIDE.md)

## Getting Help

- **Storybook**: https://storybook.gm365.me - Browse all available components
- **Quick Fix Guide**: [DESIGN_SYSTEM_QUICKSTART.md](../DESIGN_SYSTEM_QUICKSTART.md)
- **Emergency Override**: [EMERGENCY_OVERRIDE_RUNBOOK.md](../EMERGENCY_OVERRIDE_RUNBOOK.md)

## Related Issues

- [#1873](https://github.com/RC918/morningai/issues/1873) - This document
- [#1874](https://github.com/RC918/morningai/issues/1874) - PageScaffold component
- [#1875](https://github.com/RC918/morningai/issues/1875) - SectionTemplate component
- [#1876](https://github.com/RC918/morningai/issues/1876) - Spacing ESLint rule
- [#1877](https://github.com/RC918/morningai/issues/1877) - Extend no-hardcoded-colors to owner-console
