from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Course, CourseModule
from .analytics_models import AnalyticsSettings, FacilitatorTarget
from django.db.models.functions import TruncDate

class ProgressTracker:
    @staticmethod
    def get_facilitator_progress(user, days=30):
        """Get comprehensive progress tracking for a facilitator."""
        period_start = timezone.now() - timedelta(days=days)
        
        # Get all courses by the facilitator
        courses = Course.objects.filter(facilitator=user)
        total_courses = courses.count()
        
        # Calculate revenue progress
        # NOTE: Enrollment model uses `enrolled_at` as the timestamp field.
        # Use TruncDate on the correct field and compare to the period start date.
        # Aggregate revenue by summing the enrolled course price for enrollments
        # in the period. Payments are stored separately and may not have a
        # direct FK to Enrollment, so summing course price is a reliable proxy
        # for facilitator revenue for now.
        earnings_data = courses.annotate(
            date=TruncDate('enrollments__enrolled_at')
        ).values('date').annotate(
            daily_revenue=Sum('enrollments__course__price')
        ).filter(
            date__gte=period_start.date(),
            daily_revenue__isnull=False
        ).order_by('date')
        
        # Get analytics settings
        settings = AnalyticsSettings.objects.first()
        if not settings:
            settings = AnalyticsSettings.objects.create()
            
        # Get facilitator-specific targets
        facilitator_targets = FacilitatorTarget.objects.filter(facilitator=user).first()
        
        # Calculate revenue progress
        monthly_target = (
            facilitator_targets.custom_revenue_target 
            if facilitator_targets and facilitator_targets.custom_revenue_target 
            else settings.monthly_revenue_target
        )
        current_revenue = float(sum(item.get('daily_revenue', 0) or 0 for item in earnings_data))
        revenue_progress = (current_revenue / float(monthly_target) * 100) if monthly_target > 0 else 0
        
        # Calculate student progress
        student_target = (
            facilitator_targets.custom_student_target 
            if facilitator_targets and facilitator_targets.custom_student_target 
            else settings.student_target
        )
        current_students = courses.aggregate(
            total_students=Count('enrollments', distinct=True)
        )['total_students'] or 0
        student_progress = (current_students / student_target * 100) if student_target > 0 else 0
        
        # Calculate rating progress
        rating_target = (
            facilitator_targets.custom_rating_target 
            if facilitator_targets and facilitator_targets.custom_rating_target 
            else settings.ideal_rating_target
        )
        current_rating = courses.aggregate(
            avg_rating=Avg('reviews__rating')
        )['avg_rating'] or 0
        rating_progress = (current_rating / rating_target * 100) if rating_target > 0 else 0
        
        # Calculate engagement progress
        # Get engagement target
        engagement_target = (
            facilitator_targets.custom_engagement_target 
            if facilitator_targets and facilitator_targets.custom_engagement_target 
            else settings.lesson_completion_target
        )
        
        # Compute engagement as the average enrollment progress across the
        # facilitator's courses (0-100). This avoids relying on a separate
        # student_progress relation that may not exist in all deployments.
        avg_enrollment_progress = courses.aggregate(avg_progress=Avg('enrollments__progress'))['avg_progress'] or 0
        current_engagement = float(avg_enrollment_progress)
        engagement_progress = (current_engagement / engagement_target * 100) if engagement_target > 0 else 0
        
        # Save analytics report
        from .analytics_models import AnalyticsReport
        AnalyticsReport.objects.create(
            facilitator=user,
            period_days=days,
            total_revenue=current_revenue,
            revenue_growth=float(settings.monthly_revenue_target),
            total_students=current_students,
            student_growth=student_progress,
            average_rating=current_rating,
            rating_growth=rating_progress,
            engagement_rate=current_engagement,
            engagement_growth=engagement_progress,
            report_data={
                'revenue': {'current': current_revenue, 'target': float(monthly_target)},
                'students': {'current': current_students, 'target': student_target},
                'rating': {'current': current_rating, 'target': rating_target},
                'engagement': {'current': current_engagement, 'target': engagement_target},
                'earnings_data': list(earnings_data),
            }
        )
        
        return {
            'revenue': {
                'current': current_revenue,
                'target': monthly_target,
                'progress': min(revenue_progress, 100)
            },
            'students': {
                'current': current_students,
                'target': student_target,
                'progress': min(student_progress, 100)
            },
            'rating': {
                'current': current_rating,
                'target': rating_target,
                'progress': min(rating_progress, 100)
            },
            'engagement': {
                'current': current_engagement,
                'target': engagement_target,
                'progress': min(engagement_progress, 100)
            }
        }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_progress_data(request):
    """Get progress tracking data for the authenticated facilitator."""
    days = int(request.query_params.get('days', 30))
    try:
        progress_data = ProgressTracker.get_facilitator_progress(request.user, days)
        return Response(progress_data)
    except Exception as exc:
        # Log the error server-side and return a safe default payload so the
        # frontend doesn't crash while we iterate on backend fixes. The
        # response includes an `error` field to help debugging in dev.
        logging.exception("Error computing facilitator progress")
        safe_payload = {
            'revenue': {'current': 0, 'target': 0, 'progress': 0},
            'students': {'current': 0, 'target': 0, 'progress': 0},
            'rating': {'current': 0, 'target': 0, 'progress': 0},
            'engagement': {'current': 0, 'target': 0, 'progress': 0},
            'error': str(exc),
        }
        return Response(safe_payload, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics_settings(request):
    """Return analytics settings for the dashboard (admin-managed)."""
    settings = AnalyticsSettings.objects.first()
    if not settings:
        settings = AnalyticsSettings.objects.create()

    data = {
        'monthly_revenue_target': float(settings.monthly_revenue_target),
        'student_target': settings.student_target,
        'minimum_rating_target': settings.minimum_rating_target,
        'ideal_rating_target': settings.ideal_rating_target,
        'lesson_completion_target': settings.lesson_completion_target,
        'analytics_time_period': settings.analytics_time_period,
        'progress_warning_threshold': settings.progress_warning_threshold,
        'progress_success_threshold': settings.progress_success_threshold,
        'dashboard_refresh_interval': settings.dashboard_refresh_interval,
    }
    return Response(data)