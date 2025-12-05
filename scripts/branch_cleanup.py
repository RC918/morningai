#!/usr/bin/env python3
"""
Branch Cleanup Script for morningai repository

This script safely deletes stale remote branches that meet specific criteria:
- No open PRs associated with the branch
- Branch is older than a configurable threshold (default: 60 days)
- Branch is not in the protected list (main, develop, release/*, etc.)

Root Cause Analysis:
The repository has accumulated 888+ branches because:
1. GitHub's "auto-delete head branches" only triggers when a PR is MERGED
2. Many branches (especially orchestrator/* and devin/*) never had merged PRs
3. The orchestrator FAQ automation creates branches but cleanup only runs on CI completion
4. Historical branches from before auto-delete was enabled remain

Usage:
    python scripts/branch_cleanup.py --dry-run          # Preview what would be deleted
    python scripts/branch_cleanup.py --execute          # Actually delete branches
    python scripts/branch_cleanup.py --execute --yes    # Non-interactive execution
    python scripts/branch_cleanup.py --pattern "orchestrator/*" --days 30  # Custom filter
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

PROTECTED_BRANCHES = {
    'main',
    'master',
    'develop',
    'HEAD',
}

PROTECTED_PATTERNS = [
    'release/*',
    'hotfix/*',
    'gh-pages*',
]

DEFAULT_STALE_DAYS = 60
BRANCH_COUNT_WARNING_THRESHOLD = 500
BRANCH_COUNT_CRITICAL_THRESHOLD = 800


def run_git_command(cmd: List[str]) -> Tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def get_remote_branches() -> List[str]:
    """Get all remote branches."""
    success, output = run_git_command(['git', 'branch', '-r'])
    if not success:
        print(f"Error getting branches: {output}")
        sys.exit(1)

    branches = []
    for line in output.split('\n'):
        branch = line.strip()
        if branch and not branch.startswith('origin/HEAD'):
            if branch.startswith('origin/'):
                branch = branch[7:]
            branches.append(branch)

    return branches


def get_all_branch_dates() -> Dict[str, datetime]:
    """
    Get last commit dates for ALL remote branches in a single batch call.
    Uses committerdate for more accurate "last activity" tracking.
    """
    success, output = run_git_command([
        'git', 'for-each-ref',
        '--format=%(refname:short) %(committerdate:iso8601)',
        'refs/remotes/origin'
    ])

    dates: Dict[str, datetime] = {}
    if success and output:
        for line in output.split('\n'):
            if not line.strip():
                continue
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                ref_name = parts[0]
                if ref_name.startswith('origin/'):
                    branch = ref_name[7:]
                else:
                    branch = ref_name
                if branch == 'HEAD':
                    continue
                try:
                    date_str = parts[1].strip()
                    date_parts = date_str.split()
                    if len(date_parts) >= 2:
                        date_only = date_parts[0]
                        dates[branch] = datetime.strptime(date_only, '%Y-%m-%d')
                except (ValueError, IndexError):
                    dates[branch] = datetime.now()

    return dates


def is_protected(branch: str) -> bool:
    """Check if a branch is protected using fnmatch for pattern matching."""
    if branch in PROTECTED_BRANCHES:
        return True

    for pattern in PROTECTED_PATTERNS:
        if fnmatch.fnmatch(branch, pattern):
            return True

    return False


def matches_pattern(branch: str, pattern: str) -> bool:
    """Check if branch matches the given glob pattern using fnmatch."""
    if not pattern:
        return True
    return fnmatch.fnmatch(branch, pattern)


def get_branches_with_open_prs_graphql() -> Set[str]:
    """
    Get branches that have open PRs using GitHub GraphQL API for better performance.
    Falls back to REST API if GraphQL fails.
    """
    graphql_query = '''
    query($cursor: String) {
      repository(owner: "RC918", name: "morningai") {
        pullRequests(states: OPEN, first: 100, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            headRefName
          }
        }
      }
    }
    '''

    try:
        all_branches: Set[str] = set()
        cursor: Optional[str] = None

        while True:
            variables = json.dumps({"cursor": cursor})
            result = subprocess.run(
                ['gh', 'api', 'graphql', '-f', f'query={graphql_query}', '-f', f'variables={variables}'],
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)
            prs = data.get('data', {}).get('repository', {}).get('pullRequests', {})
            nodes = prs.get('nodes', [])

            for pr in nodes:
                if pr and pr.get('headRefName'):
                    all_branches.add(pr['headRefName'])

            page_info = prs.get('pageInfo', {})
            if not page_info.get('hasNextPage'):
                break
            cursor = page_info.get('endCursor')

        return all_branches

    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: GraphQL query failed ({e}), falling back to REST API...")
        return get_branches_with_open_prs_rest()


def get_branches_with_open_prs_rest() -> Set[str]:
    """Get branches that have open PRs using REST API (fallback)."""
    try:
        result = subprocess.run(
            ['gh', 'pr', 'list', '--state', 'open', '--json', 'headRefName', '-q', '.[].headRefName'],
            capture_output=True,
            text=True,
            check=True
        )
        return set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Could not get open PRs via gh CLI. Proceeding without PR check.")
        return set()


def analyze_branches(
    branches: List[str],
    branch_dates: Dict[str, datetime],
    stale_days: int,
    pattern: str,
    open_pr_branches: Set[str]
) -> Tuple[List[Tuple[str, str, int]], List[Tuple[str, str]]]:
    """
    Analyze branches and categorize them.

    Returns:
        - List of (branch, reason, age_days) tuples for branches to delete
        - List of (branch, reason) tuples for branches to keep
    """
    to_delete: List[Tuple[str, str, int]] = []
    to_keep: List[Tuple[str, str]] = []
    cutoff_date = datetime.now() - timedelta(days=stale_days)

    for branch in branches:
        if is_protected(branch):
            to_keep.append((branch, 'protected'))
            continue

        if not matches_pattern(branch, pattern):
            to_keep.append((branch, 'does not match pattern'))
            continue

        if branch in open_pr_branches:
            to_keep.append((branch, 'has open PR'))
            continue

        last_commit = branch_dates.get(branch, datetime.now())
        age_days = (datetime.now() - last_commit).days

        if last_commit > cutoff_date:
            to_keep.append((branch, f'too recent ({age_days} days old)'))
            continue

        reason = f'stale ({age_days} days old)'
        to_delete.append((branch, reason, age_days))

    return to_delete, to_keep


def delete_branch(branch: str) -> bool:
    """Delete a remote branch."""
    success, _ = run_git_command(['git', 'push', 'origin', '--delete', branch])
    return success


def check_branch_count_threshold(total_branches: int) -> Optional[str]:
    """
    Check if branch count exceeds warning/critical thresholds.
    Returns alert level or None if within normal range.
    """
    if total_branches >= BRANCH_COUNT_CRITICAL_THRESHOLD:
        return 'CRITICAL'
    elif total_branches >= BRANCH_COUNT_WARNING_THRESHOLD:
        return 'WARNING'
    return None


def print_summary(
    to_delete: List[Tuple[str, str, int]],
    to_keep: List[Tuple[str, str]],
    pattern: str,
    stale_days: int
):
    """Print analysis summary."""
    total_branches = len(to_delete) + len(to_keep)

    print("\n" + "=" * 70)
    print("BRANCH CLEANUP ANALYSIS")
    print("=" * 70)

    alert_level = check_branch_count_threshold(total_branches)
    if alert_level:
        print(f"\n[{alert_level}] Branch count ({total_branches}) exceeds threshold!")
        if alert_level == 'CRITICAL':
            print(f"  Critical threshold: {BRANCH_COUNT_CRITICAL_THRESHOLD}")
        else:
            print(f"  Warning threshold: {BRANCH_COUNT_WARNING_THRESHOLD}")
        print("  Recommendation: Run cleanup to reduce branch count.\n")

    print(f"Pattern filter: {pattern or 'all branches'}")
    print(f"Stale threshold: {stale_days} days")
    print(f"Total branches analyzed: {total_branches}")
    print(f"Branches to delete: {len(to_delete)}")
    print(f"Branches to keep: {len(to_keep)}")

    prefix_counts: Dict[str, int] = {}
    for branch, _, _ in to_delete:
        prefix = branch.split('/')[0] if '/' in branch else 'other'
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

    if prefix_counts:
        print("\nBranches to delete by category:")
        for prefix, count in sorted(prefix_counts.items(), key=lambda x: -x[1]):
            print(f"  {prefix}/*: {count}")

    print("\n" + "-" * 70)
    print("BRANCHES TO DELETE:")
    print("-" * 70)

    for branch, reason, _ in sorted(to_delete, key=lambda x: -x[2])[:50]:
        print(f"  {branch} ({reason})")

    if len(to_delete) > 50:
        print(f"  ... and {len(to_delete) - 50} more")


def print_metrics(total_branches: int, to_delete_count: int, deleted_count: int = 0):
    """Print metrics in a format suitable for monitoring systems."""
    print("\n" + "=" * 70)
    print("METRICS (for monitoring integration)")
    print("=" * 70)
    print(f"branch_cleanup_total_branches{{repo=\"morningai\"}} {total_branches}")
    print(f"branch_cleanup_stale_branches{{repo=\"morningai\"}} {to_delete_count}")
    print(f"branch_cleanup_deleted_branches{{repo=\"morningai\"}} {deleted_count}")
    print(f"branch_cleanup_warning_threshold{{repo=\"morningai\"}} {BRANCH_COUNT_WARNING_THRESHOLD}")
    print(f"branch_cleanup_critical_threshold{{repo=\"morningai\"}} {BRANCH_COUNT_CRITICAL_THRESHOLD}")

    alert_level = check_branch_count_threshold(total_branches)
    alert_value = 2 if alert_level == 'CRITICAL' else (1 if alert_level == 'WARNING' else 0)
    print(f"branch_cleanup_alert_level{{repo=\"morningai\"}} {alert_value}")


def main():
    parser = argparse.ArgumentParser(
        description='Clean up stale remote branches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete the branches'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt (non-interactive mode)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='',
        help='Only delete branches matching this pattern (e.g., "orchestrator/*", "devin/*")'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=DEFAULT_STALE_DAYS,
        help=f'Delete branches older than this many days (default: {DEFAULT_STALE_DAYS})'
    )
    parser.add_argument(
        '--skip-pr-check',
        action='store_true',
        help='Skip checking for open PRs (faster but less safe)'
    )
    parser.add_argument(
        '--metrics',
        action='store_true',
        help='Output metrics in Prometheus-compatible format'
    )

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Error: Must specify either --dry-run or --execute")
        parser.print_help()
        sys.exit(1)

    print("Fetching remote branches...")
    run_git_command(['git', 'fetch', '--all', '--prune'])

    branches = get_remote_branches()
    print(f"Found {len(branches)} remote branches")

    print("Fetching branch dates (batch query)...")
    branch_dates = get_all_branch_dates()
    print(f"Retrieved dates for {len(branch_dates)} branches")

    open_pr_branches: Set[str] = set()
    if not args.skip_pr_check:
        print("Checking for open PRs (GraphQL batch query)...")
        open_pr_branches = get_branches_with_open_prs_graphql()
        print(f"Found {len(open_pr_branches)} branches with open PRs")

    to_delete, to_keep = analyze_branches(
        branches,
        branch_dates,
        args.days,
        args.pattern,
        open_pr_branches
    )

    print_summary(to_delete, to_keep, args.pattern, args.days)

    deleted_count = 0

    if args.execute and to_delete:
        print("\n" + "=" * 70)
        print("EXECUTING DELETION")
        print("=" * 70)

        if not args.yes:
            confirm = input(f"\nAre you sure you want to delete {len(to_delete)} branches? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                sys.exit(0)

        deleted = 0
        failed = 0
        for branch, reason, _ in to_delete:
            print(f"Deleting {branch}...", end=' ')
            if delete_branch(branch):
                print("OK")
                deleted += 1
            else:
                print("FAILED")
                failed += 1

        deleted_count = deleted
        print(f"\nDeleted {deleted} branches, {failed} failed")

    elif args.dry_run:
        print("\n[DRY RUN] No branches were deleted. Use --execute to delete.")

    if args.metrics:
        print_metrics(len(branches), len(to_delete), deleted_count)


if __name__ == '__main__':
    main()
