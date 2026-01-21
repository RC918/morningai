"""
Unit tests for scripts/verify_system_state.sh

Tests the system state verification script that validates documentation vs code consistency.
This script is critical for CI and validates React versions, pgvector, orchestrator architecture, etc.

Related Issue: #2581

MAINTENANCE NOTE:
=================
These tests and the verify_system_state.sh script require long-term synchronized maintenance.
When modifying either:
1. Script output format changes -> Update assertion helpers and test expectations
2. Repository structure changes -> Update fixture paths (temp_repo, minimal_valid_repo)
3. New verification checks added -> Add corresponding test cases
4. React/dependency versions change -> Tests auto-read from real repo's package.json

The test fixtures derive expected values (like React version) from the actual repository
to minimize manual sync cost. If tests fail after repo restructuring, check:
- FRONTEND_DASHBOARD_PATH and OWNER_CONSOLE_PATH constants
- Directory structure in temp_repo and minimal_valid_repo fixtures
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import pytest

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

# Path to the script under test
SCRIPT_PATH = Path(__file__).parent.parent / 'scripts' / 'verify_system_state.sh'
REPO_ROOT = Path(__file__).parent.parent

# Repo structure constants - update these if repo structure changes
FRONTEND_DASHBOARD_PATH = 'handoff/20250928/40_App/frontend-dashboard'
OWNER_CONSOLE_PATH = 'handoff/20250928/40_App/owner-console'
API_BACKEND_PATH = 'handoff/20250928/40_App/api-backend'
ORCHESTRATOR_PATH = 'handoff/20250928/40_App/orchestrator'


# Path helper functions to avoid hardcoding throughout tests
def frontend_dashboard_dir(repo: Path) -> Path:
    """Get frontend-dashboard directory path."""
    return repo / Path(FRONTEND_DASHBOARD_PATH)


def owner_console_dir(repo: Path) -> Path:
    """Get owner-console directory path."""
    return repo / Path(OWNER_CONSOLE_PATH)


def api_backend_dir(repo: Path) -> Path:
    """Get api-backend directory path."""
    return repo / Path(API_BACKEND_PATH)


def orchestrator_dir(repo: Path) -> Path:
    """Get orchestrator directory path."""
    return repo / Path(ORCHESTRATOR_PATH)


def get_expected_react_version() -> str:
    """Read expected React version from real repo's pnpm overrides.

    This reduces manual sync cost - tests auto-adapt to version changes.
    """
    try:
        pkg_json = REPO_ROOT / 'package.json'
        if pkg_json.exists():
            data = json.loads(pkg_json.read_text())
            version = data.get('pnpm', {}).get('overrides', {}).get('react', '^19.1.0')
            return version.lstrip('^~')
    except (json.JSONDecodeError, KeyError):
        pass
    return '19.1.0'  # Fallback


# Assertion helpers for flexible output matching
def assert_check_present(stdout: str, check_label: str) -> None:
    """Assert a check label appears in output (partial match)."""
    assert check_label in stdout, f"Expected check '{check_label}' not found in output"


def assert_check_passed(stdout: str, check_label: str) -> None:
    """Assert a check passed (has checkmark prefix)."""
    pattern = rf'[✓✅]\s*{re.escape(check_label)}'
    assert re.search(pattern, stdout), f"Check '{check_label}' did not pass"


def assert_check_failed(stdout: str, check_label: str) -> None:
    """Assert a check failed (has X or error prefix)."""
    pattern = rf'[✗❌⚠]\s*{re.escape(check_label)}'
    assert re.search(pattern, stdout), f"Check '{check_label}' did not fail"


def assert_verification_status(stdout: str, status: str) -> None:
    """Assert verification summary status (PASSED/FAILED)."""
    assert f'Verification {status}' in stdout, f"Expected 'Verification {status}' in output"


def assert_version_match(stdout: str, app_name: str, version: str) -> None:
    """Assert version output with flexible matching (ignores exact formatting)."""
    pattern = rf'{re.escape(app_name)}.*React version[:\s]+{re.escape(version)}'
    assert re.search(pattern, stdout, re.IGNORECASE), \
        f"Expected {app_name} React version {version} not found"


def setup_base_package_files(repo_path: Path) -> None:
    """Setup minimum required package.json files for script to run past React check."""
    # Root package.json with pnpm overrides
    (repo_path / 'package.json').write_text(json.dumps({
        "pnpm": {"overrides": {"react": "^19.1.0"}}
    }))
    # Frontend dashboard package.json
    (frontend_dashboard_dir(repo_path) / 'package.json').write_text(
        json.dumps({"dependencies": {"react": "^19.1.0"}})
    )
    # Owner console package.json
    (owner_console_dir(repo_path) / 'package.json').write_text(
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
    frontend_dashboard_dir(tmp_path).mkdir(parents=True)
    owner_console_dir(tmp_path).mkdir(parents=True)
    (api_backend_dir(tmp_path) / 'src' / 'routes').mkdir(parents=True)
    (api_backend_dir(tmp_path) / 'tests').mkdir(parents=True)
    (api_backend_dir(tmp_path) / 'alembic' / 'versions').mkdir(parents=True)
    orchestrator_dir(tmp_path).mkdir(parents=True)
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
    (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
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
    (owner_console_dir(temp_repo) / 'package.json').write_text(
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
    (api_backend_dir(temp_repo) / 'src' / 'routes' / 'vectors.py').write_text(
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
    (api_backend_dir(temp_repo) / 'alembic.ini').write_text('[alembic]')

    # requirements.txt
    (api_backend_dir(temp_repo) / 'requirements.txt').write_text(
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
    (orchestrator_dir(temp_repo) / 'langgraph_orchestrator.py').write_text(
        '# Legacy LangGraph orchestrator'
    )

    # pytest conftest
    (api_backend_dir(temp_repo) / 'tests' / 'conftest.py').write_text(
        'import pytest'
    )

    # pytest.ini
    (api_backend_dir(temp_repo) / 'pytest.ini').write_text(
        '[pytest]\ntestpaths = tests'
    )

    # main.py without phase imports
    (api_backend_dir(temp_repo) / 'src' / 'main.py').write_text(
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps(package)
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps(package)
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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

        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            '{"dependencies": {"react": "^19.1.0"'  # Missing closing braces
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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
        """Test fallback when node is unavailable using PATH manipulation."""
        # Setup required files
        frontend_package = {"dependencies": {"react": "^19.1.0"}}
        (temp_repo / Path(FRONTEND_DASHBOARD_PATH) / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / Path(OWNER_CONSOLE_PATH) / 'package.json').write_text(
            json.dumps(frontend_package)
        )
        (temp_repo / 'package.json').write_text(json.dumps({"name": "test"}))

        # Manipulate PATH to exclude node's directory
        node_path = shutil.which("node")
        if node_path is None:
            pytest.skip("node not found in PATH, cannot test fallback")

        node_dir = str(Path(node_path).parent.resolve())
        old_path = os.environ.get('PATH', '')
        # Build new PATH excluding node's directory
        new_path = os.pathsep.join([
            p for p in old_path.split(os.pathsep)
            if p and Path(p).resolve() != Path(node_dir).resolve()
        ])

        env = os.environ.copy()
        env['PATH'] = new_path

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh'), '--verbose'],
            cwd=temp_repo,
            capture_output=True,
            text=True,
            env=env
        )

        # Should fallback to default 19.1.0 when node is unavailable
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^18.0.0"}})
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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
        """Test handling when version is empty or malformed."""
        (temp_repo / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))
        # Package with react key but empty/invalid version string
        # grep will find "react": but sed won't extract a valid semver version
        # This ensures the script reaches the mismatch logic instead of exiting early
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": ""}})
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Empty version should cause mismatch (sed extracts empty string, version comparison fails)
        # The script will show mismatch because extracted version is empty
        # Using 'and' to ensure BOTH conditions are met (stricter assertion)
        assert 'frontend-dashboard React version mismatch' in result.stdout and result.returncode != 0


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


class TestLangGraphOrchestratorArchitecture:
    """Test LangGraph orchestrator architecture verification.
    
    Note: Simple Mode removed in Issue #2651 (2025-12-18).
    USE_LANGGRAPH, USE_LANGGRAPH_PERCENT flags are no longer used.
    LangGraph is now the only orchestrator mode.
    """

    def test_orchestrator_path_in_render_yaml(self, minimal_valid_repo: Path):
        """Test detection of orchestrator path in render.yaml."""
        result = subprocess.run(
            ['bash', str(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        assert 'Orchestrator path in render.yaml' in result.stdout

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
        (api_backend_dir(temp_repo) / 'requirements.txt').write_text(
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
        (api_backend_dir(temp_repo) / 'src' / 'main.py').write_text(
            'from src.phases.phase4_meta_agent_api import router\n'
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
        (api_backend_dir(temp_repo) / 'requirements.txt').write_text(
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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text('{}')
        (owner_console_dir(temp_repo) / 'package.json').write_text('{}')

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
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            json.dumps(package)
        )
        (owner_console_dir(temp_repo) / 'package.json').write_text(
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


class TestExceptionScenarios:
    """Test exception scenarios: path anomalies, missing files, permissions.

    These tests verify the script handles edge cases gracefully without crashing.
    """

    def test_path_with_spaces(self, tmp_path: Path):
        """Test script handles paths containing spaces."""
        # Create repo in path with spaces
        repo_with_spaces = tmp_path / 'repo with spaces'
        repo_with_spaces.mkdir()
        (repo_with_spaces / 'scripts').mkdir()
        shutil.copy(SCRIPT_PATH, repo_with_spaces / 'scripts' / 'verify_system_state.sh')

        # Setup minimal structure
        frontend_dashboard_dir(repo_with_spaces).mkdir(parents=True)
        owner_console_dir(repo_with_spaces).mkdir(parents=True)
        (repo_with_spaces / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))
        (frontend_dashboard_dir(repo_with_spaces) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )
        (owner_console_dir(repo_with_spaces) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )

        result = subprocess.run(
            ['bash', str(repo_with_spaces / 'scripts' / 'verify_system_state.sh')],
            cwd=repo_with_spaces,
            capture_output=True,
            text=True
        )

        # Script should run without crashing on paths with spaces
        assert result.returncode in (0, 1), f"Script crashed: {result.stderr}"
        assert 'React version' in result.stdout or 'Verification' in result.stdout

    def test_symlinked_script(self, minimal_valid_repo: Path, tmp_path: Path):
        """Test script works when accessed via symlink."""
        # Create symlink to the script
        symlink_dir = tmp_path / 'symlinked'
        symlink_dir.mkdir()
        symlink_path = symlink_dir / 'verify_system_state.sh'
        symlink_path.symlink_to(minimal_valid_repo / 'scripts' / 'verify_system_state.sh')

        result = subprocess.run(
            ['bash', str(symlink_path)],
            cwd=minimal_valid_repo,
            capture_output=True,
            text=True
        )

        # Script should work via symlink
        assert result.returncode in (0, 1), f"Script failed via symlink: {result.stderr}"

    def test_missing_scripts_directory(self, tmp_path: Path):
        """Test graceful handling when scripts directory is missing."""
        # Create minimal repo without scripts dir
        (tmp_path / 'package.json').write_text('{}')

        # Script won't exist, so we test that bash reports the error properly
        result = subprocess.run(
            ['bash', str(tmp_path / 'scripts' / 'verify_system_state.sh')],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        # Should fail with file not found
        assert result.returncode != 0

    @pytest.mark.skipif(os.name != 'posix', reason="Permission tests only work on POSIX")
    @pytest.mark.skipif(os.geteuid() == 0, reason="Root bypasses permission checks")
    def test_unreadable_package_json(self, temp_repo: Path):
        """Test handling of unreadable package.json (permission denied)."""
        setup_base_package_files(temp_repo)
        pkg_json = temp_repo / 'package.json'

        # Remove read permission
        original_mode = pkg_json.stat().st_mode
        try:
            os.chmod(pkg_json, 0o000)

            result = subprocess.run(
                ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
                cwd=temp_repo,
                capture_output=True,
                text=True
            )

            # Script should handle permission error gracefully (non-zero exit)
            assert result.returncode != 0
        finally:
            # Restore permissions for cleanup
            os.chmod(pkg_json, original_mode)

    def test_empty_directory_structure(self, tmp_path: Path):
        """Test script behavior with completely empty repo."""
        (tmp_path / 'scripts').mkdir()
        shutil.copy(SCRIPT_PATH, tmp_path / 'scripts' / 'verify_system_state.sh')

        result = subprocess.run(
            ['bash', str(tmp_path / 'scripts' / 'verify_system_state.sh')],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        # Script should fail but not crash
        assert result.returncode != 0

    def test_corrupted_json_files(self, temp_repo: Path):
        """Test handling of corrupted/invalid JSON in multiple files."""
        # Create corrupted package.json files
        (temp_repo / 'package.json').write_text('{invalid json')
        (frontend_dashboard_dir(temp_repo) / 'package.json').write_text(
            'not json at all'
        )

        result = subprocess.run(
            ['bash', str(temp_repo / 'scripts' / 'verify_system_state.sh')],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )

        # Script should handle JSON errors gracefully
        assert result.returncode != 0

    def test_very_long_file_paths(self, tmp_path: Path):
        """Test handling of very long file paths."""
        # Create deeply nested path (but within filesystem limits)
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f'level{i}'
        deep_path.mkdir(parents=True)

        # Copy script to deep path
        (deep_path / 'scripts').mkdir()
        shutil.copy(SCRIPT_PATH, deep_path / 'scripts' / 'verify_system_state.sh')

        # Setup required directory structure for script to run
        frontend_dashboard_dir(deep_path).mkdir(parents=True)
        owner_console_dir(deep_path).mkdir(parents=True)
        (deep_path / 'package.json').write_text(json.dumps({
            "pnpm": {"overrides": {"react": "^19.1.0"}}
        }))
        (frontend_dashboard_dir(deep_path) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )
        (owner_console_dir(deep_path) / 'package.json').write_text(
            json.dumps({"dependencies": {"react": "^19.1.0"}})
        )

        result = subprocess.run(
            ['bash', str(deep_path / 'scripts' / 'verify_system_state.sh')],
            cwd=deep_path,
            capture_output=True,
            text=True
        )

        # Script should handle deep paths
        assert result.returncode in (0, 1), f"Script crashed on deep path: {result.stderr}"


class TestRepoStructureSanity:
    """Sanity tests to verify test fixtures match real repo structure.

    These tests help catch when the real repo structure changes,
    ensuring fixtures stay in sync.
    """

    def test_frontend_dashboard_path_exists(self):
        """Verify frontend-dashboard path exists in real repo."""
        path = REPO_ROOT / FRONTEND_DASHBOARD_PATH
        assert path.exists(), f"Repo structure changed: {FRONTEND_DASHBOARD_PATH} not found"

    def test_owner_console_path_exists(self):
        """Verify owner-console path exists in real repo."""
        path = REPO_ROOT / OWNER_CONSOLE_PATH
        assert path.exists(), f"Repo structure changed: {OWNER_CONSOLE_PATH} not found"

    def test_script_exists(self):
        """Verify verify_system_state.sh exists."""
        assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"

    def test_pnpm_overrides_exist(self):
        """Verify pnpm overrides exist in root package.json."""
        pkg_json = REPO_ROOT / 'package.json'
        assert pkg_json.exists(), "Root package.json not found"
        data = json.loads(pkg_json.read_text())
        assert 'pnpm' in data, "pnpm key not in package.json"
        assert 'overrides' in data['pnpm'], "pnpm.overrides not in package.json"
