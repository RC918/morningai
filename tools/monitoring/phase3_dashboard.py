#!/usr/bin/env python3
"""
Phase 3 Dashboard - Display ProjectEngineerAgent metrics

Usage:
    python phase3_dashboard.py [--window MINUTES]

Example:
    python phase3_dashboard.py --window 15
"""
import os
import sys
import argparse
import redis
from datetime import datetime

# Add orchestrator to path
sys.path.insert(0, '/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator')

try:
    from phase3_metrics import create_phase3_metrics
except ImportError as e:
    print("Error: Failed to import phase3_metrics module: %s" % e)
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def display_dashboard(window_minutes=15):
    """Display current Phase 3 metrics"""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("Error: REDIS_URL environment variable not set")
        print("Please set REDIS_URL before running this script")
        return False

    try:
        r = redis.from_url(redis_url)
        metrics = create_phase3_metrics(r, enabled=True)
    except Exception as e:
        print("Error: Failed to connect to Redis: %s" % e)
        return False

    # Get summary
    try:
        summary = metrics.get_phase3_summary(window_minutes=window_minutes)
    except Exception as e:
        print("Error: Failed to get Phase 3 summary: %s" % e)
        return False

    print("=" * 70)
    print("Phase 3 Dashboard - ProjectEngineerAgent Metrics")
    print("Time: %s UTC" % datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    print("Window: Last %d minutes" % window_minutes)
    print("=" * 70)
    print()

    if not summary.get('enabled'):
        print("Phase 3 metrics disabled")
        return False

    if summary.get('error'):
        print("Error: %s" % summary.get('error'))
        return False

    counts = summary.get('counts', {})
    rates = summary.get('rates', {})
    latency = summary.get('latency', {})
    violations = summary.get('rule_violations', {})

    # Task Execution Summary
    print("Task Execution Summary")
    print("-" * 40)
    print("  Success:   %5d" % counts.get('task_success', 0))
    print("  Failed:    %5d" % counts.get('task_failed', 0))
    print("  Timeout:   %5d" % counts.get('task_timeout', 0))
    print("  Skipped:   %5d" % counts.get('task_skipped', 0))
    print("  Total:     %5d" % counts.get('total_tasks', 0))
    print()

    # Success Rate
    total_tasks = counts.get('total_tasks', 0)
    success_rate = rates.get('success_rate', 0)
    failure_rate = rates.get('failure_rate', 0)
    timeout_rate = rates.get('timeout_rate', 0)

    if total_tasks > 0:
        if success_rate >= 95.0:
            success_status = "PASS"
        elif success_rate >= 80.0:
            success_status = "WARN"
        else:
            success_status = "FAIL"

        if failure_rate < 5.0:
            failure_status = "PASS"
        elif failure_rate < 15.0:
            failure_status = "WARN"
        else:
            failure_status = "FAIL"

        if timeout_rate < 2.0:
            timeout_status = "PASS"
        elif timeout_rate < 5.0:
            timeout_status = "WARN"
        else:
            timeout_status = "FAIL"

        print("  Success Rate: %6.2f%% (target: > 95%%) [%s]" % (
            success_rate, success_status))
        print("  Failure Rate: %6.2f%% (target: < 5%%)  [%s]" % (
            failure_rate, failure_status))
        print("  Timeout Rate: %6.2f%% (target: < 2%%)  [%s]" % (
            timeout_rate, timeout_status))
    else:
        print("  No tasks executed yet")
    print()

    # Execution Mode Distribution
    print("Execution Mode Distribution")
    print("-" * 40)
    mode_analysis = counts.get('mode_analysis', 0)
    mode_execution = counts.get('mode_execution', 0)
    total_mode = mode_analysis + mode_execution

    print("  Analysis Only: %5d" % mode_analysis)
    print("  Execution:     %5d" % mode_execution)
    if total_mode > 0:
        exec_pct = (mode_execution / total_mode) * 100
        print("  Execution %%:   %5.1f%%" % exec_pct)
    print()

    # Latency
    print("Latency (milliseconds)")
    print("-" * 40)
    p50 = latency.get('p50_ms')
    p90 = latency.get('p90_ms')
    p95 = latency.get('p95_ms')
    p99 = latency.get('p99_ms')

    print("  P50: %10s ms" % (p50 if p50 else 'N/A'))
    print("  P90: %10s ms" % (p90 if p90 else 'N/A'))

    if p95:
        # Phase 3 tasks are longer, target is 5 minutes (300000ms)
        if p95 < 300000:
            p95_status = "PASS"
        elif p95 < 600000:
            p95_status = "WARN"
        else:
            p95_status = "FAIL"
        print("  P95: %10.0f ms (target: < 300000 ms) [%s]" % (p95, p95_status))
    else:
        print("  P95: %10s ms (target: < 300000 ms)" % 'N/A')

    print("  P99: %10s ms" % (p99 if p99 else 'N/A'))
    print()

    # Semantic Rule Violations
    print("Semantic Rule Violations")
    print("-" * 40)
    rule_repo = violations.get('repo_whitelist', 0)
    rule_directory = violations.get('directory_whitelist', 0)
    rule_task_type = violations.get('task_type_whitelist', 0)
    # Phase 1 Security Foundation: New rule types
    rule_action = violations.get('action', 0)
    rule_sensitive_file = violations.get('sensitive_file', 0)
    rule_high_risk = violations.get('high_risk', 0)
    rule_path_traversal = violations.get('path_traversal', 0)
    total_violations = counts.get('rule_violations', 0)

    if total_violations == 0:
        violation_status = "PASS"
    elif total_violations < 5:
        violation_status = "WARN"
    else:
        violation_status = "FAIL"

    print("  Repo Whitelist:      %5d" % rule_repo)
    print("  Directory Whitelist: %5d" % rule_directory)
    print("  Task Type Whitelist: %5d" % rule_task_type)
    print("  Action Whitelist:    %5d" % rule_action)
    print("  Sensitive File:      %5d" % rule_sensitive_file)
    print("  High Risk:           %5d" % rule_high_risk)
    print("  Path Traversal:      %5d" % rule_path_traversal)
    print("  Total Violations:    %5d [%s]" % (total_violations, violation_status))
    print()

    # Phase 1 Security Foundation: Security Events
    security = summary.get('security', {})
    print("Phase 1 Security Foundation")
    print("-" * 40)
    security_violations = security.get('violations_total', 0)
    high_risk_blocked = security.get('high_risk_blocked', 0)
    sensitive_file_blocked = security.get('sensitive_file_blocked', 0)
    hitl_required = security.get('hitl_required', 0)
    events_blocked = security.get('events_blocked', 0)
    events_allowed = security.get('events_allowed', 0)

    if security_violations == 0 and high_risk_blocked == 0:
        security_status = "PASS"
    elif security_violations < 3:
        security_status = "WARN"
    else:
        security_status = "FAIL"

    print("  Security Violations: %5d [%s]" % (security_violations, security_status))
    print("  High Risk Blocked:   %5d" % high_risk_blocked)
    print("  Sensitive Files:     %5d" % sensitive_file_blocked)
    print("  HITL Required:       %5d" % hitl_required)
    print("  Events Blocked:      %5d" % events_blocked)
    print("  Events Allowed:      %5d" % events_allowed)
    print()

    # SLO Status Summary
    print("SLO Status Summary")
    print("-" * 40)
    slo_pass = True

    if total_tasks < 5:
        print("  Insufficient data for SLO evaluation (need 5+ tasks)")
        slo_pass = False
    else:
        if success_rate < 95.0:
            print("  [FAIL] Success rate too low: %.2f%%" % success_rate)
            slo_pass = False
        else:
            print("  [PASS] Success rate OK: %.2f%%" % success_rate)

        if failure_rate > 5.0:
            print("  [FAIL] Failure rate too high: %.2f%%" % failure_rate)
            slo_pass = False
        else:
            print("  [PASS] Failure rate OK: %.2f%%" % failure_rate)

        if timeout_rate > 2.0:
            print("  [WARN] Timeout rate elevated: %.2f%%" % timeout_rate)
        else:
            print("  [PASS] Timeout rate OK: %.2f%%" % timeout_rate)

        if total_violations > 0:
            print("  [WARN] Rule violations detected: %d" % total_violations)
        else:
            print("  [PASS] No rule violations")

        if p95 and p95 > 300000:
            print("  [WARN] P95 latency high: %.0f ms" % p95)
        elif p95:
            print("  [PASS] P95 latency OK: %.0f ms" % p95)

    print()
    if slo_pass and total_tasks >= 5:
        print("All SLOs passing!")
    elif total_tasks < 5:
        print("Insufficient data for SLO evaluation")
    else:
        print("Some SLOs failing - investigate!")

    print("=" * 70)
    return True


def main():
    parser = argparse.ArgumentParser(description='Display Phase 3 Dashboard')
    parser.add_argument('--window', type=int, default=15,
                        help='Time window in minutes (default: 15)')
    args = parser.parse_args()

    success = display_dashboard(window_minutes=args.window)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
