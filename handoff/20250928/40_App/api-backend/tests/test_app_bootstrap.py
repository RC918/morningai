"""Smoke tests for application bootstrap.

These tests verify that the Flask application can be imported and initialized
correctly. They serve as a safety net during Phase 1 refactoring to catch
any import errors or initialization failures early.

Part of Phase 1 pre-work for main.py refactoring.
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import pytest


class TestAppBootstrap:
    """Verify application can be imported and initialized correctly."""

    def test_import_main_does_not_crash(self):
        """Verify main.py can be imported without errors."""
        import src.main
        assert src.main.app is not None

    def test_app_is_flask_instance(self):
        """Verify app is a Flask instance."""
        from src.main import app
        from flask import Flask
        assert isinstance(app, Flask)

    def test_health_endpoint_returns_ok(self):
        """Verify health endpoint is accessible."""
        from src.main import app
        with app.test_client() as client:
            response = client.get('/health')
            # 503 is acceptable if DB is unavailable in test environment
            assert response.status_code in (200, 503)
            data = response.get_json()
            assert 'status' in data
            assert 'version' in data

    def test_app_has_url_map(self):
        """Verify app has routes registered."""
        from src.main import app
        # Should have at least the health endpoint
        rules = list(app.url_map.iter_rules())
        assert len(rules) > 0
        
        # Verify health endpoint exists
        health_rules = [r for r in rules if r.rule == '/health']
        assert len(health_rules) == 1

    def test_app_has_blueprints(self):
        """Verify app has blueprints registered."""
        from src.main import app
        # Should have multiple blueprints registered
        assert len(app.blueprints) > 0

    def test_livez_endpoint_returns_alive(self):
        """Verify /livez liveness endpoint returns correct response.

        The /livez endpoint is a pure liveness probe that does not touch
        DB or Redis. It should always return 200 with {"status": "alive"}.
        """
        from src.main import app
        with app.test_client() as client:
            response = client.get('/livez')
            assert response.status_code == 200
            data = response.get_json()
            assert data == {"status": "alive"}

    def test_api_livez_endpoint_returns_alive(self):
        """Verify /api/livez liveness endpoint returns correct response.

        The /api/livez endpoint is the API-prefixed version of the liveness
        probe. It should behave identically to /livez.
        """
        from src.main import app
        with app.test_client() as client:
            response = client.get('/api/livez')
            assert response.status_code == 200
            data = response.get_json()
            assert data == {"status": "alive"}

    def test_livez_routes_registered(self):
        """Verify /livez routes are registered in the URL map."""
        from src.main import app
        rules = list(app.url_map.iter_rules())

        livez_rules = [r for r in rules if r.rule == '/livez']
        assert len(livez_rules) == 1, "/livez route should be registered"

        api_livez_rules = [r for r in rules if r.rule == '/api/livez']
        assert len(api_livez_rules) == 1, "/api/livez route should be registered"
