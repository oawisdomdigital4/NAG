from rest_framework import serializers
from .models import (
    FAQ, TeamMember, Career, ContactMessage,
    ContactDetails, DepartmentContact, OfficeLocation
)


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'


class OfficeLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeLocation
        fields = ['city', 'country', 'address', 'type']


class DepartmentContactSerializer(serializers.ModelSerializer):
    # Keep a `department` key for frontend compatibility (maps to model.title)
    department = serializers.CharField(source='title', read_only=True)

    class Meta:
        model = DepartmentContact
        fields = ['department', 'email', 'description']


class ContactDetailsSerializer(serializers.ModelSerializer):
    office_locations = OfficeLocationSerializer(many=True, read_only=True)
    department_contacts = DepartmentContactSerializer(many=True, read_only=True)
    contact_methods = serializers.SerializerMethodField()
    # Backwards-compatible fields expected by the existing frontend
    main_email = serializers.CharField(source='contact_email', read_only=True)
    main_phone = serializers.CharField(source='contact_phone', read_only=True)
    primary_address = serializers.CharField(source='headquarters_address', read_only=True)
    description = serializers.SerializerMethodField()

    class Meta:
        model = ContactDetails
        fields = [
            'id',
            'contact_methods',
            # legacy keys used by frontend
            'main_email',
            'main_phone',
            'primary_address',
            'description',
            'office_locations',
            'department_contacts',
            'is_published',
            'created_at'
        ]

    def get_contact_methods(self, obj):
        """Return an array of contact method objects matching frontend shape."""
        return [
            {
                'title': 'Email Us',
                'details': obj.contact_email,
                'description': 'General inquiries and support'
            },
            {
                'title': 'Call Us',
                'details': obj.contact_phone,
                'description': obj.contact_hours
            },
            {
                'title': 'Visit Us',
                'details': obj.headquarters_address,
                'description': 'Pan-African Headquarters'
            }
        ]

    def get_description(self, obj):
        # No model description field exists in the simplified ContactDetails model.
        # Provide an empty string for frontend compatibility. If you later add a
        # description field to the model, update this to return that value.
        return ''


class TeamMemberSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    # Provide aliases used by the frontend
    photo = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    # Expose top-level twitter/linkedin for any frontend code that expects them
    twitter = serializers.CharField(source='twitter_url', read_only=True)
    linkedin = serializers.CharField(source='linkedin_url', read_only=True)

    class Meta:
        model = TeamMember
        # `title` removed from model; don't expose it in serializer.
        fields = [
            'id', 'name', 'bio', 'photo_url', 'photo', 'image',
            'linkedin_url', 'twitter_url', 'linkedin', 'twitter', 'social_links', 'email', 'order', 'is_active'
        ]

    def get_photo_url(self, obj):
        """Return an absolute photo URL when request context is present, otherwise return relative url or empty."""
        request = self.context.get('request') if isinstance(self.context, dict) else None
        if obj.photo:
            try:
                url = obj.photo.url
            except Exception:
                return None
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_photo(self, obj):
        # alias expected by frontend (leader.photo)
        return self.get_photo_url(obj)

    def get_image(self, obj):
        # some frontend components use `image` instead of `photo`
        return self.get_photo_url(obj)

    def get_social_links(self, obj):
        # Provide a social_links object matching frontend expectations
        # Always include the keys so frontend can reference them directly even if empty.
        return {
            'linkedin': obj.linkedin_url or '',
            'twitter': obj.twitter_url or ''
        }


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = '__all__'


class ContactMessageSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    inquiry = serializers.CharField(source='inquiry_type', required=False, allow_blank=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'firstName', 'lastName', 'name', 'email', 'subject', 'inquiry', 'message', 'created_at']
        read_only_fields = ['id', 'created_at', 'name']

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, attrs):
        first = attrs.get('first_name', '')
        last = attrs.get('last_name', '')
        if not first and not last and not attrs.get('name'):
            raise serializers.ValidationError("Please provide at least a first or last name.")
        if not attrs.get('email'):
            raise serializers.ValidationError({ 'email': 'Email is required.' })
        if not attrs.get('message'):
            raise serializers.ValidationError({ 'message': 'Message is required.' })
        return attrs

    def create(self, validated_data):
        fn = validated_data.get('first_name', '')
        ln = validated_data.get('last_name', '')
        if not validated_data.get('name'):
            validated_data['name'] = f"{fn} {ln}".strip()
        return super().create(validated_data)




# FooterContent serializer
class FooterContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = [
            'id', 'company_name', 'tagline', 'address_text', 'contact_email',
            # social
            'social_facebook', 'social_instagram', 'social_linkedin', 'social_twitter', 'social_youtube',
            # company
            'company_about', 'company_team', 'company_careers', 'company_contact',
            # platforms
            'platforms_magazine', 'platforms_tv', 'platforms_institute', 'platforms_summit', 'platforms_community',
            # account
            'account_login', 'account_signup', 'account_faqs',
            # legal
            'legal_terms', 'legal_privacy', 'legal_help',
            'copyright_text', 'is_published', 'created_at'
        ]


# Attach FooterContent model if available
try:
    from .models import FooterContent
    FooterContentSerializer.Meta.model = FooterContent
except Exception:
    pass


class AboutHeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'title_main', 'subtitle', 'background_image', 'is_published', 'created_at']


# Attach AboutHero model if available
try:
    from .models import AboutHero
    AboutHeroSerializer.Meta.model = AboutHero
except Exception:
    pass

