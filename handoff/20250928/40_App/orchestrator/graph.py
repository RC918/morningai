import os, argparse, time, uuid, hashlib
import logging
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import sys

repo_root = Path(__file__).resolve().parent
for _ in range(8):  # Limit search depth to avoid infinite loop
    if (repo_root / 'common').exists():
        break
    repo_root = repo_root.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from dotenv import load_dotenv
from tools.github_api import get_repo, create_branch, commit_file, open_pr, get_pr_checks, close_pr, delete_branch
from redis_queue.worker import enqueue
from memory.pgvector_store import save_text, recall_top
from llm.faq_generator import generate_faq_content
from utils.rate_limit import check_pr_rate_limit
from governance.cost_tracker import get_cost_tracker, CostBudgetExceeded
from governance.reputation_engine import get_reputation_engine
from governance.changeset_significance import check_value_gate, get_changeset_hash, analyze_diff
from governance.pr_deduplication import check_pr_deduplication, record_pr_creation
from common.config.settings import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Documentation Safety Constants (Issue #2100)
# =============================================================================
CORE_DOCS_PROTECTED = ["docs/FAQ.md", "docs/README.md", "README.md"]
GENERATED_DOCS_PATH = "docs/generated"
MAX_SLUG_LENGTH = 60

# Labels for documentation PRs
LABEL_ORCHESTRATOR_DOCS = "orchestrator-docs"
LABEL_ORCHESTRATOR_DOCS_TEST = "orchestrator-docs-test"
LABEL_ORCHESTRATOR_APPROVED = "orchestrator-approved"


class DocIssueLevel(Enum):
    """Severity level for documentation quality issues."""
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DocIssue:
    """Represents a quality issue found in documentation content."""
    level: DocIssueLevel
    code: str
    message: str


def make_topic_slug(goal: str) -> str:
    """
    Convert a goal/topic into a safe, human-readable filename slug.
    
    Issue #2100: Prevents overwriting core docs by generating unique filenames.
    
    Args:
        goal: The task goal or topic description
        
    Returns:
        A safe filename slug like "how-to-setup-auth-a1b2c3d4"
    """
    # Normalize: lowercase, remove non-word chars except spaces/hyphens
    slug = goal.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Collapse whitespace to single hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Truncate to max length (leaving room for hash suffix)
    slug = slug[:MAX_SLUG_LENGTH - 9]  # 8 chars for hash + 1 for hyphen
    # Add hash suffix for collision avoidance
    hash_suffix = hashlib.md5(goal.encode()).hexdigest()[:8]
    return f"{slug}-{hash_suffix}" if slug else hash_suffix


def validate_faq_content(question: str, content: str) -> List[DocIssue]:
    """
    Validate FAQ content for quality and security issues.
    
    Issue #2100: Content quality checks before PR creation.
    
    Args:
        question: The FAQ question/topic
        content: The generated FAQ content
        
    Returns:
        List of DocIssue objects (empty if no issues found)
    """
    issues: List[DocIssue] = []
    content_lower = content.lower()
    
    # Check 1: SQL examples should include tenant filters (multi-tenant safety)
    sql_patterns = [
        r'SELECT\s+.*\s+FROM\s+\w+',
        r'INSERT\s+INTO\s+\w+',
        r'UPDATE\s+\w+\s+SET',
        r'DELETE\s+FROM\s+\w+'
    ]
    for pattern in sql_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            # Check if tenant_id or organization_id filter is present
            if not re.search(r'(tenant_id|organization_id|org_id)\s*=', content_lower):
                issues.append(DocIssue(
                    level=DocIssueLevel.WARNING,
                    code="MISSING_TENANT_FILTER",
                    message="SQL example found without tenant_id filter - verify multi-tenant safety"
                ))
                break
    
    # Check 2: API examples should include authentication context
    if re.search(r'(curl|fetch|axios|requests\.)', content_lower):
        if not re.search(r'(authorization|bearer|api[_-]?key|token)', content_lower):
            issues.append(DocIssue(
                level=DocIssueLevel.WARNING,
                code="MISSING_AUTH_CONTEXT",
                message="API example found without authentication context"
            ))
    
    # Check 3: Dark mode docs should reference ThemeContext
    if 'dark mode' in content_lower or 'dark theme' in content_lower:
        if 'themecontext' not in content_lower and 'theme-context' not in content_lower:
            issues.append(DocIssue(
                level=DocIssueLevel.WARNING,
                code="MISSING_THEME_CONTEXT",
                message="Dark mode documentation should reference ThemeContext"
            ))
    
    # Check 4: Check for potentially sensitive information
    sensitive_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "HARDCODED_PASSWORD", "Potential hardcoded password detected"),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "HARDCODED_API_KEY", "Potential hardcoded API key detected"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "HARDCODED_SECRET", "Potential hardcoded secret detected"),
    ]
    for pattern, code, message in sensitive_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(DocIssue(
                level=DocIssueLevel.ERROR,
                code=code,
                message=message
            ))
    
    # Check 5: Metadata completeness (should have trace-id footer)
    if 'trace-id:' not in content_lower and 'generated by' not in content_lower:
        issues.append(DocIssue(
            level=DocIssueLevel.WARNING,
            code="MISSING_METADATA",
            message="Documentation missing generation metadata footer"
        ))
    
    # Check 6: Minimum content length
    if len(content.strip()) < 100:
        issues.append(DocIssue(
            level=DocIssueLevel.ERROR,
            code="CONTENT_TOO_SHORT",
            message="Generated content is too short (< 100 chars)"
        ))
    
    return issues


def is_protected_path(file_path: str) -> bool:
    """
    Check if a file path is a protected core document.
    
    Issue #2100: Prevents overwriting core documentation files.
    
    Args:
        file_path: The target file path
        
    Returns:
        True if the path is protected, False otherwise
    """
    normalized = file_path.replace('\\', '/').lower()
    for protected in CORE_DOCS_PROTECTED:
        if normalized == protected.lower() or normalized.endswith('/' + protected.lower()):
            return True
    return False


RISK_SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
SEVERITY_TO_RISK = {v: k for k, v in RISK_SEVERITY.items()}
NEVER_BLOCK_THRESHOLD = 5


def evaluate_execution_policy(
    trace_id: str,
    cost_risk: str = "info",
    rate_limit_risk: str = "info",
    goal: str = "",
    repo: str = ""
) -> Dict[str, Any]:
    """
    Policy Observability Telemetry for Core Executor (graph.execute)

    Records policy evaluation metrics for monitoring and analysis. This function
    is OBSERVABILITY-ONLY - it logs what would have happened under different
    enforcement modes but does NOT block or gate execution. Actual enforcement
    (budget exceeded, rate limited) is handled by the caller before invoking
    this function.

    The return value is currently unused by callers; this function exists to
    provide unified telemetry compatible with LangGraph's policy_enforcement_node
    schema for cross-mode observability dashboards.

    Args:
        trace_id: Unique task identifier for correlation
        cost_risk: Risk level from cost evaluation (info/low/medium/high/critical)
        rate_limit_risk: Risk level from rate limit check (info/low/medium/high/critical)
        goal: Task goal/description (truncated to 100 chars in output)
        repo: Repository being operated on

    Returns:
        Dict with policy evaluation telemetry in unified schema (not used for enforcement)
    """
    from common.config.settings import get_settings

    settings_obj = get_settings()
    mode = settings_obj.security_enforcement_mode

    advisor_risks = {
        "cost": cost_risk,
        "rate_limit": rate_limit_risk,
        "security": "info",
        "governance": "info",
        "permission": "info",
    }

    mode_thresholds = {
        "block_critical": 4,
        "block_high": 3,
        "block_all": 1,
    }

    threshold = mode_thresholds.get(mode, NEVER_BLOCK_THRESHOLD)

    worst_risk = "info"
    worst_severity = 0
    worst_advisor = "none"

    for advisor, risk in advisor_risks.items():
        severity = RISK_SEVERITY.get(risk, 0)
        if severity > worst_severity:
            worst_severity = severity
            worst_risk = risk
            worst_advisor = advisor

    would_block = worst_severity >= threshold and mode != "advisory"

    threshold_name = SEVERITY_TO_RISK.get(threshold, "none")

    policy_event = {
        "event_type": "execution_policy_evaluation",
        "trace_id": trace_id,
        "orchestrator_mode": "langgraph",
        "enforcement_mode": mode,
        "advisor_risks": advisor_risks,
        "worst_advisor": worst_advisor,
        "worst_risk": worst_risk,
        "worst_severity": worst_severity,
        "threshold": threshold,
        "threshold_name": threshold_name,
        "would_block": would_block,
        "actual_blocked": False,
        "goal": goal[:100] if goal else "",
        "repo": repo,
        "timestamp": time.time(),
    }

    logger.info(
        "[Executor][PolicyObservability] Policy evaluation",
        extra={
            "operation": "execution_policy_evaluation",
            "trace_id": trace_id,
            "enforcement_mode": mode,
            "worst_advisor": worst_advisor,
            "worst_risk": worst_risk,
            "would_block": would_block,
            "actual_blocked": False,
        }
    )

    if would_block:
        logger.warning(
            "[Executor][PolicyObservability] Would have blocked execution",
            extra={
                "operation": "execution_policy_would_block",
                "trace_id": trace_id,
                "enforcement_mode": mode,
                "worst_advisor": worst_advisor,
                "worst_risk": worst_risk,
                "block_reason": (
                    f"{worst_advisor}_risk={worst_risk} "
                    f"(mode={mode}, threshold={threshold_name})"
                ),
            }
        )

    return policy_event

def planner(goal:str):
    steps = ["analyze", "patch", "open PR", "check CI"]
    save_text("goal", goal)
    return steps

def execute(goal:str, repo_full: str, trace_id: Optional[str] = None):
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    cost_tracker = get_cost_tracker()
    reputation_engine = get_reputation_engine()
    agent_id = reputation_engine.get_or_create_agent('meta_agent')
    
    cost_risk = "info"
    rate_limit_risk = "info"
    
    # Log entry point for observability
    logger.info(
        f"[GraphExecute] Starting execution trace_id={trace_id} repo={repo_full}",
        extra={"operation": "graph_execute_start", "trace_id": trace_id, "repo": repo_full}
    )
    
    try:
        cost_tracker.enforce_budget(trace_id, period='daily')
        cost_tracker.enforce_budget(trace_id, period='hourly')
    except CostBudgetExceeded as e:
        logger.warning(
            f"[GraphExecute] Budget exceeded trace_id={trace_id}: {e}",
            extra={"operation": "budget_exceeded", "trace_id": trace_id, "error": str(e)}
        )
        cost_risk = "critical"
        evaluate_execution_policy(
            trace_id=trace_id,
            cost_risk=cost_risk,
            rate_limit_risk=rate_limit_risk,
            goal=goal,
            repo=repo_full
        )
        if agent_id:
            reputation_engine.record_event(agent_id, 'cost_overrun', trace_id=trace_id, reason=str(e))
        return None, "budget_exceeded", trace_id
    
    # Issue #2100: Use configurable docs PR rate limit (default: 3/hour)
    docs_max_prs = settings.orchestrator_docs_max_prs_per_hour or 3
    allowed, count = check_pr_rate_limit(trace_id, max_per_hour=docs_max_prs, redis_url=settings.redis_url)
    if not allowed:
        logger.warning(
            f"[GraphExecute] Rate limited trace_id={trace_id} count={count} max={docs_max_prs}",
            extra={"operation": "rate_limited", "trace_id": trace_id, "count": count, "max": docs_max_prs}
        )
        rate_limit_risk = "high"
        evaluate_execution_policy(
            trace_id=trace_id,
            cost_risk=cost_risk,
            rate_limit_risk=rate_limit_risk,
            goal=goal,
            repo=repo_full
        )
        return None, "rate_limited", trace_id
    
    evaluate_execution_policy(
        trace_id=trace_id,
        cost_risk=cost_risk,
        rate_limit_risk=rate_limit_risk,
        goal=goal,
        repo=repo_full
    )
    
    is_dry_run = settings.orchestrator_dry_run or False
    if is_dry_run:
        logger.info(
            f"[GraphExecute] Dry run mode trace_id={trace_id} repo={repo_full} - skipping GitHub operations",
            extra={
                "operation": "dry_run",
                "trace_id": trace_id,
                "goal": goal[:100],
                "repo": repo_full
            }
        )
        return f"dry-run://trace/{trace_id}", "dry_run", trace_id
    
    repo = get_repo()
    timestamp = int(time.time())
    
    # Issue #2100: Generate topic slug for unique file path
    topic_slug = make_topic_slug(goal)
    branch = create_branch(repo, base="main", new_branch=f"orchestrator/{timestamp}-docs-{topic_slug[:20]}")
    
    try:
        faq_content = generate_faq_content(goal, trace_id, repo_full)
        logger.info(
            f"[GraphExecute] Generated FAQ content trace_id={trace_id} chars={len(faq_content)}",
            extra={"operation": "faq_generated", "trace_id": trace_id, "content_length": len(faq_content)}
        )
        
        estimated_tokens = len(faq_content) // 4  # Rough estimate: 4 chars per token
        estimated_cost = cost_tracker.estimate_cost(estimated_tokens, model='gpt-4')
        cost_tracker.track_usage(trace_id, estimated_tokens, estimated_cost, model='gpt-4', operation='faq_generation')
        
    except Exception as e:
        logger.warning(
            f"[GraphExecute] FAQ generation failed trace_id={trace_id}: {e}, using fallback",
            extra={"operation": "faq_generation_failed", "trace_id": trace_id, "error": str(e)}
        )
        # Fallback is handled inside generate_faq_content
        faq_content = generate_faq_content(goal, trace_id, repo_full)
    
    # Issue #2100: Content quality validation
    quality_issues = validate_faq_content(goal, faq_content)
    has_errors = any(issue.level == DocIssueLevel.ERROR for issue in quality_issues)
    has_warnings = any(issue.level == DocIssueLevel.WARNING for issue in quality_issues)
    
    if quality_issues:
        issue_summary = ", ".join([f"{i.code}:{i.level.value}" for i in quality_issues[:5]])
        logger.info(
            f"[GraphExecute] Quality issues found trace_id={trace_id} count={len(quality_issues)} issues=[{issue_summary}]",
            extra={"operation": "quality_issues", "trace_id": trace_id, "issue_count": len(quality_issues)}
        )
    
    # Issue #2100: Default to test mode (now True by default in settings)
    # Force test mode if content has errors
    is_test_mode = settings.orchestrator_test_mode
    if has_errors and not is_test_mode:
        logger.info(
            f"[GraphExecute] Forcing test mode trace_id={trace_id} due to content errors",
            extra={"operation": "force_test_mode", "trace_id": trace_id}
        )
        is_test_mode = True
    
    # Issue #2100: Use generated docs path instead of core FAQ.md
    doc_file_path = f"{GENERATED_DOCS_PATH}/{topic_slug}.md"
    
    # Safety check: Never overwrite protected core docs
    if is_protected_path(doc_file_path):
        logger.error(
            f"[GraphExecute] Protected path blocked trace_id={trace_id} path={doc_file_path}",
            extra={
                "operation": "protected_path_blocked",
                "trace_id": trace_id,
                "path": doc_file_path
            }
        )
        return None, "protected_path", trace_id
    
    # ==========================================================================
    # Value Gate Check (Publisher Node Governance)
    # Blueprint: Flow Controller v3 + Safety Governor v2
    # ==========================================================================
    # Build a synthetic diff for value gate analysis
    synthetic_diff = f"""diff --git a/{doc_file_path} b/{doc_file_path}
new file mode 100644
--- /dev/null
+++ b/{doc_file_path}
@@ -0,0 +1,{len(faq_content.splitlines())} @@
"""
    for line in faq_content.splitlines():
        synthetic_diff += f"+{line}\n"
    
    value_gate_result = check_value_gate(synthetic_diff, goal=goal, trace_id=trace_id)
    logger.info(
        f"[ValueGate] Evaluated trace_id={trace_id} score={value_gate_result.score} type={value_gate_result.primary_change_type.value} should_create={value_gate_result.should_create_pr}",
        extra={
            "operation": "value_gate_evaluated",
            "trace_id": trace_id,
            "score": value_gate_result.score,
            "change_type": value_gate_result.primary_change_type.value,
            "should_create_pr": value_gate_result.should_create_pr
        }
    )
    
    if not value_gate_result.should_create_pr:
        logger.warning(
            f"[ValueGate] BLOCKED trace_id={trace_id} score={value_gate_result.score} reason={value_gate_result.downgrade_reason}",
            extra={
                "operation": "value_gate_blocked",
                "trace_id": trace_id,
                "score": value_gate_result.score,
                "downgrade_reason": value_gate_result.downgrade_reason,
                "goal": goal[:100]
            }
        )
        return None, "value_gate_blocked", trace_id
    
    # ==========================================================================
    # PR Deduplication Check (Memory v2 Short-term)
    # Blueprint: Memory v2 Layer 1 (Short-term Memory)
    # ==========================================================================
    changeset_hash = get_changeset_hash(synthetic_diff)
    file_paths = [doc_file_path]
    
    dedup_result = check_pr_deduplication(
        goal=goal,
        changeset_hash=changeset_hash,
        file_paths=file_paths,
        repo=repo_full,
        trace_id=trace_id
    )
    
    # Log PRDedup check result
    logger.info(
        f"[PRDedup] Checked trace_id={trace_id} is_duplicate={dedup_result.is_duplicate} type={dedup_result.duplicate_type} similarity={dedup_result.similarity_score:.2f}",
        extra={
            "operation": "pr_dedup_checked",
            "trace_id": trace_id,
            "is_duplicate": dedup_result.is_duplicate,
            "duplicate_type": dedup_result.duplicate_type,
            "similarity_score": dedup_result.similarity_score
        }
    )
    
    if dedup_result.is_duplicate:
        if not dedup_result.should_create_pr:
            logger.warning(
                f"[PRDedup] BLOCKED trace_id={trace_id} type={dedup_result.duplicate_type} similarity={dedup_result.similarity_score:.2f}",
                extra={
                    "operation": "pr_dedup_blocked",
                    "trace_id": trace_id,
                    "duplicate_type": dedup_result.duplicate_type,
                    "similarity_score": dedup_result.similarity_score,
                    "goal": goal[:100]
                }
            )
            return None, "duplicate_blocked", trace_id
    
    commit_file(repo, branch, doc_file_path, faq_content, f"docs: add {topic_slug}.md (trace-id: {trace_id})")
    
    # Issue #2100: Build quality report for PR body
    quality_report = ""
    if quality_issues:
        quality_report = "\n### Quality Check Results\n"
        for issue in quality_issues:
            emoji = "⚠️" if issue.level == DocIssueLevel.WARNING else "❌"
            quality_report += f"- {emoji} **{issue.code}**: {issue.message}\n"
        quality_report += "\n"
    
    pr_body = f"""## Automated Documentation Update

**Task:** {goal}
**Trace ID:** `{trace_id}`
**Branch:** `{branch}`
**File:** `{doc_file_path}`
**Test Mode:** {"✅ Yes (Draft PR)" if is_test_mode else "❌ No (Production)"}
{quality_report}
This PR was automatically generated by the MorningAI Orchestrator.

[Link to Devin run](https://app.devin.ai/sessions/9142c8e8a3de4754a7ba8e8c06a751ed)
Requested by: @RC918

---

**Note:** {"This is a test PR and will be automatically cleaned up after CI validation." if is_test_mode else "This is a production PR. Requires `orchestrator-approved` label for merge."}
"""
    
    # Issue #2100: Enhanced labeling for documentation PRs
    labels = [LABEL_ORCHESTRATOR_DOCS]
    if is_test_mode:
        labels.append(LABEL_ORCHESTRATOR_DOCS_TEST)
        labels.append("automated-test")
    if has_warnings:
        labels.append("needs-review")
    if has_errors:
        labels.append("quality-issues")
    
    pr_url, pr_num = open_pr(
        repo, 
        branch, 
        f"docs: Add {topic_slug[:30]} (trace-id: {trace_id[:8]})", 
        body=pr_body,
        draft=is_test_mode,
        labels=labels
    )
    logger.info(
        f"[GraphExecute] PR created trace_id={trace_id} pr_url={pr_url} pr_num={pr_num}",
        extra={"operation": "pr_created", "trace_id": trace_id, "pr_url": pr_url, "pr_num": pr_num}
    )
    
    # Record PR creation for future deduplication (Memory v2 Short-term)
    record_pr_creation(
        trace_id=trace_id,
        goal=goal,
        changeset_hash=changeset_hash,
        file_paths=file_paths,
        repo=repo_full,
        branch=branch,
        pr_url=pr_url,
        pr_number=pr_num
    )
    
    # Issue #2100: Disable auto-merge for docs PRs (require human approval)
    # Production docs PRs require `orchestrator-approved` label before merge
    if not is_test_mode:
        logger.info(
            f"[GraphExecute] Human gate enabled trace_id={trace_id} pr_num={pr_num} - requires '{LABEL_ORCHESTRATOR_APPROVED}' label",
            extra={"operation": "human_gate_enabled", "trace_id": trace_id, "pr_num": pr_num}
        )
    else:
        logger.info(
            f"[GraphExecute] Test mode trace_id={trace_id} pr_num={pr_num} - skipping auto-merge for draft PR",
            extra={"operation": "test_mode_draft", "trace_id": trace_id, "pr_num": pr_num}
        )
    
    state, checks = get_pr_checks(repo, pr_num)
    logger.info(
        f"[GraphExecute] CI status trace_id={trace_id} state={state} checks={checks}",
        extra={"operation": "ci_status", "trace_id": trace_id, "state": state, "checks": checks}
    )
    
    if agent_id and state == "success":
        reputation_engine.record_event(agent_id, 'test_passed', trace_id=trace_id, reason='CI checks passed')
    elif agent_id and state in ["failure", "error"]:
        reputation_engine.record_event(agent_id, 'test_failed', trace_id=trace_id, reason=f'CI checks failed: {state}')
    
    budget_status = cost_tracker.get_budget_status(trace_id, period='daily')
    logger.info(
        f"[GraphExecute] Budget status trace_id={trace_id} usage={budget_status['usage']['usd']:.2f} limit={budget_status['limits']['usd']:.2f} percent={budget_status['percentages']['usd']:.1f}",
        extra={"operation": "budget_status", "trace_id": trace_id, "usage_usd": budget_status['usage']['usd'], "limit_usd": budget_status['limits']['usd']}
    )
    
    if is_test_mode:
        logger.info(
            f"[GraphExecute] Test mode PR created trace_id={trace_id} pr_num={pr_num} - auto-cleanup enabled",
            extra={"operation": "test_mode_pr_created", "trace_id": trace_id, "pr_num": pr_num}
        )
        
        if state in ["success", "failure", "error"]:
            logger.info(
                f"[GraphExecute] Test mode cleanup trace_id={trace_id} ci_state={state}",
                extra={"operation": "test_mode_cleanup", "trace_id": trace_id, "ci_state": state}
            )
            
            cleanup_comment = f"""## Automated Test Cleanup

This PR was created in test mode and has completed CI validation.

**CI State:** {state}
**Trace ID:** {trace_id}

Closing this PR and cleaning up the branch.

Orchestrator system validation complete!
"""
            
            if close_pr(repo, pr_num, cleanup_comment):
                logger.info(
                    f"[GraphExecute] Test PR closed trace_id={trace_id} pr_num={pr_num}",
                    extra={"operation": "test_pr_closed", "trace_id": trace_id, "pr_num": pr_num}
                )
                
                if delete_branch(repo, branch):
                    logger.info(
                        f"[GraphExecute] Test branch deleted trace_id={trace_id} branch={branch}",
                        extra={"operation": "test_branch_deleted", "trace_id": trace_id, "branch": branch}
                    )
            else:
                logger.warning(
                    f"[GraphExecute] Test cleanup failed trace_id={trace_id} pr_num={pr_num} - manual intervention required",
                    extra={"operation": "test_cleanup_failed", "trace_id": trace_id, "pr_num": pr_num}
                )
    
    return pr_url, state, trace_id

def main(goal:str, repo:str):
    trace_id = str(uuid.uuid4())
    print(f"[Trace] Starting task with trace-id: {trace_id}")
    
    steps = planner(goal)
    print("[Planner] steps:", steps)
    
    idempotency_key = hashlib.md5(goal.encode()).hexdigest()
    
    try:
        job_ids = enqueue(steps, idempotency_key=idempotency_key)
        print("[Queue] enqueued jobs:", job_ids)
    except Exception as e:
        print(f"[Queue] Redis unavailable, continuing in demo mode: {e}")
        job_ids = [f"demo-job-{i}" for i in range(len(steps))]
    
    try:
        pr_url, state, trace_id = execute(goal, repo, trace_id=trace_id)
        print("[Result]", pr_url, state, f"trace-id: {trace_id}")
    except Exception as e:
        print(f"[GitHub] API unavailable, continuing in demo mode: {e}")
        pr_url, state = "demo-pr-url", "demo"
    
    try:
        mem = recall_top("recent")
        print("[Memory] recent items:", len(mem))
    except Exception as e:
        print(f"[Memory] Supabase unavailable, continuing in demo mode: {e}")
        mem = []

if __name__ == "__main__":
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", required=True)
    ap.add_argument("--repo", default=settings.github_repo or "RC918/morningai")
    args = ap.parse_args()
    main(args.goal, args.repo)
