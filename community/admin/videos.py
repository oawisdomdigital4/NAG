from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.utils.safestring import mark_safe
from tv.models import Video, VideoCategory

# Note: combined gradient choices removed — admin now uses separate
# color_from_choice and color_to_choice fields with a constrained palette.


class VideoCategoryForm(forms.ModelForm):
    # combined gradient selector removed — use explicit from/to choices
    # non-model field for selecting an icon from a curated list
    icon_choice = forms.ChoiceField(widget=forms.RadioSelect, choices=[], required=False)
    # separate radio choices for from/to using a constrained palette
    color_from_choice = forms.ChoiceField(widget=forms.RadioSelect, choices=[], required=False)
    color_to_choice = forms.ChoiceField(widget=forms.RadioSelect, choices=[], required=False)

    class Meta:
        model = VideoCategory
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Combined gradient selector removed; admins should use the separate
        # Color From / Color To radio groups below.

        # Build icon choices with a small preview
        ICON_CHOICES_ADMIN = [
            ('', 'Default'),
            ('film', 'Film'),
            ('play', 'Play'),
            ('tv', 'TV'),
            ('video', 'Video'),
            ('camera', 'Camera'),
            ('users', 'Users'),
            ('globe', 'Globe'),
            ('star', 'Star'),
            ('search', 'Search'),
            ('clock', 'Clock'),
            ('play-circle', 'Play Circle'),
            ('layers', 'Layers'),
            ('zap', 'Spark'),
            ('book-open', 'Book Open'),
        ]
        icon_choices = []
        for val, lab in ICON_CHOICES_ADMIN:
            if not val:
                icon_choices.append((val, lab))
                continue
            preview = f"<i class='lucide-{val}' style='font-size:18px;margin-right:8px;vertical-align:middle'></i>"
            display = mark_safe(f"{preview} {lab}")
            icon_choices.append((val, display))
        self.fields['icon_choice'].choices = icon_choices

        # Allowed color keys (must match keys in frontend tailwind.config.js)
        ALLOWED_COLOR_KEYS = [
            'brand-blue', 'brand-red', 'brand-gold', 'cool-blue', 'charcoal', 'accent-beige',
            'deep-royal-blue', 'vibrant-red', 'royal-blue-tint', 'soft-gold', 'sky-blue-tint'
        ]
        color_key_choices = [('', 'Default')] + [(k, k.replace('-', ' ').title()) for k in ALLOWED_COLOR_KEYS]
        self.fields['color_from_choice'].choices = color_key_choices
        self.fields['color_to_choice'].choices = color_key_choices

        # Combined gradient selector removed; do not set gradient initial

        # Set initial icon from instance if available
        if self.instance and getattr(self.instance, 'pk', None):
            inst_icon = getattr(self.instance, 'icon', '') or ''
            if any(inst_icon == c for c, _ in icon_choices):
                self.fields['icon_choice'].initial = inst_icon
            else:
                self.fields['icon_choice'].initial = ''
            # set initial for color from/to if stored in canonical form
            cf = getattr(self.instance, 'color_from', '') or ''
            ct = getattr(self.instance, 'color_to', '') or ''
            # strip any 'from-'/'to-' prefixes to match keys
            if cf.startswith('from-'):
                self.fields['color_from_choice'].initial = cf.replace('from-', '')
            if ct.startswith('to-'):
                self.fields['color_to_choice'].initial = ct.replace('to-', '')

    def clean(self):
        cleaned = super().clean()

        def _normalize_token(tok: str, kind: str) -> str:
            if not tok:
                return ''
            v = str(tok).strip()
            # Remove accidental separators
            v = v.replace('|', ' ').strip()
            # If already has prefix, return as-is
            if v.startswith(f'{kind}-'):
                return v
            # If it's a full class like 'blue-500' -> prefix
            if v and not v.startswith('from-') and not v.startswith('to-'):
                return f"{kind}-{v}"
            return v

        # If explicit choices provided, validate against allowed palette and set canonical values
        cf_choice = cleaned.get('color_from_choice')
        ct_choice = cleaned.get('color_to_choice')
        ALLOWED_COLOR_KEYS = [
            'brand-blue', 'brand-red', 'brand-gold', 'cool-blue', 'charcoal', 'accent-beige',
            'deep-royal-blue', 'vibrant-red', 'royal-blue-tint', 'soft-gold', 'sky-blue-tint'
        ]
        if cf_choice:
            if cf_choice not in ALLOWED_COLOR_KEYS:
                raise forms.ValidationError('Invalid color_from selection')
            cleaned['color_from'] = f'from-{cf_choice}'
        if ct_choice:
            if ct_choice not in ALLOWED_COLOR_KEYS:
                raise forms.ValidationError('Invalid color_to selection')
            cleaned['color_to'] = f'to-{ct_choice}'

        # Only normalize fallback manual entries when no explicit choices provided
        if not (cf_choice or ct_choice):
            cf_raw = cleaned.get('color_from') or ''
            ct_raw = cleaned.get('color_to') or ''
            cleaned['color_from'] = _normalize_token(cf_raw, 'from')
            cleaned['color_to'] = _normalize_token(ct_raw, 'to')

        # Normalize icon field (store kebab-case)
        icon_choice = cleaned.get('icon_choice')
        icon_manual = cleaned.get('icon')
        icon_val = icon_choice or icon_manual or ''
        icon_val = str(icon_val).strip()
        if icon_val:
            import re
            v = icon_val.replace('_', '-').replace(' ', '-').strip()
            v = re.sub(r'(?<!-)([A-Z])', lambda m: '-' + m.group(1).lower(), v)
            v = v.lstrip('-').lower()
            cleaned['icon'] = v
            cleaned['icon_choice'] = v

        return cleaned

    def save(self, commit=True):
        # Apply the selected gradient back to the model's color_from / color_to
        inst = super().save(commit=False)
        # Priority: explicit from/to choices > combined gradient choice
        cf_choice = self.cleaned_data.get('color_from_choice')
        ct_choice = self.cleaned_data.get('color_to_choice')
        if cf_choice:
            inst.color_from = f'from-{cf_choice}'
        if ct_choice:
            inst.color_to = f'to-{ct_choice}'
        # If no explicit choices provided, leave color_from/color_to as entered (clean() will normalize/manual fallback)
        # Apply icon choice to the model's icon field
        icon_sel = self.cleaned_data.get('icon_choice')
        if icon_sel:
            inst.icon = icon_sel
        # else: leave existing color_from/color_to untouched
        if commit:
            inst.save()
            self.save_m2m()
        return inst


# VideoCategoryAdmin is now registered in tv/admin.py instead
# @admin.register(VideoCategory)
# class VideoCategoryAdmin(admin.ModelAdmin):
    form = VideoCategoryForm
    list_display = ('name', 'video_count', 'icon_preview', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def video_count(self, obj):
        return obj.videos.count()
    video_count.short_description = 'Videos'

    def icon_preview(self, obj):
        return format_html(
            '<i class="lucide-{}" style="font-size:14px;color:#0D1B52;"></i> {}',
            obj.icon, obj.icon
        )
    icon_preview.short_description = 'Icon'

# VideoAdmin is now registered in tv/admin.py instead
# @admin.register(Video)
# class VideoAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_preview', 'title', 'category', 'content_type', 'duration', 'view_count', 'is_published', 'is_featured')
    list_filter = ('is_published', 'is_featured', 'category', 'content_type')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('thumbnail_preview', 'view_count', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Content', {
            'fields': ('content_type', 'youtube_url', 'video_file', 'thumbnail', 'thumbnail_preview', 'duration')
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'order', 'view_count', 'created_at', 'updated_at')
        })
    )

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 48px; border-radius: 4px;">',
                obj.thumbnail.url
            )
        return format_html('<i class="fas fa-film" style="font-size: 24px; color: #666;"></i>')
    thumbnail_preview.short_description = 'Thumbnail'