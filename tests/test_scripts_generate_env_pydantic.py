"""
Unit tests for scripts/generate_env_example.py

Tests Pydantic-based environment example generation.
"""

import pytest
from pathlib import Path
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import importlib.util

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

mock_repo_root = Mock()
test_root = Path('/tmp/test_repo')
mock_repo_root.get_repo_root.return_value = test_root
sys.modules['repo_root_utils'] = mock_repo_root

mock_common = MagicMock()
mock_config = MagicMock()
mock_settings_module = MagicMock()

class MockFieldInfo:
    def __init__(self, required=True, description=None, default=None, alias=None, annotation=str):
        self._required = required
        self.description = description
        self.default = default
        self.alias = alias
        self.annotation = annotation
        self.metadata = []
    
    def is_required(self):
        return self._required

mock_settings_class = MagicMock()
mock_settings_class.model_fields = {
    'database_url': MockFieldInfo(required=True, description='Database connection URL', annotation=str),
    'jwt_secret_key': MockFieldInfo(required=True, description='JWT secret key', annotation=str),
    'log_level': MockFieldInfo(required=False, description='Logging level', default='INFO', annotation=str),
    'debug': MockFieldInfo(required=False, description='Debug mode', default=False, annotation=bool),
}

mock_settings_module.Settings = mock_settings_class
sys.modules['common'] = mock_common
sys.modules['common.config'] = mock_config
sys.modules['common.config.settings'] = mock_settings_module

sys.modules['pydantic'] = MagicMock()
sys.modules['pydantic.fields'] = MagicMock()

script_path = Path(__file__).parent.parent / 'scripts' / 'generate_env_example.py'
spec = importlib.util.spec_from_file_location("gen_env_pydantic_mod", script_path)
gen_env_pydantic_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_env_pydantic_mod)


class TestGenerateEnvExample:
    """Test Pydantic-based .env.example generation."""
    
    def test_generate_env_example_basic(self, tmp_path, monkeypatch):
        """Test basic .env.example generation."""
        monkeypatch.setattr(gen_env_pydantic_mod, 'project_root', tmp_path)
        
        gen_env_pydantic_mod.generate_env_example()
        
        env_file = tmp_path / '.env.example'
        assert env_file.exists()
        
        content = env_file.read_text()
        
        assert 'MorningAI Environment Variables' in content
        assert 'Generated from common/config/settings.py' in content
        
        assert 'REQUIRED VARIABLES' in content
        assert 'DATABASE_URL=' in content
        assert 'JWT_SECRET_KEY=' in content
        
        assert 'OPTIONAL VARIABLES' in content
        assert 'LOG_LEVEL' in content
        assert 'DEBUG' in content
    
    def test_generate_env_example_descriptions(self, tmp_path, monkeypatch):
        """Test that descriptions are included."""
        monkeypatch.setattr(gen_env_pydantic_mod, 'project_root', tmp_path)
        
        gen_env_pydantic_mod.generate_env_example()
        
        content = (tmp_path / '.env.example').read_text()
        
        assert 'Database connection URL' in content
        assert 'JWT secret key' in content
        assert 'Logging level' in content
        assert 'Debug mode' in content
    
    def test_generate_env_example_defaults(self, tmp_path, monkeypatch):
        """Test that default values are shown."""
        monkeypatch.setattr(gen_env_pydantic_mod, 'project_root', tmp_path)
        
        gen_env_pydantic_mod.generate_env_example()
        
        content = (tmp_path / '.env.example').read_text()
        
        assert 'Default: INFO' in content
        assert 'Default: False' in content
    
    def test_generate_env_example_types(self, tmp_path, monkeypatch):
        """Test that type information is included."""
        monkeypatch.setattr(gen_env_pydantic_mod, 'project_root', tmp_path)
        
        gen_env_pydantic_mod.generate_env_example()
        
        content = (tmp_path / '.env.example').read_text()
        
        assert 'Type: str' in content or 'Type: <class \'str\'>' in content
        assert 'Type: bool' in content or 'Type: <class \'bool\'>' in content
    
    def test_generate_env_example_separates_required_optional(self, tmp_path, monkeypatch):
        """Test that required and optional fields are separated."""
        monkeypatch.setattr(gen_env_pydantic_mod, 'project_root', tmp_path)
        
        gen_env_pydantic_mod.generate_env_example()
        
        content = (tmp_path / '.env.example').read_text()
        
        required_pos = content.find('REQUIRED VARIABLES')
        optional_pos = content.find('OPTIONAL VARIABLES')
        database_pos = content.find('DATABASE_URL=')
        log_level_pos = content.find('LOG_LEVEL')
        
        assert required_pos < optional_pos
        
        assert database_pos < log_level_pos
