#!/usr/bin/env python3
"""
Coverage Trend Dashboard - Track and display test coverage trends

This dashboard tracks coverage metrics over time and provides:
- Current coverage status for all modules
- Historical trend analysis
- Threshold compliance checking
- Coverage regression alerts

Blueprint Section 5.4: CI Enforcement
- Thresholds are configurable via settings (COVERAGE_THRESHOLD_*)
- Falls back to hardcoded defaults if settings unavailable

Usage:
    python coverage_dashboard.py [--days DAYS] [--module MODULE]

Example:
    python coverage_dashboard.py --days 30
    python coverage_dashboard.py --module api-backend
"""
import os
import sys
import json
import argparse
import redis
from datetime import datetime, timedelta
from typing import Dict, Optional


def get_coverage_thresholds() -> Dict[str, int]:
    """
    Get coverage thresholds from settings or use defaults.

    Blueprint Section 5.4: CI Enforcement
    Thresholds are configurable via environment variables:
    - COVERAGE_THRESHOLD_API_BACKEND
    - COVERAGE_THRESHOLD_ORCHESTRATOR
    - COVERAGE_THRESHOLD_SHARED_UI
    - COVERAGE_THRESHOLD_FRONTEND_DASHBOARD
    - COVERAGE_THRESHOLD_OWNER_CONSOLE

    Returns:
        Dict mapping module names to coverage threshold percentages
    """
    defaults = {
        'api-backend': 74,
        'orchestrator': 50,
        'shared-ui': 60,
        'frontend-dashboard': 80,
        'owner-console': 70,
    }

    try:
        from common.config.settings import settings
        if settings:
            return {
                'api-backend': getattr(
                    settings, 'coverage_threshold_api_backend', defaults['api-backend']
                ),
                'orchestrator': getattr(
                    settings, 'coverage_threshold_orchestrator', defaults['orchestrator']
                ),
                'shared-ui': getattr(
                    settings, 'coverage_threshold_shared_ui', defaults['shared-ui']
                ),
                'frontend-dashboard': getattr(
                    settings,
                    'coverage_threshold_frontend_dashboard',
                    defaults['frontend-dashboard']
                ),
                'owner-console': getattr(
                    settings, 'coverage_threshold_owner_console', defaults['owner-console']
                ),
            }
    except ImportError:
        pass

    return defaults


COVERAGE_THRESHOLDS = get_coverage_thresholds()

# Redis key patterns
COVERAGE_HISTORY_KEY = 'coverage:history:{module}'


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client from environment"""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        return None
    try:
        return redis.from_url(redis_url)
    except redis.exceptions.RedisError as e:
        print(f"Warning: Could not connect to Redis: {e}")
        return None


def record_coverage(module: str, coverage_pct: float, commit_sha: str = None):
    """Record a coverage measurement to Redis for trend tracking"""
    r = get_redis_client()
    if not r:
        print("Warning: Redis not available, coverage not recorded")
        return False

    now = datetime.utcnow()
    timestamp = now.isoformat()
    data = {
        'timestamp': timestamp,
        'coverage': coverage_pct,
        'commit': commit_sha or 'unknown',
        'threshold': COVERAGE_THRESHOLDS.get(module, 0),
    }

    # Store in sorted set with timestamp as score
    key = COVERAGE_HISTORY_KEY.format(module=module)
    score = now.timestamp()
    r.zadd(key, {json.dumps(data): score})

    # Keep only last 90 days of data
    cutoff = (now - timedelta(days=90)).timestamp()
    r.zremrangebyscore(key, '-inf', cutoff)

    return True


def get_coverage_history(module: str, days: int = 30) -> list:
    """Get coverage history for a module"""
    r = get_redis_client()
    if not r:
        return []

    key = COVERAGE_HISTORY_KEY.format(module=module)
    cutoff = (datetime.utcnow() - timedelta(days=days)).timestamp()

    # Get all entries after cutoff
    entries = r.zrangebyscore(key, cutoff, '+inf')

    history = []
    for entry in entries:
        try:
            data = json.loads(entry)
            history.append(data)
        except json.JSONDecodeError:
            continue

    return history


def calculate_trend(history: list) -> dict:
    """Calculate coverage trend from history"""
    if len(history) < 2:
        return {'direction': 'stable', 'change': 0.0}

    # Get first and last coverage values
    first = history[0]['coverage']
    last = history[-1]['coverage']
    change = last - first

    if change > 1.0:
        direction = 'improving'
    elif change < -1.0:
        direction = 'declining'
    else:
        direction = 'stable'

    return {
        'direction': direction,
        'change': change,
        'first': first,
        'last': last,
        'samples': len(history),
    }


def display_module_status(module: str, history: list, threshold: int):
    """Display status for a single module"""
    if not history:
        print(f"  {module}: No data available")
        return

    latest = history[-1]
    coverage = latest['coverage']
    trend = calculate_trend(history)

    # Status indicators
    status = '✅' if coverage >= threshold else '❌'
    trend_icon = {
        'improving': '📈',
        'declining': '📉',
        'stable': '➡️',
    }.get(trend['direction'], '➡️')

    print(f"  {module}:")
    print(f"    Coverage: {coverage:.2f}% {status} (threshold: {threshold}%)")
    print(f"    Trend: {trend_icon} {trend['direction']} ({trend['change']:+.2f}% over {trend['samples']} samples)")
    print(f"    Last updated: {latest['timestamp']}")


def display_dashboard(days: int = 30, module: Optional[str] = None):
    """Display the coverage dashboard"""
    print("=" * 70)
    print(f"Coverage Trend Dashboard - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Showing trends for last {days} days")
    print("=" * 70)
    print()

    modules = [module] if module else list(COVERAGE_THRESHOLDS.keys())

    all_passing = True
    for mod in modules:
        threshold = COVERAGE_THRESHOLDS.get(mod, 0)
        history = get_coverage_history(mod, days)

        if history:
            latest = history[-1]['coverage']
            if latest < threshold:
                all_passing = False

        display_module_status(mod, history, threshold)
        print()

    # Summary
    print("-" * 70)
    if all_passing:
        print("✅ All modules meeting coverage thresholds!")
    else:
        print("⚠️ Some modules below coverage thresholds - action required")
    print("=" * 70)


def display_summary_table(days: int = 30):
    """Display a summary table of all module coverage"""
    print()
    print("Coverage Summary Table")
    print("-" * 60)
    print(f"{'Module':<20} {'Coverage':>10} {'Threshold':>10} {'Status':>10}")
    print("-" * 60)

    for module, threshold in COVERAGE_THRESHOLDS.items():
        history = get_coverage_history(module, days=days)
        if history:
            coverage = history[-1]['coverage']
            status = '✅ Pass' if coverage >= threshold else '❌ Fail'
            print(f"{module:<20} {coverage:>9.2f}% {threshold:>9}% {status:>10}")
        else:
            print(f"{module:<20} {'N/A':>10} {threshold:>9}% {'No data':>10}")

    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description='Coverage Trend Dashboard')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to show trends for (default: 30)')
    parser.add_argument('--module', type=str, default=None,
                        help='Specific module to show (default: all)')
    parser.add_argument('--summary', action='store_true',
                        help='Show summary table only')
    parser.add_argument('--record', type=str, nargs=2, metavar=('MODULE', 'COVERAGE'),
                        help='Record a coverage measurement: --record api-backend 75.5')
    parser.add_argument('--commit', type=str, default=None,
                        help='Commit SHA for recording (used with --record)')

    args = parser.parse_args()

    if args.record:
        module, coverage = args.record
        try:
            coverage_pct = float(coverage)
        except ValueError:
            print(f"Error: Invalid coverage value: {coverage}")
            sys.exit(1)

        if record_coverage(module, coverage_pct, args.commit):
            print(f"✅ Recorded coverage for {module}: {coverage_pct}%")
        else:
            print(f"❌ Failed to record coverage for {module}")
        return

    if args.summary:
        display_summary_table(days=args.days)
    else:
        display_dashboard(days=args.days, module=args.module)


if __name__ == '__main__':
    main()
