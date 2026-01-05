#!/usr/bin/env python3
"""
Code Generation Workflow - Automated code generation using LangGraph
Phase 2 Day 3-4: Code Generation Workflow

Supports 5 task types:
1. Backend Utils Bug Fix
2. Frontend UI Tokens
3. Simple API Endpoint
4. Test Generation
5. Documentation Update
"""
import logging
import re
import time
import os
from typing import Dict, Any, List, Optional, TypedDict
from pathlib import Path

from langgraph.graph import StateGraph

import sys

# Issue #3585: Root Cause #16 - Path corruption fix
# The previous calculation using dirname() was incorrect:
# - Old: os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# - This gave /path/to/agents instead of /path/to (repo root)
#
# Now uses common.utils.repo_root.get_repo_root() which is the canonical
# implementation with proper fallback chain and error handling.
# Must bootstrap sys.path first to import from common.utils.
_bootstrap_root = Path(__file__).resolve()
for _parent in _bootstrap_root.parents:
    if (_parent / '.git').exists():
        _bootstrap_root = _parent
        break
if str(_bootstrap_root) not in sys.path:
    sys.path.insert(0, str(_bootstrap_root))

from common.utils.repo_root import get_repo_root

project_root = str(get_repo_root())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.dev_agent.workflows.task_classifier import TaskClassifier, TaskType, classify_task
from agents.dev_agent.testing.llm_test_generator import LLMTestGenerator

logger = logging.getLogger(__name__)


class CodeGenState(TypedDict):
    """State for Code Generation Workflow"""
    task_id: int
    task_title: str
    task_description: str
    task_type: Optional[str]
    task_metadata: Optional[Dict[str, Any]]
    target_files: List[str]
    changed_files: Optional[List[str]]  # Issue #3593: fallback target files from PR
    generated_code: Optional[str]
    generated_tests: Optional[str]
    code_diff: Optional[str]
    test_results: Optional[Dict[str, Any]]
    pr_number: Optional[int]
    pr_url: Optional[str]
    error: Optional[str]
    execution_start: float
    file_backups: Dict[str, str]
    security_validated: bool


class CodeGenerationWorkflow:
    """
    Automated Code Generation Workflow using LangGraph

    Workflow Stages:
    1. Classify Task - Determine task type (5 types supported)
    2. Analyze Context - Gather context from codebase
    3. Generate Code - Use LLM to generate code
    4. Validate Security - Check for dangerous patterns
    5. Apply Code - Apply generated code
    6. Generate Tests - Create unit tests (if required)
    7. Run Tests - Verify code works
    8. Create PR - Create Pull Request
    """

    DANGEROUS_PATTERNS = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\b__import__\s*\(',
        r'\bcompile\s*\(',
        r'\bos\.system\s*\(',
        r'\bsubprocess\.(call|run|Popen)\s*\(',
        r'\bshutil\.rmtree\s*\(',
        r'\bsocket\.',
        r'\brequests\.(get|post|put|delete)\s*\(',
        r'\burllib\.',
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'TRUNCATE\s+TABLE',
        r';--',
        r'\bpickle\.loads\s*\(',
        r'\byaml\.load\s*\(',
    ]

    # Issue #3593: Code file extensions for changed_files fallback filtering
    # Used when LLM extraction fails and we need to filter PR changed_files
    CODE_EXTENSIONS = ('.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.yml', '.yaml')

    # Issue #3595: Directories that are never allowed for auto-fix
    # These are filtered out from changed_files fallback regardless of task_metadata
    # because they require special handling or are high-risk
    DISALLOWED_DIRECTORIES = (
        '.github/',      # CI/CD workflows - high risk, can bypass security checks
        '.circleci/',    # CI/CD config
        '.gitlab/',      # CI/CD config
        '.buildkite/',   # CI/CD config (gemini-code-assist suggestion)
        'infra/',        # Infrastructure code
        'terraform/',    # Infrastructure as code
        'k8s/',          # Kubernetes configs
        'deploy/',       # Deployment scripts
    )

    def __init__(self, dev_agent):
        """
        Initialize Code Generation Workflow

        Args:
            dev_agent: DevAgent instance with all tools
        """
        self.agent = dev_agent
        self.classifier = TaskClassifier()
        self.test_generator = LLMTestGenerator(enable_llm=True)

        from common.config.settings import settings
        self.repo_root = os.path.realpath(
            settings.workspace_path if settings.workspace_path else project_root
        )
        logger.info(f"Code generation repo root: {self.repo_root}")

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(CodeGenState)

        workflow.add_node("classify_task", self.classify_task)
        workflow.add_node("analyze_context", self.analyze_context)
        workflow.add_node("generate_code", self.generate_code)
        workflow.add_node("validate_security", self.validate_security)
        workflow.add_node("apply_code", self.apply_code)
        workflow.add_node("generate_tests", self.generate_tests)
        workflow.add_node("run_tests", self.run_tests)
        workflow.add_node("create_pr", self.create_pr)

        workflow.set_entry_point("classify_task")

        workflow.add_conditional_edges(
            "classify_task",
            self._should_continue_after_classify,
            {
                "analyze": "analyze_context",
                "end": "create_pr"
            }
        )
        workflow.add_edge("analyze_context", "generate_code")
        workflow.add_edge("generate_code", "validate_security")
        workflow.add_conditional_edges(
            "validate_security",
            self._should_continue_after_security,
            {
                "apply": "apply_code",
                "end": "create_pr"
            }
        )
        workflow.add_conditional_edges(
            "apply_code",
            self._should_generate_tests,
            {
                "tests": "generate_tests",
                "run": "run_tests"
            }
        )
        workflow.add_edge("generate_tests", "run_tests")
        workflow.add_conditional_edges(
            "run_tests",
            self._should_continue_after_tests,
            {
                "pr": "create_pr",
                "retry": "generate_code",
                "end": "create_pr"
            }
        )

        workflow.set_finish_point("create_pr")

        # Issue #3579: Explicitly disable checkpointer to prevent NotImplementedError
        # When CodeGenerationWorkflow runs inside the orchestrator's LangGraph context,
        # checkpointer=None can inherit the parent graph's checkpointer via contextvars.
        # This causes NotImplementedError when LangGraph tries to use abstract methods
        # from BaseCheckpointSaver that aren't implemented. Setting checkpointer=False
        # explicitly disables checkpointing and prevents inheritance.
        return workflow.compile(checkpointer=False)

    def _should_continue_after_classify(self, state: CodeGenState) -> str:
        """Decide next step after task classification"""
        if state.get("error"):
            return "end"
        if state.get("task_type") == TaskType.UNKNOWN.value:
            logger.warning("Task type unknown, cannot generate code")
            return "end"
        return "analyze"

    def _should_continue_after_security(self, state: CodeGenState) -> str:
        """Decide next step after security validation"""
        if state.get("error"):
            return "end"
        if not state.get("security_validated", False):
            logger.error("Security validation failed, cannot apply code")
            return "end"
        return "apply"

    def _should_generate_tests(self, state: CodeGenState) -> str:
        """Decide if tests should be generated"""
        if state.get("error"):
            return "run"

        metadata = state.get("task_metadata", {})
        if metadata.get("requires_tests", False):
            return "tests"
        return "run"

    def _should_continue_after_tests(self, state: CodeGenState) -> str:
        """Decide next step after running tests"""
        if state.get("error"):
            return "end"

        test_results = state.get("test_results", {})
        if test_results.get("success", False):
            return "pr"

        if state.get("generated_code") and not state.get("retry_attempted", False):
            state["retry_attempted"] = True
            return "retry"

        return "end"

    async def classify_task(self, state: CodeGenState) -> CodeGenState:
        """Stage 1: Classify task type

        If task_type is already set (e.g., from task_type_hint passed via execute()),
        skip classification and use the pre-set value.
        """
        logger.info(f"[Stage 1] Classifying task #{state['task_id']}")

        if state.get("task_type"):
            logger.info(
                f"[Stage 1] Skipping classification - task_type already set: {state['task_type']}"
            )
            if not state.get("task_metadata"):
                try:
                    task_type_enum = TaskType(state["task_type"])
                    state["task_metadata"] = self.classifier.get_task_metadata(task_type_enum)
                except ValueError:
                    logger.warning(
                        f"Invalid task_type '{state['task_type']}' provided, using default metadata."
                    )
                    state["task_metadata"] = {"complexity": "medium", "requires_tests": False}
            return state

        try:
            classification = classify_task(
                state["task_description"],
                state["task_title"]
            )

            state["task_type"] = classification["task_type"]
            state["task_metadata"] = classification["metadata"]

            if not classification["supported"]:
                state["error"] = f"Task type '{classification['task_type']}' not supported"
                logger.error(state["error"])
            else:
                logger.info(
                    f"Task classified as: {classification['task_type']} "
                    f"(complexity: {classification['metadata']['complexity']})"
                )

        except Exception as e:
            state["error"] = f"Classification failed: {str(e)}"
            logger.error(state["error"])

        return state

    async def analyze_context(self, state: CodeGenState) -> CodeGenState:
        """Stage 2: Analyze codebase context

        Issue #3593: Added fallback to changed_files when extraction fails.
        This handles cases where the LLM planner fails (e.g., quota exceeded)
        and the static plan doesn't include file paths in the task description.

        Issue #3595: Filter changed_files to exclude disallowed directories
        (e.g., .github/) that would fail security validation anyway.
        """
        logger.info(f"[Stage 2] Analyzing context for task #{state['task_id']}")

        try:
            target_files = self._extract_file_paths(state["task_description"])

            # Issue #3593: Fallback to changed_files if extraction returns empty
            if not target_files:
                changed_files = state.get("changed_files") or []
                if changed_files:
                    # Issue #3595: Filter out files in disallowed directories
                    # These would fail security validation anyway, so filter early
                    filtered_files = [
                        f for f in changed_files
                        if not any(f.startswith(d) for d in self.DISALLOWED_DIRECTORIES)
                    ]

                    # Log what was filtered out
                    filtered_out = set(changed_files) - set(filtered_files)
                    if filtered_out:
                        logger.info(
                            f"[Stage 2] Filtered out {len(filtered_out)} files in "
                            f"disallowed directories: {list(filtered_out)}"
                        )

                    # Filter to only include files that look like code files
                    # Uses class constant CODE_EXTENSIONS for maintainability
                    target_files = [
                        f for f in filtered_files
                        if f.endswith(self.CODE_EXTENSIONS)
                    ]
                    if target_files:
                        logger.info(
                            f"[Stage 2] Using changed_files as fallback target files: {target_files}"
                        )
                    else:
                        logger.warning(
                            "[Stage 2] changed_files available but no allowed code files found"
                        )

            state["target_files"] = target_files

            if not target_files:
                logger.warning("No target files found in task description")
            else:
                logger.info(f"Target files: {target_files}")

            state["file_backups"] = {}
            for file_path in target_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            state["file_backups"][file_path] = f.read()
                        logger.info(f"Backed up: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not backup {file_path}: {e}")

        except Exception as e:
            state["error"] = f"Context analysis failed: {str(e)}"
            logger.error(state["error"])

        return state

    async def generate_code(self, state: CodeGenState) -> CodeGenState:
        """Stage 3: Generate code using LLM

        Issue #3581: Added instrumentation to track LLM call duration.
        This stage was identified as the bottleneck (10+ minutes observed in staging).
        """
        stage_start = time.time()
        task_id = state['task_id']
        logger.info(f"[Stage 3] Generating code for task #{task_id}")

        try:
            task_type = state["task_type"]
            task_desc = state["task_description"]
            target_files = state.get("target_files", [])

            # Build prompt and log timing
            prompt_start = time.time()
            prompt = self._build_code_generation_prompt(
                task_type, task_desc, target_files
            )
            prompt_elapsed_ms = (time.time() - prompt_start) * 1000
            logger.info(
                f"[Stage 3] Prompt built: length={len(prompt)}, elapsed_ms={prompt_elapsed_ms:.2f}"
            )

            if hasattr(self.agent, 'llm') and self.agent.llm:
                # Log before LLM call
                llm_start = time.time()
                logger.info(
                    f"[Stage 3] Starting LLM call for task #{task_id}"
                )

                response = await self.agent.llm.generate(prompt)

                # Log after LLM call
                llm_elapsed_ms = (time.time() - llm_start) * 1000
                logger.info(
                    f"[Stage 3] LLM call completed: elapsed_ms={llm_elapsed_ms:.2f}, "
                    f"response_length={len(response) if response else 0}"
                )

                # Extract code and log timing
                extract_start = time.time()
                generated_code = self._extract_code_from_response(response)
                extract_elapsed_ms = (time.time() - extract_start) * 1000

                if generated_code:
                    state["generated_code"] = generated_code
                    logger.info(
                        f"[Stage 3] Code extracted: length={len(generated_code)}, "
                        f"extract_elapsed_ms={extract_elapsed_ms:.2f}"
                    )
                else:
                    state["error"] = "Failed to extract code from LLM response"
                    logger.error(state["error"])
            else:
                state["error"] = "LLM not available for code generation"
                logger.error(state["error"])

        except Exception as e:
            state["error"] = f"Code generation failed: {str(e)}"
            logger.error(f"[Stage 3] {state['error']}", exc_info=True)

        finally:
            stage_elapsed_ms = (time.time() - stage_start) * 1000
            logger.info(
                f"[Stage 3] Stage completed: task_id={task_id}, "
                f"total_elapsed_ms={stage_elapsed_ms:.2f}, "
                f"has_error={state.get('error') is not None}"
            )

        return state

    async def validate_security(self, state: CodeGenState) -> CodeGenState:
        """Stage 4: Validate generated code for security issues"""
        logger.info(f"[Stage 4] Validating security for task #{state['task_id']}")

        try:
            generated_code = state.get("generated_code", "")

            if not generated_code:
                state["error"] = "No code to validate"
                state["security_validated"] = False
                return state

            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, generated_code, re.IGNORECASE):
                    state["error"] = f"Security violation: dangerous pattern detected ({pattern})"
                    state["security_validated"] = False
                    logger.error(state["error"])
                    return state

            if len(generated_code) > 50000:
                state["error"] = f"Code too long: {len(generated_code)} > 50000 characters"
                state["security_validated"] = False
                logger.error(state["error"])
                return state

            target_files = state.get("target_files", [])
            task_metadata = state.get("task_metadata")
            for file_path in target_files:
                if not self._is_safe_file_path(file_path, task_metadata):
                    state["error"] = f"Unsafe file path: {file_path}"
                    state["security_validated"] = False
                    logger.error(state["error"])
                    return state

            state["security_validated"] = True
            logger.info("Security validation passed")

        except Exception as e:
            state["error"] = f"Security validation failed: {str(e)}"
            state["security_validated"] = False
            logger.error(state["error"])

        return state

    async def apply_code(self, state: CodeGenState) -> CodeGenState:
        """Stage 5: Apply generated code to files with atomic writes"""
        logger.info(f"[Stage 5] Applying code for task #{state['task_id']}")

        try:
            generated_code = state.get("generated_code", "")
            target_files = state.get("target_files", [])

            if not generated_code:
                state["error"] = "No code to apply"
                return state

            if not target_files:
                state["error"] = "No target files specified"
                return state

            target_file = target_files[0]
            task_metadata = state.get("task_metadata")

            if not self._is_safe_file_path(target_file, task_metadata):
                state["error"] = f"Unsafe file path in apply_code: {target_file}"
                logger.error(state["error"])
                return state

            try:
                os.makedirs(os.path.dirname(target_file), exist_ok=True)

                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=os.path.dirname(target_file),
                    prefix='.tmp_',
                    suffix=os.path.basename(target_file)
                )

                try:
                    with os.fdopen(temp_fd, 'w') as f:
                        f.write(generated_code)
                        f.flush()
                        os.fsync(f.fileno())

                    os.replace(temp_path, target_file)
                    logger.info(f"Applied code atomically to: {target_file}")

                except Exception as e:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    raise e

                backup = state["file_backups"].get(target_file, "")
                state["code_diff"] = self._generate_diff(backup, generated_code)

            except Exception as e:
                state["error"] = f"Failed to apply code: {str(e)}"
                logger.error(state["error"])

                self._rollback_changes(state)

        except Exception as e:
            state["error"] = f"Code application failed: {str(e)}"
            logger.error(state["error"])

        return state

    async def generate_tests(self, state: CodeGenState) -> CodeGenState:
        """Stage 6: Generate unit tests for generated code"""
        logger.info(f"[Stage 6] Generating tests for task #{state['task_id']}")

        try:
            generated_code = state.get("generated_code", "")

            if not generated_code:
                logger.warning("No code to generate tests for")
                return state

            result = self.test_generator.generate_tests(
                generated_code,
                file_path=state.get("target_files", ["unknown"])[0]
            )

            if result.get("success"):
                state["generated_tests"] = result.get("test_code", "")
                logger.info(f"Generated {result.get('total_tests', 0)} tests")
            else:
                logger.warning(f"Test generation failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.warning(f"Test generation failed: {str(e)}")

        return state

    async def run_tests(self, state: CodeGenState) -> CodeGenState:
        """Stage 7: Run tests to verify generated code

        Issue #3599: Skip pytest for fix_lint tasks and treat "pytest not found"
        as skipped rather than failed. This prevents infinite retry loops when
        pytest is not available in the environment.
        """
        logger.info(f"[Stage 7] Running tests for task #{state['task_id']}")

        # Issue #3599: Skip tests for fix_lint tasks - lint fixes should be
        # verified by running lint, not pytest. Running pytest for lint fixes
        # causes unnecessary failures and retry loops.
        task_type = state.get("task_type", "")
        if task_type in ("fix_lint", "lint_fix"):
            logger.info(
                f"[Stage 7] Skipping pytest for {task_type} task - "
                "lint fixes don't require test verification"
            )
            state["test_results"] = {
                "success": True,
                "skipped": True,
                "reason": f"pytest skipped for {task_type} task"
            }
            return state

        try:
            if hasattr(self.agent, 'test_tool') and self.agent.test_tool:
                test_results = await self.agent.test_tool.run_tests()
                state["test_results"] = test_results

                if test_results.get("success"):
                    logger.info("Tests passed!")
                else:
                    # Issue #3599: Check if failure is due to pytest not being available
                    error_msg = str(test_results.get('error', ''))
                    if 'No such file or directory' in error_msg and 'pytest' in error_msg:
                        logger.warning(
                            "[Stage 7] pytest not available in environment - "
                            "treating as skipped, not failed"
                        )
                        state["test_results"] = {
                            "success": True,
                            "skipped": True,
                            "reason": "pytest not available in environment"
                        }
                    else:
                        logger.warning(f"Tests failed: {error_msg}")
            else:
                logger.warning("Test tool not available, skipping tests")
                state["test_results"] = {"success": True, "skipped": True}

        except Exception as e:
            error_msg = str(e)
            # Issue #3599: Check if exception is due to pytest not being available
            if 'No such file or directory' in error_msg and 'pytest' in error_msg:
                logger.warning(
                    "[Stage 7] pytest not available in environment - "
                    "treating as skipped, not failed"
                )
                state["test_results"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "pytest not available in environment"
                }
            else:
                logger.warning(f"Test execution failed: {error_msg}")
                state["test_results"] = {"success": False, "error": error_msg}

        return state

    async def create_pr(self, state: CodeGenState) -> CodeGenState:
        """Stage 8: Create Pull Request

        Issue #3595: Skip PR creation if there's already an error in state.
        This prevents misleading 'NoneType' errors when security validation
        or other stages have already failed.
        """
        logger.info(f"[Stage 8] Creating PR for task #{state['task_id']}")

        # Issue #3595: Skip PR creation if there's already an error
        # This happens when security validation fails or other stages error out
        if state.get("error"):
            logger.warning(
                f"[Stage 8] Skipping PR creation due to existing error: {state['error']}"
            )
            return state

        # Issue #3595: Skip PR creation if security validation didn't pass
        # Note: The error check above already returned, so state["error"] is guaranteed
        # to be falsy here (gemini-code-assist suggestion to simplify)
        if not state.get("security_validated", False):
            logger.warning(
                "[Stage 8] Skipping PR creation - security validation not passed"
            )
            state["error"] = "PR creation skipped: security validation not passed"
            return state

        try:
            task_title = state["task_title"]
            code_diff = state.get("code_diff", "")

            pr_title = f"[Code Gen] {task_title}"
            pr_body = f"""

{code_diff[:1000] if code_diff else "No diff available"}

{state.get('test_results', {}).get('summary', 'No test results')}

---
Generated by Code Generation Workflow (Phase 2)
"""

            if hasattr(self.agent, 'git_tool') and self.agent.git_tool:
                pr_result = await self.agent.git_tool.create_pr(
                    title=pr_title,
                    body=pr_body
                )

                # Issue #3589: Defensive None-handling to prevent cascading NoneType errors
                # When file path is blocked or git push fails, pr_result may be None
                if pr_result is None:
                    logger.warning("PR creation returned None - treating as failure")
                    pr_result = {'success': False, 'error': 'create_pr returned None'}

                if pr_result.get("success"):
                    state["pr_number"] = pr_result.get("pr_number")
                    state["pr_url"] = pr_result.get("pr_url")
                    logger.info(f"Created PR #{state['pr_number']}: {state['pr_url']}")
                else:
                    logger.warning(f"PR creation failed: {pr_result.get('error', 'Unknown error')}")
            else:
                logger.warning("Git tool not available, skipping PR creation")

        except Exception as e:
            logger.warning(f"PR creation failed: {str(e)}")
            # CTO Review Fix: Set error state on PR creation failure
            state["error"] = f"PR creation failed: {str(e)}"

        return state

    def _normalize_file_path(self, raw_path: str) -> Optional[str]:
        """
        Normalize a raw file path string extracted from text.

        Issue #3591: Root Cause #21 - Path extraction was including tool prefixes
        like 'pylint handoff/...' which caused path validation to fail.

        This method:
        1. Strips known linter/tool prefixes (pylint, flake8, ruff, mypy, etc.)
        2. Removes leading/trailing whitespace
        3. Strips leading './'
        4. Removes :line:col suffixes (e.g., 'file.py:10:5')
        5. Rejects paths with spaces after normalization (likely not real paths)
        6. Rejects absolute paths (security measure)
        7. Rejects paths containing '..' (directory traversal)

        Args:
            raw_path: Raw path string that may contain tool prefixes

        Returns:
            Normalized path string, or None if path is invalid
        """
        if not raw_path:
            return None

        path = raw_path.strip()

        # Known linter/tool prefixes that may appear before file paths
        # These are stripped only when followed by a space and a path-like string
        tool_prefixes = [
            'pylint ', 'flake8 ', 'ruff ', 'mypy ', 'black ', 'isort ',
            'eslint ', 'prettier ', 'tsc ', 'pyright ',
        ]

        for prefix in tool_prefixes:
            if path.lower().startswith(prefix.lower()):
                path = path[len(prefix):].strip()
                logger.debug(f"Stripped tool prefix '{prefix.strip()}' from path: {raw_path} -> {path}")
                break

        # Strip leading './'
        while path.startswith('./'):
            path = path[2:]

        # Remove :line:col suffixes (e.g., 'file.py:10:5' -> 'file.py')
        # Match pattern: path.ext:number or path.ext:number:number
        # gemini-code-assist: Use generic extension pattern to support all file types
        line_col_match = re.match(r'^(.+\.[a-zA-Z0-9]+):\d+(?::\d+)?$', path)
        if line_col_match:
            path = line_col_match.group(1)
            logger.debug(f"Stripped line:col suffix from path: {raw_path} -> {path}")

        # Reject paths with spaces (likely not real file paths)
        if ' ' in path:
            logger.debug(f"Rejected path with spaces: {path}")
            return None

        # Reject absolute paths (security measure)
        if path.startswith('/'):
            logger.debug(f"Rejected absolute path: {path}")
            return None

        # Reject paths with directory traversal
        if '..' in path:
            logger.debug(f"Rejected path with '..': {path}")
            return None

        # Validate it looks like a real path
        # gemini-code-assist: Allow dotfiles like .gitignore, .prettierrc
        # Security validation for sensitive dotfiles is handled in _is_safe_file_path
        if not path:
            logger.debug(f"Rejected empty path: {path}")
            return None

        return path

    def _extract_file_paths(self, text: str) -> List[str]:
        """Extract and normalize file paths from text"""
        file_patterns = [
            r'`([^`]+\.(py|js|ts|jsx|tsx|md))`',
            r'([a-zA-Z0-9_/\-]+\.(py|js|ts|jsx|tsx|md))',
        ]

        files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                raw_path = match[0] if isinstance(match, tuple) else match
                # Issue #3591: Normalize path to strip tool prefixes
                normalized_path = self._normalize_file_path(raw_path)
                if normalized_path and normalized_path not in files:
                    files.append(normalized_path)

        return files

    def _is_safe_file_path(self, file_path: str, task_metadata: dict = None) -> bool:
        """
        Check if file path is safe with repo root restriction and symlink defense

        Security improvements (CTO review Phase 2 Step B):
        1. Repo root boundary enforcement (prevents writing outside project)
        2. Path normalization to resolve '..' and '.'
        3. Symlink resolution to prevent directory traversal
        4. Exact path prefix matching instead of substring matching
        5. Block writes to .git directory
        6. Global deny list for critical paths (migrations, settings, .env)

        Phase 2 Step B-1 improvements:
        7. Per-task directory whitelist (allowed_directories from task_metadata)

        Args:
            file_path: Path to validate
            task_metadata: Optional task metadata with allowed_directories constraint
        """
        try:
            if not os.path.isabs(file_path):
                candidate_path = os.path.join(self.repo_root, file_path)
            else:
                candidate_path = file_path

            normalized_path = os.path.realpath(os.path.abspath(candidate_path))

            if os.path.commonpath([normalized_path, self.repo_root]) != self.repo_root:
                logger.warning(
                    f"Blocked path outside repo root: {file_path} -> {normalized_path} "
                    f"(repo: {self.repo_root})"
                )
                return False

            git_dir = os.path.join(self.repo_root, '.git')
            if os.path.exists(git_dir):
                git_dir_normalized = os.path.realpath(git_dir)
                try:
                    if os.path.commonpath([normalized_path, git_dir_normalized]) == git_dir_normalized:
                        logger.warning(f"Blocked write to .git directory: {file_path} -> {normalized_path}")
                        return False
                except ValueError:
                    pass

            dangerous_prefixes = [
                '/etc/', '/sys/', '/proc/', '/dev/',
                '/root/',
            ]

            home_dangerous = [
                os.path.expanduser('~/.ssh/'),
                os.path.expanduser('~/.aws/'),
                os.path.expanduser('~/.config/'),
            ]
            dangerous_prefixes.extend(home_dangerous)

            for dangerous in dangerous_prefixes:
                dangerous_normalized = os.path.realpath(os.path.abspath(dangerous))
                if normalized_path.startswith(dangerous_normalized):
                    logger.warning(f"Blocked dangerous path: {file_path} -> {normalized_path}")
                    return False

            if '..' in file_path:
                logger.warning(f"Blocked path with '..': {file_path}")
                return False

            # CTO Review Fix: Global deny list for critical files/directories
            # These are blocked regardless of task type
            # Issue #3589: Block security-sensitive orchestrator code but allow tests
            forbidden_patterns = [
                '/migrations/',
                'settings.py',
                '.env',
                'policies.yaml',
                '/infra/',
                'credentials',
                '/project_engineer/safe_tasks.py',
                '/project_engineer/agent.py',
            ]

            for pattern in forbidden_patterns:
                if pattern in normalized_path or normalized_path.endswith(pattern):
                    logger.warning(f"Blocked forbidden pattern '{pattern}': {file_path} -> {normalized_path}")
                    return False

            # Phase 2 Step B-1: Per-task directory whitelist
            # Phase 2 Step B-1 Follow-up: Separate allowed_files and allowed_directories
            # If task_metadata specifies constraints, enforce them
            if task_metadata and ('allowed_directories' in task_metadata or 'allowed_files' in task_metadata):
                allowed_dirs = task_metadata.get('allowed_directories', [])
                allowed_files = task_metadata.get('allowed_files', [])

                # If both are empty, no restriction
                if not allowed_dirs and not allowed_files:
                    return True

                # Normalize file_path relative to repo_root for comparison
                try:
                    rel_path = os.path.relpath(normalized_path, self.repo_root)
                except ValueError:
                    # Path is on different drive (Windows) or outside repo
                    logger.warning(f"Cannot compute relative path for {file_path}")
                    return False

                # Check if file matches any allowed file (exact match) or directory (prefix match)
                is_allowed_as_file = any(rel_path == os.path.normpath(f) for f in allowed_files)
                is_allowed_in_dir = any(
                    rel_path.startswith(os.path.join(os.path.normpath(d), '')) for d in allowed_dirs
                )
                is_allowed = is_allowed_as_file or is_allowed_in_dir

                if not is_allowed:
                    logger.warning(
                        f"Blocked path outside allowed constraints: {file_path} -> {rel_path}. "
                        f"Allowed files: {allowed_files}, Allowed directories: {allowed_dirs}"
                    )
                    return False

            return True

        except (OSError, ValueError) as e:
            logger.warning(f"Path validation failed for {file_path}: {e}")
            return False

    def _build_code_generation_prompt(
        self,
        task_type: str,
        task_description: str,
        target_files: List[str]
    ) -> str:
        """Build prompt for code generation"""
        prompt = f"""Generate code for the following task:

Task Type: {task_type}
Description: {task_description}
Target Files: {', '.join(target_files) if target_files else 'Not specified'}

Requirements:
1. Generate clean, production-ready code
2. Follow best practices for {task_type}
3. Include proper error handling
4. Add type hints (Python) or TypeScript types
5. Write clear, self-documenting code
6. Do NOT use eval, exec, or other dangerous functions

Generate the complete code:"""

        return prompt

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract code from LLM response"""
        code_blocks = re.findall(r'```(?:python|javascript|typescript)?\n(.*?)\n```', response, re.DOTALL)

        if code_blocks:
            return code_blocks[0]

        return response.strip()

    def _generate_diff(self, old_code: str, new_code: str) -> str:
        """Generate simple diff between old and new code"""
        if not old_code:
            return f"+++ NEW FILE +++\n{new_code[:500]}"

        return f"--- OLD\n{old_code[:250]}\n\n+++ NEW\n{new_code[:250]}"

    def _rollback_changes(self, state: CodeGenState):
        """Rollback code changes on error"""
        logger.info("Rolling back changes...")

        try:
            for file_path, backup_content in state.get("file_backups", {}).items():
                try:
                    with open(file_path, 'w') as f:
                        f.write(backup_content)
                    logger.info(f"Rolled back: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to rollback {file_path}: {e}")

        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code generation workflow

        Args:
            task: Task dict with id, title, description, and optionally task_type/task_metadata
                  If task_type is provided, classification stage will be skipped.
                  Issue #3593: Also accepts changed_files as fallback for target files.

        Returns:
            Final state dict
        """
        initial_state: CodeGenState = {
            "task_id": task.get("id", 0),
            "task_title": task.get("title", ""),
            "task_description": task.get("description", ""),
            "task_type": task.get("task_type"),
            "task_metadata": task.get("task_metadata"),
            "target_files": [],
            "changed_files": task.get("changed_files"),  # Issue #3593: fallback target files
            "generated_code": None,
            "generated_tests": None,
            "code_diff": None,
            "test_results": None,
            "pr_number": None,
            "pr_url": None,
            "error": None,
            "execution_start": time.time(),
            "file_backups": {},
            "security_validated": False,
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            execution_time = time.time() - initial_state["execution_start"]
            logger.info(f"Workflow completed in {execution_time:.2f}s")

            return final_state

        except Exception as e:
            # Issue #3567: Use logger.exception for full traceback and store meaningful error
            # An exception with empty str(e) becomes indistinguishable from "no error"
            error_str = str(e)
            if not error_str:
                error_str = f"{type(e).__name__}: (empty exception message)"
            logger.exception(f"Workflow execution failed: {error_str}")
            initial_state["error"] = error_str
            return initial_state
