# handoff/20250928/40_App/api-backend/src/probe3_syntax_trap_validation.py

def validate_syntax(data):
    if not data:
        return False
    result = check_syntax(data)
    return result