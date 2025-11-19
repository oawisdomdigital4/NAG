"""
Engagement Notification Service

Handles sending notifications for engagement actions (likes, comments, mentions)
via in-app and email channels with role-based templates.

Notifications are sent asynchronously using threading to avoid blocking requests.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Count
from notifications.models import Notification, NotificationPreference
from datetime import timedelta
import threading


class NotificationService:
    """
    Service for sending engagement notifications.
    
    Respects user notification preferences and sends via configured channels.
    """
    
    # Template mapping for different notification types
    EMAIL_TEMPLATES = {
        'post_liked': 'engagement/post_liked.html',
        'post_commented': 'engagement/post_commented.html',
        'comment_liked': 'engagement/comment_liked.html',
        'comment_replied': 'engagement/comment_replied.html',
        'post_mentioned': 'engagement/post_mentioned.html',
        'comment_mentioned': 'engagement/comment_mentioned.html',
        'group_update': 'engagement/group_update.html',
    }
    
    NOTIFICATION_TITLES = {
        'post_liked': '❤️ Your post received a like',
        'post_commented': '💬 New comment on your post',
        'comment_liked': '❤️ Your comment received a like',
        'comment_replied': '💬 New reply to your comment',
        'post_mentioned': '@️ You were mentioned in a post',
        'comment_mentioned': '@ You were mentioned in a comment',
        'group_update': '👥 New activity in your group',
    }
    
    @classmethod
    def send_engagement_notification(cls, engagement_notification):
        """
        Send engagement notification via configured channels asynchronously.
        
        Uses threading to send notifications in the background without blocking the request.
        Respects user's notification preferences.
        """
        # Start notification sending in a background thread
        thread = threading.Thread(
            target=cls._send_notifications_async,
            args=(engagement_notification,),
            daemon=True
        )
        thread.start()
    
    @classmethod
    def _send_notifications_async(cls, engagement_notification):
        """
        Internal method that sends notifications in a background thread.
        """
        try:
            user = engagement_notification.user
            
            # Check notification preferences
            try:
                pref = NotificationPreference.objects.get(
                    user=user,
                    notification_type='community'
                )
            except NotificationPreference.DoesNotExist:
                # Default to sending if no preference set
                pref = NotificationPreference(
                    user=user,
                    notification_type='community',
                    in_app_enabled=True,
                    email_enabled=True
                )
            
            # Send in-app notification
            if pref.in_app_enabled:
                cls._send_in_app_notification(engagement_notification)
            
            # Send email notification
            if pref.email_enabled:
                cls._send_email_notification(engagement_notification)
        except Exception as e:
            print(f"Error in async notification thread: {e}")
    
    @classmethod
    def _send_in_app_notification(cls, engagement_notification):
        """
        Create in-app notification in the Notification model.
        """
        try:
            title = cls.NOTIFICATION_TITLES.get(
                engagement_notification.notification_type,
                'New engagement activity'
            )
            
            # Build context based on notification type and role
            context = cls._build_notification_context(engagement_notification)
            
            notification = Notification.objects.create(
                user=engagement_notification.user,
                type=engagement_notification.notification_type,
                category='community',
                title=title,
                message=context['message'],
                action_url=context.get('action_url', ''),
                metadata={
                    'engagement_notification_id': engagement_notification.id,
                    'triggered_by_user_id': engagement_notification.triggered_by_id,
                    'post_id': engagement_notification.engagement_log.post_id,
                    'comment_id': engagement_notification.engagement_log.comment_id,
                }
            )
            
            engagement_notification.in_app_sent = True
            engagement_notification.save(update_fields=['in_app_sent'])
            
            return notification
        except Exception as e:
            print(f"Error creating in-app notification: {e}")
            return None
    
    @classmethod
    def _send_email_notification(cls, engagement_notification):
        """
        Send email notification with role-based template.
        """
        try:
            user = engagement_notification.user
            triggered_by = engagement_notification.triggered_by
            
            # Skip if user hasn't set up email or opted out
            if not user.email:
                return False
            
            # Get template based on user role and notification type
            template = cls._get_email_template(
                engagement_notification.notification_type,
                user.role if hasattr(user, 'role') else 'individual'
            )
            
            # Build email context
            context = cls._build_email_context(engagement_notification)
            
            # Render email template
            html_message = render_to_string(template, context)
            
            # Send email
            send_mail(
                subject=cls.NOTIFICATION_TITLES.get(
                    engagement_notification.notification_type,
                    'New community engagement'
                ),
                message='',  # Plain text version (use HTML only)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True
            )
            
            engagement_notification.email_sent = True
            engagement_notification.save(update_fields=['email_sent'])
            
            return True
        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False
    
    @classmethod
    def _get_email_template(cls, notification_type, user_role):
        """
        Get appropriate email template based on notification type and user role.
        
        Examples:
        - Corporate users get templates emphasizing campaign engagement
        - Facilitators get course popularity emphasis
        - Individual users get standard engagement templates
        """
        base_template = cls.EMAIL_TEMPLATES.get(notification_type, 'engagement/default.html')
        
        # For now, use base templates
        # In future, could have role-specific versions:
        # - engagement_corporate/post_commented.html
        # - engagement_facilitator/post_commented.html
        
        return f'notifications/{base_template}'
    
    @classmethod
    def _build_notification_context(cls, engagement_notification):
        """
        Build context for in-app notification message.
        """
        eng_log = engagement_notification.engagement_log
        triggered_by = engagement_notification.triggered_by
        
        # Handle case where triggered_by might be None
        if triggered_by is None:
            username = "Someone"
        else:
            username = triggered_by.profile.full_name if hasattr(triggered_by, 'profile') else triggered_by.username
        
        contexts = {
            'post_liked': {
                'message': f'{username} liked your post',
                'action_url': f'/community/post/{eng_log.post.id}' if eng_log.post and eng_log.post.id else '',
            },
            'post_commented': {
                'message': f'{username} commented on your post',
                'action_url': f'/community/post/{eng_log.post.id}' if eng_log.post and eng_log.post.id else '',
            },
            'comment_liked': {
                'message': f'{username} liked your comment',
                'action_url': f'/community/post/{eng_log.comment.post.id}' if eng_log.comment and eng_log.comment.post and eng_log.comment.post.id else '',
            },
            'comment_replied': {
                'message': f'{username} replied to your comment',
                'action_url': f'/community/post/{eng_log.comment.post.id}' if eng_log.comment and eng_log.comment.post and eng_log.comment.post.id else '',
            },
            'post_mentioned': {
                'message': f'{username} mentioned you in a post',
                'action_url': f'/community/post/{eng_log.post.id}' if eng_log.post and eng_log.post.id else '',
            },
            'comment_mentioned': {
                'message': f'{username} mentioned you in a comment',
                'action_url': f'/community/post/{eng_log.comment.post.id}' if eng_log.comment and eng_log.comment.post and eng_log.comment.post.id else '',
            },
            'group_update': {
                'message': f'New activity in {eng_log.group.name}' if eng_log.group and eng_log.group.name else 'New group activity',
                'action_url': f'/community/group/{eng_log.group.id}' if eng_log.group and eng_log.group.id else '',
            },
        }
        
        return contexts.get(engagement_notification.notification_type, {
            'message': 'New community activity',
            'action_url': '/community',
        })
    
    @classmethod
    def _build_email_context(cls, engagement_notification):
        """
        Build context for email template rendering.
        
        Includes user info, engagement details, and action URLs.
        """
        eng_log = engagement_notification.engagement_log
        triggered_by = engagement_notification.triggered_by
        user = engagement_notification.user
        
        # Handle case where triggered_by might be None
        if triggered_by is None:
            triggered_by_name = "Someone"
            triggered_by_avatar = ''
        else:
            triggered_by_name = triggered_by.profile.full_name if hasattr(triggered_by, 'profile') else triggered_by.username
            triggered_by_avatar = triggered_by.profile.avatar_url if hasattr(triggered_by, 'profile') else ''
        
        # Build base context
        context = {
            'recipient_name': user.profile.full_name if hasattr(user, 'profile') else user.username,
            'recipient_email': user.email,
            'triggered_by_name': triggered_by_name,
            'triggered_by_avatar': triggered_by_avatar,
            'action_type': engagement_notification.notification_type,
            'created_at': eng_log.created_at,
            'app_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://nag.edu.ng',
        }
        
        # Add content-specific context
        if eng_log.post:
            context.update({
                'post_title': (eng_log.post.title or eng_log.post.content[:100]) if eng_log.post else '',
                'post_url': f"{context['app_url']}/community/post/{eng_log.post.id}" if eng_log.post and eng_log.post.id else '',
                'post_author': eng_log.post.author.profile.full_name if eng_log.post and eng_log.post.author and hasattr(eng_log.post.author, 'profile') else (eng_log.post.author.username if eng_log.post and eng_log.post.author else ''),
            })
        
        if eng_log.comment:
            context.update({
                'comment_preview': eng_log.comment.content[:200] if eng_log.comment and eng_log.comment.content else '',
                'post_url': f"{context['app_url']}/community/post/{eng_log.comment.post.id}" if eng_log.comment and eng_log.comment.post and eng_log.comment.post.id else '',
            })
        
        if eng_log.group:
            context.update({
                'group_name': eng_log.group.name if eng_log.group and eng_log.group.name else '',
                'group_url': f"{context['app_url']}/community/group/{eng_log.group.id}" if eng_log.group and eng_log.group.id else '',
            })
        
        # Add role-specific context
        user_role = user.role if hasattr(user, 'role') else 'individual'
        if user_role == 'facilitator':
            context['role_specific_message'] = 'This engagement is helping your course gain popularity!'
        elif user_role == 'corporate':
            context['role_specific_message'] = 'Track campaign performance with detailed engagement analytics.'
        else:
            context['role_specific_message'] = 'Build your community reputation through engagement!'
        
        return context
    
    @classmethod
    def get_notification_summary(cls, user, hours=24):
        """
        Get a summary of notifications for a user in the past N hours.
        
        Used for digest emails and dashboard summaries.
        """
        from .engagement import EngagementNotification
        
        start_time = timezone.now() - timedelta(hours=hours)
        
        notifications = EngagementNotification.objects.filter(
            user=user,
            created_at__gte=start_time,
            in_app_sent=True
        ).values('notification_type').annotate(
            count=Count('id')
        )
        
        return {
            'total': sum(n['count'] for n in notifications),
            'by_type': {n['notification_type']: n['count'] for n in notifications},
            'period_hours': hours,
        }
    
    @classmethod
    def bulk_notify(cls, user_ids, notification_type, engagement_log, triggered_by=None):
        """
        Send the same notification to multiple users.
        
        Useful for group notifications or bulk engagement notifications.
        """
        from .engagement import EngagementNotification
        from accounts.models import User
        
        users = User.objects.filter(id__in=user_ids)
        notifications = []
        
        for user in users:
            notification = EngagementNotification.objects.create(
                user=user,
                notification_type=notification_type,
                engagement_log=engagement_log,
                triggered_by=triggered_by
            )
            notifications.append(notification)
            
            # Send asynchronously would be better with Celery
            cls.send_engagement_notification(notification)
        
        return notifications
