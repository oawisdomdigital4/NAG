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
    class Meta:
        model = NotificationPreference
        fields = '__all__'
