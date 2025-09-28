import os
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "RC918/morningai")

def get_repo():
    try:
        if not GITHUB_TOKEN:
            print("[GitHub] GITHUB_TOKEN not set")
            return None
        gh = Github(GITHUB_TOKEN)
        return gh.get_repo(GITHUB_REPO)
    except Exception as e:
        print(f"[GitHub] Failed to get repo: {e}")
        return None

def create_branch(repo, base="main", new_branch="orchestrator/demo-branch"):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return "demo-branch"
        base_ref = repo.get_git_ref(f"heads/{base}")
        try:
            repo.get_git_ref(f"heads/{new_branch}")
            return new_branch
        except:
            repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=base_ref.object.sha)
            return new_branch
    except Exception as e:
        print(f"[GitHub] Failed to create branch: {e}")
        return "demo-branch"

def commit_file(repo, branch, path, content, message):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return
        file = repo.get_contents(path, ref=branch)
        repo.update_file(path, message, content, file.sha, branch=branch)
    except Exception as e:
        if repo is None:
            print("[GitHub] Repository not available")
        else:
            try:
                repo.create_file(path, message, content, branch=branch)
            except Exception as create_error:
                print(f"[GitHub] Failed to commit file: {create_error}")

def open_pr(repo, branch, title, body="", base="main"):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return "demo-pr-url", 0
        pr = repo.create_pull(title=title, body=body, head=branch, base=base)
        return pr.html_url, pr.number
    except Exception as e:
        print(f"[GitHub] Failed to open PR: {e}")
        return "demo-pr-url", 0

def get_pr_checks(repo, pr_number:int):
    try:
        if repo is None:
            print("[GitHub] Repository not available")
            return "demo", []
        pr = repo.get_pull(pr_number)
        combined = repo.get_commit(pr.head.sha).get_combined_status()
        return combined.state, [s.context + ":" + s.state for s in combined.statuses]
    except Exception as e:
        print(f"[GitHub] Failed to get PR checks: {e}")
        return "demo", []
