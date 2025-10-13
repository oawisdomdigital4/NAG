from django.contrib import admin
from .models import AIModelToggle, FAQ, Testimonial, TeamMember, Career, ContactMessage, Page


@admin.register(AIModelToggle)
class AIModelToggleAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "enabled")


admin.site.register(FAQ)
admin.site.register(Testimonial)
admin.site.register(TeamMember)
admin.site.register(Career)
admin.site.register(ContactMessage)
admin.site.register(Page)
