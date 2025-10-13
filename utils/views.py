
from rest_framework import viewsets, permissions
from .models import FAQ, Testimonial, TeamMember, Career, ContactMessage, Page, AIModelToggle
from .serializers import (
	FAQSerializer,
	TestimonialSerializer,
	TeamMemberSerializer,
	CareerSerializer,
	ContactMessageSerializer,
	PageSerializer,
	AIModelToggleSerializer,
)


class AIModelToggleViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AIModelToggle.objects.all()
	serializer_class = AIModelToggleSerializer
	permission_classes = [permissions.AllowAny]


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = FAQ.objects.all()
	serializer_class = FAQSerializer
	permission_classes = [permissions.AllowAny]

class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Testimonial.objects.all()
	serializer_class = TestimonialSerializer
	permission_classes = [permissions.AllowAny]

class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TeamMember.objects.all()
	serializer_class = TeamMemberSerializer
	permission_classes = [permissions.AllowAny]

class CareerViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Career.objects.filter(is_active=True)
	serializer_class = CareerSerializer
	permission_classes = [permissions.AllowAny]

class ContactMessageViewSet(viewsets.ModelViewSet):
	queryset = ContactMessage.objects.all()
	serializer_class = ContactMessageSerializer
	permission_classes = [permissions.AllowAny]

class PageViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Page.objects.filter(is_published=True)
	serializer_class = PageSerializer
	permission_classes = [permissions.AllowAny]
