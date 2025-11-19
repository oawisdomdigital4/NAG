from django.db import models

class FAQ(models.Model):
	question = models.CharField(max_length=255)
	answer = models.TextField()
	category = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)


class TeamMember(models.Model):
    name = models.CharField(max_length=255)
    # `title` removed — use `bio` and other fields for description/role information
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='team/', blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ContactDetails(models.Model):
    # Primary contact methods
    contact_email = models.EmailField(help_text='Main contact email address')
    contact_phone = models.CharField(max_length=50, help_text='Main contact phone number')
    contact_hours = models.CharField(max_length=100, default='Mon-Fri, 9AM-6PM EAT', help_text='Business hours')
    headquarters_address = models.CharField(max_length=255, help_text='Main headquarters location')
    
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contact Details'
        verbose_name_plural = 'Contact Details'

    def __str__(self):
        return f'Contact Details ({self.created_at.strftime("%Y-%m-%d")})'


class OfficeLocation(models.Model):
    contact_details = models.ForeignKey(ContactDetails, on_delete=models.CASCADE, related_name='office_locations')
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address = models.TextField()
    type = models.CharField(max_length=255, help_text='E.g. Headquarters, Regional Office')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'city']

    def __str__(self):
        return f"{self.city}, {self.country}"


class DepartmentContact(models.Model):
    contact_details = models.ForeignKey(ContactDetails, on_delete=models.CASCADE, related_name='department_contacts')
    title = models.CharField(max_length=255)
    email = models.EmailField()
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class Career(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField()
	location = models.CharField(max_length=100, blank=True)
	type = models.CharField(max_length=50, blank=True)  # e.g. Full-time, Part-time
	requirements = models.TextField(blank=True)
	how_to_apply = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

class ContactMessage(models.Model):
	# Keep a legacy `name` for compatibility but store first/last separately
	first_name = models.CharField(max_length=100, blank=True)
	last_name = models.CharField(max_length=100, blank=True)
	name = models.CharField(max_length=200, blank=True)
	email = models.EmailField()
	subject = models.CharField(max_length=255, blank=True)
	inquiry_type = models.CharField(max_length=100, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	@property
	def full_name(self):
		if self.name:
			return self.name
		return f"{(self.first_name or '').strip()} {(self.last_name or '').strip()}".strip()

	def save(self, *args, **kwargs):
		# Ensure the legacy 'name' is populated for older admin views
		if not self.name:
			self.name = self.full_name
		super().save(*args, **kwargs)

# --- Footer Content ---
class FooterContent(models.Model):
    """Editable footer content model. Stores all the links, text and social media
    info needed to render the site footer. Frontend will load the latest published entry.
    """
    # Company section
    company_name = models.CharField(max_length=255, help_text='Company name shown in footer')
    tagline = models.CharField(max_length=255, blank=True)
    address_text = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Social media links
    social_facebook = models.URLField(blank=True)
    social_twitter = models.URLField(blank=True)
    social_instagram = models.URLField(blank=True)
    social_linkedin = models.URLField(blank=True)
    social_youtube = models.URLField(blank=True)
    
    # Company links
    company_about = models.URLField(blank=True, help_text='About Us page URL')
    company_team = models.URLField(blank=True, help_text='Team page URL')
    company_careers = models.URLField(blank=True, help_text='Careers page URL')
    company_contact = models.URLField(blank=True, help_text='Contact Us page URL')
    
    # Platform links
    platforms_magazine = models.URLField(blank=True)
    platforms_tv = models.URLField(blank=True)
    platforms_institute = models.URLField(blank=True)
    platforms_summit = models.URLField(blank=True)
    platforms_community = models.URLField(blank=True)
    
    # Account links
    account_login = models.URLField(blank=True)
    account_signup = models.URLField(blank=True)
    account_faqs = models.URLField(blank=True)
    
    # Legal links
    legal_terms = models.URLField(blank=True, help_text='Terms of Service URL')
    legal_privacy = models.URLField(blank=True, help_text='Privacy Policy URL')
    legal_help = models.URLField(blank=True, help_text='Help/Support URL')
    
    # Footer bottom
    copyright_text = models.CharField(max_length=255, blank=True)
    
    # Publishing
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Footer Content'
        verbose_name_plural = 'Footer Content'

    def __str__(self):
        return f"Footer Content ({self.created_at.isoformat()})"


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