"""
Engagement Analytics API Views

Provides endpoints for:
- User engagement metrics and reputation
- Post engagement analytics
- Facilitator course popularity insights
- Corporate campaign performance tracking
- Community trending data
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q, Sum, Avg, F
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .engagement import CommunityEngagementLog, UserReputation, EngagementNotification, MentionLog
from .models import Post, Comment
from .engagement_serializers import (
    EngagementLogSerializer,
    EngagementMetricsSerializer,
    TrendingPostSerializer,
    ActiveUserSerializer,
    UserReputationSerializer,
    MentionLogSerializer,
    EngagementNotificationSerializer,
    NotificationSummarySerializer,
)


class EngagementAnalyticsViewSet(viewsets.ModelViewSet):
    """
    Analytics for engagement data.
    
    Endpoints:
    - /api/engagement/analytics/user_metrics/ - User's engagement metrics
    - /api/engagement/analytics/post_metrics/ - Post engagement analytics
    - /api/engagement/analytics/trending/ - Trending posts
    - /api/engagement/analytics/active_users/ - Active users leaderboard
    - /api/engagement/analytics/my_reputation/ - User's reputation score
    """
    
    permission_classes = [IsAuthenticated]
    queryset = CommunityEngagementLog.objects.all()
    serializer_class = EngagementLogSerializer
    
    @action(detail=False, methods=['get'])
    def user_metrics(self, request):
        """
        Get engagement metrics for the authenticated user.
        
        Query params:
        - days: Number of days to look back (default: 30)
        - action_type: Filter by specific action type (optional)
        """
        days = int(request.query_params.get('days', 30))
        action_type = request.query_params.get('action_type')
        
        user = request.user
        metrics = CommunityEngagementLog.get_user_engagement_metrics(user, days=days)
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'metrics': metrics,
            'period_days': days,
        })
    
    @action(detail=False, methods=['get'])
    def post_metrics(self, request):
        """
        Get engagement metrics for a specific post.
        
        Query params:
        - post_id: Post ID (required)
        """
        post_id = request.query_params.get('post_id')
        
        if not post_id:
            return Response(
                {'error': 'post_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {'error': 'Post not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has permission to view analytics (post author or admin)
        if post.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        metrics = CommunityEngagementLog.get_post_engagement_metrics(post)
        
        return Response({
            'post_id': post.id,
            'post_title': post.title or post.content[:100],
            'metrics': metrics,
        })
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending posts based on recent engagement.
        
        Query params:
        - days: Number of days to look back (default: 7)
        - limit: Number of posts to return (default: 10)
        """
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        
        trending = CommunityEngagementLog.get_trending_posts(days=days, limit=limit)
        
        return Response({
            'trending_posts': list(trending),
            'period_days': days,
            'count': len(trending),
        })
    
    @action(detail=False, methods=['get'])
    def active_users(self, request):
        """
        Get most active users leaderboard.
        
        Query params:
        - days: Number of days to look back (default: 7)
        - limit: Number of users to return (default: 20)
        """
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 20))
        
        active = CommunityEngagementLog.get_active_users(days=days, limit=limit)
        
        return Response({
            'active_users': list(active),
            'period_days': days,
            'count': len(active),
        })
    
    @action(detail=False, methods=['get'])
    def my_reputation(self, request):
        """
        Get the authenticated user's reputation and badges.
        """
        user = request.user
        
        try:
            reputation = UserReputation.objects.get(user=user)
        except UserReputation.DoesNotExist:
            reputation = UserReputation.objects.create(user=user)
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'reputation_score': reputation.reputation_score,
            'activity_level': reputation.activity_level,
            'badges': reputation.badges,
            'total_posts': reputation.total_posts,
            'total_comments': reputation.total_comments,
            'total_likes_received': reputation.total_likes_received,
            'total_engagement_actions': reputation.total_engagement_actions,
            'updated_at': reputation.updated_at,
        })
    
    @action(detail=False, methods=['get'])
    def course_popularity(self, request):
        """
        Get course popularity metrics for facilitator users.
        
        Shows which courses are getting the most engagement.
        Only accessible to facilitators and admins.
        """
        from courses.models import Course
        
        # Check if user is facilitator or admin
        if request.user.profile.role != 'facilitator' and not request.user.is_staff:
            return Response(
                {'error': 'Only facilitators can access this data'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get engagement for posts from this facilitator's courses
        courses = Course.objects.filter(instructor=request.user)
        course_engagement = []
        
        for course in courses:
            posts = Post.objects.filter(author=request.user, course=course)
            engagement = CommunityEngagementLog.objects.filter(
                post__in=posts,
                created_at__gte=start_date
            ).aggregate(
                total_engagements=Count('id'),
                likes=Count('id', filter=Q(action_type='like_post')),
                comments=Count('id', filter=Q(action_type__in=['comment_post', 'reply_comment'])),
                views=Count('id', filter=Q(action_type='view_post')),
            )
            
            course_engagement.append({
                'course_id': course.id,
                'course_name': course.title,
                **engagement
            })
        
        return Response({
            'facilitator_id': request.user.id,
            'courses': course_engagement,
            'period_days': days,
        })
    
    @action(detail=False, methods=['get'])
    def campaign_performance(self, request):
        """
        Get campaign performance metrics for corporate users.
        
        Shows engagement metrics for sponsored campaigns.
        Only accessible to corporate users and admins.
        """
        from promotions.models import Campaign
        
        # Check if user is corporate or admin
        if request.user.profile.role != 'corporate' and not request.user.is_staff:
            return Response(
                {'error': 'Only corporate users can access this data'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get engagement for campaigns by this corporate user
        campaigns = Campaign.objects.filter(sponsor=request.user)
        campaign_engagement = []
        
        for campaign in campaigns:
            engagement = CommunityEngagementLog.objects.filter(
                post__sponsored_campaign=campaign,
                created_at__gte=start_date
            ).aggregate(
                total_engagements=Count('id'),
                likes=Count('id', filter=Q(action_type='like_post')),
                comments=Count('id', filter=Q(action_type__in=['comment_post', 'reply_comment'])),
                clicks=Sum('metadata__clicks', output_field=models.IntegerField()),
                ctr=Avg('metadata__ctr'),
            )
            
            campaign_engagement.append({
                'campaign_id': campaign.id,
                'campaign_title': campaign.title,
                **engagement
            })
        
        return Response({
            'corporate_id': request.user.id,
            'campaigns': campaign_engagement,
            'period_days': days,
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def record_click(self, request):
        """
        Record a UI click on a post action (like/bookmark/share/comment button).

        Expected body:
        {
            "post_id": "<id>",
            "action": "like|bookmark|share|comment|..."
        }
        """
        post_id = request.data.get('post_id')
        action = request.data.get('action') or request.data.get('action_name') or 'click'

        if not post_id:
            return Response({'error': 'post_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Log a lightweight click action for analytics
        try:
            CommunityEngagementLog.log_engagement(
                user=request.user,
                action_type='click_action',
                post=post,
                metadata={'action': action}
            )
        except Exception:
            # Non-fatal; return success so UI isn't blocked by analytics logging
            return Response({'ok': True, 'logged': False}, status=status.HTTP_200_OK)

        return Response({'ok': True, 'logged': True}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def community_stats(self, request):
        """
        Get overall community engagement statistics.
        
        Public endpoint showing community-wide metrics.
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get all engagement metrics
        all_logs = CommunityEngagementLog.objects.filter(created_at__gte=start_date)
        
        stats = {
            'total_engagements': all_logs.count(),
            'unique_users': all_logs.values('user').distinct().count(),
            'likes': all_logs.filter(action_type__in=['like_post', 'like_comment']).count(),
            'comments': all_logs.filter(action_type__in=['comment_post', 'reply_comment']).count(),
            'mentions': all_logs.filter(action_type='mention_user').count(),
            'group_activity': all_logs.filter(action_type__in=['join_group', 'leave_group']).count(),
            'period_days': days,
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_mentions(self, request):
        """
        Get recent mentions of the authenticated user.
        
        Returns posts and comments where user was @mentioned.
        """
        limit = int(request.query_params.get('limit', 20))
        
        mentions = MentionLog.objects.filter(
            mentioned_user=request.user
        ).select_related('post', 'comment', 'mentioned_by').order_by('-created_at')[:limit]
        
        mention_data = []
        for mention in mentions:
            data = {
                'mentioned_by': mention.mentioned_by.username,
                'created_at': mention.created_at,
            }
            
            if mention.post:
                data['type'] = 'post'
                data['post_id'] = mention.post.id
                data['post_title'] = mention.post.title or mention.post.content[:50]
            elif mention.comment:
                data['type'] = 'comment'
                data['comment_id'] = mention.comment.id
                data['post_id'] = mention.comment.post.id
                data['comment_preview'] = mention.comment.content[:100]
            
            mention_data.append(data)
        
        return Response({
            'mentions': mention_data,
            'count': len(mention_data),
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_notifications(self, request):
        """
        Get engagement notifications for the authenticated user.
        
        Returns recent notifications about engagement on their content.
        """
        try:
            limit = int(request.query_params.get('limit', 20))
            read_param = request.query_params.get('read')
            
            # Build base queryset
            notifications_qs = EngagementNotification.objects.filter(
                user=request.user
            ).order_by('-created_at')
            
            # Apply read filter if provided
            if read_param is not None:
                read_bool = read_param.lower() == 'true'
                notifications_qs = notifications_qs.filter(read=read_bool)
            
            # Get limited results
            notifications = notifications_qs[:limit]
            
            # Convert to list and fetch related data
            notifications_list = list(notifications)
            
            notification_data = []
            for notif in notifications_list:
                try:
                    # Build triggered_by data safely
                    triggered_by_dict = {
                        'id': None,
                        'username': 'Unknown',
                        'profile': {},
                    }
                    
                    if notif.triggered_by:
                        triggered_by_dict['id'] = notif.triggered_by.id
                        triggered_by_dict['username'] = notif.triggered_by.username or 'Unknown'
                        
                        # Try to get profile data
                        try:
                            if hasattr(notif.triggered_by, 'profile') and notif.triggered_by.profile:
                                triggered_by_dict['profile'] = {
                                    'full_name': notif.triggered_by.profile.full_name or '',
                                    'avatar_url': notif.triggered_by.profile.avatar_url or '',
                                }
                        except Exception:
                            pass  # Profile access failed, use empty dict
                    
                    # Build notification data
                    notif_data = {
                        'id': notif.id,
                        'user_id': notif.user_id,
                        'type': notif.notification_type,
                        'notification_type': notif.notification_type,
                        'notification_type_display': notif.get_notification_type_display(),
                        'triggered_by': triggered_by_dict,
                        'message': f"{triggered_by_dict['username']} triggered a {notif.notification_type} notification",
                        'read': notif.read,
                        'email_sent': notif.email_sent,
                        'in_app_sent': notif.in_app_sent,
                        'created_at': notif.created_at.isoformat() if notif.created_at else None,
                        'read_at': notif.read_at.isoformat() if notif.read_at else None,
                    }
                    notification_data.append(notif_data)
                except Exception as item_err:
                    # Skip problematic items
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error processing notification {notif.id}: {item_err}")
                    continue
            
            return Response({
                'results': notification_data,
                'notifications': notification_data,
                'count': len(notification_data),
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in my_notifications endpoint: {e}")
            return Response({
                'results': [],
                'notifications': [],
                'count': 0,
                'error': str(e)
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_notifications_read(self, request):
        """
        Mark notifications as read.
        
        Request body:
        {
            "notification_ids": [1, 2, 3]
        }
        """
        notification_ids = request.data.get('notification_ids', [])
        
        updated = EngagementNotification.objects.filter(
            id__in=notification_ids,
            user=request.user
        ).update(
            read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'Marked {updated} notifications as read',
            'count': updated,
        })
