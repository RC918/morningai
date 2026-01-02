"""
Intentional lint errors to trigger CI failure for SeniorCoder validation.
This file is placed in api-backend/src which IS checked by Ruff lint.

Purpose: Validate that CI failure triggers SeniorCoder auto-fix flow.
Expected: Ruff lint check should fail, triggering SeniorCoder.

DO NOT MERGE - This is for staging validation only.
"""

import os
import sys
import json


def badly_formatted_function(x,y,z):
    unused_variable = "this is never used"
    result=x+y+z
    if result==0:
        pass
    return result


class bad_class_name:
    def __init__(self):
        self.value = None
    
    def Method_With_Bad_Name(self):
        x = 1
        y = 2
        return x + y


x = 1; y = 2; z = 3

# Test run 5 - 2026-01-02 15:10 UTC
# Testing get_pr_files() fix (PR #3507 merged and deployed)
import re  # F401: unused import
import time  # F401: unused import

def another_bad_function():
    unused = "test"  # F841: unused variable
    return None

# Test run 6 - 2026-01-02 16:32 UTC
# Validating CiFailureContext (PR #3511 merged and deployed)
# Expected: AutoFixer uses CI evidence instead of ReviewerAgent judgment
import collections  # F401: unused import
import functools  # F401: unused import

def ci_failure_context_test():
    test_var = "unused"  # F841: unused variable
    another_unused = 123  # F841: unused variable
    return None

# Test run 7 - 2026-01-02 17:31 UTC
# Re-validating CiFailureContext with new SHA (bypassing dedup TTL)
# Issue #3513 created to track dedup refinement
import itertools  # F401: unused import
import operator  # F401: unused import

def dedup_bypass_test():
    bypass_var = "new sha"  # F841: unused variable
    return None

# Test run 8 - 2026-01-02 18:31 UTC
# Validating PR #3514 dedup fix (check_suite_id added to dedup key)
# Expected: ci_failure_actionable logs instead of ci_failure_skip_dedup
import typing  # F401: unused import
import dataclasses  # F401: unused import

def dedup_fix_validation_test():
    validation_var = "PR #3514 deployed"  # F841: unused variable
    check_suite_id_test = 12345  # F841: unused variable
    return None

# Test run 9 - 2026-01-02 19:32 UTC
# Validating PR #3515 CiFailureContext JSON serialization fix
# Expected: Enqueue succeeds (no "Object of type CiFailureContext is not JSON serializable")
# Expected: Worker processes job and AutoFixer executes with CI evidence
import abc  # F401: unused import
import copy  # F401: unused import

def serialization_fix_validation_test():
    to_dict_test = "PR #3515 deployed"  # F841: unused variable
    from_dict_test = "JSON serializable"  # F841: unused variable
    return None

# Test run 10 - 2026-01-02 20:24 UTC
# Validating PR #3516 ci_monitor_node fast path fix
# Expected: ci_monitor_node skips GitHub API call when ci_failure_trigger=True
# Expected: Router sees ci_state="failure" and triggers [CI_FAILURE_ROUTER_SHORT_CIRCUIT]
# Expected: AutoFixer executes with CI evidence
import enum  # F401: unused import
import weakref  # F401: unused import

def ci_monitor_fast_path_validation_test():
    fast_path_test = "PR #3516 deployed"  # F841: unused variable
    ci_state_preserved = "failure"  # F841: unused variable
    skip_api_call = True  # F841: unused variable
    return None
