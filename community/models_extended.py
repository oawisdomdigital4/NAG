"""
Extended Community System Models covering all 10 requirements.
Includes:
- Global Feed & Posts (with ranking)
- Group System (facilitator, corporate, private, moderators)
- Engagement (Likes, Comments, Mentions)
- Notifications (unified notification engine)
- Sponsored Posts & Campaigns
- Opportunities (Jobs, Internships, Events)
- Collaboration (Partnerships, Requests)
- Analytics & Growth Metrics
- Subscriptions & Monetization
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


# ============================================================================
# 1. SUBSCRIPTION & MONETIZATION
# ============================================================================

class SubscriptionTier(models.Model):
    """Subscription tier configuration"""
    TIER_CHOICES = [
        ('individual', 'Individual - $1/month'),
        ('facilitator', 'Facilitator - $5/month'),
        ('corporate', 'Corporate - $500/year'),
        ('free', 'Free'),
    ]
    
    tier_type = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)  # 30 for monthly, 365 for yearly
    
    # Features & permissions
    max_posts_per_day = models.IntegerField(default=10)
    can_create_groups = models.BooleanField(default=True)
    can_sponsor_posts = models.BooleanField(default=False)
    can_post_opportunities = models.BooleanField(default=False)
    can_collaborate = models.BooleanField(default=False)
    priority_feed_ranking = models.IntegerField(default=1, help_text="Higher = better ranking")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} (${self.price})"


class Subscription(models.Model):
    """User subscription record"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_subscription')
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    renewal_date = models.DateTimeField(null=True, blank=True)
    
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=200, unique=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()
    
    def __str__(self):
        return f"{self.user.username} - {self.tier.name}"


# ============================================================================
# 2. USER ROLES & ENGAGEMENT SCORING
# ============================================================================

class UserEngagementScore(models.Model):
    """Track user engagement metrics for feed ranking and growth"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagement_score')
    
    total_posts = models.PositiveIntegerField(default=0)
    total_likes_received = models.PositiveIntegerField(default=0)
    total_comments_received = models.PositiveIntegerField(default=0)
    total_mentions = models.PositiveIntegerField(default=0)
    
    # For Facilitators: authority score based on group activity
    facilitator_authority_score = models.FloatField(default=0.0)  # 0-100
    
    # For Corporate: campaign performance score
    corporate_campaign_score = models.FloatField(default=0.0)  # 0-100
    
    # Engagement score used in feed ranking
    engagement_score = models.FloatField(default=0.0)
    
    last_activity = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-engagement_score']
    
    def recalculate_score(self):
        """Recalculate engagement score based on recent activity"""
        likes_weight = 0.2
        comments_weight = 0.5
        mentions_weight = 0.3
        
        self.engagement_score = (
            (self.total_likes_received * likes_weight) +
            (self.total_comments_received * comments_weight) +
            (self.total_mentions * mentions_weight)
        )
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - Score: {self.engagement_score:.1f}"


# ============================================================================
# 3. GLOBAL FEED & POSTS
# ============================================================================

class Post(models.Model):
    """Extended Post model with ranking, sponsorship, media"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    FEED_VISIBILITY_CHOICES = [
        ('public', 'Public Global'),
        ('group_only', 'Group Only'),
        ('followers_only', 'Followers Only'),
        ('private', 'Private'),
    ]
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_posts')
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    feed_visibility = models.CharField(max_length=20, choices=FEED_VISIBILITY_CHOICES, default='public')
    
    # Media
    media_urls = models.JSONField(default=list, blank=True)  # URLs to images/videos
    link_preview = models.JSONField(default=dict, blank=True)  # {url, title, description, image}
    
    # Engagement metrics
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    mention_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Ranking scores
    engagement_score = models.FloatField(default=0.0)
    relevance_score = models.FloatField(default=0.0)
    recency_boost = models.FloatField(default=0.0)
    ranking_score = models.FloatField(default=0.0)  # Final feed ranking
    
    # Sponsored posts
    is_sponsored = models.BooleanField(default=False)
    sponsor = models.ForeignKey('SponsoredPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    promotion_level = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Moderation
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    moderation_status = models.CharField(max_length=20, default='approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-ranking_score', '-created_at']
        indexes = [
            models.Index(fields=['-ranking_score']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['group', '-created_at']),
        ]
    
    def calculate_engagement_score(self):
        """Calculate engagement score from interactions"""
        self.engagement_score = (
            (self.like_count * 0.2) +
            (self.comment_count * 0.5) +
            (self.mention_count * 0.3)
        )
    
    def calculate_ranking_score(self):
        """Calculate final ranking score for feed"""
        self.calculate_engagement_score()
        
        # Time decay: newer posts score higher
        time_diff = timezone.now() - self.created_at
        days_old = max(1, time_diff.days)
        self.recency_boost = 100 / (1 + (days_old ** 1.5))
        
        # Combine scores
        base_score = self.engagement_score + self.recency_boost
        
        # Apply promotion level for sponsored posts
        if self.is_sponsored and self.promotion_level > 0:
            base_score = base_score * (1 + (self.promotion_level * 0.1))
        
        # Role weight
        role = getattr(self.author.profile, 'role', 'individual')
        role_weights = {'corporate': 1.5, 'facilitator': 1.2, 'individual': 1.0}
        base_score = base_score * role_weights.get(role, 1.0)
        
        self.ranking_score = base_score
    
    def __str__(self):
        return f"{self.author.username} - {self.title or self.content[:50]}"


class Like(models.Model):
    """Post/Comment likes"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post', 'comment')
        indexes = [models.Index(fields=['post', 'created_at'])]
    
    def __str__(self):
        return f"{self.user.username} liked {'post' if self.post else 'comment'}"


class Comment(models.Model):
    """Comments on posts"""
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['post', '-created_at'])]
    
    def __str__(self):
        return f"{self.author.username} commented on post"


class Mention(models.Model):
    """Track @mentions in posts and comments"""
    CONTENT_TYPE_CHOICES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
    ]
    
    mentioned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentions')
    mentioned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentions_made')
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('mentioned_user', 'content_type', 'post', 'comment')
        indexes = [models.Index(fields=['mentioned_user', '-created_at'])]
    
    def __str__(self):
        return f"{self.mentioned_by.username} mentioned {self.mentioned_user.username}"


# ============================================================================
# 4. GROUP SYSTEM
# ============================================================================

class Group(models.Model):
    """Community groups (Facilitator, Corporate, etc.)"""
    TYPE_CHOICES = [
        ('facilitator', 'Facilitator Group'),
        ('corporate', 'Corporate Group'),
        ('community', 'Community Group'),
        ('interest', 'Interest Group'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('invite_only', 'Invite Only'),
    ]
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    group_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    
    # Media
    logo = models.ImageField(upload_to='groups/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='groups/banners/', blank=True, null=True)
    
    # Metadata
    member_count = models.PositiveIntegerField(default=1)
    post_count = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    
    # Settings
    allow_external_posts = models.BooleanField(default=False)
    require_approval = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-engagement_score', '-member_count']
        indexes = [models.Index(fields=['group_type', 'privacy'])]
    
    def __str__(self):
        return f"{self.name} ({self.group_type})"


class GroupMembership(models.Model):
    """Group membership with roles"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Moderation permissions
    can_moderate_posts = models.BooleanField(default=False)
    can_manage_members = models.BooleanField(default=False)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'group')
        indexes = [models.Index(fields=['group', 'role'])]
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role})"


class GroupInvitation(models.Model):
    """Invite-only group invitations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_invitations_sent')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_invitations_received')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('group', 'invitee')
    
    def __str__(self):
        return f"Invite {self.invitee.username} to {self.group.name}"


# ============================================================================
# 5. SPONSORED POSTS & CAMPAIGNS
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
    
    # Budget & duration
    budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(10)])
    daily_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    promotion_level = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Performance metrics
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    ctr = models.FloatField(default=0.0)  # Click-through rate
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


# ============================================================================
# 6. NOTIFICATIONS
# ============================================================================

class Notification(models.Model):
    """Unified notification system"""
    TYPE_CHOICES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('mention', 'Mention'),
        ('group_join', 'Group Join'),
        ('collaboration', 'Collaboration'),
        ('opportunity', 'Opportunity'),
        ('message', 'Message'),
        ('system', 'System'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_sent')
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    
    # Related objects
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery channels
    email_sent = models.BooleanField(default=False)
    in_app = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.type} notification for {self.recipient.username}"


# ============================================================================
# 7. OPPORTUNITIES (Jobs, Internships, Events)
# ============================================================================

class CorporateOpportunity(models.Model):
    """Corporate opportunities (jobs, internships, events)"""
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
    
    # Details
    location = models.CharField(max_length=255, blank=True)
    remote_friendly = models.BooleanField(default=True)
    
    # Salary (optional)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    
    # Timeline
    deadline = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    
    # Engagement
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
    
    applied_at = models.DateTimeField(auto_now_add=True)
    status_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('applicant', 'opportunity')
    
    def __str__(self):
        return f"{self.applicant.username} - {self.opportunity.title}"


# ============================================================================
# 8. COLLABORATION & PARTNERSHIPS
# ============================================================================

class CollaborationRequest(models.Model):
    """Collaboration requests between users/orgs"""
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
    
    # Timeline
    proposed_start = models.DateTimeField(null=True, blank=True)
    proposed_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('requester', 'recipient', 'collaboration_type', 'title')
    
    def __str__(self):
        return f"{self.collaboration_type}: {self.requester.username} → {self.recipient.username}"


# ============================================================================
# 9. ANALYTICS & GROWTH METRICS
# ============================================================================

class PlatformAnalytics(models.Model):
    """Platform-wide analytics snapshot"""
    date = models.DateField(auto_now_add=True, unique=True)
    
    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    active_users_today = models.PositiveIntegerField(default=0)
    new_users_today = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    posts_created = models.PositiveIntegerField(default=0)
    comments_created = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    mentions_count = models.PositiveIntegerField(default=0)
    
    # Revenue
    subscriptions_active = models.PositiveIntegerField(default=0)
    mrr = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Monthly recurring revenue
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics - {self.date}"


class TrendingTopic(models.Model):
    """Trending topics/hashtags on the platform"""
    topic = models.CharField(max_length=255, unique=True)
    mention_count = models.PositiveIntegerField(default=1)
    engagement_score = models.FloatField(default=0.0)
    
    last_mentioned = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-engagement_score']
    
    def __str__(self):
        return f"#{self.topic} ({self.mention_count} mentions)"
