"""
Probe 1 v7 Test File - Main Module (v8 - Post PR #3693 fix)
Purpose: Validate that review_files from Annotations is NOT overridden by error_summary
This file contains an intentional lint error for testing GeneralCoder multi-file fix.
"""

import sys  # F401: unused import - intentional lint error for testing


def run_probe1_v7():
    """Run the probe test."""
    print("Probe 1 v7 (v8): Testing PR #3693 fix")
    print("Expected: review_files from Annotations NOT overridden")
    print("Expected: review_files_count = 2 (not 1)")
    return True


if __name__ == "__main__":
    run_probe1_v7()
