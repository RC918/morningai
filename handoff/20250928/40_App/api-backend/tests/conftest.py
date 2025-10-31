"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and makes fixtures
from the fixtures/ directory available to all tests.
"""

# Enable fixtures from fixtures/ directory
pytest_plugins = [
    "tests.fixtures.auth",
    "tests.fixtures.database",
]
