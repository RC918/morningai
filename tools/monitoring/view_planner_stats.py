#!/usr/bin/env python3
"""
View planner_runs.jsonl statistics

Simple CLI tool to view statistics from planner_runs.jsonl file.
Designed for internal/admin use on staging and production environments.

Usage:
    # View all statistics
    python tools/monitoring/view_planner_stats.py

    # Show last N entries
    python tools/monitoring/view_planner_stats.py --last 10

    # Use custom file path
    python tools/monitoring/view_planner_stats.py --file /path/to/planner_runs.jsonl

    # Filter by Phase 1 tasks
    python tools/monitoring/view_planner_stats.py --filter "[Phase1-Test]"

Environment Variables:
    PLANNER_EVENTS_FILE: Override default planner_runs.jsonl path
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional


def find_git_root(start_dir: str) -> Optional[str]:
    """
    Find git repository root by searching for .git directory

    Args:
        start_dir: Directory to start searching from

    Returns:
        Path to git root, or None if not found
    """
    current = start_dir
    while current != '/' and not os.path.exists(os.path.join(current, '.git')):
        current = os.path.dirname(current)
    return current if os.path.exists(os.path.join(current, '.git')) else None


def resolve_planner_events_path() -> str:
    """
    Resolve planner_runs.jsonl path using same logic as LLMPlannerAdapter

    Returns:
        Absolute path to planner_runs.jsonl file
    """
    events_file = os.environ.get('PLANNER_EVENTS_FILE', 'tools/agent_eval/data/planner_runs.jsonl')

    # If absolute path, use as-is
    if os.path.isabs(events_file):
        return events_file

    # Find git root
    cwd = os.getcwd()
    repo_root = find_git_root(cwd)

    if not repo_root:
        # Try from script location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = find_git_root(current_dir)

        if not repo_root:
            # Fallback: assume cwd is repo root or contains morningai
            if os.path.basename(cwd) == 'morningai' or os.path.basename(os.path.dirname(cwd)) == 'morningai':
                repo_root = cwd if os.path.basename(cwd) == 'morningai' else os.path.dirname(cwd)
            else:
                repo_root = current_dir

    return os.path.join(repo_root, events_file)


def load_planner_events(file_path: str, filter_goal: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load planner events from JSONL file (streaming, line-by-line)

    Args:
        file_path: Path to planner_runs.jsonl file
        filter_goal: Optional substring to filter goals by

    Returns:
        List of planner event dictionaries
    """
    events = []

    if not os.path.exists(file_path):
        return events

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)

                    # Apply filter if specified
                    if filter_goal and filter_goal not in event.get('goal', ''):
                        continue

                    events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return []

    return events


def compute_statistics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics from planner events

    Args:
        events: List of planner event dictionaries

    Returns:
        Dictionary of computed statistics
    """
    if not events:
        return {}

    # Extract metrics
    planning_times = []
    step_counts = defaultdict(int)
    planner_types = defaultdict(int)
    task_types = defaultdict(int)
    timestamps = []

    for event in events:
        # Planning time (convert ms to seconds)
        if 'planning_time_ms' in event:
            planning_times.append(event['planning_time_ms'] / 1000.0)

        # Step counts
        num_steps = event.get('num_steps', 0)
        if num_steps > 0:
            step_counts[num_steps] += 1

        # Planner types
        planner_type = event.get('planner_type', 'unknown')
        planner_types[planner_type] += 1

        # Task types
        task_type = event.get('task_type', 'unknown')
        task_types[task_type] += 1

        # Timestamps
        if 'timestamp' in event:
            timestamps.append(event['timestamp'])

    # Compute statistics
    stats = {
        'total_count': len(events),
        'planning_times': planning_times,
        'step_counts': dict(step_counts),
        'planner_types': dict(planner_types),
        'task_types': dict(task_types),
        'timestamps': timestamps
    }

    # Time statistics
    if planning_times:
        sorted_times = sorted(planning_times)
        stats['time_min'] = min(planning_times)
        stats['time_max'] = max(planning_times)
        stats['time_mean'] = sum(planning_times) / len(planning_times)
        stats['time_median'] = sorted_times[len(sorted_times) // 2]
        stats['time_p95'] = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]

    # Timeline
    if timestamps:
        sorted_timestamps = sorted(timestamps)
        stats['first_timestamp'] = sorted_timestamps[0]
        stats['last_timestamp'] = sorted_timestamps[-1]

    return stats


def format_statistics(stats: Dict[str, Any], file_path: str) -> str:
    """
    Format statistics as human-readable string

    Args:
        stats: Statistics dictionary from compute_statistics
        file_path: Path to the planner_runs.jsonl file

    Returns:
        Formatted statistics string
    """
    if not stats:
        return f"""
{'=' * 70}
Planner Statistics
{'=' * 70}

File: {file_path}

❌ No planner events found

This may indicate:
  - No LLM Planner calls have been made yet
  - The file doesn't exist or is empty
  - Canary routing is not sending traffic to LLM Planner

{'=' * 70}
"""

    lines = []
    lines.append('=' * 70)
    lines.append('Planner Statistics')
    lines.append('=' * 70)
    lines.append('')
    lines.append(f"File: {file_path}")
    lines.append('')

    # Total count
    lines.append(f"📊 Total Planner Runs: {stats['total_count']}")
    lines.append('')

    # Timeline
    if 'first_timestamp' in stats:
        try:
            first = datetime.fromisoformat(stats['first_timestamp'].replace('Z', '+00:00'))
            last = datetime.fromisoformat(stats['last_timestamp'].replace('Z', '+00:00'))
            duration_hours = (last - first).total_seconds() / 3600

            lines.append('📅 Timeline')
            lines.append(f"  First: {first.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            lines.append(f"  Last:  {last.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            lines.append(f"  Duration: {duration_hours:.1f} hours")
            if duration_hours > 0:
                rate = stats['total_count'] / duration_hours
                lines.append(f"  Rate: {rate:.2f} runs/hour")
        except Exception as e:
            lines.append(f'📅 Timeline: Error parsing timestamps ({e})')
        lines.append('')

    # Planning time statistics
    if 'time_min' in stats:
        lines.append('⏱️  Planning Time')
        lines.append(f"  Min:    {stats['time_min']:>8.2f}s")
        lines.append(f"  Median: {stats['time_median']:>8.2f}s")
        lines.append(f"  Mean:   {stats['time_mean']:>8.2f}s")
        lines.append(f"  P95:    {stats['time_p95']:>8.2f}s")
        lines.append(f"  Max:    {stats['time_max']:>8.2f}s")

        if stats['time_mean'] < 30:
            lines.append("  Status: ✅ Acceptable (< 30s target)")
        else:
            lines.append("  Status: ⚠️  High (> 30s target)")
        lines.append('')

    # Step distribution
    if stats['step_counts']:
        lines.append('📋 Plan Steps Distribution')
        total_with_steps = sum(stats['step_counts'].values())
        for num_steps in sorted(stats['step_counts'].keys()):
            count = stats['step_counts'][num_steps]
            pct = (count / total_with_steps) * 100
            bar = '█' * int(pct / 5)
            lines.append(f"  {num_steps} steps: {count:>3} ({pct:>5.1f}%) {bar}")
        lines.append('')

    # Planner type distribution
    if stats['planner_types']:
        lines.append('🤖 Planner Type Distribution')
        for planner_type, count in sorted(stats['planner_types'].items(), key=lambda x: -x[1]):
            pct = (count / stats['total_count']) * 100
            lines.append(f"  {planner_type}: {count:>3} ({pct:>5.1f}%)")
        lines.append('')

    # Task type distribution (top 10)
    if stats['task_types']:
        lines.append('📝 Task Type Distribution (Top 10)')
        sorted_task_types = sorted(stats['task_types'].items(), key=lambda x: -x[1])[:10]
        for task_type, count in sorted_task_types:
            pct = (count / stats['total_count']) * 100
            lines.append(f"  {task_type}: {count:>3} ({pct:>5.1f}%)")
        lines.append('')

    lines.append('=' * 70)

    return '\n'.join(lines)


def show_recent_entries(events: List[Dict[str, Any]], count: int) -> str:
    """
    Format recent planner entries

    Args:
        events: List of planner event dictionaries
        count: Number of recent entries to show

    Returns:
        Formatted string of recent entries
    """
    if not events:
        return "No entries to display"

    # Get last N entries
    recent = events[-count:] if len(events) > count else events

    lines = []
    lines.append('')
    lines.append(f"📜 Last {len(recent)} Entries")
    lines.append('=' * 70)

    for i, event in enumerate(reversed(recent), 1):
        timestamp = event.get('timestamp', 'N/A')
        trace_id = event.get('trace_id', 'N/A')
        num_steps = event.get('num_steps', 0)
        planning_time = event.get('planning_time_ms', 0) / 1000.0
        planner_type = event.get('planner_type', 'unknown')
        goal = event.get('goal', '')

        # Truncate goal to 60 chars
        goal_truncated = goal[:60] + '...' if len(goal) > 60 else goal

        lines.append(f"\n{i}. {timestamp}")
        lines.append(f"   Trace ID: {trace_id}")
        lines.append(f"   Planner: {planner_type} | Steps: {num_steps} | Time: {planning_time:.2f}s")
        lines.append(f"   Goal: {goal_truncated}")

    lines.append('')
    lines.append('=' * 70)

    return '\n'.join(lines)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='View planner_runs.jsonl statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--file',
        type=str,
        help='Path to planner_runs.jsonl file (default: auto-detect using PLANNER_EVENTS_FILE or repo root)'
    )

    parser.add_argument(
        '--last',
        type=int,
        metavar='N',
        help='Show last N entries with details'
    )

    parser.add_argument(
        '--filter',
        type=str,
        metavar='TEXT',
        help='Filter entries by goal substring (e.g., "[Phase1-Test]")'
    )

    args = parser.parse_args()

    # Resolve file path
    if args.file:
        file_path = args.file
    else:
        file_path = resolve_planner_events_path()

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        print("\nTip: Set PLANNER_EVENTS_FILE environment variable or use --file option", file=sys.stderr)
        sys.exit(1)

    # Load events
    events = load_planner_events(file_path, filter_goal=args.filter)

    # Compute and display statistics
    stats = compute_statistics(events)
    print(format_statistics(stats, file_path))

    # Show recent entries if requested
    if args.last and events:
        print(show_recent_entries(events, args.last))

    sys.exit(0)


if __name__ == '__main__':
    main()
