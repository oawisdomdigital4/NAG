"""
Email Integration Examples for User Registration and Password Reset

This file shows how to integrate Mailjet email sending into your authentication flows.
Copy and adapt the examples to your accounts/views.py file.
"""

# ============================================================================
# EXAMPLE 1: Send Welcome Email on User Registration
# ============================================================================
# Add this to your accounts/views.py in the user registration view:

from accounts.email_tasks import send_welcome_email
from django.urls import reverse

def register_user(request):
    """Example user registration view with email"""
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate activation URL
            activation_url = request.build_absolute_uri(
                reverse('verify-email', kwargs={'user_id': user.id})
            )
            
            # Send welcome email (can be async with Celery or sync)
            # Async (recommended):
            send_welcome_email.delay(user.id, activation_url)
            
            # Or sync (simpler but blocks request):
            # from accounts.email_tasks import send_welcome_email
            # send_welcome_email(user.id, activation_url)
            
            return Response({
                'message': 'User registered. Check email for verification link.',
                'user_id': user.id
            }, status=201)
        
        return Response(serializer.errors, status=400)


# ============================================================================
# EXAMPLE 2: Send Password Reset Email
# ============================================================================
# Add this to your accounts/views.py in the password reset view:

from accounts.email_tasks import send_password_reset_email
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status

def request_password_reset(request):
    """Request password reset - send reset email"""
    email = request.data.get('email')
    
    try:
        user = User.objects.get(email=email)
        
        # Generate reset token (use Django's password reset token generator)
        from django.contrib.auth.tokens import default_token_generator
        token = default_token_generator.make_token(user)
        
        # Build reset URL with token
        reset_url = request.build_absolute_uri(
            f'/reset-password?uid={user.id}&token={token}'
        )
        
        # Send password reset email (async recommended)
        send_password_reset_email.delay(user.id, reset_url)
        
        return Response({
            'message': 'Password reset link sent to your email'
        }, status=200)
        
    except User.DoesNotExist:
        # Don't reveal if email exists (security best practice)
        return Response({
            'message': 'If this email exists, you will receive reset instructions'
        }, status=200)


# ============================================================================
# EXAMPLE 3: Direct Email Sending (without Celery)
# ============================================================================
# If you don't have Celery set up, use the mailjet_service directly:

from utils.mailjet_service import send_email
from utils.email_templates import welcome_email_template

def register_user_sync(request):
    """Synchronous registration with email (simpler but slower)"""
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Build activation URL
            activation_url = request.build_absolute_uri(
                reverse('verify-email', kwargs={'user_id': user.id})
            )
            
            # Send email directly (synchronous)
            html = welcome_email_template(user.get_full_name() or user.username, activation_url)
            success = send_email(
                to_email=user.email,
                to_name=user.get_full_name() or user.username,
                subject='Welcome to The New Africa Group!',
                html_content=html
            )
            
            if success:
                return Response({
                    'message': 'User registered. Check email for verification.',
                    'user_id': user.id
                }, status=201)
            else:
                # Email failed but user was created
                return Response({
                    'message': 'User created but email failed to send',
                    'user_id': user.id,
                    'email_error': True
                }, status=201)
        
        return Response(serializer.errors, status=400)


# ============================================================================
# EXAMPLE 4: Custom Notification Email
# ============================================================================
# Send custom notification emails to users:

from accounts.email_tasks import send_notification_email
from utils.email_templates import notification_email_template

def notify_user_event(request, user_id):
    """Send notification to user"""
    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)
    
    # Create notification content
    html = notification_email_template(
        user_name=user.get_full_name() or user.username,
        title='New Event in Your Community!',
        message='An event you subscribed to has been updated.',
        action_url='https://thenewafricagroup.com/events'
    )
    
    # Send notification (async)
    send_notification_email.delay(
        user_id=user.id,
        subject='Community Event Update',
        html_content=html
    )
    
    return Response({'status': 'notification sent'})


# ============================================================================
# EXAMPLE 5: Batch Email to Multiple Users (Newsletter/Announcement)
# ============================================================================
# Send same email to multiple users:

from utils.mailjet_service import send_batch_emails
from django.contrib.auth.models import User

def send_newsletter(request):
    """Send newsletter to all subscribed users"""
    subscribers = User.objects.filter(is_active=True)
    
    recipients = [
        {
            'email': user.email,
            'name': user.get_full_name() or user.username,
            'variables': {
                'user_name': user.get_full_name() or user.username,
                'unsubscribe_url': f'https://thenewafricagroup.com/unsubscribe/{user.id}'
            }
        }
        for user in subscribers
    ]
    
    html_template = """
    <p>Hello {{user_name}},</p>
    <p>Check out our latest updates and articles.</p>
    <a href="{{unsubscribe_url}}">Unsubscribe</a>
    """
    
    success = send_batch_emails(
        recipients=recipients,
        subject='The New Africa Group Newsletter',
        html_content=html_template,
        use_template_variables=True
    )
    
    return Response({
        'status': 'newsletter sent' if success else 'newsletter failed',
        'recipient_count': len(recipients)
    })


# ============================================================================
# EXAMPLE 6: Integration with Django Signals (Auto-send on User Create)
# ============================================================================
# Add to accounts/signals.py to auto-send emails on user creation:

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.email_tasks import send_welcome_email

@receiver(post_save, sender=User)
def send_welcome_on_user_create(sender, instance, created, **kwargs):
    """Automatically send welcome email when user is created"""
    if created and instance.email:
        # Use delay() for async, or call directly for sync
        send_welcome_email.delay(
            user_id=instance.id,
            activation_url=None  # Will use default
        )

# Add to apps.py:
# from django.apps import AppConfig
# class AccountsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'accounts'
#     
#     def ready(self):
#         import accounts.signals  # Import signals when app is ready


# ============================================================================
# EXAMPLE 7: Error Handling and Retry Logic
# ============================================================================

from accounts.email_tasks import send_welcome_email
from django.core.mail.backends.base import BaseEmailBackend
import logging

logger = logging.getLogger(__name__)

def register_with_retry(request):
    """Registration with email retry logic"""
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            activation_url = request.build_absolute_uri(
                reverse('verify-email', kwargs={'user_id': user.id})
            )
            
            # Send email with retry on failure
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    send_welcome_email.apply_async(
                        args=[user.id, activation_url],
                        countdown=attempt * 60,  # Retry after delay
                        max_retries=max_retries
                    )
                    break
                except Exception as e:
                    logger.error(f'Email attempt {attempt + 1} failed: {str(e)}')
                    if attempt == max_retries - 1:
                        logger.error(f'All email attempts failed for user {user.id}')
            
            return Response({
                'message': 'User registered',
                'user_id': user.id
            }, status=201)
        
        return Response(serializer.errors, status=400)


# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
"""
1. Install Celery (optional but recommended for async emails):
   pip install celery redis

2. Add to myproject/settings.py:
   CELERY_BROKER_URL = 'redis://localhost:6379'
   CELERY_RESULT_BACKEND = 'redis://localhost:6379'

3. Create myproject/celery.py (for async task processing)

4. Set environment variables:
   export MAILJET_API_KEY='your-api-key'
   export MAILJET_SECRET_KEY='your-secret-key'

5. In your views, use:
   send_welcome_email.delay(user.id, activation_url)  # Async
   send_welcome_email(user.id, activation_url)  # Sync

6. Test by running:
   python manage.py shell
   >>> from accounts.email_tasks import send_welcome_email
   >>> user = User.objects.first()
   >>> send_welcome_email(user.id, 'http://example.com/verify/1')
"""
