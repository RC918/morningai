#!/usr/bin/env python3
"""
Environment Configuration Testing
Tests various environment validation scenarios including edge cases
"""

import os
import sys
import tempfile
from datetime import datetime

sys.path.append('.')

from env_schema_validator import env_schema_validator

def test_missing_required_variables():
    """Test 1: Missing required environment variables"""
    print("🔧 Test 1: Missing Required Variables")
    print("=" * 50)
    
    original_values = {}
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'FLASK_ENV']
    
    for var in required_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]
    
    try:
        validation_result = env_schema_validator.validate_environment()
        
        print(f"📊 Validation passed: {validation_result.valid}")
        print(f"📊 Errors: {len(validation_result.errors)}")
        print(f"📊 Missing required: {validation_result.missing_required}")
        
        for var, value in original_values.items():
            os.environ[var] = value
        
        if not validation_result.valid and validation_result.missing_required:
            print("✅ PASSED: Missing required variables correctly detected")
            return True
        else:
            print("❌ FAILED: Should have failed with missing required variables")
            return False
            
    except Exception as e:
        for var, value in original_values.items():
            os.environ[var] = value
        print(f"❌ FAILED: Exception during validation: {e}")
        return False

def test_invalid_format_variables():
    """Test 2: Invalid format environment variables"""
    print("\n🔧 Test 2: Invalid Format Variables")
    print("=" * 50)
    
    invalid_configs = {
        'DATABASE_URL': 'not-a-valid-url',
        'DEBUG': 'maybe',  # Should be true/false
        'PORT': 'not-a-number',
        'TIMEOUT': '-5'  # Negative timeout
    }
    
    original_values = {}
    for var, invalid_value in invalid_configs.items():
        if var in os.environ:
            original_values[var] = os.environ[var]
        os.environ[var] = invalid_value
    
    try:
        validation_result = env_schema_validator.validate_environment()
        
        print(f"📊 Validation passed: {validation_result.valid}")
        print(f"📊 Invalid values: {validation_result.invalid_values}")
        
        for var in invalid_configs:
            if var in original_values:
                os.environ[var] = original_values[var]
            elif var in os.environ:
                del os.environ[var]
        
        if not validation_result.valid and validation_result.invalid_values:
            print("✅ PASSED: Invalid format variables correctly detected")
            return True
        else:
            print("❌ FAILED: Should have failed with invalid format variables")
            return False
            
    except Exception as e:
        for var in invalid_configs:
            if var in original_values:
                os.environ[var] = original_values[var]
            elif var in os.environ:
                del os.environ[var]
        print(f"❌ FAILED: Exception during validation: {e}")
        return False

def test_edge_case_values():
    """Test 3: Edge case environment values"""
    print("\n🔧 Test 3: Edge Case Values")
    print("=" * 50)
    
    edge_cases = {
        'EMPTY_VAR': '',
        'WHITESPACE_VAR': '   ',
        'VERY_LONG_VAR': 'x' * 10000,
        'SPECIAL_CHARS': '!@#$%^&*()[]{}|\\:";\'<>?,./`~',
        'UNICODE_VAR': '测试中文变量值🚀',
        'NULL_STRING': 'null',
        'UNDEFINED_STRING': 'undefined'
    }
    
    original_values = {}
    for var, value in edge_cases.items():
        if var in os.environ:
            original_values[var] = os.environ[var]
        os.environ[var] = value
    
    try:
        validation_result = env_schema_validator.validate_environment()
        config_summary = env_schema_validator.get_config_summary()
        
        print(f"📊 Validation passed: {validation_result.valid}")
        print(f"📊 Warnings: {len(validation_result.warnings)}")
        print(f"📊 Config variables processed: {len(config_summary.get('variables', {}))}")
        
        for var in edge_cases:
            if var in original_values:
                os.environ[var] = original_values[var]
            elif var in os.environ:
                del os.environ[var]
        
        print("✅ PASSED: Edge case values handled gracefully")
        return True
        
    except Exception as e:
        for var in edge_cases:
            if var in original_values:
                os.environ[var] = original_values[var]
            elif var in os.environ:
                del os.environ[var]
        print(f"❌ FAILED: Exception with edge cases: {e}")
        return False

def test_startup_blocking():
    """Test 4: Startup blocking with invalid configuration"""
    print("\n🔧 Test 4: Startup Blocking")
    print("=" * 50)
    
    try:
        from phase7_startup import Phase7Startup
        
        original_db_url = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        startup = Phase7Startup()
        
        try:
            import asyncio
            asyncio.run(startup.initialize())
            
            if original_db_url:
                os.environ['DATABASE_URL'] = original_db_url
            print("❌ FAILED: Startup should have been blocked")
            return False
            
        except RuntimeError as e:
            if "Environment validation failed" in str(e):
                if original_db_url:
                    os.environ['DATABASE_URL'] = original_db_url
                print("✅ PASSED: Startup correctly blocked with invalid environment")
                return True
            else:
                if original_db_url:
                    os.environ['DATABASE_URL'] = original_db_url
                print(f"❌ FAILED: Wrong error type: {e}")
                return False
        except Exception as e:
            if original_db_url:
                os.environ['DATABASE_URL'] = original_db_url
            print(f"❌ FAILED: Unexpected exception: {e}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Could not test startup blocking: {e}")
        return False

def test_configuration_matrix():
    """Test 5: Configuration matrix across environments"""
    print("\n🔧 Test 5: Configuration Matrix")
    print("=" * 50)
    
    environments = {
        'development': {
            'FLASK_ENV': 'development',
            'DEBUG': 'true',
            'DATABASE_URL': 'sqlite:///dev.db'
        },
        'staging': {
            'FLASK_ENV': 'staging',
            'DEBUG': 'false',
            'DATABASE_URL': 'postgresql://staging:pass@localhost/staging'
        },
        'production': {
            'FLASK_ENV': 'production',
            'DEBUG': 'false',
            'DATABASE_URL': 'postgresql://prod:pass@localhost/prod'
        }
    }
    
    results = {}
    original_values = {}
    
    for env_name, config in environments.items():
        for var in config:
            if var in os.environ and var not in original_values:
                original_values[var] = os.environ[var]
    
    try:
        for env_name, config in environments.items():
            print(f"   Testing {env_name} environment...")
            
            for var, value in config.items():
                os.environ[var] = value
            
            validation_result = env_schema_validator.validate_environment()
            results[env_name] = {
                'valid': validation_result.valid,
                'errors': len(validation_result.errors),
                'warnings': len(validation_result.warnings)
            }
            
            print(f"     {env_name}: {'✅' if validation_result.valid else '❌'} "
                  f"(errors: {len(validation_result.errors)}, warnings: {len(validation_result.warnings)})")
        
        for var, value in original_values.items():
            os.environ[var] = value
        
        all_valid = all(result['valid'] for result in results.values())
        
        if all_valid:
            print("✅ PASSED: All environment configurations valid")
            return True
        else:
            print("❌ FAILED: Some environment configurations invalid")
            return False
            
    except Exception as e:
        for var, value in original_values.items():
            os.environ[var] = value
        print(f"❌ FAILED: Configuration matrix test error: {e}")
        return False

def run_environment_configuration_tests():
    """Run all environment configuration tests"""
    print("🧪 Environment Configuration Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    result1 = test_missing_required_variables()
    test_results.append(("Missing Required Variables", result1))
    
    result2 = test_invalid_format_variables()
    test_results.append(("Invalid Format Variables", result2))
    
    result3 = test_edge_case_values()
    test_results.append(("Edge Case Values", result3))
    
    result4 = test_startup_blocking()
    test_results.append(("Startup Blocking", result4))
    
    result5 = test_configuration_matrix()
    test_results.append(("Configuration Matrix", result5))
    
    print("\n" + "=" * 80)
    print("🎯 ENVIRONMENT CONFIGURATION TEST RESULTS")
    print("=" * 80)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall Result: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("🎉 ALL ENVIRONMENT CONFIGURATION TESTS PASSED! Configuration validation is robust.")
    else:
        print("⚠️  Some configuration tests failed. Environment validation needs improvement.")
    
    return passed_tests == len(test_results)

if __name__ == "__main__":
    run_environment_configuration_tests()
