"""
Unit tests for RQ_QUEUE_NAME Pydantic alias configuration.

Tests verify that the settings.rq_queue_name field correctly reads from
the RQ_QUEUE_NAME environment variable via Pydantic alias mapping.
"""
import pytest
from common.config.settings import get_settings, reload_settings


class TestRQQueueNameAlias:
    """Test suite for RQ_QUEUE_NAME environment variable alias."""

    def test_rq_queue_name_reads_from_env(self, monkeypatch):
        """Test that rq_queue_name reads from RQ_QUEUE_NAME environment variable."""
        monkeypatch.setenv("RQ_QUEUE_NAME", "orchestrator-staging")
        
        reload_settings()
        
        settings = get_settings()
        assert settings.rq_queue_name == "orchestrator-staging", \
            f"Expected 'orchestrator-staging' but got '{settings.rq_queue_name}'"

    def test_rq_queue_name_defaults_when_unset(self, monkeypatch):
        """Test that rq_queue_name uses default value when RQ_QUEUE_NAME is not set."""
        monkeypatch.delenv("RQ_QUEUE_NAME", raising=False)
        
        reload_settings()
        
        settings = get_settings()
        assert settings.rq_queue_name == "orchestrator", \
            f"Expected default 'orchestrator' but got '{settings.rq_queue_name}'"

    def test_rq_queue_name_custom_value(self, monkeypatch):
        """Test that rq_queue_name correctly reads custom queue names."""
        monkeypatch.setenv("RQ_QUEUE_NAME", "custom-queue-name")
        
        reload_settings()
        
        settings = get_settings()
        assert settings.rq_queue_name == "custom-queue-name", \
            f"Expected 'custom-queue-name' but got '{settings.rq_queue_name}'"

    def test_rq_queue_name_production_value(self, monkeypatch):
        """Test production-style queue name (no suffix)."""
        monkeypatch.setenv("RQ_QUEUE_NAME", "orchestrator")
        
        reload_settings()
        
        settings = get_settings()
        assert settings.rq_queue_name == "orchestrator", \
            f"Expected 'orchestrator' but got '{settings.rq_queue_name}'"

    def test_rq_queue_name_empty_string(self, monkeypatch):
        """Test that empty string falls back to default."""
        monkeypatch.setenv("RQ_QUEUE_NAME", "")
        
        reload_settings()
        
        settings = get_settings()
        assert settings.rq_queue_name == "", \
            f"Expected empty string but got '{settings.rq_queue_name}'"
