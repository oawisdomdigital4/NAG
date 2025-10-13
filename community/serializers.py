from .models import Organizer, FeaturedSpeaker
from rest_framework import serializers
from django.db import models
import json
from .models import Group, GroupMembership, Post, Comment, Partner

class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizer
        fields = ["id", "name", "title", "bio", "image", "link"]

class FeaturedSpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedSpeaker
        fields = ["id", "name", "title", "bio", "image", "link"]

class PastEditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # replaced at runtime
        fields = ["id", "year", "location", "theme", "image", "attendees"]

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'logo']

class GroupSerializer(serializers.ModelSerializer):
    # created_by is assigned server-side
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    # Accept null/None from frontend for optional text/url fields
    logo_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    banner_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tagline = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    website_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # whether the requesting user is a member of this group
    is_member = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ('created_by',)

    def validate(self, attrs):
        # Some frontend code may send null for optional string/URL fields.
        # Convert None -> '' so model fields (which use blank=True but not null=True)
        # can accept them without validation errors.
        optional_string_fields = [
            'logo_url',
            'banner_url',
            'tagline',
            'website_url',
            'company_bio',
            'category',
            'rules',
        ]
        for key in optional_string_fields:
            if key in attrs and attrs.get(key) is None:
                attrs[key] = ''
        return attrs

    def _model_field_names(self):
        # Return concrete model field names for the Group model
        model = self.Meta.model
        return {f.name for f in model._meta.get_fields() if getattr(f, 'concrete', True) and not f.many_to_many}

    def create(self, validated_data):
        # Remove any keys not present on the model (frontend may send extra UI-only fields)
        allowed = self._model_field_names()
        filtered = {k: v for k, v in validated_data.items() if k in allowed}
        return super().create(filtered)

    def update(self, instance, validated_data):
        allowed = self._model_field_names()
        filtered = {k: v for k, v in validated_data.items() if k in allowed}
        return super().update(instance, filtered)

    def get_is_member(self, obj):
        try:
            request = self.context.get('request')
            if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
                return False
            return GroupMembership.objects.filter(group=obj, user=request.user).exists()
        except Exception:
            return False

    def get_members_count(self, obj):
        try:
            return obj.memberships.count()
        except Exception:
            return 0

class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    # Author is set server-side from the authenticated user
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    # allow frontend to omit group (general feed)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), allow_null=True, required=False)
    # normalized author fields for frontend convenience
    author_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    author_verified = serializers.SerializerMethodField()
    # reactions summary
    reaction_counts = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ('author',)

    def to_representation(self, obj):
        # Get the standard representation then normalize any relative URLs to absolute
        request = self.context.get('request')
        data = super().to_representation(obj)
        try:
            base = None
            if request is not None:
                # build_absolute_uri('/') returns the origin with trailing slash
                base = request.build_absolute_uri('/')[:-1]
        except Exception:
            base = None

        # Normalize media_urls
        try:
            murls = data.get('media_urls') or []
            if isinstance(murls, str):
                # sometimes a JSON string may leak through; try to parse
                try:
                    murls = json.loads(murls)
                except Exception:
                    murls = [murls]
            normalized = []
            for u in (murls or []):
                if not u:
                    continue
                if base and isinstance(u, str) and u.startswith('/'):
                    normalized.append(f"{base}{u}")
                else:
                    normalized.append(u)
            data['media_urls'] = normalized
        except Exception:
            pass

        # Normalize link_previews image URLs
        try:
            lps = data.get('link_previews') or []
            if isinstance(lps, dict):
                lps = [lps]
            for lp in (lps or []):
                img = lp.get('image') if isinstance(lp, dict) else None
                if img and base and isinstance(img, str) and img.startswith('/'):
                    lp['image'] = f"{base}{img}"
            data['link_previews'] = lps
        except Exception:
            pass

        # Normalize author_avatar if present
        try:
            avat = data.get('author_avatar')
            if avat and base and isinstance(avat, str) and avat.startswith('/'):
                data['author_avatar'] = f"{base}{avat}"
        except Exception:
            pass

        return data

    def get_bookmarks_count(self, obj):
        try:
            return obj.bookmarks.count()
        except Exception:
            return 0

    def get_author_name(self, obj):
        try:
            user = getattr(obj, 'author', None)
            # look for common profile attributes across apps
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    full = getattr(profile, 'full_name', None) or getattr(profile, 'name', None)
                    if full:
                        return full
            # attempt to compose from first_name/last_name if available on user
            first = getattr(user, 'first_name', '')
            last = getattr(user, 'last_name', '')
            if first or last:
                return f"{first} {last}".strip()
            # last fallback: username or email
            return getattr(user, 'username', None) or getattr(user, 'email', None) or str(user)
        except Exception:
            return None

    def get_author_avatar(self, obj):
        try:
            user = getattr(obj, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    return getattr(profile, 'avatar_url', None) or getattr(profile, 'avatar', None) or None
            return getattr(user, 'avatar_url', None) or getattr(user, 'avatar', None) or None
        except Exception:
            return None

    def get_author_role(self, obj):
        try:
            user = getattr(obj, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    return getattr(profile, 'role', None)
            return getattr(user, 'role', None) or None
        except Exception:
            return None

    def get_author_verified(self, obj):
        try:
            user = getattr(obj, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    return getattr(profile, 'is_verified_corporate', False)
            return False
        except Exception:
            return False

    def get_reaction_counts(self, obj):
        try:
            counts = {}
            for rtype, _ in getattr(obj, 'postreaction_set', []):
                pass
        except Exception:
            pass
        # safer: aggregate from related model
        try:
            qs = obj.reactions.values('reaction_type').order_by().annotate(count=models.Count('id'))
            return {item['reaction_type']: item['count'] for item in qs}
        except Exception:
            return {}

    def get_user_reaction(self, obj):
        try:
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                return None
            pr = obj.reactions.filter(user=request.user).first()
            return pr.reaction_type if pr else None
        except Exception:
            return None

    def get_comments_count(self, obj):
        try:
            return obj.comments.count()
        except Exception:
            return 0

class CommentSerializer(serializers.ModelSerializer):
    # accept id fields from frontend and map them appropriately
    post_id = serializers.PrimaryKeyRelatedField(source='post', queryset=Post.objects.all(), write_only=True, required=False)
    parent_comment_id = serializers.PrimaryKeyRelatedField(source='parent_comment', queryset=Comment.objects.all(), write_only=True, required=False, allow_null=True)
    is_private_reply = serializers.BooleanField(required=False, default=False)
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    author_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    author_verified = serializers.SerializerMethodField()
    # name of the parent comment's author (for replies)
    replied_to_name = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('author', 'post')

    def get_author_name(self, obj):
        try:
            user = getattr(obj, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    full = getattr(profile, 'full_name', None) or getattr(profile, 'name', None)
                    if full:
                        return full
            full = getattr(user, 'full_name', None)
            if full:
                return full
            first = getattr(user, 'first_name', '')
            last = getattr(user, 'last_name', '')
            if first or last:
                return f"{first} {last}".strip()
            return getattr(user, 'username', None) or getattr(user, 'email', None) or str(user)
        except Exception:
            return None

    def get_author_avatar(self, obj):
        try:
            user = getattr(obj, 'author', None)
            # Prefer an avatar/url on the community_profile, then other common profile attrs
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    # common names used across projects
                    return getattr(profile, 'avatar_url', None) or getattr(profile, 'avatar', None) or None
            # fallback to common attributes on the user model
            return getattr(user, 'avatar_url', None) or getattr(user, 'avatar', None) or None
        except Exception:
            return None

    def get_author_verified(self, obj):
        try:
            user = getattr(obj, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    return getattr(profile, 'is_verified_corporate', False)
            return False
        except Exception:
            return False

    def get_author_role(self, obj):
        try:
            user = getattr(obj, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    return getattr(profile, 'role', None)
            return getattr(user, 'role', None) or None
        except Exception:
            return None

    def get_replied_to_name(self, obj):
        try:
            parent = getattr(obj, 'parent_comment', None)
            if not parent:
                return None
            user = getattr(parent, 'author', None)
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    full = getattr(profile, 'full_name', None) or getattr(profile, 'name', None)
                    if full:
                        return full
            first = getattr(user, 'first_name', '')
            last = getattr(user, 'last_name', '')
            if first or last:
                return f"{first} {last}".strip()
            return getattr(user, 'username', None) or getattr(user, 'email', None) or str(user)
        except Exception:
            return None

    def get_likes_count(self, obj):
        try:
            return obj.reactions.count()
        except Exception:
            return 0

    def get_user_has_liked(self, obj):
        try:
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                return False
            return obj.reactions.filter(user=request.user).exists()
        except Exception:
            return False


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'name', 'members', 'created_by', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'room', 'sender', 'content', 'read', 'created_at']

# Patch in PastEdition model if available
try:
    from .models import PastEdition
    PastEditionSerializer.Meta.model = PastEdition
    # Attach chat models if available
    from .models import ChatRoom, Message
    ChatRoomSerializer.Meta.model = ChatRoom
    MessageSerializer.Meta.model = Message
except Exception:
    pass
