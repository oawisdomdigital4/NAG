from rest_framework.routers import DefaultRouter
from .views import (
    FAQViewSet,
    TeamMemberViewSet,
    CareerViewSet,
    ContactMessageViewSet,
)

router = DefaultRouter()
router.register(r'faqs', FAQViewSet)
router.register(r'team-members', TeamMemberViewSet)
router.register(r'careers', CareerViewSet)
router.register(r'contact-messages', ContactMessageViewSet)

urlpatterns = router.urls
