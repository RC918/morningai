#!/usr/bin/env python3
"""
Simple Canary Dashboard - Display current metrics

Usage:
    python canary_dashboard.py [--window MINUTES]

Example:
    python canary_dashboard.py --window 15
"""
import os
import sys
import argparse
import redis
from datetime import datetime

# Add orchestrator to path
sys.path.insert(0, '/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator')

try:
    from metrics import create_canary_metrics
except ImportError as e:
    print(f"Error: Failed to import metrics module: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def display_dashboard(window_minutes=15):
    """Display current canary metrics"""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("Error: REDIS_URL environment variable not set")
        print("Please set REDIS_URL before running this script")
        return False
    
    try:
        r = redis.from_url(redis_url)
        metrics = create_canary_metrics(r, enabled=True)
    except Exception as e:
        print(f"Error: Failed to connect to Redis: {e}")
        return False
    
    # Get summary
    try:
        summary = metrics.get_canary_summary(window_minutes=window_minutes)
    except Exception as e:
        print(f"Error: Failed to get canary summary: {e}")
        return False
    
    print("=" * 60)
    print(f"Phase 1 Canary Dashboard - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Window: Last {window_minutes} minutes")
    print("=" * 60)
    print()
    
    if not summary.get('enabled'):
        print("❌ Canary metrics disabled")
        return False
    
    counts = summary.get('counts', {})
    rates = summary.get('rates', {})
    latency = summary.get('latency', {})
    
    # Routing Decisions
    print("📊 Routing Decisions")
    decisions_simple = counts.get('decisions_simple', 0)
    decisions_langgraph = counts.get('decisions_langgraph', 0)
    total_decisions = counts.get('total_decisions', 0)
    print(f"  Simple Mode:    {decisions_simple:>5}")
    print(f"  LangGraph Mode: {decisions_langgraph:>5}")
    if total_decisions > 0:
        langgraph_pct = (decisions_langgraph / total_decisions) * 100

        phases = [
            (10, '~5%', (4, 6)),
            (20, '~15%', (13, 17)),
            (40, '~25%', (23, 27)),
            (75, '~50%', (48, 52)),
        ]

        target_str = "100%"
        status = "✅" if langgraph_pct >= 98 else "⚠️"

        for limit, target, (min_ok, max_ok) in phases:
            if langgraph_pct < limit:
                target_str = target
                status = "✅" if min_ok <= langgraph_pct <= max_ok else "⚠️"
                break

        print(f"  LangGraph %:    {langgraph_pct:>5.1f}% (target: {target_str}) {status}")
    else:
        print(f"  LangGraph %:    N/A (no decisions yet)")
    print()
    
    # LLM Planner Performance
    print("🎯 LLM Planner Performance")
    print(f"  Success:   {counts.get('planner_success', 0):>5}")
    print(f"  Failure:   {counts.get('planner_failure', 0):>5}")
    print(f"  5xx Error: {counts.get('planner_error_5xx', 0):>5}")
    print(f"  Total:     {counts.get('total_planner', 0):>5}")
    print()
    
    failure_rate = rates.get('failure_rate', 0)
    error_5xx_rate = rates.get('error_5xx_rate', 0)
    
    failure_status = "✅" if failure_rate < 5.0 else "❌"
    error_status = "✅" if error_5xx_rate < 1.0 else "❌"
    
    print(f"  Failure Rate: {failure_rate:>6.2f}% (target: < 5%) {failure_status}")
    print(f"  5xx Rate:     {error_5xx_rate:>6.2f}% (target: < 1%) {error_status}")
    
    total_planner = counts.get('total_planner', 0)
    if total_planner > 0:
        success_rate = (counts.get('planner_success', 0) / total_planner) * 100
        success_status = "✅" if success_rate >= 95.0 else "❌"
        print(f"  Success Rate: {success_rate:>6.2f}% (target: > 95%) {success_status}")
    print()
    
    # Latency
    print("⏱️  Latency")
    p50 = latency.get('p50_ms')
    p90 = latency.get('p90_ms')
    p95 = latency.get('p95_ms')
    p99 = latency.get('p99_ms')
    
    print(f"  P50: {p50 if p50 else 'N/A':>8} ms")
    print(f"  P90: {p90 if p90 else 'N/A':>8} ms")
    
    if p95:
        p95_status = "✅" if p95 < 30000 else "❌"
        print(f"  P95: {p95:>8.0f} ms (target: < 30000 ms) {p95_status}")
    else:
        print(f"  P95: {'N/A':>8} ms (target: < 30000 ms)")
    
    print(f"  P99: {p99 if p99 else 'N/A':>8} ms")
    print()
    
    # Data Collection Progress
    print("📈 Data Collection Progress")
    print(f"  Total LLM Planner Calls: {total_planner}")
    print(f"  Target for Phase 2: 50+")
    if total_planner >= 50:
        print(f"  Status: ✅ Ready for Phase 2 evaluation")
    elif total_planner > 0:
        remaining = 50 - total_planner
        print(f"  Status: ⚠️ Need {remaining} more calls")
    else:
        print(f"  Status: ⚠️ No data yet - waiting for LLM Planner calls")
    print()
    
    # SLO Status
    print("✅ SLO Status")
    slo_pass = True
    
    if total_planner < 5:
        print(f"  ⚠️ Insufficient data for SLO evaluation (need 5+ calls)")
        slo_pass = False
    else:
        if failure_rate > 5.0:
            print(f"  ❌ Failure rate too high: {failure_rate:.2f}%")
            slo_pass = False
        else:
            print(f"  ✅ Failure rate OK: {failure_rate:.2f}%")
        
        if error_5xx_rate > 1.0:
            print(f"  ❌ 5xx rate too high: {error_5xx_rate:.2f}%")
            slo_pass = False
        else:
            print(f"  ✅ 5xx rate OK: {error_5xx_rate:.2f}%")
        
        if p95 and p95 > 30000:
            print(f"  ❌ P95 latency too high: {p95:.0f} ms")
            slo_pass = False
        elif p95:
            print(f"  ✅ P95 latency OK: {p95:.0f} ms")
        else:
            print(f"  ⚠️ P95 latency: No data")
    
    print()
    if slo_pass and total_planner >= 5:
        print("🎉 All SLOs passing!")
    elif total_planner < 5:
        print("⚠️ Insufficient data for SLO evaluation")
    else:
        print("⚠️ Some SLOs failing - investigate!")
    
    print("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(description='Display Phase 1 Canary Dashboard')
    parser.add_argument('--window', type=int, default=15,
                        help='Time window in minutes (default: 15)')
    args = parser.parse_args()
    
    success = display_dashboard(window_minutes=args.window)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
