# Commit and PR Conventions

This document describes the commit message and PR title conventions for the MorningAI project.

## PR Title Format

All PR titles must follow the conventional commit format:

```
<type>: <description>
```

Or with optional scope:

```
<type>(<scope>): <description>
```

### Allowed Types

| Type | Description | Example |
|------|-------------|---------|
| `feat:` | New feature | `feat: add user dashboard` |
| `fix:` | Bug fix | `fix: resolve login timeout` |
| `refactor:` | Code refactoring (no behavior change) | `refactor: extract auth service` |
| `docs:` | Documentation updates | `docs: update API documentation` |
| `test:` | Test-related changes | `test: add unit tests for auth` |
| `ci:` | CI/CD changes | `ci: update GitHub Actions workflow` |
| `bot:` | Automated/bot PRs | `bot: update dependencies` |
| `deps:` | Dependency updates | `deps: bump react to 19.0.0` |
| `chore:` | Miscellaneous maintenance | `chore: update CI config` |
| `style:` | Code style changes (no logic change) | `style: format with prettier` |
| `perf:` | Performance improvements | `perf: optimize database queries` |

### Examples

Good PR titles:
- `feat: add user authentication flow`
- `fix: resolve race condition in data fetching`
- `refactor: extract common validation logic`
- `docs: update deployment guide`
- `test: add integration tests for payment module`
- `ci: add PR title validation workflow`
- `deps: upgrade TypeScript to 5.3`
- `chore: configure ESLint rules`
- `style: apply prettier formatting`
- `perf: optimize database query performance`
- `feat(auth): implement OAuth2 login`

Bad PR titles:
- `Update code` (missing type prefix)
- `Fixed bug` (missing type prefix, past tense)
- `WIP: new feature` (WIP is not an allowed type)
- `FEAT: add dashboard` (type must be lowercase)

## CI Enforcement

PR titles are automatically validated by the `pr-title-check.yml` workflow. If your PR title does not follow the format, the CI check will fail and you will receive a comment explaining how to fix it.

To fix a failed check, simply edit your PR title to follow the correct format. The CI will automatically re-run.

## Human-only Changelog Filtering

The standardized PR title format enables easy filtering of human contributions vs bot PRs:

```bash
# Exclude bot PRs from changelog
git log --oneline --no-merges | grep -v "^.*bot:" | grep -v "^.*deps:"

# Only show feature and fix PRs
git log --oneline --grep="^feat:\|^fix:" main..HEAD

# Generate human-readable changelog
git log --oneline --no-merges | grep -E "^[a-f0-9]+ (feat|fix|refactor|perf):" 
```

## Future Considerations

### Phase 2: Commit Message Enforcement

If the team decides to enforce commit message conventions at the commit level (not just PR titles), we can add:

1. `commitlint` with `husky` commit-msg hook
2. Force every commit to follow conventional commit format

This would require all contributors to set up local hooks, so it's recommended to start with PR title enforcement first.

## Related Documentation

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - General contribution guidelines
- [GitHub Actions Workflows](../../.github/workflows/) - CI/CD configuration
