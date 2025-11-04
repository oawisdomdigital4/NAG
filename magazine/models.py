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


class Magazine(models.Model):
	title = models.CharField(max_length=300)
	issue = models.CharField(max_length=100)
	slug = models.SlugField(max_length=320, unique=True)
	description = models.TextField(blank=True)
	cover_image = models.ImageField(upload_to='magazine/covers/', null=True, blank=True)
	pdf_file = models.FileField(upload_to='magazine/pdfs/', help_text="Upload the magazine PDF file")
	pages = models.PositiveIntegerField(default=0, help_text="Total number of pages")
	published_date = models.DateField()
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-published_date', '-created_at']

	def __str__(self):
		return f"{self.title} - {self.issue}"

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(f"{self.title} {self.issue}")[:320]
		
		# Check if this is a new instance or if pdf_file has changed
		if not self.pk or 'pdf_file' in kwargs.get('update_fields', []):
			try:
				# If this is an update and we have a new file, delete the old one
				old_instance = Magazine.objects.get(pk=self.pk)
				if old_instance.pdf_file != self.pdf_file:
					old_instance.pdf_file.delete(save=False)
			except Magazine.DoesNotExist:
				pass
			
			# Update page count from new PDF if available
			if self.pdf_file and hasattr(self.pdf_file, 'file'):
				from PyPDF2 import PdfReader
				try:
					reader = PdfReader(self.pdf_file)
					self.pages = len(reader.pages)
				except Exception as e:
					# Log the error but don't prevent saving
					print(f"Error reading PDF: {e}")
		
		super().save(*args, **kwargs)
	
	def delete(self, *args, **kwargs):
		# Delete the files when the model instance is deleted
		if self.cover_image:
			self.cover_image.delete(save=False)
		if self.pdf_file:
			self.pdf_file.delete(save=False)
		super().delete(*args, **kwargs)
