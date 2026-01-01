#!/usr/bin/env python3
"""
SeniorCoder Staging Validation Test - File A

This file intentionally contains lint errors to trigger SeniorCoder
plan-execute-review flow in Staging environment.

DO NOT MERGE - This is a test PR for validation only.
"""
import os
import sys


def test_intentional_lint_error_file_a():
    """Test with intentional lint error - unused import."""
    x = 1
    y = 2
    return x + y


def test_another_function_file_a():
    """Another test function."""
    result = test_intentional_lint_error_file_a()
    assert result == 3
