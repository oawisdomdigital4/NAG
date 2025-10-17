from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    # Expose the FK as `user_id` which the frontend expects
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Notification
        # Explicitly list fields so the JSON shape is stable for the frontend
        fields = [
            'id', 'user_id', 'type', 'category', 'title', 'message',
            'action_url', 'metadata', 'read', 'read_at', 'email_sent', 'email_sent_at',
            'archived', 'archived_at', 'created_at'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user_id', 'notification_type', 'in_app_enabled', 'email_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']

    def validate_notification_type(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('notification_type is required')
        return value.strip()
