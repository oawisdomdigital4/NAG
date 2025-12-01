from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    CourseViewSet, CourseModuleViewSet, CourseReviewViewSet,
    LessonViewSet, QuizQuestionViewSet, QuizSubmissionViewSet, AssignmentSubmissionViewSet,
    ProgressReportViewSet
)
from .progress_tracking import get_progress_data, get_analytics_settings
from .exports import export_student_progress, export_course_analytics, get_course_statistics

# Create router - register all viewsets
router = DefaultRouter()

# Register non-slug endpoints first (to avoid slug pattern matching them)
router.register(r'course-modules', CourseModuleViewSet)
router.register(r'course-reviews', CourseReviewViewSet)
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'quiz-questions', QuizQuestionViewSet, basename='quiz-question')
router.register(r'quiz-submissions', QuizSubmissionViewSet, basename='quiz-submission')
router.register(r'assignment-submissions', AssignmentSubmissionViewSet, basename='assignment-submission')
router.register(r'progress-reports', ProgressReportViewSet, basename='progress-report')
# Register CourseViewSet last (with empty prefix for list/create at /)
router.register(r'', CourseViewSet, basename='course')

urlpatterns = router.urls + [
    path('progress/', get_progress_data, name='progress-data'),
    path('settings/', get_analytics_settings, name='analytics-settings'),
    path('export/student-progress/<int:enrollment_id>/', export_student_progress, name='export-student-progress'),
    path('export/course-analytics/<int:course_id>/', export_course_analytics, name='export-course-analytics'),
    path('statistics/course/<int:course_id>/', get_course_statistics, name='course-statistics'),
]
