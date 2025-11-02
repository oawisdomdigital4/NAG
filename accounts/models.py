from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
# --- Community models are defined in the `community` app. Import them here
# to avoid duplicate class definitions. This keeps `accounts` code clean and
# ensures a single source of truth for community & payments models.
from community.models import (
    Group,
    GroupMembership,
    Post,
    Comment,
    Plan,
    Subscription,
    Payment,
    CorporateVerification,
)

class UserToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.token}"



class User(AbstractUser):
    ROLE_CHOICES = (
        ('individual', 'Individual'),
        ('facilitator', 'Facilitator'),
        ('corporate', 'Corporate'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    subscription_status = models.CharField(max_length=20, default='none')
    subscription_type = models.CharField(max_length=20, blank=True)
    REQUIRED_FIELDS = ['username', 'role']
    USERNAME_FIELD = 'email'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True, default='1')
    country = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    expertise_areas = models.JSONField(default=list, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    # Flag set when a user is approved to access community features
    community_approved = models.BooleanField(default=False)
    # Public avatar URL for the user (can be blank). Use a URL field to avoid
    # Support both a stored ImageField (server-side upload) and an external URL.
    # ImageField will store uploaded avatars under MEDIA_ROOT/avatars/.
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Backwards-compatible public avatar URL for external hosts
    avatar_url = models.CharField(max_length=512, blank=True, default='')
    
class Follow(models.Model):
    """Simple follower relationship model: follower -> followed

    We keep this lightweight and explicit so we can count followers efficiently.
    """
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='following_set')
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        indexes = [models.Index(fields=['followed']), models.Index(fields=['follower'])]

    def __str__(self):
        return f"{self.follower} -> {self.followed}"




