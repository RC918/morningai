"""
Deterministic Signals Ingestion Layer for MorningAI Reviewer

Issue #3222: Deterministic Signals Ingestion - CI/Linters integration

This module provides a pluggable layer for ingesting deterministic signals
from CI systems, linters, and other static analysis tools. These signals
enhance the Reviewer Agent's reliability by providing factual, non-LLM-based
information about code quality issues.

Blueprint Alignment:
- Deterministic: Integrates factual static analysis results, not LLM judgments
- Modular: Pluggable SignalSource protocol supports multiple signal sources

Signal Sources:
1. GitHub Actions Annotations: Workflow run annotations from CI jobs
2. Check Run Output: Annotations from GitHub check runs (CodeQL, ESLint, etc.)
3. PR Review Comments: Comments from other bots (future extension)

Usage:
    from tools.signal_ingestion import fetch_signals, Signal

    # Fetch all signals for a PR
    signals = fetch_signals(repo, pr_number, head_sha, trace_id)

    # Filter by severity
    errors = [s for s in signals if s.severity == "error"]

    # Use in review context
    for signal in signals:
        print(f"[{signal.source}] {signal.file_path}:{signal.line} - {signal.message}")
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Protocol, runtime_checkable

from github import GithubException
from github.Repository import Repository

logger = logging.getLogger(__name__)


class SignalSeverity(str, Enum):
    """Severity levels for deterministic signals"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Signal:
    """
    A deterministic signal from CI/linter/static analysis.

    Attributes:
        source: Origin of the signal (e.g., "github_actions", "eslint", "codeql")
        severity: Signal severity level (error, warning, info)
        file_path: File path where the issue was detected
        message: Human-readable description of the issue
        line: Line number (optional, may be None for file-level issues)
        end_line: End line number for multi-line annotations (optional)
        column: Column number (optional)
        end_column: End column number (optional)
        rule_id: Rule/check identifier (optional, e.g., "no-unused-vars")
        title: Short title for the annotation (optional)
        raw_annotation: Original annotation data for debugging (optional)
    """
    source: str
    severity: SignalSeverity
    file_path: str
    message: str
    line: Optional[int] = None
    end_line: Optional[int] = None
    column: Optional[int] = None
    end_column: Optional[int] = None
    rule_id: Optional[str] = None
    title: Optional[str] = None
    raw_annotation: Optional[dict] = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict:
        """Convert signal to dictionary for serialization"""
        return {
            "source": self.source,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "message": self.message,
            "line": self.line,
            "end_line": self.end_line,
            "column": self.column,
            "end_column": self.end_column,
            "rule_id": self.rule_id,
            "title": self.title,
        }

    def to_review_comment(self) -> dict:
        """
        Convert signal to review comment format for Reviewer integration.

        Uses canonical schema fields (start_line/end_line) instead of legacy 'line'
        to ensure compatibility with downstream post_pr_review function.

        Returns:
            dict with keys: severity, message, file, start_line, end_line, rule_id, deterministic
        """
        severity_map = {
            SignalSeverity.ERROR: "high",
            SignalSeverity.WARNING: "medium",
            SignalSeverity.INFO: "low",
        }
        comment: dict = {
            "severity": severity_map.get(self.severity, "medium"),
            "message": f"[{self.source}] {self.message}",
            "file": self.file_path,
            "rule_id": self.rule_id,
            "deterministic": True,  # Mark as deterministic signal
        }

        # Use canonical start_line/end_line format (not legacy 'line')
        # This ensures compatibility with review_comment_schema and post_pr_review
        if self.line is not None:
            comment["start_line"] = self.line
            comment["end_line"] = self.end_line if self.end_line is not None else self.line
        elif self.end_line is not None:
            comment["start_line"] = self.end_line
            comment["end_line"] = self.end_line

        return comment


@runtime_checkable
class SignalSource(Protocol):
    """
    Protocol for deterministic signal sources.

    Implementations must provide a fetch_signals method that retrieves
    signals for a given PR/commit.
    """

    def fetch_signals(
        self,
        repo: Repository,
        pr_number: int,
        head_sha: str,
        trace_id: str = "unknown",
    ) -> List[Signal]:
        """
        Fetch signals for a PR.

        Args:
            repo: GitHub repository object
            pr_number: Pull request number
            head_sha: Head commit SHA
            trace_id: Trace ID for logging

        Returns:
            List of Signal objects
        """
        ...


class CheckRunSignalSource:
    """
    Signal source for GitHub Check Run annotations.

    This source fetches annotations from GitHub check runs, which include
    results from tools like CodeQL, ESLint (via actions), and other
    GitHub-integrated static analysis tools.
    """

    def __init__(self, max_annotations_per_run: int = 50):
        """
        Initialize CheckRunSignalSource.

        Args:
            max_annotations_per_run: Maximum annotations to fetch per check run
                                     (GitHub API returns max 50 per page)
        """
        self.max_annotations_per_run = max_annotations_per_run

    def fetch_signals(
        self,
        repo: Repository,
        pr_number: int,
        head_sha: str,
        trace_id: str = "unknown",
    ) -> List[Signal]:
        """
        Fetch signals from GitHub check run annotations.

        Args:
            repo: GitHub repository object
            pr_number: Pull request number
            head_sha: Head commit SHA
            trace_id: Trace ID for logging

        Returns:
            List of Signal objects from check run annotations
        """
        signals: List[Signal] = []

        try:
            commit = repo.get_commit(head_sha)
            check_runs = commit.get_check_runs()

            check_run_count = 0
            for check_run in check_runs:
                check_run_count += 1
                check_name = check_run.name or "unknown"

                # Get annotations from check run using PyGithub's get_annotations()
                # Note: output.annotations doesn't exist in PyGithub; we must use
                # check_run.get_annotations() which fetches from the annotations_url
                output = check_run.output
                annotations_count = getattr(output, 'annotations_count', 0) if output else 0

                if not annotations_count:
                    continue

                try:
                    annotations = check_run.get_annotations()
                except Exception as e:
                    logger.debug(
                        f"[SignalIngestion] Failed to fetch annotations for {check_name}: {e}",
                        extra={
                            "operation": "check_run_signals",
                            "trace_id": trace_id,
                            "check_name": check_name,
                            "error": str(e),
                        }
                    )
                    continue

                annotation_count = 0
                for annotation in annotations:
                    if annotation_count >= self.max_annotations_per_run:
                        logger.info(
                            f"[SignalIngestion] Reached max annotations limit for {check_name}",
                            extra={
                                "operation": "check_run_signals",
                                "trace_id": trace_id,
                                "check_name": check_name,
                                "max_annotations": self.max_annotations_per_run,
                            }
                        )
                        break

                    signal = self._annotation_to_signal(annotation, check_name)
                    if signal:
                        signals.append(signal)
                        annotation_count += 1

            logger.info(
                f"[SignalIngestion] Fetched {len(signals)} signals from {check_run_count} check runs",
                extra={
                    "operation": "check_run_signals",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "head_sha": head_sha[:12] if head_sha else None,
                    "check_run_count": check_run_count,
                    "signal_count": len(signals),
                }
            )

        except GithubException as e:
            logger.warning(
                f"[SignalIngestion] GitHub API error fetching check runs: {e}",
                extra={
                    "operation": "check_run_signals",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "error": str(e),
                    "status": getattr(e, 'status', None),
                }
            )
        except Exception as e:
            logger.warning(
                f"[SignalIngestion] Error fetching check run signals: {e}",
                extra={
                    "operation": "check_run_signals",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "error": str(e),
                }
            )

        return signals

    def _annotation_to_signal(self, annotation, check_name: str) -> Optional[Signal]:
        """Convert a GitHub check run annotation to a Signal"""
        try:
            # Map GitHub annotation levels to SignalSeverity
            level = getattr(annotation, 'annotation_level', 'warning')
            severity_map = {
                'failure': SignalSeverity.ERROR,
                'error': SignalSeverity.ERROR,
                'warning': SignalSeverity.WARNING,
                'notice': SignalSeverity.INFO,
            }
            severity = severity_map.get(level, SignalSeverity.WARNING)

            file_path = getattr(annotation, 'path', '') or ''
            message = getattr(annotation, 'message', '') or ''
            title = getattr(annotation, 'title', None)

            if not file_path or not message:
                return None

            return Signal(
                source=f"check_run:{check_name}",
                severity=severity,
                file_path=file_path,
                message=message,
                line=getattr(annotation, 'start_line', None),
                end_line=getattr(annotation, 'end_line', None),
                column=getattr(annotation, 'start_column', None),
                end_column=getattr(annotation, 'end_column', None),
                title=title,
                raw_annotation={
                    'path': file_path,
                    'message': message,
                    'annotation_level': level,
                    'title': title,
                },
            )
        except Exception as e:
            logger.debug(f"[SignalIngestion] Failed to parse annotation: {e}")
            return None


class WorkflowAnnotationSignalSource:
    """
    Signal source for GitHub Actions workflow annotations.

    This source fetches annotations from workflow run jobs, which include
    annotations created by actions like actions/github-script or
    workflow commands (::error::, ::warning::, etc.).
    """

    def __init__(
        self,
        workflow_patterns: Optional[List[str]] = None,
        max_annotations_per_job: int = 50,
    ):
        """
        Initialize WorkflowAnnotationSignalSource.

        Args:
            workflow_patterns: List of workflow name patterns to match
                              (default: ['test', 'ci', 'lint'])
            max_annotations_per_job: Maximum annotations to fetch per job
        """
        self.workflow_patterns = workflow_patterns or ['test', 'ci', 'lint']
        self.max_annotations_per_job = max_annotations_per_job

    def fetch_signals(
        self,
        repo: Repository,
        pr_number: int,
        head_sha: str,
        trace_id: str = "unknown",
    ) -> List[Signal]:
        """
        Fetch signals from GitHub Actions workflow annotations.

        Args:
            repo: GitHub repository object
            pr_number: Pull request number
            head_sha: Head commit SHA
            trace_id: Trace ID for logging

        Returns:
            List of Signal objects from workflow annotations
        """
        signals: List[Signal] = []

        try:
            # Get workflow runs for the head SHA
            workflow_runs = repo.get_workflow_runs(
                head_sha=head_sha,
                event='pull_request'
            )

            # Find matching workflow runs
            target_run = None
            for run in workflow_runs:
                workflow_name = (run.name or "").lower()
                if any(pattern in workflow_name for pattern in self.workflow_patterns):
                    target_run = run
                    break

            if not target_run:
                logger.debug(
                    "[SignalIngestion] No matching workflow run found",
                    extra={
                        "operation": "workflow_signals",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "patterns": self.workflow_patterns,
                    }
                )
                return signals

            # Get jobs from the workflow run
            jobs = target_run.jobs()

            job_count = 0
            for job in jobs:
                job_count += 1
                job_name = job.name or "unknown"

                # Get annotations from job steps
                # Note: GitHub API doesn't directly expose step annotations,
                # but we can get them from check runs associated with the job
                # For now, we rely on CheckRunSignalSource for annotations

                # Log job status for debugging
                if job.conclusion == "failure":
                    # Create a signal for failed jobs
                    signals.append(Signal(
                        source=f"workflow:{target_run.name}",
                        severity=SignalSeverity.ERROR,
                        file_path="",  # Job-level, no specific file
                        message=f"Job '{job_name}' failed",
                        title=f"CI Job Failure: {job_name}",
                    ))

            logger.info(
                f"[SignalIngestion] Processed {job_count} jobs from workflow '{target_run.name}'",
                extra={
                    "operation": "workflow_signals",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "workflow_name": target_run.name,
                    "workflow_run_id": target_run.id,
                    "job_count": job_count,
                    "signal_count": len(signals),
                }
            )

        except GithubException as e:
            logger.warning(
                f"[SignalIngestion] GitHub API error fetching workflow runs: {e}",
                extra={
                    "operation": "workflow_signals",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "error": str(e),
                    "status": getattr(e, 'status', None),
                }
            )
        except Exception as e:
            logger.warning(
                f"[SignalIngestion] Error fetching workflow signals: {e}",
                extra={
                    "operation": "workflow_signals",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "error": str(e),
                }
            )

        return signals


# Default signal sources
_default_sources: List[SignalSource] = [
    CheckRunSignalSource(),
    WorkflowAnnotationSignalSource(),
]


def fetch_signals(
    repo: Repository,
    pr_number: int,
    head_sha: str,
    trace_id: str = "unknown",
    sources: Optional[List[SignalSource]] = None,
) -> List[Signal]:
    """
    Fetch deterministic signals from all configured sources.

    This is the main entry point for signal ingestion. It aggregates
    signals from all configured sources and returns them sorted by
    severity (errors first).

    Args:
        repo: GitHub repository object
        pr_number: Pull request number
        head_sha: Head commit SHA
        trace_id: Trace ID for logging
        sources: Optional list of signal sources (default: all sources)

    Returns:
        List of Signal objects, sorted by severity (errors first)
    """
    if sources is None:
        sources = _default_sources

    all_signals: List[Signal] = []

    for source in sources:
        try:
            signals = source.fetch_signals(repo, pr_number, head_sha, trace_id)
            all_signals.extend(signals)
        except Exception as e:
            source_name = type(source).__name__
            logger.warning(
                f"[SignalIngestion] Error from {source_name}: {e}",
                extra={
                    "operation": "fetch_signals",
                    "trace_id": trace_id,
                    "source": source_name,
                    "error": str(e),
                }
            )

    # Sort by severity (errors first, then warnings, then info)
    severity_order = {
        SignalSeverity.ERROR: 0,
        SignalSeverity.WARNING: 1,
        SignalSeverity.INFO: 2,
    }
    all_signals.sort(key=lambda s: severity_order.get(s.severity, 99))

    logger.info(
        f"[SignalIngestion] Fetched {len(all_signals)} total signals",
        extra={
            "operation": "fetch_signals",
            "trace_id": trace_id,
            "pr_number": pr_number,
            "head_sha": head_sha[:12] if head_sha else None,
            "total_signals": len(all_signals),
            "error_count": sum(1 for s in all_signals if s.severity == SignalSeverity.ERROR),
            "warning_count": sum(1 for s in all_signals if s.severity == SignalSeverity.WARNING),
            "info_count": sum(1 for s in all_signals if s.severity == SignalSeverity.INFO),
        }
    )

    return all_signals


def signals_to_review_comments(
    signals: List[Signal],
    include_info: bool = False,
) -> List[dict]:
    """
    Convert signals to review comment format for Reviewer integration.

    Filters out:
    - Info-level signals (unless include_info=True)
    - Signals without file_path (job-level signals can't be posted as inline comments)

    Args:
        signals: List of Signal objects
        include_info: Whether to include info-level signals (default: False)

    Returns:
        List of review comment dictionaries suitable for inline posting
    """
    comments = []
    for signal in signals:
        # Skip info-level signals unless explicitly requested
        if not include_info and signal.severity == SignalSeverity.INFO:
            continue
        # Skip signals without file_path - they can't be posted as inline comments
        # (e.g., job-level workflow failure signals)
        if not signal.file_path:
            logger.debug(
                f"[SignalIngestion] Skipping signal without file_path: {signal.source}",
                extra={"source": signal.source, "message": signal.message[:100]}
            )
            continue
        comments.append(signal.to_review_comment())
    return comments
