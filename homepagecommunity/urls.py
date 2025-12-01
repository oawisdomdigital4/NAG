from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HeroSectionViewSet, AboutCommunityMissionViewSet,
    CommunityFeatureViewSet, SubscriptionTierViewSet,
    SubscriptionBenefitViewSet, TestimonialViewSet,
    FinalCTAViewSet, CommunityMetricsViewSet,
    CommunityPageViewSet
)

router = DefaultRouter()
router.register(r'hero', HeroSectionViewSet, basename='hero')
router.register(r'about', AboutCommunityMissionViewSet, basename='about')
router.register(r'features', CommunityFeatureViewSet, basename='features')
router.register(r'subscription-tiers', SubscriptionTierViewSet, basename='subscription-tiers')
router.register(r'benefits', SubscriptionBenefitViewSet, basename='benefits')
router.register(r'testimonials', TestimonialViewSet, basename='testimonials')
router.register(r'final-cta', FinalCTAViewSet, basename='final-cta')
router.register(r'metrics', CommunityMetricsViewSet, basename='metrics')
router.register(r'page', CommunityPageViewSet, basename='page')

urlpatterns = [
    path('', include(router.urls)),
]
