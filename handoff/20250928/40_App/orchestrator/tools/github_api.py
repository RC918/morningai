import os
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "RC918/morningai")

def get_repo():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")
    gh = Github(GITHUB_TOKEN)
    return gh.get_repo(GITHUB_REPO)

def create_branch(repo, base="main", new_branch="orchestrator/demo-branch"):
    base_ref = repo.get_git_ref(f"heads/{base}")
    try:
        repo.get_git_ref(f"heads/{new_branch}")
        return new_branch
    except:
        repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=base_ref.object.sha)
        return new_branch

def commit_file(repo, branch, path, content, message):
    try:
        file = repo.get_contents(path, ref=branch)
        repo.update_file(path, message, content, file.sha, branch=branch)
    except Exception:
        repo.create_file(path, message, content, branch=branch)

def open_pr(repo, branch, title, body="", base="main"):
    pr = repo.create_pull(title=title, body=body, head=branch, base=base)
    return pr.html_url, pr.number

def get_pr_checks(repo, pr_number:int):
    pr = repo.get_pull(pr_number)
    combined = repo.get_commit(pr.head.sha).get_combined_status()
    return combined.state, [s.context + ":" + s.state for s in combined.statuses]
