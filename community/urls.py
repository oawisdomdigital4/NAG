from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
	GroupViewSet,
	GroupMembershipViewSet,
	PostViewSet,
	CommentViewSet,
    CommunitySectionViewSet,
	CTABannerViewSet,
	UserEngagementScoreViewSet,
	SubscriptionTierViewSet,
	SponsoredPostViewSet,
	TrendingTopicViewSet,
	CorporateOpportunityViewSet,
	OpportunityApplicationViewSet,
	CollaborationRequestViewSet,
	CorporateConnectionViewSet,
	PlatformAnalyticsViewSet,
	CorporatePartnerViewSet,
	CorporateMessageViewSet,
)
from .engagement_views import EngagementAnalyticsViewSet

router = DefaultRouter()
router.register(r'community-section', CommunitySectionViewSet, basename='community-section')
router.register(r'cta-banner', CTABannerViewSet, basename='cta-banner')
router.register(r'groups', GroupViewSet)
router.register(r'group-memberships', GroupMembershipViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'engagement-scores', UserEngagementScoreViewSet, basename='engagement-score')
router.register(r'subscription-tiers', SubscriptionTierViewSet, basename='subscription-tier')
router.register(r'sponsored-posts', SponsoredPostViewSet, basename='sponsored-post')
router.register(r'trending-topics', TrendingTopicViewSet, basename='trending-topic')
router.register(r'opportunities', CorporateOpportunityViewSet, basename='opportunity')
router.register(r'opportunity-applications', OpportunityApplicationViewSet, basename='opportunity-application')
router.register(r'collaborations', CollaborationRequestViewSet, basename='collaboration')
router.register(r'connections', CorporateConnectionViewSet, basename='corporate-connection')
router.register(r'platform-analytics', PlatformAnalyticsViewSet, basename='platform-analytics')
router.register(r'engagement/analytics', EngagementAnalyticsViewSet, basename='engagement-analytics')
router.register(r'partners', CorporatePartnerViewSet, basename='corporate-partner')
router.register(r'messages', CorporateMessageViewSet, basename='corporate-message')

urlpatterns = router.urls

from .views import community_search
from .api.link_preview import fetch_link_preview
from .api.user_activity import update_user_activity, get_user_activity, get_recent_activities

urlpatterns += [
    path('search/', community_search, name='community-search'),
    path('link-preview/', fetch_link_preview, name='link-preview'),
    path('activity/update/', update_user_activity, name='update-activity'),
    path('activity/user/<int:user_id>/', get_user_activity, name='get-user-activity'),
    path('activities/', get_recent_activities, name='get-recent-activities'),
]

# Add verification submission endpoint
from .views import CorporateVerificationSubmitView
urlpatterns += [
    path('verification/submit/', CorporateVerificationSubmitView.as_view(), name='corporate-verification-submit'),
]

# Include promotions routes so sponsor-campaigns endpoints are available under /api/community/
urlpatterns += [
	path('', include('promotions.urls')),
]
