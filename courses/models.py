from django.db import models
from accounts.models import User
from .analytics_models import AnalyticsSettings, FacilitatorTarget, AnalyticsReport

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
	thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
	thumbnail_url = models.URLField(blank=True)
	preview_video = models.FileField(upload_to='course_previews/', blank=True, null=True)
	preview_video_url = models.URLField(blank=True)
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
	# Publication/status fields used by the frontend
	STATUS_CHOICES = [
		("draft", "Draft"),
		("published", "Published"),
	]
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
	is_published = models.BooleanField(default=False)
	published_at = models.DateTimeField(null=True, blank=True)
	facilitator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_facilitated')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)



class CourseModule(models.Model):
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
	title = models.CharField(max_length=255)
	content = models.TextField()
	order = models.PositiveIntegerField(default=0)

class Lesson(models.Model):
	LESSON_TYPE_CHOICES = [
		('video', 'Video'),
		('quiz', 'Quiz'),
		('assignment', 'Assignment'),
		('article', 'Article'),
	]
	module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
	order = models.PositiveIntegerField(default=0)
	# Video fields
	video_url = models.URLField(blank=True, null=True)
	duration_minutes = models.PositiveIntegerField(blank=True, null=True)
	# Article fields
	article_content = models.TextField(blank=True, null=True)
	# Quiz fields
	quiz_title = models.CharField(max_length=255, blank=True, null=True)
	questions_count = models.PositiveIntegerField(blank=True, null=True)
	passing_score = models.PositiveIntegerField(blank=True, null=True)
	# Assignment fields
	assignment_title = models.CharField(max_length=255, blank=True, null=True)
	due_date = models.DateField(blank=True, null=True)
	estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

class QuizQuestion(models.Model):
	lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
	question_text = models.TextField()
	option_a = models.CharField(max_length=255)
	option_b = models.CharField(max_length=255)
	option_c = models.CharField(max_length=255)
	option_d = models.CharField(max_length=255)
	correct_option = models.CharField(max_length=1, choices=[('a','A'),('b','B'),('c','C'),('d','D')])

class QuizSubmission(models.Model):
	enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_submissions')
	lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quiz_submissions')
	submitted_at = models.DateTimeField(auto_now_add=True)
	score = models.PositiveIntegerField(default=0)
	answers = models.JSONField(default=dict)  # {question_id: selected_option}
	graded = models.BooleanField(default=False)

class AssignmentSubmission(models.Model):
	enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='assignment_submissions')
	lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignment_submissions')
	submitted_at = models.DateTimeField(auto_now_add=True)
	content = models.TextField(blank=True)
	score = models.PositiveIntegerField(default=0)
	graded = models.BooleanField(default=False)
	auto_graded = models.BooleanField(default=True)

class CourseReview(models.Model):
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	rating = models.PositiveIntegerField()
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
