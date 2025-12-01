import os, argparse, time, uuid, hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path
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
    
    allowed, count = check_pr_rate_limit(trace_id, max_per_hour=10, redis_url=settings.redis_url)
    if not allowed:
        print(f"[Rate Limit] BLOCKED - Already created {count} PRs this hour")
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
    branch = create_branch(repo, base="main", new_branch=f"orchestrator/{timestamp}-faq-update")
    
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
    
    commit_file(repo, branch, "docs/FAQ.md", faq_content, f"docs: add FAQ.md (trace-id: {trace_id})")
    
    is_test_mode = settings.orchestrator_test_mode or False
    
    pr_body = f"""## Automated FAQ Update

**Task:** {goal}
**Trace ID:** `{trace_id}`
**Branch:** `{branch}`
**Test Mode:** {"✅ Yes (Draft PR)" if is_test_mode else "❌ No (Production)"}

This PR was automatically generated by the MorningAI Orchestrator.

[Link to Devin run](https://app.devin.ai/sessions/9142c8e8a3de4754a7ba8e8c06a751ed)
Requested by: @RC918

---

**Note:** {"This is a test PR and will be automatically cleaned up after CI validation." if is_test_mode else "This is a production PR for review and merge."}
"""
    
    labels = ["automated-test", "orchestrator"] if is_test_mode else ["orchestrator"]
    
    pr_url, pr_num = open_pr(
        repo, 
        branch, 
        f"docs: Update FAQ (trace-id: {trace_id[:8]})", 
        body=pr_body,
        draft=is_test_mode,
        labels=labels
    )
    print(f"[PR] {pr_url} (trace-id: {trace_id})")
    
    if not is_test_mode:
        try:
            import subprocess
            subprocess.run([
                "gh", "pr", "merge", str(pr_num),
                "--auto", "--squash",
                "--repo", repo_full
            ], check=False)
            print(f"[GitHub] Auto-merge enabled for production PR")
        except Exception as e:
            print(f"[GitHub] Could not enable auto-merge: {e}")
    else:
        print(f"[Test Mode] Skipping auto-merge for draft PR")
    
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
