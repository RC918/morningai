#!/usr/bin/env python3
"""
Tests for Notification Service
"""
import pytest
import os
from unittest.mock import AsyncMock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.notification_service import NotificationService, create_notification_service


class TestNotificationService:
    """Tests for NotificationService"""
    
    @pytest.fixture
    def notification_service(self):
        """Create notification service for testing"""
        return NotificationService(
            mailtrap_token="test_token",
            slack_webhook_url="https://hooks.slack.com/test",
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="test_pass"
        )
    
    def test_initialization(self, notification_service):
        """Test NotificationService initialization"""
        assert notification_service.mailtrap_token == "test_token"
        assert notification_service.slack_webhook_url == "https://hooks.slack.com/test"
        assert notification_service.smtp_user == "test@test.com"
    
    @pytest.mark.asyncio
    async def test_send_email_mailtrap_success(self, notification_service):
        """Test sending email via Mailtrap"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_post.return_value = mock_response
            
            result = await notification_service.send_email_mailtrap(
                to="user@test.com",
                subject="Test Alert",
                body="This is a test alert"
            )
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_email_mailtrap_no_token(self):
        """Test sending email without token"""
        service = NotificationService()
        
        result = await service.send_email_mailtrap(
            to="user@test.com",
            subject="Test",
            body="Test"
        )
        
        assert result['success'] is False
        assert 'token not configured' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_slack_message_success(self, notification_service):
        """Test sending Slack message"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_post.return_value = mock_response
            
            result = await notification_service.send_slack_message(
                message="Test alert message"
            )
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_slack_message_no_webhook(self):
        """Test sending Slack message without webhook"""
        service = NotificationService()
        
        result = await service.send_slack_message(
            message="Test"
        )
        
        assert result['success'] is False
        assert 'webhook' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, notification_service):
        """Test sending webhook"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_post.return_value = mock_response
            
            result = await notification_service.send_webhook(
                url="https://example.com/webhook",
                payload={"test": "data"}
            )
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_notification_email(self, notification_service):
        """Test send_notification with email channel"""
        with patch.object(notification_service, 'send_email_mailtrap', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {'success': True}
            
            result = await notification_service.send_notification(
                channel="email",
                message="Test alert",
                to="user@test.com",
                subject="Alert"
            )
            
            assert result['success'] is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification_slack(self, notification_service):
        """Test send_notification with Slack channel"""
        with patch.object(notification_service, 'send_slack_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {'success': True}
            
            result = await notification_service.send_notification(
                channel="slack",
                message="Test alert"
            )
            
            assert result['success'] is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification_webhook(self, notification_service):
        """Test send_notification with webhook channel"""
        with patch.object(notification_service, 'send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {'success': True}
            
            result = await notification_service.send_notification(
                channel="webhook",
                message="Test alert",
                url="https://example.com/webhook"
            )
            
            assert result['success'] is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification_sms(self, notification_service):
        """Test send_notification with SMS channel (not implemented)"""
        result = await notification_service.send_notification(
            channel="sms",
            message="Test"
        )
        
        assert result['success'] is False
        assert 'not yet implemented' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_notification_invalid_channel(self, notification_service):
        """Test send_notification with invalid channel"""
        result = await notification_service.send_notification(
            channel="invalid",
            message="Test"
        )
        
        assert result['success'] is False
        assert 'Invalid channel' in result['error']


class TestNotificationServiceIntegration:
    """Integration tests with real services"""
    
    @pytest.mark.skipif(
        not os.getenv('Mailtrap_API_TOKEN'),
        reason="Mailtrap_API_TOKEN not set - skipping integration test"
    )
    @pytest.mark.asyncio
    async def test_send_email_mailtrap_real(self):
        """Test real Mailtrap email sending"""
        service = NotificationService(
            mailtrap_token=os.getenv('Mailtrap_API_TOKEN')
        )
        
        result = await service.send_email_mailtrap(
            to="test@example.com",
            subject="Ops Agent Test",
            body="This is a test email from Ops Agent notification system"
        )
        
        assert 'success' in result
        
        if result['success']:
            print("\n✅ Email sent successfully via Mailtrap")
        else:
            print(f"\n⚠️ Email failed: {result.get('error')}")


class TestNotificationServiceFactory:
    """Tests for notification service factory function"""
    
    def test_create_notification_service(self):
        """Test factory function"""
        service = create_notification_service(
            mailtrap_token="test_token"
        )
        
        assert isinstance(service, NotificationService)
        assert service.mailtrap_token == "test_token"
    
    def test_create_notification_service_no_params(self):
        """Test factory function without parameters"""
        service = create_notification_service()
        
        assert isinstance(service, NotificationService)
        assert service.mailtrap_token is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
