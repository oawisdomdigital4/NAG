from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class SponsorCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('rejected', 'Rejected'),
        ('pending_payment', 'Pending Payment'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    PRIORITY_CHOICES = [
        (1, 'Standard'),
        (2, 'High'),
        (3, 'Premium')
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sponsor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sponsored_campaigns')
    sponsored_post = models.OneToOneField('community.Post', on_delete=models.CASCADE, related_name='sponsor_campaign')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority_level = models.IntegerField(choices=PRIORITY_CHOICES, default=1, help_text='Determines feed placement priority')
    budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text='Total campaign budget in USD')
    cost_per_view = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], help_text='Cost per view in USD')
    target_audience = models.JSONField(default=dict, blank=True)
    impression_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=255, blank=True)
    payment_status = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'start_date', 'end_date']), models.Index(fields=['sponsor', 'status'])]

    def __str__(self):
        return f"{self.title} by {self.sponsor.username} ({self.status})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date')

    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date

    def calculate_engagement_rate(self):
        if self.impression_count > 0:
            self.engagement_rate = (self.click_count / self.impression_count) * 100
            self.save(update_fields=['engagement_rate'])
        return self.engagement_rate

    def get_cost_per_click(self):
        """Calculate actual cost per click from budget and clicks"""
        if self.click_count == 0:
            return 0
        return float(self.budget) / self.click_count

    def get_cost_per_impression(self):
        """Calculate actual cost per impression from budget"""
        if self.impression_count == 0:
            return 0
        return float(self.budget) / self.impression_count

    def get_roi_multiplier(self):
        """Calculate ROI multiplier (impressions / budget)"""
        if self.budget == 0:
            return 0
        return self.impression_count / float(self.budget)

    def get_performance_metrics(self):
        """Get all key performance metrics for campaign"""
        # Base metrics from model fields
        metrics = {
            'impressions': self.impression_count,
            'clicks': self.click_count,
            'engagement_rate': round(self.engagement_rate, 2),
            'cost_per_click': round(self.get_cost_per_click(), 4),
            'cost_per_impression': round(self.get_cost_per_impression(), 6),
            'roi_multiplier': round(self.get_roi_multiplier(), 2),
            'budget': float(self.budget),
            'is_active': self.is_active(),
        }

        # Try to include engagement breakdown (likes, shares, comments, bookmarks, views)
        try:
            # EngagementLog is defined later in this module; resolved at runtime.
            qs = EngagementLog.objects.filter(metadata__campaign_id__in=[str(self.id), self.id])
            # Count by action type
            counts = {
                'view': 0,
                'like': 0,
                'comment': 0,
                'share': 0,
                'bookmark': 0,
            }
            totals = qs.values('action_type').order_by().annotate(count=models.Count('id'))
            for item in totals:
                at = item.get('action_type')
                if at in counts:
                    counts[at] = item.get('count', 0)

            metrics.update({
                'views': counts.get('view', 0) or self.impression_count,
                'likes': counts.get('like', 0),
                'comments': counts.get('comment', 0),
                'shares': counts.get('share', 0),
                'bookmarks': counts.get('bookmark', 0),
            })
        except Exception:
            # If anything goes wrong, fall back to basic fields
            metrics.update({
                'views': self.impression_count,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'bookmarks': 0,
            })

        return metrics


class CampaignAnalytics(models.Model):
    """Analytics data for campaigns"""
    campaign = models.ForeignKey('SponsorCampaign', on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    spend = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Campaign Analytics'
        unique_together = ['campaign', 'date']

    def __str__(self):
        return f"{self.campaign.title} - {self.date}"

    def calculate_ctr(self):
        """Calculate Click-Through Rate"""
        if self.impressions > 0:
            return (self.clicks / self.impressions) * 100
        return 0

    def calculate_conversion_rate(self):
        """Calculate Conversion Rate"""
        if self.clicks > 0:
            return (self.conversions / self.clicks) * 100
        return 0


class PromotionMetrics(models.Model):
    """Detailed metrics tracking for promotions and campaigns"""
    campaign = models.ForeignKey('SponsorCampaign', on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    # Engagement metrics
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    # Conversion metrics
    conversions = models.PositiveIntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Cost metrics
    spend = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cpc = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)  # Cost per click
    cpm = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)  # Cost per mille
    # ROI metrics
    roi = models.FloatField(default=0.0)  # Return on investment
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Promotion Metrics'
        unique_together = ['campaign', 'date']

    def __str__(self):
        return f"{self.campaign.title} Metrics - {self.date}"

    def calculate_metrics(self):
        """Calculate derived metrics"""
        # Engagement rate (clicks / impressions)
        if self.impressions > 0:
            self.engagement_rate = (self.clicks / self.impressions) * 100
        
        # Conversion rate (conversions / clicks)
        if self.clicks > 0:
            self.conversion_rate = (self.conversions / self.clicks) * 100
            self.cpc = self.spend / self.clicks
        
        # CPM (cost per thousand impressions)
        if self.impressions > 0:
            self.cpm = (self.spend / self.impressions) * 1000
        
        # ROI ((revenue - spend) / spend * 100)
        if self.spend > 0:
            self.roi = ((self.revenue - self.spend) / self.spend) * 100
        
        self.save()




class EngagementLog(models.Model):
    ACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('bookmark', 'Bookmark'),
        ('profile_view', 'Profile View'),
        ('group_join', 'Group Join'),
        ('post_create', 'Post Create'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='engagement_logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    post = models.ForeignKey('community.Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='engagement_logs')
    comment = models.ForeignKey('community.Comment', on_delete=models.SET_NULL, null=True, blank=True, related_name='engagement_logs')
    group = models.ForeignKey('community.Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='engagement_logs')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['action_type', 'created_at']), models.Index(fields=['user', 'action_type'])]

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.action_type} at {self.created_at}"
    
class FacilitatorEarning(models.Model):
    """Track earnings for facilitators"""
    facilitator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=100)  # e.g., 'course_sale', 'sponsorship'
    description = models.TextField(blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.facilitator.username} - {self.amount} ({self.source})"


class WithdrawalRequest(models.Model):
    """Track withdrawal requests from facilitators"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ]

    facilitator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='promotions_withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='promotions_processed_withdrawals'
    )

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.facilitator.username} - {self.amount} ({self.status})"

    def process(self, status, processed_by, notes=''):
        """Process the withdrawal request"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Processing withdrawal {self.id}: changing to {status}")
        
        self.status = status
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
        logger.info(f"Withdrawal {self.id} saved with status {status}")
        
        # If approved or completed, deduct from user's available_balance
        if status in ['approved', 'completed']:
            logger.info(f"Attempting to deduct balance for withdrawal {self.id}")
            profile = getattr(self.facilitator, 'profile', None)
            if profile:
                logger.info(f"Found profile for {self.facilitator.username}. Current available_balance: {profile.available_balance}")
                
                # Deduct the withdrawal amount from available_balance only
                withdrawal_amount = Decimal(str(self.amount))
                available_balance = Decimal(str(profile.available_balance or 0))
                
                # Deduct from available_balance
                if available_balance >= withdrawal_amount:
                    new_available = available_balance - withdrawal_amount
                    logger.info(f"Deducting {withdrawal_amount} from available_balance: {available_balance} -> {new_available}")
                else:
                    new_available = Decimal('0')
                    logger.warning(f"Insufficient available balance. Requested: {withdrawal_amount}, Available: {available_balance}")
                
                profile.available_balance = new_available
                profile.save()
                logger.info(f"Profile saved. New available_balance: {profile.available_balance}")
            else:
                logger.error(f"No profile found for user {self.facilitator.id}")
        else:
            logger.info(f"Status {status} is not approved or completed, skipping balance deduction")


class WalletTopUp(models.Model):
    """Track wallet top-up transactions for promotions budget"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_topups')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)  # e.g., 'credit_card', 'bank_transfer', 'paypal'
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"

    def mark_completed(self):
        """Mark the top-up as completed and add funds to user wallet"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Marking wallet top-up {self.id} as completed")
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Add amount directly to available_balance (top-ups go straight to available balance)
        profile = getattr(self.user, 'profile', None)
        if profile:
            profile.available_balance = (profile.available_balance or Decimal('0')) + Decimal(str(self.amount))
            profile.save()
            logger.info(f"Added ${self.amount} top-up to {self.user.username}'s available balance. New available: ${profile.available_balance}")
        else:
            logger.error(f"No profile found for user {self.user.id}")

    def mark_failed(self, error_message=''):
        """Mark the top-up as failed"""
        self.status = 'failed'
        if error_message:
            self.notes = error_message
        self.save()
