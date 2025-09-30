# Release v4.6.0 — Phase 4–6 Stable

## Highlights
- Test coverage raised to **25%** (from 12%)
- Functional/Integration/Performance verified; **100% success**, **88ms avg**
- Phase 4–6 APIs validated, Phase 8 health endpoints stable

## Security TODO
- JWT issuance & RBAC enforcement on sensitive endpoints
- Unified JSON error format (avoid HTML errors)

## Rollback
\`\`\`bash
git checkout v4.6.0   # this tag
# or rollback to previous stable (e.g., v4.5.0)
\`\`\`

## Artifacts
- CI workflow: `.github/workflows/post-deploy-health-assertions.yml`
- Manual report: `PHASE_4_6_MANUAL_VALIDATION.md`
