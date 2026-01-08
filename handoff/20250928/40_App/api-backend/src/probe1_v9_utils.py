"""
Probe 1 v9 Test File - Utils Module
Purpose: Validate PR #3695 fix - branch extraction from ci_failure_context
This file contains an intentional lint error for testing GeneralCoder multi-file fix.

Expected behavior after PR #3695:
- Orchestrator should log: '[Orchestrator] Set branch from ci_failure_context'
- GeneralCoder should NOT fail with 'Missing repo or branch'
- GeneralCoder should log: '[GENERAL_CODER_ATTEMPT]'
- Both files should be fixed
"""

import os  # F401: unused import - intentional lint error for testing


def get_probe1_v9_config():
    """Return probe configuration."""
    return {
        "name": "probe1_v9",
        "purpose": "validate PR #3695 branch extraction fix",
        "expected_behavior": [
            "Orchestrator sets branch from ci_failure_context",
            "GeneralCoder does NOT fail with Missing repo or branch",
            "GeneralCoder attempts to fix both files",
        ],
    }
