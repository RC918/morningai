"""
SimpleCoder Agent - D-1 Phase 0 (Proof-of-Life)

Issue #3211: D-1.1 Coder Three Don'ts Safety Guardrails
Parent Issue #2760: D-1 General Coder Agent MVP
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
CTO Approved: 2025-12-29

This module implements the SimpleCoder agent with Three Don'ts safety guardrails:
1. Low Confidence = Abort (structured output with status: skipped)
2. Side-effect Gate (handled by autofix_gate.py in Router)
3. Verification Gate (Python syntax check using ast.parse)

Schema Design:
--------------
There are TWO distinct schemas in this module:

1. LLM Response Schema (what the LLM must output):
   {
       "status": "skipped" | "patch",
       "reason": "string (required if skipped)",
       "patch": "string (required if patch)"
   }
   This is the ONLY format the LLM should emit. Keep it minimal and strict.

2. Final CoderOutput Schema (what downstream consumers receive):
   {
       "schema_version": 1,
       "status": "skipped" | "patch",
       "reason": "string (present if skipped)",
       "patch": "string (present if patch)",
       "file_path": "string (system-added)",
       "syntax_valid": bool | null (system-added, Python files only)
   }
   The system enriches the LLM response with file_path and syntax_valid.

Usage:
    from coder.simple_coder import get_simple_coder, CoderOutput

    coder = get_simple_coder()
    result = coder.generate_fix(
        file_path="src/utils.py",
        file_content="def foo():\n    pass",
        review_comment="Add docstring to function",
        severity="low"
    )

    if result.status == CoderStatus.PATCH:
        # Apply the patch
        ...
    else:
        # Log the skip reason
        logger.info(f"Coder skipped: {result.reason}")
"""
import ast
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

from core.agents import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class CoderStatus(str, Enum):
    """Status of coder output."""
    SKIPPED = "skipped"
    PATCH = "patch"


# Schema version for backward-compatible evolution (consistent with ReviewOutcome)
CODER_OUTPUT_SCHEMA_VERSION = 1


@dataclass
class CoderOutput:
    """Structured output from SimpleCoder (Final Output Schema).

    This is the enriched output that downstream consumers receive.
    The LLM only outputs {status, reason, patch}; the system adds
    schema_version, file_path, and syntax_valid.

    Three Don'ts Principle #1: Low Confidence = Abort
    If the coder is not 100% confident, it returns status=skipped.

    Attributes:
        status: "skipped" or "patch"
        reason: Required if status is "skipped", explains why
        patch: Required if status is "patch", the code fix
        file_path: Path to the file being modified (system-added)
        syntax_valid: Whether the patch passed syntax check (system-added, Python only)
    """
    status: CoderStatus
    reason: Optional[str] = None
    patch: Optional[str] = None
    file_path: Optional[str] = None
    syntax_valid: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns the Final CoderOutput Schema with schema_version.
        """
        result: Dict[str, Any] = {
            "schema_version": CODER_OUTPUT_SCHEMA_VERSION,
            "status": self.status.value
        }
        if self.reason is not None:
            result["reason"] = self.reason
        if self.patch is not None:
            result["patch"] = self.patch
        if self.file_path is not None:
            result["file_path"] = self.file_path
        if self.syntax_valid is not None:
            result["syntax_valid"] = self.syntax_valid
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def create_skipped(cls, reason: str, file_path: Optional[str] = None) -> "CoderOutput":
        """Create a skipped output."""
        return cls(
            status=CoderStatus.SKIPPED,
            reason=reason,
            file_path=file_path
        )

    @classmethod
    def create_patch(
        cls,
        patch_content: str,
        file_path: Optional[str] = None,
        syntax_valid: Optional[bool] = None
    ) -> "CoderOutput":
        """Create a patch output."""
        return cls(
            status=CoderStatus.PATCH,
            patch=patch_content,
            file_path=file_path,
            syntax_valid=syntax_valid
        )


def validate_python_syntax(code: str, file_path: str = "<string>") -> tuple:
    """Validate Python syntax using ast.parse().

    Three Don'ts Principle #3: Verification Gate
    All modified .py files must pass syntax check before commit.

    Args:
        code: Python code to validate
        file_path: File path for error messages

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Event Codes (greppable):
        [SYNTAX_CHECK_PASS] - Code passed syntax validation
        [SYNTAX_CHECK_FAIL] - Code failed syntax validation
    """
    try:
        ast.parse(code)
        logger.info(f"[SYNTAX_CHECK_PASS] {file_path}")
        return True, None
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
        logger.warning(f"[SYNTAX_CHECK_FAIL] {file_path}: {error_msg}")
        return False, error_msg


def is_python_file(file_path: str) -> bool:
    """Check if a file is a Python file."""
    return file_path.lower().endswith(".py")


CODER_SYSTEM_PROMPT = """You are a precise code fixer. Your job is to fix code issues based on review comments.

IMPORTANT RULES:
1. If you are not 100% sure how to fix the issue, DO NOT change anything.
2. If the fix requires complex logic changes or architectural decisions, DO NOT change anything.
3. Only fix simple, localized issues like:
   - Variable naming
   - Adding docstrings
   - Fixing typos
   - Adding type hints
   - Simple formatting fixes

You MUST respond with ONLY a JSON object in this exact format:
{
    "status": "skipped" or "patch",
    "reason": "explanation (required if status is skipped)",
    "patch": "the fixed code (required if status is patch)"
}

If you skip, explain why in the reason field.
If you provide a patch, include the complete fixed code in the patch field.
"""

CODER_PROMPT_TEMPLATE = """Fix the following code issue:

File: {file_path}
Review Comment: {review_comment}
Severity: {severity}

Current Code:
```
{file_content}
```

Remember:
- If you're not 100% confident, output status: "skipped" with a reason
- If you can fix it, output status: "patch" with the fixed code
- Only fix simple, localized issues

Your response (JSON only):"""


class SimpleCoder(BaseAgent):
    """SimpleCoder Agent - D-1 Phase 0 (Proof-of-Life)

    This agent implements the Three Don'ts safety guardrails:
    1. Low Confidence = Abort (structured output)
    2. Side-effect Gate (handled by Router via autofix_gate)
    3. Verification Gate (Python syntax check)

    Attributes:
        agent_id: "simple_coder"
    """

    def __init__(self):
        """Initialize SimpleCoder."""
        super().__init__(agent_id="simple_coder")
        logger.info("[SimpleCoder] Initialized with Three Don'ts safety guardrails")

    def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the coder's main task.

        Args:
            input: AgentInput containing:
                - task_id: Unique task identifier
                - prompt: The fix prompt
                - context: Dict with file_path, file_content, review_comment, severity

        Returns:
            AgentOutput with CoderOutput in data field
        """
        file_path = input.context.get("file_path", "")
        file_content = input.context.get("file_content", "")
        review_comment = input.context.get("review_comment", "")
        severity = input.context.get("severity", "low")

        if not file_path or not file_content:
            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error="Missing file_path or file_content in context",
                data=CoderOutput.create_skipped(
                    "Missing required context",
                    file_path=file_path
                ).to_dict()
            )

        coder_output = self.generate_fix(
            file_path=file_path,
            file_content=file_content,
            review_comment=review_comment,
            severity=severity
        )

        return AgentOutput(
            task_id=input.task_id,
            success=coder_output.status == CoderStatus.PATCH,
            data=coder_output.to_dict()
        )

    def generate_fix(
        self,
        file_path: str,
        file_content: str,
        review_comment: str,
        severity: str = "low"
    ) -> CoderOutput:
        """Generate a fix for a code issue.

        This method:
        1. Calls LLM to generate a fix (or skip)
        2. Parses the structured JSON response
        3. Validates Python syntax if applicable
        4. Returns CoderOutput

        Args:
            file_path: Path to the file being fixed
            file_content: Current content of the file
            review_comment: Review comment describing the issue
            severity: Severity of the issue (low/medium/high/critical)

        Returns:
            CoderOutput with status, reason/patch, and syntax_valid

        Event Codes (greppable):
            [CODER_SKIP] - Coder decided to skip (low confidence)
            [CODER_PATCH] - Coder generated a patch
            [CODER_SYNTAX_ABORT] - Patch failed syntax check, aborting
        """
        prompt = CODER_PROMPT_TEMPLATE.format(
            file_path=file_path,
            file_content=file_content,
            review_comment=review_comment,
            severity=severity
        )

        try:
            result = self.call_llm(
                prompt=prompt,
                task_type="coding",
                risk_level="low",
                system_prompt=CODER_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=2000,
                json_mode=True
            )

            content = result.get("content", "")
            return self._parse_llm_response(content, file_path)

        except Exception as e:
            logger.error(f"[SimpleCoder] LLM call failed: {e}")
            return CoderOutput.create_skipped(
                f"LLM call failed: {str(e)}",
                file_path=file_path
            )

    def _parse_llm_response(
        self,
        response: str,
        file_path: str
    ) -> CoderOutput:
        """Parse LLM response and validate.

        Args:
            response: Raw LLM response (expected JSON)
            file_path: File path for context

        Returns:
            CoderOutput from parsed response
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"[SimpleCoder] Failed to parse JSON: {e}")
            return CoderOutput.create_skipped(
                f"Failed to parse LLM response as JSON: {str(e)}",
                file_path=file_path
            )

        status_str = data.get("status", "").lower()

        if status_str == "skipped":
            reason = data.get("reason", "No reason provided")
            logger.info(f"[CODER_SKIP] {file_path}: {reason}")
            return CoderOutput.create_skipped(reason, file_path=file_path)

        if status_str == "patch":
            patch_content = data.get("patch", "")
            if not patch_content:
                logger.warning("[SimpleCoder] Patch status but no patch content")
                return CoderOutput.create_skipped(
                    "LLM returned patch status but no patch content",
                    file_path=file_path
                )

            syntax_valid = None
            if is_python_file(file_path):
                is_valid, error_msg = validate_python_syntax(patch_content, file_path)
                syntax_valid = is_valid

                if not is_valid:
                    logger.warning(
                        f"[CODER_SYNTAX_ABORT] {file_path}: {error_msg}"
                    )
                    return CoderOutput.create_skipped(
                        f"Syntax check failed: {error_msg}",
                        file_path=file_path
                    )

            logger.info(f"[CODER_PATCH] {file_path}: patch generated")
            return CoderOutput.create_patch(
                patch_content=patch_content,
                file_path=file_path,
                syntax_valid=syntax_valid
            )

        logger.warning(f"[SimpleCoder] Unknown status: {status_str}")
        return CoderOutput.create_skipped(
            f"Unknown status from LLM: {status_str}",
            file_path=file_path
        )


_CACHED_CODER: Optional[SimpleCoder] = None


def get_simple_coder() -> SimpleCoder:
    """Factory function to get SimpleCoder instance.

    Returns cached instance to avoid repeated initialization.

    Returns:
        SimpleCoder instance
    """
    global _CACHED_CODER
    if _CACHED_CODER is None:
        _CACHED_CODER = SimpleCoder()
    return _CACHED_CODER
