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
import atexit
import asyncio
import concurrent.futures
import hashlib
import logging
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from core.flow.schema import CiFailureContext

if TYPE_CHECKING:
    from common.config.settings import Settings

logger = logging.getLogger(__name__)

# Module-level executor for async-to-sync bridging (reused across calls)
_autofixer_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
_autofixer_executor_lock = threading.Lock()


def _get_autofixer_executor() -> concurrent.futures.ThreadPoolExecutor:
    """
    Get or create a reusable ThreadPoolExecutor for async-to-sync bridging.

    This avoids the overhead of creating a new executor for each call to
    run_auto_fix_sync when called from within a running event loop.

    Uses double-checked locking pattern for thread safety.

    Returns:
        ThreadPoolExecutor instance (reused across calls)
    """
    global _autofixer_executor
    if _autofixer_executor is None:
        with _autofixer_executor_lock:
            # Double-check inside the lock to prevent re-creation
            if _autofixer_executor is None:
                _autofixer_executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="autofixer"
                )
    return _autofixer_executor


def _shutdown_autofixer_executor() -> None:
    """
    Shutdown the global ThreadPoolExecutor on application exit.

    This ensures worker threads are properly terminated and resources
    are released when the application exits.
    """
    global _autofixer_executor
    with _autofixer_executor_lock:
        if _autofixer_executor is not None:
            _autofixer_executor.shutdown(wait=True)
            _autofixer_executor = None


# Register shutdown handler to clean up executor on exit
atexit.register(_shutdown_autofixer_executor)


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

    def __init__(self, settings: "Settings" = None):
        """
        Initialize AutoFixer with settings.

        Args:
            settings: Application settings containing feature flags.
                     If None, falls back to global settings.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            logger.warning(
                "[AutoFixer] settings=None passed to __init__, falling back to global settings"
            )
            settings = global_settings
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

        Implementation uses two paths:
        1. Primary path: asyncio.run() when no event loop is running (most common)
        2. Fallback path: Background thread when called from within a running event loop

        The fallback path uses a reusable ThreadPoolExecutor to avoid overhead
        of creating a new executor for each call.

        Args:
            state: AgentState dict

        Returns:
            Updated AgentState dict
        """
        trace_id = state.get("trace_id", "unknown")

        try:
            # Check if we're inside a running event loop
            asyncio.get_running_loop()
            # If we get here, we're in a running loop - use background thread
            logger.info(
                "[AutoFixer] run_auto_fix_sync called from running event loop, "
                "offloading to background thread. autofixer_async_bridge=thread trace_id=%s",
                trace_id,
                extra={
                    "operation": "auto_fix",
                    "trace_id": trace_id,
                    "autofixer_async_bridge": "thread"
                }
            )
            executor = _get_autofixer_executor()
            future = executor.submit(asyncio.run, self.run_auto_fix(state))
            return future.result()
        except RuntimeError:
            # No running event loop - safe to use asyncio.run directly
            logger.debug(
                "[AutoFixer] run_auto_fix_sync using asyncio.run (no running loop). "
                "autofixer_async_bridge=direct trace_id=%s",
                trace_id,
                extra={
                    "operation": "auto_fix",
                    "trace_id": trace_id,
                    "autofixer_async_bridge": "direct"
                }
            )
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

            # Issue #3510: CI failure mode uses CI evidence instead of ReviewerAgent
            # When ci_failure_trigger=True, we have actual CI error context and should
            # use it directly instead of relying on ReviewerAgent judgment (which may
            # use different rules than CI lint checks)
            ci_failure_trigger = state.get("ci_failure_trigger", False)
            ci_failure_context_data = state.get("ci_failure_context")

            # Issue #3546: Track task_type_hint for CI failure mode
            task_type_hint: Optional[str] = None

            if ci_failure_trigger is True and ci_failure_context_data:
                # CI failure mode: use CI evidence directly
                # Reconstruct CiFailureContext from serialized dict (RQ JSON serialization)
                ci_failure_context = CiFailureContext.from_dict(ci_failure_context_data)
                fix_description = self._build_ci_fix_description(
                    ci_failure_context, pr_number, changed_files
                )

                # Issue #3546: Infer task_type from CI failure to bypass classifier misclassification
                task_type_hint = self._infer_task_type_from_ci_failure(ci_failure_context)

                logger.info(
                    "[AutoFixer] CI failure mode - using CI evidence for fix",
                    extra={
                        "trace_id": trace_id,
                        "ci_failure_trigger": True,
                        "failed_check_name": ci_failure_context.failed_check_name,
                        "conclusion": ci_failure_context.conclusion,
                        "task_type_hint": task_type_hint,
                    }
                )
            else:
                # Normal mode: use ReviewerAgent judgment
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
                extra={"trace_id": trace_id, "task_type_hint": task_type_hint}
            )

            fix_result = await self._run_project_engineer(
                fix_description, repo, state, task_type_hint=task_type_hint
            )

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
        trace_id = state.get("trace_id", "unknown")
        pr_number = state.get("pr_number")
        repo = state.get("repo") or getattr(self.settings, "github_repo", None) or "RC918/morningai"

        logger.info(
            "[AutoFixer] _get_changed_files starting pr_number=%s repo=%s trace_id=%s",
            pr_number, repo, trace_id,
            extra={
                "operation": "get_changed_files",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "repo": repo
            }
        )

        if pr_number:
            try:
                from tools.github_api import get_repo, get_pr_files
                logger.info(
                    "[AutoFixer] github_api import succeeded, fetching PR files trace_id=%s",
                    trace_id,
                    extra={"trace_id": trace_id, "method": "github_api"}
                )
                gh_repo = get_repo()  # get_repo() uses GITHUB_REPO from settings
                file_list = get_pr_files(gh_repo, pr_number, trace_id=trace_id)
                logger.info(
                    "[AutoFixer] github_api returned %d files trace_id=%s files=%s",
                    len(file_list), trace_id, file_list[:5],
                    extra={
                        "trace_id": trace_id,
                        "method": "github_api",
                        "file_count": len(file_list)
                    }
                )
                return file_list
            except ImportError as e:
                logger.warning(
                    "[AutoFixer] github_api ImportError: %s trace_id=%s - falling back to git diff",
                    str(e), trace_id,
                    extra={
                        "trace_id": trace_id,
                        "method": "github_api",
                        "error_type": "ImportError",
                        "error": str(e)
                    }
                )
            except Exception as e:
                logger.warning(
                    "[AutoFixer] github_api Exception: %s trace_id=%s - falling back to git diff",
                    str(e), trace_id,
                    extra={
                        "trace_id": trace_id,
                        "method": "github_api",
                        "error_type": type(e).__name__,
                        "error": str(e)
                    }
                )

        # Fallback to git diff
        logger.info(
            "[AutoFixer] Using git diff fallback trace_id=%s",
            trace_id,
            extra={"trace_id": trace_id, "method": "git_diff"}
        )
        try:
            import subprocess
            import os
            cwd = os.getcwd()
            logger.info(
                "[AutoFixer] git diff cwd=%s trace_id=%s",
                cwd, trace_id,
                extra={"trace_id": trace_id, "cwd": cwd}
            )

            # Try to get default branch dynamically, fallback to main
            base_ref = "origin/main"
            try:
                head_result = subprocess.run(
                    ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if head_result.returncode == 0 and head_result.stdout.strip():
                    # refs/remotes/origin/HEAD -> refs/remotes/origin/main
                    base_ref = head_result.stdout.strip().replace(
                        "refs/remotes/", ""
                    )
                    logger.info(
                        "[AutoFixer] Detected default branch: %s trace_id=%s",
                        base_ref, trace_id,
                        extra={"trace_id": trace_id, "base_ref": base_ref}
                    )
            except Exception as e:
                logger.debug(
                    "[AutoFixer] Could not detect default branch, using origin/main: %s",
                    str(e)
                )

            result = subprocess.run(
                ["git", "diff", "--name-only", base_ref, "HEAD"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Handle stderr with truncation indicator
            stderr_preview = ""
            stderr_truncated = False
            if result.stderr:
                if len(result.stderr) > 500:
                    stderr_preview = result.stderr[:500]
                    stderr_truncated = True
                else:
                    stderr_preview = result.stderr

            logger.info(
                "[AutoFixer] git diff returncode=%d stdout_len=%d trace_id=%s",
                result.returncode, len(result.stdout), trace_id,
                extra={
                    "trace_id": trace_id,
                    "method": "git_diff",
                    "base_ref": base_ref,
                    "returncode": result.returncode,
                    "stdout_len": len(result.stdout),
                    "stderr_preview": stderr_preview,
                    "stderr_truncated": stderr_truncated
                }
            )
            if stderr_preview:
                logger.warning(
                    "[AutoFixer] git diff stderr%s: %s",
                    " (truncated)" if stderr_truncated else "",
                    stderr_preview,
                    extra={"trace_id": trace_id, "stderr_truncated": stderr_truncated}
                )

            if result.returncode == 0:
                files = [f for f in result.stdout.strip().split("\n") if f]
                logger.info(
                    "[AutoFixer] git diff returned %d files trace_id=%s",
                    len(files), trace_id,
                    extra={
                        "trace_id": trace_id,
                        "method": "git_diff",
                        "file_count": len(files),
                        "files_preview": files[:5]
                    }
                )
                return files
        except Exception as e:
            logger.warning(
                "[AutoFixer] git diff failed: %s trace_id=%s",
                str(e), trace_id,
                extra={
                    "trace_id": trace_id,
                    "method": "git_diff",
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )

        logger.warning(
            "[AutoFixer] _get_changed_files returning empty list trace_id=%s",
            trace_id,
            extra={"trace_id": trace_id, "file_count": 0}
        )
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

    def _tokenize_text(self, text: str) -> set:
        """
        Tokenize text into a set of lowercase alphanumeric tokens.

        This avoids false positives from substring matching (e.g., 'black' in 'blacklist',
        'doc' in 'docker') by splitting on non-alphanumeric characters.

        Args:
            text: Text to tokenize

        Returns:
            Set of lowercase tokens
        """
        import re
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _contains_token(self, text: str, token: str) -> bool:
        """
        Check if text contains a specific token (word-aware matching).

        Args:
            text: Text to search in
            token: Token to search for (will be lowercased)

        Returns:
            True if token is found as a complete word
        """
        tokens = self._tokenize_text(text)
        return token.lower() in tokens

    def _contains_any_token(self, text: str, token_list: list) -> Optional[str]:
        """
        Check if text contains any of the specified tokens.

        Args:
            text: Text to search in
            token_list: List of tokens to search for

        Returns:
            First matched token, or None if no match
        """
        tokens = self._tokenize_text(text)
        for token in token_list:
            if token.lower() in tokens:
                return token
        return None

    def _contains_phrase(self, text: str, phrase: str) -> bool:
        """
        Check if text contains a specific phrase (for multi-word patterns).

        Phrases like "undefined name" are less risky for substring matching
        because they're more specific.

        Args:
            text: Text to search in
            phrase: Phrase to search for

        Returns:
            True if phrase is found
        """
        return phrase.lower() in text.lower()

    def _infer_task_type_from_ci_failure(
        self,
        ci_failure_context: "CiFailureContext"
    ) -> Optional[str]:
        """
        Infer safe task_type from CI failure context.

        Issue #3546: This method deterministically maps CI failure types to safe
        task types, bypassing the LLM classifier which may produce non-whitelisted
        types like 'backend_utils_bug_fix'.

        Uses token-based matching to avoid false positives from substring matching
        (e.g., 'black' in 'blacklist', 'doc' in 'docker', 'lint' in 'flint').

        Mapping rules:
        - ruff/flake8/eslint/pylint errors → fix_lint
        - typo-like patterns (undefined name, misspelling) → fix_typo
        - documentation-related failures → documentation_update

        Args:
            ci_failure_context: CiFailureContext with CI error details

        Returns:
            Safe task_type string if inferrable, None otherwise
        """
        failed_check_name = ci_failure_context.failed_check_name or ""
        error_summary = ci_failure_context.error_summary or ""

        # Lint tool patterns → fix_lint (token-based matching)
        lint_tokens = [
            "ruff", "flake8", "eslint", "pylint", "mypy", "black",
            "prettier", "stylelint", "lint", "linting"
        ]
        matched = self._contains_any_token(failed_check_name, lint_tokens)
        if not matched:
            matched = self._contains_any_token(error_summary, lint_tokens)
        if matched:
            logger.info(
                "[AutoFixer] Inferred task_type=fix_lint from CI failure "
                "(matched token: %s)",
                matched,
                extra={"ci_failure_task_type_inference": "fix_lint"}
            )
            return "fix_lint"

        # Typo-like error patterns → fix_typo
        # Use phrase matching for multi-word patterns, token matching for error codes
        typo_phrases = ["undefined name", "undeclared variable"]
        for phrase in typo_phrases:
            if self._contains_phrase(error_summary, phrase):
                logger.info(
                    "[AutoFixer] Inferred task_type=fix_typo from CI failure "
                    "(matched phrase: %s)",
                    phrase,
                    extra={"ci_failure_task_type_inference": "fix_typo"}
                )
                return "fix_typo"

        typo_tokens = ["typo", "misspell", "f821", "f841", "e999"]
        matched = self._contains_any_token(error_summary, typo_tokens)
        if matched:
            logger.info(
                "[AutoFixer] Inferred task_type=fix_typo from CI failure "
                "(matched token: %s)",
                matched,
                extra={"ci_failure_task_type_inference": "fix_typo"}
            )
            return "fix_typo"

        # Documentation-related failures → documentation_update (token-based matching)
        doc_tokens = ["readme", "documentation", "docstring"]
        matched = self._contains_any_token(failed_check_name, doc_tokens)
        if not matched:
            matched = self._contains_any_token(error_summary, doc_tokens)
        if matched:
            logger.info(
                "[AutoFixer] Inferred task_type=documentation_update from CI failure "
                "(matched token: %s)",
                matched,
                extra={"ci_failure_task_type_inference": "documentation_update"}
            )
            return "documentation_update"

        # No match - let classifier decide (may fail whitelist check)
        logger.warning(
            "[AutoFixer] Could not infer task_type from CI failure context. "
            "Classifier will be used (may produce non-whitelisted type). "
            "failed_check_name=%s",
            ci_failure_context.failed_check_name,
            extra={"ci_failure_task_type_inference": "none"}
        )
        return None

    def _build_ci_fix_description(
        self,
        ci_failure_context: "CiFailureContext",
        pr_number: Optional[int],
        changed_files: List[str]
    ) -> str:
        """
        Build a natural language task description from CI failure context.

        Issue #3510: This method uses actual CI error evidence instead of
        ReviewerAgent judgment, enabling AutoFixer to address the exact
        errors that caused CI to fail.

        Args:
            ci_failure_context: CiFailureContext with CI error details
            pr_number: PR number if available
            changed_files: List of changed files

        Returns:
            Task description string
        """
        parts = []

        if pr_number:
            parts.append(f"Fix CI failures for PR #{pr_number}.")
        else:
            parts.append("Fix CI failures found in automated checks.")

        # Extract CI failure details using direct attribute access
        failed_check_name = ci_failure_context.failed_check_name
        conclusion = ci_failure_context.conclusion
        error_summary = ci_failure_context.error_summary
        logs_url = ci_failure_context.logs_url

        parts.append(f"CI check '{failed_check_name}' failed with conclusion: {conclusion}.")

        if error_summary:
            parts.append(f"Error details: {error_summary}")
        elif logs_url:
            parts.append(f"See CI logs for details: {logs_url}")
        else:
            parts.append("CI check failed - review the changed files for potential issues.")

        if changed_files:
            parts.append(f"Files to review: {', '.join(changed_files[:10])}")

        return " ".join(parts)

    async def _run_project_engineer(
        self,
        fix_description: str,
        repo: str,
        state: Dict[str, Any],
        task_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run ProjectEngineerAgent to generate fix.

        This method uses ProjectEngineerAgent which enforces Phase 2 Step B
        safe_tasks whitelist. Only tasks classified as safe (e.g., fix_lint,
        documentation_update, test_generation) will have code generation enabled.

        Issue #3546: Added task_type_hint parameter to bypass classifier
        misclassification for CI failure auto-fix.

        Args:
            fix_description: Natural language task description
            repo: Repository name
            state: AgentState dict
            task_type_hint: Optional safe task_type to use instead of classifier
                           (Issue #3546: deterministic CI failure task_type)

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
                "autofixer_safety_check=whitelist_enforced trace_id=%s task_type_hint=%s",
                trace_id, task_type_hint,
                extra={
                    "trace_id": trace_id,
                    "autofixer_safety_check": "whitelist_enforced",
                    "safety_mechanism": "Phase 2 Step B safe_tasks whitelist",
                    "task_type_hint": task_type_hint
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

            # Issue #3546: Pass task_type_hint to bypass classifier misclassification
            results = await self._project_engineer_agent.run_task(
                fix_description, repo, task_type_hint=task_type_hint
            )

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
