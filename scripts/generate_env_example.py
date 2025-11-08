#!/usr/bin/env python3
"""
Generate .env.example from Pydantic settings class

This script reads the Settings class from common/config/settings.py
and generates a .env.example file with all variables, their types,
descriptions, and default values.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config.settings import Settings
from pydantic.fields import FieldInfo


def generate_env_example():
    """Generate .env.example file from Settings class"""
    
    output_lines = [
        "# MorningAI Environment Variables",
        "# Generated from common/config/settings.py",
        "#",
        "# Copy this file to .env and fill in your actual values",
        "# DO NOT commit .env to version control",
        "",
        "# ============================================================================",
        "# REQUIRED VARIABLES (must be set)",
        "# ============================================================================",
        "",
    ]
    
    settings_fields = Settings.model_fields
    
    required_fields = []
    optional_fields = []
    
    for field_name, field_info in settings_fields.items():
        if field_info.is_required():
            required_fields.append((field_name, field_info))
        else:
            optional_fields.append((field_name, field_info))
    
    for field_name, field_info in required_fields:
        env_var_name = field_name.upper()
        description = field_info.description or "No description"
        
        output_lines.append(f"# {description}")
        
        field_type = field_info.annotation
        type_name = getattr(field_type, "__name__", str(field_type))
        output_lines.append(f"# Type: {type_name}")
        
        if field_info.alias:
            output_lines.append(f"# Alias: {field_info.alias}")
        
        if hasattr(field_info, "min_length") and field_info.metadata:
            for constraint in field_info.metadata:
                if hasattr(constraint, "min_length"):
                    output_lines.append(f"# Min length: {constraint.min_length}")
        
        output_lines.append(f"{env_var_name}=")
        output_lines.append("")
    
    output_lines.extend([
        "# ============================================================================",
        "# OPTIONAL VARIABLES (have defaults)",
        "# ============================================================================",
        "",
    ])
    
    for field_name, field_info in optional_fields:
        env_var_name = field_name.upper()
        description = field_info.description or "No description"
        default_value = field_info.default
        
        output_lines.append(f"# {description}")
        
        field_type = field_info.annotation
        type_name = getattr(field_type, "__name__", str(field_type))
        output_lines.append(f"# Type: {type_name}")
        
        if default_value is not None and default_value != "":
            output_lines.append(f"# Default: {default_value}")
        
        if field_info.alias:
            output_lines.append(f"# Alias: {field_info.alias}")
        
        if default_value is not None and default_value != "":
            output_lines.append(f"# {env_var_name}={default_value}")
        else:
            output_lines.append(f"# {env_var_name}=")
        
        output_lines.append("")
    
    env_example_path = project_root / ".env.example"
    with open(env_example_path, "w") as f:
        f.write("\n".join(output_lines))
    
    print(f"✅ Generated {env_example_path}")
    print(f"   - {len(required_fields)} required variables")
    print(f"   - {len(optional_fields)} optional variables")
    print(f"   - Total: {len(settings_fields)} variables")


if __name__ == "__main__":
    generate_env_example()
