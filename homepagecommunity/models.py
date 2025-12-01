from django.db import models
from django.utils.text import slugify


class HeroSection(models.Model):
    """Main hero section of the community page"""
    title_line_1 = models.CharField(max_length=100, default="One Million Voices.")
    title_line_2 = models.CharField(max_length=100, default="One Africa.")
    title_line_3 = models.CharField(max_length=100, default="One Movement.")
    subtitle = models.TextField(default="Join a global community of Africans, innovators, facilitators, and leaders shaping tomorrow.")
    
    # Pricing tiers shown in hero
    individual_price = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    individual_period = models.CharField(max_length=20, default="Month")
    
    facilitator_price = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    facilitator_period = models.CharField(max_length=20, default="Month")
    
    corporate_price = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    corporate_period = models.CharField(max_length=20, default="Year")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Section"
    
    def __str__(self):
        return "Community Hero Section"


class AboutCommunityMission(models.Model):
    """About section with mission and features"""
    mission_label = models.CharField(max_length=50, default="Our Mission")
    mission_title = models.CharField(max_length=200, default="More Than a Forum")
    mission_description = models.TextField(
        default="The New Africa Community is more than a forum — it's a continental movement uniting individuals and organizations across Africa and the diaspora into a single ecosystem of empowerment, visibility, and influence."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "About Community"
        verbose_name_plural = "About Community"
    
    def __str__(self):
        return self.mission_title


class CommunityFeature(models.Model):
    """Features displayed in About section"""
    FEATURE_CHOICES = [
        ('mentorship', 'Mentorship'),
        ('education', 'Education'),
        ('networking', 'Networking'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    feature_type = models.CharField(max_length=20, choices=FEATURE_CHOICES)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Community Feature"
    
    def __str__(self):
        return self.title


class SubscriptionTier(models.Model):
    """Subscription tier configuration (Individual, Facilitator, Corporate)"""
    TIER_CHOICES = [
        ('individual', 'Individual'),
        ('facilitator', 'Facilitator'),
        ('corporate', 'Corporate'),
    ]
    
    tier_type = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=20, help_text="e.g., Month, Year")
    description = models.TextField()
    
    # Color theming
    label_color = models.CharField(max_length=50, default="text-cool-blue")
    bg_color = models.CharField(max_length=50, default="bg-white")
    button_color = models.CharField(max_length=50, default="bg-brand-red")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription Tier"
    
    def __str__(self):
        return f"{self.get_tier_type_display()} - ${self.price}/{self.period}"


class SubscriptionBenefit(models.Model):
    """Benefits for each subscription tier"""
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.CASCADE, related_name='benefits')
    title = models.CharField(max_length=150)
    description = models.TextField()
    icon_name = models.CharField(max_length=50, help_text="Lucide React icon name")
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tier', 'order']
        verbose_name = "Subscription Benefit"
    
    def __str__(self):
        return f"{self.tier.get_tier_type_display()} - {self.title}"


class Testimonial(models.Model):
    """Community testimonials"""
    name = models.CharField(max_length=150)
    title = models.CharField(max_length=200, help_text="e.g., Tech Entrepreneur, Nigeria")
    quote = models.TextField()
    image = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order']
        verbose_name = "Testimonial"
    
    def __str__(self):
        return f"{self.name} - {self.title}"


class FinalCTA(models.Model):
    """Final Call To Action section"""
    title_part_1 = models.CharField(max_length=100, default="The future of Africa depends on those who")
    title_teach = models.CharField(max_length=50, default="teach")
    title_connect = models.CharField(max_length=50, default="connect")
    title_empower = models.CharField(max_length=50, default="empower")
    
    subtitle = models.CharField(max_length=300, default="Join the movement. Shape the narrative. Build the future.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Final CTA"
        verbose_name_plural = "Final CTAs"
    
    def __str__(self):
        return "Final Call To Action"


class CommunityMetrics(models.Model):
    """Community statistics and metrics"""
    total_members = models.IntegerField(default=0)
    active_groups = models.IntegerField(default=0)
    total_posts = models.IntegerField(default=0)
    total_facilitators = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Community Metrics"
        verbose_name_plural = "Community Metrics"
    
    def __str__(self):
        return "Community Metrics"
