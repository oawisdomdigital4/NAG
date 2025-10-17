from .models import Organizer, FeaturedSpeaker
from rest_framework import serializers
from django.db import models
import json
import logging
from typing import Any
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

    def to_representation(self, obj):
        data = super().to_representation(obj)
        try:
            # Attach creator name for frontend convenience
            if obj.created_by:
                creator = obj.created_by
                name = None
                for attr in ('profile', 'community_profile', 'userprofile'):
                    profile = getattr(creator, attr, None)
                    if profile:
                        name = getattr(profile, 'full_name', None)
                        if name:
                            break
                if not name:
                    name = getattr(creator, 'first_name', '') + ' ' + getattr(creator, 'last_name', '')
                data['creator_name'] = (name or getattr(creator, 'email', None) or str(creator)).strip()
            else:
                data['creator_name'] = ''
        except Exception:
            data['creator_name'] = ''
        return data

class SimpleUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = None  # set at runtime
        fields = ['id', 'email', 'first_name', 'last_name', 'profile']

    def get_profile(self, obj):
        try:
            profile = getattr(obj, 'profile', None) or getattr(obj, 'community_profile', None) or None
            if not profile:
                return None
            avatar = getattr(profile, 'avatar_url', None) or getattr(profile, 'avatar', None) or None

            # simple binary-like heuristic to avoid returning raw binary blobs
            def _is_binary_like(v):
                if v is None:
                    return False
                if isinstance(v, (bytes, bytearray, memoryview)):
                    return True
                if not isinstance(v, str):
                    return False
                if '\u0000' in v or 'JFIF' in v or 'ICC_PROFILE' in v:
                    return True
                non_print = sum(1 for ch in v if ord(ch) < 32 or ord(ch) > 126)
                try:
                    ratio = non_print / max(1, len(v))
                except Exception:
                    ratio = 0
                return ratio > 0.3

            if _is_binary_like(avatar):
                avatar = None

            return {
                'full_name': getattr(profile, 'full_name', None),
                'avatar_url': avatar,
            }
        except Exception:
            return None


class GroupMembershipSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()

    class Meta:
        model = GroupMembership
        fields = '__all__'

    def get_user_detail(self, obj):
        try:
            user = obj.user
            serializer = SimpleUserSerializer(user)
            return serializer.data
        except Exception:
            return None

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

        # Sanitize any binary blobs that may have accidentally been stored
        # in JSONFields (e.g. raw bytes). JSON encoding in DRF will attempt
        # to decode bytes as utf-8 which can raise UnicodeDecodeError. Convert
        # bytes to safe unicode using UTF-8 with replacement to avoid 500s.
        logger = logging.getLogger(__name__)

        def _sanitize(value: Any, path: str = '') -> Any:
            # Recursively convert bytes and other binary-like objects to strings
            # and sanitize container types. This prevents the JSON encoder from
            # attempting to decode raw binary data which can raise UnicodeDecodeError.
            try:
                # handle raw bytes, bytearray, memoryview
                if isinstance(value, (bytes, bytearray, memoryview)):
                    post_id = getattr(obj, 'id', None)
                    logger.warning('Sanitizing binary blob in serializer output for post=%s path=%s', post_id, path)
                    try:
                        b = bytes(value)
                        return b.decode('utf-8', errors='replace')
                    except Exception:
                        try:
                            return bytes(value).decode('latin-1', errors='replace')
                        except Exception:
                            logger.warning('Dropping non-decodable binary in serializer output for post=%s path=%s', post_id, path)
                            return ''

                # dicts and lists: recurse
                if isinstance(value, dict):
                    cleaned = {}
                    for k, v in value.items():
                        try:
                            key_str = str(k)
                        except Exception:
                            key_str = repr(k)
                        cleaned[key_str] = _sanitize(v, path=f"{path}.{key_str}" if path else key_str)
                    return cleaned
                if isinstance(value, list):
                    return [_sanitize(v, path=f"{path}[{i}]") for i, v in enumerate(value)]

                # Some unexpected objects (e.g. BytesIO, File-like) may still appear.
                # If they expose a buffer or tobytes, attempt to convert; otherwise
                # fall back to their string representation which is safe for JSON.
                if hasattr(value, 'tobytes') and not isinstance(value, str):
                    try:
                        return _sanitize(value.tobytes(), path=path)
                    except Exception:
                        pass
                if hasattr(value, 'read') and callable(getattr(value, 'read')):
                    try:
                        # attempt to read a small chunk (non-destructive if possible)
                        chunk = value.read() if callable(value.read) else None
                        # reset if object supports seek
                        if hasattr(value, 'seek'):
                            try:
                                value.seek(0)
                            except Exception:
                                pass
                        return _sanitize(chunk, path=path)
                    except Exception:
                        pass

                # primitives (str, int, float, bool, None) and Django/DRF handled types
                # are left as-is. As a last resort convert unknown objects to string
                # so the JSON renderer does not attempt raw binary decoding.
                return value
            except Exception:
                # on any sanitizer error, return a safe string fallback
                try:
                    return str(value)
                except Exception:
                    return ''

        try:
            cleaned = _sanitize(data)
            return cleaned
        except Exception:
            logger.exception('Failed to sanitize serializer output for post=%s', getattr(obj, 'id', None))
            # If sanitization fails for any reason, return the original data
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
    # include nested replies under a comment for easier rendering on the frontend
    replies = serializers.SerializerMethodField()

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

    def to_representation(self, obj):
        """Return sanitized representation for Comment to avoid leaking binary blobs.

        Some profile avatar fields have contained raw binary (JFIF/ICC) in the DB which
        previously made it into API JSON. Defensive sanitization mirrors PostSerializer's
        approach but is scoped to fields commonly used by the frontend (author_avatar,
        replied_to_name, etc.).
        """
        data = super().to_representation(obj)
        logger = logging.getLogger(__name__)

        def _is_binary_like(v: Any) -> bool:
            # heuristic: presence of non-printable characters typical of binary blobs
            if v is None:
                return False
            if isinstance(v, (bytes, bytearray, memoryview)):
                return True
            if not isinstance(v, str):
                return False
            # if the string contains many non-printable chars or the JFIF/ICC markers,
            # treat it as binary-like
            if '\u0000' in v or 'JFIF' in v or 'ICC_PROFILE' in v:
                return True
            # if more than 30% of chars are non-printable, consider it binary
            non_print = sum(1 for ch in v if ord(ch) < 32 or ord(ch) > 126)
            try:
                ratio = non_print / max(1, len(v))
            except Exception:
                ratio = 0
            return ratio > 0.3

        try:
            avat = data.get('author_avatar')
            if _is_binary_like(avat):
                post_id = getattr(obj, 'id', None)
                logger.warning('Dropping binary-like author_avatar for comment=%s', post_id)
                data['author_avatar'] = None
        except Exception:
            pass

        return data

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

    def get_replies(self, obj):
        """Return serialized replies for this comment.

        We respect private-reply visibility the same way the view does: only
        include private replies when the requesting user is either the reply
        author or the parent post author.
        """
        try:
            request = self.context.get('request')
            user = getattr(request, 'user', None)
            qs = obj.replies.all().order_by('created_at')
            # apply same visibility rules as PostViewSet.comments
            if user and user.is_authenticated:
                qs = qs.filter(models.Q(is_private_reply=False) | models.Q(author=user) | models.Q(post__author=user))
            else:
                qs = qs.filter(is_private_reply=False)
            serializer = CommentSerializer(qs, many=True, context=self.context)
            return serializer.data
        except Exception:
            return []


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

# Resolve runtime model for user serializer helper
try:
    from django.contrib.auth import get_user_model
    SimpleUserSerializer.Meta.model = get_user_model()
except Exception:
    pass
