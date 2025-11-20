from django.contrib import admin
from django.utils.html import format_html
from .models import NewsletterSubscriber

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('icon', 'email', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def icon(self, obj):
        return format_html("<i class='fas fa-envelope-open' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''

    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True)
    activate_subscribers.short_description = "Mark selected subscribers as active"

    def deactivate_subscribers(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_subscribers.short_description = "Mark selected subscribers as inactive"
