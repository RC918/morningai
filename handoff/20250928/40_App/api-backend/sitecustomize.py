"""
Customize Python's sys.path to include the repository root.

This ensures that the 'common' module can be imported from anywhere
within the api-backend directory, particularly during test collection.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
