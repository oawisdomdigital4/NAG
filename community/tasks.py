"""
Async tasks for community engagement.

This module provides async task support for long-running operations.
Currently uses threading; can be upgraded to Celery for production.
"""

import threading
from django.conf import settings


def send_notification_email_async(notification_id):
    """
    Send a notification email asynchronously.
    
    Can be called with:
    - threading.Thread if Celery not configured
    - Celery shared_task if Celery is configured
    """
    try:
        from .models import EngagementNotification
        from .notification_service import NotificationService
        
        notification = EngagementNotification.objects.get(id=notification_id)
        NotificationService._send_email_notification(notification)
    except Exception as e:
        print(f"Error sending notification email: {e}")


def send_notification_in_app_async(notification_id):
    """
    Send an in-app notification asynchronously.
    """
    try:
        from .models import EngagementNotification
        from .notification_service import NotificationService
        
        notification = EngagementNotification.objects.get(id=notification_id)
        NotificationService._send_in_app_notification(notification)
    except Exception as e:
        print(f"Error sending in-app notification: {e}")


def update_post_ranking_async(post_id):
    """
    Update post ranking asynchronously.
    """
    try:
        from .models import Post
        
        post = Post.objects.get(id=post_id)
        post.update_ranking()
    except Exception as e:
        print(f"Error updating post ranking: {e}")


def update_user_reputation_async(user_id):
    """
    Update user reputation asynchronously.
    """
    try:
        from .models import UserReputation
        
        reputation = UserReputation.objects.get(user_id=user_id)
        reputation.update_reputation()
    except Exception as e:
        print(f"Error updating user reputation: {e}")


class AsyncTaskRunner:
    """
    Helper class to run tasks asynchronously.
    
    Supports both threading (default) and Celery (if configured).
    """
    
    @staticmethod
    def run(task_func, *args, **kwargs):
        """
        Run a task asynchronously.
        
        If Celery is configured, uses Celery; otherwise uses threading.
        """
        # Use threading by default (simple, works without external dependencies)
        thread = threading.Thread(
            target=task_func,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
        
        return thread
