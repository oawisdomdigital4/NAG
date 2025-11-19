from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from community.models import EngagementLog, Post, Comment
from django.utils import timezone
from datetime import timedelta

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        # Get overall stats for the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        user = request.user

        # Get engagement stats
        engagement_stats = EngagementLog.objects.filter(
            user=user,
            created_at__range=(start_date, end_date)
        ).values('action_type').annotate(
            count=Count('id')
        )

        # Get post stats
        post_stats = Post.objects.filter(
            author=user,
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_posts=Count('id'),
            avg_views=Avg('view_count'),
            avg_engagement=Avg('engagement_score')
        )

        # Get comment stats
        comment_stats = Comment.objects.filter(
            author=user,
            created_at__range=(start_date, end_date)
        ).count()

        return Response({
            'engagement_stats': engagement_stats,
            'post_stats': post_stats,
            'comment_stats': comment_stats
        })

    @action(detail=False, methods=['get'])
    def daily_engagement(self, request):
        # Get daily engagement stats for last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        user = request.user

        daily_stats = EngagementLog.objects.filter(
            user=user,
            created_at__range=(start_date, end_date)
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            views=Count('id', filter=Q(action_type='view')),
            likes=Count('id', filter=Q(action_type='like')),
            comments=Count('id', filter=Q(action_type='comment')),
            shares=Count('id', filter=Q(action_type='share'))
        ).order_by('date')

        return Response(daily_stats)

    @action(detail=False, methods=['get'])
    def post_performance(self, request):
        # Get performance stats for user's posts
        user = request.user
        posts = Post.objects.filter(
            author=user
        ).values(
            'id', 
            'title', 
            'created_at'
        ).annotate(
            views=Count('engagement_logs', filter=Q(engagement_logs__action_type='view')),
            likes=Count('engagement_logs', filter=Q(engagement_logs__action_type='like')),
            comments=Count('comments'),
            engagement_rate=Avg('engagement_score')
        ).order_by('-created_at')

        return Response(posts)

    @action(detail=False, methods=['get'])
    def audience_insights(self, request):
        # Get insights about the user's audience
        user = request.user
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Get audience demographics and engagement patterns
        audience_stats = EngagementLog.objects.filter(
            post__author=user,
            created_at__range=(start_date, end_date)
        ).values(
            'user__profile__country',
            'user__role'
        ).annotate(
            engagement_count=Count('id')
        ).order_by('-engagement_count')

        return Response(audience_stats)