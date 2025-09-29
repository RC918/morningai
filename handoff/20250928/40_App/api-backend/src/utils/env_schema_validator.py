#!/usr/bin/env python3
"""Environment Schema Validator for Phase 8 Backend"""

import os
from typing import Dict, Any, Optional

REQUIRED_ENV_VARS = {
    'DATABASE_URL': str,
    'APP_VERSION': str,
}

OPTIONAL_ENV_VARS = {
    'REDIS_URL': str,
    'OPENAI_API_KEY': str,
    'SENTRY_DSN': str,
    'FLASK_ENV': str,
    'CORS_ORIGINS': str,
}

def validate_environment() -> Dict[str, Any]:
    """Validate environment variables against schema"""
    errors = []
    warnings = []
    
    for var_name, var_type in REQUIRED_ENV_VARS.items():
        value = os.environ.get(var_name)
        if not value:
            errors.append(f"Missing required environment variable: {var_name}")
        elif var_type == str and not isinstance(value, str):
            errors.append(f"Invalid type for {var_name}: expected {var_type.__name__}")
    
    for var_name, var_type in OPTIONAL_ENV_VARS.items():
        value = os.environ.get(var_name)
        if value and var_type == str and not isinstance(value, str):
            warnings.append(f"Invalid type for {var_name}: expected {var_type.__name__}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }

if __name__ == "__main__":
    result = validate_environment()
    print(f"Environment validation: {'PASSED' if result['valid'] else 'FAILED'}")
    if result['errors']:
        print("Errors:")
        for error in result['errors']:
            print(f"  - {error}")
    if result['warnings']:
        print("Warnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")
