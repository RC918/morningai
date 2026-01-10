"""
CI Failure Polling Scanner - Webhook Backup Mechanism

This module provides a periodic scanner that checks active PRs for CI failures
that were missed by webhooks, serving as the ultimate defense against silent failures.

Issue: #3519 - feat(EPIC-I): Add CI failure polling scanner as webhook backup

Architecture:
    Scanner Agent (Cron Job)
        |
        v
    [1] List PRs updated recently (1 API call)
        |
        v
    [2] Filter: Remove PRs with handled marker in Redis
        |
        v
    [3] For each candidate: Check CI status (N API calls)
        |
        v
    [4] If CI failed & not handled: Enqueue AutoFixer task
        |
        v
    [5] Set handled marker in Redis

Rate Limit Strategy (5000 requests/hour budget):
    - Narrow scan scope: Only PRs updated in last 2 hours
    - Internal handled markers: Redis key `handled:{repo}:{pr}:{sha}`
    - Budget control: Max 100 API requests per scan run
    - Low frequency: Every 15-30 minutes (last resort, not primary)

Blueprint Alignment:
    - EPIC I (Immune System): Self-healing through proactive monitoring
    - Deterministic: Clear rules for what gets scanned and when
    - Self-Healing: Automatic recovery from missed webhooks
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Scanner configuration constants
SCANNER_LOOKBACK_HOURS = 2  # Only scan PRs updated in last N hours
SCANNER_MAX_API_REQUESTS = 100  # Max API requests per scan run
SCANNER_HANDLED_KEY_PREFIX = "scanner:handled"
SCANNER_HANDLED_TTL_SECONDS = 7200  # 2 hours TTL for handled markers
SCANNER_SOURCE = "scanner"  # Source identifier for telemetry

# CI failure conclusions that trigger auto-fix
CI_FAILURE_CONCLUSIONS = {"failure", "timed_out", "cancelled"}


@dataclass
class ScanResult:
    """Result of a single PR scan."""
    repo: str
    pr_number: int
    head_sha: str
    ci_status: str
    ci_conclusion: Optional[str]
    needs_fix: bool
    was_handled: bool
    enqueued: bool
    error: Optional[str] = None


@dataclass
class ScanSummary:
    """Summary of a complete scan run."""
    scan_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    prs_scanned: int = 0
    prs_skipped_handled: int = 0
    prs_needing_fix: int = 0
    prs_enqueued: int = 0
    api_requests_used: int = 0
    errors: List[str] = field(default_factory=list)
    results: List[ScanResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/telemetry."""
        return {
            "scan_id": self.scan_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at and self.started_at else None
            ),
            "prs_scanned": self.prs_scanned,
            "prs_skipped_handled": self.prs_skipped_handled,
            "prs_needing_fix": self.prs_needing_fix,
            "prs_enqueued": self.prs_enqueued,
            "api_requests_used": self.api_requests_used,
            "error_count": len(self.errors),
        }


class CIFailureScanner:
    """
    Periodic scanner for CI failures that may have been missed by webhooks.

    This scanner provides a "Pull" mechanism to complement the "Push" webhook
    approach, ensuring no CI failures are silently ignored.

    Usage:
        scanner = CIFailureScanner(repo="RC918/morningai")
        summary = scanner.run()
        print(f"Scanned {summary.prs_scanned} PRs, enqueued {summary.prs_enqueued}")
    """

    def __init__(
        self,
        repo: Optional[str] = None,
        lookback_hours: int = SCANNER_LOOKBACK_HOURS,
        max_api_requests: int = SCANNER_MAX_API_REQUESTS,
        dry_run: bool = False,
    ):
        """
        Initialize the CI failure scanner.

        Args:
            repo: Repository in owner/repo format (defaults to GITHUB_REPO env var)
            lookback_hours: Only scan PRs updated in last N hours
            max_api_requests: Maximum API requests per scan run
            dry_run: If True, don't actually enqueue tasks (for testing)
        """
        self.repo = repo or os.environ.get("GITHUB_REPO", "RC918/morningai")
        self.lookback_hours = lookback_hours
        self.max_api_requests = max_api_requests
        self.dry_run = dry_run
        self._api_requests_used = 0
        self._redis_client = None

    def run(self) -> ScanSummary:
        """
        Execute a complete scan run.

        Returns:
            ScanSummary with results and statistics
        """
        scan_id = f"scan_{int(time.time())}"
        summary = ScanSummary(
            scan_id=scan_id,
            started_at=datetime.now(timezone.utc),
        )

        logger.info(
            "[CIFailureScanner] Starting scan run",
            extra={
                "operation": "scanner_start",
                "scan_id": scan_id,
                "repo": self.repo,
                "lookback_hours": self.lookback_hours,
                "max_api_requests": self.max_api_requests,
                "dry_run": self.dry_run,
            }
        )

        try:
            # Step 1: List recently updated PRs
            prs = self._list_recent_prs()
            if not prs:
                logger.info(
                    "[CIFailureScanner] No recent PRs found",
                    extra={"operation": "scanner_no_prs", "scan_id": scan_id}
                )
                summary.completed_at = datetime.now(timezone.utc)
                return summary

            logger.info(
                f"[CIFailureScanner] Found {len(prs)} recent PRs to scan",
                extra={
                    "operation": "scanner_prs_found",
                    "scan_id": scan_id,
                    "pr_count": len(prs),
                }
            )

            # Step 2-5: Process each PR
            for pr in prs:
                if self._api_requests_used >= self.max_api_requests:
                    logger.warning(
                        "[CIFailureScanner] API request budget exhausted",
                        extra={
                            "operation": "scanner_budget_exhausted",
                            "scan_id": scan_id,
                            "api_requests_used": self._api_requests_used,
                        }
                    )
                    break

                result = self._process_pr(pr, scan_id)
                summary.results.append(result)
                summary.prs_scanned += 1

                if result.was_handled:
                    summary.prs_skipped_handled += 1
                elif result.needs_fix:
                    summary.prs_needing_fix += 1
                    if result.enqueued:
                        summary.prs_enqueued += 1

                if result.error:
                    summary.errors.append(result.error)

        except Exception as e:
            error_msg = f"Scanner run failed: {str(e)}"
            logger.error(
                f"[CIFailureScanner] {error_msg}",
                extra={
                    "operation": "scanner_error",
                    "scan_id": scan_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            summary.errors.append(error_msg)

        summary.completed_at = datetime.now(timezone.utc)
        summary.api_requests_used = self._api_requests_used

        logger.info(
            "[CIFailureScanner] Scan run completed",
            extra={
                "operation": "scanner_complete",
                **summary.to_dict(),
            }
        )

        return summary

    def _list_recent_prs(self) -> List[Dict[str, Any]]:
        """
        List PRs updated within the lookback window.

        Returns:
            List of PR data dictionaries
        """
        try:
            from tools.github_api import get_repo

            github_repo = get_repo()
            if not github_repo:
                logger.error("[CIFailureScanner] GitHub repo not available")
                return []

            self._api_requests_used += 1

            # Get open PRs, sorted by updated_at descending
            prs = []
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)

            for pr in github_repo.get_pulls(state="open", sort="updated", direction="desc"):
                self._api_requests_used += 1

                # Check if PR was updated within lookback window
                updated_at = pr.updated_at
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)

                if updated_at < cutoff_time:
                    # PRs are sorted by updated_at desc, so we can stop here
                    break

                prs.append({
                    "number": pr.number,
                    "head_sha": pr.head.sha,
                    "head_ref": pr.head.ref,
                    "title": pr.title,
                    "updated_at": updated_at,
                    "user": pr.user.login if pr.user else "unknown",
                })

                # Early exit if we've used too many API requests
                if self._api_requests_used >= self.max_api_requests // 2:
                    logger.warning(
                        "[CIFailureScanner] Stopping PR list early to preserve API budget",
                        extra={
                            "operation": "scanner_budget_warning",
                            "api_requests_used": self._api_requests_used,
                            "prs_found": len(prs),
                        }
                    )
                    break

            return prs

        except Exception as e:
            logger.error(
                f"[CIFailureScanner] Failed to list PRs: {e}",
                extra={"operation": "scanner_list_prs_error", "error": str(e)},
                exc_info=True,
            )
            return []

    def _process_pr(self, pr: Dict[str, Any], scan_id: str) -> ScanResult:
        """
        Process a single PR: check handled status, CI status, and enqueue if needed.

        Args:
            pr: PR data dictionary
            scan_id: Current scan run ID

        Returns:
            ScanResult with processing outcome
        """
        pr_number = pr["number"]
        head_sha = pr["head_sha"]

        result = ScanResult(
            repo=self.repo,
            pr_number=pr_number,
            head_sha=head_sha,
            ci_status="unknown",
            ci_conclusion=None,
            needs_fix=False,
            was_handled=False,
            enqueued=False,
        )

        try:
            # Step 2: Check if already handled
            if self._is_handled(pr_number, head_sha):
                result.was_handled = True
                logger.debug(
                    f"[CIFailureScanner] PR #{pr_number} already handled",
                    extra={
                        "operation": "scanner_pr_handled",
                        "scan_id": scan_id,
                        "pr_number": pr_number,
                        "head_sha": head_sha[:8],
                    }
                )
                return result

            # Step 3: Check CI status
            ci_status, ci_conclusion = self._get_ci_status(pr_number, head_sha)
            result.ci_status = ci_status
            result.ci_conclusion = ci_conclusion

            # Step 4: Determine if fix is needed
            if ci_conclusion in CI_FAILURE_CONCLUSIONS:
                result.needs_fix = True

                logger.info(
                    f"[CIFailureScanner] PR #{pr_number} needs fix (CI {ci_conclusion})",
                    extra={
                        "operation": "scanner_pr_needs_fix",
                        "scan_id": scan_id,
                        "pr_number": pr_number,
                        "head_sha": head_sha[:8],
                        "ci_status": ci_status,
                        "ci_conclusion": ci_conclusion,
                    }
                )

                # Step 4: Enqueue AutoFixer task
                if not self.dry_run:
                    enqueued = self._enqueue_auto_fix(pr_number, head_sha, ci_conclusion)
                    result.enqueued = enqueued

                # Step 5: Mark as handled
                self._mark_handled(pr_number, head_sha)

            else:
                # CI passed or pending - mark as handled to avoid re-checking
                if ci_status == "completed" and ci_conclusion not in CI_FAILURE_CONCLUSIONS:
                    self._mark_handled(pr_number, head_sha)

        except Exception as e:
            result.error = str(e)
            logger.error(
                f"[CIFailureScanner] Error processing PR #{pr_number}: {e}",
                extra={
                    "operation": "scanner_pr_error",
                    "scan_id": scan_id,
                    "pr_number": pr_number,
                    "error": str(e),
                },
                exc_info=True,
            )

        return result

    def _get_ci_status(self, pr_number: int, head_sha: str) -> tuple:
        """
        Get CI status for a PR.

        Args:
            pr_number: PR number
            head_sha: Head commit SHA

        Returns:
            Tuple of (status, conclusion)
        """
        try:
            from tools.github_api import get_repo

            github_repo = get_repo()
            if not github_repo:
                return ("unknown", None)

            self._api_requests_used += 1

            # Get check runs for the head SHA
            commit = github_repo.get_commit(head_sha)
            check_runs = commit.get_check_runs()

            self._api_requests_used += 1

            # Aggregate status across all check runs
            statuses = []
            conclusions = []

            for check_run in check_runs:
                statuses.append(check_run.status)
                if check_run.conclusion:
                    conclusions.append(check_run.conclusion)

            if not statuses:
                return ("pending", None)

            # Determine overall status
            if all(s == "completed" for s in statuses):
                overall_status = "completed"
            elif any(s == "in_progress" for s in statuses):
                overall_status = "in_progress"
            else:
                overall_status = "pending"

            # Determine overall conclusion (worst case)
            if conclusions:
                if any(c in CI_FAILURE_CONCLUSIONS for c in conclusions):
                    # Find the worst failure
                    for failure_type in ["failure", "timed_out", "cancelled"]:
                        if failure_type in conclusions:
                            return (overall_status, failure_type)
                elif all(c == "success" for c in conclusions):
                    return (overall_status, "success")
                else:
                    return (overall_status, conclusions[0])

            return (overall_status, None)

        except Exception as e:
            logger.error(
                f"[CIFailureScanner] Failed to get CI status for PR #{pr_number}: {e}",
                extra={
                    "operation": "scanner_ci_status_error",
                    "pr_number": pr_number,
                    "head_sha": head_sha[:8],
                    "error": str(e),
                },
            )
            return ("error", None)

    def _is_handled(self, pr_number: int, head_sha: str) -> bool:
        """
        Check if a PR+SHA combination has already been handled.

        Args:
            pr_number: PR number
            head_sha: Head commit SHA

        Returns:
            True if already handled
        """
        redis_client = self._get_redis_client()
        if not redis_client:
            return False

        key = f"{SCANNER_HANDLED_KEY_PREFIX}:{self.repo}:{pr_number}:{head_sha}"
        try:
            return redis_client.exists(key) > 0
        except Exception as e:
            logger.warning(
                f"[CIFailureScanner] Redis check failed: {e}",
                extra={"operation": "scanner_redis_check_error", "error": str(e)},
            )
            return False

    def _mark_handled(self, pr_number: int, head_sha: str) -> bool:
        """
        Mark a PR+SHA combination as handled.

        Args:
            pr_number: PR number
            head_sha: Head commit SHA

        Returns:
            True if successfully marked
        """
        redis_client = self._get_redis_client()
        if not redis_client:
            return False

        key = f"{SCANNER_HANDLED_KEY_PREFIX}:{self.repo}:{pr_number}:{head_sha}"
        try:
            redis_client.set(key, "1", ex=SCANNER_HANDLED_TTL_SECONDS)
            return True
        except Exception as e:
            logger.warning(
                f"[CIFailureScanner] Redis set failed: {e}",
                extra={"operation": "scanner_redis_set_error", "error": str(e)},
            )
            return False

    def _enqueue_auto_fix(self, pr_number: int, head_sha: str, ci_conclusion: str) -> bool:
        """
        Enqueue an AutoFixer task for a failed PR.

        Args:
            pr_number: PR number
            head_sha: Head commit SHA
            ci_conclusion: CI conclusion (failure, timed_out, cancelled)

        Returns:
            True if successfully enqueued
        """
        try:
            from redis_queue.enqueue import enqueue_task

            task_data = {
                "repo": self.repo,
                "pr_number": pr_number,
                "head_sha": head_sha,
                "ci_conclusion": ci_conclusion,
                "source": SCANNER_SOURCE,
                "trigger": "ci_failure_scanner",
            }

            job_id = enqueue_task(
                task_type="auto_fix",
                task_data=task_data,
                priority="normal",
            )

            logger.info(
                f"[CIFailureScanner] Enqueued auto-fix task for PR #{pr_number}",
                extra={
                    "operation": "scanner_enqueue_success",
                    "pr_number": pr_number,
                    "head_sha": head_sha[:8],
                    "job_id": job_id,
                    "source": SCANNER_SOURCE,
                }
            )
            return True

        except ImportError:
            logger.warning(
                "[CIFailureScanner] redis_queue.enqueue not available - skipping enqueue",
                extra={"operation": "scanner_enqueue_import_error"},
            )
            return False
        except Exception as e:
            logger.error(
                f"[CIFailureScanner] Failed to enqueue auto-fix: {e}",
                extra={
                    "operation": "scanner_enqueue_error",
                    "pr_number": pr_number,
                    "error": str(e),
                },
            )
            return False

    def _get_redis_client(self):
        """
        Get Redis client for handled markers.

        Returns:
            Redis client instance or None if unavailable
        """
        if self._redis_client is not None:
            return self._redis_client

        try:
            import redis

            try:
                from common.config.settings import settings
                url = getattr(settings, 'redis_url', None)
            except ImportError:
                url = os.environ.get('REDIS_URL')

            if url:
                self._redis_client = redis.Redis.from_url(url, decode_responses=True)
                return self._redis_client
            else:
                logger.debug("[CIFailureScanner] No Redis URL configured")
                return None

        except Exception as e:
            logger.warning(f"[CIFailureScanner] Failed to connect to Redis: {e}")
            return None


def run_scanner(
    repo: Optional[str] = None,
    lookback_hours: int = SCANNER_LOOKBACK_HOURS,
    max_api_requests: int = SCANNER_MAX_API_REQUESTS,
    dry_run: bool = False,
) -> ScanSummary:
    """
    Convenience function to run the CI failure scanner.

    This is the main entry point for cron job execution.

    Args:
        repo: Repository in owner/repo format (defaults to GITHUB_REPO env var)
        lookback_hours: Only scan PRs updated in last N hours
        max_api_requests: Maximum API requests per scan run
        dry_run: If True, don't actually enqueue tasks (for testing)

    Returns:
        ScanSummary with results and statistics
    """
    scanner = CIFailureScanner(
        repo=repo,
        lookback_hours=lookback_hours,
        max_api_requests=max_api_requests,
        dry_run=dry_run,
    )
    return scanner.run()


if __name__ == "__main__":
    # CLI entry point for manual testing
    import argparse
    import json

    parser = argparse.ArgumentParser(description="CI Failure Scanner")
    parser.add_argument("--repo", help="Repository in owner/repo format")
    parser.add_argument("--lookback-hours", type=int, default=SCANNER_LOOKBACK_HOURS)
    parser.add_argument("--max-api-requests", type=int, default=SCANNER_MAX_API_REQUESTS)
    parser.add_argument("--dry-run", action="store_true", help="Don't enqueue tasks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    summary = run_scanner(
        repo=args.repo,
        lookback_hours=args.lookback_hours,
        max_api_requests=args.max_api_requests,
        dry_run=args.dry_run,
    )

    print(json.dumps(summary.to_dict(), indent=2))
