from typing import Optional
from github import Github
from git import Repo, GitCommandError
import time
import os

def commit_changes(repo_path: str, file_path: str, commit_message: str) -> Optional[str]:
    try:
        repo = Repo(repo_path)
        repo.git.add(file_path)
        repo.git.commit("-m", commit_message)
        print(f"Changes committed with message: {commit_message}")
        return repo.head.commit.hexsha
    except GitCommandError as e:
        print(f"Failed to commit changes: {e}")
        return None

def push_changes(repo_path: str, remote_name: str = "origin"):
    try:
        repo = Repo(repo_path)
        repo.git.push(remote_name)
        print(f"Changes pushed to {remote_name}")
    except GitCommandError as e:
        print(f"Failed to push changes: {e}")

def monitor_pipeline(github_token: str, repo_name: str, commit_sha: str):
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    while True:
        commit = repo.get_commit(sha=commit_sha)
        if commit.get_combined_status().state != "pending":
            break
        time.sleep(5)
    print(f"Pipeline status: {commit.get_combined_status().state}")

def main():
    repo_path = "<path-to-your-repo>"
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    commit_message = "Fix lint errors in probe0_lint_error.py"
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = "<username>/<repo-name>"

    commit_sha = commit_changes(repo_path, file_path, commit_message)
    if commit_sha is not None:
        push_changes(repo_path)
        monitor_pipeline(github_token, repo_name, commit_sha)

if __name__ == "__main__":
    main()