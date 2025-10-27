# Dependency Management Strategy

## Overview

This monorepo uses **pnpm workspaces** with **Turborepo** for efficient dependency management and build orchestration.

## Architecture

```
morningai/
├── package.json                              # Root package.json with pnpm overrides
├── pnpm-workspace.yaml                       # Workspace configuration
├── turbo.json                                # Turborepo configuration
├── handoff/20250928/40_App/
│   ├── frontend-dashboard/package.json       # Tenant Dashboard dependencies
│   └── owner-console/package.json            # Owner Console dependencies
└── frontend-dashboard-deploy/package.json    # Storybook deployment dependencies
```

## Dependency Unification

### Current Status (P2 Completed)

✅ **Audit Completed**: 230 package.json files analyzed
✅ **Version Conflicts Identified**: 13 dependencies with version conflicts
✅ **pnpm Overrides Configured**: Unified versions for critical dependencies

### Key Statistics

- **Total Dependencies**: 63 unique dependencies
- **Total DevDependencies**: 32 unique devDependencies
- **Shared Dependencies**: 59/63 (94%) are identical across applications
- **Version Conflicts Resolved**: 13 dependencies now use unified versions

## pnpm Overrides

The root `package.json` uses pnpm overrides to enforce consistent versions across all workspaces:

```json
{
  "pnpm": {
    "overrides": {
      "react": "^19.1.0",
      "react-dom": "^19.1.0",
      "@types/react": "^19.1.2",
      "@types/react-dom": "^19.1.2",
      "vite": "^6.3.5",
      "typescript": "5.9.3",
      "eslint": "^9.25.0",
      "@radix-ui/react-slot": "^1.2.2",
      "@radix-ui/react-collapsible": "^1.1.10",
      "@radix-ui/react-dialog": "^1.1.13",
      "@radix-ui/react-toggle": "^1.1.8",
      "tailwindcss": "^4.1.7",
      "zod": "^3.24.4",
      "@storybook/addon-a11y": "^8.6.14",
      "@storybook/addon-essentials": "^8.6.14",
      "@storybook/addon-interactions": "^8.6.14",
      "@storybook/addon-links": "^8.6.14",
      "@storybook/react": "^8.6.14",
      "@storybook/react-vite": "^8.6.14",
      "@storybook/test": "^8.6.14",
      "storybook": "^8.6.14"
    }
  }
}
```

### Why pnpm Overrides?

1. **Centralized Version Control**: All version conflicts are resolved in one place
2. **Automatic Enforcement**: pnpm automatically applies overrides to all workspaces
3. **No Code Changes Required**: Existing package.json files remain unchanged
4. **Easy Maintenance**: Update versions in one place, applies everywhere

## Application-Specific Dependencies

Some dependencies are intentionally kept application-specific:

### Frontend Dashboard Only
- `@supabase/supabase-js`: Supabase integration
- `web-vitals`: Performance monitoring

### Owner Console Only
- Currently shares all dependencies with Frontend Dashboard

### Frontend Dashboard Deploy Only
- `@chromatic-com/storybook`: Chromatic visual testing
- `@vitest/browser`, `@vitest/coverage-v8`, `vitest`: Vitest testing
- `playwright`: E2E testing

## Workspace Configuration

### pnpm-workspace.yaml

```yaml
packages:
  - 'handoff/20250928/40_App/frontend-dashboard'
  - 'handoff/20250928/40_App/owner-console'
  - 'frontend-dashboard-deploy'
```

### Benefits

1. **Shared node_modules**: pnpm creates a single node_modules with symlinks, saving ~70% disk space
2. **Faster Installs**: Dependencies are installed once and reused across workspaces
3. **Consistent Versions**: pnpm overrides ensure all workspaces use the same versions
4. **Parallel Builds**: Turborepo can build multiple workspaces in parallel

## Common Commands

### Install Dependencies

```bash
# Install all dependencies
pnpm install

# Install for specific workspace
pnpm --filter frontend-dashboard install
```

### Build

```bash
# Build all workspaces
pnpm build

# Build specific workspace
pnpm build:dashboard
pnpm build:owner
```

### Development

```bash
# Run dev server for dashboard
pnpm dev

# Run dev server for owner console
pnpm dev:owner
```

### Lint & Type Check

```bash
# Lint all workspaces
pnpm lint

# Type check all workspaces
pnpm typecheck
```

### Clean

```bash
# Clean all node_modules and build artifacts
pnpm clean

# Clean cache
pnpm clean:cache
```

## Adding New Dependencies

### For All Workspaces

If a dependency should be used by all workspaces, add it to the root `package.json`:

```bash
pnpm add -w <package-name>
```

### For Specific Workspace

```bash
pnpm --filter <workspace-name> add <package-name>
```

### Example

```bash
# Add lodash to frontend-dashboard only
pnpm --filter frontend-dashboard add lodash

# Add typescript to root (shared by all)
pnpm add -w -D typescript
```

## Version Updates

### Update All Dependencies

```bash
# Check for outdated dependencies
pnpm outdated

# Update all dependencies
pnpm update -r

# Update specific dependency
pnpm update <package-name> -r
```

### Update pnpm Overrides

When updating versions in `pnpm.overrides`, run:

```bash
pnpm install
```

This will apply the new versions across all workspaces.

## Troubleshooting

### Version Conflicts

If you encounter version conflicts:

1. Check `pnpm-lock.yaml` for the conflicting versions
2. Add the dependency to `pnpm.overrides` in root `package.json`
3. Run `pnpm install` to apply the override

### Phantom Dependencies

If a workspace imports a package not listed in its `package.json`:

1. Add the package explicitly to the workspace's `package.json`
2. Run `pnpm install`

### Cache Issues

If you encounter strange build issues:

```bash
# Clean cache
pnpm clean:cache

# Reinstall dependencies
pnpm install
```

## Best Practices

1. **Always use pnpm**: Never use npm or yarn in this monorepo
2. **Keep versions in sync**: Use pnpm overrides for shared dependencies
3. **Minimize duplication**: If multiple workspaces need the same dependency, add it to root
4. **Document changes**: Update this file when adding new dependencies or changing strategy
5. **Test after updates**: Run `pnpm build` and `pnpm test` after updating dependencies

## Future Improvements (P3)

### Planned for Phase 10

1. **Shared Component Library**: Create `@morningai/shared-ui` package
   - Extract common components (Button, Modal, etc.)
   - Reduce code duplication by ~30%

2. **Dependency Deduplication**: Further reduce node_modules size
   - Target: 50% reduction in total dependencies
   - Use `pnpm dedupe` to consolidate versions

3. **Automated Dependency Updates**: Set up Renovate or Dependabot
   - Automatic PR creation for dependency updates
   - Automated testing before merge

## References

- [pnpm Workspaces Documentation](https://pnpm.io/workspaces)
- [Turborepo Documentation](https://turbo.build/repo/docs)
- [pnpm Overrides Documentation](https://pnpm.io/package_json#pnpmoverrides)

## Audit Reports

- `DEPENDENCY_AUDIT_REPORT.json`: Full audit of all 230 package.json files
- `PACKAGE_COMPARISON_REPORT.json`: Detailed comparison of main application dependencies

---

**Last Updated**: 2025-10-23
**Phase**: P2 - Dependency Version Unification (Completed)
