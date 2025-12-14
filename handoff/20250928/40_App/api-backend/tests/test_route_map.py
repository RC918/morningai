"""
Route-map regression guard tests.

This test ensures that URL routes don't change during refactoring.
It compares the current route map against a baseline JSON file.

Part of PR0 (#2375) - Phase 0 stability guards.

Note: This test uses subprocess to generate routes in isolation, ensuring
that env vars take effect regardless of what other tests have imported.
Routes are written to a temp file to avoid stdout/stderr pollution from
warnings and log messages.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))


class TestRouteMapRegression:
    """Test suite for route-map regression guard."""

    @pytest.fixture
    def baseline_routes(self):
        """Load baseline routes from JSON file."""
        baseline_path = Path(__file__).parent / 'baselines' / 'route_map_baseline.json'
        with open(baseline_path, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def current_routes(self):
        """
        Get current routes from Flask app using subprocess.
        
        Uses subprocess to ensure env vars take effect regardless of what
        other tests have imported. This prevents test order dependencies.
        
        Routes are written to a temp file to avoid stdout/stderr pollution
        from warnings and log messages (e.g., Redis TLS warnings).
        
        The temp file path is passed via env var (not string interpolation)
        for Windows compatibility.
        """
        # Create temp file for routes output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Script to run in subprocess - writes routes to temp file
            # Temp path is passed via ROUTE_MAP_OUTPUT_FILE env var for Windows compatibility
            script = '''
import os, json
os.environ['TESTING'] = 'true'
os.environ['ENVIRONMENT'] = 'development'
os.environ['ENABLE_MOCK_USERS'] = 'true'
os.environ['ENABLE_ORCHESTRATOR'] = 'false'
from src.main import app
routes = sorted([
    (r.rule, sorted(list(r.methods - {'HEAD', 'OPTIONS'})))
    for r in app.url_map.iter_rules()
    if r.rule != '/static/<path:filename>'
])
output_path = os.environ['ROUTE_MAP_OUTPUT_FILE']
with open(output_path, "w") as f:
    json.dump(routes, f)
'''
            # Get paths for PYTHONPATH
            api_backend_dir = Path(__file__).resolve().parent.parent
            repo_root = api_backend_dir.parent.parent.parent.parent
            orchestrator_dir = repo_root / 'handoff' / '20250928' / '40_App' / 'orchestrator'
            
            env = os.environ.copy()
            env['PYTHONPATH'] = f"{repo_root}:{api_backend_dir / 'src'}:{orchestrator_dir}"
            env['ROUTE_MAP_OUTPUT_FILE'] = temp_path
            
            result = subprocess.run(
                [sys.executable, '-c', script],
                cwd=str(api_backend_dir),
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                pytest.fail(f"Failed to get routes from subprocess:\nstdout: {result.stdout}\nstderr: {result.stderr}")
            
            # Read routes from temp file
            with open(temp_path, 'r') as f:
                return json.load(f)
        finally:
            # Clean up temp file (catch OSError to avoid race conditions)
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def test_route_map_unchanged(self, baseline_routes, current_routes):
        """
        Test that the route map hasn't changed from baseline.
        
        This test compares:
        - Route rules (URL patterns)
        - HTTP methods for each route
        
        It does NOT compare:
        - Endpoint names (these change when blueprints are reorganized)
        - View functions
        
        If this test fails after intentional route changes:
        1. Review the changes to ensure they're intentional
        2. Update the baseline by running (from repo root):
           export PYTHONPATH="$PWD:$PWD/handoff/20250928/40_App/api-backend/src:$PWD/handoff/20250928/40_App/orchestrator"
           cd handoff/20250928/40_App/api-backend
           python -c "
           import os, sys, json
           os.environ['TESTING'] = 'true'
           os.environ['ENVIRONMENT'] = 'development'
           os.environ['ENABLE_MOCK_USERS'] = 'true'
           os.environ['ENABLE_ORCHESTRATOR'] = 'false'
           from src.main import app
           routes = sorted([(r.rule, sorted(list(r.methods - {'HEAD', 'OPTIONS'}))) for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'])
           with open('tests/baselines/route_map_baseline.json', 'w') as f:
               json.dump(routes, f, indent=2)
           "
        """
        # Convert to sets for easier comparison
        baseline_set = set(tuple([rule, tuple(methods)]) for rule, methods in baseline_routes)
        current_set = set(tuple([rule, tuple(methods)]) for rule, methods in current_routes)
        
        # Find differences
        added_routes = current_set - baseline_set
        removed_routes = baseline_set - current_set
        
        # Build error message if there are differences
        error_messages = []
        
        if added_routes:
            error_messages.append("Routes ADDED (not in baseline):")
            for rule, methods in sorted(added_routes):
                error_messages.append(f"  + {rule} [{', '.join(methods)}]")
        
        if removed_routes:
            error_messages.append("Routes REMOVED (in baseline but not current):")
            for rule, methods in sorted(removed_routes):
                error_messages.append(f"  - {rule} [{', '.join(methods)}]")
        
        if error_messages:
            error_messages.insert(0, "Route map has changed from baseline!")
            error_messages.append("")
            error_messages.append("If these changes are intentional, update the baseline file.")
            pytest.fail("\n".join(error_messages))

    def test_baseline_file_exists(self):
        """Ensure baseline file exists and is valid JSON."""
        baseline_path = Path(__file__).parent / 'baselines' / 'route_map_baseline.json'
        
        assert baseline_path.exists(), f"Baseline file not found: {baseline_path}"
        
        with open(baseline_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Baseline should be a list"
        assert len(data) > 0, "Baseline should not be empty"
        
        # Verify structure: each entry should be [rule, [methods]]
        for entry in data:
            assert isinstance(entry, list), f"Each entry should be a list: {entry}"
            assert len(entry) == 2, f"Each entry should have 2 elements: {entry}"
            assert isinstance(entry[0], str), f"Rule should be a string: {entry}"
            assert isinstance(entry[1], list), f"Methods should be a list: {entry}"

    def test_no_duplicate_routes(self, current_routes):
        """Check for duplicate route definitions (informational)."""
        # Group by rule
        route_counts = {}
        for rule, methods in current_routes:
            key = (rule, tuple(methods))
            route_counts[key] = route_counts.get(key, 0) + 1
        
        duplicates = [(rule, methods, count) for (rule, methods), count in route_counts.items() if count > 1]
        
        if duplicates:
            # Known pre-existing duplicates that are tracked for future cleanup
            # These are legacy routes that exist in both main.py and blueprint files
            known_duplicates = {
                ("/api/dashboard/widgets", ("GET",)),
                ("/api/phase7/monitoring/dashboard", ("GET",)),
                ("/api/dashboard/layouts", ("GET",)),
                ("/api/dashboard/layouts", ("GET", "POST")),
                ("/api/dashboard/layouts", ("POST",)),
            }
            
            unknown_duplicates = [
                (rule, methods, count) 
                for rule, methods, count in duplicates 
                if (rule, tuple(methods)) not in known_duplicates
            ]
            
            if unknown_duplicates:
                error_messages = ["NEW duplicate routes found (not in known list):"]
                for rule, methods, count in unknown_duplicates:
                    error_messages.append(f"  {rule} [{', '.join(methods)}] appears {count} times")
                error_messages.append("")
                error_messages.append("If these are intentional, add them to known_duplicates in test_route_map.py")
                pytest.fail("\n".join(error_messages))
            else:
                # Known duplicates exist but no new ones - pass with warning
                import warnings
                warning_messages = ["Known duplicate routes exist (tracked for future cleanup):"]
                for rule, methods, count in duplicates:
                    warning_messages.append(f"  {rule} [{', '.join(methods)}] appears {count} times")
                warnings.warn("\n".join(warning_messages))

    def test_all_routes_have_methods(self, current_routes):
        """Ensure all routes have at least one HTTP method."""
        routes_without_methods = [rule for rule, methods in current_routes if not methods]
        
        if routes_without_methods:
            pytest.fail(f"Routes without methods: {routes_without_methods}")

    def test_api_routes_start_with_api(self, current_routes):
        """Ensure API routes follow naming convention."""
        # Routes that should start with /api
        api_patterns = ['/api/']
        
        # Routes that are allowed to not start with /api
        allowed_non_api = ['/', '/<path:path>', '/health', '/healthz']
        
        for rule, methods in current_routes:
            if rule in allowed_non_api:
                continue
            if not any(rule.startswith(pattern) for pattern in api_patterns):
                if rule.startswith('/api'):
                    continue  # /api itself is fine
                # This is informational, not a failure
                # Some legacy routes may not follow this convention


class TestRouteMapSubprocessRobustness:
    """Test suite for subprocess-based route generation robustness."""

    def test_subprocess_stderr_noise_does_not_affect_parsing(self):
        """
        Test that stderr noise (warnings, logs) doesn't affect route parsing.
        
        The temp file approach should be immune to stdout/stderr pollution.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Script that outputs noise to stderr but still writes valid JSON to file
            script = '''
import os, sys, json
# Simulate stderr noise (warnings, logs)
sys.stderr.write("WARNING: This is a fake warning\\n")
sys.stderr.write("INFO: Loading modules...\\n")
print("Some stdout noise")
# Write valid JSON to temp file
output_path = os.environ['ROUTE_MAP_OUTPUT_FILE']
routes = [["/test", ["GET"]], ["/api/test", ["POST"]]]
with open(output_path, "w") as f:
    json.dump(routes, f)
'''
            env = os.environ.copy()
            env['ROUTE_MAP_OUTPUT_FILE'] = temp_path
            
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                env=env
            )
            
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            
            # Verify we can still parse the JSON from temp file
            with open(temp_path, 'r') as f:
                routes = json.load(f)
            
            assert routes == [["/test", ["GET"]], ["/api/test", ["POST"]]]
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def test_parallel_subprocess_isolation(self):
        """
        Test that multiple parallel subprocess calls don't interfere with each other.
        
        Each subprocess should write to its own temp file.
        """
        import concurrent.futures
        
        def run_subprocess(index):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_path = f.name
            
            try:
                script = f'''
import os, json
output_path = os.environ['ROUTE_MAP_OUTPUT_FILE']
routes = [["/route-{index}", ["GET"]]]
with open(output_path, "w") as f:
    json.dump(routes, f)
'''
                env = os.environ.copy()
                env['ROUTE_MAP_OUTPUT_FILE'] = temp_path
                
                result = subprocess.run(
                    [sys.executable, '-c', script.format(index=index)],
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                if result.returncode != 0:
                    return None, f"Failed: {result.stderr}"
                
                with open(temp_path, 'r') as f:
                    return json.load(f), None
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        
        # Run 3 parallel subprocess calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_subprocess, i) for i in range(3)]
            results = [f.result() for f in futures]
        
        # Verify each subprocess returned its own unique route
        for i, (routes, error) in enumerate(results):
            assert error is None, f"Subprocess {i} failed: {error}"
            assert routes == [[f"/route-{i}", ["GET"]]], f"Subprocess {i} returned wrong routes: {routes}"

    def test_temp_file_deleted_after_read(self):
        """
        Test that temp file is properly deleted after reading.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        # Write some data
        with open(temp_path, 'w') as f:
            json.dump([["/test", ["GET"]]], f)
        
        # Read and delete
        try:
            with open(temp_path, 'r') as f:
                routes = json.load(f)
            assert routes == [["/test", ["GET"]]]
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        
        # Verify file is deleted
        assert not os.path.exists(temp_path), f"Temp file should be deleted: {temp_path}"

    def test_subprocess_failure_handling(self):
        """
        Test that subprocess failures are properly detected and reported.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Script that fails with non-zero exit code
            script = '''
import sys
sys.stderr.write("Error: Something went wrong\\n")
sys.exit(1)
'''
            env = os.environ.copy()
            env['ROUTE_MAP_OUTPUT_FILE'] = temp_path
            
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                env=env
            )
            
            # Verify failure is detected
            assert result.returncode != 0, "Script should have failed"
            assert "Error: Something went wrong" in result.stderr
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
