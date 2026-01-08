"""Probe 1 Test File - Main Module

EPIC D GeneralCoder Multi-file Validation Test
This file imports from probe1_utils.py to test GeneralCoder's import relationship understanding.

DO NOT MERGE - This is a test vehicle for validating D-1b multi-file support.
"""

from probe1_utils import calculate_total, format_output


def process_data(data):
    """Process data using utility functions.
    
    Intentional lint error: F821 undefined name 'validator'
    """
    if validator.is_valid(data):
        total = calculate_total(data)
        return format_output(total)
    return None


def main():
    """Main entry point.
    
    Intentional lint error: F821 undefined name 'config'
    """
    data = config.load_data()
    result = process_data(data)
    print(result)


if __name__ == "__main__":
    main()
