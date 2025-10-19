#!/usr/bin/env python3
"""
Notification Service - Email, Slack, and Webhook notifications
"""
import logging
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationService:
    """Service for sending notifications through various channels"""
    
    def __init__(
        self,
        mailtrap_token: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None
    ):
        """
        Initialize Notification Service
        
        Args:
            mailtrap_token: Mailtrap API token for email
            slack_webhook_url: Slack webhook URL
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
        """
        self.mailtrap_token = mailtrap_token
        self.slack_webhook_url = slack_webhook_url
        self.smtp_host = smtp_host or "smtp.gmail.com"
        self.smtp_port = smtp_port or 587
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
    
    async def send_email_mailtrap(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str = "ops-agent@morningai.com"
    ) -> Dict[str, Any]:
        """
        Send email via Mailtrap API
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            from_email: Sender email
        
        Returns:
            Dict with result
        """
        if not self.mailtrap_token:
            return {
                'success': False,
                'error': 'Mailtrap token not configured'
            }
        
        try:
            url = "https://send.api.mailtrap.io/api/send"
            headers = {
                "Authorization": f"Bearer {self.mailtrap_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": {"email": from_email},
                "to": [{"email": to}],
                "subject": subject,
                "text": body,
                "category": "ops-agent-alerts"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Email sent successfully to {to}")
                        return {
                            'success': True,
                            'message': 'Email sent via Mailtrap'
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Mailtrap API error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Mailtrap API error: {response.status}',
                            'details': error_text
                        }
        
        except Exception as e:
            logger.error(f"Failed to send email via Mailtrap: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_email_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str = "ops-agent@morningai.com"
    ) -> Dict[str, Any]:
        """
        Send email via SMTP
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            from_email: Sender email
        
        Returns:
            Dict with result
        """
        if not self.smtp_user or not self.smtp_password:
            return {
                'success': False,
                'error': 'SMTP credentials not configured'
            }
        
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to} via SMTP")
            return {
                'success': True,
                'message': 'Email sent via SMTP'
            }
        
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_slack_message(
        self,
        message: str,
        channel: Optional[str] = None,
        username: str = "Ops Agent",
        icon_emoji: str = ":robot_face:"
    ) -> Dict[str, Any]:
        """
        Send message to Slack
        
        Args:
            message: Message text
            channel: Slack channel (optional, uses webhook default)
            username: Bot username
            icon_emoji: Bot icon emoji
        
        Returns:
            Dict with result
        """
        if not self.slack_webhook_url:
            return {
                'success': False,
                'error': 'Slack webhook URL not configured'
            }
        
        try:
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": icon_emoji
            }
            
            if channel:
                payload["channel"] = channel
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack message sent successfully")
                        return {
                            'success': True,
                            'message': 'Slack message sent'
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack API error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Slack API error: {response.status}',
                            'details': error_text
                        }
        
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send webhook notification
        
        Args:
            url: Webhook URL
            payload: Data to send
            headers: Optional HTTP headers
        
        Returns:
            Dict with result
        """
        try:
            request_headers = headers or {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=request_headers) as response:
                    if response.status < 400:
                        logger.info(f"Webhook sent successfully to {url}")
                        return {
                            'success': True,
                            'message': 'Webhook sent',
                            'status_code': response.status
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Webhook error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f'Webhook error: {response.status}',
                            'details': error_text
                        }
        
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_notification(
        self,
        channel: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send notification through specified channel
        
        Args:
            channel: Channel type (email, slack, webhook)
            message: Message content
            **kwargs: Channel-specific parameters
        
        Returns:
            Dict with result
        """
        try:
            channel_enum = NotificationChannel(channel)
            
            if channel_enum == NotificationChannel.EMAIL:
                if self.mailtrap_token:
                    return await self.send_email_mailtrap(
                        to=kwargs.get('to', kwargs.get('recipient')),
                        subject=kwargs.get('subject', 'Ops Agent Alert'),
                        body=message,
                        from_email=kwargs.get('from_email', 'ops-agent@morningai.com')
                    )
                else:
                    return await self.send_email_smtp(
                        to=kwargs.get('to', kwargs.get('recipient')),
                        subject=kwargs.get('subject', 'Ops Agent Alert'),
                        body=message,
                        from_email=kwargs.get('from_email', 'ops-agent@morningai.com')
                    )
            
            elif channel_enum == NotificationChannel.SLACK:
                return await self.send_slack_message(
                    message=message,
                    channel=kwargs.get('slack_channel') or kwargs.get('channel'),
                    username=kwargs.get('username', 'Ops Agent'),
                    icon_emoji=kwargs.get('icon_emoji', ':robot_face:')
                )
            
            elif channel_enum == NotificationChannel.WEBHOOK:
                return await self.send_webhook(
                    url=kwargs.get('url', kwargs.get('webhook_url')),
                    payload=kwargs.get('payload', {'message': message}),
                    headers=kwargs.get('headers')
                )
            
            elif channel_enum == NotificationChannel.SMS:
                logger.warning("SMS notifications not yet implemented")
                return {
                    'success': False,
                    'error': 'SMS notifications not yet implemented'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown channel: {channel}'
                }
        
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid channel: {channel}'
            }
        except Exception as e:
            logger.error(f"Notification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def create_notification_service(
    mailtrap_token: Optional[str] = None,
    slack_webhook_url: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> NotificationService:
    """Factory function to create NotificationService instance"""
    return NotificationService(
        mailtrap_token=mailtrap_token,
        slack_webhook_url=slack_webhook_url,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password
    )
