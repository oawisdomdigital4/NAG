from django.contrib import admin
from django.utils.html import format_html
from .models import Author, Category, Tag, Article


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
