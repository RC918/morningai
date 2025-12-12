"""
Review Follow-up Mode - Orchestrator Support for AI Review Comments

This module provides the Review Follow-up Mode functionality that enables
the orchestrator to process and respond to AI reviewer comments by:
1. Understanding comment content and context
2. Pulling PR context (diff, files, comments)
3. Executing fixes based on the comment
4. Updating existing PR or opening new PR

Issue: #2211 - Orchestrator Review Follow-up Mode
Milestone: Phase 7 - 生態系閉環 (AI Review Closed Loop)

Flow:
    CommentTriageResult → ReviewFollowUpTask → ReviewFollowUpService → Orchestrator
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .comment_triage import CommentTriageResult, CommentCategory, RiskLevel

logger = logging.getLogger(__name__)

SENSITIVE_FILE_PATTERNS = (
    "auth", "security", "credential", "password", "secret",
    "config", "settings", "env", "migration", "schema",
)


def determine_hitl_requirement(
    triage_result: Optional[Dict[str, Any]],
    file_path: str = "",
    action: Optional[str] = None,
) -> bool:
    """
    Unified HITL (Human-in-the-Loop) approval decision logic.

    Issue #2258: Single source of truth for HITL approval decisions.
    This function consolidates the decision logic previously duplicated in:
    - ReviewFollowUpService._requires_approval()
    - langgraph_orchestrator._determine_hitl_requirement()

    Args:
        triage_result: Result from CommentTriageAgent (dict format)
        file_path: File path being modified
        action: Action type (e.g., "escalate", "auto_fix")

    Returns:
        True if HITL approval is required
    """
    if triage_result is None:
        return True

    if triage_result.get("risk_level") == "high":
        return True

    if triage_result.get("category") == "security":
        return True

    if action == "escalate":
        return True

    if file_path:
        file_path_lower = file_path.lower()
        for pattern in SENSITIVE_FILE_PATTERNS:
            if pattern in file_path_lower:
                return True

    if (triage_result.get("should_auto_fix", False) and
            triage_result.get("confidence", 0) >= 0.8):
        return False

    return True


class ReviewFollowUpStatus(Enum):
    """Status of a review follow-up task"""
    PENDING = "pending"
    FETCHING_CONTEXT = "fetching_context"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReviewFollowUpAction(Enum):
    """Actions that can be taken for a review follow-up"""
    AUTO_FIX = "auto_fix"
    MANUAL_REVIEW = "manual_review"
    SKIP = "skip"
    ESCALATE = "escalate"


@dataclass
class PRContext:
    """
    Context information about a Pull Request.

    This contains all the information needed to understand and respond
    to a review comment on a PR.
    """
    pr_number: int
    repo: str
    branch: str
    base_branch: str
    title: str
    description: str
    author: str
    diff: str
    files_changed: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    reviews: List[Dict[str, Any]] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    ci_status: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "pr_number": self.pr_number,
            "repo": self.repo,
            "branch": self.branch,
            "base_branch": self.base_branch,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "diff_length": len(self.diff),
            "files_changed": self.files_changed,
            "comments_count": len(self.comments),
            "reviews_count": len(self.reviews),
            "labels": self.labels,
            "ci_status": self.ci_status,
            "metadata": self.metadata,
        }


@dataclass
class ReviewFollowUpTask:
    """
    A task for following up on an AI reviewer comment.

    This is the schema defined in Issue #2211 for review_follow_up tasks.

    Schema:
        {
            "task_type": "review_follow_up",
            "original_pr_number": 123,
            "repo": "RC918/morningai",
            "branch": "feature/xyz",
            "comment_url": "https://github.com/.../comments/456",
            "comment_body": "Consider using...",
            "file_path": "src/auth.py",
            "line_number": 42,
            "triage_result": {...}
        }
    """
    task_id: str
    task_type: str = "review_follow_up"
    original_pr_number: int = 0
    repo: str = ""
    branch: str = ""
    comment_url: str = ""
    comment_body: str = ""
    file_path: str = ""
    line_number: int = 0
    triage_result: Optional[CommentTriageResult] = None
    pr_context: Optional[PRContext] = None
    status: ReviewFollowUpStatus = ReviewFollowUpStatus.PENDING
    action: ReviewFollowUpAction = ReviewFollowUpAction.MANUAL_REVIEW
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "original_pr_number": self.original_pr_number,
            "repo": self.repo,
            "branch": self.branch,
            "comment_url": self.comment_url,
            "comment_body": self.comment_body[:200] if self.comment_body else "",
            "file_path": self.file_path,
            "line_number": self.line_number,
            "triage_result": self.triage_result.to_dict() if self.triage_result else None,
            "pr_context": self.pr_context.to_dict() if self.pr_context else None,
            "status": self.status.value,
            "action": self.action.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_triage_result(
        cls,
        task_id: str,
        triage_result: CommentTriageResult,
        pr_number: int,
        repo: str,
        branch: str,
        comment_url: str,
        comment_body: str,
        file_path: str = "",
        line_number: int = 0,
    ) -> "ReviewFollowUpTask":
        """
        Create a ReviewFollowUpTask from a CommentTriageResult.

        Args:
            task_id: Unique task identifier
            triage_result: Result from CommentTriageAgent
            pr_number: Original PR number
            repo: Repository in owner/repo format
            branch: Branch name
            comment_url: URL to the comment
            comment_body: Body of the comment
            file_path: File path mentioned in comment
            line_number: Line number mentioned in comment

        Returns:
            ReviewFollowUpTask ready for processing
        """
        # Determine action based on triage result
        action = cls._determine_action(triage_result)

        return cls(
            task_id=task_id,
            original_pr_number=pr_number,
            repo=repo,
            branch=branch,
            comment_url=comment_url,
            comment_body=comment_body,
            file_path=file_path or (triage_result.files_affected[0] if triage_result.files_affected else ""),
            line_number=line_number,
            triage_result=triage_result,
            action=action,
        )

    @staticmethod
    def _determine_action(triage_result: CommentTriageResult) -> ReviewFollowUpAction:
        """
        Determine the appropriate action based on triage result.

        Args:
            triage_result: Result from CommentTriageAgent

        Returns:
            ReviewFollowUpAction to take
        """
        # Auto-fix if triage recommends it
        if triage_result.should_auto_fix:
            return ReviewFollowUpAction.AUTO_FIX

        # Escalate high-risk security issues
        if (triage_result.category == CommentCategory.SECURITY and
                triage_result.risk_level == RiskLevel.HIGH):
            return ReviewFollowUpAction.ESCALATE

        # Skip unknown or very low confidence
        if (triage_result.category == CommentCategory.UNKNOWN or
                triage_result.confidence < 0.3):
            return ReviewFollowUpAction.SKIP

        # Default to manual review
        return ReviewFollowUpAction.MANUAL_REVIEW


class ReviewFollowUpService:
    """
    Service for managing review follow-up tasks.

    This service:
    1. Creates ReviewFollowUpTask from triage results
    2. Fetches PR context (diff, files, comments)
    3. Determines appropriate action
    4. Coordinates with orchestrator for execution
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the ReviewFollowUpService.

        Args:
            github_token: GitHub API token for fetching PR context
        """
        self._github_token = github_token
        self._tasks: Dict[str, ReviewFollowUpTask] = {}

        logger.info("[ReviewFollowUpService] Initialized")

    def create_task(
        self,
        triage_result: CommentTriageResult,
        pr_number: int,
        repo: str,
        branch: str,
        comment_url: str,
        comment_body: str,
        file_path: str = "",
        line_number: int = 0,
    ) -> ReviewFollowUpTask:
        """
        Create a new review follow-up task.

        Args:
            triage_result: Result from CommentTriageAgent
            pr_number: Original PR number
            repo: Repository in owner/repo format
            branch: Branch name
            comment_url: URL to the comment
            comment_body: Body of the comment
            file_path: File path mentioned in comment
            line_number: Line number mentioned in comment

        Returns:
            Created ReviewFollowUpTask
        """
        import uuid
        task_id = f"review-followup-{uuid.uuid4().hex[:8]}"

        task = ReviewFollowUpTask.from_triage_result(
            task_id=task_id,
            triage_result=triage_result,
            pr_number=pr_number,
            repo=repo,
            branch=branch,
            comment_url=comment_url,
            comment_body=comment_body,
            file_path=file_path,
            line_number=line_number,
        )

        self._tasks[task_id] = task

        logger.info(
            "[ReviewFollowUpService] Created task: id=%s, pr=%d, action=%s",
            task_id,
            pr_number,
            task.action.value,
        )

        return task

    def get_task(self, task_id: str) -> Optional[ReviewFollowUpTask]:
        """Get a task by ID"""
        return self._tasks.get(task_id)

    def fetch_pr_context(self, task: ReviewFollowUpTask) -> Optional[PRContext]:
        """
        Fetch PR context for a review follow-up task.

        This pulls the diff, files, and comments from the PR to provide
        context for the orchestrator to understand and fix the issue.

        Args:
            task: ReviewFollowUpTask to fetch context for

        Returns:
            PRContext with PR information, or None if fetch fails
        """
        task.status = ReviewFollowUpStatus.FETCHING_CONTEXT
        task.updated_at = datetime.now()

        try:
            # Import GitHub API tools
            from tools.github_api import get_repo

            logger.info(
                "[ReviewFollowUpService] Fetching PR context: repo=%s, pr=%d",
                task.repo,
                task.original_pr_number,
            )

            # Get repository
            repo = get_repo(task.repo)

            # Get PR details
            pr = repo.get_pull(task.original_pr_number)

            # Get diff
            diff = self._fetch_pr_diff(task.repo, task.original_pr_number)

            # Get changed files
            files_changed = [f.filename for f in pr.get_files()]

            # Get comments
            comments = self._fetch_pr_comments(pr)

            # Get reviews
            reviews = self._fetch_pr_reviews(pr)

            # Build PR context
            pr_context = PRContext(
                pr_number=task.original_pr_number,
                repo=task.repo,
                branch=pr.head.ref,
                base_branch=pr.base.ref,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                diff=diff,
                files_changed=files_changed,
                comments=comments,
                reviews=reviews,
                labels=[label.name for label in pr.labels],
                ci_status=self._get_ci_status(pr),
                metadata={
                    "mergeable": pr.mergeable,
                    "merged": pr.merged,
                    "state": pr.state,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                },
            )

            task.pr_context = pr_context
            task.updated_at = datetime.now()

            logger.info(
                "[ReviewFollowUpService] Fetched PR context: files=%d, comments=%d",
                len(files_changed),
                len(comments),
            )

            return pr_context

        except ImportError:
            logger.warning(
                "[ReviewFollowUpService] GitHub API tools not available, using stub context"
            )
            # Return stub context for testing
            return self._create_stub_context(task)

        except Exception as e:
            logger.error(
                "[ReviewFollowUpService] Failed to fetch PR context: %s",
                e,
                exc_info=True,
            )
            task.status = ReviewFollowUpStatus.FAILED
            task.error = f"Failed to fetch PR context: {e}"
            task.updated_at = datetime.now()
            return None

    def _fetch_pr_diff(self, repo: str, pr_number: int) -> str:
        """Fetch the diff for a PR"""
        try:
            from tools.github_api import get_pr_diff
            return get_pr_diff(repo, pr_number)
        except Exception as e:
            logger.warning("[ReviewFollowUpService] Failed to fetch diff: %s", e)
            return ""

    def _fetch_pr_comments(self, pr: Any) -> List[Dict[str, Any]]:
        """Fetch comments from a PR"""
        comments = []
        try:
            # Get issue comments
            for comment in pr.get_issue_comments():
                comments.append({
                    "id": comment.id,
                    "body": comment.body,
                    "user": comment.user.login,
                    "created_at": comment.created_at.isoformat(),
                    "type": "issue_comment",
                })

            # Get review comments
            for comment in pr.get_review_comments():
                comments.append({
                    "id": comment.id,
                    "body": comment.body,
                    "user": comment.user.login,
                    "path": comment.path,
                    "line": comment.line,
                    "created_at": comment.created_at.isoformat(),
                    "type": "review_comment",
                })
        except Exception as e:
            logger.warning("[ReviewFollowUpService] Failed to fetch comments: %s", e)

        return comments

    def _fetch_pr_reviews(self, pr: Any) -> List[Dict[str, Any]]:
        """Fetch reviews from a PR"""
        reviews = []
        try:
            for review in pr.get_reviews():
                reviews.append({
                    "id": review.id,
                    "body": review.body,
                    "user": review.user.login,
                    "state": review.state,
                    "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None,
                })
        except Exception as e:
            logger.warning("[ReviewFollowUpService] Failed to fetch reviews: %s", e)

        return reviews

    def _get_ci_status(self, pr: Any) -> str:
        """Get CI status for a PR"""
        try:
            # Get combined status
            commit = pr.head.repo.get_commit(pr.head.sha)
            status = commit.get_combined_status()
            return status.state
        except Exception as e:
            logger.warning("[ReviewFollowUpService] Failed to get CI status: %s", e)
            return "unknown"

    def _create_stub_context(self, task: ReviewFollowUpTask) -> PRContext:
        """Create a stub PR context for testing"""
        return PRContext(
            pr_number=task.original_pr_number,
            repo=task.repo,
            branch=task.branch,
            base_branch="main",
            title=f"PR #{task.original_pr_number}",
            description="Stub PR context for testing",
            author="unknown",
            diff="",
            files_changed=[task.file_path] if task.file_path else [],
            comments=[],
            reviews=[],
            labels=[],
            ci_status="unknown",
            metadata={"stub": True},
        )

    def prepare_for_orchestrator(
        self, task: ReviewFollowUpTask
    ) -> Dict[str, Any]:
        """
        Prepare a review follow-up task for the orchestrator.

        This converts the task into the format expected by the
        LangGraph orchestrator's initial state.

        Args:
            task: ReviewFollowUpTask to prepare

        Returns:
            Dictionary with orchestrator state fields
        """
        # Build goal text from comment
        goal_text = self._build_goal_text(task)

        # Determine if approval is required
        requires_approval = self._requires_approval(task)

        return {
            "task_type": "review_follow_up",
            "goal": goal_text,
            "repo": task.repo,
            "branch": task.branch,
            "original_pr_number": task.original_pr_number,
            "comment_url": task.comment_url,
            "comment_body": task.comment_body,
            "file_path": task.file_path,
            "line_number": task.line_number,
            "triage_result": task.triage_result.to_dict() if task.triage_result else {},
            "pr_context": task.pr_context.to_dict() if task.pr_context else {},
            "requires_approval": requires_approval,
            "review_follow_up_action": task.action.value,
        }

    def _build_goal_text(self, task: ReviewFollowUpTask) -> str:
        """Build goal text for the orchestrator"""
        parts = []

        # Add context about the review comment
        if task.triage_result:
            category = task.triage_result.category.value
            parts.append(f"[Review Follow-up: {category}]")

        # Add file context
        if task.file_path:
            if task.line_number:
                parts.append(f"In {task.file_path}:{task.line_number}")
            else:
                parts.append(f"In {task.file_path}")

        # Add the comment body (truncated)
        comment = task.comment_body[:500] if task.comment_body else "No comment body"
        parts.append(f"Address review comment: {comment}")

        # Add PR context
        parts.append(f"(PR #{task.original_pr_number} in {task.repo})")

        return " ".join(parts)

    def _requires_approval(self, task: ReviewFollowUpTask) -> bool:
        """
        Determine if task requires human approval.

        Issue #2258: Delegates to unified determine_hitl_requirement() function.
        """
        triage_dict = task.triage_result.to_dict() if task.triage_result else None
        return determine_hitl_requirement(
            triage_result=triage_dict,
            file_path=task.file_path,
            action=task.action.value if task.action else None,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        status_counts: Dict[str, int] = {}
        action_counts: Dict[str, int] = {}

        for task in self._tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            action = task.action.value
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "status_counts": status_counts,
            "action_counts": action_counts,
        }
