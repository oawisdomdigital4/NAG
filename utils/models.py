from django.db import models

class FAQ(models.Model):
	question = models.CharField(max_length=255)
	answer = models.TextField()
	category = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)


class TeamMember(models.Model):
	name = models.CharField(max_length=100)
	title = models.CharField(max_length=100)
	bio = models.TextField(blank=True)
	photo = models.ImageField(upload_to='team/', blank=True, null=True)
	social_links = models.URLField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

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




