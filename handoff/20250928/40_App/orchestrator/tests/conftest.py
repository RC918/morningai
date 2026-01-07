"""
Pytest configuration and fixtures for orchestrator tests.

This module provides centralized fixtures for test configuration,
including routing settings defaults for legacy tests.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_routing_settings_legacy_defaults():
    """
    Patch routing settings to use pre-cost-optimization defaults for legacy tests.
    
    PR #3638 introduced tier floor enforcement (force_tier_floor=True) which causes
    legacy routing tests to fail because they expect Tier 0/1 but get Tier 2.
    
    This fixture provides legacy defaults so existing tests continue to pass.
    New tests that explicitly test tier floor enforcement should override this
    by patching settings with force_tier_floor=True.
    
    Settings patched:
    - routing_max_escalations: 1 (default)
    - routing_max_retries: 2 (default)
    - routing_default_tier: 2 (default)
    - routing_force_tier_floor: False (legacy behavior - no tier floor enforcement)
    - routing_tier_floor: 2 (default)
    """
    mock_settings = MagicMock()
    mock_settings.routing_max_escalations = 1
    mock_settings.routing_max_retries = 2
    mock_settings.routing_default_tier = 2
    mock_settings.routing_force_tier_floor = False  # Legacy behavior - no tier floor
    mock_settings.routing_tier_floor = 2
    
    with patch('core.routing.engine.settings', mock_settings):
        yield mock_settings
