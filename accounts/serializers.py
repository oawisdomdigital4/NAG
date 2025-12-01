from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from .models import UserProfile

# Prefer community models if present (avoid duplication)
try:
    from community.models import UserProfile as CommunityUserProfile
except Exception:
    CommunityUserProfile = None

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'phone', 'country', 'bio',
            'expertise_areas', 'company_name', 'industry', 'community_approved', 'avatar_url', 'avatar',
            'verification_status', 'earning_balance', 'pending_balance', 'available_balance', 'portfolio_url'
        ]
    
    def get_avatar(self, obj):
        """Get avatar URL - returns full URL for image field"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def get_avatar_url(self, obj):
        """Get avatar URL - returns avatar_url field or falls back to avatar"""
        if obj.avatar_url:
            return obj.avatar_url
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'phone', 'country', 'bio',
            'expertise_areas', 'company_name', 'industry', 'community_approved', 'avatar_url', 'avatar',
            'verification_status', 'earning_balance', 'pending_balance', 'available_balance', 'portfolio_url'
        ]
    
    def get_verification_status(self, obj):
        """Get verification status from CorporateVerification model"""
        try:
            from community.models import CorporateVerification
            verification = CorporateVerification.objects.get(user=obj.user)
            return verification.status
        except:
            return 'pending'

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'profile', 'first_name', 'last_name']

class SignupSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    bio = serializers.CharField(required=False)
    expertise_areas = serializers.ListField(child=serializers.CharField(), required=False)
    company_name = serializers.CharField(required=False)
    industry = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'role', 'full_name', 'phone', 'country',
            'bio', 'expertise_areas', 'company_name', 'industry'
        ]

    def create(self, validated_data):
        profile_fields = {
            'full_name': validated_data.pop('full_name', ''),
            'phone': validated_data.pop('phone', ''),
            'country': validated_data.pop('country', ''),
            'bio': validated_data.pop('bio', ''),
            'expertise_areas': validated_data.pop('expertise_areas', []),
            'company_name': validated_data.pop('company_name', ''),
            'industry': validated_data.pop('industry', ''),
        }
        password = validated_data.pop('password')
        # Ensure username is unique by setting it to email
        validated_data['username'] = validated_data['email']
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, **profile_fields)
        return user

class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    token = serializers.CharField()
    new_password = serializers.CharField()