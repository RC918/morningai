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

import logging
import sys

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
        from memory.memory_integration import list_review_feedback, search_review_patterns

        logger.info("Successfully imported memory modules")
    except ImportError as e:
        logger.error(f"Failed to import: {e}")
        logger.error("Make sure PYTHONPATH includes the orchestrator directory")
        sys.exit(1)

    # Method 1: Use list_review_feedback (direct query, no vector similarity)
    # Issue #4305: This is the recommended method for verification
    logger.info("-" * 50)
    logger.info("Method 1: Using list_review_feedback() [RECOMMENDED]")
    logger.info("-" * 50)
    logger.info("This method queries by metadata type directly, bypassing vector similarity.")

    feedback_entries = list_review_feedback(limit=50)

    if feedback_entries:
        logger.info(f"Found {len(feedback_entries)} review feedback entries:")
        for i, entry in enumerate(feedback_entries, 1):
            logger.info(f"\n  [{i}] Key: {entry.get('key', 'N/A')}")
            logger.info(f"      PR: {entry.get('repo', 'N/A')}#{entry.get('pr_number', 'N/A')}")
            logger.info(f"      Verdict: {entry.get('verdict', 'N/A')}")
            logger.info(f"      Severity: {entry.get('severity', 'N/A')}")
            logger.info(f"      Blocker Count: {entry.get('blocker_count', 0)}")
            logger.info(f"      Files: {len(entry.get('file_paths', []))}")
            logger.info(f"      Comments: {len(entry.get('review_comments', []))}")
            logger.info(f"      Created At: {entry.get('created_at', 'N/A')}")
            logger.info(f"      Saved At: {entry.get('saved_at', 'N/A')}")
    else:
        logger.info("No review feedback found via list_review_feedback()")

    # Method 2: Use search_review_patterns with a broad query (vector similarity)
    logger.info("-" * 50)
    logger.info("Method 2: Using search_review_patterns() [Vector Similarity]")
    logger.info("-" * 50)
    logger.info("This method uses vector similarity search with threshold 0.7.")

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

    # Method 3: Quality Summary (using data from Method 1)
    # This section provides quality metrics and checks based on the direct query results
    logger.info("-" * 50)
    logger.info("Method 3: Quality Summary and Checks")
    logger.info("-" * 50)

    if feedback_entries:
        # Quality metrics
        verdicts = {}
        severities = {}
        total_blockers = 0
        repos = set()

        for entry in feedback_entries:
            verdict = entry.get("verdict", "unknown")
            severity = entry.get("severity", "unknown")

            verdicts[verdict] = verdicts.get(verdict, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
            total_blockers += entry.get("blocker_count", 0)

            repo = entry.get("repo")
            if repo:
                repos.add(repo)

        # Summary statistics
        logger.info("=" * 50)
        logger.info("QUALITY SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total entries: {len(feedback_entries)}")
        logger.info(f"Unique repos: {len(repos)}")
        logger.info(f"Total blockers: {total_blockers}")
        logger.info(f"Verdict distribution: {verdicts}")
        logger.info(f"Severity distribution: {severities}")

        # Quality checks
        logger.info("\n" + "-" * 50)
        logger.info("QUALITY CHECKS")
        logger.info("-" * 50)

        # Check 1: All entries should have required metadata
        missing_metadata = []
        for entry in feedback_entries:
            if not entry.get("pr_number") or not entry.get("repo"):
                missing_metadata.append(entry.get("key", "unknown"))

        if missing_metadata:
            logger.warning(f"  [WARN] {len(missing_metadata)} entries missing pr_number or repo")
        else:
            logger.info("  [OK] All entries have pr_number and repo")

        # Check 2: Verdict should be valid
        # Valid verdicts per memory_integration.py:903 (lowercase)
        valid_verdicts = {"approve", "request_changes", "comment", "blocked", "unknown"}
        invalid_verdicts = [v for v in verdicts.keys() if v not in valid_verdicts]
        if invalid_verdicts:
            logger.warning(f"  [WARN] Invalid verdicts found: {invalid_verdicts}")
        else:
            logger.info("  [OK] All verdicts are valid")

        # Check 3: Compare Method 1 vs Method 2 results
        logger.info("\n" + "-" * 50)
        logger.info("METHOD COMPARISON")
        logger.info("-" * 50)
        logger.info(f"  Method 1 (Direct Query): {len(feedback_entries)} entries")
        logger.info(f"  Method 2 (Vector Search): {len(patterns)} entries")
        if len(feedback_entries) > len(patterns):
            logger.info("  [INFO] Direct query found more entries than vector search.")
            logger.info("         This is expected - vector search requires similarity threshold.")

    else:
        logger.info("No review_feedback entries found in KNOWLEDGE_BASE")
        logger.info("\nThis could mean:")
        logger.info("  1. No PRs have been reviewed yet")
        logger.info("  2. REVIEW_FEEDBACK_ENABLED is not set to true")
        logger.info("  3. Memory v2 is not properly configured")

    logger.info("\n" + "=" * 70)
    logger.info("Verification complete")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
