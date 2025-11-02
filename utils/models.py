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




