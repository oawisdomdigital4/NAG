from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    SponsorCampaignViewSet,
    WithdrawalRequestViewSet,
    WalletTopUpViewSet,
    SponsorAnalyticsView,
)
from .dashboard_analytics import DashboardAnalyticsView, FacilitatorAnalyticsView
from .views import record_profile_visit, ProfileMetricsView, record_post_view, user_engagement_analytics
from .extended_views import OpportunityViewSet, OpportunityStats

router = DefaultRouter()
router.register(r'sponsor-campaigns', SponsorCampaignViewSet, basename='sponsor-campaign')
router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawal')
router.register(r'wallet-topups', WalletTopUpViewSet, basename='wallet-topup')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
urlpatterns = [
    # Specific paths must come BEFORE the router to avoid conflicts
    path('opportunities/stats/', OpportunityStats.as_view(), name='opportunities-stats'),
    path('', include(router.urls)),
    path('analytics/dashboard/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('analytics/facilitator/', FacilitatorAnalyticsView.as_view(), name='facilitator-analytics'),
    path('sponsored/analytics/', SponsorAnalyticsView.as_view(), name='sponsor-analytics'),
    path('analytics/profile_metrics/', ProfileMetricsView.as_view(), name='profile-metrics'),
    path('analytics/record_profile_visit/', record_profile_visit, name='record-profile-visit'),
    path('analytics/record_post_view/', record_post_view, name='record-post-view'),
    path('analytics/user_engagement/', user_engagement_analytics, name='user-engagement-analytics'),
]