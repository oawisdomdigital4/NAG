from rest_framework import serializers
from django.db import models
import json
import logging
from typing import Any
from .models import Group, GroupMembership, Post, Comment

class CommunitySectionSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = None
        fields = [
            'id', 'badge', 'title_main', 'title_highlight', 'description', 'image',
            # explicit stats
            'stat1_value', 'stat1_label', 'stat2_value', 'stat2_label', 'stat3_value', 'stat3_label',
            # explicit cards
            'card1_title', 'card1_description', 'card1_feature_1', 'card1_feature_2',
            'card2_title', 'card2_description', 'card2_feature_1', 'card2_feature_2',
            'cta_label', 'cta_url', 'is_published', 'created_at', 'updated_at'
        ]

    def to_representation(self, obj):
        """Normalize image URL to absolute when request is available."""
        data = super().to_representation(obj)
        request = self.context.get('request') if isinstance(self.context, dict) else None
        try:
            base = None
            if request is not None:
                base = request.build_absolute_uri('/')[:-1]
        except Exception:
            base = None

        try:
            img = data.get('image')
            if img and base and isinstance(img, str) and img.startswith('/'):
                data['image'] = f"{base}{img}"
        except Exception:
            pass

        return data


# Attach CommunitySection model if available
try:
    from .models import CommunitySection
    CommunitySectionSerializer.Meta.model = CommunitySection
except Exception:
    pass



class GroupSerializer(serializers.ModelSerializer):
    # created_by is assigned server-side
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    # Accept null/None from frontend for optional text/url fields
    logo_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    profile_picture_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tagline = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    website_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Image file fields for uploads
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    banner = serializers.ImageField(required=False, allow_null=True)
    
    # Computed fields for absolute image URLs (keep for backward compatibility)
    profile_picture_absolute_url = serializers.SerializerMethodField()
    banner_absolute_url = serializers.SerializerMethodField()
    
    # whether the requesting user is a member of this group
    is_member = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    # whether the requesting user is a moderator
    is_moderator = serializers.SerializerMethodField()
    # expose moderators list (ids) for management UIs
    moderators = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    # Admin info
    is_creator = serializers.SerializerMethodField()
    creator_email = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()

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
            'profile_picture_url',
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

    def _get_absolute_url(self, file_obj):
        """Convert relative file URL to absolute URL"""
        if not file_obj:
            return None
        try:
            from django.conf import settings
            request = self.context.get('request')
            file_url = file_obj.url if hasattr(file_obj, 'url') else str(file_obj)
            
            if file_url.startswith('http://') or file_url.startswith('https://'):
                return file_url
            
            if request:
                return request.build_absolute_uri(file_url)
            elif hasattr(settings, 'SITE_URL'):
                return f"{settings.SITE_URL.rstrip('/')}{file_url}"
            else:
                return f"http://localhost:8000{file_url}"
        except Exception:
            return None

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

    def get_is_moderator(self, obj):
        try:
            request = self.context.get('request')
            if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
                return False
            return obj.moderators.filter(id=request.user.id).exists()
        except Exception:
            return False

    def get_is_creator(self, obj):
        """Check if requesting user is the group creator"""
        try:
            request = self.context.get('request')
            if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
                return False
            return obj.created_by_id == request.user.id
        except Exception:
            return False

    def get_creator_email(self, obj):
        """Get creator's email address"""
        try:
            return obj.created_by.email if obj.created_by else None
        except Exception:
            return None

    def get_creator_name(self, obj):
        """Get creator's full name"""
        try:
            if not obj.created_by:
                return None
            creator = obj.created_by
            # Try to get full name from profile
            name = None
            for attr in ('profile', 'community_profile', 'userprofile'):
                profile = getattr(creator, attr, None)
                if profile:
                    name = getattr(profile, 'full_name', None)
                    if name:
                        break
            if not name:
                name = (getattr(creator, 'first_name', '') + ' ' + getattr(creator, 'last_name', '')).strip()
            return name or creator.email or str(creator)
        except Exception:
            return None

    def get_profile_picture_absolute_url(self, obj):
        """Get absolute URL for profile picture"""
        if obj.profile_picture:
            return self._get_absolute_url(obj.profile_picture)
        return obj.profile_picture_url or None

    def get_banner_absolute_url(self, obj):
        """Get absolute URL for banner"""
        if obj.banner:
            return self._get_absolute_url(obj.banner)
        return obj.banner_url or None

    def get_logo_url(self, obj):
        """Get logo URL (alias for profile_picture absolute URL for frontend compatibility)"""
        # Frontend expects 'logo_url' - provide absolute URL for profile picture
        if obj.profile_picture:
            return self._get_absolute_url(obj.profile_picture)
        return obj.profile_picture_url or None

    def get_banner_url(self, obj):
        """Get banner URL (ensure it's absolute for frontend)"""
        # Frontend expects 'banner_url' - provide absolute URL for banner
        if obj.banner:
            return self._get_absolute_url(obj.banner)
        return obj.banner_url or None

    def to_representation(self, obj):
        data = super().to_representation(obj)
        # Clean up null values for images
        if not data.get('profile_picture_absolute_url'):
            data['profile_picture_absolute_url'] = None
        if not data.get('banner_absolute_url'):
            data['banner_absolute_url'] = None
        return data

class SimpleUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)

    class Meta:
        model = None  # set at runtime
        fields = ['id', 'email', 'first_name', 'last_name', 'profile', 'is_staff']

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


class GroupInviteSerializer(serializers.ModelSerializer):
    invited_by = serializers.StringRelatedField(read_only=True)
    invited_user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = None
        fields = ('id', 'group', 'invited_by', 'invited_user', 'invited_email', 'token', 'status', 'created_at', 'expires_at', 'accepted_at', 'accepted_by')
        read_only_fields = ('token', 'status', 'created_at', 'accepted_at', 'accepted_by')

try:
    from .models import GroupInvite
    GroupInviteSerializer.Meta.model = GroupInvite
except Exception:
    pass

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
        read_only_fields = ('author', 'is_sponsored', 'sponsored_campaign')

    def to_internal_value(self, data):
        """
        Handle both 'group' and 'group_id' parameter names for backward compatibility.
        Frontend sends 'group_id', but serializer field is named 'group'.
        """
        # If frontend sent 'group_id', rename it to 'group' for the serializer
        if 'group_id' in data and 'group' not in data:
            data = dict(data)  # Make a copy to avoid modifying original
            data['group'] = data.pop('group_id')
        return super().to_internal_value(data)

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
            avatar_url = None
            avatar_obj = None
            
            # Try to get avatar from profile
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    avatar_url = getattr(profile, 'avatar_url', None)
                    if avatar_url:
                        return avatar_url
                    avatar_obj = getattr(profile, 'avatar', None)
                    if avatar_obj:
                        break
            
            # Try to get avatar directly from user
            if not avatar_obj:
                avatar_url = getattr(user, 'avatar_url', None)
                if avatar_url:
                    return avatar_url
                avatar_obj = getattr(user, 'avatar', None)
            
            # Build URL from avatar object if available
            if avatar_obj and hasattr(avatar_obj, 'url'):
                url = avatar_obj.url
                request = self.context.get('request')
                if request and isinstance(url, str) and url.startswith('/'):
                    return request.build_absolute_uri(url)
                return url
            
            return None
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
            avatar_url = None
            avatar_obj = None
            
            # Try to get avatar from profile
            for attr in ('community_profile', 'profile', 'userprofile'):
                profile = getattr(user, attr, None)
                if profile:
                    avatar_url = getattr(profile, 'avatar_url', None)
                    if avatar_url:
                        return avatar_url
                    avatar_obj = getattr(profile, 'avatar', None)
                    if avatar_obj:
                        break
            
            # Try to get avatar directly from user
            if not avatar_obj:
                avatar_url = getattr(user, 'avatar_url', None)
                if avatar_url:
                    return avatar_url
                avatar_obj = getattr(user, 'avatar', None)
            
            # Build URL from avatar object if available
            if avatar_obj and hasattr(avatar_obj, 'url'):
                url = avatar_obj.url
                request = self.context.get('request')
                if request and isinstance(url, str) and url.startswith('/'):
                    return request.build_absolute_uri(url)
                return url
            
            return None
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



# CTABanner serializer
class CTABannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = [
            'id', 'badge', 'title_main', 'title_highlight', 'description',
            'primary_cta_label', 'primary_cta_url', 'secondary_cta_label', 'secondary_cta_url',
            'feature1_title', 'feature1_subtitle', 'feature2_title', 'feature2_subtitle', 'feature3_title', 'feature3_subtitle',
            'is_published', 'created_at'
        ]


# Attach CTABanner model if available
try:
    from .models import CTABanner
    CTABannerSerializer.Meta.model = CTABanner
except Exception:
    pass


try:
    from .models import PostBookmark

    class PostBookmarkSerializer(serializers.ModelSerializer):
        post_id = serializers.PrimaryKeyRelatedField(source='post', queryset=Post.objects.all())
        user = serializers.PrimaryKeyRelatedField(read_only=True)
        
        class Meta:
            model = PostBookmark 
            fields = ['id', 'post_id', 'user', 'created_at']

        def create(self, validated_data):
            validated_data['user'] = self.context['request'].user
            return super().create(validated_data)

except Exception:
    pass


# ============================================================================
# COMMUNITY SYSTEM SERIALIZERS (NEW MODELS)
# ============================================================================

class UserEngagementScoreSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'user', 'username', 'total_posts', 'total_likes_received',
            'total_comments_received', 'total_mentions', 'facilitator_authority_score',
            'corporate_campaign_score', 'engagement_score', 'last_activity', 'updated_at'
        ]
        read_only_fields = ['id', 'last_activity', 'updated_at']


try:
    from .models import UserEngagementScore
    UserEngagementScoreSerializer.Meta.model = UserEngagementScore
except Exception:
    pass


class SubscriptionTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'tier_type', 'name', 'price', 'duration_days',
            'max_posts_per_day', 'can_create_groups', 'can_sponsor_posts', 
            'can_post_opportunities', 'can_collaborate', 'priority_feed_ranking',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


try:
    from .models import SubscriptionTier
    SubscriptionTierSerializer.Meta.model = SubscriptionTier
except Exception:
    pass


class SponsoredPostSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'creator', 'creator_name', 'title', 'description', 'status',
            'budget', 'daily_budget', 'spent', 'promotion_level', 'start_date',
            'end_date', 'impressions', 'clicks', 'ctr', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


try:
    from .models import SponsoredPost
    SponsoredPostSerializer.Meta.model = SponsoredPost
except Exception:
    pass


class TrendingTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'topic', 'mention_count', 'engagement_score',
            'last_mentioned', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


try:
    from .models import TrendingTopic
    TrendingTopicSerializer.Meta.model = TrendingTopic
except Exception:
    pass


class CorporateOpportunitySerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    company_name = serializers.CharField(source='creator.profile.company_name', read_only=True)
    application_count = serializers.ReadOnlyField()
    
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'creator', 'creator_name', 'company_name', 'title', 'description',
            'opportunity_type', 'status', 'location', 'remote_friendly',
            'salary_min', 'salary_max', 'salary_currency', 'deadline',
            'start_date', 'requirements', 'view_count', 'application_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'view_count', 'application_count', 'created_at', 'updated_at']


try:
    from .models import CorporateOpportunity
    CorporateOpportunitySerializer.Meta.model = CorporateOpportunity
except Exception:
    pass


class OpportunityApplicationSerializer(serializers.ModelSerializer):
    """Base serializer for opportunity applications"""
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    applicant_profile = serializers.SerializerMethodField(read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    reviewer_name = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'applicant', 'applicant_name', 'applicant_email', 'applicant_profile',
            'opportunity', 'opportunity_title',
            'status', 'cover_letter', 'resume_url', 
            'rejection_reason', 'reviewer_notes', 'reviewed_by', 'reviewer_name',
            'applied_at', 'status_updated_at', 'reviewed_at',
            'approved_notification_sent', 'rejected_notification_sent'
        ]
        read_only_fields = [
            'id', 'applicant', 'applicant_name', 'applicant_email', 'applicant_profile',
            'applied_at', 'status_updated_at', 'reviewed_at', 'reviewer_name'
        ]
    
    def get_applicant_profile(self, obj):
        """Get basic profile info for applicant"""
        try:
            profile = getattr(obj.applicant, 'profile', None)
            if profile:
                return {
                    'full_name': getattr(profile, 'full_name', ''),
                    'bio': getattr(profile, 'bio', ''),
                    'avatar_url': getattr(profile, 'avatar_url', '') or (str(getattr(profile, 'avatar', '')) if hasattr(profile, 'avatar') else ''),
                }
            return {}
        except Exception:
            return {}


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for corporate dashboard - shows all application details"""
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    applicant_profile = serializers.SerializerMethodField(read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    opportunity_id = serializers.IntegerField(source='opportunity.id', read_only=True)
    reviewer_name = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'applicant', 'applicant_name', 'applicant_email', 'applicant_profile',
            'opportunity', 'opportunity_id', 'opportunity_title',
            'status', 'status_display', 'cover_letter', 'resume_url',
            'rejection_reason', 'reviewer_notes', 'reviewed_by', 'reviewer_name',
            'applied_at', 'status_updated_at', 'reviewed_at',
            'approved_notification_sent', 'rejected_notification_sent'
        ]
        read_only_fields = [
            'id', 'applicant', 'applicant_name', 'applicant_email', 'applicant_profile',
            'opportunity_id', 'applied_at', 'status_updated_at', 'reviewed_at', 'reviewer_name',
            'status_display'
        ]
    
    def get_applicant_profile(self, obj):
        """Get detailed profile info for applicant"""
        try:
            profile = getattr(obj.applicant, 'profile', None)
            if profile:
                return {
                    'full_name': getattr(profile, 'full_name', ''),
                    'bio': getattr(profile, 'bio', ''),
                    'avatar_url': getattr(profile, 'avatar_url', '') or (str(getattr(profile, 'avatar', '')) if hasattr(profile, 'avatar') else ''),
                    'country': getattr(profile, 'country', ''),
                    'company_name': getattr(profile, 'company_name', ''),
                }
            return {}
        except Exception:
            return {}


try:
    from .models import OpportunityApplication
    OpportunityApplicationSerializer.Meta.model = OpportunityApplication
    ApplicationDetailSerializer.Meta.model = OpportunityApplication
except Exception:
    pass


class CollaborationRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)
    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    requester_profile = serializers.SerializerMethodField(read_only=True)
    recipient_profile = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'requester', 'requester_name', 'requester_email', 'requester_profile',
            'recipient', 'recipient_name', 'recipient_email', 'recipient_profile',
            'collaboration_type', 'title', 'description', 'status',
            'proposed_start', 'proposed_end', 'created_at', 'responded_at'
        ]
        read_only_fields = ['id', 'created_at', 'responded_at']

    def get_requester_profile(self, obj):
        """Get basic profile info for requester"""
        try:
            profile = getattr(obj.requester, 'profile', None)
            if profile:
                return {
                    'full_name': getattr(profile, 'full_name', ''),
                    'company_name': getattr(profile, 'company_name', ''),
                    'industry': getattr(profile, 'industry', ''),
                    'country': getattr(profile, 'country', ''),
                    'phone': getattr(profile, 'phone', '') or getattr(profile, 'contact_phone', ''),
                }
            return {}
        except Exception:
            return {}

    def get_recipient_profile(self, obj):
        """Get basic profile info for recipient"""
        try:
            profile = getattr(obj.recipient, 'profile', None)
            if profile:
                return {
                    'full_name': getattr(profile, 'full_name', ''),
                    'company_name': getattr(profile, 'company_name', ''),
                    'industry': getattr(profile, 'industry', ''),
                    'country': getattr(profile, 'country', ''),
                    'phone': getattr(profile, 'phone', '') or getattr(profile, 'contact_phone', ''),
                }
            return {}
        except Exception:
            return {}


try:
    from .models import CollaborationRequest
    CollaborationRequestSerializer.Meta.model = CollaborationRequest
except Exception:
    pass


class CorporateConnectionSerializer(serializers.ModelSerializer):
    # sender is provided by the server (read-only); receiver is expected as a PK
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    receiver_name = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = None  # set at runtime
        fields = [
            'id', 'sender', 'sender_name', 'receiver', 'receiver_name',
            'status', 'message', 'connected_at', 'created_at'
        ]
        read_only_fields = ['id', 'connected_at', 'created_at']


try:
    from .models import CorporateConnection
    CorporateConnectionSerializer.Meta.model = CorporateConnection
except Exception:
    pass


class PlatformAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Will be set at runtime
        fields = [
            'id', 'date', 'total_users', 'active_users_today', 'new_users_today',
            'posts_created', 'comments_created', 'likes_count', 'mentions_count',
            'subscriptions_active', 'mrr'
        ]
        read_only_fields = ['id', 'date']


try:
    from .models import PlatformAnalytics
    PlatformAnalyticsSerializer.Meta.model = PlatformAnalytics
except Exception:
    pass


class CorporatePartnerSerializer(serializers.Serializer):
    """Serializer for corporate partners directory"""
    id = serializers.SerializerMethodField()
    name = serializers.CharField(source='company_name')
    sector = serializers.CharField(source='industry')
    country = serializers.SerializerMethodField()
    description = serializers.CharField(source='business_description')
    website = serializers.CharField(source='official_website', allow_blank=True)
    contact_title = serializers.CharField(source='contact_person_title', allow_blank=True)
    contact_phone = serializers.CharField(allow_blank=True)
    verified = serializers.SerializerMethodField()
    status = serializers.CharField(allow_blank=True)
    logo_url = serializers.SerializerMethodField()
    # Expose a normalized verification timestamp for frontend use
    verification_date = serializers.SerializerMethodField()
    registration_number = serializers.CharField(allow_blank=True)
    
    def get_id(self, obj):
        """Get ID - prefer user.id if available, otherwise use pk"""
        if obj.user:
            return obj.user.id
        return obj.pk
    
    def get_country(self, obj):
        """Get country from user profile"""
        try:
            return obj.user.profile.country if obj.user and obj.user.profile else ''
        except Exception:
            return ''
    
    def get_verified(self, obj):
        """Check if corporate is verified"""
        return obj.status == 'approved'
    
    def get_logo_url(self, obj):
        """Get logo URL from user profile avatar"""
        try:
            if obj.user and obj.user.profile:
                profile = obj.user.profile
                # Return avatar URL if available, otherwise empty
                if profile.avatar_url:
                    return profile.avatar_url
                if profile.avatar:
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(profile.avatar.url)
            return ''
        except Exception:
            return ''

    def get_verification_date(self, obj):
        """Return an ISO-formatted verification date if available.

        Prefers `reviewed_at` (set when an admin reviews/approves),
        otherwise falls back to `submitted_at` if present. Returns None
        when no sensible date is available.
        """
        try:
            # some records may use reviewed_at as the admin review/approval timestamp
            dt = getattr(obj, 'reviewed_at', None) or getattr(obj, 'verified_at', None) or getattr(obj, 'submission_at', None) or getattr(obj, 'submitted_at', None)
            if not dt:
                return None
            # If dt is a datetime/date object, return ISO string
            try:
                return dt.isoformat()
            except Exception:
                # If it's already a string, return as-is
                if isinstance(dt, str):
                    return dt
            return None
        except Exception:
            return None


# Serializer for submitting/updating a CorporateVerification by the authenticated user
class CorporateVerificationSubmissionSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    registration_number = serializers.CharField(max_length=100)
    official_website = serializers.URLField(allow_blank=True, required=False)
    industry = serializers.CharField(max_length=255, allow_blank=True, required=False)
    contact_person_title = serializers.CharField(max_length=100, allow_blank=True, required=False)
    contact_phone = serializers.CharField(max_length=30, allow_blank=True, required=False)
    business_description = serializers.CharField(allow_blank=True)
    business_registration_doc = serializers.FileField(required=False, allow_null=True)
    tax_certificate_doc = serializers.FileField(required=False, allow_null=True)

    def create_or_update_for_user(self, user, validated_data):
        from .models import CorporateVerification
        import django.utils.timezone as tz

        obj, created = CorporateVerification.objects.get_or_create(user=user, defaults={
            'company_name': validated_data.get('company_name', ''),
            'registration_number': validated_data.get('registration_number', ''),
            'official_website': validated_data.get('official_website', ''),
            'industry': validated_data.get('industry', ''),
            'contact_person_title': validated_data.get('contact_person_title', ''),
            'contact_phone': validated_data.get('contact_phone', ''),
            'business_description': validated_data.get('business_description', ''),
            'status': 'pending',
            'submitted_at': tz.now(),
        })

        if not created:
            # update fields - preserve approved status, only reset to pending for other statuses
            obj.company_name = validated_data.get('company_name', obj.company_name)
            obj.registration_number = validated_data.get('registration_number', obj.registration_number)
            obj.official_website = validated_data.get('official_website', obj.official_website)
            obj.industry = validated_data.get('industry', obj.industry)
            obj.contact_person_title = validated_data.get('contact_person_title', obj.contact_person_title)
            obj.contact_phone = validated_data.get('contact_phone', obj.contact_phone)
            obj.business_description = validated_data.get('business_description', obj.business_description)
            # Only reset status to pending if not already approved
            if obj.status != 'approved':
                obj.status = 'pending'
                obj.reviewed_at = None
                obj.review_reason = ''
            obj.submitted_at = tz.now()
            # update documents if provided
            if 'business_registration_doc' in validated_data and validated_data['business_registration_doc']:
                obj.business_registration_doc = validated_data['business_registration_doc']
            if 'tax_certificate_doc' in validated_data and validated_data['tax_certificate_doc']:
                obj.tax_certificate_doc = validated_data['tax_certificate_doc']
            obj.save()
        else:
            # also save documents on initial creation if provided
            if 'business_registration_doc' in validated_data and validated_data['business_registration_doc']:
                obj.business_registration_doc = validated_data['business_registration_doc']
            if 'tax_certificate_doc' in validated_data and validated_data['tax_certificate_doc']:
                obj.tax_certificate_doc = validated_data['tax_certificate_doc']
            obj.save()

        return obj


# Corporate Messaging Serializers
class CorporateMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.profile.full_name', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    recipient_name = serializers.CharField(source='recipient.profile.full_name', read_only=True)
    recipient_email = serializers.CharField(source='recipient.email', read_only=True)
    
    class Meta:
        model = None
        fields = ['id', 'sender', 'sender_name', 'sender_email', 'recipient', 'recipient_name', 
                  'recipient_email', 'subject', 'body', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'sender_name', 'sender_email', 
                           'recipient_name', 'recipient_email']


# Attach CorporateMessage model if available
try:
    from .models import CorporateMessage
    CorporateMessageSerializer.Meta.model = CorporateMessage
except Exception:
    pass

