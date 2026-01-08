"""
Probe 1 v6 - Test file for EPIC D GeneralCoder check_run annotations extraction validation.

This file intentionally contains lint errors to trigger CI failure.
The goal is to verify that:
1. check_run events are processed correctly
2. ci_check_suite_id is extracted from check_run.check_suite.id
3. Annotations API is called to get file paths
4. GeneralCoder receives multi-file context via ci_error_file_paths

DO NOT MERGE - This is a test vehicle only.
"""

from probe1_v6_utils import calculate_total, format_output


def main():
    """Main function with intentional lint error."""
    # Intentional lint error: undefined variable
    result = calculate_total(x, y, z)
    
    # Intentional lint error: unused variable
    unused_var = "this is unused"
    
    output = format_output(result)
    print(output)
    return result


if __name__ == "__main__":
    main()
