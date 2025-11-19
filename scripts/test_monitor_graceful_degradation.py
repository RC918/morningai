"""Test monitor_orchestrator graceful degradation"""
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import pytest


def test_monitor_runs_without_slack_webhook():
    """Test that monitor runs successfully without SLACK_WEBHOOK_URL configured"""
    # Clear environment
    if 'SLACK_WEBHOOK_URL' in os.environ:
        del os.environ['SLACK_WEBHOOK_URL']
    
    # Mock settings to return None for slack_webhook_url
    with patch('monitor_orchestrator.settings') as mock_settings:
        mock_settings.slack_webhook_url = None
        mock_settings.orchestrator_api_url = "https://test-api.example.com"
        
        # Capture stdout
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            # Import and run main
            from monitor_orchestrator import main
            
            # Should not raise SystemExit(1)
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Check that it exited (could be 0 or 1 depending on health check)
            # but NOT with the "SLACK_WEBHOOK_URL not set" error
            output = captured_output.getvalue()
            assert "[WARNING] SLACK_WEBHOOK_URL not configured" in output
            assert "[INFO] Continuing with health checks" in output


def test_slack_alert_graceful_skip():
    """Test that send_slack_alert gracefully skips when webhook is empty"""
    from monitor_orchestrator import OrchestratorMonitor
    
    # Create monitor with empty webhook
    monitor = OrchestratorMonitor("https://test-api.example.com", "")
    
    # Capture stdout
    captured_output = StringIO()
    
    with patch('sys.stdout', captured_output):
        # Should return True and print to console instead
        result = monitor.send_slack_alert("Test message", severity="warning")
        
        assert result is True
        output = captured_output.getvalue()
        assert "[WARNING]" in output
        assert "Test message" in output


def test_slack_alert_with_webhook():
    """Test that send_slack_alert sends to Slack when webhook is configured"""
    from monitor_orchestrator import OrchestratorMonitor
    
    # Create monitor with webhook
    monitor = OrchestratorMonitor(
        "https://test-api.example.com",
        "https://hooks.slack.com/services/TEST"
    )
    
    # Mock requests.post
    with patch('monitor_orchestrator.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Should send to Slack
        result = monitor.send_slack_alert("Test message", severity="critical")
        
        assert result is True
        assert mock_post.called
        assert mock_post.call_args[0][0] == "https://hooks.slack.com/services/TEST"
