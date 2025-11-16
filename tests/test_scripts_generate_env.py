"""
Unit tests for scripts/generate-env-examples.py

Tests the environment example generation functionality.
"""

import pytest
from pathlib import Path
import sys
import yaml
import importlib.util
import os

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

script_path = Path(__file__).parent.parent / 'scripts' / 'generate-env-examples.py'
spec = importlib.util.spec_from_file_location("gen_env_mod", script_path)
gen_env_mod = importlib.util.module_from_spec(spec)

from unittest.mock import Mock
mock_repo_root = Mock()
mock_repo_root.get_repo_root.return_value = Path('/tmp/test_repo')
sys.modules['repo_root_utils'] = mock_repo_root

spec.loader.exec_module(gen_env_mod)


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
        with open(schema_file, 'w') as f:
            yaml.dump(schema_data, f)
        
        result = gen_env_mod.load_schema(schema_file)
        
        assert result == schema_data
        assert result['version'] == '1.0'
        assert 'TEST_VAR' in result['fields']
    
    def test_load_schema_empty_file(self, tmp_path):
        """Test loading empty schema file."""
        schema_file = tmp_path / 'empty.yaml'
        schema_file.write_text('')
        
        result = gen_env_mod.load_schema(schema_file)
        
        assert result is None


class TestGenerateEnvExample:
    """Test .env.example generation functionality."""
    
    def test_basic_generation(self, tmp_path):
        """Test basic .env.example generation."""
        schema = {
            'fields': {
                'DATABASE_URL': {
                    'category': 'Database',
                    'description': 'Database connection URL',
                    'required': True,
                    'type': 'url',
                    'example': 'postgresql://localhost:5432/db'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Database'], output_file)
        
        content = output_file.read_text()
        
        assert '# Generated from config/env.schema.yaml' in content
        assert '# Database' in content
        assert '# Database connection URL' in content
        assert '# Required: True' in content
        assert 'DATABASE_URL=postgresql://localhost:5432/db' in content
    
    def test_with_default_value(self, tmp_path):
        """Test generation with default value."""
        schema = {
            'fields': {
                'LOG_LEVEL': {
                    'category': 'Application',
                    'description': 'Logging level',
                    'required': False,
                    'type': 'string',
                    'default': 'INFO'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Application'], output_file)
        
        content = output_file.read_text()
        
        assert 'LOG_LEVEL=INFO' in content
        assert '# Required: False' in content
    
    def test_boolean_type(self, tmp_path):
        """Test generation with boolean type."""
        schema = {
            'fields': {
                'ENABLE_FEATURE': {
                    'category': 'Feature Flags',
                    'required': False,
                    'type': 'boolean'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Feature Flags'], output_file)
        
        assert 'ENABLE_FEATURE=false' in output_file.read_text()
    
    def test_secret_type(self, tmp_path):
        """Test generation with secret type."""
        schema = {
            'fields': {
                'API_KEY': {
                    'category': 'Security',
                    'required': True,
                    'type': 'secret'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Security'], output_file)
        
        assert 'API_KEY=your-secret-here' in output_file.read_text()
    
    def test_integer_type(self, tmp_path):
        """Test generation with integer type."""
        schema = {
            'fields': {
                'MAX_CONNECTIONS': {
                    'category': 'Infrastructure',
                    'required': False,
                    'type': 'integer'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Infrastructure'], output_file)
        
        assert 'MAX_CONNECTIONS=0' in output_file.read_text()
    
    def test_url_type(self, tmp_path):
        """Test generation with URL type."""
        schema = {
            'fields': {
                'WEBHOOK_URL': {
                    'category': 'Integration',
                    'required': False,
                    'type': 'url'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Integration'], output_file)
        
        assert 'WEBHOOK_URL=https://example.com' in output_file.read_text()
    
    def test_with_notes(self, tmp_path):
        """Test generation with multi-line notes."""
        schema = {
            'fields': {
                'COMPLEX_VAR': {
                    'category': 'Application',
                    'notes': 'Line 1\nLine 2',
                    'required': True,
                    'type': 'string',
                    'example': 'value'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Application'], output_file)
        
        content = output_file.read_text()
        assert '# Line 1' in content
        assert '# Line 2' in content
    
    def test_multiple_categories(self, tmp_path):
        """Test generation with multiple categories."""
        schema = {
            'fields': {
                'DB_URL': {
                    'category': 'Database',
                    'type': 'url',
                    'example': 'postgresql://localhost/db'
                },
                'API_KEY': {
                    'category': 'Security',
                    'type': 'secret'
                },
                'LOG_LEVEL': {
                    'category': 'Application',
                    'default': 'INFO'
                }
            }
        }
        
        output_file = tmp_path / '.env.example'
        gen_env_mod.generate_env_example(schema, ['Database', 'Security'], output_file)
        
        content = output_file.read_text()
        
        assert 'DB_URL=' in content
        assert 'API_KEY=' in content
        assert 'LOG_LEVEL' not in content
    
    def test_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created."""
        output_file = tmp_path / 'nested' / 'dir' / '.env.example'
        
        schema = {
            'fields': {
                'TEST_VAR': {
                    'category': 'Testing',
                    'type': 'string',
                    'example': 'test'
                }
            }
        }
        
        gen_env_mod.generate_env_example(schema, ['Testing'], output_file)
        
        assert output_file.exists()
        assert output_file.parent.exists()
