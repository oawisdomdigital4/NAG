from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, F, Window, Sum
from django.db.models.functions import ExtractDay, ExtractHour, TruncDate
from django.utils import timezone
from datetime import timedelta
from .models import Post, Comment, PostReaction, EngagementLog, SponsorCampaign, Group, UserProfile

class CommunityAnalytics:
    """Provides analytics data for the community platform."""
    
    @staticmethod
    def get_role_analytics(days=30):
        """Get engagement metrics broken down by user role."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Get post counts by role
        posts_by_role = Post.objects.filter(
            created_at__gte=period_start
        ).values(
            'author__community_profile__role'
        ).annotate(
            post_count=Count('id'),
            total_views=Sum('view_count'),
            avg_engagement=Avg('engagement_score')
        )
        
        # Get engagement by role
        engagement_by_role = EngagementLog.objects.filter(
            created_at__gte=period_start
        ).values(
            'user__community_profile__role'
        ).annotate(
            view_count=Count('id', filter=F('action_type') == 'view'),
            like_count=Count('id', filter=F('action_type') == 'like'),
            comment_count=Count('id', filter=F('action_type') == 'comment')
        )
        
        return {
            'posts_by_role': list(posts_by_role),
            'engagement_by_role': list(engagement_by_role)
        }
    
    @staticmethod
    def get_trending_topics(days=7):
        """Get trending topics/hashtags from posts."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Analyze post content for hashtags/topics
        # This is a simplified version - in production you'd want
        # proper text analysis and topic extraction
        from collections import Counter
        import re
        
        # Get recent posts
        recent_posts = Post.objects.filter(
            created_at__gte=period_start
        ).values_list('content', flat=True)
        
        # Extract hashtags
        hashtags = []
        for content in recent_posts:
            tags = re.findall(r'#(\w+)', content)
            hashtags.extend(tags)
        
        # Count occurrences
        trending = Counter(hashtags).most_common(10)
        
        return [{'tag': tag, 'count': count} for tag, count in trending]
    
    @staticmethod
    def get_user_growth(days=30):
        """Get user growth metrics."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Daily new users
        new_users = UserProfile.objects.filter(
            created_at__gte=period_start
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Active users
        active_users = EngagementLog.objects.filter(
            created_at__gte=period_start
        ).values('user').distinct().count()
        
        # Engagement rate
        total_users = UserProfile.objects.count()
        engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
        
        return {
            'new_users_trend': list(new_users),
            'active_users': active_users,
            'total_users': total_users,
            'engagement_rate': engagement_rate
        }
    
    @staticmethod
    def get_content_performance(days=30):
        """Get content performance metrics."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Top performing posts
        top_posts = Post.objects.filter(
            created_at__gte=period_start
        ).annotate(
            interaction_count=Count('reactions') + Count('comments')
        ).order_by('-interaction_count')[:10]
        
        # Hourly post activity
        hourly_activity = Post.objects.filter(
            created_at__gte=period_start
        ).annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            post_count=Count('id')
        ).order_by('hour')
        
        # Engagement by content type
        engagement_by_type = EngagementLog.objects.filter(
            created_at__gte=period_start
        ).values(
            'action_type'
        ).annotate(
            count=Count('id')
        )
        
        return {
            'top_posts': [
                {
                    'id': post.id,
                    'author': post.author.email if post.author else None,
                    'interaction_count': post.interaction_count,
                    'created_at': post.created_at
                } for post in top_posts
            ],
            'hourly_activity': list(hourly_activity),
            'engagement_by_type': list(engagement_by_type)
        }
    
    @staticmethod
    def get_group_analytics(days=30):
        """Get group activity and growth metrics."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Most active groups
        active_groups = Group.objects.filter(
            posts__created_at__gte=period_start
        ).annotate(
            post_count=Count('posts'),
            member_count=Count('memberships'),
            engagement_rate=F('post_count') * 1.0 / F('member_count')
        ).order_by('-engagement_rate')[:10]
        
        # New group creation trend
        new_groups = Group.objects.filter(
            created_at__gte=period_start
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return {
            'active_groups': [
                {
                    'id': group.id,
                    'name': group.name,
                    'post_count': group.post_count,
                    'member_count': group.member_count,
                    'engagement_rate': group.engagement_rate
                } for group in active_groups
            ],
            'new_groups_trend': list(new_groups)
        }
    
    @staticmethod
    def get_sponsor_analytics(days=30):
        """Get sponsorship and campaign metrics."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Active campaigns performance
        campaigns = SponsorCampaign.objects.filter(
            created_at__gte=period_start
        ).annotate(
            click_through_rate=F('click_count') * 100.0 / F('impression_count')
        ).values(
            'id', 'title', 'impression_count', 'click_count',
            'click_through_rate', 'budget', 'cost_per_view'
        )
        
        # Daily campaign metrics
        daily_metrics = EngagementLog.objects.filter(
            created_at__gte=period_start,
            metadata__has_key='campaign_id'
        ).annotate(
            date=TruncDate('created_at')
        ).values('date', 'action_type').annotate(
            count=Count('id')
        ).order_by('date', 'action_type')
        
        return {
            'campaigns': list(campaigns),
            'daily_metrics': list(daily_metrics)
        }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def community_analytics(request):
    """Get comprehensive community analytics."""
    days = int(request.query_params.get('days', 30))
    
    # Get all analytics
    analytics = {
        'role_metrics': CommunityAnalytics.get_role_analytics(days),
        'trending_topics': CommunityAnalytics.get_trending_topics(days),
        'user_growth': CommunityAnalytics.get_user_growth(days),
        'content_performance': CommunityAnalytics.get_content_performance(days),
        'group_analytics': CommunityAnalytics.get_group_analytics(days)
    }
    
    # Add sponsor analytics for staff/admin
    if request.user.is_staff:
        analytics['sponsor_analytics'] = CommunityAnalytics.get_sponsor_analytics(days)
    
    return Response(analytics)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_analytics(request, user_id=None):
    """Get analytics for a specific user."""
    from django.shortcuts import get_object_or_404
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    days = int(request.query_params.get('days', 30))
    period_start = timezone.now() - timedelta(days=days)
    
    # Get target user (default to requesting user)
    target_user = get_object_or_404(User, id=user_id) if user_id else request.user
    
    # Only allow users to see their own analytics unless staff
    if target_user != request.user and not request.user.is_staff:
        return Response({'detail': 'Not authorized'}, status=403)
    
    # Get user's posts
    posts = Post.objects.filter(
        author=target_user,
        created_at__gte=period_start
    )
    
    # Calculate metrics
    metrics = {
        'post_count': posts.count(),
        'total_views': posts.aggregate(Sum('view_count'))['view_count__sum'] or 0,
        'avg_engagement': posts.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0,
        
        # Get engagement received
        'reactions_received': PostReaction.objects.filter(
            post__author=target_user,
            created_at__gte=period_start
        ).count(),
        
        'comments_received': Comment.objects.filter(
            post__author=target_user,
            created_at__gte=period_start
        ).count(),
        
        # Get engagement given
        'reactions_given': PostReaction.objects.filter(
            user=target_user,
            created_at__gte=period_start
        ).count(),
        
        'comments_given': Comment.objects.filter(
            author=target_user,
            created_at__gte=period_start
        ).count(),
        
        # Group activity
        'groups_joined': target_user.community_group_memberships.filter(
            joined_at__gte=period_start
        ).count(),
        
        'groups_created': target_user.community_created_groups.filter(
            created_at__gte=period_start
        ).count()
    }
    
    # Add role-specific metrics
    try:
        role = target_user.community_profile.role
        if role in ['facilitator', 'corporate']:
            # Add sponsor campaign metrics
            campaign_metrics = SponsorCampaign.objects.filter(
                sponsor=target_user,
                created_at__gte=period_start
            ).aggregate(
                total_impressions=Sum('impression_count'),
                total_clicks=Sum('click_count'),
                total_spend=Sum('budget')
            )
            metrics.update(campaign_metrics)
    except Exception:
        pass
    
    return Response(metrics)