# Shim module for backward compatibility
# Tech Debt #4: Moved to src/phases/phase7_startup.py

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
phases_dir = os.path.join(current_dir, 'handoff', '20250928', '40_App', 'api-backend', 'src', 'phases')

if phases_dir not in sys.path:
    sys.path.append(phases_dir)

try:
    from phase7_startup import *
except ImportError:
    from src.phases.phase7_startup import *
