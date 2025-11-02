from django.db import models
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

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


# --- About page hero (site-level About page) ---
class AboutHero(models.Model):
    """Editable hero content for the site's About page. Admins can create
    one or more AboutHero entries and mark the current one as published.
    The frontend will request the latest published entry and render its
    title and subtitle.
    """
    title_main = models.CharField(max_length=255, help_text='Primary headline shown on the About page')
    subtitle = models.TextField(blank=True, help_text='Supporting paragraph shown below the headline')
    background_image = models.ImageField(upload_to='about/hero/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AboutHero ({self.created_at.isoformat()})"


# --- Per-hero stat items to simplify admin editing ---
ICON_CHOICES = [
    ('👥', 'People (👥)'),
    ('🌍', 'Globe (🌍)'),
    ('🎤', 'Microphone (🎤)'),
    ('📅', 'Calendar (📅)'),
    ('⭐', 'Star (⭐)'),
    ('💼', 'Briefcase (💼)'),
    ('📈', 'Chart (📈)'),
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


# --- Site-wide CTA Banner ---
class CTABanner(models.Model):
    """Editable site CTA banner used on the Home page (the large call-to-action section).

    Admins can create/update a banner and mark it published. The frontend will
    request the latest published instance and render its content.
    """
    badge = models.CharField(max_length=255, blank=True, help_text='Small label above the title (e.g. Ready to Get Started?)')
    title_main = models.CharField(max_length=255, help_text='Primary title text')
    title_highlight = models.CharField(max_length=255, blank=True, help_text='Highlighted part of the title')
    description = models.TextField(blank=True)

    primary_cta_label = models.CharField(max_length=255, blank=True)
    primary_cta_url = models.URLField(blank=True)
    secondary_cta_label = models.CharField(max_length=255, blank=True)
    secondary_cta_url = models.URLField(blank=True)

    # three small feature cards shown under the CTAs
    feature1_title = models.CharField(max_length=128, blank=True)
    feature1_subtitle = models.CharField(max_length=255, blank=True)
    feature2_title = models.CharField(max_length=128, blank=True)
    feature2_subtitle = models.CharField(max_length=255, blank=True)
    feature3_title = models.CharField(max_length=128, blank=True)
    feature3_subtitle = models.CharField(max_length=255, blank=True)

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CTABanner ({self.created_at.isoformat()})"


# --- Community section editable content (prototype -> frontend) ---
class CommunitySection(models.Model):
    """Editable content for the Community section used on the homepage/about pages.

    Stores headline parts, description, hero image, structured stats and cards
    so the frontend can render the prototype layout dynamically.
    """
    badge = models.CharField(max_length=255, blank=True, help_text='Small badge text shown above the title (e.g. Join Our Community)')
    title_main = models.CharField(max_length=255, help_text='Primary title text (before the highlighted part)')
    title_highlight = models.CharField(max_length=255, blank=True, help_text='Highlighted part of the title shown in gradient')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='community/hero/', blank=True, null=True)
    # Explicit editable stat fields (three stats shown in the prototype)
    stat1_value = models.CharField(max_length=64, blank=True, help_text='Stat 1 value (e.g. 95%)')
    stat1_label = models.CharField(max_length=128, blank=True, help_text='Stat 1 label (e.g. Growth Rate)')
    stat2_value = models.CharField(max_length=64, blank=True, help_text='Stat 2 value (e.g. 1M+)')
    stat2_label = models.CharField(max_length=128, blank=True, help_text='Stat 2 label (e.g. Members)')
    stat3_value = models.CharField(max_length=64, blank=True, help_text='Stat 3 value (e.g. 50+)')
    stat3_label = models.CharField(max_length=128, blank=True, help_text='Stat 3 label (e.g. Countries)')

    # Explicit card fields (two cards in prototype). Icons are hardcoded in the frontend.
    card1_title = models.CharField(max_length=255, blank=True)
    card1_description = models.TextField(blank=True)
    card1_feature_1 = models.CharField(max_length=255, blank=True)
    card1_feature_2 = models.CharField(max_length=255, blank=True)

    card2_title = models.CharField(max_length=255, blank=True)
    card2_description = models.TextField(blank=True)
    card2_feature_1 = models.CharField(max_length=255, blank=True)
    card2_feature_2 = models.CharField(max_length=255, blank=True)
    cta_label = models.CharField(max_length=255, blank=True)
    cta_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CommunitySection ({self.created_at.isoformat()})"


# --- Site footer editable content ---
class FooterContent(models.Model):
    """Editable footer content for the site. Frontend will request the latest
    published FooterContent and render the values. Fields are intentionally
    flexible (JSONFields) to allow structured sections/links.
    """
    company_name = models.CharField(max_length=255, default='New Africa', blank=True)
    tagline = models.CharField(max_length=512, blank=True)
    address_text = models.CharField(max_length=512, blank=True)
    contact_email = models.CharField(max_length=255, blank=True)


    # Social links (explicit fields for fixed icon locations)
    social_facebook = models.CharField(max_length=512, blank=True, help_text='Facebook page URL')
    social_instagram = models.CharField(max_length=512, blank=True, help_text='Instagram page URL')
    social_linkedin = models.CharField(max_length=512, blank=True, help_text='LinkedIn page URL')
    social_twitter = models.CharField(max_length=512, blank=True, help_text='Twitter page URL')
    social_youtube = models.CharField(max_length=512, blank=True, help_text='YouTube channel URL')

    # Footer sections - explicit link fields for the standard footer layout
    # Company
    company_about = models.CharField(max_length=255, blank=True)
    company_team = models.CharField(max_length=255, blank=True)
    company_careers = models.CharField(max_length=255, blank=True)
    company_contact = models.CharField(max_length=255, blank=True)
    # Platforms
    platforms_magazine = models.CharField(max_length=255, blank=True)
    platforms_tv = models.CharField(max_length=255, blank=True)
    platforms_institute = models.CharField(max_length=255, blank=True)
    platforms_summit = models.CharField(max_length=255, blank=True)
    platforms_community = models.CharField(max_length=255, blank=True)
    # Account
    account_login = models.CharField(max_length=255, blank=True)
    account_signup = models.CharField(max_length=255, blank=True)
    account_faqs = models.CharField(max_length=255, blank=True)
    # Legal & Support (bottom links)
    legal_terms = models.CharField(max_length=255, blank=True)
    legal_privacy = models.CharField(max_length=255, blank=True)
    legal_help = models.CharField(max_length=255, blank=True)

    copyright_text = models.CharField(max_length=255, blank=True)

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"FooterContent ({self.created_at.isoformat()})"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_profile')
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    expertise_areas = models.JSONField(default=list, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)

# --- Courses ---
class Course(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    facilitator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_facilitated_courses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    progress = models.IntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

# --- Community ---
class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    is_corporate_group = models.BooleanField(default=False)
    banner_url = models.URLField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_created_groups')
    created_at = models.DateTimeField(auto_now_add=True)

class GroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    # Allow null group for posts that target the general community feed
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_posts')
    content = models.TextField()
    # Controls whether post appears only in group, globally, or is private to author
    FEED_VISIBILITY_CHOICES = (
        ('group_only', 'Group only'),
        ('public_global', 'Public global'),
        ('private', 'Private (only author)'),
    )
    feed_visibility = models.CharField(max_length=20, choices=FEED_VISIBILITY_CHOICES, default='group_only')
    # Store list of media URLs (images/files) attached to this post
    media_urls = models.JSONField(default=list, blank=True)
    # Store link preview metadata for external links (list of objects)
    link_previews = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PostAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    file = models.FileField(upload_to='community/post_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.pk} for Post {self.post_id}"


class PostBookmark(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"Bookmark by {self.user_id} on Post {self.post_id}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_comments')
    content = models.TextField()
    # allow threaded replies
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    # allow marking a comment as a private reply (for future moderation/features)
    is_private_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PostReaction(models.Model):
    REACTION_CHOICES = (
        ('like', 'Like'),
        ('love', 'Love'),
        ('celebrate', 'Celebrate'),
        ('support', 'Support'),
        ('insightful', 'Insightful'),
        ('funny', 'Funny'),
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='post_reactions')
    reaction_type = models.CharField(max_length=32, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user_id} reacted {self.reaction_type} on Post {self.post_id}"


class CommentReaction(models.Model):
    # For now we only support a single 'like' reaction on comments
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comment_reactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

    def __str__(self):
        return f"{self.user_id} liked Comment {self.comment_id}"

# --- Notifications ---
class Notification(models.Model):
    CATEGORY_CHOICES = (
        ('course', 'Course'),
        ('community', 'Community'),
        ('billing', 'Billing'),
        ('system', 'System'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_notifications')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# --- Payments & Subscriptions ---
class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    interval = models.CharField(max_length=10)  # 'month', 'year'
    features = models.JSONField(default=list, blank=True)

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    provider = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)


# --- Registration Packages for the public registration page ---
class RegistrationPackage(models.Model):
    """Simple model to expose registration package options to the frontend.

    fields:
    - name: label shown in UI (e.g. "In-person Pass")
    - price: numeric price
    - currency: currency code for display (e.g. 'USD')
    - features: JSON list of strings describing included features
    - popular: whether to mark as featured in the UI
    - order: integer ordering (lower numbers appear first)
    - icon: optional emoji or icon name
    - color: optional CSS gradient class used by the frontend for styling
    """
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    features = models.JSONField(default=list, blank=True)
    popular = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    # color: choose from a small set of gradient classes used by the frontend
    color = models.CharField(max_length=255, choices=PACKAGE_COLOR_CHOICES, default='from-blue-500 to-brand-blue', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency})"

# --- Corporate Verification ---
class CorporateVerification(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_corporate_verification')
    company_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100)
    official_website = models.URLField(blank=True)
    industry = models.CharField(max_length=255, blank=True)
    contact_person_title = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    business_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


# --- Chat / Messaging ---
class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='community_chatrooms', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_chatrooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"ChatRoom {self.pk}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message {self.pk} by {self.sender_id} in room {self.room_id}"
    


def validate_youtube_url(value):
    """Validate that the URL is a YouTube video URL."""
    if 'youtube.com' not in value and 'youtu.be' not in value:
        raise ValidationError('URL must be a YouTube video URL')

class VideoCategory(models.Model):
    """Categories for organizing videos (e.g., Documentaries, Talk Shows, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, help_text="Lucide icon name, e.g., 'film' or 'tv'")
    color_from = models.CharField(max_length=50, default='from-brand-red', help_text="Tailwind gradient color (from)")
    color_to = models.CharField(max_length=50, default='to-red-700', help_text="Tailwind gradient color (to)")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Video Category'
        verbose_name_plural = 'Video Categories'

    def __str__(self):
        return self.name

class Video(models.Model):
    """Videos that can be either uploaded files or YouTube embeds."""
    CONTENT_TYPES = [
        ('youtube', 'YouTube Embed'),
        ('upload', 'Uploaded Video'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(VideoCategory, on_delete=models.PROTECT, related_name='videos')
    
    # Content can be either uploaded or embedded
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='youtube')
    youtube_url = models.URLField(
        blank=True, 
        help_text='YouTube video URL (used if content_type is youtube)',
        validators=[URLValidator(), validate_youtube_url]
    )
    video_file = models.FileField(
        upload_to='videos/',
        blank=True,
        help_text='Video file (used if content_type is upload)'
    )
    thumbnail = models.ImageField(
        upload_to='videos/thumbnails/',
        help_text='Thumbnail image shown before video plays'
    )

    # Meta information
    duration = models.CharField(max_length=50, help_text='Duration in format: "45 min" or "1:30:00"')
    is_featured = models.BooleanField(default=False, help_text='Feature this video prominently')
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        """Ensure either youtube_url or video_file is provided based on content_type."""
        if self.content_type == 'youtube' and not self.youtube_url:
            raise ValidationError('YouTube URL is required when content type is YouTube')
        if self.content_type == 'upload' and not self.video_file:
            raise ValidationError('Video file is required when content type is Upload')
        
        # Extract video ID from YouTube URL for consistent storage
        if self.content_type == 'youtube' and self.youtube_url:
            if 'youtube.com/watch?v=' in self.youtube_url:
                self.youtube_url = self.youtube_url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in self.youtube_url:
                self.youtube_url = self.youtube_url.split('youtu.be/')[1]

    def get_video_id(self):
        """Return the video ID (either YouTube ID or file path)."""
        if self.content_type == 'youtube':
            return self.youtube_url
        return self.video_file.url if self.video_file else None

    def get_absolute_url(self):
        return f'/tv/{self.slug}/'