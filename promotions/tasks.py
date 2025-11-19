from django.utils import timezone
from django.core.cache import cache
from django.db.models import F, Q, Count, Sum
from .models import SponsorCampaign, CampaignAnalytics, EngagementLog
from datetime import timedelta


class CampaignMetricsService:
    """Service for real-time campaign metrics polling and updates"""
    
    CACHE_TTL = 300  # 5 minutes cache
    
    @staticmethod
    def get_campaign_metrics(campaign_id):
        """
        Get current metrics for a specific campaign.
        Includes live counts and calculated metrics.
        """
        try:
            campaign = SponsorCampaign.objects.get(id=campaign_id)
            
            return {
                'id': campaign.id,
                'title': campaign.title,
                'status': campaign.status,
                'impressions': campaign.impression_count,
                'clicks': campaign.click_count,
                'engagement_rate': round(campaign.engagement_rate, 2),
                'cost_per_click': round(campaign.get_cost_per_click(), 4),
                'cost_per_impression': round(campaign.get_cost_per_impression(), 6),
                'budget': float(campaign.budget),
                'is_active': campaign.is_active(),
                'performance_metrics': campaign.get_performance_metrics(),
                'updated_at': campaign.updated_at.isoformat(),
            }
        except SponsorCampaign.DoesNotExist:
            return None
    
    @staticmethod
    def get_active_campaigns_metrics():
        """
        Get metrics for all active campaigns.
        Uses cache to reduce database queries.
        """
        cache_key = 'active_campaigns_metrics'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).values(
            'id', 'title', 'status', 'impression_count', 'click_count',
            'engagement_rate', 'budget', 'priority_level', 'updated_at'
        ).order_by('-priority_level', '-impression_count')
        
        data = {
            'timestamp': now.isoformat(),
            'total_campaigns': len(campaigns),
            'campaigns': list(campaigns),
        }
        
        cache.set(cache_key, data, timeout=CampaignMetricsService.CACHE_TTL)
        return data
    
    @staticmethod
    def get_user_campaigns_metrics(user_id):
        """
        Get metrics for all campaigns owned by a specific user.
        """
        cache_key = f'user_campaigns_metrics:{user_id}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            sponsor_id=user_id
        ).values(
            'id', 'title', 'status', 'impression_count', 'click_count',
            'engagement_rate', 'budget', 'priority_level', 'created_at', 'updated_at'
        ).order_by('-created_at')
        
        # Aggregate stats
        stats = SponsorCampaign.objects.filter(sponsor_id=user_id).aggregate(
            total_campaigns=Count('id'),
            active_campaigns=Count('id', filter=Q(status='active')),
            total_impressions=Sum('impression_count', default=0),
            total_clicks=Sum('click_count', default=0),
            total_budget=Sum('budget', default=0),
        )
        
        data = {
            'timestamp': now.isoformat(),
            'user_id': user_id,
            'summary': {
                'total_campaigns': stats['total_campaigns'],
                'active_campaigns': stats['active_campaigns'],
                'total_impressions': stats['total_impressions'],
                'total_clicks': stats['total_clicks'],
                'total_budget': float(stats['total_budget'] or 0),
            },
            'campaigns': list(campaigns),
        }
        
        cache.set(cache_key, data, timeout=CampaignMetricsService.CACHE_TTL)
        return data
    
    @staticmethod
    def get_campaign_daily_analytics(campaign_id, days=30):
        """
        Get daily analytics for a campaign over a time period.
        """
        cache_key = f'campaign_analytics:{campaign_id}:{days}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        start_date = timezone.now().date() - timedelta(days=days)
        analytics = CampaignAnalytics.objects.filter(
            campaign_id=campaign_id,
            date__gte=start_date
        ).values(
            'date', 'impressions', 'clicks', 'conversions', 'spend'
        ).order_by('date')
        
        data = {
            'campaign_id': campaign_id,
            'period_days': days,
            'analytics': list(analytics),
        }
        
        cache.set(cache_key, data, timeout=3600)  # 1 hour cache
        return data
    
    @staticmethod
    def refresh_campaign_metrics(campaign_id):
        """
        Manually refresh metrics for a campaign.
        Clears cache to force fresh data on next poll.
        """
        try:
            campaign = SponsorCampaign.objects.get(id=campaign_id)
            
            # Recalculate engagement rate
            campaign.calculate_engagement_rate()
            
            # Clear related caches
            cache.delete(f'campaign_metrics:{campaign_id}')
            cache.delete('active_campaigns_metrics')
            cache.delete(f'user_campaigns_metrics:{campaign.sponsor_id}')
            
            return CampaignMetricsService.get_campaign_metrics(campaign_id)
        except SponsorCampaign.DoesNotExist:
            return None
    
    @staticmethod
    def get_trending_campaigns(limit=10):
        """
        Get trending campaigns sorted by engagement.
        """
        cache_key = f'trending_campaigns:{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-engagement_rate', '-click_count')[:limit].values(
            'id', 'title', 'engagement_rate', 'click_count', 'impression_count'
        )
        
        data = {
            'timestamp': now.isoformat(),
            'trending_campaigns': list(campaigns),
        }
        
        cache.set(cache_key, data, timeout=600)  # 10 minutes cache
        return data

