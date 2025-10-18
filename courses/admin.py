from django.contrib import admin
from .models import Course, CourseModule, CourseReview, Enrollment
from django.utils.html import format_html
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("icon", "user", "course", "progress", "enrolled_at")
    search_fields = ("user__email", "course__title")

    def icon(self, obj):
        return format_html("<i class='fas fa-user-graduate' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("icon", "title", "facilitator", "category", "level", "format", "is_featured", "price", "created_at", "updated_at", "enrollments_count")
    list_filter = ("category", "level", "format", "is_featured")
    search_fields = ("title", "facilitator__email")

    def get_queryset(self, request):
        from django.db.models import Count
        qs = super().get_queryset(request)
        return qs.annotate(enrollments_count=Count('enrollments'))

    def enrollments_count(self, obj):
        return getattr(obj, 'enrollments_count', 0)
    enrollments_count.admin_order_field = 'enrollments_count'
    enrollments_count.short_description = 'Enrollments'

    def icon(self, obj):
        return format_html("<i class='fas fa-book-open' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    search_fields = ("title", "course__title")

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "rating", "created_at")
    search_fields = ("course__title", "user__email")
