from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import random
import string
from django.core.validators import URLValidator, MinValueValidator
# --- Community models are defined in the `community` app. Import them here
# to avoid duplicate class definitions. This keeps `accounts` code clean and
# ensures a single source of truth for community & payments models.
from community.models import (
    Group,
    GroupMembership,
    Post,
    Comment,
    CorporateVerification,
)
from payments.models import Plan, Subscription, Payment

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
    expertise_areas = models.JSONField(default=list, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    
    # --- Facilitator Wallet System (3-Balance Model) ---
    # earning_balance: Total amount earned from course sales (non-spendable, record-keeping)
    earning_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Total earned from course sales')
    
    # pending_balance: Earned money under processing (escrow, held temporarily)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Earned but not yet cleared (processing period)')
    
    # available_balance: Spendable money (cleared earnings + top-ups + admin credits)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Usable balance for withdrawals/campaigns/promotions')
    
    # Flag set when a user is approved to access community features
    community_approved = models.BooleanField(default=False)
    # Public avatar URL for the user (can be blank). Use a URL field to avoid
    # Support both a stored ImageField (server-side upload) and an external URL.
    # ImageField will store uploaded avatars under MEDIA_ROOT/avatars/.
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Backwards-compatible public avatar URL for external hosts
    avatar_url = models.CharField(max_length=512, blank=True, default='')
    # Portfolio URL for showcasing user work
    portfolio_url = models.CharField(max_length=512, blank=True, default='')
    
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


class OTPVerification(models.Model):
    """Model to store OTP verification records for signup, password reset, etc."""
    
    OTP_TYPE_CHOICES = [
        ('signup', 'Signup Verification'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp_verification', null=True, blank=True)
    otp_code = models.CharField(max_length=6, unique=True)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, default='signup')
    email = models.EmailField()  # Email to which OTP was sent
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp_type}"
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, email, user=None, otp_type='signup'):
        """Create or update OTP for user/email"""
        from datetime import timedelta
        
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        
        otp, created = cls.objects.update_or_create(
            email=email,
            otp_type=otp_type,
            defaults={
                'otp_code': otp_code,
                'user': user,
                'expires_at': expires_at,
                'is_verified': False,
                'attempts': 0,
            }
        )
        return otp
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid_attempt(self):
        """Check if user can still attempt verification"""
        return self.attempts < self.max_attempts
    
    def verify_otp(self, provided_otp):
        """
        Verify if provided OTP matches
        Returns: (is_valid, message)
        """
        if self.is_verified:
            return False, "OTP already verified"
        
        if self.is_expired():
            return False, "OTP has expired"
        
        if not self.is_valid_attempt():
            return False, f"Maximum attempts exceeded. Please request a new OTP."
        
        self.attempts += 1
        self.save()
        
        if self.otp_code == provided_otp:
            self.is_verified = True
            self.save()
            return True, "OTP verified successfully"
        
        remaining_attempts = self.max_attempts - self.attempts
        if remaining_attempts == 0:
            return False, "Maximum attempts exceeded. Please request a new OTP."
        
        return False, f"Invalid OTP. {remaining_attempts} attempts remaining."
    
    def resend_otp(self):
        """Generate new OTP and reset attempts"""
        from datetime import timedelta
        
        self.otp_code = self.generate_otp()
        self.expires_at = timezone.now() + timedelta(minutes=10)
        self.attempts = 0
        self.is_verified = False
        self.save()
        return self.otp_code



