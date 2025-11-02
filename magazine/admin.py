from django.contrib import admin
from .models import Author, Category, Tag, Article


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
	list_display = ('name', 'role')
	search_fields = ('name', 'role')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'author', 'date', 'views', 'likes')
	search_fields = ('title', 'excerpt', 'content')
	list_filter = ('category', 'tags', 'date')
	prepopulated_fields = {'slug': ('title',)}
	raw_id_fields = ('author',)
