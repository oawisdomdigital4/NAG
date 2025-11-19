from .models import Video, VideoCategory
from rest_framework import serializers
from django.db import models

class VideoCategorySerializer(serializers.ModelSerializer):
    video_count = serializers.SerializerMethodField()

    class Meta:
        model = VideoCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'color_from', 'color_to', 'video_count'
        ]

    def get_video_count(self, obj):
        return obj.videos.filter(is_published=True).count()

# Simplified serializer for related videos to avoid recursion
class RelatedVideoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    video_id = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description', 'category_name',
            'content_type', 'video_id', 'thumbnail_url', 'duration',
            'view_count', 'created_at'
        ]

    def get_video_id(self, obj):
        vid = obj.get_video_id()
        request = self.context.get('request') if isinstance(self.context, dict) else None
        try:
            if vid and isinstance(vid, str) and request and vid.startswith('/'):
                return request.build_absolute_uri(vid)
        except Exception:
            pass
        return vid

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            url = obj.thumbnail.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class VideoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    video_id = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    related_videos = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'category_name',
            'content_type', 'video_id', 'thumbnail_url', 'duration',
            'is_featured', 'view_count', 'created_at', 'related_videos'
        ]

    def get_video_id(self, obj):
        # Return an absolute URL for uploaded videos when a request is
        # available so the frontend fetches media from the Django backend
        # (prevents the browser resolving a relative path against the
        # frontend dev server which may not support Range requests).
        vid = obj.get_video_id()
        request = self.context.get('request') if isinstance(self.context, dict) else None
        try:
            if vid and isinstance(vid, str) and request and vid.startswith('/'):
                return request.build_absolute_uri(vid)
        except Exception:
            # on any error, fall back to the raw value
            pass
        return vid

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            url = obj.thumbnail.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_related_videos(self, obj):
        """Return 3 related videos from the same category.
        Uses RelatedVideoSerializer to avoid recursion."""
        related = Video.objects.filter(
            category=obj.category,
            is_published=True
        ).exclude(id=obj.id)[:3]
        
        return RelatedVideoSerializer(
            related, 
            many=True, 
            context=self.context
        ).data