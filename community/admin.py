from django.contrib import admin
from .models import (
	Organizer,
	FeaturedSpeaker,
	Partner,
	PastEdition,
	ChatRoom,
	Message,
)
from django.utils.html import format_html


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
	list_display = ("name", "title", "link")


@admin.register(FeaturedSpeaker)
class FeaturedSpeakerAdmin(admin.ModelAdmin):
	list_display = ("name", "title", "link")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
	list_display = ("id", "logo_preview")

	def logo_preview(self, obj):
		# If partner has an uploaded logo show thumbnail, otherwise show a Font Awesome icon
		if getattr(obj, 'logo', None):
			try:
				return format_html("<img src='{}' style='max-height:48px; object-fit:contain;'/>", obj.logo.url)
			except Exception:
				pass
		return format_html("<i class='fas fa-handshake' style='font-size:22px;color:#0D1B52;'></i>")
	logo_preview.short_description = "Logo"


@admin.register(PastEdition)
class PastEditionAdmin(admin.ModelAdmin):
	list_display = ("year", "location", "theme")
	readonly_fields = ()


@admin.action(description="Set subscription status to active")
def set_subscription_active(modeladmin, request, queryset):
	updated = queryset.update(status='active')
	modeladmin.message_user(request, f"Marked {updated} subscriptions active")


@admin.action(description="Set subscription status to cancelled")
def set_subscription_cancelled(modeladmin, request, queryset):
	updated = queryset.update(status='cancelled')
	modeladmin.message_user(request, f"Marked {updated} subscriptions cancelled")



@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
	list_display = ('id', 'icon', 'name', 'created_by', 'created_at')
	filter_horizontal = ('members',)

	def icon(self, obj):
		# Show chat icon; if room has a custom image attribute, prefer that (fallback to FA icon)
		return format_html("<i class='fas fa-comments' style='font-size:18px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'room', 'sender', 'created_at')
	list_filter = ('room', 'sender')
