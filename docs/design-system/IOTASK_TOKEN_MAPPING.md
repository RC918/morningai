# iotask Design Token Mapping

This document maps the iotask web ui kit design tokens to the MorningAI design system.

## Color Palette Mapping

### Primary Colors

| iotask Token | Hex Value | MorningAI Mapping | Notes |
|--------------|-----------|-------------------|-------|
| Primary | #4D7CFE | `color.primary.500` | Main brand color - vibrant blue |
| Primary 15% | #4D7CFE26 | `color.primary.100` | Light variant for backgrounds |

### Secondary/Neutral Colors

| iotask Token | Hex Value | MorningAI Mapping | Notes |
|--------------|-----------|-------------------|-------|
| #98A9BC | #98A9BC | `color.neutral.400` | Secondary text, icons |
| #778CA2 | #778CA2 | `color.neutral.500` | Muted text |
| #E8ECEF | #E8ECEF | `color.neutral.200` | Borders, dividers |
| #F2F4F6 | #F2F4F6 | `color.neutral.100` | Light backgrounds |
| #F8FAFB | #F8FAFB | `color.neutral.50` | Card backgrounds |
| #252631 | #252631 | `color.neutral.900` | Dark text, headers |

### Accent Colors

| iotask Token | Hex Value | MorningAI Mapping | Notes |
|--------------|-----------|-------------------|-------|
| Pink | #FE4D97 | `color.accent.pink.500` | Highlights, badges |
| Pink 15% | #FE4D9726 | `color.accent.pink.100` | Light pink backgrounds |
| Green | #6DD230 | `color.semantic.success.500` | Success states |
| Green 15% | #6DD23026 | `color.semantic.success.100` | Success backgrounds |
| Cyan | #2CE5F6 | `color.accent.cyan.500` | Info highlights |
| Cyan 15% | #2CE5F626 | `color.accent.cyan.100` | Info backgrounds |
| Orange | #FFAB2B | `color.semantic.warning.500` | Warnings, alerts |
| Orange 15% | #FFAB2B26 | `color.semantic.warning.100` | Warning backgrounds |

### Shadow Colors

| iotask Token | Hex Value | MorningAI Mapping | Notes |
|--------------|-----------|-------------------|-------|
| Shadow 5px | #5B5B5B (5px blur) | `shadow.sm` | Subtle elevation |
| Shadow 10px | #5B5B5B (10px blur) | `shadow.md` | Medium elevation |
| Shadow 20px | #5B5B5B (20px blur) | `shadow.lg` | High elevation |

## Typography Mapping

### Font Family

| iotask Token | Value | MorningAI Mapping | Notes |
|--------------|-------|-------------------|-------|
| Primary Font | Public Sans | `font.family.primary` | Main UI font |
| Icon Font | Material Symbols Outlined | `font.family.icons` | Icon font |

### Font Sizes (iotask uses Public Sans)

| iotask Token | Size | MorningAI Mapping | Notes |
|--------------|------|-------------------|-------|
| h1 | 24px | `font.size.heading1` | Page titles |
| h2 | 22px | `font.size.heading2` | Section headers |
| h3 | 20px | `font.size.heading3` | Card titles |
| h4 | 18px | `font.size.heading4` | Subsection headers |
| h5 | 16px | `font.size.body` | Body text emphasis |
| Text label 14px | 14px | `font.size.small` | Labels, captions |
| Text label 12px | 12px | `font.size.caption` | Small labels |

### Icon Sizes

| iotask Token | Size | MorningAI Mapping | Notes |
|--------------|------|-------------------|-------|
| Icon 14px | 14px | `icon.size.xs` | Inline icons |
| Icon 16px | 16px | `icon.size.sm` | Small icons |
| Icon 18px | 18px | `icon.size.md` | Medium icons |
| Icon 20px | 20px | `icon.size.lg` | Large icons |
| Icon 22px | 22px | `icon.size.xl` | Extra large icons |
| Icon 24px | 24px | `icon.size.2xl` | Header icons |

## Component Style Mapping

### Buttons

| iotask Style | MorningAI Component | Notes |
|--------------|---------------------|-------|
| Primary | `Button variant="primary"` | Blue filled button |
| Primary hover | `Button variant="primary" :hover` | Darker blue on hover |
| Outline | `Button variant="outline"` | Border only |
| Primary with icon | `Button variant="primary" icon={...}` | Icon + text |
| Primary with badge | `Button variant="primary" badge={5}` | With notification count |

### Cards

| iotask Style | MorningAI Component | Notes |
|--------------|---------------------|-------|
| Task card | `Card variant="task"` | White bg, subtle shadow |
| Stats card | `Card variant="stats"` | With mini chart |
| Project card | `Card variant="project"` | With progress bar |

### Navigation

| iotask Style | MorningAI Component | Notes |
|--------------|---------------------|-------|
| Sidebar nav item | `NavItem` | Icon + text, active state |
| Sidebar section | `NavSection` | Collapsible group |

## Spacing Scale

iotask uses consistent spacing that maps to our existing scale:

| Usage | iotask Value | MorningAI Token |
|-------|--------------|-----------------|
| Tight | 4px | `space.xs` |
| Small | 8px | `space.sm` |
| Medium | 16px | `space.md` |
| Large | 24px | `space.lg` |
| Extra Large | 32px | `space.xl` |

## Border Radius

| iotask Style | Value | MorningAI Token |
|--------------|-------|-----------------|
| Small | 4px | `radius.sm` |
| Medium | 8px | `radius.md` |
| Large | 12px | `radius.lg` |
| Full | 9999px | `radius.full` |

## Implementation Notes

1. **Gradual Migration**: Update tokens first, then components will automatically inherit new styles
2. **Backward Compatibility**: Keep existing semantic color names (success, error, warning, info)
3. **Scoped Changes**: All changes scoped to owner-console to avoid affecting tenant-dashboard
4. **Storybook Sync**: Update stories after each component change
