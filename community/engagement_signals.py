"""
Signal handlers for engagement logging.

Automatically logs engagement actions when:
- PostReaction objects are created/deleted
- Comment objects are created
- CommentReaction objects are created/deleted
- Users are mentioned
- Group memberships are created/deleted
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .engagement import CommunityEngagementLog, MentionLog, UserReputation, EngagementNotification
from .notification_service import NotificationService


@receiver(post_save, sender='community.PostReaction')
def log_post_like(sender, instance, created, **kwargs):
    """
    Log when a user likes a post.
    """
    if created:
        # Log the like action
        CommunityEngagementLog.log_engagement(
            user=instance.user,
            action_type='like_post',
            post=instance.post,
            metadata={
                'reaction_type': instance.reaction_type,
            }
        )
        
        # Update post's ranking
        instance.post.update_ranking()
        
        # Send notification to post author
        if instance.post.author and instance.post.author != instance.user:
            engagement_log = CommunityEngagementLog.objects.filter(
                user=instance.user,
                action_type='like_post',
                post=instance.post
            ).latest('created_at')
            
            EngagementNotification.create_and_notify(
                notification_type='post_liked',
                user=instance.post.author,
                triggered_by=instance.user,
                engagement_log=engagement_log
            )


@receiver(post_delete, sender='community.PostReaction')
def log_post_unlike(sender, instance, **kwargs):
    """
    Log when a user unlikes a post.
    """
    CommunityEngagementLog.log_engagement(
        user=instance.user,
        action_type='unlike_post',
        post=instance.post,
    )
    
    # Update post's ranking
    instance.post.update_ranking()


@receiver(post_save, sender='community.Comment')
def log_comment_post(sender, instance, created, **kwargs):
    """
    Log when a user comments on a post.
    
    Also handles mention extraction and creates mentions.
    """
    if created:
        # Log the comment action
        if instance.parent_comment:
            action_type = 'reply_comment'
        else:
            action_type = 'comment_post'
        
        engagement_log = CommunityEngagementLog.log_engagement(
            user=instance.author,
            action_type=action_type,
            post=instance.post,
            comment=instance,
            metadata={
                'content_preview': instance.content[:100],
            }
        )
        
        # Update post's ranking
        instance.post.update_ranking()
        
        # Extract and log mentions
        mentions = MentionLog.create_from_text(
            instance.content,
            comment=instance,
            mentioned_by=instance.author
        )
        
        # Send notifications for mentions
        for mention in mentions:
            CommunityEngagementLog.log_engagement(
                user=instance.author,
                action_type='mention_user',
                comment=instance,
                mentioned_user=mention.mentioned_user,
            )
            
            # Notify mentioned user
            EngagementNotification.create_and_notify(
                notification_type='comment_mentioned',
                user=mention.mentioned_user,
                triggered_by=instance.author,
                engagement_log=engagement_log
            )
        
        # Notify post author (if not replying to their own comment)
        if instance.post.author and instance.post.author != instance.author:
            EngagementNotification.create_and_notify(
                notification_type='post_commented',
                user=instance.post.author,
                triggered_by=instance.author,
                engagement_log=engagement_log
            )
        
        # Notify parent comment author if this is a reply
        if instance.parent_comment and instance.parent_comment.author != instance.author:
            EngagementNotification.create_and_notify(
                notification_type='comment_replied',
                user=instance.parent_comment.author,
                triggered_by=instance.author,
                engagement_log=engagement_log
            )


@receiver(post_save, sender='community.CommentReaction')
def log_comment_like(sender, instance, created, **kwargs):
    """
    Log when a user likes a comment.
    """
    if created:
        # Log the like action
        CommunityEngagementLog.log_engagement(
            user=instance.user,
            action_type='like_comment',
            comment=instance.comment,
            metadata={
                'post_id': instance.comment.post.id,
            }
        )
        
        # Update post's ranking (comment engagement affects post ranking)
        instance.comment.post.update_ranking()
        
        # Send notification to comment author
        if instance.comment.author and instance.comment.author != instance.user:
            engagement_log = CommunityEngagementLog.objects.filter(
                user=instance.user,
                action_type='like_comment',
                comment=instance.comment
            ).latest('created_at')
            
            EngagementNotification.create_and_notify(
                notification_type='comment_liked',
                user=instance.comment.author,
                triggered_by=instance.user,
                engagement_log=engagement_log
            )


@receiver(post_delete, sender='community.CommentReaction')
def log_comment_unlike(sender, instance, **kwargs):
    """
    Log when a user unlikes a comment.
    """
    CommunityEngagementLog.log_engagement(
        user=instance.user,
        action_type='unlike_comment',
        comment=instance.comment,
    )
    
    # Update post's ranking
    instance.comment.post.update_ranking()


@receiver(post_save, sender='community.GroupMembership')
def log_group_join(sender, instance, created, **kwargs):
    """
    Log when a user joins a group.
    """
    if created:
        CommunityEngagementLog.log_engagement(
            user=instance.user,
            action_type='join_group',
            group=instance.group,
            metadata={
                'group_name': instance.group.name,
            }
        )


@receiver(post_delete, sender='community.GroupMembership')
def log_group_leave(sender, instance, **kwargs):
    """
    Log when a user leaves a group.
    """
    CommunityEngagementLog.log_engagement(
        user=instance.user,
        action_type='leave_group',
        group=instance.group,
        metadata={
            'group_name': instance.group.name,
        }
    )


@receiver(post_save, sender='accounts.User')
def create_user_reputation(sender, instance, created, **kwargs):
    """
    Create UserReputation when a new user is created.
    """
    if created:
        UserReputation.objects.get_or_create(user=instance)


@receiver(post_save, sender='community.CommunityEngagementLog')
def update_user_reputation(sender, instance, created, **kwargs):
    """
    Update user reputation when engagement happens.
    
    Runs periodically (could be async with Celery for performance).
    """
    if created and instance.user:
        try:
            reputation = UserReputation.objects.get(user=instance.user)
            
            # Update reputation every 10 engagements to avoid excessive updates
            if instance.user.engagement_logs.count() % 10 == 0:
                reputation.update_reputation()
        except UserReputation.DoesNotExist:
            # Create if doesn't exist
            UserReputation.objects.create(user=instance.user)


def connect_engagement_signals():
    """
    Connect all engagement signals.
    
    Call this in apps.py AppConfig.ready() method.
    """
    pass  # Signals are auto-connected since they're in this module
