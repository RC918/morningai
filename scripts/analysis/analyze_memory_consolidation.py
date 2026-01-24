#!/usr/bin/env python3
"""
Memory Consolidation Log Analyzer

EPIC G-2: Memory Consolidation Analysis Tool
Issue: Part of Memory Consolidation evaluation

This script analyzes Memory Consolidation dry run logs to help evaluate:
1. How many memories are being scanned
2. How many reach the importance threshold
3. Distribution of memory types
4. Summarization latency

Usage:
    # Analyze logs from file
    python scripts/analysis/analyze_memory_consolidation.py --log-file /path/to/worker.log

    # Analyze logs from stdin (pipe from Render logs)
    render logs morningai-agent-worker | python scripts/analysis/analyze_memory_consolidation.py

    # Generate test data for evaluation (requires PYTHONPATH setup)
    PYTHONPATH=handoff/20250928/40_App/orchestrator:$PYTHONPATH \\
        python scripts/analysis/analyze_memory_consolidation.py --generate-test-data

    # Run a manual consolidation test (requires PYTHONPATH setup)
    PYTHONPATH=handoff/20250928/40_App/orchestrator:$PYTHONPATH \\
        python scripts/analysis/analyze_memory_consolidation.py --run-test
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TextIO

SCRIPT_VERSION = "1.0.0"

SCORE_THRESHOLD_HIGH = 0.8
SCORE_THRESHOLD_MEDIUM = 0.6
SCORE_THRESHOLD_LOW = 0.5


@dataclass
class ConsolidationRun:
    """Represents a single consolidation run"""
    run_id: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    memories_scanned: int = 0
    memories_evaluated: int = 0
    memories_consolidated: int = 0
    memories_skipped: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    dry_run_entries: List[Dict] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Analysis result summary"""
    total_runs: int = 0
    total_scanned: int = 0
    total_evaluated: int = 0
    total_consolidated: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    memory_type_distribution: Dict[str, int] = field(default_factory=dict)
    score_distribution: Dict[str, int] = field(default_factory=dict)
    runs: List[ConsolidationRun] = field(default_factory=list)


class MemoryConsolidationLogAnalyzer:
    """Analyzes Memory Consolidation logs"""

    PATTERNS = {
        "run_start": re.compile(
            r"\[Consolidation\] Starting run (consolidation_\d+_\d+)"
        ),
        "scanned": re.compile(
            r"\[Consolidation\] Scanned (\d+) expiring memories"
        ),
        "important": re.compile(
            r"\[Consolidation\] Found (\d+) important memories"
        ),
        "completed": re.compile(
            r"\[Consolidation\] Completed run (consolidation_\d+_\d+): "
            r"consolidated=(\d+), skipped=(\d+), errors=(\d+)"
        ),
        "dry_run": re.compile(
            r"\[Consolidation\] DRY RUN - Would consolidate: ([^\s]+) "
            r"\(score=([\d.]+), type=(\w+)\)"
        ),
        "scheduler_start": re.compile(
            r"Memory consolidation scheduler started "
            r"\(interval=([\d.]+)h, threshold=([\d.]+), dry_run=(\w+)\)"
        ),
    }

    def __init__(self):
        self.current_run: Optional[ConsolidationRun] = None
        self.runs: List[ConsolidationRun] = []

    def parse_line(self, line: str) -> None:
        """Parse a single log line"""
        if match := self.PATTERNS["run_start"].search(line):
            if self.current_run:
                self.runs.append(self.current_run)
            self.current_run = ConsolidationRun(run_id=match.group(1))

        elif match := self.PATTERNS["scanned"].search(line):
            if self.current_run:
                self.current_run.memories_scanned = int(match.group(1))

        elif match := self.PATTERNS["important"].search(line):
            if self.current_run:
                self.current_run.memories_evaluated = int(match.group(1))

        elif match := self.PATTERNS["completed"].search(line):
            if self.current_run:
                self.current_run.memories_consolidated = int(match.group(2))
                self.current_run.memories_skipped = int(match.group(3))
                self.current_run.error_count = int(match.group(4))
                self.runs.append(self.current_run)
                self.current_run = None

        elif match := self.PATTERNS["dry_run"].search(line):
            if self.current_run:
                self.current_run.dry_run_entries.append({
                    "key": match.group(1),
                    "score": float(match.group(2)),
                    "type": match.group(3),
                })

    def analyze(self, input_stream: TextIO) -> AnalysisResult:
        """Analyze log stream and return results"""
        for line in input_stream:
            self.parse_line(line)

        if self.current_run:
            self.runs.append(self.current_run)

        result = AnalysisResult(
            total_runs=len(self.runs),
            runs=self.runs,
        )

        memory_types: Dict[str, int] = defaultdict(int)
        score_buckets: Dict[str, int] = defaultdict(int)

        for run in self.runs:
            result.total_scanned += run.memories_scanned
            result.total_evaluated += run.memories_evaluated
            result.total_consolidated += run.memories_consolidated
            result.total_skipped += run.memories_skipped
            result.total_errors += run.error_count

            for entry in run.dry_run_entries:
                memory_types[entry["type"]] += 1
                score = entry["score"]
                if score >= SCORE_THRESHOLD_HIGH:
                    score_buckets["0.8-1.0 (high)"] += 1
                elif score >= SCORE_THRESHOLD_MEDIUM:
                    score_buckets["0.6-0.8 (medium-high)"] += 1
                elif score >= SCORE_THRESHOLD_LOW:
                    score_buckets["0.5-0.6 (threshold)"] += 1
                else:
                    score_buckets["<0.5 (below threshold)"] += 1

        result.memory_type_distribution = dict(memory_types)
        result.score_distribution = dict(score_buckets)

        return result

    def print_report(self, result: AnalysisResult) -> None:
        """Print analysis report"""
        print("\n" + "=" * 60)
        print("Memory Consolidation Analysis Report")
        print("=" * 60)

        print(f"\nTotal Runs Analyzed: {result.total_runs}")

        if result.total_runs == 0:
            print("\nNo consolidation runs found in logs.")
            print("\nPossible reasons:")
            print("  1. ENABLE_MEMORY_CONSOLIDATION is not set to TRUE")
            print("  2. No memories have been created in Agent Interaction Memory")
            print("  3. Scheduler hasn't run yet (default interval: 6 hours)")
            print("\nTo generate test data, run:")
            print("  python scripts/analysis/analyze_memory_consolidation.py --run-test")
            return

        print(f"\nMemory Statistics:")
        print(f"  Total Scanned:      {result.total_scanned}")
        print(f"  Total Evaluated:    {result.total_evaluated}")
        print(f"  Total Consolidated: {result.total_consolidated}")
        print(f"  Total Skipped:      {result.total_skipped}")
        print(f"  Total Errors:       {result.total_errors}")

        if result.total_scanned > 0:
            consolidation_rate = (
                result.total_consolidated / result.total_scanned * 100
            )
            print(f"\n  Consolidation Rate: {consolidation_rate:.1f}%")

        if result.memory_type_distribution:
            print("\nMemory Type Distribution:")
            for mem_type, count in sorted(
                result.memory_type_distribution.items(),
                key=lambda x: -x[1]
            ):
                print(f"  {mem_type}: {count}")

        if result.score_distribution:
            print("\nImportance Score Distribution:")
            for bucket, count in sorted(result.score_distribution.items()):
                print(f"  {bucket}: {count}")

        print("\n" + "-" * 60)
        print("Recommendation:")
        if result.total_consolidated > 0:
            if result.total_consolidated / max(result.total_scanned, 1) > 0.1:
                print("  Memory consolidation is capturing valuable memories.")
                print("  Consider switching from dry_run to actual write mode.")
            else:
                print("  Low consolidation rate. Consider:")
                print("  - Lowering MEMORY_CONSOLIDATION_THRESHOLD")
                print("  - Checking if memories have proper metadata")
        else:
            print("  No memories consolidated. Check:")
            print("  - Are memories being created with proper metadata?")
            print("  - Is the importance threshold too high?")
        print("=" * 60 + "\n")


def generate_test_data():
    """Generate test memory data for consolidation evaluation"""
    print("\nGenerating test data for Memory Consolidation evaluation...")

    try:
        from memory.memory_v2 import (
            MemoryEntry,
            MemoryLayer,
            MemoryScope,
            get_memory_v2,
        )

        memory = get_memory_v2()
        if memory is None:
            print("Error: Memory v2 not available. Check ENABLE_MEMORY_V2 setting.")
            return

        test_memories = [
            {
                "key": "test:debate:security_review_001",
                "content": "Debate result: Security review for PR #1234. "
                          "Left agent argued for strict input validation, "
                          "Right agent suggested rate limiting. "
                          "Consensus: Implement both with priority on validation.",
                "metadata": {
                    "debate_confidence": 0.85,
                    "outcome_impact": 0.9,
                    "memory_type": "debate_insight",
                    "pr_number": 1234,
                },
            },
            {
                "key": "test:error_fix:ci_failure_001",
                "content": "CI failure fix: TypeError in auth_service.py line 45. "
                          "Root cause: None check missing before .get() call. "
                          "Solution: Added 'if user is not None' guard.",
                "metadata": {
                    "outcome_impact": 0.8,
                    "severity": "high",
                    "memory_type": "error_fix_pair",
                    "file": "auth_service.py",
                },
            },
            {
                "key": "test:routing:provider_fallback_001",
                "content": "Routing decision: Gemini API timeout (>60s), "
                          "triggered cross-provider fallback to AliCloud qwen-max. "
                          "Task completed successfully with 2.3s latency.",
                "metadata": {
                    "outcome_impact": 0.7,
                    "memory_type": "routing_decision",
                    "original_provider": "gemini",
                    "fallback_provider": "alicloud",
                },
            },
            {
                "key": "test:solution:code_pattern_001",
                "content": "Solution pattern: Implementing retry logic with exponential backoff. "
                          "Used in drift_retry.py. Pattern: base_delay * (2 ** attempt) "
                          "with jitter. Max retries: 3, max delay: 30s.",
                "metadata": {
                    "outcome_impact": 0.6,
                    "reference_count": 5,
                    "memory_type": "solution_pattern",
                },
            },
            {
                "key": "test:safety:prompt_injection_001",
                "content": "Safety pattern detected: Prompt injection attempt in user input. "
                          "Pattern: 'ignore previous instructions'. "
                          "Action: Sanitized input, logged security event.",
                "metadata": {
                    "outcome_impact": 1.0,
                    "severity": "critical",
                    "memory_type": "safety_pattern",
                },
            },
        ]

        print(f"\nCreating {len(test_memories)} test memories...")

        for mem_data in test_memories:
            entry = MemoryEntry(
                key=mem_data["key"],
                content=mem_data["content"],
                layer=MemoryLayer.AGENT_INTERACTION,
                scope=MemoryScope.GLOBAL,
                metadata=mem_data["metadata"],
                trace_id="test_trace_001",
            )

            success = memory.save(entry, layer=MemoryLayer.AGENT_INTERACTION)
            status = "created" if success else "failed"
            print(f"  {mem_data['key']}: {status}")

        print("\nTest data created successfully!")
        print("\nNext steps:")
        print("  1. Wait for consolidation scheduler to run (default: 6 hours)")
        print("  2. Or run manual test: python scripts/analysis/analyze_memory_consolidation.py --run-test")
        print("  3. Check logs for '[Consolidation] DRY RUN' entries")

    except ImportError as e:
        print(f"Error: Could not import memory module: {e}")
        print("Make sure you're running from the morningai repo root.")
    except Exception as e:
        print(f"Error generating test data: {e}")


def run_manual_test():
    """Run a manual consolidation test"""
    print("\nRunning manual Memory Consolidation test...")

    try:
        from memory.memory_consolidation import get_consolidation_job

        job = get_consolidation_job()
        if job is None:
            print("Error: Consolidation job not available.")
            print("Check ENABLE_MEMORY_CONSOLIDATION setting.")
            return

        print(f"\nConsolidation Job Configuration:")
        print(f"  Importance Threshold: {job.importance_threshold}")
        print(f"  Batch Size: {job.batch_size}")
        print(f"  Dry Run: {job.dry_run}")
        print(f"  Interval: {job.interval_hours} hours")

        print("\nRunning consolidation...")
        result = job.run()

        print(f"\nConsolidation Result:")
        print(f"  Run ID: {result.run_id}")
        print(f"  Memories Scanned: {result.memories_scanned}")
        print(f"  Memories Evaluated: {result.memories_evaluated}")
        print(f"  Memories Consolidated: {result.memories_consolidated}")
        print(f"  Memories Skipped: {result.memories_skipped}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Summarization Latency: {result.summarization_latency_ms:.2f}ms")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

    except ImportError as e:
        print(f"Error: Could not import consolidation module: {e}")
        print("Make sure you're running from the morningai repo root.")
    except Exception as e:
        print(f"Error running test: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Memory Consolidation logs"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file to analyze"
    )
    parser.add_argument(
        "--generate-test-data",
        action="store_true",
        help="Generate test memory data for evaluation"
    )
    parser.add_argument(
        "--run-test",
        action="store_true",
        help="Run a manual consolidation test"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    if args.generate_test_data:
        generate_test_data()
        return

    if args.run_test:
        run_manual_test()
        return

    analyzer = MemoryConsolidationLogAnalyzer()

    if args.log_file:
        with open(args.log_file, "r") as f:
            result = analyzer.analyze(f)
    else:
        if sys.stdin.isatty():
            print("Reading from stdin. Paste logs and press Ctrl+D when done.")
            print("Or use --log-file to specify a log file.")
            print("Or use --generate-test-data to create test memories.")
            print("Or use --run-test to run a manual consolidation test.")
            print()
        result = analyzer.analyze(sys.stdin)

    if args.json:
        output = {
            "version": SCRIPT_VERSION,
            "total_runs": result.total_runs,
            "total_scanned": result.total_scanned,
            "total_evaluated": result.total_evaluated,
            "total_consolidated": result.total_consolidated,
            "total_skipped": result.total_skipped,
            "total_errors": result.total_errors,
            "memory_type_distribution": result.memory_type_distribution,
            "score_distribution": result.score_distribution,
        }
        print(json.dumps(output, indent=2))
    else:
        analyzer.print_report(result)


if __name__ == "__main__":
    main()
