from django.db import models
from django.core.validators import URLValidator, MinValueValidator
from django.core.exceptions import ValidationError

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


