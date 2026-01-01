#!/usr/bin/env python3
"""
SeniorCoder Staging Validation Test - File B

This file intentionally contains lint errors to trigger SeniorCoder
plan-execute-review flow in Staging environment.

DO NOT MERGE - This is a test PR for validation only.
"""
import json
import re


def test_intentional_lint_error_file_b():
    """Test with intentional lint error - unused imports."""
    data = {"key": "value"}
    return data


def test_another_function_file_b():
    """Another test function."""
    result = test_intentional_lint_error_file_b()
    assert result["key"] == "value"
