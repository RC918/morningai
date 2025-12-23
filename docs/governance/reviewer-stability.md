# MorningAI Reviewer Stability Governance

This document defines the governance framework for monitoring and ensuring the stability of the MorningAI Reviewer Agent before progressing to EPIC C (Flow Controller).

## Overview

The Reviewer Stability Scorecard is a key governance tool that measures the health and reliability of the MorningAI code review system. It provides quantitative metrics to inform decisions about:

- Enabling production flags
- Progressing to EPIC C
- Future P6 (Checks API/status gate) integration

## Key Performance Indicators (KPIs)

| Metric | Description | Target |
|--------|-------------|--------|
| Review Coverage | % of PRs with at least one MorningAI review | >= 50% for EXCELLENT |
| Duplicate Rate | % of commits reviewed multiple times | 0% (no duplicates) |
| Review Latency | Time from PR creation to MorningAI review | < 5 minutes average |
| Health Score | Composite score (lower is better) | 0 for EXCELLENT |

## Health Status Definitions

| Status | Criteria | Action |
|--------|----------|--------|
| EXCELLENT | Score = 0, no duplicates, coverage >= 50% | Ready for EPIC C progression |
| GOOD | Score < 50 | Continue monitoring |
| FAIR | Score < 100 | Investigate root causes |
| NEEDS ATTENTION | Score >= 100 | Immediate action required |

## Health Score Calculation

The health score is calculated as follows:

```
health_score = (duplicate_reviews * 50) + slow_review_penalty - coverage_percent
health_score = max(0, health_score)
```

Where:
- `duplicate_reviews * 50`: Heavy penalty for each duplicate review
- `slow_review_penalty`: +10 points if average latency > 5 minutes
- `coverage_percent`: Reward for higher coverage (subtracted from score)

Note: The score is clamped at 0 (negative values become 0). High coverage alone cannot produce a negative score.

## Monitoring Schedule

- **Frequency**: Daily at 00:00 UTC
- **Analysis Period**: Rolling 7-day window
- **Automation**: GitHub Actions workflow `reviewer-scorecard.yml`
- **Tracking**: Issue #2859 (daily reports appended as comments)

## Notification Policy

Notifications are sent only on **regression** to minimize noise:

1. **Status Downgrade**: When health status worsens (e.g., GOOD → FAIR)
2. **Execution Failure**: When the scorecard workflow fails
3. **Manual Override**: When `force_notify` is enabled in workflow dispatch

Notifications are delivered via GitHub @mention in the tracking issue.

## EPIC C Progression Criteria

Before progressing to EPIC C (Flow Controller), the following criteria must be met:

1. **Stability**: EXCELLENT or GOOD status for 7 consecutive days
2. **Coverage**: >= 50% review coverage maintained
3. **Duplicates**: Zero duplicate reviews for 7 consecutive days
4. **Latency**: Average review latency < 5 minutes

## Artifacts and Data Retention

- **JSON Reports**: Stored as GitHub Actions artifacts (90-day retention)
- **Markdown Reports**: Appended to tracking issue #2859
- **Status Cache**: Used for regression detection between runs

## Related Resources

- [Scorecard Tool](../../tools/reviewer_stability_scorecard.py)
- [Tool Documentation](../../tools/README.md)
- [Tracking Issue](https://github.com/RC918/morningai/issues/2859)
- [Workflow](../../.github/workflows/reviewer-scorecard.yml)

## FAQ

**Q: What does "UNKNOWN" status mean on the first run?**

A: On the first workflow execution, there is no previous status to compare against. The system shows "UNKNOWN" as the previous status and establishes the current status as the baseline. No notification is sent on the first run since there is no regression to detect.

**Q: How do I manually trigger the scorecard?**

A: Go to Actions → "Reviewer Stability Scorecard" → "Run workflow". You can optionally enable "Force notification" to receive a @mention regardless of regression status.

**Q: Where are the JSON artifacts stored?**

A: JSON reports are stored as GitHub Actions artifacts with 90-day retention. Navigate to the workflow run and download the `scorecard-{run_id}` artifact. These are NOT committed to the repository.

**Q: Why didn't I receive a notification?**

A: Notifications are only sent on regression (status downgrade) or execution failure. If the status improved or stayed the same, no notification is sent. Use `force_notify` to test the notification mechanism.

## Changelog

| Date | Change |
|------|--------|
| 2025-12-23 | Initial governance framework (Phase 0) |
