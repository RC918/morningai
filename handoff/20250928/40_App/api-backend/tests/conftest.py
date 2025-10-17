"""
Pytest configuration for API backend tests.

This module sets up the Python path and provides common fixtures for all tests.
"""
import sys
import os
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

orchestrator_dir = Path(__file__).parent.parent.parent / "orchestrator"
if orchestrator_dir.exists() and str(orchestrator_dir) not in sys.path:
    sys.path.insert(0, str(orchestrator_dir))
