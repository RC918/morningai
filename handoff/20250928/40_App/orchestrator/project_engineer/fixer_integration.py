#!/usr/bin/env python3
"""
Auto Fixer Integration - Phase 2 Step C Fixer Node
Integrates ReviewerAgent and ProjectEngineerAgent for auto-fixing CI failures.

This module provides:
1. AutoFixer class for orchestrating auto-fix attempts
2. Canary rollout support via PROJECT_ENGINEER_FIXER_PERCENT
3. ReviewerAgent integration for analyzing CI failures
4. ProjectEngineerAgent integration for generating fixes
"""
import hashlib
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from common.config.settings import Settings

logger = logging.getLogger(__name__)


class AutoFixer:
    """
    Orchestrates auto-fix attempts using ReviewerAgent and ProjectEngineerAgent.

    This class is responsible for:
    1. Determining if auto-fix should run for a given task (canary logic)
    2. Running ReviewerAgent to analyze code issues
    3. Building fix task descriptions from review results
    4. Invoking ProjectEngineerAgent to generate fixes

    Usage:
        from project_engineer.fixer_integration import AutoFixer
        from common.config.settings import settings

        fixer = AutoFixer(settings=settings)
        if fixer.should_run_for_task(state):
            new_state = fixer.run_auto_fix_sync(state)
    """

    MAX_FIX_RETRIES = 3

    def __init__(self, settings: "Settings"):
        """
        Initialize AutoFixer with settings.

        Args:
            settings: Application settings containing feature flags
        """
        self.settings = settings
        self._reviewer_agent = None
        self._project_engineer_agent = None
        self._dev_agent = None

    def should_run_for_task(self, state: Dict[str, Any]) -> bool:
        """
        Determine if auto-fix should run for this task.

        Uses canary rollout logic based on:
        1. ENABLE_PROJECT_ENGINEER_FIXER flag (must be true)
        2. PROJECT_ENGINEER_FIXER_PERCENT (0-100, deterministic hash routing)

        Note: Recommended to enable in staging first with 5-10% canary,
        then gradually increase in production after validation.
        Requires ENABLE_PROJECT_ENGINEER_CODEGEN=true to actually execute fixes.

        Args:
            state: AgentState dict with trace_id, pr_number, etc.

        Returns:
            True if auto-fix should be attempted, False otherwise
        """
        trace_id = state.get("trace_id", "unknown")

        if not self.settings.enable_project_engineer_fixer:
            logger.debug(
                "[AutoFixer] Auto-fix disabled by ENABLE_PROJECT_ENGINEER_FIXER=false",
                extra={
                    "trace_id": trace_id,
                    "autofixer_enabled": False,
                    "autofixer_disabled_reason": "flag_disabled"
                }
            )
            return False

        percent = self.settings.project_engineer_fixer_percent
        if percent <= 0:
            logger.debug(
                "[AutoFixer] Auto-fix disabled by PROJECT_ENGINEER_FIXER_PERCENT=0",
                extra={
                    "trace_id": trace_id,
                    "autofixer_enabled": False,
                    "autofixer_disabled_reason": "percent_zero"
                }
            )
            return False

        if percent >= 100:
            logger.info(
                "[AutoFixer] Auto-fix enabled for all tasks (percent=100)",
                extra={
                    "trace_id": trace_id,
                    "autofixer_enabled": True,
                    "autofixer_disabled_reason": None
                }
            )
            return True

        key = str(state.get("pr_number") or state.get("trace_id") or "unknown")
        task_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        bucket = task_hash % 100

        should_run = bucket < percent
        logger.info(
            "[AutoFixer] Canary check: key=%s, bucket=%d, percent=%d, should_run=%s",
            key, bucket, percent, should_run,
            extra={
                "trace_id": trace_id,
                "autofixer_enabled": should_run,
                "autofixer_disabled_reason": None if should_run else "canary_bucket_excluded",
                "canary_key": key,
                "canary_bucket": bucket,
                "canary_percent": percent
            }
        )
        return should_run

    def run_auto_fix_sync(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run auto-fix synchronously.

        This is a wrapper for async run_auto_fix that can be called from
        synchronous code (like fixer_node).

        Args:
            state: AgentState dict

        Returns:
            Updated AgentState dict
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.run_auto_fix(state))
                    return future.result()
            else:
                return loop.run_until_complete(self.run_auto_fix(state))
        except RuntimeError:
            return asyncio.run(self.run_auto_fix(state))

    async def run_auto_fix(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run auto-fix attempt using ReviewerAgent and ProjectEngineerAgent.

        Workflow:
        1. Get changed files from PR or workspace
        2. Run ReviewerAgent on changed files
        3. If review passes, skip auto-fix
        4. Build fix task description from review results
        5. Call ProjectEngineerAgent to generate fix
        6. Update state with results

        Args:
            state: AgentState dict with trace_id, pr_number, repo, etc.

        Returns:
            Updated AgentState dict
        """
        trace_id = state.get("trace_id", "unknown")
        pr_number = state.get("pr_number")
        repo = state.get("repo") or getattr(self.settings, "github_repo", None) or "RC918/morningai"

        logger.info(
            "[AutoFixer] Starting auto-fix attempt",
            extra={
                "operation": "auto_fix",
                "trace_id": trace_id,
                "pr_number": pr_number
            }
        )

        try:
            changed_files = await self._get_changed_files(state)

            if not changed_files:
                logger.warning(
                    "[AutoFixer] No changed files found, skipping auto-fix",
                    extra={"trace_id": trace_id}
                )
                state["error"] = "No changed files found for auto-fix"
                return state

            logger.info(
                "[AutoFixer] Found %d changed files: %s",
                len(changed_files), changed_files[:5],
                extra={"trace_id": trace_id}
            )

            review_result = await self._run_reviewer(changed_files, state)

            if review_result is None:
                logger.warning(
                    "[AutoFixer] ReviewerAgent not available, skipping auto-fix",
                    extra={"trace_id": trace_id}
                )
                state["error"] = "ReviewerAgent not available"
                return state

            if review_result.passed:
                logger.info(
                    "[AutoFixer] Review passed, no fixes needed",
                    extra={"trace_id": trace_id}
                )
                state["error"] = None
                return state

            fix_description = self._build_fix_task_description(
                review_result, pr_number, changed_files
            )

            logger.info(
                "[AutoFixer] Generated fix task description: %s",
                fix_description[:200],
                extra={"trace_id": trace_id}
            )

            fix_result = await self._run_project_engineer(fix_description, repo, state)

            if fix_result.get("success"):
                logger.info(
                    "[AutoFixer] Auto-fix succeeded",
                    extra={
                        "trace_id": trace_id,
                        "pr_url": fix_result.get("pr_url")
                    }
                )
                state["error"] = None
                if fix_result.get("pr_number"):
                    state["pr_number"] = fix_result["pr_number"]
                if fix_result.get("pr_url"):
                    state["pr_url"] = fix_result["pr_url"]
            else:
                logger.warning(
                    "[AutoFixer] Auto-fix failed: %s",
                    fix_result.get("error"),
                    extra={"trace_id": trace_id}
                )
                state["error"] = fix_result.get("error", "Auto-fix failed")

        except Exception as e:
            logger.error(
                "[AutoFixer] Auto-fix failed with exception: %s",
                str(e),
                extra={"trace_id": trace_id},
                exc_info=True
            )
            state["error"] = f"Auto-fix exception: {str(e)}"

        return state

    async def _get_changed_files(self, state: Dict[str, Any]) -> List[str]:
        """
        Get list of changed files from PR or workspace.

        Args:
            state: AgentState dict

        Returns:
            List of file paths
        """
        pr_number = state.get("pr_number")
        repo = state.get("repo") or getattr(self.settings, "github_repo", None) or "RC918/morningai"

        if pr_number:
            try:
                from tools.github_api import get_repo, get_pr_files
                gh_repo = get_repo(repo)
                files = get_pr_files(gh_repo, pr_number)
                return [f.filename for f in files] if files else []
            except ImportError:
                logger.warning("[AutoFixer] github_api not available, using git diff")
            except Exception as e:
                logger.warning("[AutoFixer] Failed to get PR files: %s", e)

        try:
            import subprocess
            result = subprocess.run(
                ["git", "diff", "--name-only", "origin/main", "HEAD"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split("\n") if f]
        except Exception as e:
            logger.warning("[AutoFixer] Failed to get git diff: %s", e)

        return []

    async def _run_reviewer(
        self, changed_files: List[str], state: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Run ReviewerAgent on changed files.

        Args:
            changed_files: List of file paths to review
            state: AgentState dict

        Returns:
            ReviewResult or None if ReviewerAgent not available
        """
        try:
            from agents.reviewer_agent.reviewer_agent import ReviewerAgent

            if self._reviewer_agent is None:
                workspace_path = getattr(self.settings, "workspace_path", None) or "."
                self._reviewer_agent = ReviewerAgent(repo_root=workspace_path)

            python_files = [f for f in changed_files if f.endswith(".py")]
            js_files = [f for f in changed_files if f.endswith((".js", ".jsx", ".ts", ".tsx"))]
            reviewable_files = python_files + js_files

            if not reviewable_files:
                logger.info("[AutoFixer] No reviewable files found")
                from agents.reviewer_agent.reviewer_agent import ReviewResult
                return ReviewResult(passed=True, comments=[], summary={})

            return self._reviewer_agent.review_files(reviewable_files)

        except ImportError as e:
            logger.warning("[AutoFixer] Failed to import ReviewerAgent: %s", e)
            return None
        except Exception as e:
            logger.error("[AutoFixer] ReviewerAgent failed: %s", e, exc_info=True)
            return None

    def _build_fix_task_description(
        self,
        review_result: Any,
        pr_number: Optional[int],
        changed_files: List[str]
    ) -> str:
        """
        Build a natural language task description for ProjectEngineerAgent.

        Args:
            review_result: ReviewResult from ReviewerAgent
            pr_number: PR number if available
            changed_files: List of changed files

        Returns:
            Task description string
        """
        parts = []

        if pr_number:
            parts.append(f"Fix CI failures for PR #{pr_number}.")
        else:
            parts.append("Fix code issues found by automated review.")

        summary = review_result.summary if hasattr(review_result, "summary") else {}
        error_count = summary.get("error", 0)
        warning_count = summary.get("warning", 0)
        lint_count = summary.get("lint", 0)
        security_count = summary.get("security", 0)

        if error_count or warning_count:
            parts.append(
                f"ReviewerAgent found: {error_count} errors, {warning_count} warnings."
            )

        if lint_count:
            parts.append(f"Lint issues: {lint_count}.")
        if security_count:
            parts.append(f"Security issues: {security_count}.")

        comments = review_result.comments if hasattr(review_result, "comments") else []
        error_comments = [c for c in comments if c.severity == "error"]

        if error_comments:
            parts.append("Critical issues to fix:")
            for i, comment in enumerate(error_comments[:5]):
                file_path = comment.file_path if hasattr(comment, "file_path") else "unknown"
                line_num = comment.line_number if hasattr(comment, "line_number") else "?"
                message = comment.message if hasattr(comment, "message") else ""
                suggestion = comment.suggestion if hasattr(comment, "suggestion") else ""

                issue_desc = f"- {file_path}:{line_num}: {message}"
                if suggestion:
                    issue_desc += f" (Suggestion: {suggestion})"
                parts.append(issue_desc)

        if changed_files:
            parts.append(f"Files to review: {', '.join(changed_files[:10])}")

        return " ".join(parts)

    async def _run_project_engineer(
        self,
        fix_description: str,
        repo: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run ProjectEngineerAgent to generate fix.

        This method uses ProjectEngineerAgent which enforces Phase 2 Step B
        safe_tasks whitelist. Only tasks classified as safe (e.g., fix_lint,
        documentation_update, test_generation) will have code generation enabled.

        Args:
            fix_description: Natural language task description
            repo: Repository name
            state: AgentState dict

        Returns:
            Dict with success, pr_number, pr_url, error
        """
        trace_id = state.get("trace_id", "unknown")

        try:
            if not self.settings.enable_project_engineer_codegen:
                logger.warning(
                    "[AutoFixer] ENABLE_PROJECT_ENGINEER_CODEGEN=false, "
                    "cannot execute fix. autofixer_safety_check=codegen_disabled trace_id=%s",
                    trace_id,
                    extra={
                        "trace_id": trace_id,
                        "autofixer_safety_check": "codegen_disabled"
                    }
                )
                return {
                    "success": False,
                    "error": "Code generation disabled (ENABLE_PROJECT_ENGINEER_CODEGEN=false)"
                }

            # Log safety check: ProjectEngineerAgent uses safe_tasks whitelist
            logger.info(
                "[AutoFixer] Running ProjectEngineerAgent with safe_tasks whitelist enforcement. "
                "autofixer_safety_check=whitelist_enforced trace_id=%s",
                trace_id,
                extra={
                    "trace_id": trace_id,
                    "autofixer_safety_check": "whitelist_enforced",
                    "safety_mechanism": "Phase 2 Step B safe_tasks whitelist"
                }
            )

            from project_engineer.agent import ProjectEngineerAgent

            if self._dev_agent is None:
                self._dev_agent = self._create_dev_agent()

            if self._project_engineer_agent is None:
                self._project_engineer_agent = ProjectEngineerAgent(
                    enable_code_generation=True,
                    dev_agent=self._dev_agent
                )

            results = await self._project_engineer_agent.run_task(fix_description, repo)

            success_results = [r for r in results if r.status == "success"]
            if success_results:
                result = success_results[0]
                return {
                    "success": True,
                    "pr_number": result.pr_number,
                    "pr_url": result.pr_url
                }

            failed_results = [r for r in results if r.status == "failed"]
            if failed_results:
                return {
                    "success": False,
                    "error": failed_results[0].error or "Fix task failed"
                }

            return {
                "success": False,
                "error": "No fix tasks completed"
            }

        except ImportError as e:
            logger.warning("[AutoFixer] Failed to import ProjectEngineerAgent: %s", e)
            return {"success": False, "error": f"Import error: {e}"}
        except Exception as e:
            logger.error(
                "[AutoFixer] ProjectEngineerAgent failed: %s", e, exc_info=True
            )
            return {"success": False, "error": str(e)}

    def _create_dev_agent(self) -> Any:
        """
        Create DevAgent instance for ProjectEngineerAgent.

        Returns:
            DevAgent instance
        """
        try:
            from agents.dev_agent.dev_agent_wrapper import DevAgent

            return DevAgent(
                openai_api_key=self.settings.openai_api_key
            )
        except ImportError as e:
            logger.error("[AutoFixer] Failed to import DevAgent: %s", e)
            raise
        except Exception as e:
            logger.error("[AutoFixer] Failed to create DevAgent: %s", e)
            raise
