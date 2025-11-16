"""
Unit tests for scripts/generate-env-examples.py main() function

Tests the main entry point and full workflow.
"""

import pytest
from pathlib import Path
import sys
import yaml
import importlib.util
import os
from unittest.mock import Mock, patch, MagicMock

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

script_path = Path(__file__).parent.parent / 'scripts' / 'generate-env-examples.py'
spec = importlib.util.spec_from_file_location("gen_env_main_mod", script_path)
gen_env_main_mod = importlib.util.module_from_spec(spec)

mock_repo_root = Mock()
test_root = Path('/tmp/test_repo_main')
mock_repo_root.get_repo_root.return_value = test_root
sys.modules['repo_root_utils'] = mock_repo_root

spec.loader.exec_module(gen_env_main_mod)


class TestMain:
    """Test main() function."""
    
    def test_main_success(self, tmp_path, monkeypatch, capsys):
        """Test successful main execution."""
        mock_repo_root.get_repo_root.return_value = tmp_path
        
        schema_dir = tmp_path / 'config'
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / 'env.schema.yaml'
        
        schema_data = {
            'version': '1.0',
            'fields': {
                'DATABASE_URL': {
                    'category': 'Database',
                    'description': 'Database URL',
                    'required': True,
                    'type': 'url',
                    'example': 'postgresql://localhost/db'
                },
                'API_KEY': {
                    'category': 'Security',
                    'description': 'API Key',
                    'required': False,
                    'type': 'secret'
                },
                'FRONTEND_URL': {
                    'category': 'Frontend',
                    'description': 'Frontend URL',
                    'required': True,
                    'type': 'url',
                    'example': 'http://localhost:3000'
                }
            }
        }
        
        with open(schema_file, 'w') as f:
            yaml.dump(schema_data, f)
        
        gen_env_main_mod.main()
        
        assert (tmp_path / '.env.example').exists()
        
        captured = capsys.readouterr()
        assert '📖 Loading schema from:' in captured.out
        assert '📊 Schema version: 1.0' in captured.out
        assert '📊 Total variables: 3' in captured.out
        assert '2 required, 1 optional' in captured.out
        assert '✅ All .env.example files generated successfully!' in captured.out
    
    def test_main_schema_not_found(self, tmp_path, monkeypatch):
        """Test main when schema file doesn't exist."""
        mock_repo_root.get_repo_root.return_value = tmp_path
        
        with pytest.raises(SystemExit) as exc_info:
            gen_env_main_mod.main()
        
        assert exc_info.value.code == 1
    
    def test_main_creates_all_output_files(self, tmp_path, capsys):
        """Test that main creates all expected output files."""
        mock_repo_root.get_repo_root.return_value = tmp_path
        
        schema_dir = tmp_path / 'config'
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / 'env.schema.yaml'
        
        schema_data = {
            'version': '2.0',
            'fields': {
                'DB_URL': {
                    'category': 'Database',
                    'required': True,
                    'type': 'url',
                    'example': 'postgresql://localhost/db'
                },
                'FRONTEND_VAR': {
                    'category': 'Frontend',
                    'required': False,
                    'type': 'string',
                    'default': 'test'
                },
                'WORKER_VAR': {
                    'category': 'Worker',
                    'required': True,
                    'type': 'string',
                    'example': 'worker'
                }
            }
        }
        
        with open(schema_file, 'w') as f:
            yaml.dump(schema_data, f)
        
        gen_env_main_mod.main()
        
        assert (tmp_path / '.env.example').exists()
        
        backend_path = tmp_path / 'handoff' / '20250928' / '40_App' / 'api-backend' / '.env.example'
        assert backend_path.exists()
        
        frontend_path = tmp_path / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / '.env.example'
        assert frontend_path.exists()
        
        owner_path = tmp_path / 'handoff' / '20250928' / '40_App' / 'owner-console' / '.env.example'
        assert owner_path.exists()
        
        orchestrator_path = tmp_path / 'orchestrator' / '.env.example'
        assert orchestrator_path.exists()
        
        captured = capsys.readouterr()
        assert '✅ Generated:' in captured.out
        assert '📝 Next steps:' in captured.out
        assert 'Review generated files' in captured.out
        assert 'Commit changes to git' in captured.out
    
    def test_main_with_multiple_required_optional(self, tmp_path, capsys):
        """Test main with various required/optional fields."""
        mock_repo_root.get_repo_root.return_value = tmp_path
        
        schema_dir = tmp_path / 'config'
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / 'env.schema.yaml'
        
        schema_data = {
            'version': '1.5',
            'fields': {
                'REQ1': {'category': 'Database', 'required': True, 'type': 'string', 'example': 'a'},
                'REQ2': {'category': 'Database', 'required': True, 'type': 'string', 'example': 'b'},
                'REQ3': {'category': 'Security', 'required': True, 'type': 'string', 'example': 'c'},
                'OPT1': {'category': 'Application', 'required': False, 'type': 'string', 'default': 'd'},
                'OPT2': {'category': 'Application', 'required': False, 'type': 'string', 'default': 'e'},
            }
        }
        
        with open(schema_file, 'w') as f:
            yaml.dump(schema_data, f)
        
        gen_env_main_mod.main()
        
        captured = capsys.readouterr()
        assert '📊 Total variables: 5 (3 required, 2 optional)' in captured.out


class TestMainEdgeCases:
    """Test edge cases in main() function."""
    
    def test_main_empty_schema(self, tmp_path, capsys):
        """Test main with empty schema."""
        mock_repo_root.get_repo_root.return_value = tmp_path
        
        schema_dir = tmp_path / 'config'
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / 'env.schema.yaml'
        
        schema_data = {
            'version': '1.0',
            'fields': {}
        }
        
        with open(schema_file, 'w') as f:
            yaml.dump(schema_data, f)
        
        gen_env_main_mod.main()
        
        captured = capsys.readouterr()
        assert '📊 Total variables: 0 (0 required, 0 optional)' in captured.out
    
    def test_main_all_categories_covered(self, tmp_path, capsys):
        """Test main with all category types."""
        mock_repo_root.get_repo_root.return_value = tmp_path
        
        schema_dir = tmp_path / 'config'
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / 'env.schema.yaml'
        
        schema_data = {
            'version': '1.0',
            'fields': {
                'AUTH_VAR': {'category': 'Authentication', 'required': True, 'type': 'string', 'example': 'a'},
                'SEC_VAR': {'category': 'Security', 'required': True, 'type': 'string', 'example': 'b'},
                'DB_VAR': {'category': 'Database', 'required': True, 'type': 'string', 'example': 'c'},
                'CLOUD_VAR': {'category': 'Cloud Services', 'required': True, 'type': 'string', 'example': 'd'},
                'INFRA_VAR': {'category': 'Infrastructure', 'required': True, 'type': 'string', 'example': 'e'},
                'MON_VAR': {'category': 'Monitoring', 'required': True, 'type': 'string', 'example': 'f'},
                'INT_VAR': {'category': 'Integration', 'required': True, 'type': 'string', 'example': 'g'},
                'WORK_VAR': {'category': 'Worker', 'required': True, 'type': 'string', 'example': 'h'},
                'APP_VAR': {'category': 'Application', 'required': True, 'type': 'string', 'example': 'i'},
                'FLAG_VAR': {'category': 'Feature Flags', 'required': True, 'type': 'string', 'example': 'j'},
                'TEST_VAR': {'category': 'Testing', 'required': True, 'type': 'string', 'example': 'k'},
                'FRONT_VAR': {'category': 'Frontend', 'required': True, 'type': 'string', 'example': 'l'},
            }
        }
        
        with open(schema_file, 'w') as f:
            yaml.dump(schema_data, f)
        
        gen_env_main_mod.main()
        
        root_env = (tmp_path / '.env.example').read_text()
        assert 'AUTH_VAR=' in root_env
        assert 'DB_VAR=' in root_env
        assert 'WORK_VAR=' in root_env
        
        frontend_env = (tmp_path / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / '.env.example').read_text()
        assert 'FRONT_VAR=' in frontend_env
        assert 'APP_VAR=' in frontend_env
        
        captured = capsys.readouterr()
        assert '✅ All .env.example files generated successfully!' in captured.out
