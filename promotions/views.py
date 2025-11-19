from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, BaseRenderer
from django.db.models import Q, F, Sum, Avg, Count
from .models import SponsorCampaign, EngagementLog, WithdrawalRequest
from community.models import (
    CorporateOpportunity,
    CorporateConnection,
    CorporateVerification,
)
from community.models import Post
from .serializers import (
    SponsorCampaignSerializer,
    WithdrawalRequestSerializer,
    OpportunityListSerializer,
    ConnectionListSerializer,
    EngagementLogSerializer,
)
from django.utils import timezone
from .analytics_service import AnalyticsService
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from rest_framework.decorators import api_view, authentication_classes
from accounts.authentication import DatabaseTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from django.http import HttpResponse
import csv
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from django.db import transaction
from decimal import Decimal
from accounts.models import UserProfile
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status


class CSVRenderer(BaseRenderer):
    """Custom renderer for CSV content"""
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, str):
            return data.encode('utf-8')
        return str(data).encode('utf-8')

class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Admin/staff can see all withdrawals, regular users can only see their own
        if user.is_staff or user.is_superuser:
            return WithdrawalRequest.objects.all()
        # promotions WithdrawalRequest stores facilitator as the user field
        return WithdrawalRequest.objects.filter(facilitator=user)

    def perform_create(self, serializer):
        serializer.save(facilitator=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a withdrawal request and deduct from user's balance"""
        withdrawal = self.get_object()
        notes = request.data.get('notes', '')
        try:
            withdrawal.process('approved', request.user, notes)
            serializer = self.get_serializer(withdrawal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error approving withdrawal {pk}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a withdrawal request"""
        withdrawal = self.get_object()
        notes = request.data.get('notes', '')
        try:
            withdrawal.process('rejected', request.user, notes)
            serializer = self.get_serializer(withdrawal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rejecting withdrawal {pk}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def complete(self, request, pk=None):
        """Mark a withdrawal as completed and deduct from user's balance"""
        withdrawal = self.get_object()
        notes = request.data.get('notes', '')
        try:
            withdrawal.process('completed', request.user, notes)
            serializer = self.get_serializer(withdrawal)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing withdrawal {pk}: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def record_impression(self, request, pk=None):
        """Record an impression for a sponsor campaign (public endpoint)."""
        campaign = self.get_object()
        try:
            SponsorCampaign.objects.filter(id=campaign.id).update(impression_count=F('impression_count') + 1)
            EngagementLog.objects.create(
                user=request.user if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False) else None,
                action_type='view',
                post=campaign.sponsored_post if hasattr(campaign, 'sponsored_post') else None,
                metadata={'campaign_id': campaign.id},
            )
        except Exception:
            return Response({'detail': 'failed to record impression'}, status=500)
        return Response({'status': 'impression recorded'})

class SponsorAnalyticsView(APIView):
    """Return simple aggregated analytics for a sponsor campaign.

    Query params: campaign_id (required), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        campaign_id = request.query_params.get('campaign_id')
        start = request.query_params.get('start_date')
        end = request.query_params.get('end_date')
        if not campaign_id:
            return Response({'detail': 'campaign_id is required'}, status=400)
        try:
            campaign = SponsorCampaign.objects.get(id=campaign_id)
        except SponsorCampaign.DoesNotExist:
            return Response({'detail': 'campaign not found'}, status=404)

        # Only allow sponsor or staff to fetch analytics
        user = request.user
        if not (getattr(user, 'is_staff', False) or campaign.sponsor_id == getattr(user, 'id', None)):
            return Response({'detail': 'forbidden'}, status=403)

        qs = EngagementLog.objects.filter(metadata__campaign_id__in=[str(campaign.id), campaign.id])
        if start:
            try:
                qs = qs.filter(created_at__gte=start)
            except Exception:
                pass
        if end:
            try:
                qs = qs.filter(created_at__lte=end)
            except Exception:
                pass

        totals = qs.values('action_type').order_by().annotate(count=Count('id'))
        data = {item['action_type']: item['count'] for item in totals}
        data.update({
            'impression_count': campaign.impression_count,
            'click_count': campaign.click_count,
            'engagement_rate': campaign.engagement_rate,
        })
        return Response(data)


# --------------------------- Sponsor Campaigns ---------------------------

class SponsorCampaignViewSet(viewsets.ModelViewSet):
    """Manage sponsor campaigns and provide impression/click tracking endpoints."""
    queryset = SponsorCampaign.objects.all()
    serializer_class = SponsorCampaignSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        # Only return active campaigns by default for list endpoint
        qs = super().get_queryset()
        action = getattr(self, 'action', None)
        if action == 'list':
            now = timezone.now()
            return qs.filter(status='active', start_date__lte=now, end_date__gte=now).order_by('-priority_level', '-created_at')
        # For other actions like export_report and analytics_summary, filter by current user
        if action in ['export_report', 'analytics_summary', 'my_campaigns']:
            return qs.filter(sponsor=self.request.user)

        # For detail actions (retrieve/update/destroy/etc), restrict to owner unless staff
        # Note: public 'record_impression' should be allowed for any requester (so impressions can be recorded)
        if action in ['retrieve', 'update', 'partial_update', 'destroy', 'activate', 'pause', 'resume', 'record_click']:
            user = getattr(self.request, 'user', None)
            if user and getattr(user, 'is_staff', False):
                return qs
            return qs.filter(sponsor=user)

        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def start_campaign(self, request):
        """Start a new campaign for the user"""
        user = request.user
        
        # Validate required fields
        required_fields = ['title', 'description', 'start_date', 'end_date', 'budget', 'cost_per_view']
        for field in required_fields:
            if field not in request.data:
                return Response({'error': f'{field} is required'}, status=400)
        
        try:
            # If a sponsored_post_id was provided, link to existing Post
            sponsored_post_id = request.data.get('sponsored_post_id')
            post_instance = None
            if sponsored_post_id:
                try:
                    post_instance = Post.objects.get(id=sponsored_post_id)
                except Post.DoesNotExist:
                    return Response({'error': 'Sponsored post not found'}, status=404)

            # If no post provided, create a minimal post for the campaign
            if not post_instance:
                media_urls = []
                if request.data.get('media_url'):
                    media_urls = [request.data.get('media_url')]
                
                post_instance = Post.objects.create(
                    author=user,
                    title=request.data.get('title') or 'Sponsored Content',
                    content=request.data.get('description') or '',
                    feed_visibility='public_global',
                    is_sponsored=True,
                    media_urls=media_urls
                )

            # Determine status: allow client to request 'draft', 'under_review' or 'active'
            status = request.data.get('status', 'draft')
            allowed_statuses = {choice[0] for choice in SponsorCampaign.STATUS_CHOICES}
            if status not in allowed_statuses:
                status = 'draft'

            # If status is not draft, attempt to deduct from user's profile balance
            budget = Decimal(str(request.data.get('budget', 0)))

            with transaction.atomic():
                if status != 'draft' and budget > 0:
                    # Attempt to atomically decrement user profile balance
                    updated = UserProfile.objects.filter(user=user, balance__gte=budget).update(balance=F('balance') - budget)
                    if updated == 0:
                        return Response({'error': 'Insufficient balance'}, status=402)

                # Create campaign linked to the post
                campaign = SponsorCampaign.objects.create(
                    sponsor=user,
                    title=request.data.get('title'),
                    description=request.data.get('description'),
                    sponsored_post=post_instance,
                    start_date=request.data.get('start_date'),
                    end_date=request.data.get('end_date'),
                    budget=budget,
                    cost_per_view=request.data.get('cost_per_view'),
                    priority_level=request.data.get('priority_level', 1),
                    status=status,
                    target_audience=request.data.get('target_audience', {})
                )

            serializer = self.get_serializer(campaign)
            return Response({
                'message': 'Campaign created successfully',
                'campaign': serializer.data
            }, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def perform_update(self, serializer):
        """Handle update of campaign and linked post media_urls"""
        campaign = serializer.save()
        
        # If media_url is provided in request data, update the post's media_urls
        media_url = self.request.data.get('media_url')
        if media_url and campaign.sponsored_post:
            campaign.sponsored_post.media_urls = [media_url]
            campaign.sponsored_post.save(update_fields=['media_urls'])

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        """Activate a draft campaign"""
        campaign = self.get_object()
        
        # Verify user owns the campaign
        if campaign.sponsor_id != request.user.id:
            return Response({'error': 'You do not own this campaign'}, status=403)
        
        if campaign.status != 'draft':
            return Response({'error': f'Campaign is already {campaign.status}'}, status=400)
        
        campaign.status = 'active'
        campaign.save(update_fields=['status', 'updated_at'])
        
        serializer = self.get_serializer(campaign)
        return Response({
            'message': 'Campaign activated successfully',
            'campaign': serializer.data
        }, status=200)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pause(self, request, pk=None):
        """Pause an active campaign"""
        campaign = self.get_object()
        
        if campaign.sponsor_id != request.user.id:
            return Response({'error': 'You do not own this campaign'}, status=403)
        
        if campaign.status not in ['active', 'completed']:
            return Response({'error': f'Cannot pause campaign with status {campaign.status}'}, status=400)
        
        campaign.status = 'paused'
        campaign.save(update_fields=['status', 'updated_at'])
        
        return Response({'status': 'campaign paused'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resume(self, request, pk=None):
        """Resume a paused campaign"""
        campaign = self.get_object()
        
        if campaign.sponsor_id != request.user.id:
            return Response({'error': 'You do not own this campaign'}, status=403)
        
        if campaign.status != 'paused':
            return Response({'error': f'Campaign must be paused to resume'}, status=400)
        
        campaign.status = 'active'
        campaign.save(update_fields=['status', 'updated_at'])
        
        return Response({'status': 'campaign resumed'})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def record_impression(self, request, pk=None):
        """Public endpoint to record an impression for a sponsor campaign."""
        campaign = self.get_object()
        try:
            SponsorCampaign.objects.filter(id=campaign.id).update(impression_count=F('impression_count') + 1)
            EngagementLog.objects.create(
                user=request.user if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False) else None,
                action_type='view',
                post=campaign.sponsored_post if hasattr(campaign, 'sponsored_post') else None,
                metadata={'campaign_id': campaign.id},
            )
        except Exception:
            return Response({'detail': 'failed to record impression'}, status=500)
        return Response({'status': 'impression recorded'})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_pause(self, request):
        """
        Bulk pause multiple campaigns.
        
        Request body:
        {
            "campaign_ids": [1, 2, 3, ...]
        }
        """
        campaign_ids = request.data.get('campaign_ids', [])
        
        if not campaign_ids:
            return Response({'error': 'campaign_ids list is required'}, status=400)
        
        # Update only campaigns owned by the user
        updated = SponsorCampaign.objects.filter(
            id__in=campaign_ids,
            sponsor=request.user,
            status='active'
        ).update(status='paused')
        
        return Response({
            'status': 'success',
            'updated_count': updated,
            'requested_count': len(campaign_ids)
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_resume(self, request):
        """
        Bulk resume multiple paused campaigns.
        
        Request body:
        {
            "campaign_ids": [1, 2, 3, ...]
        }
        """
        campaign_ids = request.data.get('campaign_ids', [])
        
        if not campaign_ids:
            return Response({'error': 'campaign_ids list is required'}, status=400)
        
        updated = SponsorCampaign.objects.filter(
            id__in=campaign_ids,
            sponsor=request.user,
            status='paused'
        ).update(status='active')
        
        return Response({
            'status': 'success',
            'updated_count': updated,
            'requested_count': len(campaign_ids)
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_status(self, request):
        """
        Bulk update campaign status.
        
        Request body:
        {
            "campaign_ids": [1, 2, 3, ...],
            "status": "paused|active|draft"
        }
        """
        campaign_ids = request.data.get('campaign_ids', [])
        new_status = request.data.get('status', '').lower()
        
        if not campaign_ids or not new_status:
            return Response({'error': 'campaign_ids and status are required'}, status=400)
        
        if new_status not in ['draft', 'active', 'paused', 'completed']:
            return Response({
                'error': f'Invalid status. Must be one of: draft, active, paused, completed'
            }, status=400)
        
        updated = SponsorCampaign.objects.filter(
            id__in=campaign_ids,
            sponsor=request.user
        ).update(status=new_status)
        
        return Response({
            'status': 'success',
            'updated_count': updated,
            'new_status': new_status,
            'requested_count': len(campaign_ids)
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_campaigns(self, request):
        """Get all campaigns created by the current user, regardless of status"""
        user = request.user
        campaigns = SponsorCampaign.objects.filter(sponsor=user).order_by('-created_at')
        serializer = self.get_serializer(campaigns, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[])
    def active_campaigns(self, request):
        """
        Get all active campaigns for display in Community, Magazine, and Homepage.
        No authentication required - public endpoint.
        
        Query params:
        - page: page number (default 1)
        - page_size: items per page (default 10)
        - tag: filter by industry tag (can be multiple)
        - priority: filter by priority level (1, 2, or 3)
        """
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).select_related('sponsored_post', 'sponsor').order_by('-priority_level', '-created_at')
        
        # Filter by tags if provided
        tags = request.query_params.getlist('tag')
        if tags:
            tag_queries = Q()
            for tag in tags:
                tag_queries |= Q(sponsored_post__industry_tags__contains=tag)
            campaigns = campaigns.filter(tag_queries)
        
        # Filter by priority level if provided
        priority = request.query_params.get('priority')
        if priority and str(priority).isdigit():
            campaigns = campaigns.filter(priority_level=int(priority))
        
        # Paginate results
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = campaigns.count()
        paginated_campaigns = campaigns[start:end]
        
        serializer = self.get_serializer(paginated_campaigns, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_report(self, request):
        """Export campaigns report as CSV for authenticated user"""
        user = request.user
        
        # Get campaigns for the user
        campaigns = SponsorCampaign.objects.filter(sponsor=user).order_by('-created_at')
        
        if not campaigns.exists():
            # Return an empty CSV (header-only) instead of 404 so frontend can download an empty file
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow([
                'Campaign ID',
                'Title',
                'Status',
                'Start Date',
                'End Date',
                'Budget (USD)',
                'Cost per View',
                'Impressions',
                'Clicks',
                'Engagement Rate (%)',
                'Priority Level',
                'Created At',
                'Updated At'
            ])
            csv_content = csv_buffer.getvalue()
            response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="campaigns_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            return response
        
        # Create CSV content in memory
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header row
        writer.writerow([
            'Campaign ID',
            'Title',
            'Status',
            'Start Date',
            'End Date',
            'Budget (USD)',
            'Cost per View',
            'Impressions',
            'Clicks',
            'Engagement Rate (%)',
            'Priority Level',
            'Created At',
            'Updated At'
        ])
        
        # Write campaign data rows
        for campaign in campaigns:
            writer.writerow([
                campaign.id,
                campaign.title,
                campaign.get_status_display(),
                campaign.start_date.strftime('%Y-%m-%d %H:%M:%S') if campaign.start_date else '',
                campaign.end_date.strftime('%Y-%m-%d %H:%M:%S') if campaign.end_date else '',
                float(campaign.budget),
                float(campaign.cost_per_view),
                campaign.impression_count,
                campaign.click_count,
                round(campaign.engagement_rate, 2),
                campaign.get_priority_level_display(),
                campaign.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                campaign.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Get the CSV content
        csv_content = csv_buffer.getvalue()
        
        # Return HttpResponse directly to bypass DRF content negotiation
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="campaigns_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def analytics_summary(self, request):
        """Get aggregated analytics summary for all user campaigns"""
        user = request.user
        days = int(request.query_params.get('days', 30))
        
        # Get campaigns
        campaigns = SponsorCampaign.objects.filter(sponsor=user)
        
        if not campaigns.exists():
            return Response({
                'total_campaigns': 0,
                'active_campaigns': 0,
                'total_impressions': 0,
                'total_clicks': 0,
                'average_engagement_rate': 0.0,
                'total_budget': 0.0,
                'total_spent': 0.0
            })
        
        # Aggregate metrics
        stats = campaigns.aggregate(
            total_impressions=Sum('impression_count', default=0),
            total_clicks=Sum('click_count', default=0),
            average_engagement=Avg('engagement_rate', default=0.0),
            total_budget=Sum('budget', default=0),
            active_count=Count('id', filter=Q(status='active'))
        )
        
        return Response({
            'total_campaigns': campaigns.count(),
            'active_campaigns': stats['active_count'],
            'total_impressions': stats['total_impressions'],
            'total_clicks': stats['total_clicks'],
            'average_engagement_rate': round(stats['average_engagement'], 2),
            'total_budget': float(stats['total_budget']),
            'period_days': days
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def poll_metrics(self, request):
        """
        Poll real-time metrics for a specific campaign.
        Public endpoint - no authentication required.
        Supports client-side polling for live updates.
        
        Query params:
        - campaign_id: campaign to get metrics for (required)
        """
        from .tasks import CampaignMetricsService
        
        campaign_id = request.query_params.get('campaign_id')
        if not campaign_id:
            return Response({'error': 'campaign_id is required'}, status=400)
        
        metrics = CampaignMetricsService.get_campaign_metrics(campaign_id)
        if metrics is None:
            return Response({'error': 'Campaign not found'}, status=404)
        
        return Response(metrics)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def poll_active(self, request):
        """
        Poll metrics for all active campaigns.
        Lightweight endpoint for dashboard updates.
        
        Query params:
        - limit: max number of campaigns (default 20)
        """
        from .tasks import CampaignMetricsService
        
        data = CampaignMetricsService.get_active_campaigns_metrics()
        
        limit = int(request.query_params.get('limit', 20))
        if limit > 0:
            data['campaigns'] = data['campaigns'][:limit]
        
        return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def record_profile_visit(request):
    """Public endpoint to record a profile visit.

    Expected body: { "target_user": <user_id> }
    """
    try:
        target_user = request.data.get('target_user')
        if not target_user:
            return Response({'error': 'target_user is required'}, status=400)

        EngagementLog.objects.create(
            user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
            action_type='profile_view',
            metadata={'target_user_id': str(target_user)}
        )
        return Response({'status': 'profile visit recorded'}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def record_post_view(request):
    """Public endpoint to record a post view.

    Expected body: { "post_id": <post_id> }
    """
    try:
        post_id = request.data.get('post_id')
        if not post_id:
            return Response({'error': 'post_id is required'}, status=400)

        from community.models import Post
        post = Post.objects.get(id=post_id)

        EngagementLog.objects.create(
            user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
            action_type='view',
            post=post,
            metadata={'post_id': str(post_id)}
        )
        return Response({'status': 'post view recorded'}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_engagement_analytics(request):
    """Return per-post engagement metrics for the authenticated user's posts.
    
    This includes views, likes, comments, shares, and bookmarks for each post authored by the user.
    """
    days = int(request.query_params.get('days', 30))
    user = request.user
    
    engagement_by_post = AnalyticsService.get_user_post_engagement(user, days)
    
    return Response({
        'engagement_by_post': engagement_by_post,
        'period_days': days
    }, status=status.HTTP_200_OK)





class ProfileMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        target_user_id = request.query_params.get('user_id') or request.query_params.get('target_user')

        # If a target user id is provided, attempt to resolve and return metrics for that user.
        # Otherwise default to the authenticated user.
        if target_user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                target = User.objects.get(id=target_user_id)
            except Exception:
                return Response({'error': 'target user not found'}, status=status.HTTP_404_NOT_FOUND)
            profile_metrics = AnalyticsService.get_profile_metrics(target, days)
            return Response(profile_metrics, status=status.HTTP_200_OK)

        user = request.user
        profile_metrics = AnalyticsService.get_profile_metrics(user, days)
        return Response(profile_metrics, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def poll_user_metrics(self, request):
        """
        Poll metrics for current user's campaigns.
        Authenticated endpoint for sponsor dashboard.
        """
        from .tasks import CampaignMetricsService
        
        data = CampaignMetricsService.get_user_campaigns_metrics(request.user.id)
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def poll_trending(self, request):
        """
        Poll trending campaigns based on engagement.
        
        Query params:
        - limit: number of campaigns to return (default 10)
        """
        from .tasks import CampaignMetricsService
        
        limit = int(request.query_params.get('limit', 10))
        data = CampaignMetricsService.get_trending_campaigns(limit=limit)
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def refresh_metrics(self, request, pk=None):
        """
        Manually refresh metrics for a campaign.
        Forces cache invalidation and returns fresh data.
        """
        from .tasks import CampaignMetricsService
        
        metrics = CampaignMetricsService.refresh_campaign_metrics(pk)
        if metrics is None:
            return Response({'error': 'Campaign not found'}, status=404)
        
        return Response(metrics)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def poll_analytics(self, request):
        """
        Poll daily analytics for a campaign.
        
        Query params:
        - campaign_id: campaign to get analytics for (required)
        - days: number of days to return (default 30)
        """
        from .tasks import CampaignMetricsService
        
        campaign_id = request.query_params.get('campaign_id')
        if not campaign_id:
            return Response({'error': 'campaign_id is required'}, status=400)
        
        days = int(request.query_params.get('days', 30))
        data = CampaignMetricsService.get_campaign_daily_analytics(campaign_id, days=days)
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_metrics(self, request):
        """
        Export detailed campaign metrics as JSON or CSV.
        
        Query params:
        - format: 'json' (default) or 'csv'
        - days: number of days to include (default 30)
        """
        from .tasks import CampaignMetricsService
        
        user = request.user
        export_format = request.query_params.get('format', 'json').lower()
        days = int(request.query_params.get('days', 30))
        
        campaigns = SponsorCampaign.objects.filter(sponsor=user).select_related('sponsored_post')
        
        metrics_data = []
        for campaign in campaigns:
            analytics = CampaignMetricsService.get_campaign_daily_analytics(campaign.id, days=days)
            
            metrics_data.append({
                'campaign': {
                    'id': campaign.id,
                    'title': campaign.title,
                    'status': campaign.status,
                    'priority_level': campaign.priority_level,
                    'budget': float(campaign.budget),
                    'start_date': campaign.start_date.isoformat(),
                    'end_date': campaign.end_date.isoformat(),
                },
                'performance': campaign.get_performance_metrics(),
                'daily_analytics': analytics['analytics'],
            })
        
        if export_format == 'csv':
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            
            # Header
            writer.writerow([
                'Campaign ID', 'Title', 'Status', 'Priority', 'Budget',
                'Impressions', 'Clicks', 'Engagement Rate (%)',
                'Cost per Click', 'Cost per Impression', 'ROI Multiplier'
            ])
            
            # Data rows
            for data in metrics_data:
                campaign = data['campaign']
                perf = data['performance']
                writer.writerow([
                    campaign['id'],
                    campaign['title'],
                    campaign['status'],
                    campaign['priority_level'],
                    campaign['budget'],
                    perf['impressions'],
                    perf['clicks'],
                    perf['engagement_rate'],
                    perf['cost_per_click'],
                    perf['cost_per_impression'],
                    perf['roi_multiplier'],
                ])
            
            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="campaign_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            return response
        
        # Default JSON response
        return Response({
            'export_date': timezone.now().isoformat(),
            'user_id': user.id,
            'period_days': days,
            'total_campaigns': len(metrics_data),
            'campaigns': metrics_data
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommendations(self, request):
        """
        Return personalized campaign recommendations for the authenticated user.
        """
        from .recommendations import CampaignRecommendationEngine

        limit = int(request.query_params.get('limit', 10))
        data = CampaignRecommendationEngine.get_recommended_campaigns_for_user(request.user, limit=limit)
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='trending_by_category')
    def trending_by_category(self, request):
        """
        Return trending campaigns for a specific category/tag. Public endpoint.

        Query params:
        - category: required category/tag name
        - limit: number of campaigns to return (default 5)
        """
        from .recommendations import CampaignRecommendationEngine

        category = request.query_params.get('category')
        if not category:
            return Response({'error': 'category is required'}, status=400)

        limit = int(request.query_params.get('limit', 5))
        data = CampaignRecommendationEngine.get_trending_campaigns_by_category(category, limit=limit)
        return Response(data)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny], url_path='similar')
    def similar(self, request, pk=None):
        """
        Return campaigns similar to the given campaign id. Public endpoint.

        Query params:
        - limit: number of similar campaigns to return (default 5)
        """
        from .recommendations import CampaignRecommendationEngine

        limit = int(request.query_params.get('limit', 5))
        data = CampaignRecommendationEngine.get_similar_campaigns(pk, limit=limit)
        if isinstance(data, dict) and data.get('error'):
            return Response(data, status=404)
        return Response(data)

