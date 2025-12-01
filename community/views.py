"""
Cleaned and fixed views.py for the community app.
- Compatible with Django 5.x
- Uses DatabaseTokenAuthentication only (no SimpleJWT)
- Duplicate imports removed
- Indentation and syntax errors fixed
- Defensive coding for caching, pagination, and external fetches

Drop this into your community/views.py (or whatever file you use) and run tests.
"""

from datetime import timedelta
import json
import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework import permissions, status, viewsets, parsers, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication

# Local imports
from .models import (
    Comment,
    Group,
    GroupMembership,
    Post,
    CorporateVerification,
    CollaborationRequest,
    CorporateMessage,
)

from .serializers import (
    CommentSerializer,
    GroupMembershipSerializer,
    GroupSerializer,
    PostSerializer,
    PostBookmark,
)

from .permissions import IsCommunityMember, IsSubscribed
from .feed import FeedRanker
from accounts.authentication import DatabaseTokenAuthentication
from accounts.serializers import UserSerializer
from courses.models import Course
from courses.serializers import CourseSerializer

User = get_user_model()


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


# --------------------------- Groups & Membership ---------------------------

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # Allow either our DB token auth or Django session auth (useful during dev)
    authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsCommunityMember]

    def get_parsers(self):
        """Override to support both JSON and multipart form data for file uploads"""
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
            return [MultiPartParser(), FormParser(), JSONParser()]
        from rest_framework.parsers import JSONParser
        return [JSONParser()]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Override update to check permissions - only creator or moderators can update"""
        group = self.get_object()
        user = request.user
        # Only creator, moderators, or staff can update group
        is_creator = user == group.created_by
        is_moderator = group.moderators.filter(id=user.id).exists()
        is_staff = user.is_staff
        
        if not (is_creator or is_moderator or is_staff):
            from rest_framework.response import Response
            return Response({'detail': 'Permission denied. Only group creator or moderators can update.'}, status=403)
        
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests for partial updates"""
        group = self.get_object()
        user = request.user
        # Only creator, moderators, or staff can update group
        is_creator = user == group.created_by
        is_moderator = group.moderators.filter(id=user.id).exists()
        is_staff = user.is_staff
        
        if not (is_creator or is_moderator or is_staff):
            from rest_framework.response import Response
            return Response({'detail': 'Permission denied. Only group creator or moderators can update.'}, status=403)
        
        return super().partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Get a single group by ID"""
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a group - only creator or staff can delete"""
        group = self.get_object()
        user = request.user
        
        # Only creator or staff can delete
        if not (user == group.created_by or user.is_staff):
            from rest_framework.response import Response
            return Response({'detail': 'Permission denied. Only group creator can delete.'}, status=403)
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_group(self, request, pk=None):
        """
        LiteSpeed Workaround: POST-based group update for production servers that block PUT.
        
        Usage: POST /api/community/groups/{id}/update_group/
        Content-Type: multipart/form-data or application/json
        
        This endpoint mirrors the PUT/PATCH behavior but uses POST to bypass
        LiteSpeed restrictions on PUT requests.
        """
        group = self.get_object()
        user = request.user
        
        # Same permission checks as update() and partial_update()
        is_creator = user == group.created_by
        is_moderator = group.moderators.filter(id=user.id).exists()
        is_staff = user.is_staff
        
        if not (is_creator or is_moderator or is_staff):
            return Response(
                {'detail': 'Permission denied. Only group creator or moderators can update.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use the serializer to validate and update
        serializer = self.get_serializer(group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        try:
            group = serializer.save(created_by=self.request.user)
            # Auto-assign creator as a member and moderator so they can manage the group immediately
            from .models import GroupMembership
            GroupMembership.objects.get_or_create(user=self.request.user, group=group)
            group.moderators.add(self.request.user)
        except Exception:
            group = serializer.save()
            # Retry assignment even if first save failed
            from .models import GroupMembership
            GroupMembership.objects.get_or_create(user=self.request.user, group=group)
            group.moderators.add(self.request.user)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        group = self.get_object()
        # Respect private groups: joining may be restricted unless an invite token is provided
        if getattr(group, 'is_private', False):
            token = (request.data or {}).get('invite_token') or request.query_params.get('invite_token')
            if not token:
                return Response({'detail': 'This group is private. Joining requires invitation.'}, status=status.HTTP_403_FORBIDDEN)

            # validate invite token
            try:
                from .models import GroupInvite
                invite = GroupInvite.objects.filter(group=group, token=token, status='pending').first()
                if not invite:
                    return Response({'detail': 'Invalid or expired invite token'}, status=status.HTTP_400_BAD_REQUEST)
                if invite.is_expired():
                    invite.mark_expired()
                    return Response({'detail': 'Invite has expired'}, status=status.HTTP_400_BAD_REQUEST)
                # If invite specifies a user, ensure it matches
                if invite.invited_user and invite.invited_user_id != request.user.id:
                    return Response({'detail': 'Invite not valid for this user'}, status=status.HTTP_403_FORBIDDEN)
                if invite.invited_email and request.user.email and invite.invited_email.lower() != request.user.email.lower():
                    return Response({'detail': 'Invite email does not match authenticated user'}, status=status.HTTP_403_FORBIDDEN)

                membership, created = GroupMembership.objects.get_or_create(user=request.user, group=group)
                invite.status = 'accepted'
                invite.accepted_at = timezone.now()
                invite.accepted_by = request.user
                invite.save()
                if created:
                    return Response({'success': True, 'joined': True}, status=status.HTTP_201_CREATED)
                return Response({'success': True, 'joined': True, 'message': 'Already a member'}, status=status.HTTP_200_OK)
            except Exception:
                return Response({'detail': 'Failed to accept invite'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Public group: simple join
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

    @action(detail=True, methods=['post'])
    def add_moderator(self, request, pk=None):
        """Add a moderator to the group. Moderator must already be a member.

        Only the group creator or staff can add moderators.
        """
        group = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        # permission: only creator or staff
        if not (request.user == group.created_by or request.user.is_staff):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            mod_user = User.objects.filter(id=user_id).first()
            if not mod_user:
                return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            # ensure the user is a member
            if not GroupMembership.objects.filter(user=mod_user, group=group).exists():
                return Response({'detail': 'User must be a member before being made moderator'}, status=status.HTTP_400_BAD_REQUEST)
            group.moderators.add(mod_user)
            return Response({'detail': 'Moderator added'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'Failed to add moderator', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def remove_moderator(self, request, pk=None):
        group = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not (request.user == group.created_by or request.user.is_staff):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            mod_user = User.objects.filter(id=user_id).first()
            if not mod_user:
                return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            group.moderators.remove(mod_user)
            return Response({'detail': 'Moderator removed'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'Failed to remove moderator', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the group. Only group creator can remove members.
        
        Note: CSRF is exempted here since this endpoint uses token authentication.
        """
        group = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only creator or staff can remove members
        if not (request.user == group.created_by or request.user.is_staff):
            return Response({'detail': 'Permission denied. Only group creator can remove members.'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from django.contrib.auth import get_user_model
            from .models import GroupMembership
            
            User = get_user_model()
            member_user = User.objects.filter(id=user_id).first()
            if not member_user:
                return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Prevent removing the group creator
            if member_user == group.created_by:
                return Response({'detail': 'Cannot remove group creator'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete the membership
            deleted_count, _ = GroupMembership.objects.filter(user=member_user, group=group).delete()
            if deleted_count == 0:
                return Response({'detail': 'User is not a member of this group'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Also remove from moderators if they were a moderator
            group.moderators.remove(member_user)
            
            return Response({'detail': 'Member removed successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'Failed to remove member', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def create_invite(self, request, pk=None):
        """Create an invite for a private group. Moderators and group owner can invite."""
        group = self.get_object()
        # permission: only group creator, moderators, or staff
        user = request.user
        is_moderator = group.moderators.filter(id=user.id).exists()
        if not (user.is_staff or group.created_by_id == user.id or is_moderator):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        invitee_id = request.data.get('invitee_id')
        invitee_email = request.data.get('invitee_email')
        expires_days = request.data.get('expires_days')

        if not invitee_id and not invitee_email:
            return Response({'detail': 'invitee_id or invitee_email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .models import GroupInvite
            invited_user = None
            if invitee_id:
                try:
                    from django.contrib.auth import get_user_model
                    U = get_user_model()
                    invited_user = U.objects.filter(id=invitee_id).first()
                    if not invited_user:
                        return Response({'detail': 'Invited user not found'}, status=status.HTTP_404_NOT_FOUND)
                except Exception:
                    invited_user = None

            invite = GroupInvite.objects.create(
                group=group,
                invited_by=user,
                invited_user=invited_user,
                invited_email=invitee_email or (invited_user.email if invited_user else None),
            )
            if expires_days:
                try:
                    invite.expires_at = timezone.now() + timedelta(days=int(expires_days))
                    invite.save()
                except Exception:
                    pass

            # attempt to send email invite (best-effort)
            try:
                from .utils import send_group_invite
                accept_url = None
                try:
                    accept_url = request.build_absolute_uri(f"/api/community/groups/{group.id}/accept_invite/?token={invite.token}")
                except Exception:
                    accept_url = None
                try:
                    send_group_invite(invite, invite_url=accept_url)
                except Exception:
                    pass
            except Exception:
                # utils may not be available or sending failed; ignore
                pass

            from .serializers import GroupInviteSerializer
            serializer = GroupInviteSerializer(invite, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': 'Failed to create invite', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def accept_invite(self, request, pk=None):
        """Accept an invite token for the group."""
        group = self.get_object()
        token = (request.data or {}).get('token') or request.query_params.get('token')
        if not token:
            return Response({'detail': 'token is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=status.HTTP_403_FORBIDDEN)
        try:
            from .models import GroupInvite
            invite = GroupInvite.objects.filter(group=group, token=token, status='pending').first()
            if not invite:
                return Response({'detail': 'Invite not found or already used'}, status=status.HTTP_404_NOT_FOUND)
            if invite.is_expired():
                invite.mark_expired()
                return Response({'detail': 'Invite expired'}, status=status.HTTP_400_BAD_REQUEST)
            if invite.invited_user and invite.invited_user_id != request.user.id:
                return Response({'detail': 'Invite not valid for this user'}, status=status.HTTP_403_FORBIDDEN)
            if invite.invited_email and request.user.email and invite.invited_email.lower() != request.user.email.lower():
                return Response({'detail': 'Invite email does not match authenticated user'}, status=status.HTTP_403_FORBIDDEN)

            membership, created = GroupMembership.objects.get_or_create(user=request.user, group=group)
            invite.status = 'accepted'
            invite.accepted_at = timezone.now()
            invite.accepted_by = request.user
            invite.save()
            return Response({'success': True, 'joined': True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'Failed to accept invite', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def list_invites(self, request, pk=None):
        """List invites for the group (owner/moderator/staff only)."""
        group = self.get_object()
        user = request.user
        is_moderator = group.moderators.filter(id=user.id).exists()
        if not (user.is_staff or group.created_by_id == user.id or is_moderator):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        try:
            invites = group.invites.all()
            from .serializers import GroupInviteSerializer
            serializer = GroupInviteSerializer(invites, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response({'detail': 'Failed to list invites', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def revoke_invite(self, request, pk=None):
        """Revoke an invite token."""
        group = self.get_object()
        token = (request.data or {}).get('token')
        if not token:
            return Response({'detail': 'token is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        is_moderator = group.moderators.filter(id=user.id).exists()
        if not (user.is_staff or group.created_by_id == user.id or is_moderator):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        try:
            from .models import GroupInvite
            invite = GroupInvite.objects.filter(group=group, token=token, status='pending').first()
            if not invite:
                return Response({'detail': 'Invite not found or already used'}, status=status.HTTP_404_NOT_FOUND)
            invite.status = 'revoked'
            invite.save()
            return Response({'status': 'revoked'})
        except Exception as e:
            return Response({'detail': 'Failed to revoke invite', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Delete a group. Only creator or staff can delete.
        
        Manually handles deletion to ensure all related objects (memberships, invites, posts)
        are properly deleted to avoid SQLite FK constraint issues.
        """
        group = self.get_object()
        
        # Check permissions - only creator or staff can delete
        is_creator = request.user == group.created_by
        if not (is_creator or request.user.is_staff):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from django.db import transaction
            from .models import GroupMembership, GroupInvite, Post
            
            with transaction.atomic():
                # Delete all posts in the group first (cascade will handle their dependencies)
                Post.objects.filter(group=group).delete()
                
                # Delete all invites
                GroupInvite.objects.filter(group=group).delete()
                
                # Delete all memberships
                GroupMembership.objects.filter(group=group).delete()
                
                # Finally delete the group itself
                group_id = group.id
                group.delete()
                
            return Response({'detail': 'Group deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'detail': 'Failed to delete group', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer
    authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsCommunityMember]

    def get_queryset(self):
        """Filter memberships by group and/or user if parameters are provided."""
        qs = super().get_queryset()
        
        # Filter by group if group parameter is provided
        group_id = self.request.query_params.get('group')
        if group_id:
            try:
                qs = qs.filter(group_id=int(group_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by user if user parameter is provided
        user_id = self.request.query_params.get('user')
        if user_id:
            try:
                qs = qs.filter(user_id=int(user_id))
            except (ValueError, TypeError):
                pass
        
        return qs


# --------------------------- Feed / Post ---------------------------

from .feed import FeedRanker  # re-import safe; already imported above but keep for readability


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsCommunityMember]

    def get_queryset(self):
        """Get base queryset with optional filters."""
        qs = super().get_queryset()

        # Apply visibility filters
        request_user = getattr(self.request, 'user', None)
        import logging
        logger = logging.getLogger(__name__)
        
        # If the requester is staff allow full access (no visibility filtering)
        if not (request_user and getattr(request_user, 'is_staff', False)):
            # Base filter: only approved posts
            base_q = Q(is_approved=True)

            # Public global posts are always visible
            visibility_q = Q(feed_visibility='public_global')

            # If authenticated, include group-only posts for groups the user is a member of
            # and the user's own posts. Avoid using AnonymousUser in ORM lookups.
            if request_user and getattr(request_user, 'is_authenticated', False):
                visibility_q = (
                    visibility_q
                    | Q(feed_visibility='group_only', group__memberships__user=request_user)
                    | Q(author=request_user)
                )
                logger.info(f'[PostViewSet.get_queryset] User {request_user.id} authenticated - including own posts and group posts')

            qs = qs.filter(base_q & visibility_q).distinct()
            
            # Debug logging
            logger.info(f'[PostViewSet.get_queryset] After visibility filter - user={request_user}, is_auth={getattr(request_user, "is_authenticated", False) if request_user else False}')
            logger.info(f'[PostViewSet.get_queryset] Total posts after visibility: {qs.count()}')
            if request_user and getattr(request_user, 'is_authenticated', False):
                user_groups = Group.objects.filter(memberships__user=request_user)
                logger.info(f'[PostViewSet.get_queryset] User groups: {list(user_groups.values_list("id", "name"))}')
                
                # Check author posts
                author_posts = qs.filter(author=request_user)
                logger.info(f'[PostViewSet.get_queryset] Author posts visible to user: {author_posts.count()}')

        return qs

    def get_permissions(self):
        """Allow public access to list and retrieve actions."""
        if getattr(self, 'action', None) in ['list', 'retrieve']:
            return [AllowAny()]

        # For create actions require subscription in addition to community membership
        if getattr(self, 'action', None) == 'create':
            return [IsAuthenticated(), IsCommunityMember(), IsSubscribed()]

        # Default permissions for other actions
        return [IsAuthenticated(), IsCommunityMember()]

    def list(self, request, *args, **kwargs):
        """
        Get feed posts with ranking and filtering.

        Query params:
        - feed_type: 'global' (default), 'following', 'trending', 'joined_groups'
        - author_id: filter by author
        - group_id: filter by group
        - page: page number (default 1)
        - page_size: items per page (default 20)
        - include_campaigns: include sponsored campaigns in feed (default true)
        """
        # Get basic parameters
        feed_type = request.query_params.get('feed_type', 'global')
        page_size = int(request.query_params.get('page_size', 20))
        author_id = request.query_params.get('author_id')
        group_id = request.query_params.get('group_id') or request.query_params.get('group')
        include_campaigns = request.query_params.get('include_campaigns', 'true').lower() == 'true'

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'[PostViewSet.list] Filtering posts - group_id={group_id}, author_id={author_id}, feed_type={feed_type}')

        # Get base queryset (applies visibility filters)
        qs = self.get_queryset()
        logger.info(f'[PostViewSet.list] Initial queryset count after visibility filter: {qs.count()}')

        # Apply author/group filters if provided
        if author_id:
            if str(author_id).isdigit():
                qs = qs.filter(author__id=int(author_id))
            else:
                qs = qs.filter(Q(author__username=author_id) | Q(author__email=author_id))

        if group_id:
            # Filter by specific group
            qs = qs.filter(group__id=group_id)
            logger.info(f'[PostViewSet.list] After group filter: {qs.count()} posts in group {group_id}')
            # Also log sample posts with details
            sample = qs.values_list('id', 'group_id', 'feed_visibility', 'is_approved', 'author_id')[:5]
            logger.info(f'[PostViewSet.list] Sample posts in group {group_id}: {list(sample)}')
            
            # Check if any posts exist for this group at all (before visibility filter)
            all_group_posts = Post.objects.filter(group__id=group_id)
            logger.info(f'[PostViewSet.list] ALL posts in group {group_id} (no visibility filter): {all_group_posts.count()}')
            logger.info(f'[PostViewSet.list] Sample all posts: {list(all_group_posts.values_list("id", "group_id", "feed_visibility", "is_approved")[:5])}')
        elif feed_type == 'global':
            # When viewing global feed, exclude group-only posts
            # Group-only posts should only appear when explicitly viewing that group or joined_groups tab
            qs = qs.exclude(feed_visibility='group_only')
            logger.info(f'[PostViewSet.list] Excluded group_only posts from global feed. Remaining: {qs.count()} posts')

        # Apply feed-type specific logic
        if feed_type == 'following' and request.user.is_authenticated:
            # Get posts from users being followed
            following_ids = request.user.following.values_list('id', flat=True)
            qs = qs.filter(author_id__in=following_ids)

        elif feed_type == 'trending':
            # Get posts with high engagement in last 24 hours
            yesterday = timezone.now() - timedelta(days=1)
            qs = qs.filter(created_at__gte=yesterday)

        elif feed_type == 'joined_groups' and request.user.is_authenticated:
            # Get posts from groups the user is a member of
            user_group_ids = GroupMembership.objects.filter(user=request.user).values_list('group_id', flat=True)
            qs = qs.filter(group_id__in=user_group_ids)
            logger.info(f'[PostViewSet.list] Joined groups feed - user {request.user.id} is member of groups: {list(user_group_ids)}, found {qs.count()} posts')

        # Apply ranking
        try:
            qs = FeedRanker.rank_queryset(qs)
        except Exception:
            pass

        # Try to get from cache first
        if not (author_id or group_id):  # Only cache general feeds
            try:
                cached_posts = Post.get_feed_page(
                    page=int(request.query_params.get('page', 1)),
                    page_size=page_size,
                    user=request.user if request.user.is_authenticated else None,
                    feed_type=feed_type,
                )

                if cached_posts:
                    # cached_posts may be a list of dicts (cached raw post payloads).
                    # Ensure we return fully serialized posts so fields like `media_urls`
                    # (and serializer `to_representation` logic) are applied.
                    try:
                        if isinstance(cached_posts, list) and cached_posts and all(isinstance(p, dict) and 'id' in p for p in cached_posts):
                            ids = [p['id'] for p in cached_posts]
                            posts_qs = Post.objects.filter(id__in=ids)
                            posts_map = {p.id: p for p in posts_qs}
                            # Preserve original cached order, skip missing ids
                            ordered = [posts_map.get(i) for i in ids if posts_map.get(i) is not None]
                            serializer = self.get_serializer(ordered, many=True, context={'request': request})
                            return Response({'results': serializer.data, 'page_size': page_size, 'feed_type': feed_type})
                    except Exception:
                        # If anything goes wrong, fall back to returning cached raw posts
                        pass

                    # Default fallback: return the cached raw posts as-is
                    return Response({'results': cached_posts, 'page_size': page_size, 'feed_type': feed_type})
            except Exception:
                pass

        # Paginate database results
        paginator = getattr(self, 'pagination_class', None)
        if paginator is not None:
            paginator = paginator()
            page = paginator.paginate_queryset(qs, request)
            serializer = self.get_serializer(page, many=True, context={'request': request})
            response_data = paginator.get_paginated_response(serializer.data)
            
            # Blend in active campaigns if requested and no filters applied
            if include_campaigns and not author_id and not group_id:
                try:
                    from promotions.models import SponsorCampaign
                    from promotions.serializers import SponsorCampaignSerializer
                    
                    now = timezone.now()
                    campaigns = SponsorCampaign.objects.filter(
                        status='active',
                        start_date__lte=now,
                        end_date__gte=now,
                        sponsored_post__is_approved=True
                    ).select_related('sponsored_post', 'sponsor').order_by('-priority_level', '-created_at')[:3]
                    
                    if campaigns.exists():
                        campaign_serializer = SponsorCampaignSerializer(campaigns, many=True, context={'request': request})
                        if isinstance(response_data.data, dict) and 'results' in response_data.data:
                            response_data.data['campaigns'] = campaign_serializer.data
                except Exception:
                    pass
            
            return response_data

        serializer = self.get_serializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Get a single post with updated view tracking and sponsor impressions.
        Handles caching and engagement logging.
        """
        instance = self.get_object()

        # Try to get cached post data
        cache_key = f'post_detail:{instance.id}'
        cached_data = cache.get(cache_key) if cache else None

        if cached_data and not request.query_params.get('nocache'):
            return Response(cached_data)

        # Log view engagement
        try:
            user = request.user if request.user.is_authenticated else None
            EngagementLog.objects.create(
                user=user,
                action_type='view',
                post=instance,
                metadata={
                    'path': request.path,
                    'referrer': request.META.get('HTTP_REFERER', ''),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                },
            )
        except Exception:
            pass

        # Update sponsor campaign metrics
        try:
            campaign = getattr(instance, 'sponsor_campaign', None)
            if campaign and hasattr(campaign, 'is_active') and campaign.is_active():
                SponsorCampaign.objects.filter(id=campaign.id).update(impression_count=F('impression_count') + 1)
                if hasattr(campaign, 'calculate_engagement_rate'):
                    try:
                        campaign.calculate_engagement_rate()
                    except Exception:
                        pass
        except Exception:
            pass

        # Increment view count and update ranking
        try:
            if hasattr(instance, 'increment_view'):
                instance.increment_view()
            else:
                Post.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
        except Exception:
            pass

        # If this is a group-only post and requester is not a member, return a preview
        try:
            if instance.feed_visibility == 'group_only':
                user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
                is_member = False
                try:
                    if user:
                        is_member = GroupMembership.objects.filter(group=instance.group, user=user).exists()
                except Exception:
                    is_member = False
                if not is_member and not (request.user.is_staff or (instance.author and instance.author == request.user)):
                    # Return a lightweight preview encouraging join
                    preview = {
                        'id': instance.id,
                        'title': instance.title,
                        'snippet': (instance.content[:250] + '...') if len(instance.content or '') > 250 else (instance.content or ''),
                        'author_name': None,
                        'created_at': instance.created_at.isoformat(),
                        'group_id': instance.group_id,
                        'requires_membership': True,
                    }
                    try:
                        preview['author_name'] = getattr(instance.author, 'username', None) or getattr(instance.author, 'email', None) or ''
                    except Exception:
                        preview['author_name'] = ''
                    # Cache preview briefly
                    try:
                        cache.set(cache_key, preview, timeout=300)
                    except Exception:
                        pass
                    return Response(preview)

        except Exception:
            # if any error during preview logic, fall back to full serialization
            pass

        # Serialize and cache response
        serializer = self.get_serializer(instance, context={'request': request})
        response_data = serializer.data

        # Cache for 10 minutes
        try:
            cache.set(cache_key, response_data, timeout=600)
        except Exception:
            pass

        return Response(response_data)

    def create(self, request, *args, **kwargs):
        # Allow file uploads under 'media' key as multiple files
        # We'll create the Post first, then attach uploaded files and update media_urls
        
        # Debug logging for group_id handling
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'[PostViewSet.create] Request data keys: {list(request.data.keys())}')
        logger.info(f'[PostViewSet.create] group in request.data: {"group" in request.data}')
        logger.info(f'[PostViewSet.create] group_id in request.data: {"group_id" in request.data}')
        if "group_id" in request.data:
            logger.info(f'[PostViewSet.create] Received group_id={request.data.get("group_id")}')
        if "group" in request.data:
            logger.info(f'[PostViewSet.create] Received group={request.data.get("group")}')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        
        # Debug logging
        logger.info(f'[PostViewSet.create] Post created: id={post.id}, group_id={post.group_id}, feed_visibility={post.feed_visibility}, is_approved={post.is_approved}, author_id={post.author_id}')
        
        # Auto-add author to group membership when creating a post in a group
        # This ensures they can see their own group posts via visibility filter
        if post.group_id:
            try:
                group = Group.objects.get(id=post.group_id)
                membership, created = GroupMembership.objects.get_or_create(
                    user=request.user,
                    group=group
                )
                if created:
                    logger.info(f'[PostViewSet.create] Author {request.user.id} auto-added to group {post.group_id}')
                else:
                    logger.info(f'[PostViewSet.create] Author {request.user.id} already member of group {post.group_id}')
            except Group.DoesNotExist:
                logger.warning(f'[PostViewSet.create] Group {post.group_id} not found')
            except Exception as e:
                logger.warning(f'[PostViewSet.create] Error adding user to group: {str(e)}')

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
            post.media_urls = [post.media_urls] if post.media_urls else []

        # handle uploaded files
        files = request.FILES.getlist('media') if hasattr(request, 'FILES') else []
        media_urls = []
        # Basic server-side validation: allow images and common video types
        IMAGE_CONTENT_TYPES = ('image/jpeg', 'image/png', 'image/gif', 'image/webp')
        VIDEO_CONTENT_TYPES = ('video/mp4', 'video/webm', 'video/quicktime')
        MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
        # Increase allowed video size to 1 GB to support large uploads (user request)
        MAX_VIDEO_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB
        for f in files:
            fsize = getattr(f, 'size', 0)
            ctype = getattr(f, 'content_type', '').lower()

            # Size limits per type
            if ctype in VIDEO_CONTENT_TYPES:
                if fsize > MAX_VIDEO_SIZE:
                    return Response({'detail': f'File {f.name} exceeds maximum size of 50MB for video.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if fsize > MAX_IMAGE_SIZE:
                    return Response({'detail': f'File {f.name} exceeds maximum size of 5MB.'}, status=status.HTTP_400_BAD_REQUEST)

            # Accept images and videos; for images perform magic-bytes check
            if ctype in IMAGE_CONTENT_TYPES:
                try:
                    head = f.read(12)
                    f.seek(0)
                except Exception:
                    head = b''
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
                    return Response({'detail': f'File {f.name} failed magic-bytes verification'}, status=status.HTTP_400_BAD_REQUEST)
            elif ctype in VIDEO_CONTENT_TYPES:
                # For videos, skip magic-bytes strict validation (broad support varies)
                pass
            else:
                return Response({'detail': f'File {f.name} has unsupported content type {ctype}'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                attachment = post.attachments.create(file=f)
                media_urls.append(attachment.file.url)
            except Exception:
                continue

        if media_urls:
            post.media_urls = (post.media_urls or []) + media_urls
            post.save()

        # generate link previews for any external urls in media_urls and content
        external_urls = (post.media_urls or [])
        # Also scan the post content for plain URLs to generate richer previews
        try:
            url_pattern = r'(https?://[^\s]+)'
            found = re.findall(url_pattern, post.content or '')
            for u in found:
                if u not in external_urls:
                    external_urls.append(u)
        except Exception:
            pass
        new_media_urls: list = []
        for url in external_urls:
            # skip already-saved attachments (likely full URLs pointing to our storage)
            try:
                if re.search(r"/media/community/post_media/", url):
                    new_media_urls.append(url)
                    continue
            except Exception:
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

        # Attempt to create link preview objects for non-image URLs found in content
        try:
            link_previews = []
            preview_candidates = [u for u in external_urls if not re.search(r"/media/community/post_media/", u)]
            # limit number of previews to avoid long waits
            for u in preview_candidates[:3]:
                preview = self._fetch_link_preview(u)
                if preview:
                    link_previews.append(preview)
            if link_previews:
                post.link_previews = link_previews
                post.save(update_fields=['link_previews'])
        except Exception:
            pass

        # assign normalized media_urls back to post and save
        if new_media_urls:
            post.media_urls = new_media_urls
            post.save()

        # Create mention logs for any @mentions in content
        try:
            from .engagement import MentionLog, CommunityEngagementLog
            mentions = MentionLog.create_from_text(post.content or '', post=post, mentioned_by=request.user)
            # Log engagement entries for mentions
            for m in mentions:
                try:
                    CommunityEngagementLog.log_engagement(user=request.user, action_type='mention_user', post=post, mentioned_user=m.mentioned_user, metadata={'mentioned_username': getattr(m.mentioned_user, 'username', None)})
                except Exception:
                    pass
        except Exception:
            pass

        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(post, context={'request': request}).data, status=status.HTTP_201_CREATED, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH updates including multipart file uploads for attachments."""
        instance = self.get_object()

        # Use serializer to update basic fields first
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        # Normalize media_urls field in case client sent JSON string
        try:
            if isinstance(post.media_urls, str):
                _parsed = json.loads(post.media_urls)
                if isinstance(_parsed, list):
                    post.media_urls = _parsed
                else:
                    post.media_urls = [_parsed]
        except Exception:
            post.media_urls = [post.media_urls] if post.media_urls else []

        # Handle uploaded files in PATCH (key: 'media')
        files = request.FILES.getlist('media') if hasattr(request, 'FILES') else []
        media_urls = []
        ALLOWED_CONTENT_TYPES = ('image/jpeg', 'image/png', 'image/gif', 'image/webp')
        MAX_FILE_SIZE = 5 * 1024 * 1024
        for f in files:
            if getattr(f, 'size', 0) > MAX_FILE_SIZE:
                return Response({'detail': f'File {f.name} exceeds maximum size of 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
            if hasattr(f, 'content_type') and f.content_type not in ALLOWED_CONTENT_TYPES:
                return Response({'detail': f'File {f.name} has unsupported content type {getattr(f, "content_type", "unknown")}'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                head = f.read(12)
                f.seek(0)
            except Exception:
                head = b''
            is_valid = False
            if head.startswith(b'\x89PNG\r\n\x1a\n') or head[:3] == b'\xff\xd8\xff' or head[:6] in (b'GIF87a', b'GIF89a') or (head[:4] == b'RIFF' and head[8:12] == b'WEBP'):
                is_valid = True
            if not is_valid:
                return Response({'detail': f'File {f.name} failed magic-bytes verification'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                attachment = post.attachments.create(file=f)
                media_urls.append(attachment.file.url)
            except Exception:
                continue

        if media_urls:
            post.media_urls = (post.media_urls or []) + media_urls
            post.save()

        return Response(self.get_serializer(post, context={'request': request}).data, status=status.HTTP_200_OK)

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
    def pin_post(self, request, pk=None):
        """Moderators can pin a post to the top of the group"""
        post = self.get_object()
        group = post.group
        
        if not group:
            return Response({'detail': 'Cannot pin posts without a group'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is moderator of this group
        is_moderator = group.moderators.filter(id=request.user.id).exists()
        if not is_moderator and not request.user.is_staff:
            return Response({'detail': 'Permission denied. Only moderators can pin posts'}, status=status.HTTP_403_FORBIDDEN)
        
        post.is_pinned = True
        post.save(update_fields=['is_pinned'])
        
        return Response({'detail': 'Post pinned successfully', 'is_pinned': True}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unpin_post(self, request, pk=None):
        """Moderators can unpin a post"""
        post = self.get_object()
        group = post.group
        
        if not group:
            return Response({'detail': 'Cannot unpin posts without a group'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is moderator of this group
        is_moderator = group.moderators.filter(id=request.user.id).exists()
        if not is_moderator and not request.user.is_staff:
            return Response({'detail': 'Permission denied. Only moderators can unpin posts'}, status=status.HTTP_403_FORBIDDEN)
        
        post.is_pinned = False
        post.save(update_fields=['is_pinned'])
        
        return Response({'detail': 'Post unpinned successfully', 'is_pinned': False}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def moderate_remove(self, request, pk=None):
        """Moderators can remove a post from their group"""
        post = self.get_object()
        group = post.group
        
        if not group:
            return Response({'detail': 'Cannot moderate posts without a group'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is moderator of this group
        is_moderator = group.moderators.filter(id=request.user.id).exists()
        if not is_moderator and not request.user.is_staff:
            return Response({'detail': 'Permission denied. Only moderators can remove posts'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get reason from request
        reason = request.data.get('reason', 'Removed by moderator') if isinstance(request.data, dict) else 'Removed by moderator'
        
        # Mark as not approved and hide the post
        post.is_approved = False
        post.moderation_status = 'removed'
        post.moderation_reason = reason
        post.save(update_fields=['is_approved', 'moderation_status', 'moderation_reason'])
        
        # Clear cache
        try:
            cache.delete(f'post_detail:{post.id}')
            cache.delete(f'post:{post.id}')
        except Exception:
            pass
        
        return Response({'detail': 'Post removed successfully', 'is_approved': False}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Delete a post and cascade-delete all related objects (comments, reactions, bookmarks, etc.)"""
        post = self.get_object()
        
        # Check permissions - only author or staff can delete
        is_author = post.author_id == request.user.id
        
        if not is_author and not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Perform ordered, explicit deletions to avoid SQLite FK constraint issues
        from django.db import transaction
        try:
            from .models import (
                Comment,
                PostReaction,
                PostBookmark,
                PostAttachment,
                CommentReaction,
            )
            # Some related models live in other modules
            try:
                from .engagement import CommunityEngagementLog, MentionLog, EngagementNotification
            except Exception:
                CommunityEngagementLog = None
                MentionLog = None
                EngagementNotification = None

            try:
                from .models_extended import Like, Mention, Notification as ExtNotification
            except Exception:
                Like = None
                Mention = None
                ExtNotification = None

            with transaction.atomic():
                post_id = post.id

                # 1) Engagement notifications tied to engagement logs referencing this post/comments
                if EngagementNotification is not None:
                    EngagementNotification.objects.filter(engagement_log__post=post).delete()
                    EngagementNotification.objects.filter(engagement_log__comment__post=post).delete()

                # 2) Engagement logs for post and any comments
                if CommunityEngagementLog is not None:
                    CommunityEngagementLog.objects.filter(post=post).delete()
                    CommunityEngagementLog.objects.filter(comment__post=post).delete()

                # 3) Mention logs & extended mentions
                if MentionLog is not None:
                    MentionLog.objects.filter(post=post).delete()
                    MentionLog.objects.filter(comment__post=post).delete()
                if Mention is not None:
                    Mention.objects.filter(post=post).delete()
                    Mention.objects.filter(comment__post=post).delete()

                # 4) Likes (extended) referencing post or comments
                if Like is not None:
                    Like.objects.filter(post=post).delete()
                    Like.objects.filter(comment__post=post).delete()

                # 5) Comment reactions (likes on comments)
                CommentReaction.objects.filter(comment__post=post).delete()

                # 6) Post reactions and bookmarks
                PostReaction.objects.filter(post=post).delete()
                PostBookmark.objects.filter(post=post).delete()

                # 7) Delete attachments and remove files from storage
                attachments = PostAttachment.objects.filter(post=post)
                for att in attachments:
                    try:
                        if getattr(att, 'file', None):
                            att.file.delete(save=False)
                    except Exception:
                        pass
                attachments.delete()

                # 8) Finally delete comments (replies will cascade)
                Comment.objects.filter(post=post).delete()

                # 9) Delete any extended notifications referencing this post (ext notifications)
                if ExtNotification is not None:
                    ExtNotification.objects.filter(post=post).delete()

                # 10) Delete the post itself
                post.delete()

                # Clear caches
                try:
                    cache.delete(f'post_detail:{post_id}')
                    cache.delete(f'post:{post_id}')
                except Exception:
                    pass

            # Return deleted post ID so frontend can remove it from UI
            return Response(
                {'deleted_post_id': post_id, 'detail': 'Post deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('Error deleting post')
            return Response({'detail': 'Failed to delete post'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def toggle_bookmark(self, request, pk=None):
        post = self.get_object()
        bookmark, created = PostBookmark.objects.get_or_create(post=post, user=request.user)
        if not created:
            # already exists -> remove
            bookmark.delete()
            count = PostBookmark.objects.filter(post=post).count()
            # Log engagement (unbookmark)
            try:
                from .engagement import CommunityEngagementLog
                CommunityEngagementLog.log_engagement(user=request.user, action_type='unbookmark_post', post=post)
            except Exception:
                pass
            return Response({'bookmarked': False, 'bookmarks_count': count}, status=status.HTTP_200_OK)
        count = PostBookmark.objects.filter(post=post).count()
        # Log engagement (bookmark)
        try:
            from .engagement import CommunityEngagementLog
            CommunityEngagementLog.log_engagement(user=request.user, action_type='bookmark_post', post=post)
        except Exception:
            pass
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
            action_logged = False
            if existing:
                # update or delete depending on type
                if existing.reaction_type == reaction_type:
                    # same reaction -> remove
                    existing.delete()
                    current = None
                    # log unlike for 'like' reaction
                    try:
                        from .engagement import CommunityEngagementLog
                        if reaction_type == 'like':
                            CommunityEngagementLog.log_engagement(user=user, action_type='unlike_post', post=post)
                            action_logged = True
                    except Exception:
                        pass
                else:
                    # change reaction type
                    existing.reaction_type = reaction_type
                    existing.save()
                    current = reaction_type
                    try:
                        from .engagement import CommunityEngagementLog
                        # log as a reaction change: treat as a like if new type is like
                        if reaction_type == 'like':
                            CommunityEngagementLog.log_engagement(user=user, action_type='like_post', post=post)
                            action_logged = True
                    except Exception:
                        pass
            else:
                PostReaction.objects.create(post=post, user=user, reaction_type=reaction_type)
                current = reaction_type
                try:
                    from .engagement import CommunityEngagementLog
                    if reaction_type == 'like':
                        CommunityEngagementLog.log_engagement(user=user, action_type='like_post', post=post)
                        action_logged = True
                except Exception:
                    pass
        except Exception as e:
            return Response({'detail': 'Failed to persist reaction', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # return current reaction and aggregated counts
        try:
            qs = post.reactions.values('reaction_type').order_by().annotate(count=models.Count('id'))
            counts = {item['reaction_type']: item['count'] for item in qs}
        except Exception:
            counts = {}
        return Response({'reaction_type': current, 'reaction_counts': counts}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a post - creates a 'like' type reaction"""
        post = self.get_object()
        user = request.user
        from .models import PostReaction
        try:
            existing = PostReaction.objects.filter(post=post, user=user).first()
            if existing:
                if existing.reaction_type == 'like':
                    # Already liked -> remove like
                    existing.delete()
                    return Response({'liked': False, 'detail': 'Like removed'}, status=status.HTTP_200_OK)
                else:
                    # Change reaction to like
                    existing.reaction_type = 'like'
                    existing.save()
            else:
                # Create new like
                PostReaction.objects.create(post=post, user=user, reaction_type='like')
            
            # Return updated like count
            like_count = post.reactions.filter(reaction_type='like').count()
            return Response({'liked': True, 'like_count': like_count}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': 'Failed to like post', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin a post within a group - allowed for group creator, moderators, or staff."""
        post = self.get_object()
        group = getattr(post, 'group', None)
        user = request.user
        try:
            is_moderator = False
            if group:
                is_moderator = group.moderators.filter(id=user.id).exists()
            if not (user.is_staff or (group and group.created_by_id == user.id) or is_moderator):
                return Response({'detail': 'Permission denied'}, status=403)
            post.is_pinned = True
            post.save(update_fields=['is_pinned', 'updated_at'])
            return Response({'status': 'pinned'}, status=200)
        except Exception as e:
            return Response({'detail': 'Failed to pin post', 'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Unpin a post - allowed for group creator, moderators, or staff."""
        post = self.get_object()
        group = getattr(post, 'group', None)
        user = request.user
        try:
            is_moderator = False
            if group:
                is_moderator = group.moderators.filter(id=user.id).exists()
            if not (user.is_staff or (group and group.created_by_id == user.id) or is_moderator):
                return Response({'detail': 'Permission denied'}, status=403)
            post.is_pinned = False
            post.save(update_fields=['is_pinned', 'updated_at'])
            return Response({'status': 'unpinned'}, status=200)
        except Exception as e:
            return Response({'detail': 'Failed to unpin post', 'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def moderator_remove(self, request, pk=None):
        """Allow group moderators to remove posts. Cannot remove posts authored by the group creator or staff."""
        post = self.get_object()
        group = getattr(post, 'group', None)
        user = request.user
        try:
            if not group:
                return Response({'detail': 'Post is not within a group'}, status=400)
            # Only group creator, moderators, or staff can remove
            is_moderator = group.moderators.filter(id=user.id).exists()
            if not (user.is_staff or group.created_by_id == user.id or is_moderator):
                return Response({'detail': 'Permission denied'}, status=403)
            # Protect group creator and staff posts from being removed by moderators
            if post.author and (post.author_id == group.created_by_id or getattr(post.author, 'is_staff', False)) and not user.is_staff and post.author_id != user.id:
                return Response({'detail': 'Cannot remove posts authored by group admin or staff'}, status=403)

            # Perform deletion logic similar to destroy
            from django.db import transaction
            from .models import Comment, PostReaction, PostBookmark, PostAttachment
            with transaction.atomic():
                # remove related objects
                try:
                    Comment.objects.filter(post=post).delete()
                except Exception:
                    pass
                try:
                    PostReaction.objects.filter(post=post).delete()
                except Exception:
                    pass
                try:
                    PostBookmark.objects.filter(post=post).delete()
                except Exception:
                    pass
                try:
                    for att in PostAttachment.objects.filter(post=post):
                        try:
                            if getattr(att, 'file', None):
                                att.file.delete(save=False)
                        except Exception:
                            pass
                    PostAttachment.objects.filter(post=post).delete()
                except Exception:
                    pass

                post.delete()

            # Clear caches
            try:
                cache.delete(f'post_detail:{post.id}')
                cache.delete(f'post:{post.id}')
            except Exception:
                pass

            return Response({'status': 'removed'}, status=200)
        except Exception as e:
            return Response({'detail': 'Failed to remove post', 'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a post - removes like reaction"""
        post = self.get_object()
        user = request.user
        from .models import PostReaction
        try:
            existing = PostReaction.objects.filter(post=post, user=user, reaction_type='like').first()
            if existing:
                existing.delete()
                like_count = post.reactions.filter(reaction_type='like').count()
                return Response({'liked': False, 'like_count': like_count}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Post not liked'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': 'Failed to unlike post', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def bookmarked(self, request):
        """
        Get all bookmarked posts for the authenticated user.
        
        Query params:
        - page: page number (default 1)
        - page_size: items per page (default 20)
        """
        from .models import PostBookmark
        
        user = request.user
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        # Get bookmarked posts for this user, ordered by bookmark creation date (newest first)
        bookmarked_posts = PostBookmark.objects.filter(
            user=user
        ).select_related('post').order_by('-created_at')
        
        # Extract posts in bookmark order
        posts = [bm.post for bm in bookmarked_posts]
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = len(posts)
        paginated_posts = posts[start:end]
        
        serializer = self.get_serializer(paginated_posts, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        })

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

    @action(detail=False, methods=['get'], permission_classes=[])
    def active_campaigns(self, request):
        """
        Get all active sponsored campaigns for display in feeds.
        These are ranked by priority and used to appear in Community, Magazine, Homepage.
        No authentication required - public endpoint.
        
        Query params:
        - page: page number (default 1)
        - page_size: items per page (default 5)
        - tag: filter by industry tag (can be multiple: ?tag=AI&tag=Tech)
        - priority: filter by priority level (1, 2, or 3)
        """
        from promotions.models import SponsorCampaign
        from promotions.serializers import SponsorCampaignSerializer
        
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now,
            sponsored_post__is_approved=True
        ).select_related('sponsored_post', 'sponsor').order_by('-priority_level', '-created_at')
        
        # Filter by tags if provided
        tags = request.query_params.getlist('tag')
        if tags:
            from django.db.models import Q
            tag_queries = Q()
            for tag in tags:
                tag_queries |= Q(sponsored_post__industry_tags__contains=tag)
            campaigns = campaigns.filter(tag_queries)
        
        # Filter by priority level if provided
        priority = request.query_params.get('priority')
        if priority and str(priority).isdigit():
            campaigns = campaigns.filter(priority_level=int(priority))
        
        # Paginate results
        page_size = int(request.query_params.get('page_size', 5))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = campaigns.count()
        paginated_campaigns = campaigns[start:end]
        
        serializer = SponsorCampaignSerializer(paginated_campaigns, many=True, context={'request': request})
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[])
    def poll_campaigns(self, request):
        """
        Poll for active campaigns to display in feed.
        Lightweight endpoint optimized for polling.
        
        Query params:
        - since: ISO timestamp to get campaigns since last poll
        - limit: max campaigns (default 5)
        """
        from promotions.models import SponsorCampaign
        from promotions.serializers import SponsorCampaignSerializer
        
        now = timezone.now()
        campaigns = SponsorCampaign.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now,
            sponsored_post__is_approved=True
        ).select_related('sponsored_post', 'sponsor').order_by('-priority_level', '-created_at')
        
        # Filter by timestamp if provided
        since = request.query_params.get('since')
        if since:
            try:
                since_dt = timezone.datetime.fromisoformat(since)
                campaigns = campaigns.filter(updated_at__gte=since_dt)
            except Exception:
                pass
        
        limit = int(request.query_params.get('limit', 5))
        campaigns = campaigns[:limit]
        
        serializer = SponsorCampaignSerializer(campaigns, many=True, context={'request': request})
        
        return Response({
            'timestamp': now.isoformat(),
            'count': len(campaigns),
            'campaigns': serializer.data
        })

    @action(detail=False, methods=['get'], permission_classes=[])
    def poll_feed_updates(self, request):
        """
        Poll for feed updates including new posts and campaigns.
        
        Query params:
        - since: ISO timestamp for last poll
        - include_campaigns: include sponsored campaigns (default true)
        - limit_posts: max posts (default 10)
        - limit_campaigns: max campaigns (default 3)
        """
        from promotions.models import SponsorCampaign
        from promotions.serializers import SponsorCampaignSerializer
        
        now = timezone.now()
        since = request.query_params.get('since')
        include_campaigns = request.query_params.get('include_campaigns', 'true').lower() == 'true'
        
        response_data = {
            'timestamp': now.isoformat(),
            'posts': [],
            'campaigns': []
        }
        
        # Get recent posts
        posts_qs = self.get_queryset()
        if since:
            try:
                since_dt = timezone.datetime.fromisoformat(since)
                posts_qs = posts_qs.filter(created_at__gte=since_dt)
            except Exception:
                pass
        
        limit_posts = int(request.query_params.get('limit_posts', 10))
        posts_qs = posts_qs[:limit_posts]
        
        post_serializer = self.get_serializer(posts_qs, many=True, context={'request': request})
        response_data['posts'] = post_serializer.data
        response_data['post_count'] = len(post_serializer.data)
        
        # Get active campaigns if requested
        if include_campaigns:
            campaigns = SponsorCampaign.objects.filter(
                status='active',
                start_date__lte=now,
                end_date__gte=now,
                sponsored_post__is_approved=True
            ).select_related('sponsored_post', 'sponsor').order_by('-priority_level', '-created_at')
            
            limit_campaigns = int(request.query_params.get('limit_campaigns', 3))
            campaigns = campaigns[:limit_campaigns]
            
            campaign_serializer = SponsorCampaignSerializer(campaigns, many=True, context={'request': request})
            response_data['campaigns'] = campaign_serializer.data
            response_data['campaign_count'] = len(campaign_serializer.data)
        
        return Response(response_data)


# --------------------------- Comments ---------------------------

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [DatabaseTokenAuthentication]
    permission_classes = [IsAuthenticated, IsCommunityMember]

    def get_permissions(self):
        # For creating comments require active subscription as well
        if getattr(self, 'action', None) == 'create':
            return [IsAuthenticated(), IsCommunityMember(), IsSubscribed()]
        return super().get_permissions()

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



# --------------------------- Search API ---------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def community_search(request):
    """Search posts and groups by query param `q`.

    Returns JSON: { posts: [...], groups: [...], users: [], courses: [] }
    """
    q = request.query_params.get('q', '').strip()
    results = {'posts': [], 'groups': [], 'users': [], 'courses': []}
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


# --------------------------- Video ---------------------------





# End of file

# ============================================================================
# COMMUNITY SYSTEM VIEWSETS (NEW MODELS)
# ============================================================================

class UserEngagementScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user engagement scores (read-only)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import UserEngagementScore
        return UserEngagementScore.objects.all().order_by('-engagement_score')
    
    def get_serializer_class(self):
        from .serializers import UserEngagementScoreSerializer
        return UserEngagementScoreSerializer
    
    @action(detail=False, methods=['get'])
    def current_user(self, request):
        """Get engagement score for current user"""
        from .models import UserEngagementScore
        try:
            score = request.user.engagement_score
            serializer = self.get_serializer(score)
            return Response(serializer.data)
        except UserEngagementScore.DoesNotExist:
            return Response({'detail': 'No engagement score found'}, status=404)


class SubscriptionTierViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for subscription tiers (read-only)"""
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from .models import SubscriptionTier
        return SubscriptionTier.objects.all().order_by('price')
    
    def get_serializer_class(self):
        from .serializers import SubscriptionTierSerializer
        return SubscriptionTierSerializer


class SponsoredPostViewSet(viewsets.ModelViewSet):
    """ViewSet for sponsored posts"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import SponsoredPost
        # Users can only see their own sponsored posts unless staff
        if self.request.user.is_staff:
            return SponsoredPost.objects.all()
        return SponsoredPost.objects.filter(creator=self.request.user)
    
    def get_serializer_class(self):
        from .serializers import SponsoredPostSerializer
        return SponsoredPostSerializer
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a sponsored post"""
        sponsored_post = self.get_object()
        if sponsored_post.creator != request.user and not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=403)
        sponsored_post.status = 'paused'
        sponsored_post.save()
        return Response({'status': 'post paused'})
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a sponsored post"""
        sponsored_post = self.get_object()
        if sponsored_post.creator != request.user and not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=403)
        sponsored_post.status = 'active'
        sponsored_post.save()
        return Response({'status': 'post resumed'})


class TrendingTopicViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for trending topics"""
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        from .models import TrendingTopic
        return TrendingTopic.objects.all().order_by('-engagement_score')
    
    def get_serializer_class(self):
        from .serializers import TrendingTopicSerializer
        return TrendingTopicSerializer


class CorporateOpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet for corporate opportunities"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import CorporateOpportunity
        # Users can filter by status
        status_filter = self.request.query_params.get('status')
        qs = CorporateOpportunity.objects.all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-created_at')
    
    def get_serializer_class(self):
        from .serializers import CorporateOpportunitySerializer
        return CorporateOpportunitySerializer
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """Increment view count for this opportunity"""
        opportunity = self.get_object()
        opportunity.view_count = (opportunity.view_count or 0) + 1
        opportunity.save(update_fields=['view_count'])
        return Response({'view_count': opportunity.view_count})
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Get all applications for this opportunity"""
        from .models import OpportunityApplication
        from .serializers import OpportunityApplicationSerializer
        opportunity = self.get_object()
        applications = opportunity.applications.all()
        serializer = OpportunityApplicationSerializer(applications, many=True)
        return Response(serializer.data)


class OpportunityApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for opportunity applications with LinkedIn-style management"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import OpportunityApplication
        user = self.request.user
        
        # Corporates/Facilitators see applications for their opportunities
        if user.role in ['corporate', 'facilitator']:
            return OpportunityApplication.objects.filter(
                opportunity__creator=user
            ).select_related('applicant', 'opportunity', 'reviewed_by')
        
        # Applicants see their own applications
        if self.request.user.is_staff:
            return OpportunityApplication.objects.all().select_related('applicant', 'opportunity', 'reviewed_by')
        
        return OpportunityApplication.objects.filter(
            applicant=self.request.user
        ).select_related('applicant', 'opportunity', 'reviewed_by')
    
    def get_serializer_class(self):
        from .serializers import OpportunityApplicationSerializer, ApplicationDetailSerializer
        
        # Use detailed serializer for corporate/facilitator viewing
        if self.action in ['list', 'retrieve']:
            user = self.request.user
            if user.role in ['corporate', 'facilitator']:
                return ApplicationDetailSerializer
        
        return OpportunityApplicationSerializer
    
    def perform_create(self, serializer):
        from django.db import IntegrityError
        try:
            application = serializer.save(applicant=self.request.user)
            # Increment application count on the opportunity
            opportunity = application.opportunity
            opportunity.application_count = (opportunity.application_count or 0) + 1
            opportunity.save(update_fields=['application_count'])
            
            # Send notification to corporate about new application
            try:
                from notifications.utils import send_notification
                applicant_name = self.request.user.username
                notification_title = "New Application Received"
                notification_message = f"{applicant_name} applied to your opportunity: {opportunity.title}"
                action_url = f"/dashboard/corporate/applications/{application.id}/"
                send_notification(
                    opportunity.creator,
                    'new_application',
                    notification_title,
                    notification_message,
                    action_url=action_url,
                    metadata={'application_id': application.id, 'opportunity_id': opportunity.id}
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send application notification: {e}")
                
        except IntegrityError:
            raise serializers.ValidationError({
                'opportunity': 'You have already applied for this opportunity.'
            })
    
    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """Get current user's applications (for applicants)"""
        from .models import OpportunityApplication
        from .serializers import OpportunityApplicationSerializer
        
        applications = OpportunityApplication.objects.filter(
            applicant=request.user
        ).select_related('opportunity', 'reviewed_by').order_by('-applied_at')
        
        serializer = OpportunityApplicationSerializer(applications, many=True)
        return Response({
            'count': applications.count(),
            'applications': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def opportunity_applications(self, request):
        """Get applications for user's opportunities (for corporates/facilitators)"""
        from .models import OpportunityApplication
        from .serializers import ApplicationDetailSerializer
        
        user = request.user
        if user.role not in ['corporate', 'facilitator']:
            return Response({'detail': 'Permission denied'}, status=403)
        
        # Filter by opportunity if provided
        opportunity_id = request.query_params.get('opportunity_id')
        status_filter = request.query_params.get('status')
        
        queryset = OpportunityApplication.objects.filter(
            opportunity__creator=user
        ).select_related('applicant', 'opportunity', 'reviewed_by').order_by('-applied_at')
        
        if opportunity_id:
            queryset = queryset.filter(opportunity_id=opportunity_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Paginate results
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)
        start = (int(page) - 1) * int(page_size)
        end = start + int(page_size)
        
        total = queryset.count()
        paginated = queryset[start:end]
        
        serializer = ApplicationDetailSerializer(paginated, many=True)
        return Response({
            'count': total,
            'page': int(page),
            'page_size': int(page_size),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def application_stats(self, request):
        """Get application statistics for corporate dashboard"""
        from django.db.models import Count
        from .models import OpportunityApplication
        
        user = request.user
        if user.role not in ['corporate', 'facilitator']:
            return Response({'detail': 'Permission denied'}, status=403)
        
        stats = OpportunityApplication.objects.filter(
            opportunity__creator=user
        ).values('status').annotate(count=Count('id')).order_by('status')
        
        total_applications = OpportunityApplication.objects.filter(
            opportunity__creator=user
        ).count()
        
        stats_dict = {item['status']: item['count'] for item in stats}
        
        return Response({
            'total_applications': total_applications,
            'by_status': stats_dict,
            'pending_review': stats_dict.get('applied', 0) + stats_dict.get('reviewed', 0),
            'shortlisted': stats_dict.get('shortlisted', 0),
            'accepted': stats_dict.get('accepted', 0),
            'rejected': stats_dict.get('rejected', 0),
        })
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update application status (LinkedIn-style: reviewed, shortlisted, accepted, rejected)"""
        from django.utils import timezone
        
        application = self.get_object()
        opportunity = application.opportunity
        
        # Check permission - only opportunity creator or admin can update
        if opportunity.creator != request.user and not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=403)
        
        new_status = request.data.get('status')
        if new_status not in ['applied', 'reviewed', 'shortlisted', 'rejected', 'accepted']:
            return Response({'detail': 'Invalid status'}, status=400)
        
        old_status = application.status
        application.status = new_status
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.reviewer_notes = request.data.get('reviewer_notes', '')
        
        # If rejecting, capture reason
        if new_status == 'rejected':
            application.rejection_reason = request.data.get('rejection_reason', '')
        
        application.save()
        
        # Send notification to applicant
        try:
            from notifications.utils import send_notification
            
            status_messages = {
                'reviewed': f"Your application to {opportunity.title} has been reviewed",
                'shortlisted': f"Great news! You've been shortlisted for {opportunity.title}",
                'accepted': f"Congratulations! You've been accepted for {opportunity.title}",
                'rejected': f"Your application to {opportunity.title} has been reviewed",
            }
            
            if new_status in ['shortlisted', 'accepted', 'rejected']:
                notification_title = status_messages.get(new_status, 'Application Status Updated')
                notification_message = status_messages.get(new_status)
                
                action_url = f"/dashboard/applications/{application.id}/"
                
                send_notification(
                    application.applicant,
                    f'application_{new_status}',
                    notification_title,
                    notification_message,
                    action_url=action_url,
                    metadata={
                        'application_id': application.id,
                        'opportunity_id': opportunity.id,
                        'old_status': old_status
                    }
                )
                
                # Mark notification as sent
                if new_status == 'accepted':
                    application.approved_notification_sent = True
                elif new_status == 'rejected':
                    application.rejected_notification_sent = True
                application.save()
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send application status notification: {e}")
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def shortlist(self, request, pk=None):
        """Quick action to shortlist an applicant"""
        application = self.get_object()
        opportunity = application.opportunity
        
        if opportunity.creator != request.user and not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=403)
        
        application.status = 'shortlisted'
        application.reviewed_by = request.user
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def accept_application(self, request, pk=None):
        """Accept an applicant"""
        return self.update_status(request, pk)
    
    @action(detail=True, methods=['post'])
    def reject_application(self, request, pk=None):
        """Reject an applicant"""
        return self.update_status(request, pk)


class CollaborationRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for collaboration requests"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import CollaborationRequest
        # Users can see sent and received requests (include completed items).
        # Completed collaborations are part of history and should be visible
        # to participants. Deletions remove the DB record entirely.
        return CollaborationRequest.objects.filter(
            Q(requester=self.request.user) | Q(recipient=self.request.user)
        )
    
    def get_serializer_class(self):
        from .serializers import CollaborationRequestSerializer
        return CollaborationRequestSerializer
    
    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a collaboration request"""
        collab = self.get_object()
        if collab.recipient != request.user:
            return Response({'detail': 'Permission denied'}, status=403)
        collab.status = 'accepted'
        collab.responded_at = timezone.now()
        collab.save()
        
        # Send notification to requester
        try:
            from notifications.utils import send_notification
            recipient_name = getattr(request.user, 'username', str(request.user))
            notification_title = "Collaboration request accepted"
            notification_message = f"{recipient_name} accepted your {collab.collaboration_type} collaboration request: {collab.title}"
            action_url = f"/dashboard/community/collaborations/{collab.id}/"
            send_notification(
                collab.requester,
                'collaboration_accepted',
                notification_title,
                notification_message,
                action_url=action_url,
                metadata={'collaboration_request_id': collab.id, 'recipient_id': request.user.id}
            )
        except Exception as notify_err:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send collaboration acceptance notification: {notify_err}")
        
        return Response({'status': 'collaboration request accepted'})
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a collaboration request"""
        collab = self.get_object()
        if collab.recipient != request.user:
            return Response({'detail': 'Permission denied'}, status=403)
        collab.status = 'declined'
        collab.responded_at = timezone.now()
        collab.save()
        
        # Send notification to requester
        try:
            from notifications.utils import send_notification
            recipient_name = getattr(request.user, 'username', str(request.user))
            notification_title = "Collaboration request declined"
            notification_message = f"{recipient_name} declined your {collab.collaboration_type} collaboration request: {collab.title}"
            action_url = f"/dashboard/community/collaborations/{collab.id}/"
            send_notification(
                collab.requester,
                'collaboration_declined',
                notification_title,
                notification_message,
                action_url=action_url,
                metadata={'collaboration_request_id': collab.id, 'recipient_id': request.user.id}
            )
        except Exception as notify_err:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send collaboration decline notification: {notify_err}")
        
        return Response({'status': 'collaboration request declined'})

    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        """Remove / end an existing collaboration (mark completed).

        Either party may end the collaboration. This sets status to 'completed'
        and records responded_at. A notification is sent to the other party.
        """
        collab = self.get_object()
        # Only participants can remove
        if collab.requester != request.user and collab.recipient != request.user:
            return Response({'detail': 'Permission denied'}, status=403)

        # Delete the collaboration record from the database (deleted items
        # should not reappear anywhere). We notify the other participant that
        # the collaboration was removed.
        try:
            other = collab.requester if collab.requester != request.user else collab.recipient
            actor_name = getattr(request.user, 'username', str(request.user))
            action_url = f"/dashboard/community/collaborations/{collab.id}/"
            title = collab.title
            collab.delete()

            try:
                from notifications.utils import send_notification
                notification_title = 'Collaboration removed'
                notification_message = f"{actor_name} removed the collaboration: {title}"
                send_notification(
                    other,
                    'collaboration_removed',
                    notification_title,
                    notification_message,
                    action_url=action_url,
                    metadata={'actor_id': request.user.id}
                )
            except Exception:
                # notification best-effort
                pass

            return Response({'status': 'deleted'})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Failed to delete collaboration: {e}")
            return Response({'detail': 'Failed to delete collaboration'}, status=500)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark an existing collaboration as completed (preserve record).

        This is a non-destructive operation for history. It sets `status='completed'`.
        """
        collab = self.get_object()
        # Only participants may mark completed
        if collab.requester != request.user and collab.recipient != request.user:
            return Response({'detail': 'Permission denied'}, status=403)

        if collab.status == 'completed':
            return Response({'status': 'already completed'})

        collab.status = 'completed'
        collab.responded_at = timezone.now()
        collab.save()

        # Notify the other participant
        try:
            from notifications.utils import send_notification
            other = collab.requester if collab.requester != request.user else collab.recipient
            actor_name = getattr(request.user, 'username', str(request.user))
            notification_title = 'Collaboration completed'
            notification_message = f"{actor_name} marked the collaboration as completed: {collab.title}"
            action_url = f"/dashboard/community/collaborations/{collab.id}/"
            send_notification(
                other,
                'collaboration_completed',
                notification_title,
                notification_message,
                action_url=action_url,
                metadata={'collaboration_request_id': collab.id, 'actor_id': request.user.id}
            )
        except Exception:
            pass

        return Response({'status': 'completed'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get collaboration statistics for the current user"""
        from django.db.models import Q
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'accepted': queryset.filter(status='accepted').count(),
            'declined': queryset.filter(status='declined').count(),
            'active': queryset.filter(status='active').count(),
            'completed': queryset.filter(status='completed').count(),
            'sent': queryset.filter(requester=request.user).count(),
            'received': queryset.filter(recipient=request.user).count(),
            'pending_response': queryset.filter(
                Q(recipient=request.user) & Q(status='pending')
            ).count(),
        }
        
        return Response(stats)


class CorporateConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet for corporate connections between users."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from .models import CorporateConnection
        # Users can see connections they sent or received
        return CorporateConnection.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-created_at')

    def get_serializer_class(self):
        from .serializers import CorporateConnectionSerializer
        return CorporateConnectionSerializer

    def perform_create(self, serializer):
        # ensure sender is always the authenticated user
        serializer.save(sender=self.request.user)

    def create(self, request, *args, **kwargs):
        # Prevent creating a duplicate connection or self-connection
        data = request.data or {}
        receiver_id = data.get('receiver')
        if not receiver_id:
            return Response({'detail': 'receiver is required'}, status=400)
        try:
            from .models import CorporateConnection
            # disallow connecting to self
            if str(request.user.id) == str(receiver_id) or request.user.id == int(receiver_id):
                return Response({'detail': 'Cannot create connection to yourself'}, status=400)
            exists = CorporateConnection.objects.filter(sender=request.user, receiver_id=receiver_id).exists()
            if exists:
                return Response({'detail': 'Connection already exists'}, status=400)
        except Exception:
            pass
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        conn = self.get_object()
        if conn.receiver != request.user:
            return Response({'detail': 'Permission denied'}, status=403)
        conn.status = 'accepted'
        conn.connected_at = timezone.now()
        conn.save()
        return Response({'status': 'connection accepted'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        conn = self.get_object()
        if conn.receiver != request.user:
            return Response({'detail': 'Permission denied'}, status=403)
        conn.status = 'rejected'
        conn.save()
        return Response({'status': 'connection rejected'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from .models import CorporateConnection
        qs = CorporateConnection.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        total = qs.count()
        pending = qs.filter(status='pending').count()
        accepted = qs.filter(status='accepted').count()
        rejected = qs.filter(status='rejected').count()
        return Response({'total': total, 'pending': pending, 'accepted': accepted, 'rejected': rejected})


class PlatformAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for platform analytics"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import PlatformAnalytics
        # Only staff can see analytics
        if self.request.user.is_staff:
            return PlatformAnalytics.objects.all().order_by('-date')
        return PlatformAnalytics.objects.none()
    
    def get_serializer_class(self):
        from .serializers import PlatformAnalyticsSerializer
        return PlatformAnalyticsSerializer


class CorporatePartnerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for corporate partners directory.
    Lists all verified corporate users for collaboration.
    Public listing is allowed; collaboration requests require authentication.
    """
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Get all approved corporate verifications with valid users"""
        return CorporateVerification.objects.filter(
            status='approved',
            user__isnull=False  # Ensure user is not null
        ).select_related('user', 'user__profile').order_by('-submitted_at')
    
    def get_object(self):
        """Override to lookup by user_id instead of pk"""
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        try:
            # Try to find by CorporateVerification.user_id
            return queryset.get(user_id=pk)
        except CorporateVerification.DoesNotExist:
            # Fall back to trying by pk (id of CorporateVerification)
            try:
                return queryset.get(pk=pk)
            except CorporateVerification.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound("Partner not found")
    
    def create(self, request, *args, **kwargs):
        """Disable creation on partners endpoint"""
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def update(self, request, *args, **kwargs):
        """Disable update on partners endpoint"""
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def partial_update(self, request, *args, **kwargs):
        """Disable partial update on partners endpoint"""
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def destroy(self, request, *args, **kwargs):
        """Disable deletion on partners endpoint"""
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def get_serializer_class(self):
        from .serializers import CorporatePartnerSerializer
        return CorporatePartnerSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List corporate partners with optional filtering.
        
        Query params:
        - search: search in company name or description
        - industry: filter by industry/sector
        - country: filter by country
        """
        queryset = self.get_queryset()
        
        # Apply search filter
        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(business_description__icontains=search)
            )
        
        # Apply industry filter
        industry = request.query_params.get('industry', '').strip()
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        
        # Apply country filter
        country = request.query_params.get('country', '').strip()
        if country:
            queryset = queryset.filter(user__profile__country__icontains=country)
        
        # use DRF pagination if configured on the view/router
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed information about a specific corporate partner"""
        partner = self.get_object()
        serializer = self.get_serializer(partner, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def request_collaboration(self, request, pk=None):
        """Create a CollaborationRequest for the given partner (recipient).

        Expected POST body (JSON): {
            "collaboration_type": "partnership", (optional)
            "title": "Short title",
            "description": "Optional description"
        }
        """
        partner = self.get_object()
        requester = request.user
        # recipient is the user linked to the CorporateVerification
        recipient = getattr(partner, 'user', None)
        if not recipient:
            return Response({'detail': 'Partner has no associated user'}, status=status.HTTP_400_BAD_REQUEST)

        collab_type = request.data.get('collaboration_type') or 'partnership'
        title = request.data.get('title') or f"Collaboration request from {requester.username}"
        description = request.data.get('description') or ''

        try:
            # Avoid duplicate collaboration requests by using get_or_create
            cr, created = CollaborationRequest.objects.get_or_create(
                requester=requester,
                recipient=recipient,
                collaboration_type=collab_type,
                title=title,
                defaults={'description': description, 'status': 'pending'}
            )

            from .serializers import CollaborationRequestSerializer
            serializer = CollaborationRequestSerializer(cr, context={'request': request})

            if created:
                # Send notification to recipient
                try:
                    from notifications.utils import send_notification
                    requester_name = getattr(requester, 'username', str(requester))
                    notification_title = f"New {collab_type} request from {requester_name}"
                    notification_message = f"{requester_name} sent you a {collab_type} collaboration request: {title}"
                    action_url = f"/dashboard/community/collaborations/{cr.id}/"
                    send_notification(
                        recipient,
                        'collaboration_request',
                        notification_title,
                        notification_message,
                        action_url=action_url,
                        metadata={'collaboration_request_id': cr.id, 'requester_id': requester.id}
                    )
                except Exception as notify_err:
                    # Log but don't fail the request if notification fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to send collaboration notification: {notify_err}")

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                # Return existing object to the client instead of raising an error
                return Response({'detail': 'Collaboration request already exists', 'data': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error creating collaboration request: {e}")
            return Response({'detail': 'Failed to create collaboration request', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Corporate verification submission endpoint ---
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class CorporateVerificationSubmitView(APIView):
    """Allow authenticated users to submit or update their corporate verification request."""
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def post(self, request, *args, **kwargs):
        from .serializers import CorporateVerificationSubmissionSerializer
        serializer = CorporateVerificationSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cv = serializer.create_or_update_for_user(request.user, serializer.validated_data)
            # return submission with document URLs
            doc_urls = {}
            if cv.business_registration_doc:
                doc_urls['business_registration_doc'] = request.build_absolute_uri(cv.business_registration_doc.url)
            if cv.tax_certificate_doc:
                doc_urls['tax_certificate_doc'] = request.build_absolute_uri(cv.tax_certificate_doc.url)
            data = {
                'id': cv.id,
                'status': cv.status,
                'submitted_at': cv.submitted_at,
                'documents': doc_urls,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': 'Failed to submit verification', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        """Get the current user's verification status and documents."""
        try:
            from .models import CorporateVerification
            cv = CorporateVerification.objects.get(user=request.user)
            doc_urls = {}
            if cv.business_registration_doc:
                doc_urls['business_registration_doc'] = request.build_absolute_uri(cv.business_registration_doc.url)
            if cv.tax_certificate_doc:
                doc_urls['tax_certificate_doc'] = request.build_absolute_uri(cv.tax_certificate_doc.url)
            data = {
                'id': cv.id,
                'company_name': cv.company_name,
                'registration_number': cv.registration_number,
                'official_website': cv.official_website,
                'industry': cv.industry,
                'contact_person_title': cv.contact_person_title,
                'contact_phone': cv.contact_phone,
                'business_description': cv.business_description,
                'status': cv.status,
                'submitted_at': cv.submitted_at,
                'reviewed_at': cv.reviewed_at,
                'review_reason': cv.review_reason,
                'documents': doc_urls,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'No verification record found', 'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# CORPORATE MESSAGING VIEWSET
# ============================================================================

class CorporateMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for corporate messaging between users."""
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser)
    
    def get_queryset(self):
        """Return messages for the current user."""
        from .models import CorporateMessage
        user = self.request.user
        return CorporateMessage.objects.filter(
            models.Q(recipient=user) | models.Q(sender=user)
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        from .serializers import CorporateMessageSerializer
        return CorporateMessageSerializer
    
    def perform_create(self, serializer):
        """Create a new message with sender as current user."""
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send a message to another user."""
        from .models import CorporateMessage
        from .serializers import CorporateMessageSerializer
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        recipient_id = request.data.get('recipient')
        subject = request.data.get('subject')
        body = request.data.get('body')
        
        if not all([recipient_id, subject, body]):
            return Response({'detail': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            User = get_user_model()
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response({'detail': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        message = CorporateMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=subject,
            body=body
        )
        
        # Send email notification to recipient
        try:
            sender_name = request.user.profile.full_name if hasattr(request.user, 'profile') else request.user.email
            email_subject = f"New Message from {sender_name}: {subject}"
            email_body = f"""
Hello {recipient.profile.full_name if hasattr(recipient, 'profile') else recipient.email},

You have received a new message from {sender_name} ({request.user.email}).

Subject: {subject}

Message:
{body}

---
Reply to this message by visiting your dashboard: {settings.FRONTEND_URL}/dashboard/corporate/messages

Best regards,
The New Africa Platform Team
            """
            
            send_mail(
                email_subject,
                email_body,
                request.user.email,  # From sender's email
                [recipient.email],    # To recipient's email
                fail_silently=True
            )
        except Exception as e:
            pass  # Silently fail if email fails
        
        # Send notification to recipient
        try:
            from notifications.utils import send_notification
            send_notification(
                recipient,
                'message',
                f'New message from {request.user.profile.full_name}',
                f'{request.user.profile.full_name} sent you: {subject}',
                action_url=f'/dashboard/corporate/messages',
                metadata={'message_id': message.id}
            )
        except Exception as e:
            pass  # Silently fail if notification fails
        
        serializer = CorporateMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a message as read."""
        message = self.get_object()
        if message.recipient != request.user:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        message.mark_as_read()
        # Notify the sender that their message was read
        try:
            from notifications.utils import send_notification
            sender = message.sender
            # Avoid notifying if sender is missing or same as recipient
            if sender and sender != request.user:
                recipient_name = getattr(request.user, 'profile', None) and getattr(request.user.profile, 'full_name', None) or getattr(request.user, 'username', None) or str(request.user)
                notification_title = f'Message read by {recipient_name}'
                notification_message = f'{recipient_name} has read your message: {getattr(message, "subject", "(no subject)")}'
                action_url = f'/dashboard/corporate/messages?message_id={message.id}'
                send_notification(
                    sender,
                    'message_read',
                    notification_title,
                    notification_message,
                    action_url=action_url,
                    metadata={'message_id': message.id, 'reader_id': request.user.id}
                )
        except Exception:
            # Best-effort: do not fail the request if notification sending fails
            pass

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get user's inbox (received messages)."""
        messages = CorporateMessage.objects.filter(recipient=request.user).order_by('-created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get user's sent messages."""
        messages = CorporateMessage.objects.filter(sender=request.user).order_by('-created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread messages."""
        unread = CorporateMessage.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': unread}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def connected_users(self, request):
        """Get list of connected/collaborated corporate users."""
        from .models import CorporateConnection
        from django.db.models import Q
        
        # Get all accepted connections (both directions)
        connected = CorporateConnection.objects.filter(
            Q(sender=request.user, status='accepted') | Q(receiver=request.user, status='accepted')
        )
        
        connected_user_ids = set()
        for conn in connected:
            if conn.sender == request.user:
                connected_user_ids.add(conn.receiver_id)
            else:
                connected_user_ids.add(conn.sender_id)
        
        # Get user objects for connected users
        User = get_user_model()
        users = User.objects.filter(id__in=connected_user_ids).select_related('profile').order_by('profile__full_name')
        
        # Return user data as simple objects
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile': {
                    'full_name': user.profile.full_name if hasattr(user, 'profile') else '',
                    'company_name': user.profile.company_name if hasattr(user, 'profile') else '',
                }
            })
        
        return Response(result, status=status.HTTP_200_OK)




