"""
Shared constants for the orchestrator module.

This module contains constants that are used across multiple files to prevent
drift and ensure consistency. It is intentionally lightweight with no imports
or side effects to avoid circular import issues.

Issue: Self-Trigger Loop Prevention
"""

# Self-review marker used to identify orchestrator-generated reviews
# When the orchestrator posts a review, it includes this hidden HTML comment.
# The webhook normalizer checks for this marker and skips PR_REVIEWED events
# that contain it, preventing the orchestrator from re-triggering itself.
#
# WARNING: This constant is used in both github_api.py (for adding the marker)
# and normalizer.py (for detecting the marker). If you change this value,
# both files will automatically use the new value since they import from here.
MORNINGAI_REVIEW_MARKER = "<!-- morningai:autogen-review -->"

# Redis TTL for review deduplication keys (24 hours)
# Reviews are deduplicated per PR + head SHA + reviewer version
# TTL ensures keys don't accumulate indefinitely
REVIEW_DEDUP_TTL_SECONDS = 86400  # 24 hours

# Reviewer version for deduplication key
# Increment this when review logic changes significantly to allow
# re-reviewing PRs that were reviewed with an older version
REVIEWER_VERSION = "v1"

# Labels for documentation PRs
# These labels are used by the orchestrator when creating docs PRs.
# The webhook normalizer checks for these labels and skips PR events
# that have them, preventing self-trigger loops.
#
# WARNING: These constants are used in both graph.py (for adding labels)
# and normalizer.py (for detecting labels). If you change these values,
# both files will automatically use the new values since they import from here.
LABEL_ORCHESTRATOR_DOCS = "orchestrator-docs"
LABEL_ORCHESTRATOR_DOCS_TEST = "orchestrator-docs-test"
LABEL_ORCHESTRATOR_APPROVED = "orchestrator-approved"
