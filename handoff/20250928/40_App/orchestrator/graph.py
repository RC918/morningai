import os, argparse, time
from dotenv import load_dotenv
from tools.github_api import get_repo, create_branch, commit_file, open_pr, get_pr_checks
from redis_queue.worker import enqueue
from memory.pgvector_store import save_text, recall_top

def planner(goal:str):
    steps = ["analyze", "patch", "open PR", "check CI"]
    save_text("goal", goal)
    return steps

def execute(goal:str, repo_full: str):
    repo = get_repo()
    branch = create_branch(repo, base="main", new_branch="orchestrator/demo-branch")
    commit_file(repo, branch, "demo_orchestrator.txt", f"Goal: {goal}\n", "chore: add orchestrator demo file")
    pr_url, pr_num = open_pr(repo, branch, f"Orchestrator demo: {goal}", body="automated PR")
    print(f"[PR] {pr_url}")
    state, checks = get_pr_checks(repo, pr_num)
    print(f"[CI] state={state} checks={checks}")
    if state != "success":
        # naive retry once
        time.sleep(3)
        commit_file(repo, branch, "demo_orchestrator.txt", f"Goal: {goal}\nretry fix\n", "fix: retry build")
        state, checks = get_pr_checks(repo, pr_num)
        print(f"[CI] after retry state={state}")
    return pr_url, state

def main(goal:str, repo:str):
    steps = planner(goal)
    print("[Planner] steps:", steps)
    try:
        job_ids = enqueue(steps)
        print("[Queue] enqueued jobs:", job_ids)
    except Exception as e:
        print(f"[Queue] Redis unavailable, continuing in demo mode: {e}")
        job_ids = [f"demo-job-{i}" for i in range(len(steps))]
    # In parallel, we try to execute a minimal GH loop
    try:
        pr_url, state = execute(goal, repo)
        print("[Result]", pr_url, state)
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
    ap.add_argument("--repo", default=os.getenv("GITHUB_REPO","RC918/morningai"))
    args = ap.parse_args()
    main(args.goal, args.repo)
