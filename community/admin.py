from django.contrib import admin
from .models import (
	Organizer,
	FeaturedSpeaker,
	Partner,
	PastEdition,
	ChatRoom,
	Message,
)
from admin_mixins import IconAdminMixin


@admin.register(Organizer)
class OrganizerAdmin(IconAdminMixin, admin.ModelAdmin):
	list_display = ("name", "title", "link", "icon_preview")
	readonly_fields = ("icon_preview",)
	icon_field = 'image'


@admin.register(FeaturedSpeaker)
class FeaturedSpeakerAdmin(IconAdminMixin, admin.ModelAdmin):
	list_display = ("name", "title", "link", "icon_preview")
	readonly_fields = ("icon_preview",)
	icon_field = 'image'


@admin.register(Partner)
class PartnerAdmin(IconAdminMixin, admin.ModelAdmin):
	list_display = ("id", "icon_preview")
	readonly_fields = ("icon_preview",)
	icon_field = 'logo'


@admin.register(PastEdition)
class PastEditionAdmin(IconAdminMixin, admin.ModelAdmin):
	list_display = ("year", "location", "theme", "icon_preview")
	readonly_fields = ("icon_preview",)
	icon_field = 'image'


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
	list_display = ('id', 'name', 'created_by', 'created_at')
	filter_horizontal = ('members',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'room', 'sender', 'created_at')
	list_filter = ('room', 'sender')
