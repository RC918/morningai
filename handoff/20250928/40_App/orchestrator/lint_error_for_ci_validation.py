"""
Intentional lint errors to trigger CI failure for SeniorCoder validation.
This is NOT a test file - it's a utility module that will be checked by lint.

Purpose: Validate that CI failure triggers SeniorCoder auto-fix flow.
Expected: Ruff/flake8 lint check should fail, triggering SeniorCoder.

DO NOT MERGE - This is for staging validation only.
"""

import os
import sys
import json  # F401: unused import


def badly_formatted_function(x,y,z):  # E231: missing whitespace after ','
    unused_variable = "this is never used"  # F841: local variable assigned but never used
    result=x+y+z  # E225: missing whitespace around operator
    if result==0:  # E225: missing whitespace around operator
        pass
    return result


class bad_class_name:  # N801: class name should use CapWords convention
    def __init__(self):
        self.value = None
    
    def Method_With_Bad_Name(self):  # N802: function name should be lowercase
        x = 1
        y = 2
        return x + y


# Multiple statements on one line
x = 1; y = 2; z = 3  # E702: multiple statements on one line
