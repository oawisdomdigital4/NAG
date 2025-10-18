from django.contrib import admin
from .models import (
	Organizer,
	FeaturedSpeaker,
	Partner,
	PastEdition,
	ChatRoom,
	Message,
)


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
	list_display = ("name", "title", "link")


@admin.register(FeaturedSpeaker)
class FeaturedSpeakerAdmin(admin.ModelAdmin):
	list_display = ("name", "title", "link")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
	list_display = ("id", "logo")


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
	list_display = ('id', 'name', 'created_by', 'created_at')
	filter_horizontal = ('members',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'room', 'sender', 'created_at')
	list_filter = ('room', 'sender')
