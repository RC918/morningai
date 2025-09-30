import os, sys
ROOT = os.path.dirname(__file__)
SRC  = os.path.join(ROOT, "handoff/20250928/40_App/api-backend/src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
