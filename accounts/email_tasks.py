"""
Email notification tasks for user events
Integrates Mailjet email service with user actions
"""

# Try to import celery, but make it optional
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Fallback decorator if celery not installed
    def shared_task(func):
        return func

from django.contrib.auth.models import User
from utils.mailjet_service import send_email
from utils.email_templates import welcome_email_template, password_reset_email_template, otp_email_template
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email(user_id: int, activation_url: str = None):
    """
    Send welcome email to newly registered user
    
    Args:
        user_id: ID of the user
        activation_url: URL for email verification (optional)
    """
    try:
        user = User.objects.get(id=user_id)
        
        user_name = user.get_full_name() or user.username
        activation_url = activation_url or f"https://thenewafricagroup.com/verify/{user.id}"
        
        html = welcome_email_template(user_name, activation_url)
        
        success = send_email(
            to_email=user.email,
            to_name=user_name,
            subject='Welcome to The New Africa Group!',
            html_content=html,
            text_content=f'Welcome {user_name}! Activate your account at: {activation_url}'
        )
        
        if success:
            logger.info(f'Welcome email sent to {user.email}')
        else:
            logger.error(f'Failed to send welcome email to {user.email}')
            
    except User.DoesNotExist:
        logger.error(f'User with id {user_id} not found')
    except Exception as e:
        logger.error(f'Error sending welcome email: {str(e)}')


@shared_task
def send_password_reset_email(user_id: int, reset_url: str):
    """
    Send password reset email to user
    
    Args:
        user_id: ID of the user
        reset_url: URL for password reset
    """
    try:
        user = User.objects.get(id=user_id)
        
        user_name = user.get_full_name() or user.username
        
        html = password_reset_email_template(user_name, reset_url)
        
        success = send_email(
            to_email=user.email,
            to_name=user_name,
            subject='Reset Your Password - The New Africa Group',
            html_content=html,
            text_content=f'Reset your password at: {reset_url}'
        )
        
        if success:
            logger.info(f'Password reset email sent to {user.email}')
        else:
            logger.error(f'Failed to send password reset email to {user.email}')
            
    except User.DoesNotExist:
        logger.error(f'User with id {user_id} not found')
    except Exception as e:
        logger.error(f'Error sending password reset email: {str(e)}')


@shared_task
def send_notification_email(user_id: int, subject: str, html_content: str, text_content: str = None):
    """
    Send generic notification email to user
    
    Args:
        user_id: ID of the user
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
    """
    try:
        user = User.objects.get(id=user_id)
        
        user_name = user.get_full_name() or user.username
        
        success = send_email(
            to_email=user.email,
            to_name=user_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content or subject
        )
        
        if success:
            logger.info(f'Notification email sent to {user.email}')
        else:
            logger.error(f'Failed to send notification email to {user.email}')
            
    except User.DoesNotExist:
        logger.error(f'User with id {user_id} not found')
    except Exception as e:
        logger.error(f'Error sending notification email: {str(e)}')


@shared_task
def send_otp_email(otp_id: int):
    """
    Send OTP verification email
    
    Args:
        otp_id: ID of the OTPVerification object
    """
    try:
        from accounts.models import OTPVerification
        
        otp = OTPVerification.objects.get(id=otp_id)
        user_name = otp.user.get_full_name() if otp.user else 'User'
        
        # If no user_name available, use a generic one
        if not user_name or user_name.strip() == '':
            user_name = 'User'
        
        html = otp_email_template(user_name, otp.otp_code, expires_in_minutes=10)
        
        success = send_email(
            to_email=otp.email,
            to_name=user_name,
            subject='Your OTP Verification Code - The New Africa Group',
            html_content=html,
            text_content=f'Your OTP code is: {otp.otp_code}. Valid for 10 minutes.'
        )
        
        if success:
            logger.info(f'OTP email sent to {otp.email}')
        else:
            logger.error(f'Failed to send OTP email to {otp.email}')
            
    except Exception as e:
        logger.error(f'Error sending OTP email: {str(e)}')
