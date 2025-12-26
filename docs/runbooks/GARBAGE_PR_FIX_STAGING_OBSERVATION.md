# Garbage PR Fix - Staging Observation Runbook

Issue: #3047 - Staging observation plan for garbage PR fix
Related PR: #3040 - fix(webhooks): prevent garbage PR self-trigger loop

## Overview

This runbook guides the staging observation period for the garbage PR fix deployed in PR #3040. The fix introduces two layers of protection against self-trigger loops:

1. **Fix 1**: UNKNOWN events are rejected as not actionable in `is_actionable()`
2. **Fix 2**: `should_skip_orchestrator_pr_event()` now checks PR events AND UNKNOWN events for orchestrator branch/label patterns

## Observation Timeline

| Day | Activity | Focus |
|-----|----------|-------|
| 1-3 | Active monitoring | Check logs daily, verify no garbage PRs |
| 4-7 | Passive monitoring | Check logs every 2 days |
| 8 | Review results | Decide on production deployment |

## Log Queries

### Sentry / Render Logs

Search for these log patterns to monitor the fix behavior:

#### UNKNOWN Events Skipped
```
operation:unknown_event_skip
```

Fields captured:
- `event_id`: Unique webhook delivery ID
- `repo`: Repository in owner/repo format
- `event_type`: Always "unknown"
- `github_event`: Original GitHub event type (e.g., "check_suite", "check_run", "status")
- `github_action`: GitHub action (e.g., "completed", "created")
- `head_branch`: Branch name if available (for CI events)
- `actor`: GitHub username or bot name
- `reason`: "unknown_event_type_not_actionable"

#### Orchestrator Events Skipped (Branch Match)
```
operation:orchestrator_event_skip reason:orchestrator_branch_prefix
```

Fields captured:
- `event_id`: Unique webhook delivery ID
- `repo`: Repository in owner/repo format
- `resource_id`: PR number if available
- `head_ref`: Branch name (should start with "orchestrator/")
- `event_type`: Normalized event type
- `github_event`: Original GitHub event type
- `github_action`: GitHub action
- `actor`: GitHub username or bot name

#### Orchestrator Events Skipped (Label Match)
```
operation:orchestrator_event_skip reason:orchestrator_label_match
```

Fields captured:
- Same as branch match, plus:
- `matched_labels`: Labels that triggered the skip (e.g., ["orchestrator-docs"])

## Success Criteria

The observation period is successful if:

1. **Zero garbage PRs created** - No PRs with malformed titles like "docs: Add githubunknown-docs-add-githubu"
2. **No legitimate events incorrectly rejected** - Verify that real PR events from non-orchestrator branches are still processed
3. **UNKNOWN event frequency documented** - Record what types of UNKNOWN events are being received

## Metrics to Track

Create a simple tracking table during observation:

| Date | UNKNOWN Events | Branch Skips | Label Skips | Garbage PRs | Notes |
|------|----------------|--------------|-------------|-------------|-------|
| Day 1 | | | | | |
| Day 2 | | | | | |
| ... | | | | | |

## Verification Steps

### Daily Check (Days 1-3)

1. **Check for garbage PRs**:
   - Go to https://github.com/RC918/morningai/pulls
   - Search for PRs with "githubunknown" in title
   - Expected: Zero results

2. **Check UNKNOWN event logs**:
   - Search Render/Sentry logs for `operation:unknown_event_skip`
   - Record count and common `github_event` types
   - Expected: Mostly "check_suite", "check_run", "status" events

3. **Check orchestrator skip logs**:
   - Search for `operation:orchestrator_event_skip`
   - Verify `head_ref` starts with "orchestrator/"
   - Expected: Events from orchestrator-generated PRs

4. **Verify legitimate events processed**:
   - Create a test PR from a feature branch
   - Verify it triggers task creation (check worker logs)
   - Expected: PR events from non-orchestrator branches are processed

### Every-2-Days Check (Days 4-7)

1. Repeat garbage PR check
2. Spot-check UNKNOWN event logs for anomalies
3. Verify no user complaints about missed events

### Final Review (Day 8)

1. Compile metrics from tracking table
2. Review any anomalies or edge cases
3. Decision: Deploy to production or extend observation

## Rollback Plan

If issues are discovered during observation:

1. **Immediate**: Revert PR #3040 on staging
   ```bash
   git revert <commit-sha>
   git push origin main
   ```

2. **Investigate**: Check logs for the specific issue
3. **Fix**: Create a new PR with the fix
4. **Re-observe**: Restart observation period

## Known Limitations

1. **UNKNOWN events are always rejected**: If GitHub adds new event types that should trigger workflows, they will be filtered until we add them to `GITHUB_EVENT_MAP`

2. **First branch in array is used**: For status events with multiple branches, only the first branch is checked for orchestrator prefix

3. **C901 complexity**: The `is_actionable()` function has high complexity (tracked in #3043)

## Post-Observation Actions

After successful observation:

1. Deploy to production
2. Close #3047
3. Update #3044 with documented UNKNOWN event types
4. Consider implementing #3045 (config control) if needed

## Contact

For questions or issues during observation:
- Create an issue in the repository
- Tag @RC918 for urgent matters
