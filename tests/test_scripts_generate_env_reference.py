"""
Unit tests for scripts/generate-env-reference.py

Tests the environment reference documentation generation functionality.
"""

import pytest
from pathlib import Path
import sys
import yaml
import importlib.util
import os

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

script_path = Path(__file__).parent.parent / 'scripts' / 'generate-env-reference.py'
spec = importlib.util.spec_from_file_location("gen_env_ref_mod", script_path)
gen_env_ref_mod = importlib.util.module_from_spec(spec)

from unittest.mock import Mock
mock_repo_root = Mock()
mock_repo_root.get_repo_root.return_value = Path('/tmp/test_repo')
sys.modules['repo_root_utils'] = mock_repo_root

spec.loader.exec_module(gen_env_ref_mod)


class TestLoadSchema:
    """Test schema loading functionality."""

    def test_load_schema_success(self, tmp_path):
        """Test successful schema loading."""
        schema_data = {
            'version': '1.0',
            'fields': {
                'TEST_VAR': {
                    'category': 'Testing',
                    'description': 'Test variable',
                    'required': True,
                    'type': 'string'
                }
            }
        }

        schema_file = tmp_path / 'schema.yaml'
        with open(schema_file, 'w', encoding='utf-8') as f:
            yaml.dump(schema_data, f)

        result = gen_env_ref_mod.load_schema(schema_file)

        assert result == schema_data
        assert result['version'] == '1.0'
        assert 'TEST_VAR' in result['fields']

    def test_load_schema_empty_file(self, tmp_path):
        """Test loading empty schema file."""
        schema_file = tmp_path / 'empty.yaml'
        schema_file.write_text('')

        result = gen_env_ref_mod.load_schema(schema_file)

        assert result is None

    def test_load_schema_missing_file(self, tmp_path):
        """Test loading non-existent schema file raises error."""
        schema_file = tmp_path / 'nonexistent.yaml'

        with pytest.raises(FileNotFoundError):
            gen_env_ref_mod.load_schema(schema_file)


class TestCategorizeFields:
    """Test field categorization functionality."""

    def test_categorize_fields_basic(self):
        """Test basic field categorization."""
        fields = {
            'DB_URL': {'category': 'Database', 'type': 'url'},
            'API_KEY': {'category': 'Security', 'type': 'secret'},
            'LOG_LEVEL': {'category': 'Application', 'type': 'string'},
        }

        result = gen_env_ref_mod.categorize_fields(fields)

        assert 'Database' in result
        assert 'Security' in result
        assert 'Application' in result
        assert len(result['Database']) == 1
        assert result['Database'][0][0] == 'DB_URL'

    def test_categorize_fields_multiple_in_category(self):
        """Test categorization with multiple fields in same category."""
        fields = {
            'DB_URL': {'category': 'Database', 'type': 'url'},
            'DB_HOST': {'category': 'Database', 'type': 'string'},
            'DB_PORT': {'category': 'Database', 'type': 'integer'},
        }

        result = gen_env_ref_mod.categorize_fields(fields)

        assert len(result['Database']) == 3
        var_names = [item[0] for item in result['Database']]
        assert 'DB_URL' in var_names
        assert 'DB_HOST' in var_names
        assert 'DB_PORT' in var_names

    def test_categorize_fields_default_category(self):
        """Test that fields without category go to 'Other'."""
        fields = {
            'UNKNOWN_VAR': {'type': 'string'},
        }

        result = gen_env_ref_mod.categorize_fields(fields)

        assert 'Other' in result
        assert result['Other'][0][0] == 'UNKNOWN_VAR'


class TestFormatType:
    """Test type formatting functionality."""

    def test_format_type_string(self):
        """Test formatting string type."""
        var_config = {'type': 'string'}
        result = gen_env_ref_mod.format_type(var_config)
        assert result == 'string'

    def test_format_type_integer(self):
        """Test formatting integer type."""
        var_config = {'type': 'integer'}
        result = gen_env_ref_mod.format_type(var_config)
        assert result == 'integer'

    def test_format_type_boolean(self):
        """Test formatting boolean type."""
        var_config = {'type': 'boolean'}
        result = gen_env_ref_mod.format_type(var_config)
        assert result == 'boolean'

    def test_format_type_with_choices(self):
        """Test formatting type with choices."""
        var_config = {'type': 'string', 'choices': ['debug', 'info', 'warning', 'error']}
        result = gen_env_ref_mod.format_type(var_config)
        assert result == 'string (debug, info, warning, error)'

    def test_format_type_default(self):
        """Test formatting with no type specified defaults to string."""
        var_config = {}
        result = gen_env_ref_mod.format_type(var_config)
        assert result == 'string'


class TestFormatDefault:
    """Test default value formatting functionality."""

    def test_format_default_none(self):
        """Test formatting None default."""
        var_config = {'default': None}
        result = gen_env_ref_mod.format_default(var_config)
        assert result == '-'

    def test_format_default_missing(self):
        """Test formatting when default is not specified."""
        var_config = {}
        result = gen_env_ref_mod.format_default(var_config)
        assert result == '-'

    def test_format_default_boolean_true(self):
        """Test formatting boolean True default."""
        var_config = {'default': True}
        result = gen_env_ref_mod.format_default(var_config)
        assert result == 'true'

    def test_format_default_boolean_false(self):
        """Test formatting boolean False default."""
        var_config = {'default': False}
        result = gen_env_ref_mod.format_default(var_config)
        assert result == 'false'

    def test_format_default_string(self):
        """Test formatting string default."""
        var_config = {'default': 'INFO'}
        result = gen_env_ref_mod.format_default(var_config)
        assert result == 'INFO'

    def test_format_default_integer(self):
        """Test formatting integer default."""
        var_config = {'default': 15}
        result = gen_env_ref_mod.format_default(var_config)
        assert result == '15'

    def test_format_default_with_env_specific(self):
        """Test formatting with environment-specific values."""
        var_config = {
            'default': 15,
            'environment_specific': {
                'production': 15,
                'development': 30,
                'ci': 60
            }
        }
        result = gen_env_ref_mod.format_default(var_config, include_env_specific=True)
        assert '15' in result
        assert 'production=15' in result
        assert 'development=30' in result
        assert 'ci=60' in result

    def test_format_default_without_env_specific_flag(self):
        """Test that env_specific is not included when flag is False."""
        var_config = {
            'default': 15,
            'environment_specific': {
                'production': 15,
                'development': 30,
            }
        }
        result = gen_env_ref_mod.format_default(var_config, include_env_specific=False)
        assert result == '15'
        assert 'production' not in result


class TestGenerateEnvReference:
    """Test ENV_REFERENCE.md generation functionality."""

    def test_basic_generation(self, tmp_path):
        """Test basic ENV_REFERENCE.md generation."""
        schema = {
            'version': '1.0',
            'metadata': {'last_updated': '2025-01-01'},
            'fields': {
                'DATABASE_URL': {
                    'category': 'Database',
                    'description': 'Database connection URL',
                    'required': True,
                    'type': 'url',
                    'security_level': 'secret'
                }
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '# Environment Variable Reference' in content
        assert 'Auto-generated from `config/env.schema.yaml`' in content
        assert 'DO NOT EDIT THIS FILE MANUALLY' in content
        assert '## Database' in content
        assert '`DATABASE_URL`' in content
        assert 'Database connection URL' in content
        assert 'SECRET' in content

    def test_generation_with_multiple_categories(self, tmp_path):
        """Test generation with multiple categories."""
        schema = {
            'version': '1.0',
            'fields': {
                'DB_URL': {
                    'category': 'Database',
                    'description': 'Database URL',
                    'type': 'url'
                },
                'API_KEY': {
                    'category': 'Security',
                    'description': 'API key',
                    'type': 'secret',
                    'security_level': 'critical'
                },
                'LOG_LEVEL': {
                    'category': 'Application',
                    'description': 'Log level',
                    'type': 'string',
                    'default': 'INFO'
                }
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '## Database' in content
        assert '## Security' in content
        assert '## Application' in content

    def test_generation_overview_section(self, tmp_path):
        """Test that overview section contains correct counts."""
        schema = {
            'version': '2.0',
            'metadata': {'last_updated': '2025-12-16'},
            'fields': {
                'REQUIRED_VAR': {
                    'category': 'Testing',
                    'required': True,
                    'type': 'string'
                },
                'OPTIONAL_VAR': {
                    'category': 'Testing',
                    'required': False,
                    'type': 'string'
                }
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '**Schema Version**: 2.0' in content
        assert '**Total Variables**: 2' in content
        assert '**Required**: 1' in content
        assert '**Optional**: 1' in content

    def test_generation_table_of_contents(self, tmp_path):
        """Test that table of contents is generated."""
        schema = {
            'version': '1.0',
            'fields': {
                'DB_URL': {'category': 'Database', 'type': 'url'},
                'API_KEY': {'category': 'Security', 'type': 'secret'},
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '## Table of Contents' in content
        assert '[Database](#database)' in content
        assert '[Security](#security)' in content

    def test_generation_security_levels_table(self, tmp_path):
        """Test that security levels table is generated."""
        schema = {
            'version': '1.0',
            'fields': {
                'TEST_VAR': {'category': 'Testing', 'type': 'string'}
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '## Security Levels' in content
        assert '| CRITICAL |' in content
        assert '| SECRET |' in content
        assert '| MEDIUM |' in content
        assert '| LOW |' in content
        assert '| PUBLIC |' in content

    def test_generation_details_section(self, tmp_path):
        """Test that details section is generated for each variable."""
        schema = {
            'version': '1.0',
            'fields': {
                'TEST_VAR': {
                    'category': 'Testing',
                    'description': 'A test variable',
                    'type': 'string',
                    'required': True,
                    'default': 'test_value',
                    'example': 'example_value',
                    'security_level': 'low'
                }
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '### Details' in content
        assert '#### `TEST_VAR`' in content
        assert 'A test variable' in content
        assert '**Type**: string' in content
        assert '**Required**: Yes' in content
        assert '**Default**: `test_value`' in content
        assert '**Example**: `example_value`' in content
        assert '**Security Level**: LOW' in content

    def test_generation_with_notes(self, tmp_path):
        """Test generation with notes field."""
        schema = {
            'version': '1.0',
            'fields': {
                'COMPLEX_VAR': {
                    'category': 'Application',
                    'description': 'Complex variable',
                    'type': 'string',
                    'notes': 'Line 1\nLine 2\nLine 3'
                }
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '**Notes**:' in content
        assert '> Line 1' in content
        assert '> Line 2' in content
        assert '> Line 3' in content

    def test_generation_with_environment_specific(self, tmp_path):
        """Test generation with environment-specific values."""
        schema = {
            'version': '1.0',
            'fields': {
                'TIMEOUT': {
                    'category': 'Application',
                    'description': 'Request timeout',
                    'type': 'integer',
                    'default': 30,
                    'environment_specific': {
                        'production': 30,
                        'development': 60,
                        'ci': 120
                    }
                }
            }
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '**Environment-specific values**:' in content
        assert 'production: `30`' in content
        assert 'development: `60`' in content
        assert 'ci: `120`' in content

    def test_generation_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created."""
        output_file = tmp_path / 'nested' / 'dir' / 'ENV_REFERENCE.md'

        schema = {
            'version': '1.0',
            'fields': {
                'TEST_VAR': {'category': 'Testing', 'type': 'string'}
            }
        }

        gen_env_ref_mod.generate_env_reference(schema, output_file)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_generation_is_deterministic(self, tmp_path):
        """Test that generation produces identical output on multiple runs."""
        schema = {
            'version': '1.0',
            'fields': {
                'VAR_A': {'category': 'Application', 'type': 'string'},
                'VAR_B': {'category': 'Database', 'type': 'url'},
                'VAR_C': {'category': 'Security', 'type': 'secret'},
            }
        }

        output_file1 = tmp_path / 'output1.md'
        output_file2 = tmp_path / 'output2.md'

        gen_env_ref_mod.generate_env_reference(schema, output_file1)
        gen_env_ref_mod.generate_env_reference(schema, output_file2)

        content1 = output_file1.read_text()
        content2 = output_file2.read_text()

        assert content1 == content2

    def test_generation_empty_fields(self, tmp_path):
        """Test generation with empty fields."""
        schema = {
            'version': '1.0',
            'fields': {}
        }

        output_file = tmp_path / 'ENV_REFERENCE.md'
        gen_env_ref_mod.generate_env_reference(schema, output_file)

        content = output_file.read_text()

        assert '# Environment Variable Reference' in content
        assert '**Total Variables**: 0' in content
        assert '**Required**: 0' in content
        assert '**Optional**: 0' in content
