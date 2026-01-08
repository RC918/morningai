"""
Probe 1 v7 Test File - Utils Module (v8 - Post PR #3693 fix)
Purpose: Validate that review_files from Annotations is NOT overridden by error_summary
This file contains an intentional lint error for testing GeneralCoder multi-file fix.
"""

import os  # F401: unused import - intentional lint error for testing


def get_probe1_v7_config():
    """Return probe configuration."""
    return {
        "name": "probe1_v7",
        "purpose": "validate context passing",
        "expected_context_keys": [
            "ci_check_suite_id",
            "ci_error_file_paths",
        ],
    }
