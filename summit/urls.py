from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    PartnerViewSet,
	OrganizerViewSet,
	FeaturedSpeakerViewSet,
	PastEditionViewSet,
	SummitHeroViewSet,
    PartnerSectionViewSet,
    SummitAboutViewSet,
	SummitKeyThemesViewSet,
	SummitAgendaViewSet,
	RegistrationPackageViewSet,
)

router = DefaultRouter()
router.register(r'partners', PartnerViewSet, basename='partner')
router.register(r'organizers', OrganizerViewSet, basename='organizer')
router.register(r'featured-speakers', FeaturedSpeakerViewSet, basename='featured-speaker')
router.register(r'past-editions', PastEditionViewSet, basename='past-edition')
router.register(r'summit-hero', SummitHeroViewSet, basename='summit-hero')
router.register(r'partner-section', PartnerSectionViewSet, basename='partner-section')
router.register(r'summit-about', SummitAboutViewSet, basename='summit-about')
router.register(r'summit-keythemes', SummitKeyThemesViewSet, basename='summit-keythemes')
router.register(r'summit-agenda', SummitAgendaViewSet, basename='summit-agenda')
router.register(r'registration-packages', RegistrationPackageViewSet, basename='registration-package')

urlpatterns = router.urls