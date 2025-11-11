"""Test SLACK_WEBHOOK_URL alias configuration"""
import os
import pytest
from common.config.settings import Settings


def test_slack_webhook_url_from_env():
    """Test that SLACK_WEBHOOK_URL is loaded from environment variable"""
    test_url = "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
    
    # Set environment variable
    os.environ['SLACK_WEBHOOK_URL'] = test_url
    
    try:
        # Create new settings instance
        settings = Settings()
        
        # Verify the URL is loaded correctly
        assert settings.slack_webhook_url == test_url
        assert settings.slack_webhook_url is not None
    finally:
        # Clean up
        if 'SLACK_WEBHOOK_URL' in os.environ:
            del os.environ['SLACK_WEBHOOK_URL']


def test_slack_webhook_url_repr_false():
    """Test that slack_webhook_url has repr=False to avoid logging"""
    from pydantic.fields import FieldInfo
    
    # Get the field info
    field_info = Settings.model_fields['slack_webhook_url']
    
    # Verify repr=False is set
    assert field_info.repr is False, "slack_webhook_url should have repr=False to avoid logging secrets"


def test_slack_webhook_url_optional():
    """Test that slack_webhook_url is optional and defaults to None"""
    # Clear environment
    if 'SLACK_WEBHOOK_URL' in os.environ:
        del os.environ['SLACK_WEBHOOK_URL']
    
    settings = Settings()
    
    # Should be None when not set
    assert settings.slack_webhook_url is None
