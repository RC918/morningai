"""
Regression Pipeline for Simulation Suite

Blueprint Section 5.4: Regression Pipeline v1

Automated regression test generation from errors:
- Error capture from multiple sources
- Priority calculation
- Regression test generation (H-2.3: LLM-powered)
- CI enforcement rules

H-2.3 Test Generation Integration:
- Bridges RegressionTestGenerator with LLM for actual test code generation
- Uses MRE from Diagnostic Agent to create functional tests
- Falls back to template generation if LLM fails
"""

import ast
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

    def generate_test_with_llm(
        self,
        candidate: RegressionCandidate,
        test_name: Optional[str] = None,
        enable_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a regression test using LLM for actual test logic.

        H-2.3 Test Generation Integration (Blueprint Section 5.4):
        - Uses MRE from Diagnostic Agent to create functional tests
        - Falls back to template generation if LLM fails
        - Bridges RegressionTestGenerator with Test Agent v2 capabilities

        Args:
            candidate: RegressionCandidate to generate test for
            test_name: Optional custom test name
            enable_llm: Whether to use LLM (False = template only)

        Returns:
            Dict with:
                - success: bool
                - test_code: str (generated test code)
                - llm_used: bool (whether LLM was used)
                - candidate_id: str
                - test_name: str
                - error: Optional[str] (if failed)
        """
        if test_name is None:
            safe_name = candidate.error_type.replace(":", "_").replace(".", "_")
            test_name = f"test_regression_{safe_name}_{candidate.candidate_id[:8]}"

        result: Dict[str, Any] = {
            "success": False,
            "test_code": "",
            "llm_used": False,
            "candidate_id": candidate.candidate_id,
            "test_name": test_name,
            "error": None,
        }

        if enable_llm:
            try:
                llm_test_code = self._generate_test_with_llm_internal(
                    candidate, test_name
                )
                if llm_test_code:
                    result["success"] = True
                    result["test_code"] = llm_test_code
                    result["llm_used"] = True

                    self._generated_tests.append({
                        "candidate_id": candidate.candidate_id,
                        "test_name": test_name,
                        "test_code": llm_test_code,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_used": True,
                    })

                    logger.info(
                        f"[Regression] H-2.3: Generated LLM test: {test_name}",
                        extra={
                            "operation": "simulation.regression.llm",
                            "candidate_id": candidate.candidate_id,
                            "test_name": test_name,
                            "llm_used": True,
                        }
                    )
                    return result

            except Exception as e:
                logger.warning(
                    f"[Regression] H-2.3: LLM test generation failed, "
                    f"falling back to template: {e}",
                    extra={
                        "operation": "simulation.regression.llm",
                        "candidate_id": candidate.candidate_id,
                        "error": str(e),
                    }
                )

        # Fallback to template generation
        # (Cursor Bugbot: track template tests in _generated_tests for consistency)
        template_test_code = self.generate_test(candidate, test_name)
        result["success"] = True
        result["test_code"] = template_test_code
        result["llm_used"] = False

        # Track template-generated tests in _generated_tests list
        self._generated_tests.append({
            "candidate_id": candidate.candidate_id,
            "test_name": test_name,
            "test_code": template_test_code,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_used": False,
        })

        logger.info(
            f"[Regression] H-2.3: Generated template test: {test_name}",
            extra={
                "operation": "simulation.regression.template",
                "candidate_id": candidate.candidate_id,
                "test_name": test_name,
                "llm_used": False,
            }
        )
        return result

    def _generate_test_with_llm_internal(
        self,
        candidate: RegressionCandidate,
        test_name: str,
    ) -> Optional[str]:
        """
        Internal method to generate test using LLM.

        Args:
            candidate: RegressionCandidate with MRE and reproduction steps
            test_name: Name for the test function

        Returns:
            Generated test code string or None if failed
        """
        try:
            from common.config.settings import settings
        except ImportError:
            logger.warning(
                "[Regression] H-2.3: Could not import settings, "
                "falling back to template"
            )
            return None

        model = getattr(settings, 'llm_test_generator_model', 'qwen-max')
        api_key = None
        base_url = None

        if 'qwen' in model.lower():
            api_key = getattr(settings, 'dashscope_api_key', None)
            base_url = getattr(settings, 'dashscope_base_url', None)
        else:
            api_key = getattr(settings, 'openai_api_key', None)

        if not api_key:
            logger.warning(
                "[Regression] H-2.3: No API key configured for LLM test generation"
            )
            return None

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            logger.warning(
                "[Regression] H-2.3: OpenAI client not available"
            )
            return None

        prompt = self._build_regression_test_prompt(candidate, test_name)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Python test engineer specializing in "
                            "regression tests. Generate comprehensive pytest tests that "
                            "verify the error no longer occurs. Focus on reproducing "
                            "the exact conditions that caused the original error."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )

            llm_output = response.choices[0].message.content
            if not llm_output:
                return None

            llm_output = llm_output.strip()
            test_code = self._parse_llm_regression_test_output(
                llm_output, test_name, candidate
            )
            return test_code

        except Exception as e:
            logger.warning(
                f"[Regression] H-2.3: LLM API call failed: {e}",
                extra={
                    "operation": "simulation.regression.llm",
                    "candidate_id": candidate.candidate_id,
                    "error": str(e),
                }
            )
            return None

    def _build_regression_test_prompt(
        self,
        candidate: RegressionCandidate,
        test_name: str,
    ) -> str:
        """
        Build LLM prompt for regression test generation.

        Includes MRE code and reproduction steps from Diagnostic Agent.

        Args:
            candidate: RegressionCandidate with error context
            test_name: Name for the test function

        Returns:
            Prompt string for LLM
        """
        mre_code = ""
        setup_instructions = ""
        expected_error = ""

        if candidate.reproduction_steps:
            for step in candidate.reproduction_steps:
                if step.startswith("MRE Code:"):
                    mre_code = step.replace("MRE Code:", "").strip()
                elif step.startswith("Setup:"):
                    setup_instructions = step.replace("Setup:", "").strip()
                elif step.startswith("Expected Error:"):
                    expected_error = step.replace("Expected Error:", "").strip()

        repro_steps_text = ""
        if candidate.reproduction_steps:
            repro_steps_text = "\n".join(
                f"- {step}" for step in candidate.reproduction_steps
                if not step.startswith(("MRE Code:", "Setup:", "Expected Error:"))
            )

        safe_error_message = candidate.error_message[:500]
        safe_error_type = candidate.error_type

        prompt = f"""Generate a regression test to prevent recurrence of this error.

## Error Information
- **Error Type**: {safe_error_type}
- **Error Source**: {candidate.source.value}
- **Priority**: {candidate.priority.value}
- **Error Message**:
```
{safe_error_message}
```

## Stack Trace (if available)
```
{candidate.stack_trace[:1000] if candidate.stack_trace else "Not available"}
```

## Minimal Reproducible Example (MRE)
```python
{mre_code if mre_code else "# No MRE provided - generate based on error context"}
```

## Setup Instructions
{setup_instructions if setup_instructions else "No specific setup required"}

## Expected Error
{expected_error if expected_error else safe_error_type}

## Reproduction Steps
{repro_steps_text if repro_steps_text else "Follow the MRE code above"}

## Requirements
1. Use pytest framework
2. Test function name: `{test_name}`
3. Include a descriptive docstring explaining what regression this prevents
4. Test should PASS when the bug is fixed (error no longer occurs)
5. Test should FAIL if the bug regresses (error occurs again)
6. Include appropriate assertions to verify correct behavior
7. Add REGRESSION_METADATA dict at the end with candidate_id and protected=True
8. Return ONLY the complete test code, no explanations

## Example Structure
```python
import pytest

class TestRegression_{candidate.candidate_id[:8]}:
    \"\"\"
    Regression test for: {safe_error_type}
    Blueprint Section 5.4: CI Enforcement
    \"\"\"

    def {test_name}(self):
        \"\"\"Verify that [error] no longer occurs.\"\"\"
        # Setup
        # Execute the operation that caused the error
        # Assert the error no longer occurs
        pass

REGRESSION_METADATA = {{
    "candidate_id": "{candidate.candidate_id}",
    "protected": True,
}}
```

Generate the complete regression test:"""

        return prompt

    def _parse_llm_regression_test_output(
        self,
        llm_output: str,
        test_name: str,
        candidate: RegressionCandidate,
    ) -> Optional[str]:
        """
        Parse LLM output to extract valid test code.

        Args:
            llm_output: Raw LLM output
            test_name: Expected test function name
            candidate: RegressionCandidate for metadata

        Returns:
            Valid test code string or None if parsing fails
        """
        code_blocks: List[str] = []
        in_code_block = False
        current_block: List[str] = []

        for line in llm_output.split('\n'):
            if line.strip().startswith('```'):
                if in_code_block:
                    code_blocks.append('\n'.join(current_block))
                    current_block = []
                in_code_block = not in_code_block
            elif in_code_block:
                current_block.append(line)

        if not code_blocks:
            code_blocks = [llm_output]

        for block in code_blocks:
            if test_name in block or 'def test_' in block:
                try:
                    ast.parse(block)

                    if 'REGRESSION_METADATA' not in block:
                        # Escape special characters to prevent syntax errors
                        # (Cursor Bugbot: error_type may contain quotes/backslashes)
                        import json
                        safe_candidate_id = json.dumps(candidate.candidate_id)
                        safe_error_type = json.dumps(candidate.error_type)
                        safe_priority = json.dumps(candidate.priority.value)
                        safe_source = json.dumps(candidate.source.value)
                        safe_generated_at = json.dumps(
                            datetime.now(timezone.utc).isoformat()
                        )
                        metadata = f'''

# Metadata for CI enforcement
REGRESSION_METADATA = {{
    "candidate_id": {safe_candidate_id},
    "error_type": {safe_error_type},
    "priority": {safe_priority},
    "source": {safe_source},
    "generated_at": {safe_generated_at},
    "protected": True,
    "llm_generated": True,
}}
'''
                        block = block + metadata
                        # Re-validate after adding metadata
                        try:
                            ast.parse(block)
                        except SyntaxError:
                            logger.warning(
                                "[Regression] H-2.3: Metadata injection "
                                "caused syntax error, skipping metadata"
                            )
                            block = block.replace(metadata, "")

                    return block.strip()

                except SyntaxError as e:
                    logger.warning(
                        f"[Regression] H-2.3: LLM generated invalid Python: {e}"
                    )
                    continue

        return None

    def generate_tests_for_priority_with_llm(
        self,
        collector: RegressionCandidateCollector,
        priority: RegressionPriority,
        enable_llm: bool = True,
        max_tests: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate tests for all candidates of a given priority using LLM.

        H-2.3 Test Generation Integration (Blueprint Section 5.4).

        Args:
            collector: RegressionCandidateCollector with candidates
            priority: Priority level to generate tests for
            enable_llm: Whether to use LLM (False = template only)
            max_tests: Maximum number of tests to generate (uses
                       regression_test_max_per_run setting if not specified)

        Returns:
            List of generation results (see generate_test_with_llm return type)
        """
        # Get max_tests from settings if not specified
        # (MorningAI Reviewer: limit unbounded LLM calls)
        if max_tests is None:
            try:
                from common.config.settings import settings
                max_tests = getattr(settings, 'regression_test_max_per_run', 5)
            except ImportError:
                max_tests = 5  # Default fallback

        candidates = collector.get_candidates_by_priority(priority)

        # Limit candidates to max_tests to prevent unbounded LLM calls
        if len(candidates) > max_tests:
            logger.info(
                f"[Regression] H-2.3: Limiting test generation from "
                f"{len(candidates)} to {max_tests} candidates",
                extra={
                    "operation": "simulation.regression.limit",
                    "priority": priority.value,
                    "total_candidates": len(candidates),
                    "max_tests": max_tests,
                }
            )
            candidates = candidates[:max_tests]

        results = []
        for candidate in candidates:
            result = self.generate_test_with_llm(
                candidate, enable_llm=enable_llm
            )
            results.append(result)
        return results


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
