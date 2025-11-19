from django.shortcuts import render
from .models import Video, VideoCategory
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from .serializers import VideoSerializer, VideoCategorySerializer
from rest_framework import viewsets 
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F


class VideoCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoCategory.objects.filter(is_active=True)
    serializer_class = VideoCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        """Only return categories that have published videos."""
        return super().get_queryset().filter(videos__is_published=True).distinct()


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.filter(is_published=True)
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category', None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    @action(detail=True, methods=['post'])
    def increment_views(self, request, slug=None):
        """Increment the view count for a video."""
        video = self.get_object()
        Video.objects.filter(id=video.id).update(view_count=F('view_count') + 1)
        return Response({'status': 'view count updated'})

