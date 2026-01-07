# Before linting
import os, sys
def foo(): 
    var='hello, world'
    print(var)
    return 1

# After linting
import os
import sys


def foo() -> int: 
    """
    Prints a greeting and returns 1.

    Returns:
        int: The return value. Always returns 1.
    """
    var = 'hello, world'
    print(var)
    return 1