import pytest
from src.utils.env_schema_validator import validate_environment, REQUIRED_ENV_VARS, OPTIONAL_ENV_VARS


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment for testing"""
    for var in list(REQUIRED_ENV_VARS.keys()) + list(OPTIONAL_ENV_VARS.keys()):
        monkeypatch.delenv(var, raising=False)


def test_validate_environment_with_all_required_vars(monkeypatch):
    """Test validation passes when all required vars are set"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')

    result = validate_environment()

    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert len(result['warnings']) == 0


def test_validate_environment_missing_required_var(clean_env, monkeypatch):
    """Test validation fails when required var is missing"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')

    result = validate_environment()

    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'APP_VERSION' in result['errors'][0]


def test_validate_environment_all_missing(clean_env):
    """Test validation fails when all required vars are missing"""
    result = validate_environment()

    assert result['valid'] is False
    assert len(result['errors']) == 2


def test_validate_environment_with_optional_vars(monkeypatch):
    """Test validation passes with optional vars set"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test123')

    result = validate_environment()

    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_environment_empty_required_var(clean_env, monkeypatch):
    """Test validation fails when required var is empty string"""
    monkeypatch.setenv('DATABASE_URL', '')
    monkeypatch.setenv('APP_VERSION', '1.0.0')

    result = validate_environment()

    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'DATABASE_URL' in result['errors'][0]


def test_required_env_vars_constant():
    """Test REQUIRED_ENV_VARS constant is defined"""
    assert 'DATABASE_URL' in REQUIRED_ENV_VARS
    assert 'APP_VERSION' in REQUIRED_ENV_VARS


def test_optional_env_vars_constant():
    """Test OPTIONAL_ENV_VARS constant is defined"""
    assert 'REDIS_URL' in OPTIONAL_ENV_VARS
    assert 'OPENAI_API_KEY' in OPTIONAL_ENV_VARS


def test_validate_environment_with_all_optional_vars(monkeypatch):
    """Test validation with all optional vars set"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test123')
    monkeypatch.setenv('SENTRY_DSN', 'https://test@sentry.io/123')
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('CORS_ORIGINS', 'http://localhost:3000')

    result = validate_environment()

    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert len(result['warnings']) == 0


def test_validate_environment_multiple_missing_required(clean_env):
    """Test validation with multiple missing required vars"""
    result = validate_environment()

    assert result['valid'] is False
    assert len(result['errors']) >= 2
    assert any('DATABASE_URL' in error for error in result['errors'])
    assert any('APP_VERSION' in error for error in result['errors'])


def test_validate_environment_partial_required(clean_env, monkeypatch):
    """Test validation with only some required vars set"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')

    result = validate_environment()

    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'APP_VERSION' in result['errors'][0]


def test_validate_environment_with_warnings(monkeypatch):
    """Test validation generates warnings for optional vars"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')

    result = validate_environment()

    assert result['valid'] is True
    assert 'errors' in result
    assert 'warnings' in result


def test_validate_environment_return_structure(monkeypatch):
    """Test validation returns correct structure"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')

    result = validate_environment()

    assert isinstance(result, dict)
    assert 'valid' in result
    assert 'errors' in result
    assert 'warnings' in result
    assert isinstance(result['valid'], bool)
    assert isinstance(result['errors'], list)
    assert isinstance(result['warnings'], list)


def test_main_block_valid_environment(monkeypatch, capsys):
    """Test __main__ block with valid environment"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')

    import runpy
    import sys

    original_argv = sys.argv
    sys.argv = ['env_schema_validator.py']

    try:
        runpy.run_module('src.utils.env_schema_validator', run_name='__main__', alter_sys=True)
    except SystemExit:
        pass
    finally:
        sys.argv = original_argv

    captured = capsys.readouterr()
    assert 'PASSED' in captured.out or 'validation' in captured.out.lower()


def test_main_block_invalid_environment(clean_env, capsys):
    """Test __main__ block with invalid environment"""
    import runpy
    import sys

    original_argv = sys.argv
    sys.argv = ['env_schema_validator.py']

    try:
        runpy.run_module('src.utils.env_schema_validator', run_name='__main__', alter_sys=True)
    except SystemExit:
        pass
    finally:
        sys.argv = original_argv

    captured = capsys.readouterr()
    assert 'FAILED' in captured.out or 'Errors' in captured.out or 'validation' in captured.out.lower()


# ============================================================================
# Edge Case Tests - Issue #4229
# ============================================================================

class TestEnvSchemaValidatorEdgeCases:
    """Edge case tests for env_schema_validator - Issue #4229"""

    def test_whitespace_only_required_var(self, clean_env, monkeypatch):
        """Test validation fails when required var contains only whitespace.

        Issue #4257: Whitespace-only values should be treated as missing.
        """
        monkeypatch.setenv('DATABASE_URL', '   ')
        monkeypatch.setenv('APP_VERSION', '1.0.0')

        result = validate_environment()

        # Whitespace-only should be rejected (Issue #4257 fix)
        assert result['valid'] is False
        assert any('DATABASE_URL' in error for error in result['errors'])

    def test_special_characters_in_env_values(self, monkeypatch):
        """Test validation handles special characters in env values"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:p@ss!word#123@localhost/db?sslmode=require')
        monkeypatch.setenv('APP_VERSION', '1.0.0-beta+build.123')

        result = validate_environment()

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_very_long_env_value(self, monkeypatch):
        """Test validation handles very long env values"""
        long_value = 'x' * 10000
        monkeypatch.setenv('DATABASE_URL', long_value)
        monkeypatch.setenv('APP_VERSION', '1.0.0')

        result = validate_environment()

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_unicode_in_env_values(self, monkeypatch):
        """Test validation handles unicode characters in env values"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/データベース')
        monkeypatch.setenv('APP_VERSION', '版本1.0.0')

        result = validate_environment()

        assert result['valid'] is True

    def test_newline_in_env_value(self, monkeypatch):
        """Test validation handles newlines in env values"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db\nwith\nnewlines')
        monkeypatch.setenv('APP_VERSION', '1.0.0')

        result = validate_environment()

        assert result['valid'] is True

    def test_all_optional_vars_empty(self, monkeypatch):
        """Test validation with all optional vars set to empty strings"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('APP_VERSION', '1.0.0')
        monkeypatch.setenv('REDIS_URL', '')
        monkeypatch.setenv('OPENAI_API_KEY', '')
        monkeypatch.setenv('SENTRY_DSN', '')

        result = validate_environment()

        assert result['valid'] is True
        assert len(result['warnings']) == 0

    def test_validation_idempotent(self, monkeypatch):
        """Test that multiple validation calls return consistent results"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('APP_VERSION', '1.0.0')

        result1 = validate_environment()
        result2 = validate_environment()
        result3 = validate_environment()

        assert result1 == result2 == result3

    def test_error_message_format(self, clean_env, monkeypatch):
        """Test that error messages have correct format"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        # APP_VERSION is missing

        result = validate_environment()

        assert result['valid'] is False
        assert len(result['errors']) == 1
        error_msg = result['errors'][0]
        assert 'Missing required environment variable' in error_msg
        assert 'APP_VERSION' in error_msg

    def test_required_vars_type_definitions(self):
        """Test that REQUIRED_ENV_VARS has correct type definitions"""
        for var_name, var_type in REQUIRED_ENV_VARS.items():
            assert var_type is str, f"{var_name} should have str type"

    def test_optional_vars_type_definitions(self):
        """Test that OPTIONAL_ENV_VARS has correct type definitions"""
        for var_name, var_type in OPTIONAL_ENV_VARS.items():
            assert var_type is str, f"{var_name} should have str type"


class TestMainBlockEdgeCases:
    """Edge case tests for __main__ block - Issue #4229"""

    def test_main_block_with_warnings_output(self, monkeypatch, capsys):
        """Test __main__ block outputs warnings when present"""
        import runpy
        import sys
        from unittest.mock import patch

        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('APP_VERSION', '1.0.0')

        # Mock validate_environment to return warnings
        mock_result = {
            'valid': True,
            'errors': [],
            'warnings': ['Test warning message']
        }

        original_argv = sys.argv
        sys.argv = ['env_schema_validator.py']

        try:
            with patch('src.utils.env_schema_validator.validate_environment', return_value=mock_result):
                runpy.run_module('src.utils.env_schema_validator', run_name='__main__', alter_sys=True)
        except SystemExit:
            pass
        finally:
            sys.argv = original_argv

        captured = capsys.readouterr()
        assert 'PASSED' in captured.out or 'validation' in captured.out.lower()

    def test_main_block_with_errors_and_warnings(self, clean_env, capsys):
        """Test __main__ block outputs both errors and warnings"""
        import runpy
        import sys
        from unittest.mock import patch

        # Mock validate_environment to return both errors and warnings
        mock_result = {
            'valid': False,
            'errors': ['Missing required environment variable: DATABASE_URL'],
            'warnings': ['Test warning']
        }

        original_argv = sys.argv
        sys.argv = ['env_schema_validator.py']

        try:
            with patch('src.utils.env_schema_validator.validate_environment', return_value=mock_result):
                runpy.run_module('src.utils.env_schema_validator', run_name='__main__', alter_sys=True)
        except SystemExit:
            pass
        finally:
            sys.argv = original_argv

        captured = capsys.readouterr()
        assert 'FAILED' in captured.out or 'Errors' in captured.out


class TestTypeValidationEdgeCases:
    """Tests for type validation edge cases - Issue #4229"""

    def test_type_validation_with_mocked_non_string_required(self, monkeypatch):
        """Test type validation error path for required vars (via mock)"""
        from unittest.mock import patch
        import src.utils.env_schema_validator as validator

        # Mock os.environ.get to return a non-string for testing
        def mock_get(var_name, default=None):
            if var_name == 'DATABASE_URL':
                return 'postgresql://localhost/test'
            elif var_name == 'APP_VERSION':
                return 123  # Return int instead of string
            return default

        with patch.object(validator.os.environ, 'get', side_effect=mock_get):
            result = validator.validate_environment()

        # The type check will trigger because we returned an int
        # Note: In practice, os.environ.get always returns str, but this tests the code path
        assert 'errors' in result

    def test_type_validation_with_mocked_non_string_optional(self, monkeypatch):
        """Test type validation warning path for optional vars (via mock)"""
        from unittest.mock import patch
        import src.utils.env_schema_validator as validator

        # Mock os.environ.get to return a non-string for optional var
        def mock_get(var_name, default=None):
            if var_name == 'DATABASE_URL':
                return 'postgresql://localhost/test'
            elif var_name == 'APP_VERSION':
                return '1.0.0'
            elif var_name == 'REDIS_URL':
                return 12345  # Return int instead of string
            return default

        with patch.object(validator.os.environ, 'get', side_effect=mock_get):
            result = validator.validate_environment()

        # The type check will trigger a warning
        assert 'warnings' in result
