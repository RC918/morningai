"""
Test to verify Sentry is disabled during tests
"""
import os
import pytest

from common.config.settings import settings


def test_sentry_dsn_is_removed():
    """Verify SENTRY_DSN is not set during tests"""
    assert settings.sentry_dsn is None, "SENTRY_DSN should be removed during tests"


def test_sentry_enabled_is_false():
    """Verify SENTRY_ENABLED is set to false"""
    assert settings.sentry_enabled == "false", "SENTRY_ENABLED should be 'false' during tests"


def test_testing_flag_is_true():
    """Verify TESTING environment variable is set"""
    assert settings.testing == "true", "TESTING should be 'true' during tests"
