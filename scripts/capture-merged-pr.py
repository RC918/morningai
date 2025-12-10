#!/usr/bin/env python3
"""
Capture merged PR data and append to raw feed.

This script is triggered by GitHub Actions when a PR is merged to main.
It captures PR metadata and appends it to docs/pr-changelog-raw.yaml
for later curation into the main pr-changelog.yaml.

Usage:
    python scripts/capture-merged-pr.py --pr-number 1234

Environment variables:
    GITHUB_TOKEN: GitHub token for API access (provided by GitHub Actions)
    GITHUB_REPOSITORY: Repository in owner/repo format (provided by GitHub Actions)
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# GitHub API URL
GITHUB_API_URL = "https://api.github.com"

# Maximum number of files to consider when determining primary path
MAX_FILES_TO_CONSIDER = 10

# Regex pattern for conventional commit format: type(scope): description
CONVENTIONAL_COMMIT_PATTERN = re.compile(r"^(\w+)(?:\(([^)]+)\))?:")


def _parse_conventional_commit(title: str) -> tuple[str | None, str | None]:
    """Parse conventional commit format from PR title.

    Returns:
        Tuple of (type, scope) where either can be None if not found.

    Examples:
        "feat(owner-console): add feature" -> ("feat", "owner-console")
        "fix: bug fix" -> ("fix", None)
        "random title" -> (None, None)
    """
    match = CONVENTIONAL_COMMIT_PATTERN.match(title)
    if match:
        return match.group(1), match.group(2)
    return None, None


def get_pr_data(repo: str, pr_number: int, token: str) -> dict[str, Any]:
    """Fetch PR data from GitHub API."""
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MorningAI-Changelog-Bot",
    }

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def extract_category_from_title(title: str) -> str:
    """Extract category hint from PR title using conventional commit format.

    Examples:
        "feat(owner-console): add feature" -> "owner-console"
        "fix(orchestrator): fix bug" -> "orchestrator"
        "docs: update readme" -> "docs"
    """
    pr_type, scope = _parse_conventional_commit(title)
    if scope:
        return scope
    if pr_type:
        return pr_type
    return "uncategorized"


def extract_pr_type(title: str) -> str:
    """Extract PR type from title.

    Examples:
        "feat(owner-console): add feature" -> "feat"
        "fix(orchestrator): fix bug" -> "fix"
    """
    pr_type, _ = _parse_conventional_commit(title)
    if pr_type:
        return pr_type
    return "other"


def get_changed_paths(repo: str, pr_number: int, token: str) -> list[str]:
    """Get list of changed file paths from PR."""
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MorningAI-Changelog-Bot",
    }

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        files = json.loads(response.read().decode())
        return [f["filename"] for f in files[:MAX_FILES_TO_CONSIDER]]


def load_raw_feed(raw_feed_path: Path) -> dict[str, Any]:
    """Load existing raw feed or create new structure."""
    if raw_feed_path.exists():
        with open(raw_feed_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                return data
    return {
        "raw_feed": [],
        "metadata": {
            "description": "Auto-captured PR data from GitHub. Review and curate into pr-changelog.yaml.",
            "last_updated": None,
        },
    }


def save_raw_feed(raw_feed_path: Path, data: dict[str, Any]) -> None:
    """Save raw feed to YAML file."""
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    with open(raw_feed_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def pr_exists_in_feed(feed: dict[str, Any], pr_number: int) -> bool:
    """Check if PR already exists in raw feed."""
    for entry in feed.get("raw_feed", []):
        if entry.get("number") == pr_number:
            return True
    return False


def _get_primary_path(changed_paths: list[str]) -> str:
    """Get the most common parent directory from changed paths.

    Uses Counter to find the most frequently occurring parent directory,
    which provides better signal than just using the first file's directory.
    """
    if not changed_paths:
        return ""

    # Count occurrences of each parent directory
    parent_dirs = [str(Path(p).parent) for p in changed_paths]
    counter = Counter(parent_dirs)

    # Return the most common parent directory
    most_common = counter.most_common(1)
    if most_common:
        return most_common[0][0]
    return ""


def create_raw_entry(pr_data: dict[str, Any], changed_paths: list[str]) -> dict[str, Any]:
    """Create a raw feed entry from PR data."""
    title = pr_data["title"]
    labels = [label["name"] for label in pr_data.get("labels", [])]

    # Extract primary path (most commonly changed directory)
    primary_path = _get_primary_path(changed_paths)

    return {
        "number": pr_data["number"],
        "title": title,
        "type": extract_pr_type(title),
        "scope": extract_category_from_title(title),
        "labels": labels,
        "primary_path": primary_path,
        "changed_files_count": pr_data.get("changed_files", 0),
        "merged_at": pr_data.get("merged_at", ""),
        "merged_by": pr_data.get("merged_by", {}).get("login", ""),
        "author": pr_data.get("user", {}).get("login", ""),
        "html_url": pr_data.get("html_url", ""),
        "body_preview": (pr_data.get("body") or "")[:200],
        "curated": False,  # Flag to track if this has been added to pr-changelog.yaml
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Capture merged PR data and append to raw feed"
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        required=True,
        help="PR number to capture",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be captured without saving",
    )
    args = parser.parse_args()

    # Get environment variables
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return 1

    if not repo:
        print("Error: GITHUB_REPOSITORY environment variable not set")
        return 1

    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    raw_feed_path = repo_root / "docs" / "pr-changelog-raw.yaml"

    print(f"Capturing PR #{args.pr_number} from {repo}")

    # Fetch PR data
    try:
        pr_data = get_pr_data(repo, args.pr_number, token)
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR data: HTTP {e.code} - {e.reason}")
        return 1
    except urllib.error.URLError as e:
        print(f"Error fetching PR data: {e.reason}")
        return 1

    # Check if PR was actually merged
    if not pr_data.get("merged"):
        print(f"PR #{args.pr_number} is not merged, skipping")
        return 0

    # Get changed files
    try:
        changed_paths = get_changed_paths(repo, args.pr_number, token)
    except urllib.error.HTTPError as e:
        print(f"Warning: Could not fetch changed files: HTTP {e.code} - {e.reason}")
        changed_paths = []
    except urllib.error.URLError as e:
        print(f"Warning: Could not fetch changed files: {e.reason}")
        changed_paths = []

    # Load existing raw feed
    raw_feed = load_raw_feed(raw_feed_path)

    # Check for duplicates
    if pr_exists_in_feed(raw_feed, args.pr_number):
        print(f"PR #{args.pr_number} already exists in raw feed, skipping")
        return 0

    # Create entry
    entry = create_raw_entry(pr_data, changed_paths)

    if args.dry_run:
        print("\nDRY RUN - Would add entry:")
        print(yaml.dump(entry, allow_unicode=True, default_flow_style=False))
        return 0

    # Append to raw feed
    raw_feed["raw_feed"].insert(0, entry)  # Insert at beginning (newest first)

    # Save
    save_raw_feed(raw_feed_path, raw_feed)
    print(f"Successfully captured PR #{args.pr_number}")
    print(f"  Title: {entry['title']}")
    print(f"  Type: {entry['type']}")
    print(f"  Scope: {entry['scope']}")
    print(f"  Labels: {entry['labels']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
