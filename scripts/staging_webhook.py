#!/usr/bin/env python3
"""
Staging Webhook Simulation CLI Tool

This tool simulates GitHub webhook events in staging by:
1. Fetching PR data from GitHub API
2. Constructing a valid task payload
3. Enqueuing it to the staging Redis queue

This solves the problem that GitHub App webhooks only point to production,
making it impossible to test webhook-triggered workflows in staging.

Usage:
    # Trigger a review task for a specific PR
    python scripts/staging_webhook.py --repo RC918/morningai --pr 3263

    # Dry run (show payload without enqueuing)
    python scripts/staging_webhook.py --repo RC918/morningai --pr 3263 --dry-run

    # Use custom Redis URL
    REDIS_URL=rediss://... python scripts/staging_webhook.py --repo RC918/morningai --pr 3263

Environment Variables:
    REDIS_URL: Redis connection URL (required for staging)
    GITHUB_TOKEN: GitHub token for API access (optional, uses gh CLI if not set)

Issue: #3265
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

try:
    import redis
    from rq import Queue
    from rq.serializers import JSONSerializer
except ImportError:
    print("Error: Required packages not installed. Run: pip install redis rq")
    sys.exit(1)


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def fetch_pr_data(repo: str, pr_number: int, token: Optional[str] = None) -> dict:
    """Fetch PR data from GitHub API."""
    import urllib.request
    import urllib.error

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "staging-webhook-cli"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"PR #{pr_number} not found in {repo}")
        elif e.code == 401:
            raise ValueError("GitHub authentication failed. Set GITHUB_TOKEN or run 'gh auth login'")
        else:
            raise ValueError(f"GitHub API error: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        raise ValueError(f"Network error: {e.reason}")


def construct_task_payload(pr_data: dict, repo: str) -> dict:
    """Construct a task payload matching the orchestrator format."""
    pr_number = pr_data["number"]
    pr_title = pr_data["title"]
    pr_url = pr_data["html_url"]
    head_sha = pr_data["head"]["sha"]

    task_id = f"staging-{uuid.uuid4().hex[:8]}-{pr_number}"

    question = f"Review PR #{pr_number}: {pr_title}"

    context = {
        "resource_id": pr_number,
        "resource_type": "pull_request",
        "url": pr_url,
        "head_sha": head_sha,
        "source": "staging_webhook_cli",
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "task_id": task_id,
        "question": question,
        "repo": repo,
        "task_type": "review",
        "context": context,
    }


def validate_payload(payload: dict) -> list[str]:
    """
    Validate task payload structure.

    Returns a list of validation errors (empty if valid).
    This provides lightweight self-validation without external dependencies.
    """
    errors = []

    required_fields = ["task_id", "question", "repo", "task_type", "context"]
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    if "context" in payload:
        context = payload["context"]
        context_fields = ["resource_id", "resource_type", "url", "head_sha", "source"]
        for field in context_fields:
            if field not in context:
                errors.append(f"Missing context field: {field}")

        if "resource_id" in context and not isinstance(context["resource_id"], int):
            errors.append("context.resource_id must be an integer")

        if "head_sha" in context:
            sha = context["head_sha"]
            if not isinstance(sha, str) or len(sha) != 40:
                errors.append("context.head_sha must be a 40-character hex string")

    return errors


def enqueue_task(redis_url: str, payload: dict, queue_name: str = "orchestrator") -> str:
    """
    Enqueue task to Redis queue.

    Uses string-based function reference to avoid importing worker module directly,
    which would trigger module-level initialization (Redis connections, Sentry, etc.)
    even in dry-run mode.
    """
    redis_client = redis.Redis.from_url(
        redis_url,
        decode_responses=False,
        socket_connect_timeout=10,
    )

    q = Queue(queue_name, connection=redis_client, serializer=JSONSerializer())

    job = q.enqueue(
        "redis_queue.worker.run_orchestrator_task",
        task_id=payload["task_id"],
        question=payload["question"],
        repo=payload["repo"],
        task_type=payload["task_type"],
        context=payload["context"],
        job_timeout=600,
        result_ttl=86400,
        failure_ttl=3600,
    )

    return job.id


def main():
    parser = argparse.ArgumentParser(
        description="Simulate GitHub webhook events in staging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Trigger a review task for PR #3263
    python scripts/staging_webhook.py --repo RC918/morningai --pr 3263

    # Dry run to see the payload
    python scripts/staging_webhook.py --repo RC918/morningai --pr 3263 --dry-run

    # Use staging Redis
    REDIS_URL=rediss://... python scripts/staging_webhook.py --repo RC918/morningai --pr 3263
        """
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in owner/repo format (e.g., RC918/morningai)"
    )
    parser.add_argument(
        "--pr",
        type=int,
        required=True,
        help="Pull request number"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show payload without enqueuing"
    )
    parser.add_argument(
        "--queue",
        default="orchestrator",
        help="Redis queue name (default: orchestrator)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    redis_url = os.environ.get("REDIS_URL")
    if not redis_url and not args.dry_run:
        print("Error: REDIS_URL environment variable is required")
        print("For staging: export REDIS_URL=rediss://...")
        sys.exit(1)

    print(f"Fetching PR #{args.pr} from {args.repo}...")
    token = get_github_token()
    if args.verbose:
        print(f"  Using GitHub token: {'yes' if token else 'no'}")

    try:
        pr_data = fetch_pr_data(args.repo, args.pr, token)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"  Title: {pr_data['title']}")
    print(f"  State: {pr_data['state']}")
    print(f"  Head SHA: {pr_data['head']['sha'][:12]}")

    payload = construct_task_payload(pr_data, args.repo)

    validation_errors = validate_payload(payload)
    if validation_errors:
        print("Error: Invalid payload structure:")
        for error in validation_errors:
            print(f"  - {error}")
        sys.exit(1)

    if args.verbose or args.dry_run:
        print("\nTask payload:")
        print(json.dumps(payload, indent=2, default=str))

    if args.dry_run:
        print("\n[DRY RUN] Task not enqueued")
        return

    print(f"\nEnqueuing task to '{args.queue}' queue...")
    try:
        job_id = enqueue_task(redis_url, payload, args.queue)
        print(f"  Job ID: {job_id}")
        print(f"  Task ID: {payload['task_id']}")
        print("\nTask enqueued successfully!")
        print(f"Monitor with: redis-cli -u $REDIS_URL HGETALL agent:task:{payload['task_id']}")
    except Exception as e:
        print(f"Error enqueuing task: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
