"""
Test file with intentional lint errors to trigger CI failure.
This is for SeniorCoder validation - DO NOT MERGE.

Purpose: Validate that CI failure triggers auto-fix flow via webhook.
Expected: Ruff lint check should fail, triggering SeniorCoder plan-execute-review.

Branch: test/* (not devin/*) to bypass normalizer exclusion rule.
Staging Webhook ID: 589262487

Trigger: logs_url fix validation (PR #3439) - 2026-01-01T11:29
"""

import os
import sys
import json  # unused import - F401


def badly_formatted_function(x,y,z):  # E501 line too long if we add more, missing spaces after commas
    unused_variable = "this is never used"  # F841 local variable assigned but never used
    result=x+y+z  # E225 missing whitespace around operator
    if result==0:  # E225 missing whitespace around operator
        pass
    return result


class test_class:  # N801 class name should use CapWords convention
    def __init__(self):
        self.value = None
    
    def Method_With_Bad_Name(self):  # N802 function name should be lowercase
        x = 1
        y = 2
        return x + y


# Intentional undefined name error
# result = undefined_function()  # F821 undefined name - commented out to avoid runtime error

# Multiple statements on one line
x = 1; y = 2; z = 3  # E702 multiple statements on one line

# Comparison to None
value = None
if value == None:  # E711 comparison to None should be 'if cond is None:'
    pass

# Comparison to True
flag = True
if flag == True:  # E712 comparison to True should be 'if cond is True:' or 'if cond:'
    pass
