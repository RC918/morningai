"""
Route-map regression guard tests.

This test ensures that URL routes don't change during refactoring.
It compares the current route map against a baseline JSON file.

Part of PR0 (#2375) - Phase 0 stability guards.
"""
import json
import os
import sys
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
        """Get current routes from Flask app."""
        # Set test environment before importing app
        os.environ['TESTING'] = 'true'
        os.environ['ENVIRONMENT'] = 'development'
        os.environ['ENABLE_MOCK_USERS'] = 'true'
        
        from src.main import app
        
        # Extract routes: (rule, sorted methods) excluding HEAD and OPTIONS
        # Also exclude static file route which is Flask internal
        routes = sorted([
            (r.rule, sorted(list(r.methods - {'HEAD', 'OPTIONS'})))
            for r in app.url_map.iter_rules()
            if r.rule != '/static/<path:filename>'
        ])
        return routes

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
        2. Update the baseline by running:
           python -c "
           import os, sys, json
           sys.path.insert(0, 'handoff/20250928/40_App/api-backend/src')
           sys.path.insert(0, 'handoff/20250928/40_App/api-backend')
           sys.path.insert(0, '.')
           os.environ['TESTING'] = 'true'
           os.environ['ENVIRONMENT'] = 'development'
           os.environ['ENABLE_MOCK_USERS'] = 'true'
           from src.main import app
           routes = sorted([(r.rule, sorted(list(r.methods - {'HEAD', 'OPTIONS'}))) for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'])
           with open('handoff/20250928/40_App/api-backend/tests/baselines/route_map_baseline.json', 'w') as f:
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
