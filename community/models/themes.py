from django.db import models
from django.conf import settings

# Color choices for SummitTheme
COLOR_CHOICES = [
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

class SummitKeyThemes(models.Model):
    """Container model for Key Themes section"""
    title = models.CharField(max_length=255, default='Key Themes')
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SummitKeyThemes ({self.created_at.isoformat()})"


class SummitTheme(models.Model):
    """Theme item shown on the Key Themes section"""
    ICON_CHOICES = [
        ('Bot', 'AI Robot'),
        ('GraduationCap', 'Education'),
        ('Handshake', 'Partnership'),
        ('Sprout', 'Growth'),
        ('TrendingUp', 'Trends'),
    ]

    parent = models.ForeignKey(SummitKeyThemes, on_delete=models.CASCADE, related_name='themes')
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='Bot')
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=255,
        choices=COLOR_CHOICES,
        default='from-blue-500 to-blue-600',
        help_text='Choose a gradient color for the theme card'
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title