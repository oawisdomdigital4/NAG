from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count
from .models import (
    HeroSection, AboutCommunityMission, CommunityFeature,
    SubscriptionTier, SubscriptionBenefit, Testimonial,
    FinalCTA, CommunityMetrics
)
from .serializers import (
    HeroSectionSerializer, AboutCommunityMissionSerializer,
    CommunityFeatureSerializer, SubscriptionTierSerializer,
    SubscriptionBenefitSerializer, TestimonialSerializer,
    FinalCTASerializer, CommunityMetricsSerializer,
    CommunityPageDataSerializer
)


class HeroSectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HeroSection.objects.all()
    serializer_class = HeroSectionSerializer
    permission_classes = [AllowAny]


class AboutCommunityMissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AboutCommunityMission.objects.all()
    serializer_class = AboutCommunityMissionSerializer
    permission_classes = [AllowAny]


class CommunityFeatureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommunityFeature.objects.all().order_by('order')
    serializer_class = CommunityFeatureSerializer
    permission_classes = [AllowAny]


class SubscriptionTierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionTier.objects.all().prefetch_related('benefits')
    serializer_class = SubscriptionTierSerializer
    permission_classes = [AllowAny]


class SubscriptionBenefitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionBenefit.objects.all().order_by('tier', 'order')
    serializer_class = SubscriptionBenefitSerializer
    permission_classes = [AllowAny]


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.filter(is_active=True).order_by('display_order')
    serializer_class = TestimonialSerializer
    permission_classes = [AllowAny]


class FinalCTAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FinalCTA.objects.all()
    serializer_class = FinalCTASerializer
    permission_classes = [AllowAny]


class CommunityMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommunityMetrics.objects.all()
    serializer_class = CommunityMetricsSerializer
    permission_classes = [AllowAny]


class CommunityPageViewSet(viewsets.ViewSet):
    """Complete community page data endpoint"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def all_data(self, request):
        """Get all community page data"""
        try:
            hero = HeroSection.objects.first() or HeroSection()
            about = AboutCommunityMission.objects.first() or AboutCommunityMission()
            features = CommunityFeature.objects.all().order_by('order')
            subscription_tiers = SubscriptionTier.objects.all().prefetch_related('benefits')
            testimonials = Testimonial.objects.filter(is_active=True).order_by('display_order')
            final_cta = FinalCTA.objects.first() or FinalCTA()
            metrics = CommunityMetrics.objects.first() or CommunityMetrics()
            
            data = {
                'hero': hero,
                'about': about,
                'features': features,
                'subscription_tiers': subscription_tiers,
                'testimonials': testimonials,
                'final_cta': final_cta,
                'metrics': metrics
            }
            
            serializer = CommunityPageDataSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
