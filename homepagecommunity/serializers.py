from rest_framework import serializers
from .models import (
    HeroSection, AboutCommunityMission, CommunityFeature,
    SubscriptionTier, SubscriptionBenefit, Testimonial,
    FinalCTA, CommunityMetrics
)


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = [
            'id', 'title_line_1', 'title_line_2', 'title_line_3',
            'subtitle', 'individual_price', 'individual_period',
            'facilitator_price', 'facilitator_period',
            'corporate_price', 'corporate_period'
        ]


class AboutCommunityMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutCommunityMission
        fields = ['id', 'mission_label', 'mission_title', 'mission_description']


class CommunityFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityFeature
        fields = ['id', 'title', 'description', 'feature_type', 'order']


class SubscriptionBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionBenefit
        fields = ['id', 'title', 'description', 'icon_name', 'order']


class SubscriptionTierSerializer(serializers.ModelSerializer):
    benefits = SubscriptionBenefitSerializer(many=True, read_only=True)
    
    class Meta:
        model = SubscriptionTier
        fields = [
            'id', 'tier_type', 'title', 'subtitle', 'price', 'period',
            'description', 'label_color', 'bg_color', 'button_color', 'benefits'
        ]


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'name', 'title', 'quote', 'image', 'display_order']


class FinalCTASerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalCTA
        fields = [
            'id', 'title_part_1', 'title_teach', 'title_connect',
            'title_empower', 'subtitle'
        ]


class CommunityMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMetrics
        fields = [
            'id', 'total_members', 'active_groups', 'total_posts',
            'total_facilitators', 'total_courses', 'total_enrollments'
        ]


class CommunityPageDataSerializer(serializers.Serializer):
    """Complete community page data"""
    hero = HeroSectionSerializer()
    about = AboutCommunityMissionSerializer()
    features = CommunityFeatureSerializer(many=True)
    subscription_tiers = SubscriptionTierSerializer(many=True)
    testimonials = TestimonialSerializer(many=True)
    final_cta = FinalCTASerializer()
    metrics = CommunityMetricsSerializer()
