from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
	GroupViewSet,
	GroupMembershipViewSet,
	PostViewSet,
	CommentViewSet,
	PartnerViewSet,
	OrganizerViewSet,
	FeaturedSpeakerViewSet,
	PastEditionViewSet,
	SummitHeroViewSet,
    AboutHeroViewSet,
	PartnerSectionViewSet,
	FooterContentViewSet,
	SummitAboutViewSet,
	SummitKeyThemesViewSet,
	SummitAgendaViewSet,
	RegistrationPackageViewSet,
    CommunitySectionViewSet,
	CTABannerViewSet,
    ChatRoomViewSet,
    MessageViewSet,
    VideoViewSet,
    VideoCategoryViewSet,
)

router = DefaultRouter()
router.register(r'partners', PartnerViewSet, basename='partner')
router.register(r'organizers', OrganizerViewSet, basename='organizer')
router.register(r'featured-speakers', FeaturedSpeakerViewSet, basename='featured-speaker')
router.register(r'past-editions', PastEditionViewSet, basename='past-edition')
router.register(r'summit-hero', SummitHeroViewSet, basename='summit-hero')
router.register(r'about-hero', AboutHeroViewSet, basename='about-hero')
router.register(r'partner-section', PartnerSectionViewSet, basename='partner-section')
router.register(r'footer', FooterContentViewSet, basename='footer')
router.register(r'summit-about', SummitAboutViewSet, basename='summit-about')
router.register(r'summit-keythemes', SummitKeyThemesViewSet, basename='summit-keythemes')
router.register(r'summit-agenda', SummitAgendaViewSet, basename='summit-agenda')
router.register(r'registration-packages', RegistrationPackageViewSet, basename='registration-package')
router.register(r'community-section', CommunitySectionViewSet, basename='community-section')
router.register(r'cta-banner', CTABannerViewSet, basename='cta-banner')
router.register(r'groups', GroupViewSet)
router.register(r'group-memberships', GroupMembershipViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'chat-rooms', ChatRoomViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'video-categories', VideoCategoryViewSet, basename='video-category')

urlpatterns = router.urls

from .views import community_search

urlpatterns += [
	path('search/', community_search, name='community-search'),
]
