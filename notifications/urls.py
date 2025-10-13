from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationPreferenceViewSet

router = DefaultRouter()
# Register NotificationViewSet at the include root so when this module is
# included under path('api/notifications/', include('notifications.urls'))
# the list and custom action endpoints become:
#   GET /api/notifications/            -> list
#   GET /api/notifications/unread_count/ -> unread_count action
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'notification-preferences', NotificationPreferenceViewSet)

urlpatterns = router.urls
