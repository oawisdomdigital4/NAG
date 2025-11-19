from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class AnalyticsSettings(models.Model):
    """Global settings for analytics dashboard."""
    
    # Revenue targets
    monthly_revenue_target = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=5000.00,
        validators=[MinValueValidator(0)],
        help_text="Monthly revenue target for facilitators (in $)"
    )
    
    # Student targets
    student_target = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Target number of students per facilitator"
    )
    
    # Rating targets
    minimum_rating_target = models.FloatField(
        default=4.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Minimum acceptable rating for courses"
    )
    ideal_rating_target = models.FloatField(
        default=4.5,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Ideal rating target for courses"
    )
    
    # Engagement targets
    lesson_completion_target = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Target lesson completion rate (percentage)"
    )
    
    # Time periods
    analytics_time_period = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Default time period for analytics in days"
    )
    
    # Progress thresholds
    progress_warning_threshold = models.IntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Threshold percentage below which progress bars show warning color"
    )
    progress_success_threshold = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Threshold percentage above which progress bars show success color"
    )
    
    # Auto-refresh settings
    dashboard_refresh_interval = models.IntegerField(
        default=30,
        validators=[MinValueValidator(10)],
        help_text="Dashboard auto-refresh interval in seconds"
    )
    
    class Meta:
        verbose_name = "Analytics Settings"
        verbose_name_plural = "Analytics Settings"

class FacilitatorTarget(models.Model):
    """Individual targets for facilitators."""
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics_targets'
    )
    
    # Revenue targets
    custom_revenue_target = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Custom monthly revenue target (leave blank to use global)"
    )
    
    # Student targets
    custom_student_target = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Custom student target (leave blank to use global)"
    )
    
    # Rating targets
    custom_rating_target = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Custom rating target (leave blank to use global)"
    )
    
    # Engagement targets
    custom_engagement_target = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Custom engagement target percentage (leave blank to use global)"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Notes about this facilitator's targets"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Facilitator Target"
        verbose_name_plural = "Facilitator Targets"
        
    def __str__(self):
        return f"Targets for {self.facilitator.get_full_name() or self.facilitator.username}"

class AnalyticsReport(models.Model):
    """Saved analytics reports for historical tracking."""
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics_reports'
    )
    
    report_date = models.DateField(auto_now_add=True)
    period_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)]
    )
    
    # Revenue metrics
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    revenue_growth = models.FloatField(default=0)
    
    # Student metrics
    total_students = models.IntegerField(default=0)
    student_growth = models.FloatField(default=0)
    
    # Rating metrics
    average_rating = models.FloatField(default=0)
    rating_growth = models.FloatField(default=0)
    
    # Engagement metrics
    engagement_rate = models.FloatField(default=0)
    engagement_growth = models.FloatField(default=0)
    
    report_data = models.JSONField(
        default=dict,
        help_text="Full report data in JSON format"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Analytics Report"
        verbose_name_plural = "Analytics Reports"
        ordering = ['-report_date']
        
    def __str__(self):
        return f"Report for {self.facilitator.get_full_name() or self.facilitator.username} - {self.report_date}"