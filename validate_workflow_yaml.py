#!/usr/bin/env python3
"""
Validate YAML syntax for GitHub Actions workflow files
"""

import yaml
import sys
import os

def validate_yaml_file(file_path):
    """Validate YAML syntax for a given file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        parsed = yaml.safe_load(content)
        
        print(f"✅ YAML file '{file_path}' is valid")
        print(f"📋 Parsed structure keys: {list(parsed.keys()) if parsed else 'None'}")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error in '{file_path}':")
        print(f"   Error: {e}")
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            print(f"   Line: {mark.line + 1}, Column: {mark.column + 1}")
        return False
        
    except Exception as e:
        print(f"❌ Error reading file '{file_path}': {e}")
        return False

def main():
    """Main validation function"""
    workflow_file = ".github/workflows/env-diagnose.yml"
    
    if not os.path.exists(workflow_file):
        print(f"❌ Workflow file '{workflow_file}' not found")
        return False
    
    print(f"🔍 Validating YAML syntax for: {workflow_file}")
    print("=" * 50)
    
    return validate_yaml_file(workflow_file)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
