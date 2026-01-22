#!/usr/bin/env python3
"""
Verify KNOWLEDGE_BASE quality for Reviewer Agent feedback storage.

This script queries the KNOWLEDGE_BASE layer to:
1. List all stored review_feedback entries
2. Display metadata (pr_number, repo, verdict, severity)
3. Verify data quality and completeness

Usage:
    cd ~/repos/morningai
    source .venv/bin/activate
    export PYTHONPATH="$PWD:$PWD/handoff/20250928/40_App/orchestrator:$PYTHONPATH"
    cd handoff/20250928/40_App/orchestrator
    python scripts/verify_knowledge_base.py

For Render environment:
    cd ~/project/src
    source .venv/bin/activate
    export PYTHONPATH="$PWD:$PWD/handoff/20250928/40_App/orchestrator:$PYTHONPATH"
    cd handoff/20250928/40_App/orchestrator
    python scripts/verify_knowledge_base.py

Blueprint Reference: B-13 Review Feedback Loop verification
"""

import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """Query and display KNOWLEDGE_BASE review feedback entries."""
    logger.info("=" * 70)
    logger.info("KNOWLEDGE_BASE Quality Verification - B-13 Reviewer Agent")
    logger.info("=" * 70)

    # Import here to ensure proper path setup
    try:
        from memory.memory_integration import search_review_patterns
        from memory.memory_v2 import MemoryLayer, MemoryV2

        logger.info("Successfully imported memory modules")
    except ImportError as e:
        logger.error(f"Failed to import: {e}")
        logger.error("Make sure PYTHONPATH includes the orchestrator directory")
        sys.exit(1)

    # Method 1: Use search_review_patterns with a broad query
    logger.info("-" * 50)
    logger.info("Method 1: Using search_review_patterns()")
    logger.info("-" * 50)

    # Use a generic query to find any review patterns
    patterns = search_review_patterns(
        query="def function code review",
        limit=20,
        min_similarity=0.0,  # Get all matches regardless of similarity
    )

    if patterns:
        logger.info(f"Found {len(patterns)} review patterns:")
        for i, pattern in enumerate(patterns, 1):
            logger.info(f"\n  [{i}] Key: {pattern.get('key', 'N/A')}")
            logger.info(f"      PR: {pattern.get('repo', 'N/A')}#{pattern.get('pr_number', 'N/A')}")
            logger.info(f"      Verdict: {pattern.get('verdict', 'N/A')}")
            logger.info(f"      Severity: {pattern.get('severity', 'N/A')}")
            logger.info(f"      Blocker Count: {pattern.get('blocker_count', 0)}")
            logger.info(f"      Files: {len(pattern.get('file_paths', []))}")
            logger.info(f"      Comments: {len(pattern.get('review_comments', []))}")
            logger.info(f"      Similarity: {pattern.get('similarity', 'N/A')}")
            logger.info(f"      Saved At: {pattern.get('saved_at', 'N/A')}")
    else:
        logger.info("No review patterns found via search_review_patterns()")

    # Method 2: Direct KNOWLEDGE_BASE query
    logger.info("-" * 50)
    logger.info("Method 2: Direct KNOWLEDGE_BASE query")
    logger.info("-" * 50)

    try:
        memory = MemoryV2()
        
        # Search for all review_feedback entries
        entries = memory.search(
            query="review feedback verdict",
            layers=[MemoryLayer.KNOWLEDGE_BASE],
            limit=50,
        )

        review_entries = [e for e in entries if e.metadata.get("type") == "review_feedback"]

        if review_entries:
            logger.info(f"Found {len(review_entries)} review_feedback entries:")
            
            # Quality metrics
            verdicts = {}
            severities = {}
            total_blockers = 0
            repos = set()

            for entry in review_entries:
                meta = entry.metadata
                verdict = meta.get("verdict", "unknown")
                severity = meta.get("severity", "unknown")
                
                verdicts[verdict] = verdicts.get(verdict, 0) + 1
                severities[severity] = severities.get(severity, 0) + 1
                total_blockers += meta.get("blocker_count", 0)
                
                repo = meta.get("repo")
                if repo:
                    repos.add(repo)

                logger.info(f"\n  Entry: {entry.key}")
                logger.info(f"    PR: {meta.get('repo', 'N/A')}#{meta.get('pr_number', 'N/A')}")
                logger.info(f"    Verdict: {verdict}")
                logger.info(f"    Severity: {severity}")
                logger.info(f"    Blockers: {meta.get('blocker_count', 0)}")
                logger.info(f"    Files: {meta.get('file_count', 0)}")
                logger.info(f"    Comments: {meta.get('comment_count', 0)}")
                logger.info(f"    Has expires_at: {entry.expires_at is not None}")

            # Summary statistics
            logger.info("\n" + "=" * 50)
            logger.info("QUALITY SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Total entries: {len(review_entries)}")
            logger.info(f"Unique repos: {len(repos)}")
            logger.info(f"Total blockers: {total_blockers}")
            logger.info(f"Verdict distribution: {verdicts}")
            logger.info(f"Severity distribution: {severities}")

            # Quality checks
            logger.info("\n" + "-" * 50)
            logger.info("QUALITY CHECKS")
            logger.info("-" * 50)

            # Check 1: All entries should NOT have expires_at (permanent storage)
            entries_with_expiry = [e for e in review_entries if e.expires_at is not None]
            if entries_with_expiry:
                logger.warning(f"  [WARN] {len(entries_with_expiry)} entries have expires_at (should be None for KNOWLEDGE_BASE)")
            else:
                logger.info("  [OK] All entries have no expires_at (permanent storage)")

            # Check 2: All entries should have required metadata
            missing_metadata = []
            for entry in review_entries:
                meta = entry.metadata
                if not meta.get("pr_number") or not meta.get("repo"):
                    missing_metadata.append(entry.key)
            
            if missing_metadata:
                logger.warning(f"  [WARN] {len(missing_metadata)} entries missing pr_number or repo")
            else:
                logger.info("  [OK] All entries have pr_number and repo")

            # Check 3: Verdict should be valid
            valid_verdicts = {"APPROVE", "REQUEST_CHANGES", "COMMENT"}
            invalid_verdicts = [v for v in verdicts.keys() if v not in valid_verdicts]
            if invalid_verdicts:
                logger.warning(f"  [WARN] Invalid verdicts found: {invalid_verdicts}")
            else:
                logger.info("  [OK] All verdicts are valid")

        else:
            logger.info("No review_feedback entries found in KNOWLEDGE_BASE")
            logger.info("\nThis could mean:")
            logger.info("  1. No PRs have been reviewed yet")
            logger.info("  2. REVIEW_FEEDBACK_ENABLED is not set to true")
            logger.info("  3. Memory v2 is not properly configured")

    except Exception as e:
        logger.error(f"Failed to query KNOWLEDGE_BASE: {e}")
        import traceback
        traceback.print_exc()

    logger.info("\n" + "=" * 70)
    logger.info("Verification complete")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
