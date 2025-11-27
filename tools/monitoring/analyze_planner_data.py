#!/usr/bin/env python3
"""
Analyze JSONL planner data for Phase 2 readiness

Usage:
    python analyze_planner_data.py [JSONL_PATH]

Example:
    python analyze_planner_data.py /path/to/planner_runs.jsonl
"""
import json
import sys
import os
from datetime import datetime
from collections import defaultdict


def analyze_planner_data(jsonl_path):
    """Analyze planner runs from JSONL file"""
    
    if not os.path.exists(jsonl_path):
        print(f"Error: File not found: {jsonl_path}")
        return False
    
    data = []
    try:
        with open(jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    if not data:
        print("=" * 60)
        print("Phase 1 JSONL Data Analysis")
        print("=" * 60)
        print()
        print("❌ No data found in JSONL file")
        print()
        print("This is expected if:")
        print("  1. No LLM Planner calls have been made yet")
        print("  2. The canary is still at 5% and waiting for traffic")
        print("  3. All recent calls used Simple mode (not LangGraph)")
        print()
        print("Next steps:")
        print("  - Wait for more Staging traffic")
        print("  - Run manual tests with LangGraph mode")
        print("  - Check that USE_LANGGRAPH_PERCENT=5 is set")
        print("=" * 60)
        return False
    
    print("=" * 60)
    print(f"Phase 1 JSONL Data Analysis - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)
    print()
    
    print(f"📊 Total LLM Planner Calls: {len(data)}")
    print()
    
    # Success rate
    successes = sum(1 for d in data if d.get('success'))
    failures = len(data) - successes
    success_rate = (successes / len(data)) * 100
    
    print(f"🎯 Success Rate")
    print(f"  Successes: {successes}")
    print(f"  Failures:  {failures}")
    print(f"  Rate:      {success_rate:.2f}%")
    
    if success_rate >= 95:
        print(f"  Status:    ✅ Meets target (> 95%)")
    else:
        print(f"  Status:    ❌ Below target (> 95%)")
    print()
    
    # Planning time statistics
    times = [d.get('planning_time_seconds', 0) for d in data if d.get('planning_time_seconds')]
    if times:
        times_sorted = sorted(times)
        print(f"⏱️  Planning Time")
        print(f"  Min:    {min(times):>8.2f}s")
        print(f"  Max:    {max(times):>8.2f}s")
        print(f"  Avg:    {sum(times)/len(times):>8.2f}s")
        print(f"  Median: {times_sorted[len(times_sorted)//2]:>8.2f}s")
        print(f"  P95:    {times_sorted[int(len(times_sorted)*0.95)]:>8.2f}s")
        
        avg_time = sum(times)/len(times)
        if avg_time < 30:
            print(f"  Status: ✅ Acceptable (< 30s)")
        else:
            print(f"  Status: ⚠️ High (> 30s)")
    else:
        print(f"⏱️  Planning Time: No data")
    print()
    
    # Cost analysis
    costs = [d.get('cost_usd', 0) for d in data if d.get('cost_usd')]
    if costs:
        total_cost = sum(costs)
        avg_cost = total_cost / len(costs)
        print(f"💰 Cost Analysis")
        print(f"  Total Cost:        ${total_cost:>8.4f}")
        print(f"  Average per Call:  ${avg_cost:>8.4f}")
        print()
        print(f"  Projected Daily Cost:")
        print(f"    Staging (5%):    ${avg_cost * 5:>8.4f} (~5 calls/day)")
        print(f"    Production (5%): ${avg_cost * 50:>8.4f} (~50 calls/day)")
        print()
        print(f"  Projected Monthly Cost:")
        print(f"    Staging (5%):    ${avg_cost * 5 * 30:>8.2f}")
        print(f"    Production (5%): ${avg_cost * 50 * 30:>8.2f}")
        
        if avg_cost <= 0.05:
            print(f"  Status: ✅ Cost acceptable (< $0.05/call)")
        else:
            print(f"  Status: ⚠️ Cost high (> $0.05/call)")
    else:
        print(f"💰 Cost Analysis: No cost data available")
        print(f"  Note: Cost tracking may not be implemented yet")
    print()
    
    # Plan steps distribution
    steps = [d.get('plan_steps', 0) for d in data if d.get('plan_steps')]
    if steps:
        print(f"📋 Plan Steps Distribution")
        print(f"  Min: {min(steps)}")
        print(f"  Max: {max(steps)}")
        print(f"  Avg: {sum(steps)/len(steps):.1f}")
        
        # Count by step number
        step_counts = defaultdict(int)
        for s in steps:
            step_counts[s] += 1
        
        print(f"  Distribution:")
        for step_num in sorted(step_counts.keys()):
            count = step_counts[step_num]
            pct = (count / len(steps)) * 100
            bar = "█" * int(pct / 5)
            print(f"    {step_num} steps: {count:>3} ({pct:>5.1f}%) {bar}")
    else:
        print(f"📋 Plan Steps: No data")
    print()
    
    # Timeline analysis
    timestamps = [d.get('timestamp') for d in data if d.get('timestamp')]
    if timestamps:
        timestamps_sorted = sorted(timestamps)
        first = datetime.fromisoformat(timestamps_sorted[0].replace('Z', '+00:00'))
        last = datetime.fromisoformat(timestamps_sorted[-1].replace('Z', '+00:00'))
        duration = (last - first).total_seconds() / 3600  # hours
        
        print(f"📅 Timeline")
        print(f"  First Call: {first.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Last Call:  {last.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Duration:   {duration:.1f} hours")
        if duration > 0:
            calls_per_hour = len(data) / duration
            print(f"  Rate:       {calls_per_hour:.2f} calls/hour")
    print()
    
    # Phase 2 readiness
    print("=" * 60)
    print("🎯 Phase 2 Readiness Assessment")
    print("=" * 60)
    print()
    
    ready_count = 0
    total_criteria = 4
    
    # Criterion 1: Data collection
    if len(data) >= 50:
        print(f"✅ Data collection: {len(data)}/50 calls")
        ready_count += 1
    else:
        remaining = 50 - len(data)
        print(f"⚠️ Data collection: {len(data)}/50 calls (need {remaining} more)")
    
    # Criterion 2: Success rate
    if success_rate >= 95:
        print(f"✅ Success rate: {success_rate:.2f}% (target: > 95%)")
        ready_count += 1
    else:
        print(f"❌ Success rate: {success_rate:.2f}% (target: > 95%)")
    
    # Criterion 3: Cost
    if costs and avg_cost <= 0.05:
        print(f"✅ Cost per call: ${avg_cost:.4f} (target: < $0.05)")
        ready_count += 1
    elif costs:
        print(f"⚠️ Cost per call: ${avg_cost:.4f} (target: < $0.05)")
    else:
        print(f"⚠️ Cost per call: No data (target: < $0.05)")
    
    # Criterion 4: Latency
    if times and sum(times)/len(times) < 30:
        print(f"✅ Avg latency: {sum(times)/len(times):.2f}s (target: < 30s)")
        ready_count += 1
    elif times:
        print(f"⚠️ Avg latency: {sum(times)/len(times):.2f}s (target: < 30s)")
    else:
        print(f"⚠️ Avg latency: No data (target: < 30s)")
    
    print()
    print(f"Overall: {ready_count}/{total_criteria} criteria met")
    print()
    
    if ready_count == total_criteria:
        print("🎉 Phase 2 READY - All criteria met!")
    elif ready_count >= 3:
        print("⚠️ Phase 2 ALMOST READY - Most criteria met")
    else:
        print("❌ Phase 2 NOT READY - More data/improvements needed")
    
    print("=" * 60)
    return True


def main():
    if len(sys.argv) > 1:
        jsonl_path = sys.argv[1]
    else:
        # Default path
        jsonl_path = '/home/ubuntu/repos/morningai/tools/agent_eval/data/planner_runs.jsonl'
    
    success = analyze_planner_data(jsonl_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
