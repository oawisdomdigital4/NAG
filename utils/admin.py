from django.contrib import admin
from django.utils.html import format_html
from .models import (
    FAQ,
    TeamMember,
    Career,
    ContactMessage,
    ContactDetails,
    OfficeLocation,
    DepartmentContact
)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
	list_display = ("icon", "question", "created_at") if hasattr(FAQ, 'question') else ("icon",)

	def icon(self, obj):
		return format_html("<i class='fas fa-question-circle' style='font-size:14px;color:#0D1B52;'></i>")
	icon.short_description = ''


# Team member and contact information admin
class OfficeLocationInline(admin.TabularInline):
    model = OfficeLocation
    extra = 1
    fields = ('city', 'country', 'address', 'type', 'order')


class DepartmentContactInline(admin.TabularInline):
    model = DepartmentContact
    extra = 1
    fields = ('title', 'email', 'description', 'order')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('photo_preview', 'name', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('photo_preview', 'created_at', 'updated_at')
    fields = (
        'name', 'bio', 'photo', 'photo_preview',
        'linkedin_url', 'twitter_url', 'email',
        'order', 'is_active',
        'created_at', 'updated_at'
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 48px; border-radius: 4px;">',
                obj.photo.url
            )
        return format_html('<i class="fas fa-user" style="font-size: 24px; color: #666;"></i>')
    photo_preview.short_description = 'Photo'


@admin.register(ContactDetails)
class ContactDetailsAdmin(admin.ModelAdmin):
    list_display = ('contact_email', 'contact_phone', 'is_published', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('contact_email', 'contact_phone', 'contact_hours', 'headquarters_address')
        }),
        ('Publishing', {
            'fields': ('is_published', 'created_at', 'updated_at')
        })
    )
    inlines = [OfficeLocationInline, DepartmentContactInline]


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
