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
    ChatRoomViewSet,
    MessageViewSet,
)

router = DefaultRouter()
router.register(r'partners', PartnerViewSet, basename='partner')
router.register(r'organizers', OrganizerViewSet, basename='organizer')
router.register(r'featured-speakers', FeaturedSpeakerViewSet, basename='featured-speaker')
router.register(r'past-editions', PastEditionViewSet, basename='past-edition')
router.register(r'groups', GroupViewSet)
router.register(r'group-memberships', GroupMembershipViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'chat-rooms', ChatRoomViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = router.urls

from .views import community_search

urlpatterns += [
	path('search/', community_search, name='community-search'),
]
