from django.db import models

# --- Per-hero stat items to simplify admin editing ---
ICON_CHOICES = [
    ('👥', 'People'),
    ('🌍', 'Globe'),
    ('🎤', 'Microphone'),
    ('📅', 'Calendar'),
    ('⭐', 'Star'),
    ('💼', 'Briefcase'),
    ('📈', 'Chart'),
]

# --- Registration package visual choices ---
PACKAGE_COLOR_CHOICES = [
    ('', 'Default'),
    # SummitTheme palette (ensure DB values like 'from-green-500 to-green-600' are valid)
    ('from-blue-500 to-blue-600', 'Blue'),
    ('from-purple-500 to-purple-600', 'Purple'),
    ('from-green-500 to-green-600', 'Green'),
    ('from-emerald-500 to-emerald-600', 'Emerald'),
    ('from-orange-500 to-orange-600', 'Orange'),
    ('from-red-500 to-red-600', 'Red'),
    ('from-yellow-500 to-yellow-600', 'Yellow'),
    ('from-teal-500 to-teal-600', 'Teal'),
    ('from-indigo-500 to-indigo-600', 'Indigo'),
    # Branded / package-specific gradients
    ('from-blue-500 to-brand-blue', 'Blue gradient'),
    ('from-brand-gold to-yellow-600', 'Gold gradient'),
    ('from-purple-500 to-pink-500', 'Purple->Pink'),
    ('from-green-500 to-emerald-500', 'Green gradient'),
    ('from-indigo-500 to-blue-500', 'Indigo gradient'),
]

# --- Summit Organizers ---
class Organizer(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='summit/organizers/')
    link = models.URLField(blank=True)

    def __str__(self):
        return self.name

# --- Summit Featured Speakers ---
class FeaturedSpeaker(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    # Location (city/country or brief location string) used by the prototype
    # to show where the speaker is from. Keep blank=True to be optional.
    location = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='summit/speakers/')
    link = models.URLField(blank=True)

    def __str__(self):
        return self.name


# --- Past Editions Photos ---
class PastEdition(models.Model):
    year = models.CharField(max_length=10)
    location = models.CharField(max_length=255, blank=True)
    theme = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='summit/past_editions/')
    attendees = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return f"{self.year} - {self.location}"


# --- Summit Hero / Landing content ---
class SummitHero(models.Model):
    """
    Store editable hero/landing content for the Summit page. Admins can
    create/update an entry in the admin panel; the API will expose the
    latest published instance.
    """
    title_main = models.CharField(max_length=255, help_text='Primary title (e.g. The New Africa)')
    title_highlight = models.CharField(max_length=255, blank=True, help_text='Highlighted part of the title')
    date_text = models.CharField(max_length=255, blank=True, help_text='Human-readable date (e.g. October 7-11, 2025)')
    location_text = models.CharField(max_length=255, blank=True, help_text='Location text (e.g. Casablanca & Dakhla, Morocco)')
    subtitle = models.TextField(blank=True, help_text='Bigger subtitle / description shown under the title')
    strapline = models.CharField(max_length=255, blank=True, help_text='Short strapline shown under subtitle')
    # CTA labels allow editors to customize button text shown in the frontend
    cta_register_label = models.CharField(max_length=255, blank=True, help_text='Label text for the register CTA button')
    cta_register_url = models.URLField(blank=True)
    cta_brochure_label = models.CharField(max_length=255, blank=True, help_text='Label text for the brochure CTA button')
    cta_brochure_url = models.URLField(blank=True)
    background_image = models.ImageField(upload_to='summit/hero/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SummitHero ({self.created_at.isoformat()})"



class SummitStat(models.Model):
    hero = models.ForeignKey(SummitHero, on_delete=models.CASCADE, related_name='stats')
    icon = models.CharField(max_length=4, choices=ICON_CHOICES, default='👥')
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.IntegerField(default=0, help_text='Ordering for display (lower numbers first)')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label}: {self.value}"


# --- Summit About / Pillars ---
class SummitAbout(models.Model):
    # Top-level editable content for the About section shown on the Summit page
    title_main = models.CharField(max_length=255, help_text='Primary title (e.g. Building Africa\'s)')
    title_highlight = models.CharField(max_length=255, blank=True, help_text='Highlighted part of the title')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='summit/about/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SummitAbout ({self.created_at.isoformat()})"
    


class SummitPillar(models.Model):
    ICON_CHOICES_PILLAR = [
        ('Target', 'Target'),
        ('Compass', 'Compass'),
        ('Lightbulb', 'Lightbulb'),
        ('Users', 'Users'),
        ('Globe', 'Globe'),
    ]
    about = models.ForeignKey(SummitAbout, on_delete=models.CASCADE, related_name='pillars')
    icon = models.CharField(max_length=50, choices=ICON_CHOICES_PILLAR, default='Lightbulb')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


# --- Summit Key Themes (KeyThemes section) ---
class SummitKeyThemes(models.Model):
    # container for key themes; admin can create one entry and add Theme rows
    # title_main + title_highlight allow the frontend to render a highlighted
    # portion of the title (e.g. "2025 Key" + "Themes") matching the prototype.
    # Remove legacy `title` and `description` (not used by frontend) to keep
    # the schema minimal; keep `subtitle` for the smaller paragraph under title.
    title_main = models.CharField(max_length=255, default='2025 Key', help_text='Primary part of the section title')
    title_highlight = models.CharField(max_length=255, default='Themes', help_text='Highlighted part of the title')
    subtitle = models.CharField(max_length=255, blank=True)
    # Optional CTA for the Key Themes section (button shown below the grid)
    cta_label = models.CharField(max_length=255, blank=True, help_text='Label for the CTA button (e.g. "Explore Full Programme Details")')
    cta_url = models.URLField(blank=True, help_text='URL for the CTA button')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SummitKeyThemes ({self.created_at.isoformat()})"


# --- Summit Agenda Models ---
class SummitAgenda(models.Model):
    """Top-level container for a summit's agenda."""
    title = models.CharField(max_length=255, help_text='Title of the summit/event')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Summit Agenda'
        verbose_name_plural = 'Summit Agendas'

    def __str__(self):
        return self.title


class SummitAgendaDay(models.Model):
    """Individual day entry in the summit agenda."""
    agenda = models.ForeignKey(SummitAgenda, on_delete=models.CASCADE, related_name='days')
    title = models.CharField(max_length=255, help_text='Title for this agenda day')
    location = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    order = models.IntegerField(default=0)
    # Plain-text comma-separated activities field for a simple single-line UI.
    # Each item should be formatted as "HH:MM-HH:MM|Activity title" and items
    # separated by commas. This provides an easy client-side input while the
    # project can still keep structured `SummitAgendaItem` rows if needed.
    activities_text = models.TextField(blank=True, help_text='Comma-separated activities in the format "HH:MM-HH:MM|Title"')
    # Optional visual hints for frontend: an emoji/icon and a color gradient CSS class
    icon = models.CharField(max_length=64, blank=True, help_text='Optional emoji or icon name for this day')
    color = models.CharField(max_length=255, blank=True, help_text='Optional gradient/color CSS classes for the day header')

    class Meta:
        ordering = ['order', 'date']
        verbose_name = 'Agenda Day'
        verbose_name_plural = 'Agenda Days'

    def __str__(self):
        return f"{self.title} ({self.date})"

    # Convenience helpers to parse/format the plain-text activities field.
    def get_activities_list(self):
        """Return activities_text parsed into a list of dicts: [{'time': 'HH:MM-HH:MM', 'title': '...'}, ...]"""
        text = (self.activities_text or '').strip()
        if not text:
            return []
        parts = [p.strip() for p in text.split(',') if p.strip()]
        items = []
        for p in parts:
            if '|' in p:
                time, title = p.split('|', 1)
                items.append({'time': time.strip(), 'title': title.strip()})
            else:
                # fallback: treat the whole part as title with no time
                items.append({'time': None, 'title': p})
        return items

    def set_activities_from_list(self, activities):
        """Accept a list of dicts/tuples and store into activities_text.

        activities: iterable of {'time': 'HH:MM-HH:MM'|'', 'title': '...'} or tuples
        """
        out = []
        for a in (activities or []):
            if isinstance(a, (list, tuple)) and len(a) >= 2:
                time, title = a[0], a[1]
            elif isinstance(a, dict):
                time = a.get('time')
                title = a.get('title') or a.get('label') or ''
            else:
                # stringify fallback
                time = None
                title = str(a)
            if time:
                out.append(f"{time.strip()}|{title.strip()}")
            else:
                out.append(title.strip())
        self.activities_text = ', '.join(out)

    @property
    def activities(self):
        """Property alias for templates/serializers to access parsed activities."""
        return self.get_activities_list()


class SummitAgendaItem(models.Model):
    """Individual timed activity within an agenda day."""
    day = models.ForeignKey(SummitAgendaDay, related_name='items', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} {self.title}"



class SummitTheme(models.Model):
    ICON_CHOICES_THEME = [
        ('Bot', 'AI Bot'),
        ('GraduationCap', 'Education'),
        ('Handshake', 'Partnership'),
        ('Sprout', 'Growth'),
        ('TrendingUp', 'Trends'),
    ]
    
    COLOR_CHOICES_THEME = [
        ('from-blue-500 to-blue-600', 'Blue'),
        ('from-purple-500 to-purple-600', 'Purple'),
        ('from-green-500 to-green-600', 'Green'),
        ('from-emerald-500 to-emerald-600', 'Emerald'),
        ('from-orange-500 to-orange-600', 'Orange'),
        ('from-red-500 to-red-600', 'Red'),
        ('from-yellow-500 to-yellow-600', 'Yellow'),
        ('from-teal-500 to-teal-600', 'Teal'),
        ('from-indigo-500 to-indigo-600', 'Indigo'),
    ]
    parent = models.ForeignKey(SummitKeyThemes, on_delete=models.CASCADE, related_name='themes')
    icon = models.CharField(max_length=50, choices=ICON_CHOICES_THEME, default='Bot')
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=255,
        choices=COLOR_CHOICES_THEME,
        default='from-blue-500 to-blue-600',
        help_text='Choose a gradient color for the theme card'
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


# --- Partners ---
class Partner(models.Model):
    logo = models.ImageField(upload_to='partners/logos/')

    def __str__(self):
        return f"Partner Logo {self.pk}"


# --- Partners section editable content ---
class PartnerSection(models.Model):
    """Editable content for the partners & sponsors call-to-action section.

    Admins can create one or more PartnerSection entries and mark the current
    one as published. The frontend will request the latest published entry and
    render its title, subtitle and CTA.
    """
    partner_section_title = models.CharField(max_length=255, blank=True, help_text='Section title (e.g. Become a Partner)')
    partner_section_subtitle = models.TextField(blank=True, help_text='Smaller paragraph under the title')
    partner_cta_label = models.CharField(max_length=255, blank=True, help_text='CTA button label')
    partner_cta_url = models.URLField(blank=True, help_text='CTA button URL')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PartnerSection ({self.created_at.isoformat()})"



# --- Registration Package ---
class RegistrationPackage(models.Model):
    """Registration package model for summit/event registration.
    
    Packages are displayed as cards with tiered pricing and features.
    Each package can be styled with a gradient color and can be marked as popular.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    features = models.JSONField(default=list, help_text='List of features included in this package')
    popular = models.BooleanField(default=False, help_text='Whether to highlight this as a popular option')
    color = models.CharField(
        max_length=255,
        choices=PACKAGE_COLOR_CHOICES,
        blank=True,
        help_text='Optional gradient color class for the package card'
    )
    order = models.IntegerField(default=0, help_text='Display order (lower numbers first)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Registration Package'
        verbose_name_plural = 'Registration Packages'

    def __str__(self):
        return self.name

