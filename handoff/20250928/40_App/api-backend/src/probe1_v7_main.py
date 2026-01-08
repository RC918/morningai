"""
Probe 1 v7 Test File - Main Module
Purpose: Validate ci_check_suite_id and ci_error_file_paths are passed to context
This file contains an intentional lint error for testing GeneralCoder multi-file fix.
"""

import sys  # F401: unused import - intentional lint error


def run_probe1_v7():
    """Run the probe test."""
    print("Probe 1 v7: Testing context key propagation")
    print("Expected: ci_check_suite_id in context_keys")
    print("Expected: ci_error_file_paths in context_keys")
    print("Expected: review_files_count > 0")
    return True


if __name__ == "__main__":
    run_probe1_v7()
