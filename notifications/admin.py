from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationPreference


@admin.action(description="Mark selected notifications as read")
def make_read(modeladmin, request, queryset):
	updated = queryset.filter(read=False).update(read=True)
	modeladmin.message_user(request, f"Marked {updated} notifications as read")


@admin.action(description="Mark selected notifications as unread")
def make_unread(modeladmin, request, queryset):
	updated = queryset.filter(read=True).update(read=False)
	modeladmin.message_user(request, f"Marked {updated} notifications as unread")


@admin.action(description="Archive selected notifications")
def archive_notifications(modeladmin, request, queryset):
	updated = queryset.filter(archived=False).update(archived=True)
	modeladmin.message_user(request, f"Archived {updated} notifications")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ("id", "icon", "title", "short_message", "user", "category", "read", "archived", "created_at")
	list_filter = ("category", "read", "archived", "created_at")
	search_fields = ("title", "message", "user__email", "user__first_name", "user__last_name")
	readonly_fields = ("created_at", "read_at", "email_sent_at", "archived_at")
	actions = (make_read, make_unread, archive_notifications)

	def short_message(self, obj):
		if not obj.message:
			return ""
		return (obj.message[:75] + "...") if len(obj.message) > 75 else obj.message

	short_message.short_description = "Message"

	def icon(self, obj):
		# Use a small envelope icon for notifications; could be customized per category
		return format_html("<i class='fas fa-envelope' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "notification_type", "in_app_enabled", "email_enabled", "created_at")
	list_filter = ("in_app_enabled", "email_enabled", "notification_type")
	search_fields = ("user__email", "notification_type")
	readonly_fields = ("created_at", "updated_at")

