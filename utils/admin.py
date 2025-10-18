from django.contrib import admin
from django.utils.html import format_html
from .models import FAQ, TeamMember, Career, ContactMessage


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
	list_display = ("icon", "question", "created_at") if hasattr(FAQ, 'question') else ("icon",)

	def icon(self, obj):
		return format_html("<i class='fas fa-question-circle' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
	list_display = ("photo_preview", "name", "role") if hasattr(TeamMember, 'name') else ("photo_preview",)

	def photo_preview(self, obj):
		img = getattr(obj, 'photo', None) or getattr(obj, 'avatar', None)
		if img:
			try:
				url = img.url if hasattr(img, 'url') else img
				return format_html("<img src='{}' style='max-height:48px; object-fit:contain; border-radius:6px;'/>", url)
			except Exception:
				pass
		return format_html("<i class='fas fa-user-tie' style='font-size:18px;color:#0D1B52;'></i>")
	photo_preview.short_description = ''


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
	list_display = ("icon", "title") if hasattr(Career, 'title') else ("icon",)

	def icon(self, obj):
		return format_html("<i class='fas fa-briefcase' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ("icon", "subject", "email") if hasattr(ContactMessage, 'subject') else ("icon",)

	def icon(self, obj):
		return format_html("<i class='fas fa-envelope' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''
