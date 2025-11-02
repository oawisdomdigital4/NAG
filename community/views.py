from .models import Organizer, FeaturedSpeaker
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Group, GroupMembership, Post, Comment, Partner, PostBookmark
from .serializers import GroupSerializer, GroupMembershipSerializer, PostSerializer, CommentSerializer, PartnerSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from courses.serializers import CourseSerializer
from courses.models import Course
from accounts.serializers import UserSerializer

User = get_user_model()
from .serializers import OrganizerSerializer, FeaturedSpeakerSerializer
from .serializers import PastEditionSerializer, ChatRoomSerializer, MessageSerializer
from .models import PastEdition, ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .serializers import SummitHeroSerializer
from .models import SummitHero
from .serializers import AboutHeroSerializer
from .models import AboutHero
from .serializers import SummitAboutSerializer
from .models import SummitAbout
from .serializers import SummitKeyThemesSerializer
from .models import SummitKeyThemes
from rest_framework.authentication import SessionAuthentication
from django.db.models import Q
from django.db import models
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
import re
import json
from django.core.files.base import ContentFile
from accounts.authentication import DatabaseTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCommunityMember
from accounts.authentication import DatabaseTokenAuthentication
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from community.models import Video, VideoCategory
from .serializers import VideoSerializer, VideoCategorySerializer


class OrganizerViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Organizer.objects.all()
	serializer_class = OrganizerSerializer
	permission_classes = [permissions.AllowAny]

class FeaturedSpeakerViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = FeaturedSpeaker.objects.all()
	serializer_class = FeaturedSpeakerSerializer
	permission_classes = [permissions.AllowAny]


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


class PastEditionViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = PastEdition.objects.all()
	serializer_class = PastEditionSerializer
	permission_classes = [AllowAny]


class SummitHeroViewSet(viewsets.ReadOnlyModelViewSet):
	"""Return the latest published SummitHero instance as a single object.
	The frontend calls the list endpoint and receives the current hero object
	(or `{}` if none exists).
	"""
	# prefetch related stats for efficient serialization
	queryset = SummitHero.objects.filter(is_published=True).order_by('-created_at').prefetch_related('stats')
	serializer_class = SummitHeroSerializer
	permission_classes = [AllowAny]

	def list(self, request, *args, **kwargs):
		obj = self.queryset.first()
		if not obj:
			return Response({}, status=200)
		serializer = self.get_serializer(obj, context={'request': request})
		return Response(serializer.data)


class CommunitySectionViewSet(viewsets.ReadOnlyModelViewSet):
	"""Return the latest published CommunitySection instance as a single object."""
	permission_classes = [AllowAny]

	def get_queryset(self):
		from .models import CommunitySection
		return CommunitySection.objects.filter(is_published=True).order_by('-created_at')

	def get_serializer_class(self):
		from .serializers import CommunitySectionSerializer
		return CommunitySectionSerializer

	def list(self, request, *args, **kwargs):
		qs = self.get_queryset()
		obj = qs.first()
		if not obj:
			return Response({}, status=200)
		serializer = self.get_serializer(obj, context={'request': request})
		return Response(serializer.data)


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


class CTABannerViewSet(viewsets.ReadOnlyModelViewSet):
	"""Return the latest published CTABanner instance as a single object."""
	permission_classes = [AllowAny]

	def get_queryset(self):
		from .models import CTABanner
		return CTABanner.objects.filter(is_published=True).order_by('-created_at')

	def get_serializer_class(self):
		from .serializers import CTABannerSerializer
		return CTABannerSerializer

	def list(self, request, *args, **kwargs):
		qs = self.get_queryset()
		obj = qs.first()
		if not obj:
			return Response({}, status=200)
		serializer = self.get_serializer(obj, context={'request': request})
		return Response(serializer.data)

class GroupViewSet(viewsets.ModelViewSet):
	queryset = Group.objects.all()
	serializer_class = GroupSerializer
	# Allow either our DB token auth or Django session auth (useful during dev)
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated, IsCommunityMember]

	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		return super().create(request, *args, **kwargs)

	def perform_create(self, serializer):
		try:
			serializer.save(created_by=self.request.user)
		except Exception:
			serializer.save()

	@action(detail=True, methods=['post'])
	def join(self, request, pk=None):
		group = self.get_object()
		membership, created = GroupMembership.objects.get_or_create(user=request.user, group=group)
		if created:
			return Response({'success': True, 'joined': True}, status=status.HTTP_201_CREATED)
		return Response({'success': True, 'joined': True, 'message': 'Already a member'}, status=status.HTTP_200_OK)

	@action(detail=True, methods=['post'])
	def leave(self, request, pk=None):
		group = self.get_object()
		deleted, _ = GroupMembership.objects.filter(user=request.user, group=group).delete()
		if deleted:
			return Response({'success': True, 'left': True}, status=status.HTTP_200_OK)
		return Response({'success': True, 'left': False, 'message': 'Not a member'}, status=status.HTTP_200_OK)

class GroupMembershipViewSet(viewsets.ModelViewSet):
	queryset = GroupMembership.objects.all()
	serializer_class = GroupMembershipSerializer
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated, IsCommunityMember]

class PostViewSet(viewsets.ModelViewSet):
	queryset = Post.objects.all()
	serializer_class = PostSerializer
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated, IsCommunityMember]

	def list(self, request, *args, **kwargs):
		"""
		Allow filtering posts list by query params:
		- author_id or author: numeric user id (returns posts by that user)
		- group: group id to filter by group
		Falls back to default queryset if no filters provided.
		"""
		qs = self.queryset
		author_id = request.query_params.get('author_id') or request.query_params.get('author')
		group_id = request.query_params.get('group')
		try:
			if author_id:
				# try numeric match first
				if str(author_id).isdigit():
					qs = qs.filter(author__id=int(author_id))
				else:
					# try matching username/email fallback
					qs = qs.filter(Q(author__username=author_id) | Q(author__email=author_id))
			if group_id:
				qs = qs.filter(group__id=group_id)
		except Exception:
			# ignore filter errors and use base queryset
			qs = self.queryset

		page = self.paginate_queryset(qs)
		if page is not None:
			serializer = self.get_serializer(page, many=True, context={'request': request})
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(qs, many=True, context={'request': request})
		return Response(serializer.data)

	def create(self, request, *args, **kwargs):
		# Allow file uploads under 'media' key as multiple files
		# We'll create the Post first, then attach uploaded files and update media_urls
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		post = serializer.save(author=request.user)

		# Normalize media_urls in case the client sent them as a JSON string
		# (common when using multipart/form-data). Ensure post.media_urls is a list.
		try:
			if isinstance(post.media_urls, str):
				_parsed = json.loads(post.media_urls)
				if isinstance(_parsed, list):
					post.media_urls = _parsed
				else:
					post.media_urls = [_parsed]
		except Exception:
			# fallback: if parsing fails, wrap the string in a list so iteration works
			post.media_urls = [post.media_urls]

		# handle uploaded files
		files = request.FILES.getlist('media') or []
		media_urls = []
		# Basic server-side validation: file types and sizes
		ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/png', 'image/gif', 'image/webp')
		MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
		for f in files:
			if f.size > MAX_FILE_SIZE:
				return Response({'detail': f'File {f.name} exceeds maximum size of 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
			# check content type header first
			if hasattr(f, 'content_type') and f.content_type not in ALLOWED_CONTENT_TYPES:
				return Response({'detail': f'File {f.name} has unsupported content type {getattr(f, "content_type", "unknown")}'}, status=status.HTTP_400_BAD_REQUEST)
			# magic-bytes verification (read initial bytes)
			head = f.read(12)
			f.seek(0)
			is_valid = False
			# PNG signature
			if head.startswith(b'\x89PNG\r\n\x1a\n'):
				is_valid = True
			# JPEG signature
			if head[:3] == b'\xff\xd8\xff':
				is_valid = True
			# GIF signatures
			if head[:6] in (b'GIF87a', b'GIF89a'):
				is_valid = True
			# WebP starts with 'RIFF'....'WEBP'
			if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
				is_valid = True
			if not is_valid:
				return Response({'detail': f'File {f.name} failed magic-bytes verification'}, status=status.HTTP_400_BAD_REQUEST)
			try:
				attachment = post.attachments.create(file=f)
				# build URL; during development FileField.url will work if MEDIA_URL is configured
				media_urls.append(attachment.file.url)
			except Exception:
				continue

		if media_urls:
			post.media_urls = (post.media_urls or []) + media_urls
			post.save()

		# generate link previews for any external urls in media_urls
		# For any media_urls that point to external resources, attempt to download
		# images and save them as attachments so the frontend can preview the file.
		# Non-image URLs are kept as external links in media_urls. We no longer
		# generate or store rich link previews here.
		external_urls = (post.media_urls or [])
		new_media_urls: list = []
		for url in external_urls:
			# skip already-saved attachments (likely full URLs pointing to our storage)
			if re.search(r"/media/community/post_media/", url):
				new_media_urls.append(url)
				continue
			# quick extension check for common image types
			if re.search(r"\.(jpg|jpeg|png|gif|webp)(\?.*)?$", url, re.IGNORECASE):
				# attempt to fetch and save
				try:
					req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
					with urlopen(req, timeout=5) as res:
						content = res.read()
						content_type = res.headers.get('Content-Type', '')
						# enforce size limit
						if len(content) > (5 * 1024 * 1024):
							# too large, keep as external link instead of saving
							new_media_urls.append(url)
							continue
						# basic magic-bytes check reused from upload path
						head = content[:12]
						is_valid = False
						if head.startswith(b'\x89PNG\r\n\x1a\n'):
							is_valid = True
						if head[:3] == b'\xff\xd8\xff':
							is_valid = True
						if head[:6] in (b'GIF87a', b'GIF89a'):
							is_valid = True
						if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
							is_valid = True
						if not is_valid:
							new_media_urls.append(url)
							continue
						# save to attachment using ContentFile and preserve extension when possible
						try:
							ext = 'jpg'
							m = re.search(r"\.([a-zA-Z0-9]+)(?:\?.*)?$", url)
							if m:
								ext = m.group(1).lower()
							filename = f'post_img_{post.id}_{len(new_media_urls)}.{ext}'
							attachment = post.attachments.create()
							attachment.file.save(filename, ContentFile(content))
							attachment.save()
							new_media_urls.append(attachment.file.url)
						except Exception:
							new_media_urls.append(url)
				except Exception:
					# if fetch fails, keep original url as a link
					new_media_urls.append(url)
			else:
				# Non-image link -> keep as external url (frontend will render as link)
				new_media_urls.append(url)
		# assign normalized media_urls back to post and save
		if new_media_urls:
			post.media_urls = new_media_urls
			post.save()

		headers = self.get_success_headers(serializer.data)
		return Response(self.get_serializer(post, context={'request': request}).data, status=status.HTTP_201_CREATED, headers=headers)

	def _fetch_link_preview(self, url):
		# minimal, safe fetch with timeout and simple parsing
		try:
			req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
			with urlopen(req, timeout=3) as res:
				content = res.read(65536)
			s = content.decode(errors='ignore')
			# extract title
			title_match = re.search(r'<title.*?>(.*?)</title>', s, re.IGNORECASE | re.DOTALL)
			title = title_match.group(1).strip() if title_match else ''
			# description meta
			desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', s, re.IGNORECASE)
			description = desc_match.group(1).strip() if desc_match else ''
			# og:image
			og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', s, re.IGNORECASE)
			image = og_match.group(1).strip() if og_match else ''
			return {'url': url, 'title': title, 'description': description, 'image': image}
		except (HTTPError, URLError, Exception):
			return None

	def perform_create(self, serializer):
		try:
			serializer.save(author=self.request.user)
		except Exception:
			# fallback to default behavior
			serializer.save()

	@action(detail=True, methods=['post'])
	def toggle_bookmark(self, request, pk=None):
		post = self.get_object()
		bookmark, created = PostBookmark.objects.get_or_create(post=post, user=request.user)
		if not created:
			# already exists -> remove
			bookmark.delete()
			count = PostBookmark.objects.filter(post=post).count()
			return Response({'bookmarked': False, 'bookmarks_count': count}, status=status.HTTP_200_OK)
		count = PostBookmark.objects.filter(post=post).count()
		return Response({'bookmarked': True, 'bookmarks_count': count}, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=['post'])
	def toggle_reaction(self, request, pk=None):
		"""
		Simple reaction toggle endpoint. Expects JSON body: { 'reaction_type': '<type>' }
		This implementation echoes back the reaction type and returns 200. For a full
		real implementation, add a PostReaction model to persist user reactions and
		update reaction counts.
		"""
		post = self.get_object()
		reaction_type = request.data.get('reaction_type') if isinstance(request.data, dict) else None
		if not reaction_type:
			return Response({'detail': 'reaction_type is required'}, status=status.HTTP_400_BAD_REQUEST)
		user = request.user
		# Toggle or set reaction
		from .models import PostReaction
		try:
			existing = PostReaction.objects.filter(post=post, user=user).first()
			if existing:
				# update or delete depending on type
				if existing.reaction_type == reaction_type:
					# same reaction -> remove
					existing.delete()
					current = None
				else:
					existing.reaction_type = reaction_type
					existing.save()
					current = reaction_type
			else:
				PostReaction.objects.create(post=post, user=user, reaction_type=reaction_type)
				current = reaction_type
		except Exception as e:
			return Response({'detail': 'Failed to persist reaction', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		# return current reaction and aggregated counts
		try:
			qs = post.reactions.values('reaction_type').order_by().annotate(count=models.Count('id'))
			counts = {item['reaction_type']: item['count'] for item in qs}
		except Exception:
			counts = {}
		return Response({'reaction_type': current, 'reaction_counts': counts}, status=status.HTTP_200_OK)

	@action(detail=True, methods=['get'])
	def comments(self, request, pk=None):
		post = self.get_object()
		# Hide private replies unless requester is the post author or the comment author
		# Return only top-level comments; nested replies will be serialized by
		# CommentSerializer.get_replies so the frontend receives a nested structure
		if request.user.is_authenticated:
			qs = post.comments.filter(parent_comment__isnull=True).filter(
				Q(is_private_reply=False) | Q(author=request.user) | Q(post__author=request.user)
			).order_by('created_at')
		else:
			qs = post.comments.filter(parent_comment__isnull=True, is_private_reply=False).order_by('created_at')
		# Use CommentSerializer explicitly so nested replies (SerializerMethodField
		# `replies`) and comment-specific SerializerMethodFields are included in the
		# response. Using self.get_serializer here would select PostSerializer which
		# is not suitable for serializing Comment instances.
		from .serializers import CommentSerializer as _CommentSerializer
		serializer = _CommentSerializer(qs, many=True, context={'request': request})
		return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
	queryset = Comment.objects.all()
	serializer_class = CommentSerializer
	authentication_classes = [DatabaseTokenAuthentication]
	permission_classes = [IsAuthenticated, IsCommunityMember]

	def perform_create(self, serializer):
		try:
			serializer.save(author=self.request.user)
		except Exception:
			serializer.save()

	def create(self, request, *args, **kwargs):
		# Ensure created comment is serialized from the saved instance so
		# SerializerMethodFields (replied_to_name, author_*, likes_count) are computed
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		comment = serializer.save(author=request.user)
		# Return the freshly serialized comment instance with request in context
		return Response(self.get_serializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=['post'])
	def toggle_like(self, request, pk=None):
		comment = self.get_object()
		user = request.user
		from .models import CommentReaction
		try:
			existing = CommentReaction.objects.filter(comment=comment, user=user).first()
			if existing:
				existing.delete()
				liked = False
			else:
				CommentReaction.objects.create(comment=comment, user=user)
				liked = True
		except Exception as e:
			return Response({'detail': 'Failed to toggle like', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		likes_count = comment.reactions.count()
		return Response({'liked': liked, 'likes_count': likes_count}, status=status.HTTP_200_OK)


class ChatRoomViewSet(viewsets.ModelViewSet):
	queryset = ChatRoom.objects.all()
	serializer_class = ChatRoomSerializer
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated]


class MessageViewSet(viewsets.ModelViewSet):
	queryset = Message.objects.all()
	serializer_class = MessageSerializer
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated]


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def community_search(request):
	"""Search posts and groups by query param `q`.

	Returns JSON: { posts: [...], groups: [...], users: [] }
	"""
	q = request.query_params.get('q', '').strip()
	results = {'posts': [], 'groups': [], 'users': []}
	if not q or len(q) < 2:
		return Response(results)

	try:
		# search posts (title or content)
		post_qs = Post.objects.filter(Q(title__icontains=q) | Q(content__icontains=q)).order_by('-created_at')[:20]
		posts_data = PostSerializer(post_qs, many=True, context={'request': request}).data
		results['posts'] = posts_data

		# search groups (name or description)
		group_qs = Group.objects.filter(Q(name__icontains=q) | Q(description__icontains=q)).order_by('-created_at')[:20]
		groups_data = GroupSerializer(group_qs, many=True, context={'request': request}).data
		results['groups'] = groups_data

		# search courses by title/short_description
		try:
			course_qs = Course.objects.filter(Q(title__icontains=q) | Q(short_description__icontains=q)).order_by('-created_at')[:20]
			results['courses'] = CourseSerializer(course_qs, many=True, context={'request': request}).data
		except Exception:
			results['courses'] = []

		# search users by username or profile.full_name
		try:
			users_qs = User.objects.filter(Q(username__icontains=q) | Q(email__icontains=q))[:20]
			results['users'] = UserSerializer(users_qs, many=True).data
		except Exception:
			results['users'] = []
	except Exception as e:
		return Response({'detail': 'Search failed', 'error': str(e)}, status=500)

	return Response(results)



class VideoCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoCategory.objects.filter(is_active=True)
    serializer_class = VideoCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        """Only return categories that have published videos."""
        return super().get_queryset().filter(videos__is_published=True).distinct()

class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.filter(is_published=True)
    serializer_class = VideoSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category', None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    @action(detail=True, methods=['post'])
    def increment_views(self, request, slug=None):
        """Increment the view count for a video."""
        video = self.get_object()
        Video.objects.filter(id=video.id).update(view_count=F('view_count') + 1)
        return Response({'status': 'view count updated'})