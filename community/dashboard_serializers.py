from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Course,
    CourseEnrollment,
    Opportunity,
    Campaign,
    WithdrawalRequest,
    PartnerDirectory,
    CorporateConnection,
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested relationships"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = fields

class CourseSerializer(serializers.ModelSerializer):
    facilitator = UserBasicSerializer(read_only=True)
    enrollment_status = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'facilitator', 'thumbnail',
            'preview_video', 'duration', 'level', 'prerequisites',
            'learning_outcomes', 'syllabus', 'price', 'status',
            'rating', 'enrollment_count', 'enrollment_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['enrollment_count', 'rating', 'created_at', 'updated_at']

    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = CourseEnrollment.objects.get(
                    user=request.user,
                    course=obj
                )
                return enrollment.status
            except CourseEnrollment.DoesNotExist:
                pass
        return None

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'user', 'course', 'progress', 'completion_percentage',
            'status', 'enrolled_at', 'completed_at'
        ]
        read_only_fields = ['enrolled_at', 'completed_at']

class OpportunitySerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'description', 'company', 'location',
            'type', 'created_by', 'requirements', 'application_url',
            'deadline', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class CampaignSerializer(serializers.ModelSerializer):
    owner = UserBasicSerializer(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'description', 'owner', 'budget',
            'start_date', 'end_date', 'target_audience',
            'performance_metrics', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user', 'amount', 'bank_name', 'account_number',
            'account_name', 'status', 'notes', 'processed_at',
            'created_at'
        ]
        read_only_fields = ['processed_at', 'created_at', 'status']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PartnerDirectorySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    industry = serializers.CharField(source='company.industry', read_only=True)

    class Meta:
        model = PartnerDirectory
        fields = [
            'id', 'company', 'company_name', 'industry', 'industry_tags',
            'services', 'achievements', 'social_links', 'showcase_images',
            'featured', 'verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['featured', 'verified', 'created_at', 'updated_at']

class CorporateConnectionSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    receiver = UserBasicSerializer(read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.filter(community_profile__role='corporate')
    )

    class Meta:
        model = CorporateConnection
        fields = [
            'id', 'sender', 'receiver', 'receiver_id', 'status',
            'message', 'connected_at', 'created_at'
        ]
        read_only_fields = ['connected_at', 'created_at', 'status']

    def create(self, validated_data):
        receiver_id = validated_data.pop('receiver_id')
        validated_data['sender'] = self.context['request'].user
        validated_data['receiver_id'] = receiver_id
        return super().create(validated_data)