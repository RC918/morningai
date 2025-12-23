#!/usr/bin/env python3
"""
MorningAI Reviewer Stability Scorecard

This tool calculates reviewer stability metrics using the GitHub API.
It is part of EPIC B's governance measurement layer, used to determine:
- When to enable production flags
- When to proceed to EPIC C (Flow Controller)
- Future P6 (Checks API/status gate) integration

Usage:
    GITHUB_TOKEN=xxx python tools/reviewer_stability_scorecard.py [--days 7] [--output json|markdown]

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with repo read access
    GITHUB_REPO: Repository in owner/repo format (default: RC918/morningai)

Metrics Calculated:
    - Review count per PR
    - Duplicate review detection (same commit_id reviewed multiple times)
    - Review coverage (PRs with at least one MorningAI review)
    - Review latency (time from PR open/push to review)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

# MorningAI review marker - must match orchestrator/utils/constants.py
MORNINGAI_REVIEW_MARKER = "<!-- morningai:autogen-review -->"

# Default configuration
DEFAULT_REPO = "RC918/morningai"
DEFAULT_DAYS = 7
API_BASE = "https://api.github.com"
REQUEST_TIMEOUT = 30  # seconds

# Health score weights (lower score = better)
DUPLICATE_PENALTY = 50  # Points per duplicate review
SLOW_REVIEW_PENALTY = 10  # Points if avg latency > 5 min
SLOW_REVIEW_THRESHOLD_SECONDS = 300  # 5 minutes

# Status thresholds
STATUS_GOOD_THRESHOLD = 50
STATUS_FAIR_THRESHOLD = 100
# EXCELLENT_COVERAGE_THRESHOLD: Minimum coverage % required for EXCELLENT status.
# Rationale: A repo with 0% MorningAI review coverage should not be classified
# as EXCELLENT even if it has no duplicates and score=0. The 50% threshold
# ensures meaningful reviewer adoption before granting the highest status.
# See Issue #2851 for discussion.
EXCELLENT_COVERAGE_THRESHOLD = 50


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    pass


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, reset_time: int):
        self.reset_time = reset_time
        reset_dt = datetime.fromtimestamp(reset_time, tz=timezone.utc)
        super().__init__(
            f"GitHub API rate limit exceeded. Resets at {reset_dt.isoformat()}. "
            f"Try reducing --days or wait until reset."
        )


def get_headers(token: str) -> dict:
    """Get headers for GitHub API requests."""
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def check_rate_limit(response) -> None:
    """Check response headers for rate limit and raise if exhausted."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) == 0:
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        raise RateLimitError(reset_time)


def get_recent_prs(
    session: requests.Session, repo: str, days: int, state: str = "all"
) -> list:
    """Get PRs updated within the specified number of days.

    Args:
        session: requests.Session with auth headers configured
        repo: Repository in owner/repo format
        days: Number of days to look back
        state: PR state filter (default: all)
    """
    url = f"{API_BASE}/repos/{repo}/pulls"
    since = datetime.now(timezone.utc) - timedelta(days=days)

    all_prs = []
    page = 1
    per_page = 100

    while True:
        params = {
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "per_page": per_page,
            "page": page,
        }

        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        check_rate_limit(resp)

        if resp.status_code != 200:
            raise GitHubAPIError(
                f"Failed to fetch PRs: {resp.status_code} {resp.text}"
            )

        prs = resp.json()
        if not prs:
            break

        for pr in prs:
            updated_at = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            if updated_at < since:
                return all_prs
            all_prs.append(pr)

        if len(prs) < per_page:
            break
        page += 1

    return all_prs


def get_pr_reviews(session: requests.Session, repo: str, pr_number: int) -> list:
    """Get all reviews for a specific PR.

    Args:
        session: requests.Session with auth headers configured
        repo: Repository in owner/repo format
        pr_number: Pull request number
    """
    url = f"{API_BASE}/repos/{repo}/pulls/{pr_number}/reviews"

    all_reviews = []
    page = 1
    per_page = 100

    while True:
        params = {"per_page": per_page, "page": page}
        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        check_rate_limit(resp)

        if resp.status_code != 200:
            raise GitHubAPIError(
                f"Failed to fetch reviews for PR #{pr_number}: {resp.status_code}"
            )

        reviews = resp.json()
        if not reviews:
            break

        all_reviews.extend(reviews)
        if len(reviews) < per_page:
            break
        page += 1

    return all_reviews


def is_morningai_review(review: dict) -> bool:
    """Check if a review was generated by MorningAI.

    Detection: Checks for the MorningAI marker in the review body.
    The marker is an HTML comment that is invisible to users but
    allows programmatic identification of auto-generated reviews.
    """
    body = review.get("body") or ""
    return MORNINGAI_REVIEW_MARKER in body


def analyze_pr_reviews(pr: dict, reviews: list) -> tuple:
    """Analyze reviews for a single PR.

    Returns:
        Tuple of (pr_info dict, morningai_reviews list, latencies list)
    """
    pr_number = pr["number"]
    pr_title = pr["title"][:50]
    pr_created_at = datetime.fromisoformat(
        pr["created_at"].replace("Z", "+00:00")
    )
    head_sha = pr["head"]["sha"]

    morningai_reviews = [r for r in reviews if is_morningai_review(r)]

    pr_info = {
        "number": pr_number,
        "title": pr_title,
        "state": pr["state"],
        "head_sha": head_sha[:7],
        "total_reviews": len(reviews),
        "morningai_reviews": len(morningai_reviews),
        "morningai_review_commits": [],
    }

    latencies = []
    for review in morningai_reviews:
        commit_id = review.get("commit_id")
        # Skip reviews with missing commit_id to avoid false duplicate detection
        if commit_id:
            pr_info["morningai_review_commits"].append(commit_id[:7])

        submitted_at_str = review.get("submitted_at")
        if submitted_at_str:
            submitted_at = datetime.fromisoformat(
                submitted_at_str.replace("Z", "+00:00")
            )
            latency = (submitted_at - pr_created_at).total_seconds()
            if latency > 0:
                latencies.append(latency)

    return pr_info, morningai_reviews, latencies


def compute_duplicates(reviews_by_commit: dict) -> tuple:
    """Compute duplicate review statistics.

    Returns:
        Tuple of (duplicate_count, duplicate_commits list)
    """
    duplicate_count = 0
    duplicate_commits = []

    for commit_id, reviews_list in reviews_by_commit.items():
        if len(reviews_list) > 1:
            duplicate_count += len(reviews_list) - 1
            duplicate_commits.append({
                "commit_id": commit_id[:7] if commit_id else "unknown",
                "review_count": len(reviews_list),
                "pr_numbers": [r["pr_number"] for r in reviews_list],
            })

    return duplicate_count, duplicate_commits


def compute_latency_stats(latencies: list) -> dict:
    """Compute latency statistics from a list of latency values."""
    if not latencies:
        return {
            "avg_latency_seconds": None,
            "min_latency_seconds": None,
            "max_latency_seconds": None,
        }

    return {
        "avg_latency_seconds": round(sum(latencies) / len(latencies), 1),
        "min_latency_seconds": round(min(latencies), 1),
        "max_latency_seconds": round(max(latencies), 1),
    }


def compute_health_score(
    duplicate_reviews: int,
    coverage_percent: float,
    avg_latency_seconds: float
) -> tuple:
    """Compute health score and status.

    Health score is lower = better:
    - Each duplicate review: +DUPLICATE_PENALTY points (heavy penalty)
    - Review coverage: -1 point per % coverage (reward)
    - Slow reviews (>SLOW_REVIEW_THRESHOLD_SECONDS avg): +SLOW_REVIEW_PENALTY points

    Returns:
        Tuple of (health_score, status)
    """
    health_score = 0
    health_score += duplicate_reviews * DUPLICATE_PENALTY
    health_score -= coverage_percent
    if avg_latency_seconds and avg_latency_seconds > SLOW_REVIEW_THRESHOLD_SECONDS:
        health_score += SLOW_REVIEW_PENALTY

    health_score = max(0, health_score)

    # Issue #2851: EXCELLENT requires minimum coverage threshold
    # 0% coverage should not be classified as EXCELLENT
    if (health_score == 0 and duplicate_reviews == 0 and
            coverage_percent >= EXCELLENT_COVERAGE_THRESHOLD):
        status = "EXCELLENT"
    elif health_score < STATUS_GOOD_THRESHOLD:
        status = "GOOD"
    elif health_score < STATUS_FAIR_THRESHOLD:
        status = "FAIR"
    else:
        status = "NEEDS ATTENTION"

    return health_score, status


def calculate_metrics(token: str, repo: str, days: int) -> dict:
    """Calculate reviewer stability metrics.

    This is the main orchestration function that:
    1. Fetches PRs from GitHub
    2. Analyzes reviews for each PR
    3. Computes aggregate statistics
    4. Returns a metrics dictionary

    Issue #2852: Uses requests.Session for connection reuse and better performance.
    Uses context manager for proper resource cleanup.
    """
    # Issue #2852: Create session for connection pooling with context manager
    # for proper cleanup (recommended by Gemini Code Assist)
    with requests.Session() as session:
        session.headers.update(get_headers(token))

        print(f"Fetching PRs from {repo} updated in last {days} days...")
        prs = get_recent_prs(session, repo, days)
        print(f"Found {len(prs)} PRs")

        # Initialize tracking structures
        reviews_by_commit: dict = defaultdict(list)
        all_latencies = []
        prs_with_review = 0
        total_reviews = 0
        prs_analyzed = []

        # Analyze each PR
        for pr in prs:
            pr_number = pr["number"]
            pr_title = pr["title"][:50]
            print(f"  Analyzing PR #{pr_number}: {pr_title}...")

            try:
                reviews = get_pr_reviews(session, repo, pr_number)
            except GitHubAPIError as e:
                print(f"    Warning: {e}")
                continue

            pr_info, morningai_reviews, latencies = analyze_pr_reviews(pr, reviews)
            prs_analyzed.append(pr_info)

            if morningai_reviews:
                prs_with_review += 1
                total_reviews += len(morningai_reviews)
                all_latencies.extend(latencies)

                # Track reviews by commit for duplicate detection
                for review in morningai_reviews:
                    commit_id = review.get("commit_id")
                    if commit_id:  # Only track if commit_id exists
                        reviews_by_commit[commit_id].append({
                            "pr_number": pr_number,
                            "review_id": review["id"],
                            "submitted_at": review.get("submitted_at"),
                        })

    # Compute aggregate statistics (outside session context - no more API calls)
    total_prs = len(prs)
    coverage_percent = (
        round(100 * prs_with_review / total_prs, 1) if total_prs > 0 else 0.0
    )

    duplicate_count, duplicate_commits = compute_duplicates(reviews_by_commit)

    total_reviewed_commits = len(reviews_by_commit)
    duplicate_rate = (
        round(100 * len(duplicate_commits) / total_reviewed_commits, 1)
        if total_reviewed_commits > 0
        else 0.0
    )

    latency_stats = compute_latency_stats(all_latencies)
    health_score, status = compute_health_score(
        duplicate_count, coverage_percent, latency_stats["avg_latency_seconds"]
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "days_analyzed": days,
        "total_prs": total_prs,
        "prs_with_morningai_review": prs_with_review,
        "review_coverage_percent": coverage_percent,
        "total_morningai_reviews": total_reviews,
        "duplicate_reviews": duplicate_count,
        "duplicate_rate_percent": duplicate_rate,
        "duplicate_commits": duplicate_commits,
        "health_score": health_score,
        "status": status,
        # Internal data (excluded from output but used for analysis)
        "prs_analyzed": prs_analyzed,
        "review_latencies_seconds": all_latencies,
        **latency_stats,
    }


def format_markdown(metrics: dict) -> str:
    """Format metrics as Markdown report."""
    lines = [
        "# MorningAI Reviewer Stability Scorecard",
        "",
        f"**Generated:** {metrics['generated_at']}",
        f"**Repository:** {metrics['repo']}",
        f"**Analysis Period:** Last {metrics['days_analyzed']} days",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total PRs Analyzed | {metrics['total_prs']} |",
        f"| PRs with MorningAI Review | {metrics['prs_with_morningai_review']} |",
        f"| Review Coverage | {metrics['review_coverage_percent']}% |",
        f"| Total MorningAI Reviews | {metrics['total_morningai_reviews']} |",
        f"| Duplicate Reviews | {metrics['duplicate_reviews']} |",
        f"| Duplicate Rate | {metrics['duplicate_rate_percent']}% |",
        "",
    ]

    if metrics["avg_latency_seconds"] is not None:
        lines.extend([
            "## Review Latency",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Average | {metrics['avg_latency_seconds']:.0f}s |",
            f"| Minimum | {metrics['min_latency_seconds']:.0f}s |",
            f"| Maximum | {metrics['max_latency_seconds']:.0f}s |",
            "",
        ])

    if metrics["duplicate_commits"]:
        lines.extend([
            "## Duplicate Reviews (Needs Investigation)",
            "",
            "| Commit | Review Count | PRs |",
            "|--------|--------------|-----|",
        ])
        for dup in metrics["duplicate_commits"]:
            pr_list = ", ".join(f"#{n}" for n in dup["pr_numbers"])
            lines.append(
                f"| {dup['commit_id']} | {dup['review_count']} | {pr_list} |"
            )
        lines.append("")

    lines.extend([
        "## Health Assessment",
        "",
        f"**Health Score:** {metrics['health_score']} (lower is better)",
        f"**Status:** {metrics['status']}",
        "",
        "### Scoring Criteria",
        "",
        "- Each duplicate review: +50 points",
        "- Review coverage: -1 point per % coverage",
        "- Slow reviews (>5 min avg): +10 points",
        "",
        "### Status Thresholds",
        "",
        f"- EXCELLENT: Score = 0, no duplicates, coverage >= {EXCELLENT_COVERAGE_THRESHOLD}%",
        "- GOOD: Score < 50",
        "- FAIR: Score < 100",
        "- NEEDS ATTENTION: Score >= 100",
    ])

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MorningAI Reviewer Stability Scorecard"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Number of days to analyze (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--output",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help=f"Repository in owner/repo format (default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Write JSON output to file (optional, for CI workflows)",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default=None,
        help="Write Markdown output to file (optional, for CI workflows)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    repo = args.repo or os.environ.get("GITHUB_REPO", DEFAULT_REPO)

    try:
        metrics = calculate_metrics(token, repo, args.days)
    except GitHubAPIError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error: {e}")
        sys.exit(1)

    # Remove detailed PR list from output (too verbose)
    output_metrics = {k: v for k, v in metrics.items() if k != "prs_analyzed"}
    # Also remove raw latency list
    output_metrics.pop("review_latencies_seconds", None)

    json_content = json.dumps(output_metrics, indent=2)
    md_content = format_markdown(output_metrics)

    if args.json_out:
        with open(args.json_out, "w") as f:
            f.write(json_content)
        print(f"JSON output written to: {args.json_out}")

    if args.md_out:
        with open(args.md_out, "w") as f:
            f.write(md_content)
        print(f"Markdown output written to: {args.md_out}")

    if args.output in ("json", "both"):
        print("\n" + "=" * 60)
        print("JSON Output:")
        print("=" * 60)
        print(json_content)

    if args.output in ("markdown", "both"):
        print("\n" + "=" * 60)
        print("Markdown Output:")
        print("=" * 60)
        print(md_content)

    # Exit with non-zero if status is bad
    if metrics["status"] == "NEEDS ATTENTION":
        sys.exit(2)

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
