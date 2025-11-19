from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import( CampaignAnalytics,
                    PromotionMetrics,
                    FacilitatorEarning,
                    EngagementLog,
                    SponsorCampaign,
)

class AnalyticsService:
    @staticmethod
    def get_campaign_performance(user, days=30):
        """Get aggregated campaign performance metrics for a user"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all sponsored campaigns
        sponsor_campaigns = SponsorCampaign.objects.filter(
            sponsor=user,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        # Aggregate metrics for regular campaigns (using PromotionMetrics)
        regular_metrics = PromotionMetrics.objects.filter(
            campaign__isnull=False
        ).aggregate(
            total_impressions=Sum('impressions'),
            total_clicks=Sum('clicks'),
            total_conversions=Sum('conversions'),
            total_revenue=Sum('revenue'),
            total_spend=Sum('spend'),
            avg_engagement_rate=Avg('engagement_rate'),
            avg_conversion_rate=Avg('conversion_rate'),
            avg_roi=Avg('roi')
        )
        
        # Aggregate metrics for sponsored campaigns
        # SponsorCampaign is a separate model (linked to Post), so aggregate directly
        # from SponsorCampaign fields instead of attempting to filter CampaignAnalytics
        sponsor_metrics = sponsor_campaigns.aggregate(
            total_impressions=Sum('impression_count'),
            total_clicks=Sum('click_count'),
            total_spend=Sum('budget')
        )
        # Provide a sensible default for conversions (model doesn't track conversions)
        sponsor_metrics['total_conversions'] = 0
        
        # Normalize aggregates: convert None -> 0 and Decimal -> float for JSON/frontend friendliness
        def normalize_agg(agg: dict):
            out = {}
            for k, v in (agg or {}).items():
                if v is None:
                    out[k] = 0
                elif isinstance(v, Decimal):
                    out[k] = float(v)
                else:
                    # ensure numeric-like strings/values remain as-is
                    out[k] = v
            return out

        return {
            'regular_campaigns': normalize_agg(regular_metrics),
            'sponsored_campaigns': normalize_agg(sponsor_metrics),
            'period_days': days,
            'trends': AnalyticsService._get_campaign_trends(user, days)
        }

    @staticmethod
    def _get_campaign_trends(user, days=30):
        """Return a simple timeseries of impressions per day across all campaigns
        for the provided user over the given date range. This helps populate
        charts in the frontend.
        """
        from django.db.models import Sum
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        qs = CampaignAnalytics.objects.filter(
            campaign__sponsor=user,
            date__range=(start_date.date(), end_date.date())
        ).values('date').annotate(views=Sum('impressions')).order_by('date')

        trends = []
        for item in qs:
            period = item['date'].strftime('%Y-%m-%d')
            trends.append({
                'period': period,
                'metrics': {
                    'views': int(item['views'] or 0)
                }
            })
        return trends
    
    @staticmethod
    def get_earnings_summary(facilitator, days=30):
        """Get earnings summary for a facilitator"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        earnings = FacilitatorEarning.objects.filter(
            facilitator=facilitator,
            earned_at__range=(start_date, end_date)
        )
        
        summary = earnings.aggregate(
            total_earnings=Sum('amount'),
            paid_earnings=Sum('amount', filter=Q(is_paid=True)),
            pending_earnings=Sum('amount', filter=Q(is_paid=False))
        )
        
        # Add earnings by source
        earnings_by_source = earnings.values('source').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        summary['earnings_by_source'] = list(earnings_by_source)
        summary['period_days'] = days
        
        return summary
    
    @staticmethod
    def get_engagement_patterns(user, days=30):
        """Analyze engagement patterns for user's content"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get hourly engagement distribution (include community engagement logs)
        try:
            from community.engagement import CommunityEngagementLog
            community_qs = CommunityEngagementLog.objects.filter(
                post__author=user,
                created_at__range=(start_date, end_date)
            )
        except Exception:
            community_qs = None

        hourly_pattern = EngagementLog.objects.filter(
            post__author=user,
            created_at__range=(start_date, end_date)
        ).annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        # Merge hourly from community logs if available
        if community_qs is not None:
            comm_hours = community_qs.annotate(hour=ExtractHour('created_at')).values('hour').annotate(count=Count('id')).order_by('hour')
            # fold community counts into hourly_pattern dict by hour
            hours_map = {h['hour']: h['count'] for h in hourly_pattern}
            for h in comm_hours:
                hours_map[h['hour']] = hours_map.get(h['hour'], 0) + h['count']
            hourly_pattern = [{'hour': k, 'count': v} for k, v in sorted(hours_map.items())]
        
        # Get engagement by type (merge promotions EngagementLog and community action types)
        engagement_types_qs = EngagementLog.objects.filter(
            post__author=user,
            created_at__range=(start_date, end_date)
        ).values('action_type').annotate(count=Count('id')).order_by('-count')

        engagement_types = {item['action_type']: item['count'] for item in engagement_types_qs}
        if community_qs is not None:
            comm_types = community_qs.values('action_type').annotate(count=Count('id'))
            for ct in comm_types:
                engagement_types[ct['action_type']] = engagement_types.get(ct['action_type'], 0) + ct['count']
            # convert to list of dicts ordered by count
            engagement_types = sorted([{'action_type': k, 'count': v} for k, v in engagement_types.items()], key=lambda x: -x['count'])
        else:
            engagement_types = list(engagement_types_qs)

        # Get engagement by country (if available) - merge both sources
        engagement_by_country_prom = EngagementLog.objects.filter(
            post__author=user,
            created_at__range=(start_date, end_date)
        ).values('user__profile__country').annotate(count=Count('id')).order_by('-count')
        if community_qs is not None:
            engagement_by_country_comm = community_qs.values('user__profile__country').annotate(count=Count('id')).order_by('-count')
            country_map = {}
            for it in engagement_by_country_prom:
                country_map[it.get('user__profile__country')] = country_map.get(it.get('user__profile__country'), 0) + it.get('count', 0)
            for it in engagement_by_country_comm:
                country_map[it.get('user__profile__country')] = country_map.get(it.get('user__profile__country'), 0) + it.get('count', 0)
            engagement_by_country = [{'user__profile__country': k, 'count': v} for k, v in sorted(country_map.items(), key=lambda x: -x[1])]
        else:
            engagement_by_country = list(engagement_by_country_prom)
        
        return {
            'hourly_pattern': list(hourly_pattern),
            'engagement_types': list(engagement_types),
            'engagement_by_country': list(engagement_by_country),
            'period_days': days
        }
    
    @staticmethod
    def get_roi_metrics(user, days=30):
        """Calculate ROI metrics for campaigns"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics for campaigns in the time range
        # PromotionMetrics stores daily values in `date` field, so filter by date range
        metrics = PromotionMetrics.objects.filter(
            campaign__isnull=False,
            date__range=(start_date.date(), end_date.date())
        )
        
        overall_roi = metrics.aggregate(
            total_revenue=Sum('revenue'),
            total_spend=Sum('spend'),
            avg_roi=Avg('roi'),
            total_conversions=Sum('conversions')
        )
        
        # Calculate cost per conversion
        if overall_roi['total_conversions'] and overall_roi['total_spend']:
            overall_roi['cost_per_conversion'] = (
                overall_roi['total_spend'] / overall_roi['total_conversions']
            )
        else:
            overall_roi['cost_per_conversion'] = Decimal('0.00')
        
        # Get ROI by campaign
        campaign_roi = metrics.values(
            'campaign__title'
        ).annotate(
            revenue=Sum('revenue'),
            spend=Sum('spend'),
            roi=Avg('roi'),
            conversions=Sum('conversions')
        ).order_by('-roi')
        
        return {
            'overall_metrics': overall_roi,
            'campaign_metrics': list(campaign_roi),
            'period_days': days
        }
    
    @staticmethod
    def get_audience_insights(user, days=30):
        """Get detailed audience insights"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        base_query = EngagementLog.objects.filter(
            post__author=user,
            created_at__range=(start_date, end_date)
        )
        # also include community engagement logs when possible
        try:
            from community.engagement import CommunityEngagementLog
            community_base = CommunityEngagementLog.objects.filter(post__author=user, created_at__range=(start_date, end_date))
        except Exception:
            community_base = None
        
        # Audience by role
        audience_roles = base_query.values(
            'user__role'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Audience by industry
        audience_industries = base_query.values(
            'user__profile__industry'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Engagement by content (group by post id and title because Post doesn't have `content_type`)
        content_engagement_map = {}
        # promotions EngagementLog counts
        prom_content = base_query.values('post__id', 'post__title').annotate(
            views=Count('id', filter=Q(action_type='view')),
            likes=Count('id', filter=Q(action_type='like')),
            comments=Count('id', filter=Q(action_type='comment')),
            shares=Count('id', filter=Q(action_type='share'))
        )
        for c in prom_content:
            pid = c.get('post__id')
            content_engagement_map[pid] = {
                'post__id': pid,
                'post__title': c.get('post__title'),
                'views': c.get('views', 0),
                'likes': c.get('likes', 0),
                'comments': c.get('comments', 0),
                'shares': c.get('shares', 0),
                'clicks': 0
            }

        # merge community counts
        if community_base is not None:
            comm_content = community_base.values('post__id', 'post__title', 'action_type').annotate(count=Count('id'))
            for c in comm_content:
                pid = c.get('post__id')
                if pid not in content_engagement_map:
                    content_engagement_map[pid] = {
                        'post__id': pid,
                        'post__title': c.get('post__title'),
                        'views': 0,
                        'likes': 0,
                        'comments': 0,
                        'shares': 0,
                        'clicks': 0
                    }
                at = c.get('action_type')
                cnt = c.get('count', 0)
                if at in ('view_post', 'view'):
                    content_engagement_map[pid]['views'] = content_engagement_map[pid].get('views', 0) + cnt
                elif at in ('like_post', 'like'):
                    content_engagement_map[pid]['likes'] = content_engagement_map[pid].get('likes', 0) + cnt
                elif at in ('comment_post', 'reply_comment', 'comment'):
                    content_engagement_map[pid]['comments'] = content_engagement_map[pid].get('comments', 0) + cnt
                elif at in ('share_post', 'share'):
                    content_engagement_map[pid]['shares'] = content_engagement_map[pid].get('shares', 0) + cnt
                elif at == 'click_action':
                    content_engagement_map[pid]['clicks'] = content_engagement_map[pid].get('clicks', 0) + cnt

        content_engagement = sorted(list(content_engagement_map.values()), key=lambda x: -x.get('views', 0))
        
        return {
            'audience_roles': list(audience_roles),
            'audience_industries': list(audience_industries),
            'content_engagement': list(content_engagement),
            'period_days': days
        }

    @staticmethod
    def get_profile_metrics(user, days=30):
        """Return high-level profile metrics for a user: total views, profile visits,
        engagement rate (engagement events per view), and total connections.
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Total content views (views on posts authored by user)
        total_views = EngagementLog.objects.filter(
            post__author=user,
            action_type='view',
            created_at__range=(start_date, end_date)
        ).count()
        # include community view_post counts
        try:
            from community.engagement import CommunityEngagementLog
            total_views += CommunityEngagementLog.objects.filter(post__author=user, action_type='view_post', created_at__range=(start_date, end_date)).count()
        except Exception:
            pass

        # Profile visits (explicit profile_view events recorded by frontend)
        profile_visits_qs = EngagementLog.objects.filter(
            action_type='profile_view',
            created_at__range=(start_date, end_date)
        )
        # If metadata includes a target_user_id, filter it; otherwise we assume metadata.target_user
        try:
            profile_visits = profile_visits_qs.filter(metadata__target_user_id=str(user.id)).count()
        except Exception:
            profile_visits = profile_visits_qs.count()

        # Engagement events: count interactions (likes, comments, shares, bookmarks)
        # These are meaningful interactions on posts authored by the user
        # Engagement events: include both promotions and community action types
        total_engagement_events = EngagementLog.objects.filter(
            post__author=user,
            action_type__in=['like', 'comment', 'share', 'bookmark'],
            created_at__range=(start_date, end_date)
        ).count()
        try:
            from community.engagement import CommunityEngagementLog
            total_engagement_events += CommunityEngagementLog.objects.filter(
                post__author=user,
                action_type__in=['like_post', 'comment_post', 'reply_comment', 'share_post', 'bookmark_post'],
                created_at__range=(start_date, end_date)
            ).count()
            # include clicks as engagement events optionally if desired
        except Exception:
            pass

        # Compute engagement rate as engagement events per view (percentage)
        # If there are views, calculate engagement rate; otherwise default to 0.0
        if total_views > 0:
            engagement_rate = round((total_engagement_events / total_views) * 100, 2)
        else:
            engagement_rate = 0.0

        # Connections: fetch from the community collaborations endpoint
        # Same as /dashboard/corporate/connections - counts accepted/active/completed collaborations
        connections_count = 0
        try:
            from community.models import CollaborationRequest
            # Count accepted, active, or completed collaborations involving this user
            connections_count = CollaborationRequest.objects.filter(
                Q(requester=user) | Q(recipient=user),
                status__in=['accepted', 'active', 'completed']
            ).count()
        except Exception:
            connections_count = 0

        return {
            'total_views': total_views,
            'profile_visits': profile_visits,
            'engagement_rate': engagement_rate,
            'connections': connections_count,
            'period_days': days
        }

    @staticmethod
    def get_user_post_engagement(user, days=30):
        """Return per-post engagement metrics (views, likes, comments, shares, bookmarks) for all posts authored by the user."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get all posts authored by the user
        from community.models import Post
        posts = Post.objects.filter(author=user).values_list('id', 'title', 'content')

        engagement_data = []
        for post_id, post_title, post_content in posts:
            # Get engagement metrics for this post
            engagement_qs = EngagementLog.objects.filter(
                post_id=post_id,
                created_at__range=(start_date, end_date)
            )

            post_metrics = engagement_qs.values('action_type').annotate(
                count=Count('id')
            )

            # Organize counts by action type
            metrics_by_type = {item['action_type']: item['count'] for item in post_metrics}

            # Merge community engagement counts for this post
            try:
                from community.engagement import CommunityEngagementLog
                comm_metrics = CommunityEngagementLog.objects.filter(post_id=post_id, created_at__range=(start_date, end_date)).values('action_type').annotate(count=Count('id'))
                for cm in comm_metrics:
                    at = cm['action_type']
                    cnt = cm['count']
                    if at in ('view_post', 'view'):
                        metrics_by_type['view'] = metrics_by_type.get('view', 0) + cnt
                    elif at in ('like_post', 'like'):
                        metrics_by_type['like'] = metrics_by_type.get('like', 0) + cnt
                    elif at in ('comment_post', 'reply_comment', 'comment'):
                        metrics_by_type['comment'] = metrics_by_type.get('comment', 0) + cnt
                    elif at in ('share_post', 'share'):
                        metrics_by_type['share'] = metrics_by_type.get('share', 0) + cnt
                    elif at in ('bookmark_post', 'bookmark'):
                        metrics_by_type['bookmark'] = metrics_by_type.get('bookmark', 0) + cnt
                    elif at == 'click_action':
                        metrics_by_type['click'] = metrics_by_type.get('click', 0) + cnt
            except Exception:
                pass

            engagement_data.append({
                'post_id': post_id,
                'post_title': post_title or post_content[:100],  # Use title or snippet of content
                'views': metrics_by_type.get('view', 0),
                'likes': metrics_by_type.get('like', 0),
                'comments': metrics_by_type.get('comment', 0),
                'shares': metrics_by_type.get('share', 0),
                'bookmarks': metrics_by_type.get('bookmark', 0),
                'clicks': metrics_by_type.get('click', 0),
                'total_engagement': sum(metrics_by_type.values())
            })

        # Sort by total engagement (descending)
        engagement_data.sort(key=lambda x: x['total_engagement'], reverse=True)
        return engagement_data

    @staticmethod
    def get_user_account_insights(user, days=30):
        """Get comprehensive user account insights including posts, engagement, content stats.
        This is different from profile_metrics - this shows user activity and content creation stats.
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # User's posts and content creation
        from community.models import Post, Comment
        
        posts_created = Post.objects.filter(
            author=user,
            created_at__range=(start_date, end_date)
        ).count()
        
        comments_created = Comment.objects.filter(
            author=user,
            created_at__range=(start_date, end_date)
        ).count()
        
        # Total engagement received (on user's content)
        total_likes_received = EngagementLog.objects.filter(
            post__author=user,
            action_type='like',
            created_at__range=(start_date, end_date)
        ).count()
        
        try:
            from community.engagement import CommunityEngagementLog
            total_likes_received += CommunityEngagementLog.objects.filter(
                post__author=user,
                action_type='like_post',
                created_at__range=(start_date, end_date)
            ).count()
        except Exception:
            pass
        
        total_comments_received = Comment.objects.filter(
            post__author=user,
            created_at__range=(start_date, end_date)
        ).count()
        
        total_shares_received = EngagementLog.objects.filter(
            post__author=user,
            action_type='share',
            created_at__range=(start_date, end_date)
        ).count()
        
        try:
            from community.engagement import CommunityEngagementLog
            total_shares_received += CommunityEngagementLog.objects.filter(
                post__author=user,
                action_type='share_post',
                created_at__range=(start_date, end_date)
            ).count()
        except Exception:
            pass
        
        # Engagement given (user's activity)
        likes_given = EngagementLog.objects.filter(
            user=user,
            action_type='like',
            created_at__range=(start_date, end_date)
        ).count()
        
        try:
            from community.engagement import CommunityEngagementLog
            likes_given += CommunityEngagementLog.objects.filter(
                user=user,
                action_type='like_post',
                created_at__range=(start_date, end_date)
            ).count()
        except Exception:
            pass
        
        comments_given = Comment.objects.filter(
            author=user,
            created_at__range=(start_date, end_date)
        ).count()
        
        # Average engagement per post
        avg_engagement_per_post = 0
        if posts_created > 0:
            total_engagement_on_posts = total_likes_received + total_comments_received + total_shares_received
            avg_engagement_per_post = round(total_engagement_on_posts / posts_created, 2)
        
        # Get top performing posts
        top_posts = []
        try:
            from community.models import Post
            posts_qs = Post.objects.filter(author=user).values('id', 'title', 'created_at')
            
            for post in posts_qs[:10]:
                # Get engagement for this post
                post_likes = EngagementLog.objects.filter(
                    post_id=post['id'],
                    action_type='like',
                    created_at__range=(start_date, end_date)
                ).count()
                
                try:
                    from community.engagement import CommunityEngagementLog
                    post_likes += CommunityEngagementLog.objects.filter(
                        post_id=post['id'],
                        action_type='like_post',
                        created_at__range=(start_date, end_date)
                    ).count()
                except Exception:
                    pass
                
                post_comments = Comment.objects.filter(
                    post_id=post['id'],
                    created_at__range=(start_date, end_date)
                ).count()
                
                post_shares = EngagementLog.objects.filter(
                    post_id=post['id'],
                    action_type='share',
                    created_at__range=(start_date, end_date)
                ).count()
                
                total_post_engagement = post_likes + post_comments + post_shares
                
                if total_post_engagement > 0:
                    top_posts.append({
                        'post_id': post['id'],
                        'title': post['title'][:100] if post['title'] else 'Untitled',
                        'likes': post_likes,
                        'comments': post_comments,
                        'shares': post_shares,
                        'total_engagement': total_post_engagement,
                        'created_at': post['created_at'].strftime('%Y-%m-%d')
                    })
        except Exception:
            pass
        
        # Sort by engagement
        top_posts.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return {
            'user_activity': {
                'posts_created': posts_created,
                'comments_created': comments_created,
                'likes_given': likes_given,
                'comments_given': comments_given,
            },
            'engagement_received': {
                'likes': total_likes_received,
                'comments': total_comments_received,
                'shares': total_shares_received,
                'total': total_likes_received + total_comments_received + total_shares_received,
            },
            'engagement_metrics': {
                'avg_engagement_per_post': avg_engagement_per_post,
                'engagement_per_day': round((total_likes_received + total_comments_received + total_shares_received) / max(days, 1), 2),
            },
            'top_posts': top_posts[:5],
            'period_days': days
        }
