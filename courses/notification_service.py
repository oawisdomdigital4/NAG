"""
Notification Service
Handles sending notifications to students about assignments, quizzes, and achievements
"""

from django.utils import timezone
from django.db import models
from django.core.mail import send_mail
from datetime import datetime, timedelta
import json

class NotificationService:
    """Centralized notification management"""
    
    # Notification types
    NOTIFICATION_TYPES = {
        'quiz_available': 'New Quiz Available',
        'quiz_due_soon': 'Quiz Due Soon',
        'assignment_available': 'New Assignment',
        'assignment_due_soon': 'Assignment Due Soon',
        'grade_posted': 'Your Grade is Ready',
        'achievement_unlocked': 'Achievement Unlocked',
        'course_completed': 'Course Completed',
        'feedback_received': 'Feedback on Your Work',
        'reminder_incomplete': 'Incomplete Tasks Reminder',
        'course_started': 'Course Started'
    }
    
    @staticmethod
    def send_quiz_available_notification(quiz, enrollments):
        """Notify students that a quiz is available"""
        for enrollment in enrollments:
            notification_data = {
                'type': 'quiz_available',
                'title': f'Quiz Available: {quiz.title}',
                'message': f'A new quiz "{quiz.title}" has been added to your course.',
                'action_url': f'/lessons/{quiz.id}',
                'icon': 'BookOpen'
            }
            NotificationService._create_notification(enrollment.user, notification_data)
    
    @staticmethod
    def send_assignment_available_notification(assignment, enrollments):
        """Notify students that an assignment is available"""
        for enrollment in enrollments:
            notification_data = {
                'type': 'assignment_available',
                'title': f'Assignment Available: {assignment.title}',
                'message': f'A new assignment "{assignment.title}" has been added to your course.',
                'action_url': f'/lessons/{assignment.id}',
                'icon': 'FileText'
            }
            NotificationService._create_notification(enrollment.user, notification_data)
    
    @staticmethod
    def send_due_soon_notification(assessment, enrollment, days_remaining):
        """Notify student that assessment is due soon"""
        assessment_type = 'Quiz' if hasattr(assessment, 'questions') else 'Assignment'
        
        if days_remaining == 0:
            urgency = 'TODAY!'
        elif days_remaining == 1:
            urgency = 'tomorrow'
        else:
            urgency = f'in {days_remaining} days'
        
        notification_data = {
            'type': 'quiz_due_soon' if assessment_type == 'Quiz' else 'assignment_due_soon',
            'title': f'{assessment_type} Due Soon: {assessment.title}',
            'message': f'"{assessment.title}" is due {urgency}. Don\'t miss the deadline!',
            'action_url': f'/lessons/{assessment.id}',
            'icon': 'Clock',
            'priority': 'high'
        }
        NotificationService._create_notification(enrollment.user, notification_data)
    
    @staticmethod
    def send_grade_posted_notification(submission, score, feedback_available=False):
        """Notify student that their grade has been posted"""
        assessment_type = 'Quiz' if hasattr(submission, 'quiz') else 'Assignment'
        
        message = f'Your {assessment_type} has been graded: {score}%'
        if feedback_available:
            message += '. Feedback is available.'
        
        notification_data = {
            'type': 'grade_posted',
            'title': f'Grade Posted: {score}%',
            'message': message,
            'action_url': f'/submissions/{submission.id}',
            'icon': 'CheckCircle',
            'metadata': {'score': score}
        }
        NotificationService._create_notification(submission.enrollment.user, notification_data)
    
    @staticmethod
    def send_achievement_notification(user, achievement_name, achievement_description, badge_url=None):
        """Notify student of unlocked achievement"""
        notification_data = {
            'type': 'achievement_unlocked',
            'title': f'🏆 Achievement Unlocked: {achievement_name}',
            'message': achievement_description,
            'action_url': '/achievements',
            'icon': 'Award',
            'metadata': {'badge_url': badge_url}
        }
        NotificationService._create_notification(user, notification_data)
    
    @staticmethod
    def send_feedback_notification(submission, feedback):
        """Notify student that feedback has been provided"""
        assessment_type = 'Quiz' if hasattr(submission, 'quiz') else 'Assignment'
        
        notification_data = {
            'type': 'feedback_received',
            'title': f'Feedback on Your {assessment_type}',
            'message': f'Your {assessment_type} has received detailed feedback from your instructor.',
            'action_url': f'/submissions/{submission.id}',
            'icon': 'MessageSquare'
        }
        NotificationService._create_notification(submission.enrollment.user, notification_data)
    
    @staticmethod
    def send_incomplete_reminder(enrollment):
        """Send reminder about incomplete course tasks"""
        from courses.models import QuizSubmission, AssignmentSubmission, Lesson
        
        pending_lessons = Lesson.objects.filter(
            module__course=enrollment.course
        ).exclude(
            quiz_submissions__enrollment=enrollment,
            assignment_submissions__enrollment=enrollment
        )
        
        if pending_lessons.exists():
            pending_count = pending_lessons.count()
            
            notification_data = {
                'type': 'reminder_incomplete',
                'title': f'You have {pending_count} pending tasks',
                'message': f'Complete your course: {pending_count} lessons awaiting your work.',
                'action_url': f'/courses/{enrollment.course.id}',
                'icon': 'AlertCircle',
                'priority': 'medium'
            }
            NotificationService._create_notification(enrollment.user, notification_data)
    
    @staticmethod
    def send_course_completion_notification(enrollment):
        """Notify student of course completion"""
        notification_data = {
            'type': 'course_completed',
            'title': f'🎉 Course Completed: {enrollment.course.title}',
            'message': f'Congratulations! You\'ve completed "{enrollment.course.title}".',
            'action_url': f'/courses/{enrollment.course.id}/certificate',
            'icon': 'Trophy'
        }
        NotificationService._create_notification(enrollment.user, notification_data)
    
    @staticmethod
    def send_email_notification(user, subject, message_body, html_template=None):
        """Send email notification to user"""
        try:
            send_mail(
                subject=subject,
                message=message_body,
                from_email='noreply@academyplatform.com',
                recipient_list=[user.email],
                html_message=html_template,
                fail_silently=False
            )
            return True
        except Exception as e:
            print(f"Error sending email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def _create_notification(user, notification_data):
        """Internal helper to create notification record"""
        # This would integrate with your notifications app
        # For now, storing as example
        try:
            from notifications.models import Notification
            
            Notification.objects.create(
                user=user,
                notification_type=notification_data.get('type'),
                title=notification_data.get('title'),
                message=notification_data.get('message'),
                action_url=notification_data.get('action_url'),
                icon=notification_data.get('icon'),
                priority=notification_data.get('priority', 'normal'),
                metadata=notification_data.get('metadata', {}),
                created_at=timezone.now()
            )
        except ImportError:
            # Notifications app not configured
            pass
    
    @staticmethod
    def get_due_soon_assessments(enrollment, hours_threshold=48):
        """Get assessments due within specified hours"""
        from courses.models import Lesson
        
        cutoff_time = timezone.now() + timedelta(hours=hours_threshold)
        
        # Get lessons with due dates
        lessons = Lesson.objects.filter(
            module__course=enrollment.course,
            due_date__gte=timezone.now(),
            due_date__lte=cutoff_time
        )
        
        return lessons
    
    @staticmethod
    def schedule_bulk_notifications(notification_type, user_filter, notification_data):
        """Schedule bulk notifications for multiple users"""
        users = user_filter
        successful = 0
        failed = 0
        
        for user in users:
            try:
                NotificationService._create_notification(user, notification_data)
                successful += 1
            except Exception as e:
                print(f"Failed to notify {user.email}: {str(e)}")
                failed += 1
        
        return {
            'notification_type': notification_type,
            'successful': successful,
            'failed': failed,
            'total': successful + failed
        }


class UserNotificationPreferences:
    """Manage user notification preferences"""
    
    DEFAULT_PREFERENCES = {
        'quiz_available': True,
        'quiz_due_soon': True,
        'assignment_available': True,
        'assignment_due_soon': True,
        'grade_posted': True,
        'achievement_unlocked': True,
        'course_completed': True,
        'feedback_received': True,
        'reminder_incomplete': False,  # Default off
        'course_started': True,
        # Email preferences
        'email_digests': True,
        'digest_frequency': 'daily'  # daily, weekly, never
    }
    
    @staticmethod
    def get_preferences(user):
        """Get user's notification preferences"""
        # Would connect to user preferences model
        return UserNotificationPreferences.DEFAULT_PREFERENCES
    
    @staticmethod
    def should_send_notification(user, notification_type):
        """Check if notification should be sent based on user preferences"""
        preferences = UserNotificationPreferences.get_preferences(user)
        return preferences.get(notification_type, True)
    
    @staticmethod
    def update_preferences(user, preferences):
        """Update user's notification preferences"""
        # Would save to user preferences model
        return True
