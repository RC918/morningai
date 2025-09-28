def open_pr(patch:str):
    print(f"[GitHub] Opened PR with patch: {patch[:40]}...")
    return {"url": "https://github.com/RC918/morningai/pull/mock"}

def read_ci_status(pr_url:str):
    print(f"[GitHub] Read CI for {pr_url}: success")
    return "success", []
