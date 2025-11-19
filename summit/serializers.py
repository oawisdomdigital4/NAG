from rest_framework import serializers
from django.db import models
import json
import logging
from typing import Any
from .models import Organizer, FeaturedSpeaker, Partner, SummitAgenda, SummitAgendaDay, SummitAgendaItem

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

class SummitStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ['id', 'label', 'value']


class SummitHeroSerializer(serializers.ModelSerializer):
    # Link to small stat objects if present
    stats = SummitStatSerializer(many=True, read_only=True)

    class Meta:
        model = None
        fields = ['id', 'title', 'subtitle', 'image', 'is_published', 'stats', 'created_at']

class PastEditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # replaced at runtime
        fields = ["id", "year", "location", "theme", "image", "attendees"]

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'logo']

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