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


def evaluate_simple_mode_policy(
    trace_id: str,
    cost_risk: str = "info",
    rate_limit_risk: str = "info",
    goal: str = "",
    repo: str = ""
) -> Dict[str, Any]:
    """
    PR-3: Simple Mode Policy Observability

    Evaluates what the policy enforcement WOULD have done in Simple Mode.
    This is observability-only - Simple Mode never blocks, but we record
    what would have happened if enforcement was enabled.

    Uses the same schema as LangGraph policy_enforcement_node for unified
    observability across both orchestrator modes.

    Args:
        trace_id: Unique task identifier
        cost_risk: Risk level from cost evaluation (info/low/medium/high/critical)
        rate_limit_risk: Risk level from rate limit check
        goal: Task goal/description
        repo: Repository being operated on

    Returns:
        Dict with policy evaluation results in unified schema
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
        "event_type": "simple_mode_policy_evaluation",
        "trace_id": trace_id,
        "orchestrator_mode": "simple",
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
        "[SimpleMode][PolicyObservability] Policy evaluation",
        extra={
            "operation": "simple_mode_policy_evaluation",
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
            "[SimpleMode][PolicyObservability] Would have blocked execution",
            extra={
                "operation": "simple_mode_policy_would_block",
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
    
    try:
        cost_tracker.enforce_budget(trace_id, period='daily')
        cost_tracker.enforce_budget(trace_id, period='hourly')
    except CostBudgetExceeded as e:
        print(f"[Cost] Budget exceeded: {e}")
        cost_risk = "critical"
        evaluate_simple_mode_policy(
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
        print(f"[Rate Limit] BLOCKED - Already created {count} docs PRs this hour (max: {docs_max_prs})")
        rate_limit_risk = "high"
        evaluate_simple_mode_policy(
            trace_id=trace_id,
            cost_risk=cost_risk,
            rate_limit_risk=rate_limit_risk,
            goal=goal,
            repo=repo_full
        )
        return None, "rate_limited", trace_id
    
    evaluate_simple_mode_policy(
        trace_id=trace_id,
        cost_risk=cost_risk,
        rate_limit_risk=rate_limit_risk,
        goal=goal,
        repo=repo_full
    )
    
    is_dry_run = settings.orchestrator_dry_run or False
    if is_dry_run:
        print(f"[DRY_RUN] Skipping PR creation for goal: {goal[:50]}...")
        print(f"[DRY_RUN] trace_id={trace_id}, repo={repo_full}")
        logger.info(
            "[DRY_RUN] Orchestrator dry run mode - skipping GitHub operations",
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
        print(f"[GPT-4] Generated FAQ content ({len(faq_content)} chars)")
        
        estimated_tokens = len(faq_content) // 4  # Rough estimate: 4 chars per token
        estimated_cost = cost_tracker.estimate_cost(estimated_tokens, model='gpt-4')
        cost_tracker.track_usage(trace_id, estimated_tokens, estimated_cost, model='gpt-4', operation='faq_generation')
        
    except Exception as e:
        print(f"[GPT-4] Failed to generate content: {e}, using fallback")
        # Fallback is handled inside generate_faq_content
        faq_content = generate_faq_content(goal, trace_id, repo_full)
    
    # Issue #2100: Content quality validation
    quality_issues = validate_faq_content(goal, faq_content)
    has_errors = any(issue.level == DocIssueLevel.ERROR for issue in quality_issues)
    has_warnings = any(issue.level == DocIssueLevel.WARNING for issue in quality_issues)
    
    if quality_issues:
        print(f"[Quality] Found {len(quality_issues)} issue(s) in generated content:")
        for issue in quality_issues:
            print(f"  [{issue.level.value.upper()}] {issue.code}: {issue.message}")
    
    # Issue #2100: Default to test mode (now True by default in settings)
    # Force test mode if content has errors
    is_test_mode = settings.orchestrator_test_mode
    if has_errors and not is_test_mode:
        print("[Quality] Forcing test mode due to content errors")
        is_test_mode = True
    
    # Issue #2100: Use generated docs path instead of core FAQ.md
    doc_file_path = f"{GENERATED_DOCS_PATH}/{topic_slug}.md"
    
    # Safety check: Never overwrite protected core docs
    if is_protected_path(doc_file_path):
        print(f"[Safety] BLOCKED - Cannot overwrite protected path: {doc_file_path}")
        logger.error(
            "[Safety] Attempted to overwrite protected documentation",
            extra={
                "operation": "protected_path_blocked",
                "trace_id": trace_id,
                "path": doc_file_path
            }
        )
        return None, "protected_path", trace_id
    
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
    print(f"[PR] {pr_url} (trace-id: {trace_id})")
    
    # Issue #2100: Disable auto-merge for docs PRs (require human approval)
    # Production docs PRs require `orchestrator-approved` label before merge
    if not is_test_mode:
        print(f"[Human Gate] Production docs PR requires '{LABEL_ORCHESTRATOR_APPROVED}' label for merge")
        print("[Human Gate] Auto-merge disabled for documentation PRs (Issue #2100)")
    else:
        print("[Test Mode] Skipping auto-merge for draft PR")
    
    state, checks = get_pr_checks(repo, pr_num)
    print(f"[CI] state={state} checks={checks}")
    
    if agent_id and state == "success":
        reputation_engine.record_event(agent_id, 'test_passed', trace_id=trace_id, reason='CI checks passed')
    elif agent_id and state in ["failure", "error"]:
        reputation_engine.record_event(agent_id, 'test_failed', trace_id=trace_id, reason=f'CI checks failed: {state}')
    
    budget_status = cost_tracker.get_budget_status(trace_id, period='daily')
    print(f"[Cost] Daily budget: {budget_status['usage']['usd']:.2f}/${budget_status['limits']['usd']:.2f} USD ({budget_status['percentages']['usd']:.1f}%)")
    
    if is_test_mode:
        print(f"[Test Mode] PR #{pr_num} created as draft for testing")
        print(f"[Test Mode] Auto-cleanup enabled after CI validation")
        
        if state in ["success", "failure", "error"]:
            print(f"[Test Mode] CI completed with state: {state}")
            print(f"[Test Mode] Cleaning up test PR...")
            
            cleanup_comment = f"""## Automated Test Cleanup

This PR was created in test mode and has completed CI validation.

**CI State:** {state}
**Trace ID:** {trace_id}

Closing this PR and cleaning up the branch.

✅ Orchestrator system validation complete!
"""
            
            if close_pr(repo, pr_num, cleanup_comment):
                print(f"[Test Mode] PR #{pr_num} closed")
                
                if delete_branch(repo, branch):
                    print(f"[Test Mode] Branch {branch} deleted")
            else:
                print(f"[Test Mode] Failed to cleanup, manual intervention required")
    
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
