#!/usr/bin/env python3
"""
Generate .env.example from config/env.schema.yaml
Ensures .env.example stays in sync with schema
"""

import yaml
import sys
from datetime import datetime
from pathlib import Path

def generate_env_example():
    """Generate .env.example from schema"""
    
    schema_path = Path(__file__).parent.parent / 'config' / 'env.schema.yaml'
    
    if not schema_path.exists():
        print(f"❌ Schema not found at {schema_path}")
        sys.exit(1)
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    lines = [
        "# ============================================================================",
        "# Morning AI Environment Configuration",
        "# ============================================================================",
        f"# Auto-generated from config/env.schema.yaml",
        f"# Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "#",
        "# Security Levels:",
        "#   - critical: Must be kept secret, never commit to git",
        "#   - secret: Sensitive data, use secure storage",
        "#   - public: Safe to share, configuration only",
        "#",
        "# Required variables are marked with [REQUIRED]",
        "# Optional variables show their default values",
        "#",
        "# For local development setup, see: /docs/config/env_schema.md",
        "# ============================================================================",
        ""
    ]
    
    by_category = {}
    for var_name, var_config in sorted(schema['fields'].items()):
        category = var_config.get('category', 'Uncategorized')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append((var_name, var_config))
    
    for category in sorted(by_category.keys()):
        lines.append("")
        lines.append(f"# {category}")
        lines.append("# " + "=" * 78)
        lines.append("")
        
        for var_name, var_config in by_category[category]:
            description = var_config.get('description', '')
            security = var_config.get('security_level', 'public')
            required = var_config.get('required', False)
            
            if description:
                lines.append(f"# {description}")
            
            if required:
                lines.append(f"# Security: {security} [REQUIRED]")
            else:
                lines.append(f"# Security: {security}")
            
            if var_config.get('example'):
                lines.append(f"# Example: {var_config['example']}")
            
            if var_config.get('default') is not None:
                default = var_config['default']
                lines.append(f"{var_name}={default}")
            elif var_config.get('type') == 'secret':
                lines.append(f"# {var_name}=your-secret-key-here")
            else:
                lines.append(f"# {var_name}=")
            
            lines.append("")
    
    output_path = Path(__file__).parent.parent / '.env.example'
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Generated .env.example with {len(schema['fields'])} variables")
    print(f"   Total categories: {len(by_category)}")
    print(f"   Output: {output_path}")

if __name__ == '__main__':
    generate_env_example()
