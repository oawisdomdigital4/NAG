from django.contrib import admin
from .models import FAQ, TeamMember, Career, ContactMessage
from admin_mixins import IconAdminMixin


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
	list_display = ("question", "category", "created_at")


@admin.register(TeamMember)
class TeamMemberAdmin(IconAdminMixin, admin.ModelAdmin):
	list_display = ("name", "title", "icon_preview")
	readonly_fields = ("icon_preview",)
	icon_field = 'photo'


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
	list_display = ("title", "location", "type", "is_active", "created_at")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ("full_name", "email", "subject", "created_at")
	readonly_fields = ("full_name",)
