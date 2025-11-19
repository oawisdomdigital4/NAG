from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import (
    FAQ, TeamMember, Career, ContactMessage,
    ContactDetails, OfficeLocation, DepartmentContact, AboutHero,
)
# Import only non-contact related serializers to avoid circular imports
from .serializers import FAQSerializer, CareerSerializer, ContactMessageSerializer, AboutHeroSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


class AboutHeroViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest published AboutHero instance as a single object."""
    permission_classes = [AllowAny]

    def get_queryset(self):
        from .models import AboutHero

        return AboutHero.objects.filter(is_published=True).order_by('-created_at')

    def get_serializer_class(self):
        from .serializers import AboutHeroSerializer

        return AboutHeroSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        obj = qs.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)

class FAQViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = FAQ.objects.all()
	serializer_class = FAQSerializer
	permission_classes = [permissions.AllowAny]

class ContactDetailsViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ContactDetails.objects.all()
	serializer_class = None
	permission_classes = [permissions.AllowAny]

	def get_serializer_class(self):
		from .serializers import ContactDetailsSerializer
		return ContactDetailsSerializer

	def get_queryset(self):
		# Return the latest contact details
		return ContactDetails.objects.order_by('-created_at')

	def list(self, request, *args, **kwargs):
		# For list view, return only the latest contact details
		queryset = self.get_queryset()
		obj = queryset.first()
		if not obj:
			return Response({})
		serializer = self.get_serializer(obj)
		return Response(serializer.data)

class OfficeLocationViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = OfficeLocation.objects.all()
	serializer_class = None
	permission_classes = [permissions.AllowAny]

	def get_serializer_class(self):
		from .serializers import OfficeLocationSerializer
		return OfficeLocationSerializer

class DepartmentContactViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = DepartmentContact.objects.all()
	serializer_class = None
	permission_classes = [permissions.AllowAny]

	def get_serializer_class(self):
		from .serializers import DepartmentContactSerializer
		return DepartmentContactSerializer


class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
	"""Expose team members. Prefer community.TeamMember if available to avoid duplicate data.
	Falls back to utils.TeamMember when community model not present.
	"""
	serializer_class = None  # Set dynamically in get_serializer_class
	permission_classes = [permissions.AllowAny]

	def get_queryset(self):
		# try community model first
		try:
			from community.models import TeamMember as CommunityTeamMember
			return CommunityTeamMember.objects.filter(is_active=True).order_by('order', 'id')
		except Exception:
			return TeamMember.objects.all().order_by('id')

	def get_serializer_class(self):
		# try community serializer first
		try:
			from community.serializers import TeamMemberSerializer as CommunityTeamMemberSerializer
			return CommunityTeamMemberSerializer
		except Exception:
			from .serializers import TeamMemberSerializer
			return TeamMemberSerializer

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


class FooterContentViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest published FooterContent instance as a single object."""
    permission_classes = [AllowAny]

    def get_queryset(self):
        from .models import FooterContent

        return FooterContent.objects.filter(is_published=True).order_by('-created_at')

    def get_serializer_class(self):
        from .serializers import FooterContentSerializer

        return FooterContentSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        obj = qs.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)