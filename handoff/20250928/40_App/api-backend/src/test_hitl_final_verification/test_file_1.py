# Before Fix
import os
import sys
import json  # F401: 'json' imported but unused

def test_function():
    print("This is a test function")

# After Fix
import os
import sys

def test_function():
    print("This is a test function")