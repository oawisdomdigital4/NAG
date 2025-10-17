from rest_framework import viewsets, permissions
from .models import FAQ, TeamMember, Career, ContactMessage
from .serializers import (
	FAQSerializer,
	TeamMemberSerializer,
	CareerSerializer,
	ContactMessageSerializer,
)



class FAQViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = FAQ.objects.all()
	serializer_class = FAQSerializer
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
	"""
	Public: allow creating contact messages (POST).
	Admins: can list/retrieve/delete via the browsable API (IsAdminUser required).
	"""
	queryset = ContactMessage.objects.all()
	serializer_class = ContactMessageSerializer

	def get_permissions(self):
		# Allow anyone to create. Only admin users can list/retrieve/delete.
		if self.action in ['create']:
			return [permissions.AllowAny()]
		return [permissions.IsAdminUser()]

	def list(self, request, *args, **kwargs):
		return self.permission_denied(request, message='Listing contact messages is restricted.')

	def retrieve(self, request, *args, **kwargs):
		return self.permission_denied(request, message='Retrieve is restricted.')


