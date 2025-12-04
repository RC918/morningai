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

All pages should follow this structure:

```tsx
<AdminShell>
  <PageHeader>
    <Title>{t("page.title")}</Title>
    <Actions>...</Actions>
  </PageHeader>
  
  <KPIRow>
    <StatCard ... />
    <StatCard ... />
  </KPIRow>
  
  <ContentSection>
    <SectionCard title={t("section.title")}>
      ...content...
    </SectionCard>
  </ContentSection>
</AdminShell>
```

## Available Components

### Layout Components
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
