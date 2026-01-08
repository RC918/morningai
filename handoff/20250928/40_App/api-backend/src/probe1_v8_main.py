"""
Probe 1 v8 Test File - Main Module
Purpose: Validate PR #3693 fix - review_files from Annotations NOT overridden by error_summary
This file contains an intentional lint error for testing GeneralCoder multi-file fix.

Expected behavior after PR #3693:
- Fixer should log: '[Fixer] Skipping error_summary extraction - review_files already set from Annotations'
- review_files_count should be 2 (not 1)
- GeneralCoder should detect both files
"""

import sys  # F401: unused import - intentional lint error for testing


def run_probe1_v8():
    """Run the probe test."""
    print("Probe 1 v8: Testing PR #3693 fix")
    print("Expected: review_files from Annotations NOT overridden")
    print("Expected: review_files_count = 2 (not 1)")
    return True


if __name__ == "__main__":
    run_probe1_v8()
