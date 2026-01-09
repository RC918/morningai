# handoff/20250928/40_App/api-backend/src/probe3_syntax_trap_validation.py

import json

def validate_probe3_syntax(data):
    try:
        parsed_data = json.loads(data)
        if "probe3" not in parsed_data:
            return False
        return True
    except json.JSONDecodeError:
        return False