from .models import Organizer, FeaturedSpeaker
from rest_framework import serializers
from django.db import models
import json
import logging
from typing import Any
from .models import Group, GroupMembership, Post, Comment, Partner
from .models import SummitAgenda, SummitAgendaDay, SummitAgendaItem
from .models import Video, VideoCategory

class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizer
        # The prototype displays organiser name and a short descriptive line.
        # Expose only the fields needed by the UI: id, name, bio and image.
        # We intentionally omit link and title to keep the API minimal for the
        # prototype-based UI.
        fields = ["id", "name", "bio", "image"]

class FeaturedSpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedSpeaker
        # Expose name + bio + image + location for the prototype-based UI.
        fields = ["id", "name", "bio", "image", "location"]

class PastEditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # replaced at runtime
        fields = ["id", "year", "location", "theme", "image", "attendees"]

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'logo']



class SummitStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'icon', 'label', 'value', 'order']


class SummitHeroSerializer(serializers.ModelSerializer):
    # nested stats provided via related_name 'stats'
    stats = SummitStatSerializer(many=True, read_only=True)

    class Meta:
        model = None  # set at runtime if available
        fields = [
            'id', 'title_main', 'title_highlight', 'date_text', 'location_text',
            'subtitle', 'strapline', 'cta_register_label', 'cta_register_url', 'cta_brochure_label', 'cta_brochure_url', 'stats',
            'background_image', 'is_published', 'created_at'
        ]


class SummitPillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'icon', 'title', 'description', 'order']


class SummitAboutSerializer(serializers.ModelSerializer):
    pillars = SummitPillarSerializer(many=True, read_only=True)

    class Meta:
        model = None
        fields = ['id', 'title_main', 'title_highlight', 'description', 'image', 'pillars', 'created_at']


class SummitThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'icon', 'title', 'subtitle', 'description', 'color', 'order']


class SummitAgendaItemSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = SummitAgendaItem
        fields = ['id', 'time', 'title', 'order']

    def get_time(self, obj):
        # Format time as "HH:MM - HH:MM"
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"


class SummitAgendaDaySerializer(serializers.ModelSerializer):
    # Keep structured items available for clients that use them
    # source='items' is redundant when the field name matches the relation
    items = SummitAgendaItemSerializer(many=True, read_only=True)

    # Expose the plain-text field for editing as well as a parsed activities list
    activities_text = serializers.CharField(required=False, allow_blank=True)
    activities = serializers.SerializerMethodField()

    # friendly frontend helpers
    day = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    date_formatted = serializers.SerializerMethodField()

    class Meta:
        model = SummitAgendaDay
        # include a friendly 'day' label and optional icon/color for frontend
        fields = ['id', 'day', 'title', 'location', 'date', 'date_formatted', 'order', 'activities_text', 'activities', 'items', 'icon', 'color']
        ordering = ['order', 'date']

    def get_activities(self, obj):
        try:
            acts = getattr(obj, 'activities', []) or []
            out = []
            if acts:
                for a in acts:
                    time = a.get('time') if isinstance(a, dict) else None
                    title = (a.get('title') if isinstance(a, dict) else str(a)) or ''
                    if time:
                        # normalize separators to " - " for frontend display
                        t = str(time).strip().replace('\u2013', '-').replace('–', '-').replace('--', '-')
                        if '-' in t and ' - ' not in t:
                            parts = [p.strip() for p in t.split('-')]
                            t = ' - '.join(parts)
                        time = t
                    out.append({'time': time or '', 'title': title})
                return out

            # fallback: build from structured items if no plain-text activities present
            for item in getattr(obj, 'items', []).all() if hasattr(obj, 'items') else []:
                try:
                    time = f"{item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')}"
                except Exception:
                    time = ''
                out.append({'time': time, 'title': getattr(item, 'title', '')})
            return out
        except Exception:
            return []

    def get_day(self, obj):
        # Human-friendly label for the frontend (uses ordering if available)
        try:
            idx = (obj.order or 0) + 1
            return f"Day {idx}"
        except Exception:
            return ''

    def get_icon(self, obj):
        # No icon stored on the model currently — return None so frontend can fallback
        try:
            return getattr(obj, 'icon', None) or None
        except Exception:
            return None

    def get_color(self, obj):
        # No color stored on the model currently — return None for frontend default
        try:
            return getattr(obj, 'color', None) or None
        except Exception:
            return None

    def get_date_formatted(self, obj):
        try:
            if not getattr(obj, 'date', None):
                return ''
            return obj.date.strftime('%B %-d, %Y')
        except Exception:
            try:
                # Windows/strptime/platform differences: fallback without '-' flag
                return obj.date.strftime('%B %d, %Y')
            except Exception:
                return ''

class SummitAgendaSerializer(serializers.ModelSerializer):
    days = SummitAgendaDaySerializer(many=True, read_only=True)

    # Provide frontend-friendly aliases so the React component can read
    # title_main/title_highlight/subtitle without special-casing different models.
    title_main = serializers.SerializerMethodField()
    title_highlight = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()

    class Meta:
        model = SummitAgenda
        # expose a frontend-friendly shape: title_main/title_highlight/subtitle map to
        # the simple SummitAgenda's title/description if present
        fields = ['id', 'title', 'title_main', 'title_highlight', 'subtitle', 'description', 'days', 'created_at', 'updated_at']

    def get_title_main(self, obj):
        try:
            return getattr(obj, 'title', '')
        except Exception:
            return ''

    def get_title_highlight(self, obj):
        # No separate highlight stored on this model; return empty so frontend falls back
        return ''

    def get_subtitle(self, obj):
        try:
            return getattr(obj, 'description', '')
        except Exception:
            return ''


class SummitKeyThemesSerializer(serializers.ModelSerializer):
    themes = SummitThemeSerializer(many=True, read_only=True)

    class Meta:
        model = None
        # expose title_main + title_highlight so frontend can preserve the
        # prototype's highlighted title styling rather than hard-coding text
        # Remove legacy `title` and `description` fields (frontend uses the
        # two-part title and subtitle).
        fields = ['id', 'title_main', 'title_highlight', 'subtitle', 'cta_label', 'cta_url', 'themes', 'created_at']


class PartnerSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'partner_section_title', 'partner_section_subtitle', 'partner_cta_label', 'partner_cta_url', 'is_published', 'created_at']


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


class AboutHeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'title_main', 'subtitle', 'background_image', 'is_published', 'created_at']

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

class RegistrationPackageSerializer(serializers.ModelSerializer):
    """Expose registration packages to the frontend in a simple shape.

    The frontend expects an array of packages with: id, name, price, currency,
    features (list), popular (bool), order (int), icon, color.
    """

    class Meta:
        model = None
        # include description so frontend can render the package subtitle/text
        # icons were removed for RegistrationPackage; expose color only
        fields = ['id', 'name', 'description', 'price', 'currency', 'features', 'popular', 'order', 'color', 'created_at']


# Patch in runtime models (PastEdition, SummitHero/Stat, SummitAbout/Pillar, Chat models)
try:
    from .models import PastEdition
    PastEditionSerializer.Meta.model = PastEdition
except Exception:
    pass

try:
    from .models import SummitKeyThemes, SummitTheme
    # attach serializers if available
    SummitKeyThemesSerializer.Meta.model = SummitKeyThemes
    SummitThemeSerializer.Meta.model = SummitTheme
except Exception:
    pass

try:
    from .models import SummitAgenda, SummitAgendaDay
    SummitAgendaSerializer.Meta.model = SummitAgenda
    SummitAgendaDaySerializer.Meta.model = SummitAgendaDay
except Exception:
    pass

try:
    from .models import SummitHero
    SummitHeroSerializer.Meta.model = SummitHero
    try:
        from .models import SummitStat
        SummitStatSerializer.Meta.model = SummitStat
    except Exception:
        pass
except Exception:
    pass

try:
    from .models import SummitAbout, SummitPillar
    SummitAboutSerializer.Meta.model = SummitAbout
    SummitPillarSerializer.Meta.model = SummitPillar
except Exception:
    pass

try:
    from .models import ChatRoom, Message
    ChatRoomSerializer.Meta.model = ChatRoom
    MessageSerializer.Meta.model = Message
except Exception:
    pass

# Attach RegistrationPackage model to serializer if available
try:
    from .models import RegistrationPackage
    RegistrationPackageSerializer.Meta.model = RegistrationPackage
except Exception:
    pass

# Attach PartnerSection model to serializer if available
try:
    from .models import PartnerSection
    PartnerSectionSerializer.Meta.model = PartnerSection
except Exception:
    pass


# FooterContent serializer
class FooterContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = [
            'id', 'company_name', 'tagline', 'address_text', 'contact_email',
            # social
            'social_facebook', 'social_instagram', 'social_linkedin', 'social_twitter', 'social_youtube',
            # company
            'company_about', 'company_team', 'company_careers', 'company_contact',
            # platforms
            'platforms_magazine', 'platforms_tv', 'platforms_institute', 'platforms_summit', 'platforms_community',
            # account
            'account_login', 'account_signup', 'account_faqs',
            # legal
            'legal_terms', 'legal_privacy', 'legal_help',
            'copyright_text', 'is_published', 'created_at'
        ]


# Attach FooterContent model if available
try:
    from .models import FooterContent
    FooterContentSerializer.Meta.model = FooterContent
except Exception:
    pass

# Attach AboutHero model if available
try:
    from .models import AboutHero
    AboutHeroSerializer.Meta.model = AboutHero
except Exception:
    pass

# Attach CommunitySection model if available
try:
    from .models import CommunitySection
    CommunitySectionSerializer.Meta.model = CommunitySection
except Exception:
    pass


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




class VideoCategorySerializer(serializers.ModelSerializer):
    video_count = serializers.SerializerMethodField()

    class Meta:
        model = VideoCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'color_from', 'color_to', 'video_count'
        ]

    def get_video_count(self, obj):
        return obj.videos.filter(is_published=True).count()

# Simplified serializer for related videos to avoid recursion
class RelatedVideoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    video_id = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description', 'category_name',
            'content_type', 'video_id', 'thumbnail_url', 'duration',
            'view_count', 'created_at'
        ]

    def get_video_id(self, obj):
        vid = obj.get_video_id()
        request = self.context.get('request') if isinstance(self.context, dict) else None
        try:
            if vid and isinstance(vid, str) and request and vid.startswith('/'):
                return request.build_absolute_uri(vid)
        except Exception:
            pass
        return vid

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            url = obj.thumbnail.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class VideoSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    video_id = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    related_videos = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'category_name',
            'content_type', 'video_id', 'thumbnail_url', 'duration',
            'is_featured', 'view_count', 'created_at', 'related_videos'
        ]

    def get_video_id(self, obj):
        # Return an absolute URL for uploaded videos when a request is
        # available so the frontend fetches media from the Django backend
        # (prevents the browser resolving a relative path against the
        # frontend dev server which may not support Range requests).
        vid = obj.get_video_id()
        request = self.context.get('request') if isinstance(self.context, dict) else None
        try:
            if vid and isinstance(vid, str) and request and vid.startswith('/'):
                return request.build_absolute_uri(vid)
        except Exception:
            # on any error, fall back to the raw value
            pass
        return vid

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            url = obj.thumbnail.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_related_videos(self, obj):
        """Return 3 related videos from the same category.
        Uses RelatedVideoSerializer to avoid recursion."""
        related = Video.objects.filter(
            category=obj.category,
            is_published=True
        ).exclude(id=obj.id)[:3]
        
        return RelatedVideoSerializer(
            related, 
            many=True, 
            context=self.context
        ).data