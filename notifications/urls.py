from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationPreferenceViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.urls import path

router = DefaultRouter()
# Register NotificationViewSet at the include root so when this module is
# included under path('api/notifications/', include('notifications.urls'))
# the list and custom action endpoints become:
#   GET /api/notifications/            -> list
#   GET /api/notifications/unread_count/ -> unread_count action
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'notification-preferences', NotificationPreferenceViewSet)

urlpatterns = router.urls

# Compatibility helper: ensure a simple GET at /notification-preferences/ exists
# (some frontend builds may request this directly). This view will return an empty
# list for unauthenticated callers or the authenticated user's preferences when available.
@api_view(['GET'])
@permission_classes([AllowAny])
def _compat_notification_preferences(request):
	try:
		# If the viewset and models are functional, attempt to return the user's prefs
		if request.user and request.user.is_authenticated:
			from .models import NotificationPreference
			prefs = NotificationPreference.objects.filter(user=request.user)
			from .serializers import NotificationPreferenceSerializer
			return Response(NotificationPreferenceSerializer(prefs, many=True).data)
	except Exception:
		# Fall back to empty list if anything goes wrong
		pass
	return Response([])

urlpatterns = [
	path('notification-preferences/', _compat_notification_preferences)
] + urlpatterns
