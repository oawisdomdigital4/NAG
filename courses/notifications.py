"""
Email notification system for course events
"""
from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import User


class NotificationTemplate(models.Model):
    """Email notification templates"""
    TEMPLATE_TYPES = [
        ('enrollment_confirmation', 'Enrollment Confirmation'),
        ('lesson_available', 'New Lesson Available'),
        ('quiz_graded', 'Quiz Graded'),
        ('assignment_graded', 'Assignment Graded'),
        ('course_complete', 'Course Completed'),
        ('low_performance', 'Low Performance Alert'),
    ]
    
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=255)
    body_text = models.TextField()
    body_html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type']
    
    def __str__(self):
        return f"{self.get_template_type_display()}"


class NotificationLog(models.Model):
    """Log of all sent notifications"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_logs')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.recipient.email} ({self.status})"


class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enrollment = models.BooleanField(default=True)
    email_lesson = models.BooleanField(default=True)
    email_quiz_graded = models.BooleanField(default=True)
    email_assignment_graded = models.BooleanField(default=True)
    email_course_complete = models.BooleanField(default=True)
    email_low_performance = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class NotificationService:
    """Service for sending notifications"""
    
    @staticmethod
    def send_enrollment_confirmation(user: User, course):
        """Send enrollment confirmation email"""
        try:
            template = NotificationTemplate.objects.get(template_type='enrollment_confirmation')
            context = {
                'user_name': user.get_full_name() or user.username,
                'course_title': course.title,
                'course_url': f"{settings.FRONTEND_URL}/courses/{course.slug}"
            }
            
            subject = template.subject.format(**context)
            body = template.body_text.format(**context)
            
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=template.body_html.format(**context) if template.body_html else None
            )
            
            NotificationLog.objects.create(
                recipient=user,
                template=template,
                subject=subject,
                body=body,
                status='sent'
            )
        except NotificationTemplate.DoesNotExist:
            pass
    
    @staticmethod
    def send_quiz_graded(user: User, lesson, score: int, passed: bool):
        """Send quiz graded notification"""
        try:
            template = NotificationTemplate.objects.get(template_type='quiz_graded')
            context = {
                'user_name': user.get_full_name() or user.username,
                'lesson_title': lesson.title,
                'score': score,
                'passed': 'PASSED' if passed else 'NEEDS IMPROVEMENT',
                'status_color': '#22c55e' if passed else '#ef4444'
            }
            
            subject = template.subject.format(**context)
            body = template.body_text.format(**context)
            
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=template.body_html.format(**context) if template.body_html else None
            )
            
            NotificationLog.objects.create(
                recipient=user,
                template=template,
                subject=subject,
                body=body,
                status='sent'
            )
        except NotificationTemplate.DoesNotExist:
            pass
    
    @staticmethod
    def send_assignment_graded(user: User, lesson, score: int, instructor_feedback: str = ''):
        """Send assignment graded notification"""
        try:
            template = NotificationTemplate.objects.get(template_type='assignment_graded')
            context = {
                'user_name': user.get_full_name() or user.username,
                'lesson_title': lesson.title,
                'score': score,
                'feedback': instructor_feedback or 'Great work!'
            }
            
            subject = template.subject.format(**context)
            body = template.body_text.format(**context)
            
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=template.body_html.format(**context) if template.body_html else None
            )
            
            NotificationLog.objects.create(
                recipient=user,
                template=template,
                subject=subject,
                body=body,
                status='sent'
            )
        except NotificationTemplate.DoesNotExist:
            pass
    
    @staticmethod
    def send_course_completion(user: User, course, final_score: float):
        """Send course completion congratulations"""
        try:
            template = NotificationTemplate.objects.get(template_type='course_complete')
            context = {
                'user_name': user.get_full_name() or user.username,
                'course_title': course.title,
                'final_score': round(final_score, 2),
                'certificate_url': f"{settings.FRONTEND_URL}/certificates/{user.id}/{course.id}"
            }
            
            subject = template.subject.format(**context)
            body = template.body_text.format(**context)
            
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=template.body_html.format(**context) if template.body_html else None
            )
            
            NotificationLog.objects.create(
                recipient=user,
                template=template,
                subject=subject,
                body=body,
                status='sent'
            )
        except NotificationTemplate.DoesNotExist:
            pass
    
    @staticmethod
    def send_performance_alert(user: User, course, alert_type: str):
        """Send low performance alert"""
        try:
            template = NotificationTemplate.objects.get(template_type='low_performance')
            context = {
                'user_name': user.get_full_name() or user.username,
                'course_title': course.title,
                'alert_type': alert_type,
                'help_url': f"{settings.FRONTEND_URL}/help/study-tips"
            }
            
            subject = template.subject.format(**context)
            body = template.body_text.format(**context)
            
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=template.body_html.format(**context) if template.body_html else None
            )
            
            NotificationLog.objects.create(
                recipient=user,
                template=template,
                subject=subject,
                body=body,
                status='sent'
            )
        except NotificationTemplate.DoesNotExist:
            pass
