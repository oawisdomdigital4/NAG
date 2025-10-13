from django.db import models

class FAQ(models.Model):
	question = models.CharField(max_length=255)
	answer = models.TextField()
	category = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

class Testimonial(models.Model):
	name = models.CharField(max_length=100)
	title = models.CharField(max_length=100, blank=True)
	quote = models.TextField()
	image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

class TeamMember(models.Model):
	name = models.CharField(max_length=100)
	title = models.CharField(max_length=100)
	bio = models.TextField(blank=True)
	photo = models.ImageField(upload_to='team/', blank=True, null=True)
	social_links = models.JSONField(default=dict, blank=True)
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
	name = models.CharField(max_length=100)
	email = models.EmailField()
	subject = models.CharField(max_length=255, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

class Page(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(unique=True)
	content = models.TextField()
	is_published = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


class AIModelToggle(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=100, unique=True)
	enabled = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.name} ({'enabled' if self.enabled else 'disabled'})"
