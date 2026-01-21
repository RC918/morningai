# Shim module for backward compatibility
# Tech Debt #4: Moved to src/phases/phase5_data_intelligence.py

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
phases_dir = os.path.join(current_dir, 'handoff', '20250928', '40_App', 'api-backend', 'src', 'phases')

if phases_dir not in sys.path:
    sys.path.append(phases_dir)

try:
    from phase5_data_intelligence import *
except ImportError:
    from src.phases.phase5_data_intelligence import *
