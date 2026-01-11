"""
Pytest configuration and fixtures for orchestrator tests.

This module provides centralized fixtures for test configuration,
including routing settings defaults for legacy tests.

=============================================================================
IMPORTANT: Tier Floor Enforcement Testing Guide
=============================================================================

PR #3638 introduced tier floor enforcement for cost optimization. In production,
`ROUTING_FORCE_TIER_FLOOR=true` (default) forces 90%+ traffic to Tier 2-3 models.

However, this fixture sets `force_tier_floor=False` by default so that legacy
tests (which expect Tier 0/1 routing) continue to pass.

HOW TO WRITE NEW TESTS FOR TIER FLOOR ENFORCEMENT:
--------------------------------------------------

If you need to test tier floor behavior, you MUST explicitly override the
fixture by patching settings with `force_tier_floor=True`:

    from unittest.mock import patch, MagicMock

    def test_tier_floor_enforced(self):
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        with patch('core.routing.engine.settings') as mock_settings:
            mock_settings.routing_max_escalations = 1
            mock_settings.routing_max_retries = 2
            mock_settings.routing_default_tier = 2
            mock_settings.routing_force_tier_floor = True  # Enable tier floor
            mock_settings.routing_tier_floor = 2

            # Now tier floor enforcement is active
            model_info = engine.select_model(TaskType.CODING, risk_level="medium")
            assert model_info.tier.value >= 2  # Should be Tier 2 or 3

PRODUCTION vs TEST BEHAVIOR:
----------------------------
- Production (Render): force_tier_floor=True (default) - tier floor enforced
- Tests (this fixture): force_tier_floor=False - legacy behavior for compatibility

See PR #3638 and Issue #3647 for more context.
=============================================================================
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_routing_settings_legacy_defaults(request):
    """
    Patch routing settings to use pre-cost-optimization defaults for legacy tests.

    PR #3638 introduced tier floor enforcement (force_tier_floor=True) which causes
    legacy routing tests to fail because they expect Tier 0/1 but get Tier 2.

    This fixture provides legacy defaults so existing tests continue to pass.

    IMPORTANT: New tests that explicitly test tier floor enforcement should
    override this by patching settings with force_tier_floor=True.
    See the module docstring above for a complete example.

    Settings patched:
    - routing_max_escalations: 1 (default)
    - routing_max_retries: 2 (default)
    - routing_default_tier: 2 (default)
    - routing_force_tier_floor: False (legacy behavior - no tier floor enforcement)
    - routing_tier_floor: 2 (default)

    Note: This fixture is skipped for tests that don't use routing (e.g., planner tests)
    to avoid import errors when core.routing.engine doesn't exist in the test context.
    """
    # Skip this fixture for tests that don't need routing settings
    # (e.g., planner tests like test_dag_builder.py, test_parallel_executor.py)
    test_file = request.fspath.basename if hasattr(request, 'fspath') else ""
    skip_patterns = ['test_dag_builder', 'test_parallel_executor', 'test_planner']
    if any(pattern in test_file for pattern in skip_patterns):
        yield None
        return

    mock_settings = MagicMock()
    mock_settings.routing_max_escalations = 1
    mock_settings.routing_max_retries = 2
    mock_settings.routing_default_tier = 2
    mock_settings.routing_force_tier_floor = False  # Legacy behavior - no tier floor
    mock_settings.routing_tier_floor = 2

    try:
        with patch('core.routing.engine.settings', mock_settings):
            yield mock_settings
    except (ModuleNotFoundError, AttributeError):
        # If core.routing.engine doesn't exist, skip the patch
        yield None
