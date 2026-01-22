#!/usr/bin/env python3
"""
Test script to trigger DebateHook with a simulated HIGH risk plan.

This script creates a mock PlannerOutput with HIGH risk level and
passes it through DebateHook to verify the full flow:
1. DebateHook detects HIGH risk plan
2. DebateHook triggers DebateEngine.debate()
3. Debate result is saved to AGENT_INTERACTION memory with expires_at

Usage:
    cd ~/repos/morningai
    source .venv/bin/activate
    export PYTHONPATH="$PWD:$PWD/handoff/20250928/40_App/orchestrator:$PYTHONPATH"
    cd handoff/20250928/40_App/orchestrator
    python scripts/test_debate_hook.py

Expected logs:
    [DebateHook] Triggering debate for high-risk plan ...
    [DebateEngine] Starting debate on: ...
    [MemoryIntegration] Saved debate result

Blueprint Reference: F-6 DebateHook verification
"""

import logging
import sys
import uuid

# Configure logging to see all output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """Run DebateHook with a simulated HIGH risk plan."""
    logger.info("=" * 60)
    logger.info("Test DebateHook - F-6 Planner Agent Verification")
    logger.info("=" * 60)

    # Import here to ensure proper path setup
    try:
        from core.planner.planner_types import (
            PlannerOutput,
            PlanType,
            RiskLevel,
            RiskMetadata,
            TaskNode,
            TaskTree,
            TaskType,
        )
        from core.planner.model_tier_selection import DebateHook

        logger.info("Successfully imported DebateHook and PlannerOutput")
    except ImportError as e:
        logger.error(f"Failed to import: {e}")
        logger.error("Make sure PYTHONPATH includes the orchestrator directory")
        sys.exit(1)

    # Create a mock HIGH risk plan
    trace_id = f"test_hook_{uuid.uuid4().hex[:8]}"
    
    # Create task nodes with HIGH/CRITICAL risk levels
    task1 = TaskNode(
        task_id="task_1",
        task_type=TaskType.DEPLOY,
        description="Deploy critical infrastructure changes to production",
        risk_level=RiskLevel.HIGH,
        estimated_duration_minutes=30,
    )
    task2 = TaskNode(
        task_id="task_2",
        task_type=TaskType.CODE,
        description="Migrate database schema with breaking changes",
        risk_level=RiskLevel.CRITICAL,
        estimated_duration_minutes=60,
    )

    # Create task tree
    task_tree = TaskTree(nodes=[task1, task2])

    # Create HIGH risk plan
    plan = PlannerOutput(
        plan_id=f"plan_{trace_id}",
        plan_type=PlanType.DETAILED,
        goal="Deploy critical infrastructure changes with database migration",
        task_tree=task_tree,
        risk_metadata=RiskMetadata(
            overall_risk=RiskLevel.HIGH,
            requires_approval=False,
            risk_factors=["production deployment", "database migration", "breaking changes"],
        ),
    )

    logger.info(f"Created mock plan with trace_id: {trace_id}")
    logger.info(f"Plan goal: {plan.goal}")
    logger.info(f"Plan risk level: {plan.risk_metadata.overall_risk.value}")
    logger.info(f"Task count: {len(plan.task_tree.nodes)}")

    # Create DebateHook and process the plan
    hook = DebateHook(trace_id=trace_id)
    logger.info("Created DebateHook instance")

    logger.info("-" * 40)
    logger.info("Invoking DebateHook.on_plan_created()...")
    logger.info("-" * 40)

    try:
        modified_plan = hook.on_plan_created(plan)

        logger.info("-" * 40)
        logger.info("DebateHook completed!")
        logger.info(f"  Original requires_approval: False")
        logger.info(f"  Modified requires_approval: {modified_plan.risk_metadata.requires_approval}")

        if modified_plan.risk_metadata.requires_approval:
            logger.info("  -> Debate result requires human review!")
        else:
            logger.info("  -> Debate result does not require human review")

        logger.info("=" * 60)
        logger.info("VERIFICATION STEPS:")
        logger.info("1. Check logs for '[DebateHook] Triggering debate for high-risk plan'")
        logger.info("2. Check logs for '[DebateEngine] Starting debate on'")
        logger.info("3. Check logs for '[MemoryIntegration] Saved debate result'")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"DebateHook failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
