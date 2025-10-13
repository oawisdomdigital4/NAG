from rest_framework.routers import DefaultRouter
from .views import (
    FAQViewSet,
    TestimonialViewSet,
    TeamMemberViewSet,
    CareerViewSet,
    ContactMessageViewSet,
    PageViewSet,
    AIModelToggleViewSet,
)

router = DefaultRouter()
router.register(r'faqs', FAQViewSet)
router.register(r'testimonials', TestimonialViewSet)
router.register(r'team-members', TeamMemberViewSet)
router.register(r'careers', CareerViewSet)
router.register(r'contact-messages', ContactMessageViewSet)
router.register(r'pages', PageViewSet)
router.register(r'ai-models', AIModelToggleViewSet, basename='ai-model')

urlpatterns = router.urls
