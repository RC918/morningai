# Documentation Migration Records

This directory contains records of documentation migrations performed as part of Epic #2374 (Technical Debt Optimization).

## PR7 Migration (2025-12-16)

**PR**: #2587  
**Issue**: #2382  
**Scope**: Move 116 report files from root directory to structured `docs/` hierarchy

### Path Mapping

The complete old-to-new path mapping is available in CSV format:

- [PR7_PATH_MAPPING.csv](PR7_PATH_MAPPING.csv) - 116 file moves with categories

### Categories

| Category | Count | New Location |
|----------|-------|--------------|
| Analysis | 17 | `docs/reports/analysis/` |
| Calibration | 3 | `docs/reports/calibration/` |
| Coverage | 13 | `docs/reports/coverage/` |
| Infrastructure | 3 | `docs/reports/infrastructure/` |
| Ops | 5 | `docs/reports/ops/` |
| Phase | 21 | `docs/reports/phase/` |
| Planning | 7 | `docs/reports/planning/` |
| PR Reviews | 13 | `docs/reports/pr-reviews/` |
| Security | 9 | `docs/reports/security/` |
| UI/UX | 8 | `docs/reports/uiux/` |
| Validation | 9 | `docs/reports/validation/` |
| Guides | 4 | `docs/guides/` |
| Releases | 2 | `docs/releases/` |
| Runbooks | 2 | `docs/runbooks/` |

### Stub Files

The following stub files were created for backward compatibility:

| Stub Location | Points To | Removal Date |
|---------------|-----------|--------------|
| `docs/reports/analysis/MORNINGAI_深度解析報告_2025-11-20.md` | `MorningAI_Deep_Analysis_Report_zhTW_2025-11-20.md` | 2026-03-16 |

### Usage

To find the new location of a moved file:

```bash
# Search by old filename
grep "OLD_FILENAME" docs/migration/PR7_PATH_MAPPING.csv
```

Or use the CSV in your preferred spreadsheet application for filtering and searching.
