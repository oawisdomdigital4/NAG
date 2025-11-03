from rest_framework.routers import DefaultRouter
from .views import (
    FAQViewSet,
    TeamMemberViewSet,
    CareerViewSet,
    ContactMessageViewSet,
        ContactDetailsViewSet,
        OfficeLocationViewSet,
        DepartmentContactViewSet,
)
from .views_extra import ensure_csrf
from django.urls import path

router = DefaultRouter()
router.register(r'faqs', FAQViewSet)
router.register(r'team-members', TeamMemberViewSet, basename='team-members')
router.register(r'careers', CareerViewSet)
router.register(r'contact-messages', ContactMessageViewSet)
router.register(r'contact-details', ContactDetailsViewSet, basename='contact-details')
router.register(r'office-locations', OfficeLocationViewSet)
router.register(r'department-contacts', DepartmentContactViewSet)

urlpatterns = router.urls + [
    path('csrf/', ensure_csrf, name='api-utils-csrf'),
]
