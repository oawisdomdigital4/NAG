from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, CourseModuleViewSet, CourseReviewViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'course-modules', CourseModuleViewSet)
router.register(r'course-reviews', CourseReviewViewSet)

urlpatterns = router.urls
