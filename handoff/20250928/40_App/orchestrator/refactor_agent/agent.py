#!/usr/bin/env python3
"""
Refactor Agent - Phase 4 (#1818, #1888, #1889, #1890)

Automated TypeScript strict mode error fixing agent.
Runs nightly to fix TS errors and submit PRs automatically.

Design Principles:
- Autonomous: Runs without human intervention
- Incremental: Fixes a configurable number of errors per run (default: 10)
- Safe: Creates PRs for human review, never pushes directly to main
- Observable: Logs all actions and maintains progress metrics
- LLM-Powered: Uses LLM to generate actual code fixes (#1888)
- File Modification: Applies fixes to files with backup and rollback (#1889)
- PR Automation: Automatically creates PRs with changelog (#1890)
"""
import logging
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

TS_FIX_PROMPT_TEMPLATES: Dict[str, str] = {
    "null_check": """Fix the TypeScript error where an object is possibly 'null'.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix that adds proper null checking. Options include:
1. Optional chaining (?.)
2. Nullish coalescing (??)
3. Type guard (if statement)
4. Non-null assertion (!) - only if you're certain the value is never null

Return ONLY the fixed code snippet that should replace the problematic line(s).
Do not include explanations, just the code.""",

    "undefined_check": """Fix the TypeScript error where an object is possibly 'undefined'.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix that adds proper undefined checking. Options include:
1. Optional chaining (?.)
2. Default value assignment
3. Type guard (if statement)
4. Non-null assertion (!) - only if you're certain the value is defined

Return ONLY the fixed code snippet that should replace the problematic line(s).
Do not include explanations, just the code.""",

    "implicit_any": """Fix the TypeScript error where a parameter implicitly has an 'any' type.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix that adds an explicit type annotation. Infer the most appropriate type from:
1. How the parameter is used in the function body
2. The function name and context
3. Common TypeScript patterns

Return ONLY the fixed code snippet with the type annotation added.
Do not include explanations, just the code.""",

    "type_mismatch": """Fix the TypeScript type mismatch error.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix for the type mismatch. Options include:
1. Type assertion (as Type)
2. Type conversion function
3. Fixing the source value to match expected type
4. Updating the type definition

Return ONLY the fixed code snippet that resolves the type mismatch.
Do not include explanations, just the code.""",

    "property_missing": """Fix the TypeScript error where a property does not exist on a type.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix for the missing property. Options include:
1. Type assertion to a more specific type
2. Optional chaining if the property might not exist
3. Type guard to narrow the type
4. Using 'in' operator to check property existence

Return ONLY the fixed code snippet that resolves the missing property error.
Do not include explanations, just the code.""",

    "argument_type": """Fix the TypeScript error where an argument type is incompatible.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix for the argument type mismatch. Options include:
1. Type assertion (as Type)
2. Converting the value to the expected type
3. Using a type guard before the function call

Return ONLY the fixed code snippet that resolves the argument type error.
Do not include explanations, just the code.""",

    "unknown_type": """Fix the TypeScript error where an object is of type 'unknown'.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix for the unknown type. Options include:
1. Type assertion (as Type) if you know the actual type
2. Type guard (typeof, instanceof, or custom type guard)
3. Using 'as unknown as Type' for complex conversions

Return ONLY the fixed code snippet that properly handles the unknown type.
Do not include explanations, just the code.""",

    "binding_any": """Fix the TypeScript error where a binding element implicitly has an 'any' type.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix that adds explicit type annotation to the destructured binding.
This typically involves adding a type annotation to the destructuring pattern.

Return ONLY the fixed code snippet with the type annotation added.
Do not include explanations, just the code.""",

    "argument_count": """Fix the TypeScript error about incorrect number of arguments.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix for the argument count mismatch. Options include:
1. Adding missing required arguments
2. Removing extra arguments
3. Making parameters optional in the function signature

Return ONLY the fixed code snippet that resolves the argument count error.
Do not include explanations, just the code.""",

    "generic": """Fix the following TypeScript error.

Error: {error_message}
Error Code: {error_code}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Analyze the error and generate an appropriate fix.
Consider TypeScript best practices and type safety.

Return ONLY the fixed code snippet.
Do not include explanations, just the code.""",
}

STRATEGY_TO_TEMPLATE: Dict[str, str] = {
    "null_check": "null_check",
    "undefined_check": "undefined_check",
    "implicit_any": "implicit_any",
    "type_mismatch": "type_mismatch",
    "property_missing": "property_missing",
    "argument_type": "argument_type",
    "unknown_type": "unknown_type",
    "unknown_type_use": "unknown_type",
    "binding_any": "binding_any",
    "argument_count": "argument_count",
    "possibly_null": "null_check",
    "possibly_undefined": "undefined_check",
}

MIN_LLM_FIX_LENGTH = 5


class RefactorRisk(Enum):
    """Refactor risk levels"""
    HIGH = "high"          # Complex refactor, may break functionality
    MEDIUM = "medium"      # Moderate complexity
    LOW = "low"            # Simple fix, low risk
    INFO = "info"          # Informational only


@dataclass
class TSError:
    """Represents a TypeScript error"""
    file_path: str
    line: int
    column: int
    error_code: str
    message: str
    severity: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class RefactorTask:
    """Represents a refactor task for a single TS error"""
    task_id: str
    error: TSError
    fix_strategy: str
    estimated_risk: RefactorRisk
    status: str = "pending"  # pending, in_progress, completed, failed
    fix_applied: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "error": self.error.to_dict(),
            "fix_strategy": self.fix_strategy,
            "estimated_risk": self.estimated_risk.value,
            "status": self.status,
            "fix_applied": self.fix_applied,
            "error_message": self.error_message,
        }


@dataclass
class RefactorResult:
    """Result of a refactor run"""
    run_id: str
    started_at: float
    completed_at: Optional[float] = None
    total_errors_found: int = 0
    errors_fixed: int = 0
    errors_failed: int = 0
    tasks: List[RefactorTask] = field(default_factory=list)
    pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_errors_found": self.total_errors_found,
            "errors_fixed": self.errors_fixed,
            "errors_failed": self.errors_failed,
            "tasks": [t.to_dict() for t in self.tasks],
            "pr_url": self.pr_url,
            "branch_name": self.branch_name,
            "summary": self.summary,
            "metadata": self.metadata,
        }


# Common TS error fix strategies
TS_FIX_STRATEGIES = {
    "TS2322": "type_mismatch",      # Type 'X' is not assignable to type 'Y'
    "TS2339": "property_missing",    # Property 'X' does not exist on type 'Y'
    "TS2345": "argument_type",       # Argument of type 'X' is not assignable
    "TS2531": "null_check",          # Object is possibly 'null'
    "TS2532": "undefined_check",     # Object is possibly 'undefined'
    "TS2554": "argument_count",      # Expected X arguments, but got Y
    "TS2571": "unknown_type",        # Object is of type 'unknown'
    "TS7006": "implicit_any",        # Parameter 'X' implicitly has an 'any' type
    "TS7031": "binding_any",         # Binding element 'X' implicitly has an 'any' type
    "TS18046": "unknown_type_use",   # 'X' is of type 'unknown'
    "TS18047": "possibly_null",      # 'X' is possibly 'null'
    "TS18048": "possibly_undefined",  # 'X' is possibly 'undefined'
}


class RefactorAgent:
    """
    Refactor Agent for automated TypeScript strict mode error fixing.

    Phase 4 Features (#1818):
    - Nightly execution: Runs automatically at configured time
    - Incremental fixes: Fixes configurable number of errors per run
    - PR automation: Creates PRs for human review
    - Progress tracking: Maintains metrics on fix progress
    """

    DEFAULT_ERRORS_PER_RUN = 10
    DEFAULT_FRONTEND_PATH = "handoff/20250928/40_App/frontend-dashboard"
    DEFAULT_OWNER_CONSOLE_PATH = "handoff/20250928/40_App/owner-console"

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize RefactorAgent with configuration"""
        self.repo_path = Path(repo_path) if repo_path else self._find_repo_path()
        self._load_settings()
        logger.info("[RefactorAgent] Initialized - Phase 4 (#1818)")

    def _find_repo_path(self) -> Path:
        """Find the repository root path"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return Path.cwd()

    def _load_settings(self):
        """Load settings from environment"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(settings, 'refactor_agent_enabled', True)
            self.errors_per_run = getattr(
                settings, 'refactor_agent_errors_per_run', self.DEFAULT_ERRORS_PER_RUN
            )
            self.auto_pr = getattr(settings, 'refactor_agent_auto_pr', True)
            self.target_projects = getattr(
                settings, 'refactor_agent_target_projects',
                [self.DEFAULT_FRONTEND_PATH, self.DEFAULT_OWNER_CONSOLE_PATH]
            )
            logger.info(
                "[RefactorAgent] Settings loaded: enabled=%s, errors_per_run=%s",
                self.enabled, self.errors_per_run
            )
        except (ImportError, AttributeError) as e:
            logger.warning(
                "[RefactorAgent] Failed to load settings: %s, using defaults", e
            )
            self.enabled = True
            self.errors_per_run = self.DEFAULT_ERRORS_PER_RUN
            self.auto_pr = True
            self.target_projects = [
                self.DEFAULT_FRONTEND_PATH,
                self.DEFAULT_OWNER_CONSOLE_PATH
            ]

    def collect_ts_errors(self, project_path: Optional[str] = None) -> List[TSError]:
        """
        Collect TypeScript strict mode errors from the project.

        Uses `pnpm run typecheck:strict` to ensure consistency with CI workflow.
        This requires the project to have a `typecheck:strict` script defined
        in package.json that runs `tsc -p tsconfig.strict.json --noEmit`.

        Args:
            project_path: Path to the TypeScript project (relative to repo root)

        Returns:
            List of TSError objects
        """
        errors: List[TSError] = []
        projects = [project_path] if project_path else self.target_projects

        for proj in projects:
            proj_full_path = self.repo_path / proj
            if not proj_full_path.exists():
                logger.warning(
                    "[RefactorAgent] Project path not found: %s", proj_full_path
                )
                continue

            try:
                # Use pnpm run typecheck:strict for consistency with CI
                # This ensures we use the same tsconfig.strict.json as the CI workflow
                result = subprocess.run(
                    ["pnpm", "run", "typecheck:strict"],
                    cwd=proj_full_path,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env={**subprocess.os.environ, "FORCE_COLOR": "0"}
                )

                # Parse errors from both stdout and stderr
                for line in result.stdout.split("\n"):
                    error = self._parse_tsc_error(line, proj)
                    if error:
                        errors.append(error)

                for line in result.stderr.split("\n"):
                    error = self._parse_tsc_error(line, proj)
                    if error:
                        errors.append(error)

            except subprocess.TimeoutExpired:
                logger.error("[RefactorAgent] typecheck:strict timeout for %s", proj)
            except FileNotFoundError:
                logger.error("[RefactorAgent] pnpm not found for %s", proj)
            except Exception as e:
                logger.error("[RefactorAgent] Error collecting TS errors: %s", e)

        logger.info("[RefactorAgent] Collected %d TS strict errors", len(errors))
        return errors

    def _parse_tsc_error(self, line: str, project: str) -> Optional[TSError]:
        """Parse a single tsc error line"""
        # Pattern: file(line,col): error TSxxxx: message
        pattern = r"^(.+?)\((\d+),(\d+)\):\s*(error|warning)\s+(TS\d+):\s*(.+)$"
        match = re.match(pattern, line.strip())

        if match:
            file_path, line_num, col, severity, error_code, message = match.groups()
            return TSError(
                file_path=f"{project}/{file_path}",
                line=int(line_num),
                column=int(col),
                error_code=error_code,
                message=message,
                severity=severity
            )
        return None

    def analyze_error(self, error: TSError) -> RefactorTask:
        """
        Analyze a TS error and create a refactor task.

        Args:
            error: TSError to analyze

        Returns:
            RefactorTask with fix strategy
        """
        task_id = str(uuid.uuid4())[:8]

        # Determine fix strategy based on error code
        fix_strategy = TS_FIX_STRATEGIES.get(error.error_code, "manual_review")

        # Estimate risk based on error type
        risk = RefactorRisk.LOW
        if error.error_code in ["TS2322", "TS2345"]:
            risk = RefactorRisk.MEDIUM
        elif fix_strategy == "manual_review":
            risk = RefactorRisk.HIGH

        return RefactorTask(
            task_id=task_id,
            error=error,
            fix_strategy=fix_strategy,
            estimated_risk=risk
        )

    def _get_llm_client(self):
        """Get or create LLM client for fix generation"""
        if not hasattr(self, '_llm_client'):
            try:
                from llm import LLMClient
                self._llm_client = LLMClient(provider="auto")
                logger.info("[RefactorAgent] LLM client initialized")
            except (ImportError, ValueError) as e:
                logger.warning("[RefactorAgent] LLM client not available: %s", e)
                self._llm_client = None
        return self._llm_client

    def _get_code_context(
        self,
        file_path: str,
        line: int,
        context_lines: int = 5
    ) -> str:
        """
        Get code context around the error line.

        Args:
            file_path: Path to the file (relative to repo root)
            line: Line number of the error
            context_lines: Number of lines before and after to include

        Returns:
            Code context as a string
        """
        full_path = self.repo_path / file_path
        if not full_path.exists():
            return f"// File not found: {file_path}"

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start = max(0, line - context_lines - 1)
            end = min(len(lines), line + context_lines)

            context_lines_list = []
            for i in range(start, end):
                line_num = i + 1
                marker = ">>> " if line_num == line else "    "
                context_lines_list.append(f"{marker}{line_num}: {lines[i].rstrip()}")

            return "\n".join(context_lines_list)
        except Exception as e:
            logger.warning("[RefactorAgent] Failed to read file %s: %s", file_path, e)
            return f"// Error reading file: {e}"

    def _build_fix_prompt(self, task: RefactorTask) -> str:
        """
        Build the prompt for LLM fix generation.

        Args:
            task: RefactorTask containing error details

        Returns:
            Formatted prompt string
        """
        error = task.error
        strategy = task.fix_strategy

        template_key = STRATEGY_TO_TEMPLATE.get(strategy, "generic")
        template = TS_FIX_PROMPT_TEMPLATES.get(template_key, TS_FIX_PROMPT_TEMPLATES["generic"])

        code_context = self._get_code_context(error.file_path, error.line)

        return template.format(
            error_message=error.message,
            error_code=error.error_code,
            file_path=error.file_path,
            line=error.line,
            column=error.column,
            code_context=code_context
        )

    def _generate_fix_with_llm(
        self,
        task: RefactorTask,
        max_retries: int = 2
    ) -> Optional[str]:
        """
        Generate a fix using LLM with retry mechanism.

        Args:
            task: RefactorTask to fix
            max_retries: Maximum number of retry attempts

        Returns:
            Generated fix code or None if unable to fix
        """
        llm_client = self._get_llm_client()
        if llm_client is None:
            return None

        prompt = self._build_fix_prompt(task)
        system_prompt = (
            "You are an expert TypeScript developer specializing in fixing strict mode errors. "
            "Generate minimal, targeted fixes that resolve the specific error while maintaining "
            "code quality and type safety. Return ONLY the fixed code, no explanations."
        )

        for attempt in range(max_retries + 1):
            try:
                response = llm_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=500
                )

                fix = response.content.strip()

                # Remove markdown code blocks if present
                if fix.startswith("```"):
                    lines = fix.split("\n")
                    if len(lines) > 2:
                        fix = "\n".join(lines[1:-1])

                # Sanitize LLM output to remove prompt format pollution
                # This removes line numbers and markers that may have been copied from the prompt
                fix = self._sanitize_llm_output(fix)

                if fix and len(fix) > MIN_LLM_FIX_LENGTH:
                    logger.info(
                        "[RefactorAgent] Generated fix for %s:%d (attempt %d)",
                        task.error.file_path, task.error.line, attempt + 1
                    )
                    return fix

            except Exception as e:
                logger.warning(
                    "[RefactorAgent] LLM fix generation failed (attempt %d/%d): %s",
                    attempt + 1, max_retries + 1, e
                )
                if attempt < max_retries:
                    time.sleep(2 ** attempt)

        return None

    def generate_fix(self, task: RefactorTask) -> Optional[str]:
        """
        Generate a fix for the given task using LLM.

        This method uses the LLM to generate actual code fixes for TypeScript errors.
        Falls back to placeholder comments if LLM is not available.

        Args:
            task: RefactorTask to fix

        Returns:
            Generated fix code or None if unable to fix
        """
        llm_fix = self._generate_fix_with_llm(task)
        if llm_fix:
            return llm_fix

        error = task.error
        strategy = task.fix_strategy

        fallback_messages = {
            "null_check": f"// Add null check at line {error.line}",
            "undefined_check": f"// Add undefined check at line {error.line}",
            "implicit_any": f"// Add explicit type annotation at line {error.line}",
            "possibly_null": f"// Add optional chaining or null check at line {error.line}",
            "possibly_undefined": f"// Add optional chaining or undefined check at line {error.line}",
            "type_mismatch": f"// Fix type mismatch at line {error.line}",
            "property_missing": f"// Fix missing property at line {error.line}",
            "argument_type": f"// Fix argument type at line {error.line}",
            "unknown_type": f"// Handle unknown type at line {error.line}",
            "binding_any": f"// Add type annotation to binding at line {error.line}",
            "argument_count": f"// Fix argument count at line {error.line}",
        }

        return fallback_messages.get(strategy)

    def _sanitize_llm_output(self, fix: str) -> str:
        """
        Sanitize LLM output to remove prompt format pollution.

        The code context in prompts includes line numbers and markers (e.g., ">>> 34: code").
        LLMs sometimes copy these formats into their output, which corrupts the code.

        Safety: Only strips lines that contain the ">>>" marker we inject in _get_code_context().
        This prevents false positives on legitimate code like `1: "first"` in object literals.

        Args:
            fix: Raw LLM output

        Returns:
            Sanitized code without line numbers or markers
        """
        if not fix:
            return fix

        # Only sanitize if the output contains our injected ">>>" marker
        # This prevents false positives on legitimate code like `1: "first"`
        if ">>>" not in fix:
            return fix

        # Pattern matches lines with our marker format: ">>> 34: code" or "    34: code"
        # We only strip when >>> marker is present in the output (indicating prompt pollution)
        sanitized = re.sub(r'^\s*>>>\s*\d+:\s*', '', fix, flags=re.MULTILINE)
        sanitized = re.sub(r'^\s{4}\d+:\s*', '', sanitized, flags=re.MULTILINE)

        lines_removed = fix.count('\n') - sanitized.count('\n')
        chars_removed = len(fix) - len(sanitized)

        if chars_removed > 0:
            logger.info(
                "[RefactorAgent] Sanitized LLM output: removed %d characters from %d lines",
                chars_removed, lines_removed if lines_removed > 0 else 1
            )

        return sanitized

    def _verify_syntax_after_fix(self, project_path: str) -> Tuple[bool, List[str]]:
        """
        Verify that the project has no syntax errors after applying fixes.

        Syntax errors (TS1xxx codes) indicate that the code cannot be parsed,
        which means the fix corrupted the file. This is different from type errors
        (TS2xxx codes) which are expected during the fixing process.

        Args:
            project_path: Path to the TypeScript project (relative to repo root)

        Returns:
            Tuple of (has_syntax_errors, list of syntax error messages)
        """
        proj_full_path = self.repo_path / project_path
        if not proj_full_path.exists():
            return (False, [])

        try:
            result = subprocess.run(
                ["pnpm", "run", "typecheck:strict"],
                cwd=proj_full_path,
                capture_output=True,
                text=True,
                timeout=120,
                env={**subprocess.os.environ, "FORCE_COLOR": "0"}
            )

            syntax_errors = []
            # TS1xxx errors are syntax/parse errors
            syntax_error_pattern = r"error TS1\d{3}:"

            for line in result.stdout.split("\n") + result.stderr.split("\n"):
                if re.search(syntax_error_pattern, line):
                    syntax_errors.append(line.strip())

            has_syntax_errors = len(syntax_errors) > 0
            if has_syntax_errors:
                logger.warning(
                    "[RefactorAgent] Found %d syntax errors after fix in %s",
                    len(syntax_errors), project_path
                )

            return (has_syntax_errors, syntax_errors)

        except Exception as e:
            logger.error("[RefactorAgent] Error verifying syntax: %s", e)
            return (True, [f"Error during syntax verification: {e}"])

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a backup of a file before modification.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file, or None if backup failed
        """
        if not file_path.exists():
            logger.warning("[RefactorAgent] Cannot backup non-existent file: %s", file_path)
            return None

        backup_dir = self.repo_path / ".refactor_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time() * 1000)
        relative_path = file_path.relative_to(self.repo_path)
        safe_name = str(relative_path).replace("/", "_").replace("\\", "_")
        backup_path = backup_dir / f"{safe_name}.{timestamp}.bak"

        try:
            shutil.copy2(file_path, backup_path)
            logger.info("[RefactorAgent] Created backup: %s", backup_path)
            return backup_path
        except Exception as e:
            logger.error("[RefactorAgent] Failed to create backup for %s: %s", file_path, e)
            return None

    def _restore_from_backup(self, original_path: Path, backup_path: Path) -> bool:
        """
        Restore a file from its backup.

        Args:
            original_path: Path to restore to
            backup_path: Path to the backup file

        Returns:
            True if restore succeeded, False otherwise
        """
        if not backup_path.exists():
            logger.error("[RefactorAgent] Backup file not found: %s", backup_path)
            return False

        try:
            shutil.copy2(backup_path, original_path)
            logger.info("[RefactorAgent] Restored file from backup: %s", original_path)
            return True
        except Exception as e:
            logger.error("[RefactorAgent] Failed to restore from backup: %s", e)
            return False

    def get_diff_preview(self, task: RefactorTask, fix: str) -> Optional[str]:
        """
        Generate a diff preview showing the proposed change.

        Args:
            task: RefactorTask containing error details
            fix: The fix code to apply

        Returns:
            Diff string showing before/after, or None if unable to generate
        """
        file_path = self.repo_path / task.error.file_path
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()

            line_idx = task.error.line - 1
            if line_idx < 0 or line_idx >= len(original_lines):
                return None

            context_start = max(0, line_idx - 3)
            context_end = min(len(original_lines), line_idx + 4)

            fix_lines = fix.split("\n")
            fix_line_count = len(fix_lines)

            old_line_count = context_end - context_start
            new_line_count = old_line_count - 1 + fix_line_count

            diff_lines = []
            diff_lines.append(f"--- {task.error.file_path}")
            diff_lines.append(f"+++ {task.error.file_path}")
            diff_lines.append(f"@@ -{context_start + 1},{old_line_count} +{context_start + 1},{new_line_count} @@")

            for i in range(context_start, context_end):
                if i == line_idx:
                    diff_lines.append(f"-{original_lines[i].rstrip()}")
                    for fix_line in fix_lines:
                        diff_lines.append(f"+{fix_line}")
                else:
                    diff_lines.append(f" {original_lines[i].rstrip()}")

            return "\n".join(diff_lines)
        except Exception as e:
            logger.warning("[RefactorAgent] Failed to generate diff preview: %s", e)
            return None

    def apply_fix(
        self,
        task: RefactorTask,
        fix: str,
        create_backup: bool = True
    ) -> Tuple[bool, Optional[Path]]:
        """
        Apply a fix to the target file.

        Args:
            task: RefactorTask containing error details
            fix: The fix code to apply
            create_backup: Whether to create a backup before modifying

        Returns:
            Tuple of (success, backup_path)
        """
        file_path = self.repo_path / task.error.file_path
        if not file_path.exists():
            logger.error("[RefactorAgent] File not found: %s", file_path)
            return (False, None)

        backup_path = None
        if create_backup:
            backup_path = self._create_backup(file_path)
            if backup_path is None:
                logger.error("[RefactorAgent] Failed to create backup, aborting fix")
                return (False, None)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line_idx = task.error.line - 1
            if line_idx < 0 or line_idx >= len(lines):
                logger.error(
                    "[RefactorAgent] Line %d out of range for file %s (total lines: %d)",
                    task.error.line, file_path, len(lines)
                )
                return (False, backup_path)

            original_line = lines[line_idx]
            indent = len(original_line) - len(original_line.lstrip())
            indent_str = original_line[:indent]

            fix_lines = fix.split("\n")
            indented_fix = "\n".join(
                indent_str + line if line.strip() else line
                for line in fix_lines
            )

            if not indented_fix.endswith("\n"):
                indented_fix += "\n"

            lines[line_idx] = indented_fix

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            logger.info(
                "[RefactorAgent] Applied fix to %s:%d",
                task.error.file_path, task.error.line
            )
            return (True, backup_path)

        except Exception as e:
            logger.error("[RefactorAgent] Failed to apply fix: %s", e)
            if backup_path:
                self._restore_from_backup(file_path, backup_path)
            return (False, backup_path)

    def apply_fixes_batch(
        self,
        tasks: List[RefactorTask],
        fixes: List[str],
        create_backups: bool = True
    ) -> Dict[str, Any]:
        """
        Apply multiple fixes in a batch with rollback support.

        Handles same-file line offset: when multiple fixes target the same file,
        line numbers are adjusted based on previously applied multi-line fixes.

        Args:
            tasks: List of RefactorTasks to fix
            fixes: List of fix codes corresponding to tasks
            create_backups: Whether to create backups before modifying

        Returns:
            Dictionary with results: {
                'success_count': int,
                'failure_count': int,
                'applied': List[str],  # file paths successfully modified
                'failed': List[str],   # file paths that failed
                'backups': Dict[str, Path],  # file_path -> backup_path mapping
                'task_results': Dict[str, bool]  # task_id -> success mapping
            }
        """
        if len(tasks) != len(fixes):
            raise ValueError("tasks and fixes must have the same length")

        results = {
            'success_count': 0,
            'failure_count': 0,
            'applied': [],
            'failed': [],
            'backups': {},
            'task_results': {}
        }

        applied_backups: Dict[str, Path] = {}
        line_offsets: Dict[str, int] = {}

        task_fix_pairs = list(zip(tasks, fixes))
        task_fix_pairs.sort(key=lambda x: (x[0].error.file_path, x[0].error.line))

        for task, fix in task_fix_pairs:
            if fix is None or fix == "":
                results['failure_count'] += 1
                results['failed'].append(task.error.file_path)
                results['task_results'][task.task_id] = False
                continue

            file_path = task.error.file_path
            offset = line_offsets.get(file_path, 0)

            adjusted_line = task.error.line + offset

            adjusted_task = RefactorTask(
                task_id=task.task_id,
                error=TSError(
                    file_path=task.error.file_path,
                    line=adjusted_line,
                    column=task.error.column,
                    error_code=task.error.error_code,
                    message=task.error.message
                ),
                fix_strategy=task.fix_strategy,
                estimated_risk=task.estimated_risk,
                status=task.status,
                fix_applied=task.fix_applied,
                error_message=task.error_message
            )

            should_backup = create_backups and file_path not in applied_backups
            success, backup_path = self.apply_fix(
                adjusted_task, fix, create_backup=should_backup
            )

            if success:
                results['success_count'] += 1
                results['applied'].append(file_path)
                results['task_results'][task.task_id] = True
                if backup_path:
                    applied_backups[file_path] = backup_path

                fix_lines = fix.split("\n")
                line_change = len(fix_lines) - 1
                if line_change != 0:
                    line_offsets[file_path] = offset + line_change
            else:
                results['failure_count'] += 1
                results['failed'].append(file_path)
                results['task_results'][task.task_id] = False

        results['backups'] = applied_backups

        logger.info(
            "[RefactorAgent] Batch apply complete: %d success, %d failed",
            results['success_count'], results['failure_count']
        )

        return results

    def rollback_batch(self, backups: Dict[str, Path]) -> Dict[str, bool]:
        """
        Rollback multiple files from their backups.

        Args:
            backups: Dictionary mapping file paths to backup paths

        Returns:
            Dictionary mapping file paths to rollback success status
        """
        results = {}

        for file_path_str, backup_path in backups.items():
            file_path = self.repo_path / file_path_str
            success = self._restore_from_backup(file_path, backup_path)
            results[file_path_str] = success

        success_count = sum(1 for v in results.values() if v)
        logger.info(
            "[RefactorAgent] Rollback complete: %d/%d files restored",
            success_count, len(results)
        )

        return results

    def cleanup_backups(self, max_age_hours: int = 24) -> int:
        """
        Clean up old backup files.

        Args:
            max_age_hours: Maximum age of backups to keep (default: 24 hours)

        Returns:
            Number of backup files deleted
        """
        backup_dir = self.repo_path / ".refactor_backups"
        if not backup_dir.exists():
            return 0

        deleted_count = 0
        cutoff_time = time.time() - (max_age_hours * 3600)

        for backup_file in backup_dir.glob("*.bak"):
            try:
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.warning("[RefactorAgent] Failed to delete backup %s: %s", backup_file, e)

        if deleted_count > 0:
            logger.info("[RefactorAgent] Cleaned up %d old backup files", deleted_count)

        return deleted_count

    def run_refactor(
        self,
        max_errors: Optional[int] = None,
        dry_run: bool = False
    ) -> RefactorResult:
        """
        Run a refactor session.

        Args:
            max_errors: Maximum number of errors to fix (default: errors_per_run)
            dry_run: If True, don't apply fixes, just analyze

        Returns:
            RefactorResult with summary of the run
        """
        if not self.enabled:
            return RefactorResult(
                run_id=str(uuid.uuid4()),
                started_at=time.time(),
                completed_at=time.time(),
                summary="Refactor Agent disabled"
            )

        run_id = str(uuid.uuid4())
        started_at = time.time()
        max_errors = max_errors or self.errors_per_run

        logger.info(
            "[RefactorAgent] Starting refactor run %s (max_errors=%d, dry_run=%s)",
            run_id, max_errors, dry_run
        )

        # Collect errors
        all_errors = self.collect_ts_errors()
        total_errors = len(all_errors)

        # Limit to max_errors
        errors_to_fix = all_errors[:max_errors]

        # Analyze and create tasks
        tasks: List[RefactorTask] = []
        for error in errors_to_fix:
            task = self.analyze_error(error)
            tasks.append(task)

        # Generate fixes (if not dry run)
        errors_fixed = 0
        errors_failed = 0

        if not dry_run:
            for task in tasks:
                task.status = "in_progress"
                fix = self.generate_fix(task)

                if fix:
                    task.fix_applied = fix
                    task.status = "completed"
                    errors_fixed += 1
                else:
                    task.status = "failed"
                    task.error_message = "Unable to generate automatic fix"
                    errors_failed += 1

            # Apply fixes to files if we have any completed tasks
            completed_tasks = [t for t in tasks if t.status == "completed"]
            if completed_tasks:
                # Filter out tasks with None/empty fix_applied
                tasks_to_apply = []
                fixes_to_apply = []
                for task in completed_tasks:
                    if task.fix_applied and task.fix_applied.strip():
                        tasks_to_apply.append(task)
                        fixes_to_apply.append(task.fix_applied)
                    else:
                        # Mark task as failed if fix_applied is None/empty
                        task.status = "failed"
                        task.error_message = "No fix generated (fix_applied is empty)"
                        errors_failed += 1
                        errors_fixed -= 1  # Decrement since we counted it as fixed earlier

                if tasks_to_apply:
                    logger.info(
                        "[RefactorAgent] Applying %d fixes to files",
                        len(tasks_to_apply)
                    )
                    apply_results = self.apply_fixes_batch(tasks_to_apply, fixes_to_apply)

                    # Update task statuses based on per-task results
                    for task in tasks_to_apply:
                        task_success = apply_results['task_results'].get(task.task_id, False)
                        if not task_success:
                            task.status = "failed"
                            task.error_message = "Failed to apply fix to file"

                    # Update counts from apply results
                    errors_fixed = apply_results['success_count']
                    errors_failed += apply_results['failure_count']

                    # Post-fix validation: Check for syntax errors (TS1xxx)
                    # If fixes introduced syntax errors, rollback all changes
                    if errors_fixed > 0:
                        syntax_errors_found = False
                        for proj in self.target_projects:
                            has_syntax_errors, syntax_error_list = self._verify_syntax_after_fix(proj)
                            if has_syntax_errors:
                                syntax_errors_found = True
                                logger.error(
                                    "[RefactorAgent] Syntax errors detected in %s after applying fixes. "
                                    "Rolling back all changes. Errors: %s",
                                    proj, syntax_error_list[:5]  # Log first 5 errors
                                )

                        if syntax_errors_found:
                            # Rollback all applied fixes
                            backup_paths = apply_results.get('backups', {})
                            if backup_paths:
                                self.rollback_batch(backup_paths)
                                logger.warning(
                                    "[RefactorAgent] Rolled back %d files due to syntax errors",
                                    len(backup_paths)
                                )

                            # Mark all tasks as failed
                            for task in tasks_to_apply:
                                task.status = "failed"
                                task.error_message = "Fix caused syntax errors, rolled back"

                            errors_failed += errors_fixed
                            errors_fixed = 0

        completed_at = time.time()
        latency_ms = (completed_at - started_at) * 1000

        result = RefactorResult(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            total_errors_found=total_errors,
            errors_fixed=errors_fixed,
            errors_failed=errors_failed,
            tasks=tasks,
            summary=self._generate_summary(total_errors, errors_fixed, errors_failed),
            metadata={
                "max_errors": max_errors,
                "dry_run": dry_run,
                "latency_ms": latency_ms,
                "target_projects": self.target_projects,
            }
        )

        # Create PR if we have fixes and auto_pr is enabled
        if not dry_run and errors_fixed > 0 and self.auto_pr:
            logger.info("[RefactorAgent] Creating PR for %d fixes", errors_fixed)
            pr_url, pr_number = self.create_pr(result, tasks)
            if pr_url:
                result.pr_url = pr_url
                result.metadata["pr_number"] = pr_number
                logger.info("[RefactorAgent] Created PR: %s", pr_url)
            else:
                logger.warning("[RefactorAgent] Failed to create PR")

        logger.info(
            "[RefactorAgent] Refactor run complete: %s",
            result.summary,
            extra={
                "run_id": run_id,
                "total_errors": total_errors,
                "errors_fixed": errors_fixed,
                "errors_failed": errors_failed,
                "latency_ms": latency_ms,
                "pr_url": result.pr_url,
            }
        )

        return result

    def _generate_summary(
        self,
        total_errors: int,
        errors_fixed: int,
        errors_failed: int
    ) -> str:
        """Generate a human-readable summary"""
        remaining = total_errors - errors_fixed
        return (
            f"Found {total_errors} TS errors. "
            f"Fixed {errors_fixed}, failed {errors_failed}. "
            f"Remaining: {remaining}"
        )

    def get_progress_report(self) -> Dict[str, Any]:
        """
        Get a progress report on TS strict mode migration.

        Returns:
            Dictionary with progress metrics
        """
        errors = self.collect_ts_errors()
        total = len(errors)

        # Group by error code
        by_code: Dict[str, int] = {}
        for error in errors:
            by_code[error.error_code] = by_code.get(error.error_code, 0) + 1

        # Group by project (file_path format: "project/path/to/file.ts")
        by_project: Dict[str, int] = {}
        for error in errors:
            parts = error.file_path.split("/")
            project = parts[0] if len(parts) > 1 else "unknown"
            by_project[project] = by_project.get(project, 0) + 1

        # Estimate completion
        target = 0  # Target is 0 errors
        progress_pct = 100.0 if total == 0 else 0.0

        return {
            "total_errors": total,
            "target_errors": target,
            "progress_percent": progress_pct,
            "errors_by_code": by_code,
            "errors_by_project": by_project,
            "top_error_codes": sorted(
                by_code.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def _generate_branch_name(self, timestamp: Optional[datetime] = None) -> str:
        """
        Generate a branch name for the refactor PR.

        Args:
            timestamp: Optional timestamp to use (default: now)

        Returns:
            Branch name in format: refactor/ts-fixes-YYYYMMDD-HHMMSS
        """
        ts = timestamp or datetime.now()
        ts_str = ts.strftime("%Y%m%d-%H%M%S")
        return f"refactor/ts-fixes-{ts_str}"

    def _generate_pr_title(self, errors_fixed: int, timestamp: Optional[datetime] = None) -> str:
        """
        Generate a PR title for the refactor.

        Args:
            errors_fixed: Number of errors fixed
            timestamp: Optional timestamp to use (default: now)

        Returns:
            PR title string
        """
        ts = timestamp or datetime.now()
        date_str = ts.strftime("%Y-%m-%d")
        error_word = "error" if errors_fixed == 1 else "errors"
        return f"fix(ts): Automated TS strict mode fixes ({errors_fixed} {error_word}) - {date_str}"

    def _generate_changelog(self, tasks: List[RefactorTask]) -> str:
        """
        Generate a changelog from completed tasks.

        Args:
            tasks: List of RefactorTasks

        Returns:
            Changelog string in markdown format
        """
        completed_tasks = [t for t in tasks if t.status == "completed"]
        if not completed_tasks:
            return "No fixes applied."

        by_file: Dict[str, List[RefactorTask]] = {}
        for task in completed_tasks:
            file_path = task.error.file_path
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(task)

        lines = ["## Changelog\n"]
        for file_path, file_tasks in sorted(by_file.items()):
            lines.append(f"### `{file_path}`\n")
            for task in sorted(file_tasks, key=lambda t: t.error.line):
                error = task.error
                lines.append(
                    f"- Line {error.line}: Fixed `{error.error_code}` - {error.message}"
                )
            lines.append("")

        return "\n".join(lines)

    def _generate_pr_description(
        self,
        result: RefactorResult,
        tasks: List[RefactorTask]
    ) -> str:
        """
        Generate a PR description with changelog.

        Args:
            result: RefactorResult with summary
            tasks: List of RefactorTasks

        Returns:
            PR description in markdown format
        """
        changelog = self._generate_changelog(tasks)

        by_code: Dict[str, int] = {}
        for task in tasks:
            if task.status == "completed":
                code = task.error.error_code
                by_code[code] = by_code.get(code, 0) + 1

        error_summary = ", ".join(
            f"`{code}`: {count}" for code, count in sorted(by_code.items())
        )

        description = f"""## Description

Automated TypeScript strict mode error fixes generated by Refactor Agent.

**Summary:** {result.summary}

**Error Types Fixed:** {error_summary if error_summary else "None"}

{changelog}

## How to Review

1. Check each fix for correctness
2. Ensure no regressions in functionality
3. Run `npm run typecheck` to verify remaining errors

## Generated By

- **Agent:** Refactor Agent (Phase 4 #1818, #1890)
- **Run ID:** `{result.run_id}`
- **Timestamp:** {datetime.now().isoformat()}

---
*This PR was automatically generated. Please review carefully before merging.*
"""
        return description

    def _create_refactor_branch(self, branch_name: str) -> bool:
        """
        Create a new branch for the refactor.

        Args:
            branch_name: Name of the branch to create

        Returns:
            True if branch created successfully, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(
                    "[RefactorAgent] Failed to create branch %s: %s",
                    branch_name, result.stderr
                )
                return False

            logger.info("[RefactorAgent] Created branch: %s", branch_name)
            return True
        except Exception as e:
            logger.error("[RefactorAgent] Failed to create branch: %s", e)
            return False

    def _commit_fixes(
        self,
        tasks: List[RefactorTask],
        message: str
    ) -> bool:
        """
        Commit the applied fixes.

        Args:
            tasks: List of RefactorTasks with applied fixes
            message: Commit message

        Returns:
            True if commit successful, False otherwise
        """
        try:
            completed_tasks = [t for t in tasks if t.status == "completed"]
            if not completed_tasks:
                logger.warning("[RefactorAgent] No completed tasks to commit")
                return False

            files_to_add = list(set(t.error.file_path for t in completed_tasks))

            for file_path in files_to_add:
                result = subprocess.run(
                    ["git", "add", file_path],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    logger.error(
                        "[RefactorAgent] Failed to add file %s: %s",
                        file_path, result.stderr
                    )
                    return False

            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(
                    "[RefactorAgent] Failed to commit: %s", result.stderr
                )
                return False

            logger.info(
                "[RefactorAgent] Committed %d files", len(files_to_add)
            )
            return True
        except Exception as e:
            logger.error("[RefactorAgent] Failed to commit fixes: %s", e)
            return False

    def _push_branch(self, branch_name: str) -> bool:
        """
        Push the branch to remote.

        Args:
            branch_name: Name of the branch to push

        Returns:
            True if push successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(
                    "[RefactorAgent] Failed to push branch %s: %s",
                    branch_name, result.stderr
                )
                return False

            logger.info("[RefactorAgent] Pushed branch: %s", branch_name)
            return True
        except Exception as e:
            logger.error("[RefactorAgent] Failed to push branch: %s", e)
            return False

    def _get_github_repo(self):
        """
        Get GitHub repository object.

        Returns:
            GitHub repository object or None if unavailable
        """
        try:
            from tools.github_api import get_repo
            return get_repo()
        except ImportError:
            logger.warning(
                "[RefactorAgent] GitHub API not available, trying direct import"
            )
            try:
                from github import Github
                from common.config.settings import settings
                token = getattr(settings, 'agent_github_token', None)
                token = token or getattr(settings, 'github_token', None)
                if not token:
                    logger.error("[RefactorAgent] No GitHub token available")
                    return None
                gh = Github(token)
                repo_name = getattr(settings, 'github_repo', 'RC918/morningai')
                return gh.get_repo(repo_name)
            except Exception as e:
                logger.error("[RefactorAgent] Failed to get GitHub repo: %s", e)
                return None

    def _check_existing_refactor_pr(self, target_branch: Optional[str] = None):
        """
        Check if there's an existing open refactor PR created by this agent.

        Detection criteria (must match ALL):
        1. PR is open and targets the specified branch (default: repo's default branch)
        2. PR title starts with "fix(ts):" (matches _generate_pr_title() format)
        3. PR has the "automated" label (added by create_pr())

        This prevents the nightly workflow from creating duplicate PRs when
        an existing automated refactor PR is still open/pending review.

        Args:
            target_branch: Branch to check PRs against (default: repo's default branch)

        Returns:
            The existing PR object if found, None otherwise

        Note:
            To force creation of a new PR when one exists, either:
            - Merge or close the existing PR
            - Remove the "automated" label from the existing PR
        """
        repo = self._get_github_repo()
        if repo is None:
            return None

        try:
            base_branch = target_branch or getattr(repo, 'default_branch', 'main')
            logger.debug(
                "[RefactorAgent] Checking for existing refactor PRs targeting '%s'",
                base_branch
            )

            open_prs = repo.get_pulls(state='open', base=base_branch)
            for pr in open_prs:
                labels = {label.name.lower() for label in pr.labels}

                is_refactor_agent_pr = (
                    pr.title.startswith("fix(ts):") and
                    "automated" in labels
                )

                if is_refactor_agent_pr:
                    logger.debug(
                        "[RefactorAgent] Found existing refactor PR: #%d (%s)",
                        pr.number, pr.title
                    )
                    return pr

            return None
        except Exception as e:
            logger.warning(
                "[RefactorAgent] Failed to check existing PRs: %s", e
            )
            return None

    def _prepare_pr_branch(
        self,
        branch_name: str,
        tasks: List[RefactorTask],
        title: str
    ) -> bool:
        """
        Prepare the PR branch by creating it, committing fixes, and pushing.

        Args:
            branch_name: Name of the branch to create
            tasks: List of RefactorTasks with fixes
            title: Commit message / PR title

        Returns:
            True if successful, False otherwise
        """
        if not self._create_refactor_branch(branch_name):
            return False

        if not self._commit_fixes(tasks, title):
            self._checkout_main()
            return False

        if not self._push_branch(branch_name):
            self._checkout_main()
            return False

        return True

    def _submit_pr_to_github(
        self,
        repo,
        branch_name: str,
        title: str,
        body: str,
        draft: bool,
        labels: List[str],
        base_branch: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Submit the PR to GitHub and add labels.

        Args:
            repo: GitHub repository object
            branch_name: Name of the branch
            title: PR title
            body: PR description
            draft: Whether to create as draft
            labels: Labels to add
            base_branch: Target branch for PR (default: repo's default branch)

        Returns:
            Tuple of (pr_url, pr_number) or (None, None) if failed
        """
        try:
            target_branch = base_branch or getattr(repo, 'default_branch', 'main')
            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=target_branch,
                draft=draft
            )

            if labels:
                try:
                    pr.add_to_labels(*labels)
                except Exception as e:
                    logger.warning("[RefactorAgent] Failed to add labels: %s", e)

            logger.info("[RefactorAgent] Created PR #%d: %s", pr.number, pr.html_url)
            return (pr.html_url, pr.number)

        except Exception as e:
            logger.error("[RefactorAgent] Failed to create PR: %s", e)
            return (None, None)

    def create_pr(
        self,
        result: RefactorResult,
        tasks: List[RefactorTask],
        draft: bool = False,
        labels: Optional[List[str]] = None
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Create a Pull Request with the refactor fixes.

        Args:
            result: RefactorResult with summary
            tasks: List of RefactorTasks
            draft: Create as draft PR (default: False)
            labels: List of labels to add (default: ["refactor", "automated"])

        Returns:
            Tuple of (pr_url, pr_number) or (None, None) if failed
        """
        # Early validation checks
        if not self.auto_pr:
            logger.info("[RefactorAgent] auto_pr disabled, skipping PR creation")
            return (None, None)

        completed_tasks = [t for t in tasks if t.status == "completed"]
        if not completed_tasks:
            logger.warning("[RefactorAgent] No completed tasks, skipping PR")
            return (None, None)

        existing_pr = self._check_existing_refactor_pr()
        if existing_pr:
            logger.warning(
                "[RefactorAgent] Existing open refactor PR found: #%d (%s). "
                "Skipping PR creation to avoid duplicates.",
                existing_pr.number, existing_pr.html_url
            )
            return (None, None)

        # Generate PR metadata
        now = datetime.now()
        branch_name = self._generate_branch_name(timestamp=now)
        title = self._generate_pr_title(len(completed_tasks), timestamp=now)
        labels = labels or ["refactor", "automated"]

        # Prepare branch with commits
        if not self._prepare_pr_branch(branch_name, tasks, title):
            return (None, None)

        # Get GitHub repo and submit PR
        repo = self._get_github_repo()
        if repo is None:
            logger.error("[RefactorAgent] Cannot create PR: GitHub unavailable")
            self._checkout_main()
            return (None, None)

        body = self._generate_pr_description(result, tasks)
        pr_result = self._submit_pr_to_github(repo, branch_name, title, body, draft, labels)

        # Always return to main branch
        self._checkout_main()

        return pr_result

    def _checkout_main(self) -> bool:
        """
        Checkout main branch.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "checkout", "main"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False


# Singleton instance
_refactor_agent: Optional[RefactorAgent] = None


def get_refactor_agent() -> RefactorAgent:
    """Get or create the singleton RefactorAgent instance"""
    global _refactor_agent
    if _refactor_agent is None:
        _refactor_agent = RefactorAgent()
    return _refactor_agent


def run_nightly_refactor(
    max_errors: Optional[int] = None,
    dry_run: bool = False
) -> RefactorResult:
    """
    Convenience function for nightly refactor runs.

    Args:
        max_errors: Maximum number of errors to fix
        dry_run: If True, don't apply fixes

    Returns:
        RefactorResult with summary
    """
    agent = get_refactor_agent()
    return agent.run_refactor(max_errors=max_errors, dry_run=dry_run)
