"""
Probe 1 v8 Test File - Utils Module
Purpose: Validate PR #3693 fix - review_files from Annotations NOT overridden by error_summary
This file contains an intentional lint error for testing GeneralCoder multi-file fix.

Expected behavior after PR #3693:
- Fixer should log: '[Fixer] Skipping error_summary extraction - review_files already set from Annotations'
- review_files_count should be 2 (not 1)
- GeneralCoder should detect both files
"""

import os  # F401: unused import - intentional lint error for testing


def get_probe1_v8_config():
    """Return probe configuration."""
    return {
        "name": "probe1_v8",
        "purpose": "validate PR #3693 review_files fix",
        "expected_behavior": [
            "Fixer skips error_summary extraction",
            "review_files_count = 2",
            "GeneralCoder detects both files",
        ],
    }
