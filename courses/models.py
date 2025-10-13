from django.db import models
from accounts.models import User

class Enrollment(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
	course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='enrollments')
	progress = models.IntegerField(default=0)
	enrolled_at = models.DateTimeField(auto_now_add=True)


class Course(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(unique=True)
	short_description = models.CharField(max_length=500)
	full_description = models.TextField()
	thumbnail_url = models.URLField(blank=True)
	price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
	duration = models.CharField(max_length=50, blank=True)
	# New fields for frontend compatibility
	LEVEL_CHOICES = [
		("Beginner", "Beginner"),
		("Intermediate", "Intermediate"),
		("Advanced", "Advanced"),
	]
	level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="Beginner")
	CATEGORY_CHOICES = [
		("Business", "Business"),
		("Technology", "Technology"),
		("Creative", "Creative"),
		("Other", "Other"),
	]
	category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Other")
	FORMAT_CHOICES = [
		("Online", "Online"),
		("Self-paced", "Self-paced"),
		("Live", "Live"),
		("Hybrid", "Hybrid"),
	]
	format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="Online")
	is_featured = models.BooleanField(default=False)
	facilitator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_facilitated')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


class CourseModule(models.Model):
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
	title = models.CharField(max_length=255)
	content = models.TextField()
	order = models.PositiveIntegerField(default=0)

class CourseReview(models.Model):
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	rating = models.PositiveIntegerField()
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
