"""
Path utilities for planner events and other shared file paths.

This module provides utilities for resolving file paths relative to the repository root,
with support for environment variable overrides and multiple execution contexts.
"""

import os

from common.utils.repo_root import get_repo_root


def resolve_planner_events_path(
    env_var: str = 'PLANNER_EVENTS_FILE',
    default_rel: str = 'tools/agent_eval/data/planner_runs.jsonl'
) -> str:
    """
    Resolve planner_runs.jsonl path using repo root detection.

    This function is used by both the LLM planner adapter (for writing events)
    and the monitoring CLI tool (for reading events).

    Resolution order:
    1. If env_var is set and is an absolute path, use it as-is
    2. If env_var is set and is relative, resolve it relative to repo root
    3. Otherwise, use default_rel resolved relative to repo root

    Args:
        env_var: Environment variable name to check for override
        default_rel: Default relative path from repo root

    Returns:
        Absolute path to planner events file

    Examples:
        >>> # Default usage
        >>> path = resolve_planner_events_path()
        >>> # /home/ubuntu/repos/morningai/tools/agent_eval/data/planner_runs.jsonl

        >>> # With environment variable override
        >>> os.environ['PLANNER_EVENTS_FILE'] = '/custom/path/events.jsonl'
        >>> path = resolve_planner_events_path()
        >>> # /custom/path/events.jsonl
    """
    events_file = os.environ.get(env_var, default_rel)

    # If absolute path, use as-is
    if os.path.isabs(events_file):
        return events_file

    # Resolve relative to repo root
    repo_root = get_repo_root()
    return str(repo_root / events_file)
