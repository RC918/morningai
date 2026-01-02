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

# Test run 3 - 2026-01-02 06:48 UTC
# Testing webhook dedup fix (PR #3485 merged and deployed)
import re  # F401: unused import
import time  # F401: unused import

def another_bad_function():
    unused = "test"  # F841: unused variable
    return None
