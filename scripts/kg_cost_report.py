#!/usr/bin/env python3
"""
Knowledge Graph Cost Report Script
Generates daily and weekly cost reports for OpenAI API usage
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.dev_agent.knowledge_graph import get_embeddings_cache  # noqa: E402


def format_cost_report(stats: dict, period: str) -> str:
    """Format cost statistics into readable report"""
    if not stats.get('summary'):
        return f"No cost data available for {period}"

    summary = stats['summary']

    report = []
    report.append(f"\n{'=' * 70}")
    report.append(f"Knowledge Graph Cost Report - {period}")
    report.append(f"{'=' * 70}\n")

    report.append(f"📊 API Usage:")
    report.append(f"   Total Calls: {summary.get('total_calls', 0):,}")
    report.append(f"   Total Tokens: {summary.get('total_tokens', 0):,}")
    report.append(f"   Cache Hits: {summary.get('cache_hits', 0):,}")
    report.append(f"   Cache Misses: {summary.get('cache_misses', 0):,}")

    cache_hit_rate = summary.get('cache_hit_rate', 0)
    report.append(f"   Cache Hit Rate: {cache_hit_rate:.1f}%")

    report.append(f"\n💰 Cost Breakdown:")
    report.append(f"   Total Cost: ${summary.get('total_cost', 0):.4f} USD")

    if summary.get('total_calls', 0) > 0:
        avg_cost = summary.get('total_cost', 0) / summary.get('total_calls', 1)
        report.append(f"   Avg Cost per Call: ${avg_cost:.6f} USD")

    if summary.get('cache_misses', 0) > 0:
        cost_per_miss = summary.get(
            'total_cost', 0) / summary.get('cache_misses', 1)
        report.append(f"   Cost per Cache Miss: ${cost_per_miss:.6f} USD")

    if cache_hit_rate > 0:
        estimated_savings = summary.get(
            'total_cost', 0) * (cache_hit_rate / (100 - cache_hit_rate))
        report.append(
            f"   Estimated Savings (caching): ${
                estimated_savings:.4f} USD")

    report.append(f"\n")

    return "\n".join(report)


def generate_daily_report():
    """Generate report for today"""
    cache = get_embeddings_cache()

    if not cache.enabled:
        print("❌ Cache not enabled. Cannot generate cost report.")
        print("   Configure Redis to enable cost tracking.")
        return 1

    stats = cache.get_stats(days=1)
    print(format_cost_report(stats, "Today"))

    return 0


def generate_weekly_report():
    """Generate report for past 7 days"""
    cache = get_embeddings_cache()

    if not cache.enabled:
        print("❌ Cache not enabled. Cannot generate cost report.")
        return 1

    stats = cache.get_stats(days=7)
    print(format_cost_report(stats, "Past 7 Days"))

    if stats.get('summary'):
        print(f"📅 Daily Breakdown:")

        total_cost = stats['summary'].get('total_cost', 0)
        avg_daily = total_cost / 7
        print(f"   Average per day: ${avg_daily:.4f} USD")
        print()

    return 0


def generate_comparison_report():
    """Generate comparison report (today vs. yesterday)"""
    cache = get_embeddings_cache()

    if not cache.enabled:
        print("❌ Cache not enabled. Cannot generate cost report.")
        return 1

    today_stats = cache.get_stats(days=1)

    week_stats = cache.get_stats(days=7)

    print(format_cost_report(today_stats, "Today"))

    if week_stats.get('summary'):
        week_total = week_stats['summary'].get('total_cost', 0)
        week_avg = week_total / 7

        today_total = today_stats.get('summary', {}).get('total_cost', 0)

        print(f"📈 Comparison:")
        print(f"   Today: ${today_total:.4f} USD")
        print(f"   Weekly Average: ${week_avg:.4f} USD")

        if week_avg > 0:
            diff_pct = ((today_total - week_avg) / week_avg) * 100
            if diff_pct > 0:
                print(f"   Difference: +{diff_pct:.1f}% (above average)")
            else:
                print(f"   Difference: {diff_pct:.1f}% (below average)")
        print()

    return 0


def check_cost_limit():
    """Check if approaching or exceeded daily cost limit"""
    import os

    max_daily_cost_str = os.getenv('OPENAI_MAX_DAILY_COST')
    if not max_daily_cost_str:
        print("ℹ️  No daily cost limit configured (OPENAI_MAX_DAILY_COST not set)")
        return 0

    try:
        max_daily_cost = float(max_daily_cost_str)
    except ValueError:
        print(f"❌ Invalid OPENAI_MAX_DAILY_COST value: {max_daily_cost_str}")
        return 1

    cache = get_embeddings_cache()

    if not cache.enabled:
        print("❌ Cache not enabled. Cannot check cost limit.")
        return 1

    stats = cache.get_stats(days=1)

    if not stats.get('summary'):
        print(f"✅ No usage today. Daily limit: ${max_daily_cost:.4f} USD")
        return 0

    daily_cost = stats['summary'].get('total_cost', 0)

    print(f"\n💰 Daily Cost Limit Check:")
    print(f"   Current Usage: ${daily_cost:.4f} USD")
    print(f"   Daily Limit: ${max_daily_cost:.4f} USD")
    print(f"   Remaining: ${max(0, max_daily_cost - daily_cost):.4f} USD")

    usage_pct = (daily_cost / max_daily_cost) * \
        100 if max_daily_cost > 0 else 0
    print(f"   Usage: {usage_pct:.1f}%")

    if daily_cost >= max_daily_cost:
        print(f"\n   ❌ DAILY LIMIT EXCEEDED!")
        print(f"   API calls will be blocked until tomorrow.")
        return 1
    elif usage_pct >= 80:
        print(f"\n   ⚠️  WARNING: Approaching daily limit ({usage_pct:.1f}%)")
        return 0
    elif usage_pct >= 50:
        print(f"\n   ⚠️  Moderate usage ({usage_pct:.1f}%)")
        return 0
    else:
        print(f"\n   ✅ Usage within normal range ({usage_pct:.1f}%)")
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate Knowledge Graph OpenAI API cost reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kg_cost_report.py --daily

  python kg_cost_report.py --weekly

  python kg_cost_report.py --check-limit

  python kg_cost_report.py --compare

Environment Variables:
  REDIS_URL                   - Redis connection URL (required)
  OPENAI_MAX_DAILY_COST      - Maximum daily cost in USD (optional)
        """
    )

    parser.add_argument(
        '--daily',
        action='store_true',
        help='Generate daily cost report'
    )

    parser.add_argument(
        '--weekly',
        action='store_true',
        help='Generate weekly cost report (past 7 days)'
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='Generate comparison report'
    )

    parser.add_argument(
        '--check-limit',
        action='store_true',
        help='Check if approaching or exceeded daily cost limit'
    )

    args = parser.parse_args()

    if not any([args.daily, args.weekly, args.compare, args.check_limit]):
        args.daily = True

    exit_code = 0

    if args.daily:
        exit_code = max(exit_code, generate_daily_report())

    if args.weekly:
        exit_code = max(exit_code, generate_weekly_report())

    if args.compare:
        exit_code = max(exit_code, generate_comparison_report())

    if args.check_limit:
        exit_code = max(exit_code, check_cost_limit())

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
