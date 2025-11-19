"""
Data export and reporting utilities
"""
import csv
from io import StringIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Avg, Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Enrollment, QuizSubmission, AssignmentSubmission
from .grading import ProgressTracker


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_student_progress(request, enrollment_id):
    """
    Export student progress report as CSV
    """
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
    except Enrollment.DoesNotExist:
        return Response({'error': 'Enrollment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Generate report
    report = ProgressTracker.get_student_report(enrollment)
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student Progress Report'])
    writer.writerow(['Course', enrollment.course.title])
    writer.writerow(['Student', enrollment.user.get_full_name()])
    writer.writerow(['Enrolled At', enrollment.enrolled_at.strftime('%Y-%m-%d')])
    writer.writerow([])
    
    # Summary
    writer.writerow(['Summary'])
    writer.writerow(['Overall Progress %', report['progress']['overall_progress']])
    writer.writerow(['Total Lessons', report['progress']['total_lessons']])
    writer.writerow(['Completed Lessons', report['progress']['completed_lessons']])
    writer.writerow(['Quiz Average %', report['progress']['quiz_average']])
    writer.writerow(['Assignment Average %', report['progress']['assignment_average']])
    writer.writerow([])
    
    # Recent Quizzes
    writer.writerow(['Recent Quizzes'])
    writer.writerow(['Lesson', 'Score', 'Date', 'Passed'])
    for quiz in report['recent_quizzes']:
        writer.writerow([
            quiz['lesson_title'],
            quiz['score'],
            quiz['submitted_at'][:10],
            'Yes' if quiz['passed'] else 'No'
        ])
    writer.writerow([])
    
    # Recent Assignments
    writer.writerow(['Recent Assignments'])
    writer.writerow(['Lesson', 'Score', 'Date', 'Graded By'])
    for assignment in report['recent_assignments']:
        writer.writerow([
            assignment['lesson_title'],
            assignment['score'],
            assignment['submitted_at'][:10],
            assignment['graded_by']
        ])
    writer.writerow([])
    
    # Recommendations
    writer.writerow(['Recommendations'])
    for rec in report['recommendations']:
        writer.writerow([rec])
    
    # Create response
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="progress_report_{enrollment_id}.csv"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_course_analytics(request, course_id):
    """
    Export course analytics report as CSV (instructor only)
    """
    try:
        course = Course.objects.get(id=course_id, facilitator=request.user)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found or unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get enrollments
    enrollments = Enrollment.objects.filter(course=course).select_related('user')
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Course Analytics Report'])
    writer.writerow(['Course', course.title])
    writer.writerow(['Facilitator', request.user.get_full_name()])
    writer.writerow(['Report Date', datetime.now().strftime('%Y-%m-%d')])
    writer.writerow([])
    
    # Summary
    quiz_subs = QuizSubmission.objects.filter(lesson__module__course=course)
    assignment_subs = AssignmentSubmission.objects.filter(lesson__module__course=course)
    
    writer.writerow(['Summary'])
    writer.writerow(['Total Students', enrollments.count()])
    writer.writerow(['Total Enrollments', enrollments.count()])
    writer.writerow(['Average Progress %', enrollments.aggregate(Avg('progress'))['progress__avg'] or 0])
    writer.writerow(['Total Quiz Submissions', quiz_subs.count()])
    writer.writerow(['Average Quiz Score', quiz_subs.aggregate(Avg('score'))['score__avg'] or 0])
    writer.writerow(['Total Assignment Submissions', assignment_subs.count()])
    writer.writerow(['Average Assignment Score', assignment_subs.aggregate(Avg('score'))['score__avg'] or 0])
    writer.writerow([])
    
    # Student Breakdown
    writer.writerow(['Student Breakdown'])
    writer.writerow(['Student Name', 'Email', 'Progress %', 'Quizzes Completed', 'Avg Quiz Score', 'Assignments Completed', 'Avg Assignment Score'])
    
    for enrollment in enrollments:
        student_quizzes = quiz_subs.filter(enrollment__user=enrollment.user)
        student_assignments = assignment_subs.filter(enrollment__user=enrollment.user)
        
        writer.writerow([
            enrollment.user.get_full_name(),
            enrollment.user.email,
            enrollment.progress,
            student_quizzes.count(),
            round(student_quizzes.aggregate(Avg('score'))['score__avg'] or 0, 2),
            student_assignments.count(),
            round(student_assignments.aggregate(Avg('score'))['score__avg'] or 0, 2)
        ])
    
    # Create response
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="course_analytics_{course_id}.csv"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_statistics(request, course_id):
    """
    Get detailed course statistics (instructor only)
    """
    try:
        course = Course.objects.get(id=course_id, facilitator=request.user)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found or unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    enrollments = Enrollment.objects.filter(course=course)
    quiz_subs = QuizSubmission.objects.filter(lesson__module__course=course, graded=True)
    assignment_subs = AssignmentSubmission.objects.filter(lesson__module__course=course, graded=True)
    
    # Calculate statistics
    total_students = enrollments.count()
    avg_progress = enrollments.aggregate(Avg('progress'))['progress__avg'] or 0
    
    quiz_stats = {
        'total_submissions': quiz_subs.count(),
        'avg_score': round(quiz_subs.aggregate(Avg('score'))['score__avg'] or 0, 2),
        'passing_rate': round((quiz_subs.filter(score__gte=70).count() / quiz_subs.count() * 100) if quiz_subs.count() > 0 else 0, 2)
    }
    
    assignment_stats = {
        'total_submissions': assignment_subs.count(),
        'avg_score': round(assignment_subs.aggregate(Avg('score'))['score__avg'] or 0, 2),
        'auto_graded_count': assignment_subs.filter(auto_graded=True).count(),
        'manual_graded_count': assignment_subs.filter(auto_graded=False).count()
    }
    
    # Get top performers
    top_students = []
    for enrollment in enrollments.order_by('-progress')[:5]:
        progress = ProgressTracker.calculate_lesson_progress(enrollment)
        top_students.append({
            'student_name': enrollment.user.get_full_name(),
            'progress': enrollment.progress,
            'quiz_average': progress['quiz_average'],
            'assignment_average': progress['assignment_average']
        })
    
    # Performance distribution
    performance_dist = {
        'excellent': enrollments.filter(progress__gte=90).count(),
        'good': enrollments.filter(progress__gte=75, progress__lt=90).count(),
        'fair': enrollments.filter(progress__gte=50, progress__lt=75).count(),
        'needs_work': enrollments.filter(progress__lt=50).count()
    }
    
    return Response({
        'course': course.title,
        'total_students': total_students,
        'avg_progress': round(avg_progress, 2),
        'quiz_statistics': quiz_stats,
        'assignment_statistics': assignment_stats,
        'top_performers': top_students,
        'performance_distribution': performance_dist
    })
