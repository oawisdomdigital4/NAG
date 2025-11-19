"""
Mailjet Email Service
Handles sending emails via Mailjet API
"""
import os
import requests
import json
from typing import List, Dict, Optional
from django.conf import settings
from django.core.mail import EmailMessage
import logging

logger = logging.getLogger(__name__)


class MailjetEmailService:
    """Service for sending emails via Mailjet API"""
    
    BASE_URL = 'https://api.mailjet.com/v3.1'
    
    def __init__(self):
        # Try environment variables first, then Django settings
        self.api_key = os.environ.get('MAILJET_API_KEY') or getattr(settings, 'MAILJET_API_KEY', '')
        self.secret_key = os.environ.get('MAILJET_SECRET_KEY') or getattr(settings, 'MAILJET_SECRET_KEY', '')
        self.from_email = os.environ.get('MAILJET_FROM_EMAIL') or getattr(settings, 'MAILJET_FROM_EMAIL', 'no-reply@thenewafricagroup.com')
        self.from_name = getattr(settings, 'MAILJET_FROM_NAME', 'The New Africa Group')
        
        if not self.api_key or not self.secret_key:
            logger.warning('Mailjet credentials not configured')
    
    def _get_auth(self):
        """Get basic auth tuple for Mailjet API"""
        return (self.api_key, self.secret_key)
    
    def send_email(
        self,
        to_email: str,
        to_name: Optional[str] = None,
        subject: str = '',
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        variables: Optional[Dict] = None,
    ) -> bool:
        """
        Send an email via Mailjet API
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name (optional)
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            reply_to: Reply-to email address
            variables: Custom variables for template
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if not self.api_key or not self.secret_key:
            logger.error('Mailjet credentials not configured')
            return False
        
        # Build recipients list
        recipients = [
            {
                'Email': to_email,
                'Name': to_name or to_email
            }
        ]
        
        # Add CC recipients
        if cc_emails:
            for cc_email in cc_emails:
                recipients.append({
                    'Email': cc_email,
                    'Name': cc_email
                })
        
        # Build the payload
        payload = {
            'Messages': [
                {
                    'From': {
                        'Email': self.from_email,
                        'Name': self.from_name
                    },
                    'To': recipients,
                    'Subject': subject,
                }
            ]
        }
        
        # Add email content
        if html_content:
            payload['Messages'][0]['HTMLPart'] = html_content
        if text_content:
            payload['Messages'][0]['TextPart'] = text_content
        
        # Add reply-to
        if reply_to:
            payload['Messages'][0]['ReplyTo'] = {
                'Email': reply_to
            }
        
        # Add custom variables if provided
        if variables:
            payload['Messages'][0]['Variables'] = variables
        
        # Add BCC recipients if provided
        if bcc_emails:
            payload['Messages'][0]['Bcc'] = [
                {'Email': bcc_email, 'Name': bcc_email}
                for bcc_email in bcc_emails
            ]
        
        try:
            response = requests.post(
                f'{self.BASE_URL}/send',
                json=payload,
                auth=self._get_auth(),
                timeout=10
            )
            
            if response.status_code in (200, 201):
                logger.info(f'Email sent successfully to {to_email}')
                return True
            else:
                logger.error(
                    f'Failed to send email to {to_email}. '
                    f'Status: {response.status_code}, '
                    f'Response: {response.text}'
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Error sending email to {to_email}: {str(e)}')
            return False
    
    def send_batch_emails(
        self,
        recipients: List[Dict],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send emails to multiple recipients in a single API call
        
        Args:
            recipients: List of dicts with 'email' and optional 'name' keys
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if not self.api_key or not self.secret_key:
            logger.error('Mailjet credentials not configured')
            return False
        
        if not recipients:
            logger.warning('No recipients provided for batch email')
            return False
        
        # Build recipients list
        to_list = [
            {
                'Email': recipient.get('email'),
                'Name': recipient.get('name', recipient.get('email'))
            }
            for recipient in recipients
        ]
        
        payload = {
            'Messages': [
                {
                    'From': {
                        'Email': self.from_email,
                        'Name': self.from_name
                    },
                    'To': to_list,
                    'Subject': subject,
                }
            ]
        }
        
        if html_content:
            payload['Messages'][0]['HTMLPart'] = html_content
        if text_content:
            payload['Messages'][0]['TextPart'] = text_content
        
        try:
            response = requests.post(
                f'{self.BASE_URL}/send',
                json=payload,
                auth=self._get_auth(),
                timeout=10
            )
            
            if response.status_code in (200, 201):
                logger.info(f'Batch email sent to {len(recipients)} recipients')
                return True
            else:
                logger.error(
                    f'Failed to send batch email. '
                    f'Status: {response.status_code}, '
                    f'Response: {response.text}'
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Error sending batch email: {str(e)}')
            return False


# Singleton instance
mailjet_service = MailjetEmailService()


def send_email(
    to_email: str,
    subject: str,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    to_name: Optional[str] = None,
    **kwargs
) -> bool:
    """
    Convenience function to send an email via Mailjet
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body
        to_name: Recipient name (optional)
        **kwargs: Additional arguments passed to mailjet_service.send_email()
        
    Returns:
        bool: True if successful, False otherwise
    """
    return mailjet_service.send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        to_name=to_name,
        **kwargs
    )


def send_batch_emails(
    recipients: List[Dict],
    subject: str,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
) -> bool:
    """
    Convenience function to send batch emails via Mailjet
    
    Args:
        recipients: List of dicts with 'email' and optional 'name' keys
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body
        
    Returns:
        bool: True if successful, False otherwise
    """
    return mailjet_service.send_batch_emails(
        recipients=recipients,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
