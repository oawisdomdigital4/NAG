from .views import VideoViewSet, VideoCategoryViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'video-categories', VideoCategoryViewSet, basename='video-category')

urlpatterns = router.urls