"""
GeneralCoder Agent - D-1b Multi-file Extension

Issue #2760: D-1b Multi-file GeneralCoder (<=5 files)
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
CTO Approved: 2025-12-30

This module implements the GeneralCoder agent for multi-file editing with:
1. Multi-file support (<=5 files)
2. Import relationship understanding
3. Per-file syntax validation
4. Atomic commit semantics via commit_files()

Schema Design:
--------------
There are TWO distinct schemas in this module:

1. LLM Response Schema (what the LLM must output):
   {
       "status": "skipped" | "patch",
       "reason": "string (required if skipped)",
       "patches": [
           {"file_path": "string", "patch": "string"},
           ...
       ] (required if patch, max 5 files)
   }
   This is the ONLY format the LLM should emit. Keep it minimal and strict.

2. Final MultiFileCoderOutput Schema (what downstream consumers receive):
   {
       "schema_version": 1,
       "status": "skipped" | "patch",
       "reason": "string (present if skipped)",
       "patches": [
           {
               "file_path": "string",
               "patch": "string",
               "syntax_valid": bool | null (Python files only)
           },
           ...
       ] (present if patch),
       "files_affected": int (system-added)
   }
   The system enriches the LLM response with syntax_valid per file.

Usage:
    from coder.general_coder import get_general_coder, MultiFileCoderOutput

    coder = get_general_coder()
    result = coder.generate_multi_file_fix(
        files=[
            {"path": "src/utils.py", "content": "def foo():\n    pass"},
            {"path": "src/main.py", "content": "from utils import foo"},
        ],
        review_comment="Add docstrings to functions",
        severity="low"
    )

    if result.status == CoderStatus.PATCH:
        # Apply patches atomically via commit_files()
        ...
    else:
        # Log the skip reason
        logger.info(f"Coder skipped: {result.reason}")
"""
import ast
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from core.agents import BaseAgent, AgentInput, AgentOutput
from coder.simple_coder import (
    CoderStatus,
    validate_python_syntax,
    is_python_file,
    CODER_OUTPUT_SCHEMA_VERSION,
)

logger = logging.getLogger(__name__)


# Schema field definitions - Single Source of Truth for drift detection tests
# These sets define which fields belong to each schema layer
MULTI_FILE_LLM_RESPONSE_FIELDS = frozenset({"status", "reason", "patches"})
MULTI_FILE_SYSTEM_ADDED_FIELDS = frozenset({"schema_version", "files_affected"})
FILE_PATCH_LLM_FIELDS = frozenset({"file_path", "patch"})
FILE_PATCH_SYSTEM_FIELDS = frozenset({"syntax_valid"})

# D-1b guardrail: maximum files per operation
MAX_FILES_PER_OPERATION = 5


@dataclass
class FilePatch:
    """Single file patch within a multi-file operation.

    Attributes:
        file_path: Path to the file being modified
        patch: The new file content (full replacement)
        syntax_valid: Whether the patch passed syntax check (Python files only)
    """
    file_path: str
    patch: str
    syntax_valid: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "file_path": self.file_path,
            "patch": self.patch,
        }
        if self.syntax_valid is not None:
            result["syntax_valid"] = self.syntax_valid
        return result


@dataclass
class MultiFileCoderOutput:
    """Structured output from GeneralCoder (Final Output Schema).

    This is the enriched output that downstream consumers receive.
    The LLM only outputs {status, reason, patches}; the system adds
    schema_version, syntax_valid per file, and files_affected.

    Three Don'ts Principle #1: Low Confidence = Abort
    If the coder is not 100% confident, it returns status=skipped.

    Attributes:
        status: "skipped" or "patch"
        reason: Required if status is "skipped", explains why
        patches: List of FilePatch objects (required if status is "patch")
        files_affected: Number of files affected (system-added)
    """
    status: CoderStatus
    reason: Optional[str] = None
    patches: List[FilePatch] = field(default_factory=list)
    files_affected: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns the Final MultiFileCoderOutput Schema with schema_version.
        """
        result: Dict[str, Any] = {
            "schema_version": CODER_OUTPUT_SCHEMA_VERSION,
            "status": self.status.value,
            "files_affected": self.files_affected,
        }
        if self.reason is not None:
            result["reason"] = self.reason
        if self.patches:
            result["patches"] = [p.to_dict() for p in self.patches]
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def create_skipped(cls, reason: str) -> "MultiFileCoderOutput":
        """Create a skipped output."""
        return cls(
            status=CoderStatus.SKIPPED,
            reason=reason,
            files_affected=0
        )

    @classmethod
    def create_patch(
        cls,
        patches: List[FilePatch]
    ) -> "MultiFileCoderOutput":
        """Create a patch output."""
        return cls(
            status=CoderStatus.PATCH,
            patches=patches,
            files_affected=len(patches)
        )


def parse_python_imports(code: str, file_path: str = "<string>") -> List[str]:
    """Parse Python imports from source code.

    D-1b: Import relationship understanding
    Extracts local imports that can be resolved to repo-relative paths.

    Args:
        code: Python source code
        file_path: File path for error messages

    Returns:
        List of imported module names (local imports only)

    Event Codes (greppable):
        [IMPORT_PARSE_SUCCESS] - Successfully parsed imports
        [IMPORT_PARSE_FAIL] - Failed to parse imports (syntax error)
    """
    imports = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        logger.debug(f"[IMPORT_PARSE_SUCCESS] {file_path}: found {len(imports)} imports")
        return imports
    except SyntaxError as e:
        logger.warning(f"[IMPORT_PARSE_FAIL] {file_path}: {e}")
        return []


def resolve_local_import(
    import_name: str,
    base_file_path: str,
    available_files: List[str]
) -> Optional[str]:
    """Resolve a local import to a file path.

    Attempts to find the imported module in the available files list.
    Only resolves local imports (not stdlib or third-party).

    Args:
        import_name: Module name (e.g., "utils", "core.agents")
        base_file_path: Path of the file doing the import
        available_files: List of available file paths in the repo

    Returns:
        Resolved file path or None if not found/not local
    """
    # Convert module name to potential file paths
    module_path = import_name.replace(".", "/")
    potential_paths = [
        f"{module_path}.py",
        f"{module_path}/__init__.py",
    ]

    # Also try relative to the base file's directory
    import os
    base_dir = os.path.dirname(base_file_path)
    if base_dir:
        potential_paths.extend([
            f"{base_dir}/{module_path}.py",
            f"{base_dir}/{module_path}/__init__.py",
        ])

    for path in potential_paths:
        # Normalize path
        normalized = os.path.normpath(path)
        if normalized in available_files:
            return normalized

    return None


GENERAL_CODER_SYSTEM_PROMPT = """You are a precise multi-file code fixer. Your job is to fix code issues that may span multiple files.

IMPORTANT RULES:
1. If you are not 100% sure how to fix the issue, DO NOT change anything.
2. If the fix requires complex logic changes or architectural decisions, DO NOT change anything.
3. Only fix simple, localized issues like:
   - Variable naming
   - Adding docstrings
   - Fixing typos
   - Adding type hints
   - Simple formatting fixes
   - Import fixes
4. You can modify up to 5 files maximum.
5. Each file patch must contain the COMPLETE new file content.

You MUST respond with ONLY a JSON object in this exact format:
{
    "status": "skipped" or "patch",
    "reason": "explanation (required if status is skipped)",
    "patches": [
        {"file_path": "path/to/file.py", "patch": "complete new file content"},
        ...
    ] (required if status is patch, max 5 files)
}

If you skip, explain why in the reason field.
If you provide patches, include the complete fixed code for each file.
"""

GENERAL_CODER_PROMPT_TEMPLATE = """Fix the following code issue that may span multiple files:

Review Comment: {review_comment}
Severity: {severity}

Files to consider:
{files_context}

Remember:
- If you're not 100% confident, output status: "skipped" with a reason
- If you can fix it, output status: "patch" with the fixed code for each affected file
- Only fix simple, localized issues
- Maximum 5 files can be modified

Your response (JSON only):"""


class GeneralCoder(BaseAgent):
    """GeneralCoder Agent - D-1b Multi-file Extension

    This agent implements multi-file editing with:
    1. Multi-file support (<=5 files)
    2. Import relationship understanding
    3. Per-file syntax validation
    4. Three Don'ts safety guardrails (inherited from SimpleCoder design)

    Attributes:
        agent_id: "general_coder"
    """

    def __init__(self):
        """Initialize GeneralCoder."""
        super().__init__(agent_id="general_coder")
        logger.info("[GeneralCoder] Initialized with multi-file support (D-1b)")

    def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the coder's main task.

        Args:
            input: AgentInput containing:
                - task_id: Unique task identifier
                - prompt: The fix prompt
                - context: Dict with files, review_comment, severity

        Returns:
            AgentOutput with MultiFileCoderOutput in data field
        """
        files = input.context.get("files", [])
        review_comment = input.context.get("review_comment", "")
        severity = input.context.get("severity", "low")

        if not files:
            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error="Missing files in context",
                data=MultiFileCoderOutput.create_skipped(
                    "Missing required context: no files provided"
                ).to_dict()
            )

        if len(files) > MAX_FILES_PER_OPERATION:
            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error=f"Too many files: {len(files)} > {MAX_FILES_PER_OPERATION}",
                data=MultiFileCoderOutput.create_skipped(
                    f"Too many files: {len(files)} > {MAX_FILES_PER_OPERATION}"
                ).to_dict()
            )

        coder_output = self.generate_multi_file_fix(
            files=files,
            review_comment=review_comment,
            severity=severity
        )

        return AgentOutput(
            task_id=input.task_id,
            success=coder_output.status == CoderStatus.PATCH,
            data=coder_output.to_dict()
        )

    def generate_multi_file_fix(
        self,
        files: List[Dict[str, str]],
        review_comment: str,
        severity: str = "low"
    ) -> MultiFileCoderOutput:
        """Generate fixes for a multi-file code issue.

        This method:
        1. Builds context from all files
        2. Calls LLM to generate fixes (or skip)
        3. Parses the structured JSON response
        4. Validates Python syntax for each affected file
        5. Returns MultiFileCoderOutput

        Args:
            files: List of dicts with "path" and "content" keys
            review_comment: Review comment describing the issue
            severity: Severity of the issue (low/medium/high/critical)

        Returns:
            MultiFileCoderOutput with status, reason/patches, and syntax_valid per file

        Event Codes (greppable):
            [GENERAL_CODER_SKIP] - Coder decided to skip (low confidence)
            [GENERAL_CODER_PATCH] - Coder generated patches
            [GENERAL_CODER_SYNTAX_ABORT] - Patch failed syntax check, aborting
        """
        # Build files context for prompt
        files_context = self._build_files_context(files)

        prompt = GENERAL_CODER_PROMPT_TEMPLATE.format(
            review_comment=review_comment,
            severity=severity,
            files_context=files_context
        )

        try:
            result = self.call_llm(
                prompt=prompt,
                task_type="coding",
                risk_level="low",
                system_prompt=GENERAL_CODER_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=4000,  # Higher limit for multi-file
                json_mode=True
            )

            content = result.get("content", "")
            return self._parse_llm_response(content, files)

        except Exception as e:
            logger.error(f"[GeneralCoder] LLM call failed: {e}")
            return MultiFileCoderOutput.create_skipped(
                f"LLM call failed: {str(e)}"
            )

    def _build_files_context(self, files: List[Dict[str, str]]) -> str:
        """Build context string from files for the prompt.

        Args:
            files: List of dicts with "path" and "content" keys

        Returns:
            Formatted string with all file contents
        """
        context_parts = []
        for f in files:
            path = f.get("path", "unknown")
            content = f.get("content", "")
            context_parts.append(f"--- File: {path} ---\n```\n{content}\n```\n")
        return "\n".join(context_parts)

    def _parse_llm_response(
        self,
        response: str,
        original_files: List[Dict[str, str]]
    ) -> MultiFileCoderOutput:
        """Parse LLM response and validate.

        Args:
            response: Raw LLM response (expected JSON)
            original_files: Original files for context

        Returns:
            MultiFileCoderOutput from parsed response
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"[GeneralCoder] Failed to parse JSON: {e}")
            return MultiFileCoderOutput.create_skipped(
                f"Failed to parse LLM response as JSON: {str(e)}"
            )

        status_str = data.get("status", "").lower()

        if status_str == "skipped":
            reason = data.get("reason", "No reason provided")
            logger.info(f"[GENERAL_CODER_SKIP] {reason}")
            return MultiFileCoderOutput.create_skipped(reason)

        if status_str == "patch":
            patches_data = data.get("patches", [])
            if not patches_data:
                logger.warning("[GeneralCoder] Patch status but no patches")
                return MultiFileCoderOutput.create_skipped(
                    "LLM returned patch status but no patches"
                )

            if len(patches_data) > MAX_FILES_PER_OPERATION:
                logger.warning(
                    f"[GeneralCoder] Too many patches: {len(patches_data)} > {MAX_FILES_PER_OPERATION}"
                )
                return MultiFileCoderOutput.create_skipped(
                    f"Too many patches: {len(patches_data)} > {MAX_FILES_PER_OPERATION}"
                )

            # Validate and build FilePatch objects
            file_patches = []
            for patch_data in patches_data:
                file_path = patch_data.get("file_path", "")
                patch_content = patch_data.get("patch", "")

                if not file_path:
                    logger.warning("[GeneralCoder] Patch missing file_path")
                    return MultiFileCoderOutput.create_skipped(
                        "Patch missing file_path"
                    )

                if not patch_content:
                    logger.warning(f"[GeneralCoder] Empty patch for {file_path}")
                    return MultiFileCoderOutput.create_skipped(
                        f"Empty patch content for {file_path}"
                    )

                # Safety check: reject whitespace-only patches (Issue #3288)
                if not patch_content.strip():
                    logger.warning(
                        f"[GENERAL_CODER_WHITESPACE_ABORT] {file_path}: whitespace-only content"
                    )
                    return MultiFileCoderOutput.create_skipped(
                        f"Whitespace-only patch for {file_path}"
                    )

                # Path validation (no traversal)
                if ".." in file_path or file_path.startswith("/"):
                    logger.warning(
                        f"[GeneralCoder] Invalid path: {file_path}"
                    )
                    return MultiFileCoderOutput.create_skipped(
                        f"Invalid file path: {file_path}"
                    )

                # Syntax validation for Python files
                syntax_valid = None
                if is_python_file(file_path):
                    is_valid, error_msg = validate_python_syntax(patch_content, file_path)
                    syntax_valid = is_valid

                    if not is_valid:
                        logger.warning(
                            f"[GENERAL_CODER_SYNTAX_ABORT] {file_path}: {error_msg}"
                        )
                        return MultiFileCoderOutput.create_skipped(
                            f"Syntax check failed for {file_path}: {error_msg}"
                        )

                file_patches.append(FilePatch(
                    file_path=file_path,
                    patch=patch_content,
                    syntax_valid=syntax_valid
                ))

            logger.info(
                f"[GENERAL_CODER_PATCH] Generated patches for {len(file_patches)} files"
            )
            return MultiFileCoderOutput.create_patch(file_patches)

        logger.warning(f"[GeneralCoder] Unknown status: {status_str}")
        return MultiFileCoderOutput.create_skipped(
            f"Unknown status from LLM: {status_str}"
        )


_CACHED_GENERAL_CODER: Optional[GeneralCoder] = None
_CACHED_GENERAL_CODER_LOCK = threading.Lock()


def get_general_coder() -> GeneralCoder:
    """Factory function to get GeneralCoder instance.

    Returns cached instance to avoid repeated initialization.
    Thread-safe via module-level lock (per-process singleton;
    multiprocessing environments will have one instance per process).

    Returns:
        GeneralCoder instance
    """
    global _CACHED_GENERAL_CODER
    with _CACHED_GENERAL_CODER_LOCK:
        if _CACHED_GENERAL_CODER is None:
            _CACHED_GENERAL_CODER = GeneralCoder()
    return _CACHED_GENERAL_CODER
