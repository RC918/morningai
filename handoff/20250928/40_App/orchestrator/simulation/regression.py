"""
Regression Pipeline for Simulation Suite

Blueprint Section 5.4: Regression Pipeline v1

Automated regression test generation from errors:
- Error capture from multiple sources
- Priority calculation
- Regression test generation
- CI enforcement rules
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RegressionPriority(Enum):
    """
    Regression priority levels.

    Blueprint Section 5.4:
    - P0: 立即建立 regression
    - P1: 排入 nightly regression cycle
    - P2: 觀察是否重複再建立
    """
    P0 = "p0"  # Immediate regression
    P1 = "p1"  # Nightly regression cycle
    P2 = "p2"  # Observe for repetition


class ErrorSource(Enum):
    """
    Error sources for regression candidates.

    Blueprint Section 5.4 Error Sources:
    - Runtime Errors: Node backend / Python orchestrator logs
    - BrowserNode Failures: selector 找不到、DOM 結構變動
    - Sentry / Datadog Alerts: stack trace + breadcrumbs
    - Diagnostic Agent Reports: root cause + 重現步驟
    - CI Failures: GitHub Actions / CI pipeline failures
    """
    RUNTIME_ERROR = "runtime_error"
    BROWSERNODE_FAILURE = "browsernode_failure"
    SENTRY_ALERT = "sentry_alert"
    DATADOG_ALERT = "datadog_alert"
    DIAGNOSTIC_AGENT = "diagnostic_agent"
    SIMULATION_FAILURE = "simulation_failure"
    CI_FAILURE = "ci_failure"  # Added for H-2 Regression Pipeline integration


@dataclass
class RegressionCandidate:
    """
    A candidate for regression test generation.

    Blueprint Section 5.4: Regression Candidate Selection
    priority = severity*0.5 + frequency*0.3 + blast_radius*0.2

    Attributes:
        candidate_id: Unique identifier (hash of error signature)
        error_signature: Unique signature for deduplication
        source: Where the error originated
        error_type: Type/class of the error
        error_message: Error message
        stack_trace: Full stack trace if available
        reproduction_steps: Steps to reproduce (from Diagnostic Agent)
        severity: Severity score (0.0 - 1.0)
        frequency: How often this error occurs (0.0 - 1.0)
        blast_radius: Impact scope (0.0 - 1.0)
        priority: Calculated priority level
        metadata: Additional context
        first_seen: When first observed
        last_seen: When last observed
        occurrence_count: Number of times observed
    """
    candidate_id: str
    error_signature: str
    source: ErrorSource
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    reproduction_steps: Optional[List[str]] = None
    severity: float = 0.5
    frequency: float = 0.0
    blast_radius: float = 0.3
    priority: RegressionPriority = RegressionPriority.P2
    metadata: Dict[str, Any] = field(default_factory=dict)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    occurrence_count: int = 1

    def calculate_priority_score(self) -> float:
        """
        Calculate priority score using Blueprint formula.

        priority = severity*0.5 + frequency*0.3 + blast_radius*0.2
        """
        return (
            self.severity * 0.5 +
            self.frequency * 0.3 +
            self.blast_radius * 0.2
        )

    def update_priority(self) -> None:
        """Update priority level based on calculated score."""
        score = self.calculate_priority_score()
        if score >= 0.7:
            self.priority = RegressionPriority.P0
        elif score >= 0.4:
            self.priority = RegressionPriority.P1
        else:
            self.priority = RegressionPriority.P2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "candidate_id": self.candidate_id,
            "error_signature": self.error_signature,
            "source": self.source.value,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "reproduction_steps": self.reproduction_steps,
            "severity": self.severity,
            "frequency": self.frequency,
            "blast_radius": self.blast_radius,
            "priority": self.priority.value,
            "priority_score": self.calculate_priority_score(),
            "metadata": self.metadata,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "occurrence_count": self.occurrence_count,
        }


class RegressionCandidateCollector:
    """
    Collects and manages regression candidates from various error sources.

    Blueprint Section 5.4: Error Sources
    - Runtime Errors
    - BrowserNode Failures
    - Sentry/Datadog Alerts
    - Diagnostic Agent Reports

    Features:
    - Deduplication by error signature
    - Frequency tracking
    - Priority calculation
    - Candidate filtering by priority
    """

    def __init__(self, max_candidates: int = 1000):
        """
        Initialize the collector.

        Args:
            max_candidates: Maximum number of candidates to keep
        """
        self.max_candidates = max_candidates
        self._candidates: Dict[str, RegressionCandidate] = {}
        self._total_errors_collected = 0

    @staticmethod
    def generate_signature(
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ) -> str:
        """
        Generate a unique signature for error deduplication.

        Uses error type and first line of stack trace for grouping.
        """
        # Normalize error message (remove variable parts like IDs, timestamps)
        normalized_message = error_message[:200]  # Truncate long messages

        # Use first meaningful line of stack trace if available
        trace_key = ""
        if stack_trace:
            lines = [line.strip() for line in stack_trace.split("\n") if line.strip()]
            # Find first line with file reference
            for line in lines:
                if "File" in line or ".py" in line or ".js" in line:
                    trace_key = line[:100]
                    break

        signature_input = f"{error_type}:{normalized_message}:{trace_key}"
        return hashlib.sha256(signature_input.encode()).hexdigest()[:16]

    def collect(
        self,
        source: ErrorSource,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        reproduction_steps: Optional[List[str]] = None,
        severity: float = 0.5,
        blast_radius: float = 0.3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RegressionCandidate:
        """
        Collect an error as a regression candidate.

        If the error signature already exists, updates frequency.
        Otherwise, creates a new candidate.

        Args:
            source: Error source
            error_type: Type/class of error
            error_message: Error message
            stack_trace: Full stack trace
            reproduction_steps: Steps to reproduce
            severity: Severity score (0.0 - 1.0)
            blast_radius: Impact scope (0.0 - 1.0)
            metadata: Additional context

        Returns:
            RegressionCandidate (new or updated)
        """
        self._total_errors_collected += 1

        signature = self.generate_signature(error_type, error_message, stack_trace)

        if signature in self._candidates:
            # Update existing candidate
            candidate = self._candidates[signature]
            candidate.occurrence_count += 1
            candidate.last_seen = datetime.now(timezone.utc)

            # Update frequency based on occurrence rate
            # Higher occurrence = higher frequency score
            candidate.frequency = min(1.0, candidate.occurrence_count / 10.0)

            # Update severity if new severity is higher
            if severity > candidate.severity:
                candidate.severity = severity

            # Update blast radius if new is higher
            if blast_radius > candidate.blast_radius:
                candidate.blast_radius = blast_radius

            # Recalculate priority
            candidate.update_priority()

            logger.info(
                f"[Regression] Updated candidate {signature}: "
                f"count={candidate.occurrence_count}, priority={candidate.priority.value}",
                extra={
                    "operation": "simulation.regression",
                    "candidate_id": signature,
                    "occurrence_count": candidate.occurrence_count,
                }
            )
        else:
            # Create new candidate
            candidate = RegressionCandidate(
                candidate_id=signature,
                error_signature=signature,
                source=source,
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                reproduction_steps=reproduction_steps,
                severity=severity,
                blast_radius=blast_radius,
                metadata=metadata or {},
            )
            candidate.update_priority()

            self._candidates[signature] = candidate

            logger.info(
                f"[Regression] New candidate {signature}: "
                f"type={error_type}, priority={candidate.priority.value}",
                extra={
                    "operation": "simulation.regression",
                    "candidate_id": signature,
                    "error_type": error_type,
                    "priority": candidate.priority.value,
                }
            )

            # Prune if over limit
            self._prune_if_needed()

        return candidate

    def collect_from_simulation(
        self,
        scenario_name: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RegressionCandidate:
        """
        Convenience method to collect errors from simulation failures.

        Args:
            scenario_name: Name of the failed scenario
            error_message: Error message
            stack_trace: Full stack trace
            metadata: Additional context

        Returns:
            RegressionCandidate
        """
        return self.collect(
            source=ErrorSource.SIMULATION_FAILURE,
            error_type=f"SimulationFailure:{scenario_name}",
            error_message=error_message,
            stack_trace=stack_trace,
            severity=0.6,  # Simulation failures are medium-high severity
            blast_radius=0.4,
            metadata={
                "scenario_name": scenario_name,
                **(metadata or {}),
            },
        )

    def get_candidates_by_priority(
        self,
        priority: RegressionPriority
    ) -> List[RegressionCandidate]:
        """Get all candidates with the given priority."""
        return [
            c for c in self._candidates.values()
            if c.priority == priority
        ]

    def get_p0_candidates(self) -> List[RegressionCandidate]:
        """Get all P0 (immediate) candidates."""
        return self.get_candidates_by_priority(RegressionPriority.P0)

    def get_all_candidates(self) -> List[RegressionCandidate]:
        """Get all candidates sorted by priority score (descending)."""
        return sorted(
            self._candidates.values(),
            key=lambda c: c.calculate_priority_score(),
            reverse=True,
        )

    def get_candidate(self, candidate_id: str) -> Optional[RegressionCandidate]:
        """Get a specific candidate by ID."""
        return self._candidates.get(candidate_id)

    def remove_candidate(self, candidate_id: str) -> bool:
        """Remove a candidate (e.g., after regression test is created)."""
        if candidate_id in self._candidates:
            del self._candidates[candidate_id]
            return True
        return False

    def _prune_if_needed(self) -> None:
        """Remove lowest priority candidates if over limit."""
        if len(self._candidates) > self.max_candidates:
            # Sort by priority score and keep top candidates
            sorted_candidates = sorted(
                self._candidates.items(),
                key=lambda x: x[1].calculate_priority_score(),
                reverse=True,
            )
            self._candidates = dict(sorted_candidates[:self.max_candidates])

    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        candidates = list(self._candidates.values())
        return {
            "total_candidates": len(candidates),
            "total_errors_collected": self._total_errors_collected,
            "p0_count": len([c for c in candidates if c.priority == RegressionPriority.P0]),
            "p1_count": len([c for c in candidates if c.priority == RegressionPriority.P1]),
            "p2_count": len([c for c in candidates if c.priority == RegressionPriority.P2]),
            "by_source": {
                source.value: len([c for c in candidates if c.source == source])
                for source in ErrorSource
            },
        }


class RegressionTestGenerator:
    """
    Generates regression tests from candidates.

    Blueprint Section 5.4: Regression Test Generation Flow
    Error → Diagnostic Agent → MRE → Test Agent v2 → Regression Test → CI Validation

    This class generates test code templates that can be:
    - Added to the test suite
    - Validated in CI
    - Protected from modification/deletion
    """

    @staticmethod
    def _escape_for_docstring(text: str) -> str:
        """
        Escape text for safe inclusion in Python docstrings.

        Handles triple quotes, backslashes, and other special characters
        that could break generated test syntax.

        Args:
            text: Raw text to escape

        Returns:
            Escaped text safe for docstring inclusion
        """
        if not text:
            return text
        # Escape backslashes first (before other escapes add more)
        escaped = text.replace("\\", "\\\\")
        # Escape triple quotes (both styles)
        escaped = escaped.replace('"""', '\\"\\"\\"')
        escaped = escaped.replace("'''", "\\'\\'\\'")
        return escaped

    def __init__(self, output_dir: str = "tests/regression"):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write generated tests
        """
        self.output_dir = output_dir
        self._generated_tests: List[Dict[str, Any]] = []

    def generate_test(
        self,
        candidate: RegressionCandidate,
        test_name: Optional[str] = None,
    ) -> str:
        """
        Generate a regression test from a candidate.

        Args:
            candidate: RegressionCandidate to generate test for
            test_name: Optional custom test name

        Returns:
            Generated test code as string
        """
        if test_name is None:
            # Generate test name from error type
            safe_name = candidate.error_type.replace(":", "_").replace(".", "_")
            test_name = f"test_regression_{safe_name}_{candidate.candidate_id[:8]}"

        # Generate reproduction steps as comments
        repro_comments = ""
        if candidate.reproduction_steps:
            repro_comments = "\n".join(
                f"    # Step {i + 1}: {step}"
                for i, step in enumerate(candidate.reproduction_steps)
            )
            repro_comments = f"\n{repro_comments}\n"

        # Escape error message for safe docstring inclusion
        # Prevents syntax errors from triple quotes or backslashes in error messages
        safe_error_message_long = self._escape_for_docstring(candidate.error_message[:500])
        safe_error_message_short = self._escape_for_docstring(candidate.error_message[:200])
        safe_error_type = self._escape_for_docstring(candidate.error_type)

        # Generate test code
        test_code = f'''"""
Regression test for: {safe_error_type}
Generated from: {candidate.source.value}
Priority: {candidate.priority.value}
First seen: {candidate.first_seen.isoformat()}
Candidate ID: {candidate.candidate_id}

Original error message:
{safe_error_message_long}
"""

import pytest


class TestRegression_{candidate.candidate_id[:8]}:
    """
    Regression test to prevent recurrence of:
    {safe_error_type}

    Blueprint Section 5.4: CI Enforcement
    - If this test fails → PR is blocked
    - If this test is modified → Requires reviewer approval
    - If this test is deleted → Safety Governor blocks
    """
{repro_comments}
    def {test_name}(self):
        """
        Regression test for {safe_error_type}.

        This test was auto-generated from error:
        {safe_error_message_short}
        """
        # TODO: Implement test logic based on reproduction steps
        # The Diagnostic Agent should provide MRE (Minimal Reproducible Example)

        # Placeholder assertion - replace with actual test logic
        # based on the reproduction steps above
        assert True, "Implement regression test logic"

        # Example structure:
        # 1. Set up test fixtures
        # 2. Execute the operation that caused the error
        # 3. Assert that the error no longer occurs
        # 4. Clean up


# Metadata for CI enforcement
REGRESSION_METADATA = {{
    "candidate_id": "{candidate.candidate_id}",
    "error_type": "{candidate.error_type}",
    "priority": "{candidate.priority.value}",
    "source": "{candidate.source.value}",
    "generated_at": "{datetime.now(timezone.utc).isoformat()}",
    "protected": True,  # CI should block deletion/modification without review
}}
'''

        self._generated_tests.append({
            "candidate_id": candidate.candidate_id,
            "test_name": test_name,
            "test_code": test_code,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(
            f"[Regression] Generated test: {test_name}",
            extra={
                "operation": "simulation.regression",
                "candidate_id": candidate.candidate_id,
                "test_name": test_name,
            }
        )

        return test_code

    def generate_tests_for_priority(
        self,
        collector: RegressionCandidateCollector,
        priority: RegressionPriority,
    ) -> List[str]:
        """
        Generate tests for all candidates of a given priority.

        Args:
            collector: RegressionCandidateCollector with candidates
            priority: Priority level to generate tests for

        Returns:
            List of generated test code strings
        """
        candidates = collector.get_candidates_by_priority(priority)
        return [self.generate_test(c) for c in candidates]

    def get_generated_tests(self) -> List[Dict[str, Any]]:
        """Get list of all generated tests."""
        return self._generated_tests.copy()


# Global collector instance for convenience
_global_collector: Optional[RegressionCandidateCollector] = None


def get_regression_collector() -> RegressionCandidateCollector:
    """Get or create the global regression candidate collector."""
    global _global_collector
    if _global_collector is None:
        _global_collector = RegressionCandidateCollector()
    return _global_collector


def collect_regression_candidate(
    source: ErrorSource,
    error_type: str,
    error_message: str,
    **kwargs
) -> RegressionCandidate:
    """
    Convenience function to collect a regression candidate.

    Uses the global collector instance.
    """
    collector = get_regression_collector()
    return collector.collect(
        source=source,
        error_type=error_type,
        error_message=error_message,
        **kwargs,
    )
