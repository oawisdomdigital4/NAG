from django.contrib import admin
from django.utils.html import format_html
from .models import Author, Category, Tag, Article, Magazine
from PyPDF2 import PdfReader


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
	list_display = ('icon', 'name', 'role')
	search_fields = ('name', 'role')

	def icon(self, obj):
		return format_html("<i class='fas fa-user' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('icon', 'name', 'slug')
	prepopulated_fields = {'slug': ('name',)}

	def icon(self, obj):
		return format_html("<i class='fas fa-folder' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ('icon', 'name', 'slug')
	prepopulated_fields = {'slug': ('name',)}

	def icon(self, obj):
		return format_html("<i class='fas fa-tag' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
	list_display = ('icon', 'title', 'category', 'author', 'date', 'views', 'likes')
	search_fields = ('title', 'excerpt', 'content')
	list_filter = ('category', 'tags', 'date')
	prepopulated_fields = {'slug': ('title',)}
	raw_id_fields = ('author',)

	def icon(self, obj):
		return format_html("<i class='fas fa-newspaper' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(Magazine)
class MagazineAdmin(admin.ModelAdmin):
	list_display = ('icon', 'title', 'issue', 'published_date', 'pages', 'is_active')
	list_filter = ('is_active', 'published_date')
	search_fields = ('title', 'issue', 'description')
	prepopulated_fields = {'slug': ('title', 'issue')}
	readonly_fields = ('pages',)

	def icon(self, obj):
		return format_html("<i class='fas fa-book' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''

	def save_model(self, request, obj, form, change):
		if 'pdf_file' in form.changed_data:
			try:
				# Create a new file handle for reading
				pdf_file = form.cleaned_data['pdf_file']
				# Reset the file pointer to the beginning
				pdf_file.seek(0)
				pdf = PdfReader(pdf_file)
				obj.pages = len(pdf.pages)
			except Exception as e:
				self.message_user(request, f"Error reading PDF: {str(e)}", level='ERROR')
				obj.pages = 0
		super().save_model(request, obj, form, change)
