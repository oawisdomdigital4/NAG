from rest_framework import serializers
from .models import FAQ, TeamMember, Career, ContactMessage



class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'




class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = '__all__'


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = '__all__'


class ContactMessageSerializer(serializers.ModelSerializer):
    # Accept frontend-style camelCase fields and map them to model fields
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    inquiry = serializers.CharField(source='inquiry_type', required=False, allow_blank=True)

    class Meta:
        model = ContactMessage
        # expose the model fields plus the incoming camelCase aliases
        fields = ['id', 'firstName', 'lastName', 'name', 'email', 'subject', 'inquiry', 'message', 'created_at']
        read_only_fields = ['id', 'created_at', 'name']

    def validate_email(self, value):
        # Basic email normalization/validation
        return value.lower().strip()

    def validate(self, attrs):
        # Ensure we have either a name or first/last provided
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
        # DRF will have moved camelCase source fields into the model keys (first_name, last_name, inquiry_type)
        # Build name for legacy compatibility
        fn = validated_data.get('first_name', '')
        ln = validated_data.get('last_name', '')
        if not validated_data.get('name'):
            validated_data['name'] = f"{fn} {ln}".strip()
        return super().create(validated_data)


