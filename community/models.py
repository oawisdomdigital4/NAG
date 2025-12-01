from django.db import models
from django.db.models import F
from django.conf import settings
from django.core.validators import URLValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from .user_activity import UserActivity
from django.core.cache import cache
import json
import uuid


def generate_invite_token():
    return uuid.uuid4().hex


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


# --- Community ---
class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    is_corporate_group = models.BooleanField(default=False)
    # Whether the group is private (requires invitation) - optional feature
    is_private = models.BooleanField(default=False)
    # Image fields for profile picture and banner
    profile_picture = models.ImageField(upload_to='community/group_profiles/', blank=True, null=True)
    profile_picture_url = models.URLField(blank=True, null=True)
    banner = models.ImageField(upload_to='community/group_banners/', blank=True, null=True)
    banner_url = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_created_groups')
    # Moderators are selected from existing group members
    moderators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='moderated_groups', blank=True)
    # Optional: link group to facilitator courses (for course discussion groups)
    # Using string reference to avoid circular imports with courses app
    courses = models.ManyToManyField('courses.Course', related_name='community_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def delete(self, *args, **kwargs):
        """Override delete to properly handle relationships (SQLite limitation).
        
        SQLite is strict about FK constraints even within transactions, so we need to
        explicitly delete all related objects BEFORE deleting the Group itself.
        """
        from django.db import transaction
        
        with transaction.atomic():
            # Delete all related objects explicitly first
            # (CASCADE would handle this but SQLite enforces it strictly)
            self.posts.all().delete()  # Post has FK to Group with CASCADE
            self.invites.all().delete()  # GroupInvite has FK to Group with CASCADE
            self.memberships.all().delete()  # GroupMembership has FK to Group with CASCADE
            
            # Clear M2M relationships (SQLite doesn't cascade M2M deletes)
            self.moderators.clear()
            self.courses.clear()
            
            # Now delete the group itself
            super().delete(*args, **kwargs)

class GroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)


class GroupInvite(models.Model):
    """Invite records for private or invite-only groups."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invites')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_group_invites')
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_group_invites')
    invited_email = models.EmailField(blank=True, null=True)
    token = models.CharField(max_length=64, unique=True, default=generate_invite_token)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_group_invites')

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def mark_expired(self):
        self.status = 'expired'
        self.save(update_fields=['status'])


class Post(models.Model):
    # Allow null group for posts that target the general community feed
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='community_posts')
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    
    # Post category for better organization and filtering
    POST_CATEGORY_CHOICES = (
        ('general', 'General Discussion'),
        ('announcement', 'Announcement'),
        ('event', 'Event'),
        ('job_posting', 'Job Posting'),
        ('resource', 'Resource'),
        ('question', 'Question'),
    )
    post_category = models.CharField(max_length=50, choices=POST_CATEGORY_CHOICES, default='general')
    
    # Controls whether post appears only in group, globally, or is private to author
    FEED_VISIBILITY_CHOICES = (
        ('group_only', 'Group only'),
        ('public_global', 'Public global'),
        ('private', 'Private (only author)'),
    )
    feed_visibility = models.CharField(max_length=20, choices=FEED_VISIBILITY_CHOICES, default='group_only')
    
    # Media and link previews
    media_urls = models.JSONField(default=list, blank=True)
    link_previews = models.JSONField(default=list, blank=True)
    
    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    ranking_score = models.FloatField(default=0.0)
    
    # Sponsorship
    is_sponsored = models.BooleanField(default=False)
    sponsored_campaign = models.ForeignKey('SponsoredPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    
    # Flags and moderation
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    moderation_status = models.CharField(max_length=20, default='approved')
    moderation_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-ranking_score']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['group', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title or self.content[:50]} by {self.author_id}"

    def update_ranking(self, save=True):
        """Update engagement and ranking scores."""
        from .feed import FeedRanker
        
        # Calculate engagement score
        self.engagement_score = FeedRanker.calculate_engagement_score(self)
        
        # Calculate final ranking incorporating all factors
        time_decay = FeedRanker.calculate_time_decay(self.created_at)
        role_boost = FeedRanker.calculate_role_boost(self)
        sponsored_boost = FeedRanker.calculate_sponsored_boost(self)
        
        self.ranking_score = self.engagement_score * time_decay * role_boost * sponsored_boost
        
        if save:
            self.save(update_fields=['engagement_score', 'ranking_score', 'updated_at'])
            self.cache_ranking()
    
    def increment_view(self):
        """Increment view count and update ranking."""
        Post.objects.filter(id=self.id).update(
            view_count=F('view_count') + 1,
            last_activity_at=timezone.now()
        )
        self.refresh_from_db(fields=['view_count', 'last_activity_at'])
        self.update_ranking()
    
    def cache_ranking(self):
        """Cache ranking score for fast feed generation."""
        try:
            # Cache post data for quick retrieval (expire after 1 hour)
            cache_key = f'post:{self.id}'
            cache_data = {
                'id': self.id,
                'author_id': self.author_id,
                'group_id': self.group_id,
                'title': self.title,
                'content': self.content[:500],  # Cache preview only
                'engagement_score': self.engagement_score,
                'ranking_score': self.ranking_score,
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat()
            }
            
            # Use Django's cache framework
            cache.set(cache_key, json.dumps(cache_data), timeout=3600)
            
            # Cache the ranking score in memory
            rankings = cache.get('post_rankings') or {}
            rankings[str(self.id)] = self.ranking_score
            cache.set('post_rankings', rankings, timeout=3600)
            
        except Exception:
            # Log error but don't fail if caching is unavailable
            pass

    @staticmethod
    def get_feed_page(page=1, page_size=20, user=None, feed_type='global'):
        """Get a page of ranked posts from cache if available."""
        try:
            # Get cached rankings
            rankings = cache.get('post_rankings') or {}
            
            # Sort posts by ranking score
            sorted_posts = sorted(rankings.items(), key=lambda x: float(x[1]), reverse=True)
            
            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            page_post_ids = [post_id for post_id, _ in sorted_posts[start:end]]
            
            # Try to get posts from cache
            posts = []
            missing_ids = []
            
            for post_id in page_post_ids:
                cached_data = cache.get(f'post:{post_id}')
                
                if cached_data:
                    posts.append(json.loads(cached_data))
                else:
                    missing_ids.append(post_id)
            
            # Fetch missing posts from database
            if missing_ids:
                from .feed import FeedRanker
                db_posts = FeedRanker.rank_queryset(
                    Post.objects.filter(id__in=missing_ids)
                )
                
                # Add fetched posts to result and cache them
                for post in db_posts:
                    post.cache_ranking()
                    posts.append({
                        'id': post.id,
                        'author_id': post.author_id,
                        'group_id': post.group_id,
                        'title': post.title,
                        'content': post.content[:500],
                        'engagement_score': post.engagement_score,
                        'ranking_score': post.ranking_score,
                        'created_at': post.created_at.isoformat(),
                        'updated_at': post.updated_at.isoformat()
                    })
            
            return posts
            
        except Exception:
            # Fallback to database if Redis is unavailable
            from .feed import FeedRanker
            posts = FeedRanker.get_feed_for_user(user) if user else FeedRanker.rank_queryset(Post.objects.all())
            return posts[start:end]


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
    

# --- Opportunities ---

# --- Withdrawals ---
class WithdrawalRequest(models.Model):
    """Withdrawal requests for facilitators"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.status})"

# --- Partner Directory ---
class PartnerDirectory(models.Model):
    """Directory of corporate partners"""
    company = models.OneToOneField('CorporateVerification', on_delete=models.CASCADE, related_name='directory_listing')
    industry_tags = models.JSONField(default=list)
    services = models.JSONField(default=list)
    achievements = models.JSONField(default=list)
    social_links = models.JSONField(default=dict)
    showcase_images = models.JSONField(default=list)
    featured = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Partner Directory'

    def __str__(self):
        return f"{self.company.company_name} Directory"

# --- Corporate Connection ---
class CorporateConnection(models.Model):
    """Connections between corporate users"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"


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
    # Optional field for admin to provide a reason when approving/rejecting
    review_reason = models.TextField(blank=True)
    # Supporting documents for verification
    business_registration_doc = models.FileField(upload_to='corporate_verification/documents/', null=True, blank=True)
    tax_certificate_doc = models.FileField(upload_to='corporate_verification/documents/', null=True, blank=True)
    additional_docs = models.JSONField(default=list, blank=True, help_text='Additional document URLs/metadata')

    def __str__(self):
        return f"{self.company_name} ({self.status})"


# ============================================================================
# EXTENDED COMMUNITY SYSTEM MODELS
# ============================================================================
# (See models_extended.py for complete implementations of these models)
# These models implement all 10 requirements for the community system

from django.core.validators import MinValueValidator, MaxValueValidator


# ============================================================================
# 1. SUBSCRIPTION TIERS & MONETIZATION
# ============================================================================
# Note: User Subscription model is in payments.models.Subscription
# This defines the tier configurations for subscription features

class SubscriptionTier(models.Model):
    """Subscription tier configuration with feature permissions"""
    TIER_CHOICES = [
        ('individual', 'Individual - $1/month'),
        ('facilitator', 'Facilitator - $5/month'),
        ('corporate', 'Corporate - $500/year'),
        ('free', 'Free'),
    ]
    
    tier_type = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    
    # Feature permissions per tier
    max_posts_per_day = models.IntegerField(default=10)
    can_create_groups = models.BooleanField(default=True)
    can_sponsor_posts = models.BooleanField(default=False)
    can_post_opportunities = models.BooleanField(default=False)
    can_collaborate = models.BooleanField(default=False)
    priority_feed_ranking = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} (${self.price})"


# ============================================================================
# 2. USER ENGAGEMENT SCORING
# ============================================================================

class UserEngagementScore(models.Model):
    """Track user engagement metrics for feed ranking and growth"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagement_score')
    
    total_posts = models.PositiveIntegerField(default=0)
    total_likes_received = models.PositiveIntegerField(default=0)
    total_comments_received = models.PositiveIntegerField(default=0)
    total_mentions = models.PositiveIntegerField(default=0)
    
    facilitator_authority_score = models.FloatField(default=0.0)
    corporate_campaign_score = models.FloatField(default=0.0)
    engagement_score = models.FloatField(default=0.0)
    
    last_activity = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-engagement_score']
    
    def recalculate_score(self):
        """Recalculate engagement score based on recent activity"""
        self.engagement_score = (
            (self.total_likes_received * 0.2) +
            (self.total_comments_received * 0.5) +
            (self.total_mentions * 0.3)
        )
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - Score: {self.engagement_score:.1f}"


# ============================================================================
# 3. SPONSORED POSTS & CAMPAIGNS
# ============================================================================

class SponsoredPost(models.Model):
    """Sponsored post campaigns"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
        ('expired', 'Expired'),
    ]
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sponsored_posts')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(10)])
    daily_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    promotion_level = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


# ============================================================================
# 4. OPPORTUNITIES (Jobs, Internships, Events)
# Note: Notifications are handled by the notifications app
# ============================================================================

class CorporateOpportunity(models.Model):
    """Corporate opportunities"""
    TYPE_CHOICES = [
        ('job', 'Job'),
        ('internship', 'Internship'),
        ('event', 'Event'),
        ('project', 'Project'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
        ('draft', 'Draft'),
    ]
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='opportunities')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    opportunity_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    location = models.CharField(max_length=255, blank=True)
    remote_friendly = models.BooleanField(default=True)
    
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    
    deadline = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    
    requirements = models.TextField(blank=True, help_text='Comma-separated list of requirements')
    
    view_count = models.PositiveIntegerField(default=0)
    application_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.opportunity_type})"


class OpportunityApplication(models.Model):
    """User applications to opportunities"""
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ]
    
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='opportunity_applications')
    opportunity = models.ForeignKey(CorporateOpportunity, on_delete=models.CASCADE, related_name='applications')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    cover_letter = models.TextField(blank=True)
    resume_url = models.URLField(blank=True)
    
    # LinkedIn-style fields for better tracking
    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewer_notes = models.TextField(blank=True)
    
    applied_at = models.DateTimeField(auto_now_add=True)
    status_updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Track if notifications have been sent
    approved_notification_sent = models.BooleanField(default=False)
    rejected_notification_sent = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('applicant', 'opportunity')
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['opportunity', 'status']),
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.applicant.username} - {self.opportunity.title} ({self.status})"


# ============================================================================
# 6. COLLABORATION & PARTNERSHIPS
# ============================================================================

class CollaborationRequest(models.Model):
    """Collaboration requests between users"""
    TYPE_CHOICES = [
        ('partnership', 'Partnership'),
        ('mentorship', 'Mentorship'),
        ('project', 'Project'),
        ('event', 'Event'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]
    
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaboration_requests_sent')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaboration_requests_received')
    
    collaboration_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    proposed_start = models.DateTimeField(null=True, blank=True)
    proposed_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('requester', 'recipient', 'collaboration_type', 'title')
    
    def __str__(self):
        return f"{self.collaboration_type}: {self.requester.username} → {self.recipient.username}"


# ============================================================================
# 7. ANALYTICS & GROWTH METRICS
# ============================================================================

class PlatformAnalytics(models.Model):
    """Platform-wide analytics snapshot"""
    date = models.DateField(auto_now_add=True, unique=True)
    
    total_users = models.PositiveIntegerField(default=0)
    active_users_today = models.PositiveIntegerField(default=0)
    new_users_today = models.PositiveIntegerField(default=0)
    
    posts_created = models.PositiveIntegerField(default=0)
    comments_created = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    mentions_count = models.PositiveIntegerField(default=0)
    
    subscriptions_active = models.PositiveIntegerField(default=0)
    mrr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics - {self.date}"


class TrendingTopic(models.Model):
    """Trending topics/hashtags"""
    topic = models.CharField(max_length=255, unique=True)
    mention_count = models.PositiveIntegerField(default=1)
    engagement_score = models.FloatField(default=0.0)
    
    last_mentioned = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-engagement_score']
    
    def __str__(self):
        return f"#{self.topic} ({self.mention_count} mentions)"


# ============================================================================
# MESSAGING SYSTEM
# ============================================================================

class CorporateMessage(models.Model):
    """Direct messages between corporate users"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_corporate_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_corporate_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}: {self.subject}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()


