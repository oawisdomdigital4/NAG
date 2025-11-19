from rest_framework import serializers
from django.contrib.auth.models import User
from .engagement import (
    CommunityEngagementLog,
    MentionLog,
    UserReputation,
    EngagementNotification,
)
from .models import Post, Comment


class UserSimpleSerializer(serializers.ModelSerializer):
    """Simplified user serializer for engagement data."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class PostSimpleSerializer(serializers.ModelSerializer):
    """Simplified post serializer for engagement context."""
    
    author = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at']
        read_only_fields = fields


class CommentSimpleSerializer(serializers.ModelSerializer):
    """Simplified comment serializer for engagement context."""
    
    author = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']
        read_only_fields = fields


class EngagementLogSerializer(serializers.ModelSerializer):
    """Serialize engagement log entries with related user and content info."""
    
    user = UserSimpleSerializer(read_only=True)
    post = PostSimpleSerializer(read_only=True)
    comment = CommentSimpleSerializer(read_only=True)
    mentioned_user = UserSimpleSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = CommunityEngagementLog
        fields = [
            'id',
            'user',
            'action_type',
            'action_display',
            'post',
            'comment',
            'mentioned_user',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class MentionLogSerializer(serializers.ModelSerializer):
    """Serialize mention logs with context about who was mentioned."""
    
    mentioned_user = UserSimpleSerializer(read_only=True)
    mentioned_by = UserSimpleSerializer(read_only=True)
    post = PostSimpleSerializer(read_only=True)
    comment = CommentSimpleSerializer(read_only=True)
    
    class Meta:
        model = MentionLog
        fields = [
            'id',
            'mentioned_user',
            'mentioned_by',
            'post',
            'comment',
            'created_at',
        ]
        read_only_fields = fields


class UserReputationSerializer(serializers.ModelSerializer):
    """Serialize user reputation with badges and activity level."""
    
    user = UserSimpleSerializer(read_only=True)
    activity_level_display = serializers.CharField(source='get_activity_level_display', read_only=True)
    badges_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserReputation
        fields = [
            'id',
            'user',
            'reputation_score',
            'activity_level',
            'activity_level_display',
            'badges',
            'badges_display',
            'total_posts',
            'total_comments',
            'total_likes_received',
            'total_engagement_actions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_badges_display(self, obj):
        """Convert badge list to readable format."""
        if not obj.badges:
            return []
        return [
            {'name': badge, 'awarded_at': obj.updated_at}
            for badge in obj.badges
        ]


class EngagementNotificationSerializer(serializers.ModelSerializer):
    """Serialize engagement notifications."""
    
    user = UserSimpleSerializer(read_only=True)
    triggered_by = UserSimpleSerializer(read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    
    class Meta:
        model = EngagementNotification
        fields = [
            'id',
            'user',
            'triggered_by',
            'notification_type',
            'notification_type_display',
            'email_sent',
            'in_app_sent',
            'read',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields


class EngagementMetricsSerializer(serializers.Serializer):
    """Serialize aggregated engagement metrics."""
    
    total_engagements = serializers.IntegerField(read_only=True)
    likes = serializers.IntegerField(read_only=True)
    comments = serializers.IntegerField(read_only=True)
    mentions = serializers.IntegerField(read_only=True)
    group_joins = serializers.IntegerField(read_only=True)
    comment_likes = serializers.IntegerField(read_only=True)
    comment_replies = serializers.IntegerField(read_only=True)
    period = serializers.CharField(read_only=True)
    average_per_day = serializers.FloatField(read_only=True)


class TrendingPostSerializer(serializers.Serializer):
    """Serialize trending posts with engagement metrics."""
    
    post_id = serializers.IntegerField(read_only=True)
    post_title = serializers.CharField(read_only=True)
    author = UserSimpleSerializer(read_only=True)
    total_engagements = serializers.IntegerField(read_only=True)
    likes = serializers.IntegerField(read_only=True)
    comments = serializers.IntegerField(read_only=True)
    engagement_score = serializers.FloatField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    period = serializers.CharField(read_only=True)


class ActiveUserSerializer(serializers.Serializer):
    """Serialize active users with engagement stats."""
    
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    total_engagements = serializers.IntegerField(read_only=True)
    reputation_score = serializers.IntegerField(read_only=True)
    activity_level = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)
    period = serializers.CharField(read_only=True)
    
    def get_avatar_url(self, obj):
        """Get user avatar URL if available."""
        request = self.context.get('request')
        if hasattr(obj.get('user'), 'profile') and hasattr(obj['user'].profile, 'avatar'):
            return obj['user'].profile.avatar.url if request else None
        return None


class NotificationSummarySerializer(serializers.Serializer):
    """Serialize notification summary for digest emails."""
    
    total_unread = serializers.IntegerField(read_only=True)
    by_type = serializers.DictField(read_only=True)
    recent_notifications = EngagementNotificationSerializer(
        many=True,
        read_only=True
    )
    period = serializers.CharField(read_only=True)


class CourseLikeSerializer(serializers.Serializer):
    """Serialize course engagement metrics for facilitators."""
    
    course_id = serializers.IntegerField(read_only=True)
    course_name = serializers.CharField(read_only=True)
    total_engagements = serializers.IntegerField(read_only=True)
    likes = serializers.IntegerField(read_only=True)
    comments = serializers.IntegerField(read_only=True)
    active_participants = serializers.IntegerField(read_only=True)
    engagement_rate = serializers.FloatField(read_only=True)
    trend = serializers.CharField(read_only=True)  # 'up', 'stable', 'down'


class CampaignEngagementSerializer(serializers.Serializer):
    """Serialize campaign engagement metrics for corporate users."""
    
    campaign_id = serializers.IntegerField(read_only=True)
    campaign_name = serializers.CharField(read_only=True)
    total_engagements = serializers.IntegerField(read_only=True)
    likes = serializers.IntegerField(read_only=True)
    comments = serializers.IntegerField(read_only=True)
    mentions = serializers.IntegerField(read_only=True)
    engagement_rate = serializers.FloatField(read_only=True)
    impressions = serializers.IntegerField(read_only=True)
    ctr = serializers.FloatField(read_only=True)  # Click-through rate
    conversion_rate = serializers.FloatField(read_only=True)
    trend = serializers.CharField(read_only=True)  # 'up', 'stable', 'down'


class CommunityStatsSerializer(serializers.Serializer):
    """Serialize public community-wide statistics."""
    
    total_users = serializers.IntegerField(read_only=True)
    active_users = serializers.IntegerField(read_only=True)
    total_posts = serializers.IntegerField(read_only=True)
    total_comments = serializers.IntegerField(read_only=True)
    total_engagements = serializers.IntegerField(read_only=True)
    total_mentions = serializers.IntegerField(read_only=True)
    total_groups = serializers.IntegerField(read_only=True)
    total_group_members = serializers.IntegerField(read_only=True)
    avg_engagement_per_post = serializers.FloatField(read_only=True)
    avg_engagement_per_user = serializers.FloatField(read_only=True)
    community_health_score = serializers.FloatField(read_only=True)
    top_contributors = ActiveUserSerializer(many=True, read_only=True)
    trending_posts = TrendingPostSerializer(many=True, read_only=True)
