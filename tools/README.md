# MorningAI Tools

This directory contains CLI tools for monitoring and governance of the MorningAI ecosystem.

## Reviewer Stability Scorecard

**Purpose:** EPIC B governance measurement layer - calculates reviewer stability metrics to determine production readiness and EPIC C progression.

### Usage

```bash
# Set required environment variable
export GITHUB_TOKEN=your_github_token

# Run with defaults (last 7 days, both JSON and Markdown output)
python tools/reviewer_stability_scorecard.py

# Customize analysis period
python tools/reviewer_stability_scorecard.py --days 14

# Output format options
python tools/reviewer_stability_scorecard.py --output json
python tools/reviewer_stability_scorecard.py --output markdown

# Specify repository
python tools/reviewer_stability_scorecard.py --repo RC918/morningai
```

### Metrics Calculated

| Metric | Description |
|--------|-------------|
| Review Coverage | Percentage of PRs with at least one MorningAI review |
| Duplicate Reviews | Number of times the same commit was reviewed multiple times |
| Duplicate Rate | Percentage of reviewed commits with duplicates |
| Review Latency | Time from PR creation to MorningAI review |
| Health Score | Composite score (lower is better) |

### Health Score Calculation

- Each duplicate review: +50 points (heavy penalty)
- Review coverage: -1 point per % coverage (reward)
- Slow reviews (>5 min avg): +10 points (penalty)

### Status Thresholds

| Status | Criteria |
|--------|----------|
| EXCELLENT | Score = 0, no duplicates, coverage >= 50% |
| GOOD | Score < 50 |
| FAIR | Score < 100 |
| NEEDS ATTENTION | Score >= 100 |

### Exit Codes

- `0`: Success (status is EXCELLENT, GOOD, or FAIR)
- `1`: Error (missing token, API error, etc.)
- `2`: Status is NEEDS ATTENTION

### Integration with CI

This tool can be integrated into GitHub Actions as a scheduled job:

```yaml
name: Reviewer Stability Check
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
jobs:
  scorecard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r tools/requirements.txt
      - run: python tools/reviewer_stability_scorecard.py --output markdown
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Limitations & Future Improvements

**Current limitations:**
- No rate limit handling - GitHub API allows 5000 requests/hour for authenticated users. For repos with many PRs, consider using `--days` to limit scope.
- Uses REST API with O(n) calls per PR - GraphQL could be more efficient for large-scale analysis.
- Token security - ensure GITHUB_TOKEN is not logged in error messages.

**Future improvements (P6):**
- Integration with GitHub Checks API (EPIC B Phase 4) for automated status gates
- Machine-readable governance signals for PR merge decisions
- Dashboard integration for real-time monitoring
