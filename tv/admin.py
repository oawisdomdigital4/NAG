from django.contrib import admin
from django.utils.html import format_html
from .models import Video, VideoCategory


@admin.register(VideoCategory)
class VideoCategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'slug', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    ordering = ('order', 'name')

    def icon(self, obj):
        return format_html("<i class='fas fa-film' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('icon', 'title', 'category', 'content_type', 'view_count', 'is_featured', 'created_at')
    list_filter = ('category', 'content_type', 'is_featured', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'created_at', 'updated_at')

    def icon(self, obj):
        return format_html("<i class='fas fa-play-circle' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
