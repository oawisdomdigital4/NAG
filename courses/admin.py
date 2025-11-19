from django.contrib import admin
from .models import (
    Course, CourseModule, CourseReview, Enrollment,
    Lesson, QuizQuestion, QuizSubmission, AssignmentSubmission
)
from .analytics_models import AnalyticsSettings, FacilitatorTarget, AnalyticsReport
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
    list_display = ("icon", "title", "course", "order")
    def icon(self, obj):
        return format_html("<i class='fas fa-layer-group' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    search_fields = ("title", "course__title")

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ("icon", "course", "user", "rating", "created_at")
    def icon(self, obj):
        return format_html("<i class='fas fa-star' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    search_fields = ("course__title", "user__email")


class QuizQuestionInline(admin.TabularInline):
    """Inline editor for quiz questions"""
    model = QuizQuestion
    extra = 1
    fields = ('question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("icon", "title", "module", "lesson_type", "order", "get_duration")
    list_filter = ("lesson_type", "module__course")
    search_fields = ("title", "module__title", "module__course__title")
    readonly_fields = ("module",)
    inlines = [QuizQuestionInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('module', 'title', 'description', 'lesson_type', 'order')
        }),
        ('Video Lesson', {
            'fields': ('video_url', 'duration_minutes'),
            'classes': ('collapse',)
        }),
        ('Article Lesson', {
            'fields': ('article_content',),
            'classes': ('collapse',)
        }),
        ('Quiz Lesson', {
            'fields': ('quiz_title', 'questions_count', 'passing_score'),
            'classes': ('collapse',)
        }),
        ('Assignment Lesson', {
            'fields': ('assignment_title', 'due_date', 'estimated_hours'),
            'classes': ('collapse',)
        }),
    )
    
    def icon(self, obj):
        icons = {
            'video': '🎥',
            'quiz': '❓',
            'assignment': '📝',
            'article': '📖'
        }
        return icons.get(obj.lesson_type, '📚')
    icon.short_description = ''
    
    def get_duration(self, obj):
        if obj.duration_minutes:
            return f"{obj.duration_minutes} min"
        return "-"
    get_duration.short_description = "Duration"


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("icon", "question_text", "lesson", "correct_option")
    list_filter = ("lesson__module__course", "lesson")
    search_fields = ("question_text", "lesson__title")
    
    def icon(self, obj):
        return format_html("<i class='fas fa-question-circle' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ("icon", "enrollment", "lesson", "score", "graded", "submitted_at")
    list_filter = ("graded", "submitted_at", "lesson__module__course")
    search_fields = ("enrollment__user__email", "lesson__title")
    readonly_fields = ("enrollment", "lesson", "submitted_at", "answers")
    
    def icon(self, obj):
        return format_html("<i class='fas fa-check-square' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    
    def has_add_permission(self, request):
        return False  # Submissions are created via API
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("icon", "enrollment", "lesson", "score", "graded", "auto_graded", "submitted_at")
    list_filter = ("graded", "auto_graded", "submitted_at", "lesson__module__course")
    search_fields = ("enrollment__user__email", "lesson__title")
    readonly_fields = ("enrollment", "lesson", "submitted_at", "content")
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('enrollment', 'lesson', 'submitted_at')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Grading', {
            'fields': ('score', 'graded', 'auto_graded')
        }),
    )
    
    def icon(self, obj):
        return format_html("<i class='fas fa-file-alt' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    
    def has_add_permission(self, request):
        return False  # Submissions are created via API
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
@admin.register(AnalyticsSettings)
class AnalyticsSettingsAdmin(admin.ModelAdmin):
    """Admin interface for global analytics settings."""
    
    fieldsets = (
        ('Revenue Settings', {
            'fields': ('monthly_revenue_target',)
        }),
        ('Student Settings', {
            'fields': ('student_target',)
        }),
        ('Rating Settings', {
            'fields': ('minimum_rating_target', 'ideal_rating_target')
        }),
        ('Engagement Settings', {
            'fields': ('lesson_completion_target',)
        }),
        ('Display Settings', {
            'fields': (
                'analytics_time_period',
                'progress_warning_threshold',
                'progress_success_threshold',
                'dashboard_refresh_interval'
            )
        }),
    )

    def icon(self, obj):
        return format_html("<i class='fas fa-chart-line' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    
    def has_add_permission(self, request):
        # Only allow one instance of settings
        return not AnalyticsSettings.objects.exists()

@admin.register(FacilitatorTarget)
class FacilitatorTargetAdmin(admin.ModelAdmin):
    """Admin interface for facilitator-specific targets."""
    
    list_display = ('icon', 'facilitator_name', 'revenue_target_display', 'student_target_display', 
                   'rating_target_display', 'engagement_target_display', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('facilitator__username', 'facilitator__first_name', 'facilitator__last_name',
                    'notes')
    
    def icon(self, obj):
        return format_html("<i class='fas fa-bullseye' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    
    def facilitator_name(self, obj):
        return obj.facilitator.get_full_name() or obj.facilitator.username
    facilitator_name.short_description = "Facilitator"
    
    def revenue_target_display(self, obj):
        if obj.custom_revenue_target:
            return format_html('<span style="color: #1a73e8;">${}</span>', 
                             obj.custom_revenue_target)
        return "Using global target"
    revenue_target_display.short_description = "Revenue Target"
    
    def student_target_display(self, obj):
        if obj.custom_student_target:
            return format_html('<span style="color: #1a73e8;">{}</span>', 
                             obj.custom_student_target)
        return "Using global target"
    student_target_display.short_description = "Student Target"
    
    def rating_target_display(self, obj):
        if obj.custom_rating_target:
            return format_html('<span style="color: #1a73e8;">{:.1f}</span>', 
                             obj.custom_rating_target)
        return "Using global target"
    rating_target_display.short_description = "Rating Target"
    
    def engagement_target_display(self, obj):
        if obj.custom_engagement_target:
            return format_html('<span style="color: #1a73e8;">{}%</span>', 
                             obj.custom_engagement_target)
        return "Using global target"
    engagement_target_display.short_description = "Engagement Target"

@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    """Admin interface for saved analytics reports."""
    
    list_display = ('icon', 'report_date', 'facilitator_name', 'total_revenue', 'total_students',
                   'average_rating', 'engagement_rate')
    list_filter = ('report_date', 'facilitator')
    search_fields = ('facilitator__username', 'facilitator__first_name', 'facilitator__last_name')
    readonly_fields = ('report_date', 'created_at', 'report_data')
    
    def icon(self, obj):
        return format_html("<i class='fas fa-file-chart-line' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''
    
    def facilitator_name(self, obj):
        return obj.facilitator.get_full_name() or obj.facilitator.username
    facilitator_name.short_description = "Facilitator"
    
    def has_add_permission(self, request):
        # Reports should only be created by the system
        return False
    
    def has_change_permission(self, request, obj=None):
        # Reports should not be modified once created
        return False