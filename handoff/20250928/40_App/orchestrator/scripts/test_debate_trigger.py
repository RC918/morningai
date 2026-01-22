#!/usr/bin/env python3
"""
Test script to trigger a debate and verify Memory Consolidation fix.

This script directly calls DebateEngine.debate() to:
1. Trigger a test debate
2. Verify save_debate_result() is called with expires_at
3. Create an AGENT_INTERACTION memory entry for consolidation to process

Usage:
    cd handoff/20250928/40_App/orchestrator
    python scripts/test_debate_trigger.py

Expected logs:
    [DebateEngine] Starting debate on: ...
    [MemoryIntegration] Saved debate result ... expires_at=...

Blueprint Reference: G-2 Memory Consolidation verification
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
    """Run a test debate to verify Memory Consolidation fix."""
    logger.info("=" * 60)
    logger.info("Test Debate Trigger - G-2 Memory Consolidation Verification")
    logger.info("=" * 60)

    # Import here to ensure proper path setup
    try:
        from core.planner.debate_engine import (
            DebateCategory,
            DebateEngine,
            DebateTopic,
        )

        logger.info("Successfully imported DebateEngine")
    except ImportError as e:
        logger.error(f"Failed to import DebateEngine: {e}")
        logger.error("Make sure PYTHONPATH includes the orchestrator directory")
        sys.exit(1)

    # Create a test topic
    trace_id = f"test_debate_{uuid.uuid4().hex[:8]}"
    topic = DebateTopic(
        question="Should we implement feature X using approach A or approach B?",
        context={
            "test": True,
            "purpose": "G-2 Memory Consolidation verification",
            "trace_id": trace_id,
        },
        risk_level="high",
        category=DebateCategory.STRATEGY,
        constraints=["Must be completed within 1 sprint"],
        success_criteria=["Code quality maintained", "Performance not degraded"],
    )

    logger.info(f"Created test topic with trace_id: {trace_id}")
    logger.info(f"Topic question: {topic.question}")

    # Create engine with enable_llm=False for faster testing
    # This uses template-based arguments instead of LLM calls
    engine = DebateEngine(trace_id=trace_id, enable_llm=False)
    logger.info("Created DebateEngine with enable_llm=False (template mode)")

    # Run the debate
    logger.info("Starting debate...")
    logger.info("-" * 40)

    try:
        result = engine.debate(topic)

        logger.info("-" * 40)
        logger.info("Debate completed successfully!")
        logger.info(f"  Outcome: {result.decision.outcome.value}")
        logger.info(f"  Confidence: {result.decision.confidence:.2f}")
        logger.info(f"  Rounds completed: {result.rounds_completed}")
        logger.info(f"  Debate time: {result.debate_time_ms:.2f}ms")
        logger.info(f"  Requires human review: {result.decision.requires_human_review}")

        logger.info("=" * 60)
        logger.info("VERIFICATION STEPS:")
        logger.info("1. Check Render logs for '[MemoryIntegration] Saved debate result'")
        logger.info("2. Verify the log contains 'expires_at' field")
        logger.info("3. After 18-24 hours, check consolidation logs for")
        logger.info("   'Scanned N expiring memories' where N > 0")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Debate failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
