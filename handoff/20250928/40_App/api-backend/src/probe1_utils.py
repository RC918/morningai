"""Probe 1 Test File - Utils Module

EPIC D GeneralCoder Multi-file Validation Test
This file contains intentional lint errors to test GeneralCoder's multi-file fix capability.

DO NOT MERGE - This is a test vehicle for validating D-1b multi-file support.
"""


def calculate_total(items):
    """Calculate total from items list.
    
    Intentional lint error: F821 undefined name 'sum_values'
    """
    result = sum_values(items)
    return result


def format_output(value):
    """Format output value.
    
    Intentional lint error: F821 undefined name 'formatter'
    """
    return formatter.format(value)
