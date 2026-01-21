# Shim module for backward compatibility
# Tech Debt #4: Moved to src/phases/phase4_meta_agent.py

import sys
import os

# Add the specific phases directory to sys.path
# This allows importing the module directly despite parent directories having numeric names
current_dir = os.path.dirname(os.path.abspath(__file__))
phases_dir = os.path.join(current_dir, 'handoff', '20250928', '40_App', 'api-backend', 'src', 'phases')

if phases_dir not in sys.path:
    sys.path.append(phases_dir)

# Now we can import directly
try:
    from phase4_meta_agent import *
except ImportError:
    # If the above fails, try importing via the src package if available
    # This covers cases where 'src' is already in path
    from src.phases.phase4_meta_agent import *
