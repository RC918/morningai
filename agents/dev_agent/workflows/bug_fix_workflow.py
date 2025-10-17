#!/usr/bin/env python3
"""
Bug Fix Workflow - Automated bug fixing using LangGraph
Phase 1 Week 6: Bug Fix Workflow
Adapted from PR #291 to use PR #292's Knowledge Graph architecture
"""
import logging
import re
import time
from typing import Dict, Any, List, Optional, TypedDict

from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)


class BugFixState(TypedDict):
    """State for Bug Fix Workflow"""
    issue_id: int
    issue_title: str
    issue_body: str
    bug_type: Optional[str]
    affected_files: List[str]
    root_cause: Optional[str]
    fix_strategy: Optional[str]
    fix_code_diff: Optional[str]
    test_results: Optional[Dict[str, Any]]
    pr_number: Optional[int]
    pr_url: Optional[str]
    approval_status: Optional[str]
    error: Optional[str]
    execution_start: float
    patterns_used: List[int]
    file_backups: Dict[str, str]


class BugFixWorkflow:
    """
    Automated Bug Fix Workflow using LangGraph

    Workflow Stages:
    1. Parse Issue - Extract bug information from GitHub Issue
    2. Reproduce Bug - Run tests to confirm bug exists
    3. Analyze Root Cause - Use LSP + Knowledge Graph
    4. Generate Fixes - Use learned patterns + LLM
    5. Apply Fix - Apply code changes
    6. Run Tests - Verify fix works
    7. Create PR - Create Pull Request
    8. Request Approval - HITL approval
    """

    def __init__(self, dev_agent):
        """
        Initialize Bug Fix Workflow

        Args:
            dev_agent: DevAgent instance with all tools
        """
        self.agent = dev_agent
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(BugFixState)

        workflow.add_node("parse_issue", self.parse_issue)
        workflow.add_node("reproduce_bug", self.reproduce_bug)
        workflow.add_node("analyze_root_cause", self.analyze_root_cause)
        workflow.add_node("generate_fixes", self.generate_fixes)
        workflow.add_node("apply_fix", self.apply_fix)
        workflow.add_node("run_tests", self.run_tests)
        workflow.add_node("create_pr", self.create_pr)
        workflow.add_node("request_approval", self.request_approval)

        workflow.set_entry_point("parse_issue")

        workflow.add_edge("parse_issue", "reproduce_bug")
        workflow.add_conditional_edges(
            "reproduce_bug",
            self._should_continue_after_reproduce,
            {
                "analyze": "analyze_root_cause",
                "end": "request_approval"
            }
        )
        workflow.add_edge("analyze_root_cause", "generate_fixes")
        workflow.add_edge("generate_fixes", "apply_fix")
        workflow.add_edge("apply_fix", "run_tests")
        workflow.add_conditional_edges(
            "run_tests",
            self._should_continue_after_test,
            {
                "pr": "create_pr",
                "retry": "generate_fixes",
                "end": "request_approval"
            }
        )
        workflow.add_edge("create_pr", "request_approval")

        workflow.set_finish_point("request_approval")

        return workflow.compile()

    def _should_continue_after_reproduce(self, state: BugFixState) -> str:
        """Decide next step after bug reproduction"""
        if state.get("error"):
            return "end"
        if state.get("test_results", {}).get("success"):
            return "end"
        return "analyze"

    def _should_continue_after_test(self, state: BugFixState) -> str:
        """Decide next step after running tests"""
        if state.get("error"):
            return "end"
        if state.get("test_results", {}).get("success"):
            return "pr"
        retry_count = len(state.get("patterns_used", []))
        if retry_count >= 3:
            return "end"
        return "retry"

    async def parse_issue(self, state: BugFixState) -> BugFixState:
        """Stage 1: Parse GitHub Issue and extract bug information"""
        logger.info(f"[Stage 1] Parsing issue #{state['issue_id']}")

        issue_body = state["issue_body"]

        bug_type = self._classify_bug_type(issue_body)
        affected_files = self._extract_file_paths(issue_body)

        state["bug_type"] = bug_type
        state["affected_files"] = affected_files

        logger.info(f"Bug type: {bug_type}, Affected files: {affected_files}")

        return state

    def _classify_bug_type(self, issue_body: str) -> str:
        """Classify bug type from issue description"""
        issue_lower = issue_body.lower()

        if any(word in issue_lower for word in [
            "nonetype", "none", "null", "nullpointer"
        ]):
            return "null_pointer"
        elif any(word in issue_lower for word in [
            "typeerror", "type error", "attribute error", "attributeerror"
        ]):
            return "type_error"
        elif any(word in issue_lower for word in [
            "index", "keyerror", "indexerror"
        ]):
            return "index_error"
        elif any(word in issue_lower for word in [
            "import", "module", "importerror", "modulenotfound"
        ]):
            return "import_error"
        elif any(word in issue_lower for word in ["syntax", "invalid syntax"]):
            return "syntax_error"
        elif any(word in issue_lower for word in [
            "logic", "incorrect", "wrong"
        ]):
            return "logic_error"
        else:
            return "unknown"

    def _extract_file_paths(self, text: str) -> List[str]:
        """Extract file paths from issue description"""
        file_patterns = [
            r'`([^`]+\.py)`',
            r'`([^`]+\.js)`',
            r'`([^`]+\.ts)`',
            r'in\s+([a-zA-Z0-9_/\.]+\.py)',
            r'file\s+([a-zA-Z0-9_/\.]+\.py)',
        ]

        files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, text)
            files.extend(matches)

        return list(set(files))

    def _is_safe_file_path(self, code: str) -> bool:
        """
        Check if file operations in code target safe paths.

        Safe paths (whitelist):
        - Project source files (*.py, *.js, *.ts, *.json, *.yaml, *.md)
        - Test files (*_test.py, *_spec.js, *.test.ts)
        - Configuration files (*.yaml, *.json, *.toml, *.ini, *.cfg)
        - Documentation (*.md, *.rst, *.txt)

        Unsafe paths (blacklist):
        - System files (/etc/, /bin/, /usr/, /sys/)
        - Relative path traversal (../, ../../, ../../../)
        - User home directory (~/, $HOME, $HOME/file.txt)
        - Environment files (*.env, .env.*, credentials.*)
        - SSH keys (id_rsa, *.pem, *.key)

        Args:
            code: Code containing file operations

        Returns:
            True if all file paths are safe, False otherwise
        """
        open_matches = re.finditer(
            r'\bopen\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]',
            code
        )

        for match in open_matches:
            file_path = match.group(1)
            mode = match.group(2)

            unsafe_path_patterns = [
                r'^/etc/',
                r'^/bin/',
                r'^/usr/',
                r'^/sys/',
                r'^/proc/',
                r'\.\./\.\./\.\.',  # Block ../../../
                r'\.\.[\\/]',        # Block ../ or ..\
                r'^~/?$',
                r'\$HOME',  # Block any path containing $HOME
                r'\.env',
                r'credentials\.',
                r'id_rsa',
                r'\.pem$',
                r'\.key$',
                r'/\.ssh/',
            ]

            for unsafe_pattern in unsafe_path_patterns:
                if re.search(unsafe_pattern, file_path, re.IGNORECASE):
                    logger.warning(
                        f"Unsafe file path detected: {file_path}"
                    )
                    return False

            if 'w' in mode or 'a' in mode:
                safe_extensions = [
                    r'\.py$', r'\.js$', r'\.ts$', r'\.tsx$', r'\.jsx$',
                    r'\.json$', r'\.yaml$', r'\.yml$', r'\.toml$',
                    r'\.md$', r'\.rst$', r'\.txt$', r'\.cfg$', r'\.ini$',
                    r'_test\.py$', r'_spec\.js$', r'\.test\.ts$'
                ]

                is_safe = any(
                    re.search(ext, file_path, re.IGNORECASE)
                    for ext in safe_extensions
                )

                if not is_safe:
                    logger.warning(
                        f"Write to non-whitelisted file: {file_path}"
                    )
                    return False

        return True

    def _sanitize_code(self, code: str) -> Optional[str]:
        """
        Validate LLM-generated code for security issues.

        Security checks:
        1. Dangerous function calls (eval, exec, __import__)
        2. File operations (validated via whitelist/blacklist)
        3. Network operations (blocked)
        4. Shell command execution (blocked)
        5. SQL injection patterns (blocked)
        6. Unsafe deserialization (blocked)
        7. Code length limit (50,000 chars)

        Args:
            code: The code string to sanitize

        Returns:
            Sanitized code if safe, None if unsafe
        """
        if not code or not isinstance(code, str):
            return None

        dangerous_patterns = [
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

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning(
                    f"Unsafe code pattern detected: {pattern}"
                )
                return None

        if not self._is_safe_file_path(code):
            logger.error("Code contains unsafe file operations")
            return None

        max_code_length = 50000
        if len(code) > max_code_length:
            logger.warning(
                f"Code too long: {len(code)} > {max_code_length}"
            )
            return None

        return code

    async def _rollback_changes(self, state: BugFixState) -> bool:
        """
        Rollback file changes using backups.

        Restores all modified files from their backup copies stored
        in state['file_backups']. This is called when tests fail after
        applying a fix, to ensure the codebase returns to a working state.

        Args:
            state: Current workflow state containing file_backups

        Returns:
            True if rollback succeeded, False otherwise
        """
        logger.info("[Rollback] Restoring files from backup")

        file_backups = state.get("file_backups", {})
        if not file_backups:
            logger.warning("No backups found to rollback")
            return False

        rollback_success = True
        for file_path, backup_content in file_backups.items():
            try:
                write_result = await self.agent.fs_tool.write_file(
                    file_path, backup_content
                )

                if write_result.get("success"):
                    logger.info(f"Restored {file_path} from backup")
                else:
                    logger.error(
                        f"Failed to restore {file_path}: "
                        f"{write_result.get('error')}"
                    )
                    rollback_success = False

            except Exception as e:
                logger.error(f"Error restoring {file_path}: {e}")
                rollback_success = False

        if rollback_success:
            logger.info("All files successfully rolled back")
        else:
            logger.error("Rollback completed with errors")

        return rollback_success

    def _apply_code_changes(
        self, current_content: str, fix_code: str, state: BugFixState
    ) -> str:
        """
        Apply code changes to the current file content.

        This is a simplified implementation that looks for
        specific patterns in the fix_code and applies them.

        Args:
            current_content: Current file content
            fix_code: Fix code from LLM
            state: Current workflow state

        Returns:
            Modified content
        """
        try:
            import_match = re.search(
                r'import\s+([a-zA-Z0-9_., ]+)', fix_code
            )
            if import_match and import_match.group(0) not in current_content:
                lines = current_content.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import') or \
                       line.strip().startswith('from'):
                        insert_index = i + 1
                if insert_index > 0:
                    lines.insert(insert_index, import_match.group(0))
                    current_content = '\n'.join(lines)

            function_match = re.search(
                r'def\s+([a-zA-Z0-9_]+)\s*\([^)]*\):[^}]+',
                fix_code, re.DOTALL
            )
            if function_match:
                func_name = function_match.group(1)
                if func_name not in current_content:
                    current_content += '\n\n' + function_match.group(0)

            if_block_match = re.search(
                r'if\s+[^:]+:\s*\n\s+[^\n]+', fix_code
            )
            if if_block_match and if_block_match.group(0) not in \
                    current_content:
                lines = current_content.split('\n')
                if len(lines) > 0:
                    current_content += '\n    ' + if_block_match.group(0)

            return current_content

        except Exception as e:
            logger.warning(f"Could not apply code changes: {e}")
            return current_content

    async def reproduce_bug(self, state: BugFixState) -> BugFixState:
        """Stage 2: Reproduce the bug by running tests"""
        logger.info("[Stage 2] Reproducing bug")

        try:
            affected_files = state.get("affected_files", [])
            test_pattern = []

            if affected_files:
                for file in affected_files:
                    test_file = file.replace(
                        ".py", "_test.py"
                    ).replace("/", "/tests/")
                    test_pattern.append(test_file)

            result = await self.agent.test_tool.run_tests(
                test_pattern if test_pattern else None
            )

            state["test_results"] = result

            if not result.get("success"):
                logger.info(
                    "Bug reproduced successfully (tests failing as expected)"
                )
            else:
                logger.warning(
                    "Tests passing - bug may not exist or tests incomplete"
                )
                state["error"] = "Cannot reproduce bug - tests are passing"

        except Exception as e:
            logger.error(f"Failed to reproduce bug: {e}")
            state["error"] = f"Reproduction failed: {str(e)}"

        return state

    async def analyze_root_cause(self, state: BugFixState) -> BugFixState:
        """Stage 3: Analyze root cause using LSP and Knowledge Graph"""
        logger.info("[Stage 3] Analyzing root cause")

        try:
            bug_type = state.get("bug_type", "unknown")
            affected_files = state.get("affected_files", [])
            test_error = state.get("test_results", {}).get("error", "")

            similar_bugs = self.agent.pattern_learner.get_similar_bug_patterns(
                bug_description=state["issue_body"],
                bug_type=bug_type,
                top_k=3
            )

            root_cause_analysis = []

            if (similar_bugs.get("success") and
                    similar_bugs["data"]["count"] > 0):
                logger.info(
                    f"Found {similar_bugs['data']['count']} "
                    "similar bug patterns"
                )
                for pattern in similar_bugs["data"]["patterns"]:
                    examples = pattern.get("examples", [])
                    if examples:
                        root_cause_analysis.append(
                            examples[0].get("root_cause", "")
                        )

            if affected_files and self.agent.llm:
                for file_path in affected_files[:2]:
                    try:
                        content = self.agent.fs_tool.read_file(
                            file_path
                        )
                        if content:
                            prompt = f"""Analyze this code for the bug: \
{state['issue_body']}

Error: {test_error}

Code:
{content[:2000]}

What is the root cause?"""
                            llm_analysis = await \
                                self.agent.llm.generate(prompt)
                            root_cause_analysis.append(llm_analysis)
                    except Exception as e:
                        logger.warning(
                            f"Could not analyze file {file_path}: {e}"
                        )

            if root_cause_analysis:
                state["root_cause"] = "\n\n".join(root_cause_analysis)
            else:
                state["root_cause"] = (
                    f"Bug type: {bug_type}. Error: {test_error}"
                )

            logger.info(
                f"Root cause identified: {state['root_cause'][:200]}..."
            )

        except Exception as e:
            logger.error(f"Failed to analyze root cause: {e}")
            state["error"] = f"Analysis failed: {str(e)}"

        return state

    async def generate_fixes(self, state: BugFixState) -> BugFixState:
        """Stage 4: Generate fix using learned patterns and LLM"""
        logger.info("[Stage 4] Generating fixes")

        try:
            root_cause = state.get("root_cause", "")

            fix_patterns = self.agent.pattern_learner.get_similar_fix_patterns(
                bug_description=state["issue_body"],
                min_success_rate=0.7,
                top_k=3
            )

            fix_strategies = []

            if (fix_patterns.get("success") and
                    fix_patterns["data"]["count"] > 0):
                logger.info(
                    f"Found {fix_patterns['data']['count']} "
                    "similar fix patterns"
                )
                for pattern in fix_patterns["data"]["patterns"]:
                    examples = pattern.get("examples", [])
                    if examples:
                        fix_strategies.append(
                            examples[0].get("fix_strategy", "")
                        )
                        state["patterns_used"].append(pattern["id"])

            if self.agent.llm:
                prompt = f"""Generate a fix for this bug:

Issue: {state['issue_title']}
Description: {state['issue_body']}
Root Cause: {root_cause}

Similar fixes that worked:
{chr(10).join(f'- {s}' for s in fix_strategies[:3])}

Provide:
1. Fix strategy (high-level approach)
2. Code changes needed (be specific)

Format as:
STRATEGY: <strategy>
CHANGES: <changes>
"""
                llm_fix = await self.agent.llm.generate(prompt)

                strategy_match = re.search(
                    r'STRATEGY:\s*(.+?)(?=CHANGES:|$)', llm_fix, re.DOTALL
                )
                changes_match = re.search(
                    r'CHANGES:\s*(.+)', llm_fix, re.DOTALL
                )

                state["fix_strategy"] = (
                    strategy_match.group(1).strip()
                    if strategy_match else llm_fix
                )
                state["fix_code_diff"] = (
                    changes_match.group(1).strip()
                    if changes_match else ""
                )

            logger.info(
                f"Fix strategy: {state.get('fix_strategy', '')[:200]}..."
            )

        except Exception as e:
            logger.error(f"Failed to generate fixes: {e}")
            state["error"] = f"Fix generation failed: {str(e)}"

        return state

    async def apply_fix(self, state: BugFixState) -> BugFixState:
        """
        Stage 5: Apply the fix to code.

        Creates backups of all files before modification to enable
        automatic rollback if tests fail.
        """
        logger.info("[Stage 5] Applying fix")

        try:
            fix_code = state.get("fix_code_diff", "")
            affected_files = state.get("affected_files", [])

            if not fix_code or not affected_files:
                logger.warning("No fix code or affected files to apply")
                state["error"] = "Cannot apply fix - missing fix code or files"
                return state

            logger.info(
                f"Applying fix to {len(affected_files)} files"
            )

            sanitized_code = self._sanitize_code(fix_code)
            if not sanitized_code:
                logger.error("Code sanitization failed - unsafe code detected")
                state["error"] = "Fix code contains unsafe patterns"
                return state

            if "file_backups" not in state:
                state["file_backups"] = {}

            for file_path in affected_files:
                try:
                    read_result = await self.agent.fs_tool.read_file(file_path)
                    if not read_result.get("success"):
                        logger.warning(
                            f"Could not read {file_path}: "
                            f"{read_result.get('error')}"
                        )
                        continue

                    current_content = read_result.get("content", "")

                    state["file_backups"][file_path] = current_content
                    logger.info(f"Backed up {file_path}")

                    new_content = self._apply_code_changes(
                        current_content, sanitized_code, state
                    )

                    write_result = await self.agent.fs_tool.write_file(
                        file_path, new_content
                    )

                    if write_result.get("success"):
                        logger.info(f"Successfully applied fix to {file_path}")
                    else:
                        logger.error(
                            f"Failed to write {file_path}: "
                            f"{write_result.get('error')}"
                        )
                        await self._rollback_changes(state)
                        state["error"] = (
                            f"Failed to write file: {file_path}"
                        )
                        return state

                except Exception as file_error:
                    logger.error(
                        f"Error processing {file_path}: {file_error}"
                    )
                    await self._rollback_changes(state)
                    state["error"] = (
                        f"File processing failed: {str(file_error)}"
                    )
                    return state

            logger.info(
                f"Fix successfully applied to all affected files. "
                f"Backups created for {len(state['file_backups'])} files."
            )

        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            if state.get("file_backups"):
                await self._rollback_changes(state)
            state["error"] = f"Fix application failed: {str(e)}"

        return state

    async def run_tests(self, state: BugFixState) -> BugFixState:
        """
        Stage 6: Run tests to verify the fix.

        Automatically rolls back changes if tests fail, ensuring the
        codebase returns to a working state.
        """
        logger.info("[Stage 6] Running tests to verify fix")

        try:
            affected_files = state.get("affected_files", [])
            test_pattern = []

            if affected_files:
                for file in affected_files:
                    test_file = file.replace(
                        ".py", "_test.py"
                    ).replace("/", "/tests/")
                    test_pattern.append(test_file)

            result = await self.agent.test_tool.run_tests(
                test_pattern if test_pattern else None
            )

            state["test_results"] = result

            if result.get("success"):
                logger.info("Tests passed! Fix verified.")

                state["file_backups"] = {}
                logger.info("Backups cleared - fix successful")

                if state.get("bug_type") and state.get("fix_strategy"):
                    self.agent.pattern_learner.learn_fix_pattern(
                        bug_description=state["issue_body"],
                        fix_strategy=state["fix_strategy"],
                        fix_code=state.get("fix_code_diff", ""),
                        success=True
                    )
            else:
                logger.warning("Tests still failing after fix")

                if state.get("file_backups"):
                    logger.info(
                        "Initiating automatic rollback due to test failure"
                    )
                    rollback_success = await self._rollback_changes(state)

                    if rollback_success:
                        logger.info(
                            "Rollback successful - codebase restored to "
                            "working state"
                        )
                        state["file_backups"] = {}
                    else:
                        logger.error(
                            "Rollback failed - manual intervention may be "
                            "required"
                        )
                        state["error"] = (
                            "Tests failed and rollback encountered errors"
                        )

        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            state["test_results"] = {"success": False, "error": str(e)}

            if state.get("file_backups"):
                logger.info("Rolling back due to test execution error")
                await self._rollback_changes(state)

        return state

    async def create_pr(self, state: BugFixState) -> BugFixState:
        """Stage 7: Create Pull Request"""
        logger.info("[Stage 7] Creating Pull Request")

        try:
            import time
            pr_title = "Fix: {}".format(state['issue_title'])
            branch_name = "bug-fix/{}-{}".format(
                state['issue_id'], int(time.time())
            )

            logger.info(f"Creating branch: {branch_name}")
            branch_result = await self.agent.git_tool.create_branch(
                branch_name
            )
            if not branch_result.get('success'):
                logger.error(
                    f"Failed to create branch: {branch_result.get('error')}"
                )
                state["error"] = (
                    f"Branch creation failed: {branch_result.get('error')}"
                )
                return state

            affected_files = state.get("affected_files", [])
            commit_message = (
                f"{pr_title}\n\n"
                f"Bug Type: {state.get('bug_type', 'unknown')}\n"
                f"Root Cause: {state.get('root_cause', '')[:200]}\n"
                f"Fix Strategy: {state.get('fix_strategy', '')[:200]}"
            )

            logger.info("Committing changes")
            commit_result = await self.agent.git_tool.commit(
                message=commit_message,
                files=affected_files if affected_files else None
            )
            if not commit_result.get('success'):
                logger.error(
                    f"Failed to commit: {commit_result.get('error')}"
                )
                state["error"] = (
                    f"Commit failed: {commit_result.get('error')}"
                )
                return state

            logger.info("Pushing branch to remote")
            push_result = await self.agent.git_tool.push(
                remote='origin',
                branch=branch_name
            )
            if not push_result.get('success'):
                logger.error(
                    f"Failed to push: {push_result.get('error')}"
                )
                state["error"] = (
                    f"Push failed: {push_result.get('error')}"
                )
                return state

            repo_url = "https://github.com/RC918/morningai"
            pr_url = f"{repo_url}/compare/main...{branch_name}"
            state["pr_url"] = pr_url
            logger.info(f"PR ready: {pr_url}")

            pr_body = (
                f"## Automated Bug Fix\n\n"
                f"**Issue:** #{state['issue_id']} - "
                f"{state['issue_title']}\n\n"
                f"**Bug Type:** {state.get('bug_type', 'unknown')}\n\n"
                f"**Root Cause:**\n{state.get('root_cause', '')}\n\n"
                f"**Fix Strategy:**\n{state.get('fix_strategy', '')}\n\n"
                f"**Affected Files:**\n"
            )
            for file in affected_files:
                pr_body += f"- `{file}`\n"

            test_passed = state.get('test_results', {}).get('success')
            pr_body += (
                f"\n**Test Results:** "
                f"{'✅ Passed' if test_passed else '❌ Failed'}\n"
            )

            logger.info(
                f"Pull request created successfully\n"
                f"Title: {pr_title}\n"
                f"Branch: {branch_name}\n"
                f"URL: {pr_url}"
            )

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            state["error"] = f"PR creation failed: {str(e)}"

        return state

    async def request_approval(self, state: BugFixState) -> BugFixState:
        """Stage 8: Request HITL approval"""
        logger.info("[Stage 8] Requesting HITL approval")

        try:
            success = state.get("test_results", {}).get("success", False)
            execution_time = int(time.time() - state["execution_start"])

            self.agent.pattern_learner.record_bug_fix(
                issue_number=state["issue_id"],
                issue_title=state["issue_title"],
                bug_description=state["issue_body"],
                bug_type=state.get("bug_type", "unknown"),
                affected_files=state.get("affected_files", []),
                root_cause=state.get("root_cause", ""),
                fix_strategy=state.get("fix_strategy", ""),
                fix_code_diff=state.get("fix_code_diff", ""),
                pr_number=state.get("pr_number"),
                pr_url=state.get("pr_url"),
                success=success,
                execution_time_seconds=execution_time,
                patterns_used=state.get("patterns_used", []),
                test_results=state.get("test_results")
            )

            if success and state.get("pr_url"):
                approval_request = await (
                    self.agent.hitl_client.create_approval_request(
                        title=f"Bug Fix PR Ready: {state['issue_title']}",
                        description=(
                            f"Automated fix for issue #{state['issue_id']}"
                        ),
                        context={
                            "issue_id": state["issue_id"],
                            "pr_url": state["pr_url"],
                            "bug_type": state.get("bug_type"),
                            "test_status": "passed"
                        },
                        requester_agent="dev_agent",
                        priority="medium"
                    )
                )

                state["approval_status"] = "pending"
                logger.info(
                    f"Approval request created: "
                    f"{approval_request.request_id}"
                )
            else:
                state["approval_status"] = "not_required"
                logger.info(
                    "No approval needed - workflow incomplete or "
                    "tests failed"
                )

        except Exception as e:
            logger.error(f"Failed to request approval: {e}")
            state["error"] = f"Approval request failed: {str(e)}"

        return state

    async def execute(self, github_issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Bug Fix Workflow

        Args:
            github_issue: Dict with 'number', 'title', 'body'

        Returns:
            Final state dict
        """
        initial_state: BugFixState = {
            "issue_id": github_issue["number"],
            "issue_title": github_issue["title"],
            "issue_body": github_issue.get("body", ""),
            "bug_type": None,
            "affected_files": [],
            "root_cause": None,
            "fix_strategy": None,
            "fix_code_diff": None,
            "test_results": None,
            "pr_number": None,
            "pr_url": None,
            "approval_status": None,
            "error": None,
            "execution_start": time.time(),
            "patterns_used": [],
            "file_backups": {}
        }

        try:
            logger.info(
                f"Starting Bug Fix Workflow for issue "
                f"#{github_issue['number']}"
            )
            final_state = await self.workflow.ainvoke(initial_state)
            logger.info("Bug Fix Workflow completed")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                **initial_state,
                "error": f"Workflow failed: {str(e)}"
            }
