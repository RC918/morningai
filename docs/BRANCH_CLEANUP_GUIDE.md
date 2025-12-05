# Branch Cleanup Guide

This document explains why the repository accumulated 888+ branches despite having GitHub's "auto-delete head branches" setting enabled, and provides solutions for cleanup and prevention.

## Root Cause Analysis

### Why Branches Weren't Auto-Deleted

GitHub's "Automatically delete head branches" setting only triggers under specific conditions:

1. **Only on PR merge events**: The setting only deletes branches when a PR is merged (not closed without merge)
2. **Not retroactive**: Branches from PRs merged before the setting was enabled are not cleaned up
3. **Requires a PR**: Branches that never had a PR associated with them are never deleted

### Branch Breakdown (as of investigation)

| Category | Count | Description |
|----------|-------|-------------|
| `orchestrator/*` | 393 | FAQ Agent automation branches |
| `devin/*` | 392 | Devin integration task branches |
| Other (`chore/*`, `ci/*`, `hotfix/*`, etc.) | ~100 | Various feature/fix branches |
| **Total** | ~886 | |

### Why Each Category Accumulated

**orchestrator/* branches (393)**
- Created by the FAQ Agent automation in `graph.py`
- Each execution creates a new `orchestrator/{timestamp}-faq-update` branch
- Cleanup only runs when CI completes, but many branches are created without CI completion
- Root cause: Line 216 in `handoff/20250928/40_App/orchestrator/graph.py`

**devin/* branches (392)**
- Created by Devin for each task/PR
- Many are experimental branches that never had merged PRs
- Some had PRs that were closed without merge

**Other branches**
- Historical branches from before auto-delete was enabled
- Branches from PRs that were closed without merge
- Long-lived branches kept for CI/testing purposes

## Solutions

### 1. One-Time Cleanup Script

Use the Python cleanup script for a one-time cleanup:

```bash
# Preview what would be deleted (dry run)
python scripts/branch_cleanup.py --dry-run --days 60

# Delete orchestrator branches older than 30 days
python scripts/branch_cleanup.py --execute --pattern "orchestrator/*" --days 30

# Delete devin branches older than 90 days
python scripts/branch_cleanup.py --execute --pattern "devin/*" --days 90

# Delete all stale branches older than 60 days
python scripts/branch_cleanup.py --execute --days 60
```

### 2. Automated Weekly Cleanup (GitHub Actions)

A GitHub Actions workflow runs weekly to identify stale branches:

- **Schedule**: Every Sunday at 00:00 UTC
- **Default mode**: Dry run (reports only, no deletion)
- **Manual trigger**: Can be run manually with custom parameters

To run the cleanup workflow:
1. Go to Actions > Branch Cleanup
2. Click "Run workflow"
3. Set `dry_run` to `false` to actually delete branches
4. Optionally set a pattern (e.g., `orchestrator/*`) and age threshold

### 3. Orchestrator Cleanup Function

A new function `cleanup_stale_orchestrator_branches()` has been added to `github_api.py`:

```python
from tools.github_api import cleanup_stale_orchestrator_branches

# Dry run - see what would be deleted
cleanup_stale_orchestrator_branches(max_age_days=7, dry_run=True)

# Actually delete stale branches
cleanup_stale_orchestrator_branches(max_age_days=7, dry_run=False)
```

## Prevention Recommendations

### Short-term

1. **Run the one-time cleanup** to reduce the current 888 branches
2. **Enable the weekly cleanup workflow** with `dry_run=false` after reviewing the first few reports

### Long-term

1. **Improve orchestrator cleanup logic**: The FAQ Agent should always clean up its branches, not just when CI completes
2. **Consider using forks**: For automation that creates many branches, consider using a fork instead of the main repository
3. **Set shorter retention**: Configure the cleanup to delete `orchestrator/*` branches after 7 days instead of 60
4. **Monitor branch count**: Add a metric/alert for when branch count exceeds a threshold

## Safe Cleanup Criteria

The cleanup scripts use these criteria to determine if a branch is safe to delete:

1. **Not protected**: Not `main`, `master`, `develop`, or matching `release/*`, `gh-pages*`
2. **No open PRs**: The branch doesn't have any open pull requests
3. **Age threshold**: Last commit is older than the specified number of days
4. **Pattern match**: Optionally, only delete branches matching a specific pattern

## Commands Reference

```bash
# Fetch and prune deleted branches
git fetch --all --prune

# Count total remote branches
git branch -r | grep -v HEAD | wc -l

# Count branches by pattern
git branch -r | grep "orchestrator/" | wc -l
git branch -r | grep "devin/" | wc -l

# List oldest branches
git for-each-ref --sort=committerdate --format='%(refname:short) %(committerdate:short)' refs/remotes/origin | head -30

# Delete a specific remote branch
git push origin --delete branch-name
```
