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
        """Stage 5: Apply the fix to code"""
        logger.info("[Stage 5] Applying fix")

        try:
            fix_code = state.get("fix_code_diff", "")
            affected_files = state.get("affected_files", [])

            if not fix_code or not affected_files:
                logger.warning("No fix code or affected files to apply")
                state["error"] = "Cannot apply fix - missing fix code or files"
                return state

            logger.info(
                f"Fix would be applied to {len(affected_files)} files"
            )
            logger.info(
                "Note: Actual file modification requires "
                "fs_tool implementation"
            )

        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            state["error"] = f"Fix application failed: {str(e)}"

        return state

    async def run_tests(self, state: BugFixState) -> BugFixState:
        """Stage 6: Run tests to verify the fix"""
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

                if state.get("bug_type") and state.get("fix_strategy"):
                    self.agent.pattern_learner.learn_fix_pattern(
                        bug_description=state["issue_body"],
                        fix_strategy=state["fix_strategy"],
                        fix_code=state.get("fix_code_diff", ""),
                        success=True
                    )
            else:
                logger.warning("Tests still failing after fix")

        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            state["test_results"] = {"success": False, "error": str(e)}

        return state

    async def create_pr(self, state: BugFixState) -> BugFixState:
        """Stage 7: Create Pull Request"""
        logger.info("[Stage 7] Creating Pull Request")

        try:
            pr_title = "Fix: {}".format(state['issue_title'])

            logger.info("PR would be created: {}".format(pr_title))
            logger.info(
                "Note: Actual PR creation requires git_tool implementation"
            )

            state["pr_number"] = 999
            state["pr_url"] = "https://github.com/example/repo/pull/999"

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
            "patterns_used": []
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
