#!/usr/bin/env python3
"""
Governance Dashboard CLI - Phase 4 PR-5

Display 5-Agent Advisory Pipeline governance summary.

Usage:
    python governance_dashboard.py [--trace-id TRACE_ID] [--json]

Example:
    python governance_dashboard.py --trace-id abc123
    python governance_dashboard.py --json
"""
import sys
import argparse
import json

sys.path.insert(0, '/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator')

try:
    from governance_dashboard import (
        build_governance_dashboard,
        format_dashboard_text
    )
except ImportError as e:
    print("Error: Failed to import governance_dashboard module: %s" % e)
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def create_sample_state(trace_id: str = "sample-trace-001") -> dict:
    """
    Create a sample AgentState for demonstration.

    In production, this would be loaded from Redis or a database.
    """
    return {
        "trace_id": trace_id,
        "goal": "Implement feature X with proper error handling",
        "plan": ["Analyze requirements", "Write code", "Add tests", "Create PR"],
        "task_type": "feature_implementation",
        "agent_id": "orchestrator",
        "environment": "sandbox",

        "security_risk": "low",
        "security_compliant": True,
        "security_advisory": {
            "is_compliant": True,
            "overall_risk": "low",
            "findings": [],
            "recommendations": []
        },

        "governance_risk": "info",
        "governance_compliant": True,
        "governance_advisory": {
            "is_compliant": True,
            "overall_risk": "info",
            "findings": [],
            "recommendations": []
        },

        "cost_risk": "info",
        "cost_within_budget": True,
        "cost_advisory": {
            "is_compliant": True,
            "overall_risk": "info",
            "findings": [],
            "recommendations": []
        },

        "permission_risk": "info",
        "permission_granted": True,
        "permission_advisory": {
            "is_compliant": True,
            "overall_risk": "info",
            "findings": [],
            "recommendations": []
        },

        "reputation_level": "trusted",
        "reputation_score": 100,
        "reputation_advisory": {
            "agent_id": "orchestrator",
            "score": 100,
            "level": "trusted",
            "history": [],
            "recommendations": []
        }
    }


def display_dashboard(trace_id: str = None, output_json: bool = False) -> bool:
    """
    Display governance dashboard.

    Args:
        trace_id: Optional trace ID to display (uses sample if not provided)
        output_json: If True, output JSON instead of formatted text

    Returns:
        True if successful, False otherwise
    """
    try:
        state = create_sample_state(trace_id or "sample-trace-001")

        summary = build_governance_dashboard(state)

        if output_json:
            print(json.dumps(summary.to_dict(), indent=2))
        else:
            print(format_dashboard_text(summary))

        return True

    except Exception as e:
        print("Error: Failed to build governance dashboard: %s" % e)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Display Governance Dashboard - 5-Agent Advisory Summary'
    )
    parser.add_argument(
        '--trace-id',
        type=str,
        default=None,
        help='Trace ID to display (uses sample data if not provided)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of formatted text'
    )
    args = parser.parse_args()

    success = display_dashboard(trace_id=args.trace_id, output_json=args.json)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
