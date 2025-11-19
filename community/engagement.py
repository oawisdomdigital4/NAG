"""
Engagement System for Community Posts and Comments

Tracks all engagement actions (likes, comments, mentions) and logs them for analytics.
Integrates with notification system for real-time user feedback.
"""

from django.db import models
from django.db.models import F, Q, Count, Sum
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import json
from datetime import timedelta


class CommunityEngagementLog(models.Model):
    """
    Comprehensive engagement logging for analytics and insights.
    
    Tracks all user interactions: likes, comments, mentions, group joins.
    Used by facilitator analytics, corporate campaign insights, and reputation system.
    """
    
    ACTION_TYPES = (
        ('click_action', 'Clicked Action'),
        ('like_post', 'Liked a Post'),
        ('unlike_post', 'Unliked a Post'),
        ('like_comment', 'Liked a Comment'),
        ('unlike_comment', 'Unliked a Comment'),
        ('comment_post', 'Commented on Post'),
        ('reply_comment', 'Replied to Comment'),
        ('mention_user', 'Mentioned a User'),
        ('join_group', 'Joined Group'),
        ('leave_group', 'Left Group'),
        ('view_post', 'Viewed Post'),
        ('share_post', 'Shared Post'),
        ('bookmark_post', 'Bookmarked Post'),
        ('unbookmark_post', 'Unbookmarked Post'),
    )
    
    # Who did the action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='community_engagement_logs'
    )
    
    # What action was taken
    action_type = models.CharField(max_length=32, choices=ACTION_TYPES)
    
    # What was engaged with
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='community_engagement_logs'
    )
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='community_engagement_logs'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='community_engagement_logs'
    )
    
    # Mentioned users (for mention tracking)
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentions_received'
    )
    
    # Metadata for context
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['post', 'action_type']),
            models.Index(fields=['mentioned_user', '-created_at']),
            models.Index(fields=['user', 'action_type', '-created_at']),
        ]
        verbose_name_plural = 'Community Engagement Logs'
    
    def __str__(self):
        return f"{self.user_id} - {self.action_type} ({self.created_at})"
    
    @classmethod
    def log_engagement(cls, user, action_type, post=None, comment=None, group=None, 
                       mentioned_user=None, metadata=None):
        """
        Log an engagement action.
        
        Args:
            user: User performing the action
            action_type: Type of engagement action
            post: Post being engaged with (if applicable)
            comment: Comment being engaged with (if applicable)
            group: Group being engaged with (if applicable)
            mentioned_user: User being mentioned (if applicable)
            metadata: Additional context data
        
        Returns:
            CommunityEngagementLog instance
        """
        if metadata is None:
            metadata = {}
        
        log = cls.objects.create(
            user=user,
            action_type=action_type,
            post=post,
            comment=comment,
            group=group,
            mentioned_user=mentioned_user,
            metadata=metadata
        )
        
        # Clear related caches
        if post:
            cache.delete(f'post_engagement:{post.id}')
        if comment:
            cache.delete(f'comment_engagement:{comment.id}')
        if user:
            cache.delete(f'user_activity:{user.id}')
        
        return log
    
    @classmethod
    def get_user_engagement_metrics(cls, user, days=30):
        """
        Get engagement metrics for a user over the past N days.
        
        Used for reputation system, activity tracking, and badge eligibility.
        """
        start_date = timezone.now() - timedelta(days=days)
        
        logs = cls.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        metrics = {
            'total_actions': logs.count(),
            'likes': logs.filter(action_type__in=['like_post', 'like_comment']).count(),
            'comments': logs.filter(action_type__in=['comment_post', 'reply_comment']).count(),
            'mentions': logs.filter(action_type='mention_user').count(),
            'group_joins': logs.filter(action_type='join_group').count(),
            'views': logs.filter(action_type='view_post').count(),
            'shares': logs.filter(action_type='share_post').count(),
            'clicks': logs.filter(action_type='click_action').count(),
            'bookmarks': logs.filter(action_type__in=['bookmark_post']).count(),
        }
        
        return metrics
    
    @classmethod
    def get_post_engagement_metrics(cls, post):
        """
        Get engagement metrics for a specific post.
        
        Used by facilitators and corporate users to analyze content performance.
        """
        cache_key = f'post_engagement:{post.id}'
        cached = cache.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        logs = cls.objects.filter(post=post)
        
        metrics = {
            'total_engagement': logs.count(),
            'likes': logs.filter(action_type='like_post').count(),
            'comments': logs.filter(action_type__in=['comment_post', 'reply_comment']).count(),
            'mentions': logs.filter(action_type='mention_user').count(),
            'views': logs.filter(action_type='view_post').count(),
            'clicks': logs.filter(action_type='click_action').count(),
            'shares': logs.filter(action_type='share_post').count(),
            'bookmarks': logs.filter(action_type='bookmark_post').count(),
            'unique_engagers': logs.values('user').distinct().count(),
        }
        
        # Cache for 1 hour
        cache.set(cache_key, json.dumps(metrics), timeout=3600)
        
        return metrics
    
    @classmethod
    def get_trending_posts(cls, days=7, limit=10):
        """
        Get trending posts based on engagement in the past N days.
        
        Used for feed ranking and recommendations.
        """
        start_date = timezone.now() - timedelta(days=days)
        
        trending = (
            cls.objects.filter(
                created_at__gte=start_date,
                action_type__in=['like_post', 'comment_post', 'share_post']
            )
            .values('post__id', 'post__title')
            .annotate(
                engagement_count=Count('id'),
                unique_engagers=Count('user', distinct=True)
            )
            .order_by('-engagement_count')[:limit]
        )
        
        return trending
    
    @classmethod
    def get_active_users(cls, days=7, limit=20):
        """
        Get most active users in the past N days.
        
        Used for community recognition and reputation tracking.
        """
        start_date = timezone.now() - timedelta(days=days)
        
        active = (
            cls.objects.filter(created_at__gte=start_date)
            .values('user__id', 'user__profile__full_name')
            .annotate(
                action_count=Count('id'),
                post_count=Count('id', filter=Q(action_type__in=['comment_post', 'reply_comment'])),
                like_count=Count('id', filter=Q(action_type__in=['like_post', 'like_comment']))
            )
            .order_by('-action_count')[:limit]
        )
        
        return active


class MentionLog(models.Model):
    """
    Dedicated model for tracking mentions.
    
    Enables efficient querying for @mentions and notification triggering.
    """
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentions_in_posts'
    )
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mentions'
    )
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mentions'
    )
    mentioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mentions_made'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mentioned_user', '-created_at']),
            models.Index(fields=['post', 'mentioned_user']),
            models.Index(fields=['comment', 'mentioned_user']),
        ]
    
    def __str__(self):
        return f"{self.mentioned_by_id} mentioned {self.mentioned_user_id}"
    
    @classmethod
    def extract_mentions(cls, text):
        """
        Extract @mentions from text.
        
        Returns list of usernames mentioned.
        """
        import re
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, text)
        return matches
    
    @classmethod
    def create_from_text(cls, text, post=None, comment=None, mentioned_by=None):
        """
        Create MentionLog entries from text with @mentions.
        """
        from accounts.models import User
        
        mentions = cls.extract_mentions(text)
        created_logs = []
        
        for username in mentions:
            try:
                user = User.objects.get(username=username)
                log = cls.objects.create(
                    mentioned_user=user,
                    post=post,
                    comment=comment,
                    mentioned_by=mentioned_by
                )
                created_logs.append(log)
            except User.DoesNotExist:
                # Skip non-existent users
                continue
        
        return created_logs


class UserReputation(models.Model):
    """
    User reputation system based on engagement.
    
    Tracks activity rank, badges, and engagement metrics for individual users.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reputation'
    )
    
    # Reputation score (can earn badges at certain thresholds)
    reputation_score = models.IntegerField(default=0)
    
    # Activity level (based on engagement frequency)
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('inactive', 'Inactive'),
            ('novice', 'Novice'),
            ('active', 'Active'),
            ('power_user', 'Power User'),
            ('community_leader', 'Community Leader'),
        ],
        default='novice'
    )
    
    # Badges earned (JSON array of badge identifiers)
    badges = models.JSONField(default=list, blank=True)
    
    # Metrics (updated periodically)
    total_posts = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_likes_received = models.IntegerField(default=0)
    total_engagement_actions = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'User Reputations'
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_level} (Score: {self.reputation_score})"
    
    def update_reputation(self):
        """
        Recalculate reputation score and activity level.
        """
        from django.db.models import Count, Q
        
        # Get engagement metrics from last 30 days
        logs = CommunityEngagementLog.objects.filter(
            user=self.user,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Calculate score components
        like_score = logs.filter(action_type__in=['like_post', 'like_comment']).count() * 1
        comment_score = logs.filter(action_type__in=['comment_post', 'reply_comment']).count() * 5
        mention_score = logs.filter(action_type='mention_user').count() * 10
        group_score = logs.filter(action_type='join_group').count() * 3
        share_score = logs.filter(action_type='share_post').count() * 7
        
        self.reputation_score = like_score + comment_score + mention_score + group_score + share_score
        
        # Determine activity level based on action count
        action_count = logs.count()
        if action_count == 0:
            self.activity_level = 'inactive'
        elif action_count < 10:
            self.activity_level = 'novice'
        elif action_count < 50:
            self.activity_level = 'active'
        elif action_count < 200:
            self.activity_level = 'power_user'
        else:
            self.activity_level = 'community_leader'
        
        # Award badges based on achievements
        self.badges = self._calculate_badges()
        
        self.save(update_fields=['reputation_score', 'activity_level', 'badges', 'updated_at'])
        
        # Clear cache
        cache.delete(f'user_reputation:{self.user.id}')
    
    def _calculate_badges(self):
        """
        Calculate earned badges based on user achievements.
        """
        badges = []
        
        # Check various achievement conditions
        if self.reputation_score >= 100:
            badges.append('rising_star')
        if self.reputation_score >= 500:
            badges.append('influencer')
        if self.reputation_score >= 1000:
            badges.append('community_legend')
        
        if self.total_comments >= 50:
            badges.append('conversationalist')
        if self.total_comments >= 200:
            badges.append('debate_master')
        
        if self.total_likes_received >= 100:
            badges.append('well_liked')
        if self.total_likes_received >= 500:
            badges.append('beloved')
        
        if self.activity_level == 'power_user':
            badges.append('power_user')
        if self.activity_level == 'community_leader':
            badges.append('leader')
        
        return list(set(badges))  # Remove duplicates


class EngagementNotification(models.Model):
    """
    Tracks engagement notifications sent to users.
    
    Records when users are notified about likes, comments, mentions, etc.
    For email digest and notification preference management.
    """
    
    NOTIFICATION_TYPES = (
        ('post_liked', 'Your post was liked'),
        ('post_commented', 'Someone commented on your post'),
        ('comment_liked', 'Your comment was liked'),
        ('comment_replied', 'Someone replied to your comment'),
        ('post_mentioned', 'You were mentioned in a post'),
        ('comment_mentioned', 'You were mentioned in a comment'),
        ('group_update', 'New activity in your group'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_notifications'
    )
    
    notification_type = models.CharField(max_length=32, choices=NOTIFICATION_TYPES)
    
    # Link to the engagement action
    engagement_log = models.ForeignKey(
        CommunityEngagementLog,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # The user who triggered the notification
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='engagement_notifications_sent'
    )
    
    # Notification status
    in_app_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.notification_type}"
    
    @classmethod
    def create_and_notify(cls, notification_type, user, triggered_by, engagement_log):
        """
        Create a notification and send it via configured channels.
        """
        notification = cls.objects.create(
            user=user,
            notification_type=notification_type,
            engagement_log=engagement_log,
            triggered_by=triggered_by
        )
        
        # Send notifications asynchronously
        from .notification_service import NotificationService
        NotificationService.send_engagement_notification(notification)
        
        return notification
