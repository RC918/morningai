"""
Unit tests for scripts/verify_system_state.sh

Tests the system state verification script that validates documentation vs code consistency.
This script is critical for CI and validates React versions, pgvector, orchestrator architecture, etc.

Related Issue: #2581
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import pytest

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

# Path to the script under test
SCRIPT_PATH = Path(__file__).parent.parent / 'scripts' / 'verify_system_state.sh'


def setup_base_package_files(repo_path: Path) -> None:
    """Setup minimum required package.json files for script to run past React check."""
    # Root package.json with pnpm overrides
    (repo_path / 'package.json').write_text(json.dumps({
        "pnpm": {"overrides": {"react": "^19.1.0"}}
    }))
    # Frontend dashboard package.json
    (repo_path / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
        json.dumps({"dependencies": {"react": "^19.1.0"}})
    )
    # Owner console package.json
    (repo_path / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
        json.dumps({"dependencies": {"react": "^19.1.0"}})
    )


@pytest.fixture
def temp_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary repository structure for testing."""
    # Create basic directory structure
    (tmp_path / 'scripts').mkdir(parents=True)
    (tmp_path / 'migrations').mkdir(parents=True)
    (tmp_path / 'agents' / 'dev_agent' / 'migrations').mkdir(parents=True)
    (tmp_path / 'agents' / 'faq_agent' / 'migrations').mkdir(parents=True)
    (tmp_path / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard').mkdir(parents=True)
    (tmp_path / 'handoff' / '20250928' / '40_App' / 'owner-console').mkdir(parents=True)
    (tmp_path / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src' / 'routes').mkdir(parents=True)
    (tmp_path / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'tests').mkdir(parents=True)
    (tmp_path / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'alembic' / 'versions').mkdir(parents=True)
    (tmp_path / 'handoff' / '20250928' / '40_App' / 'orchestrator').mkdir(parents=True)
    (tmp_path / 'orchestrator').mkdir(parents=True)
    (tmp_path / 'docs' / 'adr').mkdir(parents=True)

    # Copy the script to test
    shutil.copy(SCRIPT_PATH, tmp_path / 'scripts' / 'verify_system_state.sh')

    yield tmp_path


@pytest.fixture
def minimal_valid_repo(temp_repo: Path) -> Path:
    """Create a minimal valid repository that passes all checks."""
    # Root package.json with pnpm overrides
    root_package = {
        "name": "morningai",
        "pnpm": {
            "overrides": {
                "react": "^19.1.0",
                "react-dom": "^19.1.0"
            }
        }
    }
    (temp_repo / 'package.json').write_text(json.dumps(root_package, indent=2))

    # Frontend dashboard package.json
    frontend_package = {
        "name": "frontend-dashboard",
        "dependencies": {
            "react": "^19.1.0",
            "react-dom": "^19.1.0"
        }
    }
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
        json.dumps(frontend_package, indent=2)
    )

    # Owner console package.json
    owner_package = {
        "name": "owner-console",
        "dependencies": {
            "react": "^19.1.0",
            "react-dom": "^19.1.0"
        }
    }
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
        json.dumps(owner_package, indent=2)
    )

    # pgvector migrations
    (temp_repo / 'migrations' / '001_init.sql').write_text(
        'CREATE EXTENSION IF NOT EXISTS vector;\n'
        'CREATE TABLE embeddings (id SERIAL, embedding vector(1536));'
    )
    (temp_repo / 'agents' / 'dev_agent' / 'migrations' / '001_init.sql').write_text(
        'CREATE EXTENSION IF NOT EXISTS vector;'
    )
    (temp_repo / 'agents' / 'faq_agent' / 'migrations' / '001_init.sql').write_text(
        'CREATE EXTENSION IF NOT EXISTS vector;'
    )

    # Vector API
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src' / 'routes' / 'vectors.py').write_text(
        '# Vector API implementation'
    )

    # render.yaml with USE_LANGGRAPH=false
    render_yaml = """
services:
  - name: api-backend
    envVars:
      - key: USE_LANGGRAPH
        value: false
    dockerfilePath: orchestrator/Dockerfile
    rootDir: handoff/20250928/40_App/orchestrator
    cors:
      allowedOrigins:
        - https://app.gm365.me
        - https://admin.gm365.me
"""
    (temp_repo / 'render.yaml').write_text(render_yaml)

    # TERMINOLOGY.md with production URLs
    (temp_repo / 'docs' / 'TERMINOLOGY.md').write_text(
        '# Terminology\n\n'
        'Production URLs:\n'
        '- app.gm365.me - Main application\n'
        '- admin.gm365.me - Admin console\n'
    )

    # Alembic setup
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'alembic.ini').write_text('[alembic]')

    # requirements.txt
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'requirements.txt').write_text(
        'PyJWT==2.8.0\n'
        'rq==1.15.1\n'
        'pyotp==2.9.0\n'
        'numpy==1.26.0\n'
        'alembic==1.12.0\n'
    )

    # orchestrator requirements (without langgraph)
    (temp_repo / 'orchestrator' / 'requirements.txt').write_text(
        'fastapi==0.104.0\n'
        'uvicorn==0.24.0\n'
    )

    # Legacy orchestrator
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'orchestrator' / 'langgraph_orchestrator.py').write_text(
        '# Legacy LangGraph orchestrator'
    )

    # pytest conftest
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'tests' / 'conftest.py').write_text(
        'import pytest'
    )

    # pytest.ini
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'pytest.ini').write_text(
        '[pytest]\ntestpaths = tests'
    )

    # main.py without phase imports
    (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src' / 'main.py').write_text(
        'from fastapi import FastAPI\napp = FastAPI()'
    )

    # ADR-005
    (temp_repo / 'docs' / 'adr' / '005-dual-orchestrator-architecture.md').write_text(
        '# ADR-005: Dual Orchestrator Architecture'
    )

    return temp_repo


class TestReactVersionExtraction:
    """Test React version extraction from package.json files."""

    def test_valid_caret_version(self, temp_repo: Path):
        """Test extraction of caret version (^19.1.0)."""
        # Setup
        package = {"dependencies": {"react": "^19.1.0"}}
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(package)
        )
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))

        # Run script (will fail on other checks, but we're testing React extraction)
        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Verify React version was extracted correctly
        assert 'frontend-dashboard React version: 19.1.0' in result.stdout

    def test_valid_exact_version(self, temp_repo: Path):
        """Test extraction of exact version (19.1.0 without caret)."""
        package = {"dependencies": {"react": "19.1.0"}}
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(package)
        )
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "19.1.0"}}
        }))

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'frontend-dashboard React version: 19.1.0' in result.stdout

    def test_version_mismatch_detected(self, temp_repo: Path):
        """Test that version mismatch is detected and reported."""
        # Frontend has different version than expected
        frontend_package = {"dependencies": {"react": "^18.2.0"}}
        owner_package = {"dependencies": {"react": "^19.1.0"}}

        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(owner_package)
        )
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'frontend-dashboard React version mismatch' in result.stdout
        assert 'expected 19.1.0' in result.stdout
        assert 'got 18.2.0' in result.stdout

    def test_missing_package_json_graceful_handling(self, temp_repo: Path):
        """Test graceful handling when package.json is missing."""
        # Don't create package.json files
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Script should still run (grep will return empty)
        assert result.returncode != 0  # Will fail due to missing files
        assert 'Verifying React versions' in result.stdout

    def test_malformed_json_handling(self, temp_repo: Path):
        """Test handling of malformed JSON in package.json."""
        # Write invalid JSON
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            '{"dependencies": {"react": "^19.1.0"'  # Missing closing braces
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            '{"dependencies": {"react": "^19.1.0"}}'
        )
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Script uses grep, so malformed JSON still works for version extraction
        assert 'Verifying React versions' in result.stdout


class TestPnpmOverrideReading:
    """Test pnpm override reading from root package.json."""

    def test_valid_overrides(self, temp_repo: Path):
        """Test reading valid pnpm overrides."""
        root_package = {
            "pnpm": {
                "overrides": {
                    "react": "^19.1.0",
                    "react-dom": "^19.1.0"
                }
            }
        }
        (temp_repo / 'package.json').write_text(json.dumps(root_package))

        # Create matching frontend packages
        frontend_package = {"dependencies": {"react": "^19.1.0"}}
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(frontend_package)
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh'), '--verbose'],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'Expected React version from pnpm overrides: 19.1.0' in result.stdout

    def test_missing_overrides_fallback(self, temp_repo: Path):
        """Test fallback when pnpm.overrides section is missing."""
        # Root package without overrides
        root_package = {"name": "morningai"}
        (temp_repo / 'package.json').write_text(json.dumps(root_package))

        frontend_package = {"dependencies": {"react": "^19.1.0"}}
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(frontend_package)
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh'), '--verbose'],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Should fallback to 19.1.0
        assert 'Expected React version from pnpm overrides: 19.1.0' in result.stdout

    def test_node_unavailable_fallback(self, temp_repo: Path):
        """Test fallback when node is unavailable."""
        # Create a script that simulates node being unavailable
        modified_script = (temp_repo / 'scripts' / 'verify_system_state.sh').read_text()
        modified_script = modified_script.replace(
            'EXPECTED_REACT=$(node -p',
            'EXPECTED_REACT=$(nonexistent_command -p'
        )
        (temp_repo / 'scripts' / 'verify_system_state.sh').write_text(modified_script)

        frontend_package = {"dependencies": {"react": "^19.1.0"}}
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / 'package.json').write_text(json.dumps({"name": "test"}))

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh'), '--verbose'],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Should fallback to default 19.1.0
        assert 'Expected React version from pnpm overrides: 19.1.0' in result.stdout


class TestVersionComparison:
    """Test version comparison logic."""

    def test_matching_versions_pass(self, minimal_valid_repo: Path):
        """Test that matching versions pass verification."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'frontend-dashboard React version: 19.1.0 (matches pnpm override)' in result.stdout
        assert 'owner-console React version: 19.1.0 (matches pnpm override)' in result.stdout

    def test_mismatched_versions_fail(self, temp_repo: Path):
        """Test that mismatched versions fail verification."""
        # Setup with mismatched versions
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^18.0.0"}})
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'frontend-dashboard React version mismatch' in result.stdout
        assert result.returncode != 0

    def test_empty_version_handling(self, temp_repo: Path):
        """Test handling when version is empty or missing."""
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))
        # Package without react dependency - grep will find "react" but no version
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps({"dependencies": {"other": "1.0.0"}})
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Empty version should cause mismatch (grep returns empty, version comparison fails)
        # The script will show mismatch because extracted version is empty
        assert 'frontend-dashboard React version mismatch' in result.stdout or result.returncode != 0


class TestPgvectorVerification:
    """Test pgvector implementation verification."""

    def test_pgvector_extension_found(self, minimal_valid_repo: Path):
        """Test detection of pgvector extension in migrations."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'pgvector (vector extension) in main migrations/' in result.stdout
        assert 'pgvector (vector extension) in dev_agent migrations' in result.stdout
        assert 'pgvector (vector extension) in faq_agent migrations' in result.stdout

    def test_pgvector_extension_missing(self, temp_repo: Path):
        """Test failure when pgvector extension is missing."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        # Create empty migrations without pgvector
        (temp_repo / 'migrations' / '001_init.sql').write_text('CREATE TABLE users (id SERIAL);')

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'pgvector (vector extension) NOT found in migrations/' in result.stdout

    def test_vector_columns_detected(self, minimal_valid_repo: Path):
        """Test detection of vector column definitions."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'pgvector columns actively used in migrations' in result.stdout

    def test_vector_api_exists(self, minimal_valid_repo: Path):
        """Test detection of Vector API implementation."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'Vector API implementation exists' in result.stdout


class TestDualOrchestratorArchitecture:
    """Test dual orchestrator architecture verification."""

    def test_use_langgraph_false(self, minimal_valid_repo: Path):
        """Test detection of USE_LANGGRAPH=false in render.yaml."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'USE_LANGGRAPH=false in render.yaml' in result.stdout

    def test_use_langgraph_true_fails(self, temp_repo: Path):
        """Test failure when USE_LANGGRAPH is not false."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        render_yaml = """
services:
  - name: api-backend
    envVars:
      - key: USE_LANGGRAPH
        value: true
"""
        (temp_repo / 'render.yaml').write_text(render_yaml)

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'USE_LANGGRAPH flag not set to false' in result.stdout

    def test_orchestrator_dockerfile_reference(self, minimal_valid_repo: Path):
        """Test detection of orchestrator Dockerfile reference."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'New orchestrator Dockerfile reference in render.yaml' in result.stdout

    def test_new_orchestrator_no_langgraph(self, minimal_valid_repo: Path):
        """Test that new orchestrator doesn't include langgraph."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'New orchestrator does NOT include langgraph' in result.stdout

    def test_new_orchestrator_with_langgraph_fails(self, temp_repo: Path):
        """Test failure when new orchestrator includes langgraph."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        (temp_repo / 'orchestrator' / 'requirements.txt').write_text(
            'fastapi==0.104.0\n'
            'langgraph==0.1.0\n'
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'New orchestrator should NOT include langgraph dependency' in result.stdout


class TestProductionURLMapping:
    """Test production URL mapping verification."""

    def test_production_urls_documented(self, minimal_valid_repo: Path):
        """Test detection of production URLs in TERMINOLOGY.md."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'Production URLs documented in TERMINOLOGY.md' in result.stdout

    def test_production_urls_missing(self, temp_repo: Path):
        """Test failure when production URLs are missing."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        (temp_repo / 'docs' / 'TERMINOLOGY.md').write_text('# Terminology\n\nSome content')

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'Production URLs not properly documented' in result.stdout

    def test_production_urls_in_cors(self, minimal_valid_repo: Path):
        """Test detection of production URLs in CORS configuration."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'Production URLs in CORS configuration' in result.stdout


class TestAlembicStatus:
    """Test Alembic implementation verification."""

    def test_alembic_implemented(self, minimal_valid_repo: Path):
        """Test detection of Alembic implementation."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'Alembic implemented (alembic.ini exists)' in result.stdout
        assert 'Alembic implemented (alembic/ directory exists)' in result.stdout
        assert 'Alembic versions directory exists' in result.stdout
        assert 'Alembic in requirements.txt' in result.stdout

    def test_alembic_missing(self, temp_repo: Path):
        """Test failure when Alembic is not implemented."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'requirements.txt').write_text(
            'fastapi==0.104.0\n'
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'Alembic NOT implemented' in result.stdout


class TestPhaseAPIModules:
    """Test Phase API module status verification."""

    def test_main_py_no_phase_imports(self, minimal_valid_repo: Path):
        """Test that main.py doesn't directly import phase modules."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'main.py does NOT directly import Phase API modules' in result.stdout

    def test_main_py_with_phase_imports_fails(self, temp_repo: Path):
        """Test failure when main.py directly imports phase modules."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src' / 'main.py').write_text(
            'from phase4_meta_agent_api import router\n'
            'from fastapi import FastAPI\n'
            'app = FastAPI()'
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'main.py directly imports Phase API modules' in result.stdout


class TestCriticalDependencies:
    """Test critical dependencies verification."""

    def test_all_dependencies_present(self, minimal_valid_repo: Path):
        """Test detection of all critical dependencies."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'PyJWT in requirements.txt' in result.stdout
        assert 'rq (Redis Queue) in requirements.txt' in result.stdout
        assert 'pyotp in requirements.txt' in result.stdout
        assert 'numpy in requirements.txt' in result.stdout

    def test_missing_dependency_fails(self, temp_repo: Path):
        """Test failure when critical dependency is missing."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'requirements.txt').write_text(
            'fastapi==0.104.0\n'
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'PyJWT NOT in requirements.txt' in result.stdout


class TestTestFramework:
    """Test test framework verification."""

    def test_pytest_setup_exists(self, minimal_valid_repo: Path):
        """Test detection of pytest setup."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'pytest conftest.py exists' in result.stdout
        assert 'pytest.ini configuration exists' in result.stdout


class TestADRVerification:
    """Test Architecture Decision Records verification."""

    def test_adr_005_exists(self, minimal_valid_repo: Path):
        """Test detection of ADR-005."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'ADR-005 (Dual Orchestrator) exists' in result.stdout

    def test_adr_005_missing(self, temp_repo: Path):
        """Test failure when ADR-005 is missing."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'ADR-005 NOT found' in result.stdout


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_package_json(self, temp_repo: Path):
        """Test handling of empty package.json."""
        (temp_repo / 'package.json').write_text('{}')
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text('{}')
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text('{}')

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Script should handle empty package.json gracefully
        assert 'Verifying React versions' in result.stdout

    def test_multiple_react_entries(self, temp_repo: Path):
        """Test handling of multiple react entries in package.json."""
        # Package with react in both dependencies and devDependencies
        package = {
            "dependencies": {"react": "^19.1.0"},
            "devDependencies": {"react": "^18.0.0"}
        }
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / 'package.json').write_text(
            json.dumps(package)
        )
        (temp_repo / 'handoff' / '20250928' / '40_App' / 'owner-console' / 'package.json').write_text(
            json.dumps(package)
        )
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Should use head -1 to get first match
        assert 'frontend-dashboard React version: 19.1.0' in result.stdout

    def test_unicode_in_paths(self, temp_repo: Path):
        """Test handling of unicode characters in file content."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        (temp_repo / 'docs' / 'TERMINOLOGY.md').write_text(
            '# 術語表\n\n'
            'Production URLs:\n'
            '- app.gm365.me - 主應用程式\n'
            '- admin.gm365.me - 管理控制台\n'
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'Production URLs documented in TERMINOLOGY.md' in result.stdout

    def test_verbose_flag(self, minimal_valid_repo: Path):
        """Test verbose output mode."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh'), '--verbose'],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        # Verbose mode should show additional details
        assert 'Expected React version from pnpm overrides' in result.stdout


class TestSummaryOutput:
    """Test verification summary output."""

    def test_summary_all_pass(self, minimal_valid_repo: Path):
        """Test summary when all checks pass."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'Verification Summary' in result.stdout
        assert 'Total checks:' in result.stdout

    def test_summary_with_errors(self, temp_repo: Path):
        """Test summary when there are errors."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        # But don't create other required files so we get errors

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert 'Verification FAILED' in result.stdout
        assert result.returncode == 1

    def test_exit_code_success(self, minimal_valid_repo: Path):
        """Test exit code 0 on success."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        # May have warnings but no errors
        assert result.returncode == 0 or 'Verification PASSED' in result.stdout

    def test_exit_code_failure(self, temp_repo: Path):
        """Test exit code 1 on failure."""
        # Setup base files so script can run past React check
        setup_base_package_files(temp_repo)
        # But don't create other required files so we get errors

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


class TestEnvironmentVariables:
    """Test environment variable verification."""

    def test_redis_url_set(self, minimal_valid_repo: Path):
        """Test detection of REDIS_URL when set."""
        env = os.environ.copy()
        env['REDIS_URL'] = 'redis://localhost:6379'

        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True,
            env=env
        )

        assert 'REDIS_URL is set' in result.stdout

    def test_redis_url_not_set(self, minimal_valid_repo: Path):
        """Test warning when REDIS_URL is not set."""
        env = os.environ.copy()
        env.pop('REDIS_URL', None)

        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True,
            env=env
        )

        assert 'REDIS_URL not set' in result.stdout

    def test_database_url_set(self, minimal_valid_repo: Path):
        """Test detection of DATABASE_URL when set."""
        env = os.environ.copy()
        env['DATABASE_URL'] = 'postgresql://localhost/test'

        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True,
            env=env
        )

        assert 'DATABASE_URL is set' in result.stdout
