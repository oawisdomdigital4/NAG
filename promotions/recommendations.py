from django.utils import timezone
from django.db.models import Q, F, Count
from django.core.cache import cache
from .models import SponsorCampaign
from community.models import Post


class CampaignRecommendationEngine:
    """Service for intelligent campaign recommendations"""
    
    @staticmethod
    def get_recommended_campaigns_for_user(user, limit=10):
        """
        Get personalized campaign recommendations based on user profile.
        """
        cache_key = f'recommended_campaigns:{user.id}:{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        now = timezone.now()
        recommendations = []
        
        try:
            # Get user's interests from profile
            user_interests = getattr(user.profile, 'interests', []) if hasattr(user, 'profile') else []
            user_role = getattr(user.community_profile, 'role', 'individual') if hasattr(user, 'community_profile') else 'individual'
            
            # Query campaigns with matching tags
            campaigns = SponsorCampaign.objects.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            ).select_related('sponsored_post', 'sponsor')
            
            # Score campaigns based on relevance
            scored_campaigns = []
            for campaign in campaigns:
                score = 0
                
                # Tag matching
                post_tags = getattr(campaign.sponsored_post, 'industry_tags', []) if campaign.sponsored_post else []
                matching_tags = set(post_tags) & set(user_interests)
                score += len(matching_tags) * 10
                
                # Role-based preferences
                if user_role == 'facilitator':
                    # Facilitators prefer educational content
                    if 'education' in post_tags or 'learning' in post_tags:
                        score += 5
                
                if user_role == 'corporate':
                    # Corporates prefer partnership opportunities
                    if 'partnership' in post_tags or 'collaboration' in post_tags:
                        score += 5
                
                # Engagement boost
                score += campaign.engagement_rate / 10
                
                # Priority boost
                score += campaign.priority_level * 2
                
                scored_campaigns.append({
                    'campaign_id': campaign.id,
                    'title': campaign.title,
                    'score': score,
                    'relevance': len(matching_tags),
                })
            
            # Sort by score and take top N
            scored_campaigns.sort(key=lambda x: x['score'], reverse=True)
            recommendations = scored_campaigns[:limit]
            
        except Exception:
            # Fallback: just return top campaigns by engagement
            top_campaigns = SponsorCampaign.objects.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            ).order_by('-engagement_rate', '-impression_count')[:limit].values(
                'id', 'title'
            )
            recommendations = [
                {'campaign_id': c['id'], 'title': c['title'], 'score': 0, 'relevance': 0}
                for c in top_campaigns
            ]
        
        data = {
            'timestamp': now.isoformat(),
            'user_id': user.id,
            'recommendations': recommendations,
            'count': len(recommendations),
        }
        
        cache.set(cache_key, data, timeout=3600)  # 1 hour cache
        return data
    
    @staticmethod
    def get_trending_campaigns_by_category(category, limit=5):
        """
        Get trending campaigns in a specific category.
        """
        cache_key = f'trending_by_category:{category}:{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        now = timezone.now()
        
        # Find campaigns with matching tags/categories
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now,
            sponsored_post__industry_tags__contains=[category]
        ).select_related('sponsored_post', 'sponsor').order_by(
            '-engagement_rate', '-click_count'
        )[:limit]
        
        data = {
            'timestamp': now.isoformat(),
            'category': category,
            'campaigns': [
                {
                    'id': c.id,
                    'title': c.title,
                    'engagement_rate': c.engagement_rate,
                    'impressions': c.impression_count,
                    'clicks': c.click_count,
                }
                for c in campaigns
            ],
            'count': campaigns.count(),
        }
        
        cache.set(cache_key, data, timeout=1800)  # 30 minutes
        return data
    
    @staticmethod
    def get_similar_campaigns(campaign_id, limit=5):
        """
        Get campaigns similar to a given campaign.
        """
        cache_key = f'similar_campaigns:{campaign_id}:{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        now = timezone.now()
        
        try:
            campaign = SponsorCampaign.objects.get(id=campaign_id)
            campaign_tags = getattr(campaign.sponsored_post, 'industry_tags', []) if campaign.sponsored_post else []
            
            # Find campaigns with overlapping tags
            similar = SponsorCampaign.objects.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now
            ).exclude(id=campaign_id).select_related('sponsored_post', 'sponsor')
            
            # Score by tag overlap
            scored = []
            for c in similar:
                c_tags = getattr(c.sponsored_post, 'industry_tags', []) if c.sponsored_post else []
                overlap = len(set(campaign_tags) & set(c_tags))
                
                if overlap > 0:
                    scored.append({
                        'campaign': c,
                        'overlap': overlap,
                    })
            
            # Sort by overlap and engagement
            scored.sort(key=lambda x: (x['overlap'], x['campaign'].engagement_rate), reverse=True)
            
            data = {
                'timestamp': now.isoformat(),
                'source_campaign_id': campaign_id,
                'similar_campaigns': [
                    {
                        'id': s['campaign'].id,
                        'title': s['campaign'].title,
                        'overlap_score': s['overlap'],
                        'engagement_rate': s['campaign'].engagement_rate,
                    }
                    for s in scored[:limit]
                ],
                'count': len(scored[:limit]),
            }
        except SponsorCampaign.DoesNotExist:
            data = {
                'error': 'Campaign not found',
                'count': 0,
                'similar_campaigns': []
            }
        
        cache.set(cache_key, data, timeout=1800)  # 30 minutes
        return data
    
    @staticmethod
    def refresh_recommendations(user_id):
        """Clear cached recommendations for a user"""
        for limit in [5, 10, 20]:
            cache.delete(f'recommended_campaigns:{user_id}:{limit}')
        
        return {'status': 'success', 'caches_cleared': 3}
