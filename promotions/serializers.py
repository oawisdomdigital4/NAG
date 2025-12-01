from rest_framework import serializers
from django.db import models
from community.models import (
    CorporateOpportunity,
    CorporateConnection, CorporateVerification
)
from .models import (
    WithdrawalRequest, FacilitatorEarning,
    CampaignAnalytics, PromotionMetrics, SponsorCampaign, EngagementLog,
    WalletTopUp,
)


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    total_earnings = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'amount', 'status', 'requested_at',
            'processed_at', 'total_earnings', 'pending_amount',
            'bank_name', 'account_number', 'account_name', 'notes'
        ]
        read_only_fields = ('status', 'processed_at', 'created_at', 'id')
    
    def get_total_earnings(self, obj):
        return FacilitatorEarning.objects.filter(
            facilitator=obj.facilitator
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    def get_pending_amount(self, obj):
        return FacilitatorEarning.objects.filter(
            facilitator=obj.facilitator,
            is_paid=False
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def validate_amount(self, value):
        """Validate that withdrawal amount is positive and within limits"""
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be positive")
        if value < 50:
            raise serializers.ValidationError("Minimum withdrawal amount is $50")
        
        # Get the user from the request context
        request = self.context.get('request')
        if request and request.user:
            profile = getattr(request.user, 'profile', None)
            if profile:
                # Use the new available_balance field from the three-balance wallet system
                available_balance = float(profile.available_balance or 0)
                if value > available_balance:
                    raise serializers.ValidationError(
                        f"Insufficient available balance. Available: ${available_balance:.2f}"
                    )
        return value

class OpportunityListSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    company_name = serializers.CharField(source='creator.profile.company_name', read_only=True)
    application_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CorporateOpportunity
        fields = [
            'id', 'title', 'opportunity_type',
            'location', 'deadline', 'status',
            'creator', 'creator_name', 'company_name', 'application_count',
            'description', 'remote_friendly', 'salary_min', 'salary_max',
            'salary_currency', 'created_at', 'requirements', 'start_date'
        ]
    
    def get_creator(self, obj):
        return obj.creator.id if obj.creator else None
    
    def get_application_count(self, obj):
        return obj.application_count

class ConnectionListSerializer(serializers.ModelSerializer):
    partner_details = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = CorporateConnection
        fields = [
            'id', 'sender', 'receiver',
            'status', 'connected_at',
            'partner_details', 'recent_activity'
        ]
    
    def get_partner_details(self, obj):
        partner = obj.receiver if obj.sender == self.context['request'].user else obj.sender
        try:
            verification = CorporateVerification.objects.get(user=partner)
            return {
                'company_name': verification.company_name,
                'industry': verification.industry,
                'is_verified': verification.status == 'approved',
                'profile': {
                    'full_name': partner.profile.full_name if hasattr(partner, 'profile') else None,
                    'avatar': partner.profile.avatar.url if hasattr(partner, 'profile') and partner.profile.avatar else None
                }
            }
        except CorporateVerification.DoesNotExist:
            return None
    
    def get_recent_activity(self, obj):
        # This would need to be implemented based on your activity tracking system
        return None  # Placeholder
    

class EngagementLogSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()

    class Meta:
        model = EngagementLog
        fields = ['id', 'user', 'user_detail', 'action_type', 'post', 'comment', 'group', 'metadata', 'ip_address', 'user_agent', 'created_at']

    def get_user_detail(self, obj):
        try:
            u = obj.user
            if not u:
                return None
            return {'id': u.id, 'username': getattr(u, 'username', None), 'email': getattr(u, 'email', None)}
        except Exception:
            return None



class SummitStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'icon', 'label', 'value', 'order']


class SummitHeroSerializer(serializers.ModelSerializer):
    # nested stats provided via related_name 'stats'
    stats = SummitStatSerializer(many=True, read_only=True)

    class Meta:
        model = None  # set at runtime if available
        fields = [
            'id', 'title_main', 'title_highlight', 'date_text', 'location_text',
            'subtitle', 'strapline', 'cta_register_label', 'cta_register_url', 'cta_brochure_label', 'cta_brochure_url', 'stats',
            'background_image', 'is_published', 'created_at'
        ]


class SponsorCampaignSerializer(serializers.ModelSerializer):
    sponsor_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()
    cost_per_click = serializers.SerializerMethodField()
    cost_per_impression = serializers.SerializerMethodField()

    class Meta:
        model = SponsorCampaign
        fields = [
            'id', 'title', 'description', 'sponsor', 'sponsor_name', 'sponsored_post',
            'start_date', 'end_date', 'status', 'priority_level', 'budget',
            'cost_per_view', 'target_audience', 'impression_count', 'click_count', 'engagement_rate', 
            'cost_per_click', 'cost_per_impression', 'performance_metrics', 'created_at', 'image_url'
        ]

    def get_image_url(self, obj):
        try:
            post = obj.sponsored_post
            # Try media_urls first (Post.media_urls is a JSONField list)
            if hasattr(post, 'media_urls') and post.media_urls:
                first = post.media_urls[0]
                # If it's a dict or URL string
                if isinstance(first, dict):
                    return first.get('url') or first.get('src')
                return first

            # Fall back to attachments
            attachments = getattr(post, 'attachments', None)
            if attachments is not None:
                first_att = attachments.first()
                if first_att and getattr(first_att, 'file', None):
                    try:
                        return first_att.file.url
                    except Exception:
                        return None

            return None
        except Exception:
            return None

    def get_sponsor_name(self, obj):
        try:
            return getattr(obj.sponsor, 'username', None) or getattr(obj.sponsor, 'email', None)
        except Exception:
            return None

    def get_cost_per_click(self, obj):
        try:
            return round(obj.get_cost_per_click(), 4)
        except Exception:
            return 0

    def get_cost_per_impression(self, obj):
        try:
            return round(obj.get_cost_per_impression(), 6)
        except Exception:
            return 0

    def get_performance_metrics(self, obj):
        try:
            return obj.get_performance_metrics()
        except Exception:
            return {}


class WalletTopUpSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = WalletTopUp
        fields = [
            'id', 'user_id', 'amount', 'status', 'payment_method',
            'transaction_id', 'payment_reference', 'notes',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ('id', 'user_id', 'status', 'transaction_id', 
                           'created_at', 'updated_at', 'completed_at')

    def validate_amount(self, value):
        """Validate that top-up amount is reasonable"""
        from decimal import Decimal
        if value <= 0:
            raise serializers.ValidationError("Top-up amount must be positive")
        if value < Decimal('1.00'):
            raise serializers.ValidationError("Minimum top-up amount is $1.00")
        if value > Decimal('10000.00'):
            raise serializers.ValidationError("Maximum top-up amount is $10,000")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)

