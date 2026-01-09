"""
SeniorCoder Agent - D-2 Reasoning-First Architecture

Issue #2761: D-2 Senior Coder Logic (Tier 1)
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family

This module implements the SeniorCoder agent with reasoning-first architecture:
1. Analyze task complexity before coding
2. Design architecture and file structure
3. Generate implementation spec for JuniorCoder
4. Review and approve JuniorCoder's output

Workflow:
---------
User Request
    |
    v
+-------------+
|SeniorCoder  | (Tier 1: reasoning model)
|  Reasoning  |
+-------------+
    |
    v (Architecture Spec)
+-------------+
|JuniorCoder  | (Tier 2: GeneralCoder/SimpleCoder)
|Implementation|
+-------------+
    |
    v (Code)
+-------------+
|SeniorCoder  | (Review)
|  Approval   |
+-------------+

Schema Design:
--------------
1. Architecture Spec Schema (SeniorCoder output for JuniorCoder):
   {
       "schema_version": 1,
       "task_analysis": {
           "complexity": "simple" | "moderate" | "complex",
           "reasoning": "string explaining the analysis"
       },
       "architecture": {
           "files_to_modify": ["path1", "path2", ...],
           "files_to_create": ["path1", "path2", ...],
           "dependencies": {"file1": ["file2", "file3"], ...}
       },
       "implementation_plan": [
           {
               "file_path": "string",
               "action": "modify" | "create",
               "description": "what to do",
               "function_signatures": ["def foo(x: int) -> str", ...],
               "test_cases": ["test description 1", ...]
           },
           ...
       ],
       "constraints": ["constraint 1", "constraint 2", ...],
       "abort_reason": "string (present if complexity is too high)"
   }

2. Review Result Schema (SeniorCoder review of JuniorCoder output):
   {
       "schema_version": 1,
       "approved": bool,
       "feedback": "string",
       "required_changes": ["change 1", "change 2", ...]
   }

Usage:
    from coder.senior_coder import get_senior_coder, ArchitectureSpec

    senior = get_senior_coder()
    spec = senior.analyze_and_plan(
        task_description="Add user authentication",
        files=[
            {"path": "src/auth.py", "content": "..."},
            {"path": "src/routes.py", "content": "..."},
        ]
    )

    if spec.task_analysis.complexity != "complex":
        # Proceed with JuniorCoder
        ...
    else:
        # Task too complex, escalate to human
        logger.info(f"Task too complex: {spec.abort_reason}")
"""
import json
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

from core.agents import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Complexity level of a coding task."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class FileAction(str, Enum):
    """Action to perform on a file."""
    MODIFY = "modify"
    CREATE = "create"


# Schema version for backward-compatible evolution
ARCHITECTURE_SPEC_SCHEMA_VERSION = 1
REVIEW_RESULT_SCHEMA_VERSION = 1

# Maximum files SeniorCoder can plan for (aligned with GeneralCoder limit)
MAX_FILES_IN_PLAN = 5

# Maximum characters to include from a file in the context prompt
MAX_FILE_CONTEXT_LENGTH = 2000


# =============================================================================
# JSON Schema Definitions for SeniorCoder Output Validation
# Issue: [P2] SeniorCoder JSON Schema - 驗證 spec 格式，增加決策可靠性
# Blueprint: Section 9.1 可預測性 - Makes output format predictable
# =============================================================================

ARCHITECTURE_SPEC_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["task_analysis"],
    "properties": {
        "task_analysis": {
            "type": "object",
            "required": ["complexity", "reasoning"],
            "properties": {
                "complexity": {
                    "type": "string",
                    "enum": ["simple", "moderate", "complex"]
                },
                "reasoning": {"type": "string"}
            }
        },
        "architecture": {
            "type": "object",
            "properties": {
                "files_to_modify": {"type": "array", "items": {"type": "string"}},
                "files_to_create": {"type": "array", "items": {"type": "string"}},
                "dependencies": {"type": "object"}
            }
        },
        "implementation_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["file_path", "action", "description"],
                "properties": {
                    "file_path": {"type": "string"},
                    "action": {"type": "string", "enum": ["modify", "create"]},
                    "description": {"type": "string"},
                    "function_signatures": {"type": "array", "items": {"type": "string"}},
                    "test_cases": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "constraints": {"type": "array", "items": {"type": "string"}},
        "abort_reason": {"type": "string"}
    }
}

REVIEW_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["approved", "feedback"],
    "properties": {
        "approved": {"type": "boolean"},
        "feedback": {"type": "string"},
        "required_changes": {"type": "array", "items": {"type": "string"}}
    }
}


@dataclass
class SchemaValidationResult:
    """Result of JSON schema validation.

    Attributes:
        is_valid: Whether the data passed validation
        errors: List of validation error messages
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)


def validate_against_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    path: str = ""
) -> SchemaValidationResult:
    """Validate data against a JSON schema definition.

    This is a lightweight schema validator that checks:
    - Required fields presence
    - Type correctness (string, boolean, array, object)
    - Enum value constraints

    Args:
        data: The data to validate
        schema: The JSON schema definition
        path: Current path in the data structure (for error messages)

    Returns:
        SchemaValidationResult with validation status and errors

    Event Codes (greppable):
        [SENIOR_CODER_SCHEMA_VALID] - Schema validation passed
        [SENIOR_CODER_SCHEMA_INVALID] - Schema validation failed
    """
    errors: List[str] = []

    # Check if data is the expected type
    expected_type = schema.get("type")
    if expected_type:
        if expected_type == "object" and not isinstance(data, dict):
            errors.append(f"{path or 'root'}: expected object, got {type(data).__name__}")
            return SchemaValidationResult(is_valid=False, errors=errors)
        elif expected_type == "array" and not isinstance(data, list):
            errors.append(f"{path or 'root'}: expected array, got {type(data).__name__}")
            return SchemaValidationResult(is_valid=False, errors=errors)
        elif expected_type == "string" and not isinstance(data, str):
            errors.append(f"{path or 'root'}: expected string, got {type(data).__name__}")
            return SchemaValidationResult(is_valid=False, errors=errors)
        elif expected_type == "boolean" and not isinstance(data, bool):
            errors.append(f"{path or 'root'}: expected boolean, got {type(data).__name__}")
            return SchemaValidationResult(is_valid=False, errors=errors)

    # Check enum constraint
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path or 'root'}: value '{data}' not in allowed values {schema['enum']}")

    # For objects, check required fields and validate properties
    if expected_type == "object" and isinstance(data, dict):
        required_fields = schema.get("required", [])
        for field_name in required_fields:
            if field_name not in data:
                errors.append(f"{path or 'root'}: missing required field '{field_name}'")

        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                prop_path = f"{path}.{prop_name}" if path else prop_name
                prop_result = validate_against_schema(data[prop_name], prop_schema, prop_path)
                errors.extend(prop_result.errors)

    # For arrays, validate items
    if expected_type == "array" and isinstance(data, list):
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data):
                item_path = f"{path}[{i}]" if path else f"[{i}]"
                item_result = validate_against_schema(item, items_schema, item_path)
                errors.extend(item_result.errors)

    return SchemaValidationResult(is_valid=len(errors) == 0, errors=errors)


@dataclass
class TaskAnalysis:
    """Analysis of task complexity.

    Attributes:
        complexity: simple/moderate/complex
        reasoning: Explanation of the complexity assessment
    """
    complexity: TaskComplexity
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "complexity": self.complexity.value,
            "reasoning": self.reasoning,
        }


@dataclass
class ArchitecturePlan:
    """Architecture plan for the implementation.

    Attributes:
        files_to_modify: List of existing files to modify
        files_to_create: List of new files to create
        dependencies: Map of file dependencies
    """
    files_to_modify: List[str] = field(default_factory=list)
    files_to_create: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "files_to_modify": self.files_to_modify,
            "files_to_create": self.files_to_create,
            "dependencies": self.dependencies,
        }


@dataclass
class ImplementationStep:
    """Single step in the implementation plan.

    Attributes:
        file_path: Path to the file
        action: modify or create
        description: What to do in this file
        function_signatures: Expected function signatures
        test_cases: Test case descriptions
    """
    file_path: str
    action: FileAction
    description: str
    function_signatures: List[str] = field(default_factory=list)
    test_cases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "action": self.action.value,
            "description": self.description,
            "function_signatures": self.function_signatures,
            "test_cases": self.test_cases,
        }


@dataclass
class ArchitectureSpec:
    """Complete architecture specification from SeniorCoder.

    This is the output that JuniorCoder (GeneralCoder/SimpleCoder) receives
    to guide implementation.

    Attributes:
        task_analysis: Complexity analysis
        architecture: File structure plan
        implementation_plan: Step-by-step implementation guide
        constraints: Implementation constraints
        abort_reason: Present if task is too complex
    """
    task_analysis: TaskAnalysis
    architecture: ArchitecturePlan = field(default_factory=ArchitecturePlan)
    implementation_plan: List[ImplementationStep] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    abort_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "schema_version": ARCHITECTURE_SPEC_SCHEMA_VERSION,
            "task_analysis": self.task_analysis.to_dict(),
            "architecture": self.architecture.to_dict(),
            "implementation_plan": [step.to_dict() for step in self.implementation_plan],
            "constraints": self.constraints,
        }
        if self.abort_reason:
            result["abort_reason"] = self.abort_reason
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @property
    def should_proceed(self) -> bool:
        """Check if implementation should proceed."""
        return (
            self.task_analysis.complexity != TaskComplexity.COMPLEX
            and self.abort_reason is None
        )

    @classmethod
    def create_abort(cls, reason: str, reasoning: str) -> "ArchitectureSpec":
        """Create an aborted spec (task too complex)."""
        return cls(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.COMPLEX,
                reasoning=reasoning
            ),
            abort_reason=reason
        )


@dataclass
class ReviewResult:
    """Result of SeniorCoder reviewing JuniorCoder's output.

    Attributes:
        approved: Whether the implementation is approved
        feedback: Feedback on the implementation
        required_changes: List of required changes if not approved
    """
    approved: bool
    feedback: str
    required_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "schema_version": REVIEW_RESULT_SCHEMA_VERSION,
            "approved": self.approved,
            "feedback": self.feedback,
        }
        if self.required_changes:
            result["required_changes"] = self.required_changes
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


SENIOR_CODER_SYSTEM_PROMPT = """You are a senior software architect. Your job is to analyze coding tasks and create implementation plans.

IMPORTANT RULES:
1. Analyze the task complexity first (simple/moderate/complex)
2. If the task is complex (requires architectural changes, new patterns, or affects many files), mark it as complex and explain why
3. For simple/moderate tasks, create a detailed implementation plan
4. Maximum 5 files can be modified/created
5. Be conservative - if unsure, mark as complex

You MUST respond with ONLY a JSON object in this exact format:
{
    "task_analysis": {
        "complexity": "simple" | "moderate" | "complex",
        "reasoning": "explanation of complexity assessment"
    },
    "architecture": {
        "files_to_modify": ["path1", "path2"],
        "files_to_create": ["path3"],
        "dependencies": {"path1": ["path2"]}
    },
    "implementation_plan": [
        {
            "file_path": "path/to/file.py",
            "action": "modify" | "create",
            "description": "what to do",
            "function_signatures": ["def foo(x: int) -> str"],
            "test_cases": ["test that foo returns correct value"]
        }
    ],
    "constraints": ["constraint 1", "constraint 2"],
    "abort_reason": "reason (only if complexity is complex)"
}
"""

SENIOR_CODER_PLAN_TEMPLATE = """Analyze the following coding task and create an implementation plan:

Task Description: {task_description}

Available Files:
{files_context}

Remember:
- Assess complexity first (simple/moderate/complex)
- If complex, provide abort_reason and don't create detailed plan
- Maximum 5 files can be modified/created
- Be conservative with complexity assessment

Your response (JSON only):"""

SENIOR_CODER_REVIEW_SYSTEM_PROMPT = """You are a senior software architect reviewing code implementation.

Your job is to:
1. Check if the implementation matches the original spec
2. Verify code quality and correctness
3. Approve or request changes

You MUST respond with ONLY a JSON object in this exact format:
{
    "approved": true | false,
    "feedback": "overall feedback",
    "required_changes": ["change 1", "change 2"] (only if not approved)
}
"""

SENIOR_CODER_REVIEW_TEMPLATE = """Review the following implementation against the original spec:

Original Task: {task_description}

Original Spec:
{spec_summary}

Implementation:
{implementation_summary}

Your response (JSON only):"""


class SeniorCoder(BaseAgent):
    """SeniorCoder Agent - D-2 Reasoning-First Architecture

    This agent implements reasoning-first development:
    1. Analyze task complexity
    2. Design architecture
    3. Generate implementation spec
    4. Review implementation

    Attributes:
        agent_id: "senior_coder"
    """

    def __init__(self):
        """Initialize SeniorCoder."""
        super().__init__(agent_id="senior_coder")
        logger.info("[SeniorCoder] Initialized with reasoning-first architecture (D-2)")

    def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the senior coder's main task.

        Args:
            input: AgentInput containing:
                - task_id: Unique task identifier
                - prompt: The task description
                - context: Dict with files, mode (plan/review)

        Returns:
            AgentOutput with ArchitectureSpec or ReviewResult in data field
        """
        mode = input.context.get("mode", "plan")
        task_description = input.prompt
        files = input.context.get("files", [])

        if mode == "plan":
            spec = self.analyze_and_plan(
                task_description=task_description,
                files=files
            )
            return AgentOutput(
                task_id=input.task_id,
                success=spec.should_proceed,
                data=spec.to_dict()
            )
        elif mode == "review":
            spec_dict = input.context.get("spec", {})
            implementation = input.context.get("implementation", {})
            result = self.review_implementation(
                task_description=task_description,
                spec_dict=spec_dict,
                implementation=implementation
            )
            return AgentOutput(
                task_id=input.task_id,
                success=result.approved,
                data=result.to_dict()
            )
        else:
            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error=f"Unknown mode: {mode}",
                data={}
            )

    def analyze_and_plan(
        self,
        task_description: str,
        files: List[Dict[str, str]]
    ) -> ArchitectureSpec:
        """Analyze task and create implementation plan.

        This method:
        1. Analyzes task complexity
        2. Designs architecture if feasible
        3. Creates step-by-step implementation plan
        4. Returns ArchitectureSpec

        Args:
            task_description: Description of the coding task
            files: List of dicts with "path" and "content" keys

        Returns:
            ArchitectureSpec with analysis and plan

        Event Codes (greppable):
            [SENIOR_CODER_PLAN_SIMPLE] - Task assessed as simple
            [SENIOR_CODER_PLAN_MODERATE] - Task assessed as moderate
            [SENIOR_CODER_PLAN_COMPLEX] - Task assessed as complex, aborting
            [SENIOR_CODER_PLAN_ERROR] - Error during planning
        """
        files_context = self._build_files_context(files)

        prompt = SENIOR_CODER_PLAN_TEMPLATE.format(
            task_description=task_description,
            files_context=files_context
        )

        try:
            result = self.call_llm(
                prompt=prompt,
                task_type="reasoning",
                risk_level="low",
                system_prompt=SENIOR_CODER_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=4000,
                json_mode=True
            )

            content = result.get("content", "")
            return self._parse_plan_response(content)

        except Exception as e:
            logger.error(f"[SENIOR_CODER_PLAN_ERROR] LLM call failed: {e}")
            return ArchitectureSpec.create_abort(
                reason=f"Planning failed: {str(e)}",
                reasoning="LLM call failed during planning phase"
            )

    def review_implementation(
        self,
        task_description: str,
        spec_dict: Dict[str, Any],
        implementation: Dict[str, Any]
    ) -> ReviewResult:
        """Review JuniorCoder's implementation.

        Args:
            task_description: Original task description
            spec_dict: Original ArchitectureSpec as dict
            implementation: Implementation result from JuniorCoder

        Returns:
            ReviewResult with approval status and feedback

        Event Codes (greppable):
            [SENIOR_CODER_REVIEW_APPROVED] - Implementation approved
            [SENIOR_CODER_REVIEW_REJECTED] - Implementation rejected
            [SENIOR_CODER_REVIEW_ERROR] - Error during review
        """
        spec_summary = json.dumps(spec_dict, indent=2)
        implementation_summary = json.dumps(implementation, indent=2)

        prompt = SENIOR_CODER_REVIEW_TEMPLATE.format(
            task_description=task_description,
            spec_summary=spec_summary,
            implementation_summary=implementation_summary
        )

        try:
            result = self.call_llm(
                prompt=prompt,
                task_type="reasoning",
                risk_level="low",
                system_prompt=SENIOR_CODER_REVIEW_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=2000,
                json_mode=True
            )

            content = result.get("content", "")
            return self._parse_review_response(content)

        except Exception as e:
            logger.error(f"[SENIOR_CODER_REVIEW_ERROR] LLM call failed: {e}")
            return ReviewResult(
                approved=False,
                feedback=f"Review failed: {str(e)}",
                required_changes=["Unable to complete review due to error"]
            )

    def _build_files_context(self, files: List[Dict[str, str]]) -> str:
        """Build context string from files for the prompt."""
        if not files:
            return "(No files provided)"

        context_parts = []
        for f in files:
            path = f.get("path", "unknown")
            content = f.get("content", "")
            # Truncate very long files
            if len(content) > MAX_FILE_CONTEXT_LENGTH:
                content = content[:MAX_FILE_CONTEXT_LENGTH] + "\n... (truncated)"
            context_parts.append(f"--- File: {path} ---\n```\n{content}\n```\n")
        return "\n".join(context_parts)

    def _parse_plan_response(self, response: str) -> ArchitectureSpec:
        """Parse LLM planning response with JSON schema validation.

        Validates the response against ARCHITECTURE_SPEC_SCHEMA before parsing.
        On validation failure, logs warning but continues with graceful degradation.

        Event Codes (greppable):
            [SENIOR_CODER_SCHEMA_VALID] - Schema validation passed
            [SENIOR_CODER_SCHEMA_INVALID] - Schema validation failed
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"[SeniorCoder] Failed to parse JSON: {e}")
            return ArchitectureSpec.create_abort(
                reason=f"Failed to parse planning response: {str(e)}",
                reasoning="JSON parsing failed"
            )

        # Validate against schema (observe-only, graceful degradation)
        validation_result = validate_against_schema(data, ARCHITECTURE_SPEC_SCHEMA)
        if validation_result.is_valid:
            logger.info(
                "[SENIOR_CODER_SCHEMA_VALID] Architecture spec schema validation passed",
                extra={
                    "operation": "schema_validation",
                    "schema_type": "architecture_spec",
                    "event_code": "SENIOR_CODER_SCHEMA_VALID",
                }
            )
        else:
            logger.warning(
                f"[SENIOR_CODER_SCHEMA_INVALID] Architecture spec schema validation failed: "
                f"{validation_result.errors}",
                extra={
                    "operation": "schema_validation",
                    "schema_type": "architecture_spec",
                    "event_code": "SENIOR_CODER_SCHEMA_INVALID",
                    "validation_errors": validation_result.errors,
                }
            )

        # Parse task analysis
        analysis_data = data.get("task_analysis", {})
        complexity_str = analysis_data.get("complexity", "complex").lower()
        try:
            complexity = TaskComplexity(complexity_str)
        except ValueError:
            complexity = TaskComplexity.COMPLEX

        task_analysis = TaskAnalysis(
            complexity=complexity,
            reasoning=analysis_data.get("reasoning", "No reasoning provided")
        )

        # Check for abort
        abort_reason = data.get("abort_reason")
        if complexity == TaskComplexity.COMPLEX:
            logger.info(f"[SENIOR_CODER_PLAN_COMPLEX] {abort_reason or task_analysis.reasoning}")
            return ArchitectureSpec.create_abort(
                reason=abort_reason or "Task complexity too high",
                reasoning=task_analysis.reasoning
            )

        # Parse architecture
        arch_data = data.get("architecture", {})
        files_to_modify = arch_data.get("files_to_modify", [])
        files_to_create = arch_data.get("files_to_create", [])

        # Validate file count
        total_files = len(files_to_modify) + len(files_to_create)
        if total_files > MAX_FILES_IN_PLAN:
            logger.warning(
                f"[SeniorCoder] Too many files in plan: {total_files} > {MAX_FILES_IN_PLAN}"
            )
            return ArchitectureSpec.create_abort(
                reason=f"Plan affects too many files: {total_files} > {MAX_FILES_IN_PLAN}",
                reasoning="File count exceeds maximum allowed"
            )

        architecture = ArchitecturePlan(
            files_to_modify=files_to_modify,
            files_to_create=files_to_create,
            dependencies=arch_data.get("dependencies", {})
        )

        # Parse implementation plan
        plan_data = data.get("implementation_plan", [])
        implementation_plan = []
        for step_data in plan_data:
            action_str = step_data.get("action", "modify").lower()
            try:
                action = FileAction(action_str)
            except ValueError:
                action = FileAction.MODIFY

            step = ImplementationStep(
                file_path=step_data.get("file_path", ""),
                action=action,
                description=step_data.get("description", ""),
                function_signatures=step_data.get("function_signatures", []),
                test_cases=step_data.get("test_cases", [])
            )
            implementation_plan.append(step)

        constraints = data.get("constraints", [])

        log_level = "[SENIOR_CODER_PLAN_SIMPLE]" if complexity == TaskComplexity.SIMPLE else "[SENIOR_CODER_PLAN_MODERATE]"
        logger.info(f"{log_level} Plan created with {len(implementation_plan)} steps")

        return ArchitectureSpec(
            task_analysis=task_analysis,
            architecture=architecture,
            implementation_plan=implementation_plan,
            constraints=constraints
        )

    def _parse_review_response(self, response: str) -> ReviewResult:
        """Parse LLM review response with JSON schema validation.

        Validates the response against REVIEW_RESULT_SCHEMA before parsing.
        On validation failure, logs warning but continues with graceful degradation.

        Event Codes (greppable):
            [SENIOR_CODER_SCHEMA_VALID] - Schema validation passed
            [SENIOR_CODER_SCHEMA_INVALID] - Schema validation failed
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"[SeniorCoder] Failed to parse review JSON: {e}")
            return ReviewResult(
                approved=False,
                feedback=f"Failed to parse review response: {str(e)}",
                required_changes=["Review parsing failed"]
            )

        # Validate against schema (observe-only, graceful degradation)
        validation_result = validate_against_schema(data, REVIEW_RESULT_SCHEMA)
        if validation_result.is_valid:
            logger.info(
                "[SENIOR_CODER_SCHEMA_VALID] Review result schema validation passed",
                extra={
                    "operation": "schema_validation",
                    "schema_type": "review_result",
                    "event_code": "SENIOR_CODER_SCHEMA_VALID",
                }
            )
        else:
            logger.warning(
                f"[SENIOR_CODER_SCHEMA_INVALID] Review result schema validation failed: "
                f"{validation_result.errors}",
                extra={
                    "operation": "schema_validation",
                    "schema_type": "review_result",
                    "event_code": "SENIOR_CODER_SCHEMA_INVALID",
                    "validation_errors": validation_result.errors,
                }
            )

        approved = data.get("approved", False)
        feedback = data.get("feedback", "No feedback provided")
        required_changes = data.get("required_changes", [])

        if approved:
            logger.info("[SENIOR_CODER_REVIEW_APPROVED] Implementation approved")
        else:
            logger.info(f"[SENIOR_CODER_REVIEW_REJECTED] {len(required_changes)} changes required")

        return ReviewResult(
            approved=approved,
            feedback=feedback,
            required_changes=required_changes
        )


_CACHED_SENIOR_CODER: Optional[SeniorCoder] = None
_CACHED_SENIOR_CODER_LOCK = threading.Lock()


def get_senior_coder() -> SeniorCoder:
    """Factory function to get SeniorCoder instance.

    Returns cached instance to avoid repeated initialization.
    Thread-safe via module-level lock.

    Returns:
        SeniorCoder instance
    """
    global _CACHED_SENIOR_CODER
    with _CACHED_SENIOR_CODER_LOCK:
        if _CACHED_SENIOR_CODER is None:
            _CACHED_SENIOR_CODER = SeniorCoder()
    return _CACHED_SENIOR_CODER
