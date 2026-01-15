"""
Benchmark Evaluator - EPIC I Phase I-3 Autonomous Evolution

This module implements periodic benchmark evaluation for provider capability scoring.
It enables the system to self-evolve based on real performance data.

Key Features:
- Standardized benchmark tasks for code generation evaluation
- Provider capability scoring with trend analysis
- Scheduled benchmark execution (weekly full, daily smoke)
- Safety guards: no auto-upgrade without human review

Blueprint Alignment:
- Section 4.4: Autonomous Provisioning v2
- EPIC I-3: Autonomous Evolution (Benchmark & Capability Scoring)

Issue: #3342
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Redis keys for benchmark data
BENCHMARK_RESULTS_KEY = "governance:benchmark_results"
BENCHMARK_SCHEDULE_KEY = "governance:benchmark_schedule"
BENCHMARK_RESULTS_TTL = 86400 * 30  # 30 days


class BenchmarkTaskType(Enum):
    """Types of benchmark tasks"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"


class BenchmarkScheduleType(Enum):
    """Types of benchmark schedules"""
    WEEKLY_FULL = "weekly_full"  # Sunday 02:00 UTC - comprehensive evaluation
    DAILY_SMOKE = "daily_smoke"  # Daily 02:00 UTC - early degradation detection
    ON_DEMAND = "on_demand"  # Post-incident validation


@dataclass
class BenchmarkTask:
    """
    Standardized benchmark task for provider evaluation.

    EPIC I-3: Benchmark Task Schema

    Attributes:
        task_id: Unique identifier for benchmark task
        task_type: Type of coding task (code_generation, code_review, etc.)
        prompt: Standardized prompt for benchmark
        expected_output_schema: JSON Schema for expected output format
        evaluation_criteria: Weights for scoring (correctness, format, latency, cost)
        difficulty: Task difficulty level (easy, medium, hard)
        timeout_seconds: Maximum time allowed for task completion
    """
    task_id: str
    task_type: BenchmarkTaskType
    prompt: str
    expected_output_schema: Dict[str, Any]
    evaluation_criteria: Dict[str, float] = field(default_factory=lambda: {
        "correctness_weight": 0.4,
        "format_compliance_weight": 0.3,
        "latency_weight": 0.2,
        "cost_weight": 0.1,
    })
    difficulty: str = "medium"
    timeout_seconds: int = 60
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "prompt": self.prompt,
            "expected_output_schema": self.expected_output_schema,
            "evaluation_criteria": self.evaluation_criteria,
            "difficulty": self.difficulty,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkTask":
        """Create from dictionary"""
        return cls(
            task_id=data["task_id"],
            task_type=BenchmarkTaskType(data["task_type"]),
            prompt=data["prompt"],
            expected_output_schema=data.get("expected_output_schema", {}),
            evaluation_criteria=data.get("evaluation_criteria", {}),
            difficulty=data.get("difficulty", "medium"),
            timeout_seconds=data.get("timeout_seconds", 60),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class BenchmarkResult:
    """
    Result of a single benchmark task execution.

    Attributes:
        task_id: ID of the benchmark task
        provider: Provider that executed the task
        model: Model used for execution
        success: Whether the task completed successfully
        correctness_score: Score for output correctness (0-100)
        format_compliance_score: Score for format compliance (0-100)
        latency_ms: Execution latency in milliseconds
        cost_usd: Estimated cost in USD
        error: Error message if failed
        raw_output: Raw output from the model
        timestamp: ISO 8601 timestamp of execution
    """
    task_id: str
    provider: str
    model: str
    success: bool
    correctness_score: float = 0.0
    format_compliance_score: float = 0.0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None
    raw_output: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def calculate_weighted_score(self, criteria: Dict[str, float]) -> float:
        """
        Calculate weighted score based on evaluation criteria.

        Args:
            criteria: Dictionary with weight keys (correctness_weight, etc.)

        Returns:
            Weighted score (0-100)
        """
        if not self.success:
            return 0.0

        correctness_weight = criteria.get("correctness_weight", 0.4)
        format_weight = criteria.get("format_compliance_weight", 0.3)
        latency_weight = criteria.get("latency_weight", 0.2)
        cost_weight = criteria.get("cost_weight", 0.1)

        # Normalize latency score (lower is better, cap at 10s)
        latency_score = max(0, 100 - (self.latency_ms / 100))

        # Normalize cost score (lower is better, cap at $0.10)
        cost_score = max(0, 100 - (self.cost_usd * 1000))

        weighted_score = (
            self.correctness_score * correctness_weight +
            self.format_compliance_score * format_weight +
            latency_score * latency_weight +
            cost_score * cost_weight
        )

        return min(100, max(0, weighted_score))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "provider": self.provider,
            "model": self.model,
            "success": self.success,
            "correctness_score": self.correctness_score,
            "format_compliance_score": self.format_compliance_score,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "error": self.error,
            "raw_output": self.raw_output,
            "timestamp": self.timestamp,
        }


class BenchmarkEvaluator:
    """
    Evaluates provider capabilities through standardized benchmark tasks.

    EPIC I-3: Autonomous Evolution

    This class manages benchmark task execution and result collection.
    It is designed to be called from the governance heartbeat for scheduled
    benchmark runs.

    Safety Contract:
    - Benchmark failures MUST NOT affect production routing
    - All operations are wrapped in try/except
    - Results are stored for human review before any action

    Attributes:
        enabled: Whether benchmark evaluation is enabled
        dry_run: Whether to run in dry-run mode (no actual LLM calls)
        redis_client: Redis client for result storage
    """

    def __init__(
        self,
        redis_client: Optional["Redis"] = None,
        enabled: bool = True,
        dry_run: bool = True,
    ):
        self.redis_client = redis_client
        self.enabled = enabled
        self.dry_run = dry_run
        self._benchmark_suite = self._load_benchmark_suite()

    def _load_benchmark_suite(self) -> List[BenchmarkTask]:
        """
        Load the standard benchmark suite.

        Returns a list of predefined benchmark tasks for provider evaluation.
        """
        return [
            BenchmarkTask(
                task_id="bench_code_gen_001",
                task_type=BenchmarkTaskType.CODE_GENERATION,
                prompt=(
                    "Write a Python function that takes a list of integers and returns "
                    "the two numbers that sum to a target value. Include type hints and docstring."
                ),
                expected_output_schema={
                    "type": "object",
                    "required": ["code"],
                    "properties": {
                        "code": {"type": "string"},
                    },
                },
                difficulty="easy",
            ),
            BenchmarkTask(
                task_id="bench_code_gen_002",
                task_type=BenchmarkTaskType.CODE_GENERATION,
                prompt=(
                    "Write a Python class that implements a thread-safe LRU cache with "
                    "configurable max size. Include proper locking and type hints."
                ),
                expected_output_schema={
                    "type": "object",
                    "required": ["code"],
                    "properties": {
                        "code": {"type": "string"},
                    },
                },
                difficulty="medium",
            ),
            BenchmarkTask(
                task_id="bench_code_review_001",
                task_type=BenchmarkTaskType.CODE_REVIEW,
                prompt=(
                    "Review the following Python code and identify potential issues:\n"
                    "```python\n"
                    "def process_data(data):\n"
                    "    result = []\n"
                    "    for item in data:\n"
                    "        if item['status'] == 'active':\n"
                    "            result.append(item['value'] * 2)\n"
                    "    return result\n"
                    "```"
                ),
                expected_output_schema={
                    "type": "object",
                    "required": ["issues", "suggestions"],
                    "properties": {
                        "issues": {"type": "array"},
                        "suggestions": {"type": "array"},
                    },
                },
                difficulty="easy",
            ),
            BenchmarkTask(
                task_id="bench_bug_fix_001",
                task_type=BenchmarkTaskType.BUG_FIX,
                prompt=(
                    "Fix the bug in this Python code that causes an infinite loop:\n"
                    "```python\n"
                    "def find_index(arr, target):\n"
                    "    left, right = 0, len(arr)\n"
                    "    while left < right:\n"
                    "        mid = (left + right) // 2\n"
                    "        if arr[mid] == target:\n"
                    "            return mid\n"
                    "        elif arr[mid] < target:\n"
                    "            left = mid\n"
                    "        else:\n"
                    "            right = mid\n"
                    "    return -1\n"
                    "```"
                ),
                expected_output_schema={
                    "type": "object",
                    "required": ["fixed_code", "explanation"],
                    "properties": {
                        "fixed_code": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                },
                difficulty="medium",
            ),
        ]

    def get_benchmark_suite(
        self,
        schedule_type: BenchmarkScheduleType = BenchmarkScheduleType.WEEKLY_FULL,
    ) -> List[BenchmarkTask]:
        """
        Get benchmark tasks for a specific schedule type.

        Args:
            schedule_type: Type of benchmark schedule

        Returns:
            List of benchmark tasks to execute
        """
        if schedule_type == BenchmarkScheduleType.DAILY_SMOKE:
            # Return only easy tasks for daily smoke tests
            return [t for t in self._benchmark_suite if t.difficulty == "easy"]
        elif schedule_type == BenchmarkScheduleType.ON_DEMAND:
            # Return medium difficulty tasks for on-demand validation
            return [t for t in self._benchmark_suite if t.difficulty == "medium"]
        else:
            # Return full suite for weekly evaluation
            return self._benchmark_suite

    def evaluate_task(
        self,
        task: BenchmarkTask,
        provider: str,
        model: str,
    ) -> BenchmarkResult:
        """
        Evaluate a single benchmark task against a provider/model.

        Args:
            task: Benchmark task to evaluate
            provider: Provider to test
            model: Model to use

        Returns:
            BenchmarkResult with evaluation scores
        """
        start_time = time.monotonic()

        if self.dry_run:
            # In dry-run mode, return simulated results
            logger.info(
                f"[Benchmark] Dry-run evaluation: task={task.task_id}, "
                f"provider={provider}, model={model}",
                extra={
                    "operation": "benchmark_evaluate",
                    "task_id": task.task_id,
                    "provider": provider,
                    "model": model,
                    "dry_run": True,
                }
            )

            # Simulate realistic scores based on provider
            simulated_scores = self._get_simulated_scores(provider, task.difficulty)

            return BenchmarkResult(
                task_id=task.task_id,
                provider=provider,
                model=model,
                success=True,
                correctness_score=simulated_scores["correctness"],
                format_compliance_score=simulated_scores["format"],
                latency_ms=simulated_scores["latency_ms"],
                cost_usd=simulated_scores["cost_usd"],
                raw_output="[DRY-RUN] Simulated output",
            )

        # Real evaluation (when dry_run=False)
        try:
            # Import LLM client for actual evaluation
            from llm.client import get_llm_client

            client = get_llm_client()

            # Execute the benchmark task
            response = client.generate(
                prompt=task.prompt,
                provider=provider,
                model=model,
                timeout=task.timeout_seconds,
            )

            latency_ms = (time.monotonic() - start_time) * 1000

            # Evaluate the response
            correctness_score = self._evaluate_correctness(
                response.content,
                task.expected_output_schema,
            )
            format_score = self._evaluate_format_compliance(
                response.content,
                task.expected_output_schema,
            )

            return BenchmarkResult(
                task_id=task.task_id,
                provider=provider,
                model=model,
                success=True,
                correctness_score=correctness_score,
                format_compliance_score=format_score,
                latency_ms=latency_ms,
                cost_usd=response.cost_usd if hasattr(response, "cost_usd") else 0.0,
                raw_output=response.content,
            )

        except Exception as e:
            latency_ms = (time.monotonic() - start_time) * 1000

            logger.warning(
                f"[Benchmark] Task evaluation failed: {e}",
                extra={
                    "operation": "benchmark_evaluate",
                    "task_id": task.task_id,
                    "provider": provider,
                    "model": model,
                    "error": str(e),
                }
            )

            return BenchmarkResult(
                task_id=task.task_id,
                provider=provider,
                model=model,
                success=False,
                latency_ms=latency_ms,
                error=str(e),
            )

    def _get_simulated_scores(
        self,
        provider: str,
        difficulty: str,
    ) -> Dict[str, float]:
        """
        Get simulated scores for dry-run mode.

        Returns realistic scores based on provider and task difficulty.
        """
        # Base scores by provider (simulated based on typical performance)
        provider_base_scores = {
            "openai": {"correctness": 92, "format": 95, "latency_ms": 800, "cost_usd": 0.02},
            "gemini": {"correctness": 90, "format": 93, "latency_ms": 600, "cost_usd": 0.015},
            "alicloud": {"correctness": 85, "format": 88, "latency_ms": 1200, "cost_usd": 0.01},
            "siliconflow": {"correctness": 82, "format": 85, "latency_ms": 1500, "cost_usd": 0.008},
        }

        base = provider_base_scores.get(provider, {
            "correctness": 80,
            "format": 82,
            "latency_ms": 1000,
            "cost_usd": 0.015,
        })

        # Adjust for difficulty
        difficulty_multipliers = {
            "easy": 1.05,
            "medium": 1.0,
            "hard": 0.9,
        }
        multiplier = difficulty_multipliers.get(difficulty, 1.0)

        return {
            "correctness": min(100, base["correctness"] * multiplier),
            "format": min(100, base["format"] * multiplier),
            "latency_ms": base["latency_ms"] / multiplier,
            "cost_usd": base["cost_usd"] * (2 - multiplier),
        }

    def _evaluate_correctness(
        self,
        output: str,
        expected_schema: Dict[str, Any],
    ) -> float:
        """
        Evaluate output correctness against expected schema.

        Returns a score from 0-100.
        """
        # Basic correctness check - verify output is not empty
        if not output or len(output.strip()) < 10:
            return 0.0

        # Check if output contains expected elements
        score = 50.0  # Base score for non-empty output

        # Check for code blocks if expected
        if "code" in str(expected_schema):
            if "```" in output or "def " in output or "class " in output:
                score += 25.0

        # Check for structured response
        if "{" in output and "}" in output:
            score += 15.0

        # Check for explanation/reasoning
        if len(output) > 200:
            score += 10.0

        return min(100.0, score)

    def _evaluate_format_compliance(
        self,
        output: str,
        expected_schema: Dict[str, Any],
    ) -> float:
        """
        Evaluate output format compliance against expected schema.

        Returns a score from 0-100.
        """
        if not output:
            return 0.0

        score = 60.0  # Base score

        # Check for JSON structure if expected
        required_fields = expected_schema.get("required", [])
        for field_name in required_fields:
            if field_name.lower() in output.lower():
                score += 10.0

        return min(100.0, score)

    def run_benchmark_suite(
        self,
        providers: List[str],
        models: Dict[str, str],
        schedule_type: BenchmarkScheduleType = BenchmarkScheduleType.WEEKLY_FULL,
    ) -> Dict[str, Any]:
        """
        Run the benchmark suite against multiple providers.

        Args:
            providers: List of providers to benchmark
            models: Dictionary mapping provider to model name
            schedule_type: Type of benchmark schedule

        Returns:
            Dictionary with benchmark results and summary
        """
        if not self.enabled:
            return {
                "executed": False,
                "reason": "benchmark_disabled",
            }

        tasks = self.get_benchmark_suite(schedule_type)
        results: List[BenchmarkResult] = []
        provider_scores: Dict[str, List[float]] = {}

        logger.info(
            f"[Benchmark] Starting benchmark suite: schedule={schedule_type.value}, "
            f"providers={providers}, tasks={len(tasks)}",
            extra={
                "operation": "benchmark_suite",
                "schedule_type": schedule_type.value,
                "providers": providers,
                "task_count": len(tasks),
                "dry_run": self.dry_run,
            }
        )

        for provider in providers:
            model = models.get(provider, "default")
            provider_scores[provider] = []

            for task in tasks:
                result = self.evaluate_task(task, provider, model)
                results.append(result)

                weighted_score = result.calculate_weighted_score(task.evaluation_criteria)
                provider_scores[provider].append(weighted_score)

        # Calculate summary statistics
        summary = {}
        for provider, scores in provider_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                summary[provider] = {
                    "average_score": round(avg_score, 2),
                    "task_count": len(scores),
                    "success_rate": sum(1 for r in results if r.provider == provider and r.success) / len(scores) * 100,
                }

        # Store results in Redis if available
        if self.redis_client:
            self._store_results(results, schedule_type)

        logger.info(
            f"[Benchmark] Suite completed: {len(results)} results",
            extra={
                "operation": "benchmark_suite",
                "schedule_type": schedule_type.value,
                "result_count": len(results),
                "summary": summary,
            }
        )

        return {
            "executed": True,
            "schedule_type": schedule_type.value,
            "dry_run": self.dry_run,
            "results": [r.to_dict() for r in results],
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _store_results(
        self,
        results: List[BenchmarkResult],
        schedule_type: BenchmarkScheduleType,
    ) -> bool:
        """Store benchmark results in Redis."""
        if not self.redis_client:
            return False

        try:
            result_data = {
                "schedule_type": schedule_type.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": [r.to_dict() for r in results],
            }

            # Store with timestamp-based key for history
            key = f"{BENCHMARK_RESULTS_KEY}:{int(time.time())}"
            self.redis_client.setex(
                key,
                BENCHMARK_RESULTS_TTL,
                json.dumps(result_data),
            )

            logger.debug(
                f"[Benchmark] Results stored: key={key}",
                extra={
                    "operation": "benchmark_store",
                    "key": key,
                    "result_count": len(results),
                }
            )
            return True

        except Exception as e:
            logger.warning(
                f"[Benchmark] Failed to store results: {e}",
                extra={
                    "operation": "benchmark_store",
                    "error": str(e),
                }
            )
            return False


# Global instance
_benchmark_evaluator: Optional[BenchmarkEvaluator] = None


def get_benchmark_evaluator(
    redis_client: Optional["Redis"] = None,
) -> BenchmarkEvaluator:
    """Get or create global BenchmarkEvaluator instance."""
    global _benchmark_evaluator
    if _benchmark_evaluator is None:
        import os
        enabled = os.getenv("BENCHMARK_EVALUATION_ENABLED", "false").lower() == "true"
        dry_run = os.getenv("BENCHMARK_DRY_RUN", "true").lower() == "true"
        _benchmark_evaluator = BenchmarkEvaluator(
            redis_client=redis_client,
            enabled=enabled,
            dry_run=dry_run,
        )
    return _benchmark_evaluator
