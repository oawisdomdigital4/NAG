from django.shortcuts import render
from .models import(
    FeaturedSpeaker,Organizer,
    PastEdition,
    Partner,
    SummitAbout,
    SummitHero,
    SummitKeyThemes,
    )
from .serializers import(
    OrganizerSerializer,
    PastEditionSerializer,
    PartnerSerializer,
    FeaturedSpeakerSerializer,
    SummitAboutSerializer,
    SummitHeroSerializer,
    SummitKeyThemesSerializer,
) 
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication

class FeaturedSpeakerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FeaturedSpeaker.objects.all()
    serializer_class = FeaturedSpeakerSerializer
    permission_classes = [AllowAny]


# --------------------------- Simple read-only viewsets ---------------------------

class OrganizerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organizer.objects.all()
    serializer_class = OrganizerSerializer
    permission_classes = [AllowAny]



class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [AllowAny]


class RegistrationPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Expose registration packages to the frontend as a simple ordered list."""
    permission_classes = [AllowAny]

    def get_queryset(self):
        from .models import RegistrationPackage

        return RegistrationPackage.objects.all().order_by('order', 'id')

    def get_serializer_class(self):
        from .serializers import RegistrationPackageSerializer

        return RegistrationPackageSerializer


class PartnerSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest published PartnerSection instance as a single object.

    The frontend calls the list endpoint and receives the current partner section
    object (or `{}` if none exists).
    """
    permission_classes = [AllowAny]

    def get_queryset(self):
        from .models import PartnerSection

        return PartnerSection.objects.filter(is_published=True).order_by('-created_at')

    def get_serializer_class(self):
        from .serializers import PartnerSectionSerializer

        return PartnerSectionSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        obj = qs.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)

class SummitHeroViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest published SummitHero instance as a single object.
    The frontend calls the list endpoint and receives the current hero object
    (or `{}` if none exists).
    """
    queryset = SummitHero.objects.filter(is_published=True).order_by('-created_at').prefetch_related('stats')
    serializer_class = SummitHeroSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        obj = self.queryset.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)
    
class PastEditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PastEdition.objects.all()
    serializer_class = PastEditionSerializer
    permission_classes = [AllowAny]

class SummitAboutViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest SummitAbout instance (with pillars) for the Summit page."""
    queryset = SummitAbout.objects.all().order_by('-created_at').prefetch_related('pillars')
    serializer_class = SummitAboutSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        obj = self.queryset.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)


class SummitKeyThemesViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest SummitKeyThemes instance (with nested themes)."""
    queryset = SummitKeyThemes.objects.all().order_by('-created_at').prefetch_related('themes')
    serializer_class = SummitKeyThemesSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        obj = self.queryset.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)


class SummitAgendaViewSet(viewsets.ReadOnlyModelViewSet):
    """Return the latest SummitAgenda instance (with days)."""
    queryset = None
    serializer_class = None
    permission_classes = [AllowAny]

    def get_queryset(self):
        from .models import SummitAgenda

        return SummitAgenda.objects.all().order_by('-created_at').prefetch_related('days')

    def get_serializer_class(self):
        from .serializers import SummitAgendaSerializer

        return SummitAgendaSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        obj = qs.first()
        if not obj:
            return Response({}, status=200)
        serializer = self.get_serializer(obj, context={'request': request})
        return Response(serializer.data)
