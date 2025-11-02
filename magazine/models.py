from django.db import models
from django.utils.text import slugify


class Author(models.Model):
	name = models.CharField(max_length=200)
	avatar = models.ImageField(upload_to='authors/avatars/', null=True, blank=True)
	role = models.CharField(max_length=200, blank=True)
	bio = models.TextField(blank=True)

	def __str__(self):
		return self.name


class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=120, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name_plural = 'categories'

	def __str__(self):
		return self.name


class Tag(models.Model):
	name = models.CharField(max_length=50, unique=True)
	slug = models.SlugField(max_length=60, unique=True)

	def __str__(self):
		return self.name


class Article(models.Model):
	title = models.CharField(max_length=300)
	slug = models.SlugField(max_length=320, unique=True)
	excerpt = models.TextField(blank=True)
	content = models.TextField(blank=True)
	image = models.ImageField(upload_to='articles/images/', null=True, blank=True)
	pdf = models.FileField(upload_to='articles/pdfs/', null=True, blank=True)
	author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name='articles')
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
	tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
	date = models.DateField()
	read_time = models.CharField(max_length=50, blank=True)
	views = models.PositiveIntegerField(default=0)
	likes = models.PositiveIntegerField(default=0)
	comments_count = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-date', '-created_at']

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)[:320]
		super().save(*args, **kwargs)
