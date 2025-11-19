from rest_framework import serializers
from .models import (
    Course, CourseModule, CourseReview, Enrollment,
    Lesson, QuizQuestion, QuizSubmission, AssignmentSubmission
)
from accounts.models import UserProfile
from django.conf import settings
import json


class FacilitatorSerializer(serializers.Serializer):
    """Serializer for facilitator (User) with photo_url from profile"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField()
    
    # Add fields from UserProfile
    name = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    years_experience = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        """Get facilitator name from first_name and last_name"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    
    def get_title(self, obj):
        """Get title from profile"""
        if hasattr(obj, 'profile') and obj.profile:
            # Extract title from company_name or industry field
            return getattr(obj.profile, 'industry', '') or getattr(obj.profile, 'company_name', '') or 'Instructor'
        return 'Instructor'
    
    def get_bio(self, obj):
        """Get bio from profile"""
        if hasattr(obj, 'profile') and obj.profile:
            return getattr(obj.profile, 'bio', '')
        return ''
    
    def get_photo_url(self, obj):
        """Get photo URL from user profile avatar_url or avatar"""
        if hasattr(obj, 'profile') and obj.profile:
            profile = obj.profile
            # Prefer avatar_url if it's set
            if profile.avatar_url:
                return profile.avatar_url
            # Otherwise, check if avatar image field exists and get its URL
            if profile.avatar:
                try:
                    url = profile.avatar.url
                    # avatar.url returns a relative path like /media/avatars/...
                    # Build absolute URL if not already absolute
                    if not url.startswith('http'):
                        # Get the site domain from request context if available
                        request = self.context.get('request') if isinstance(self.context, dict) else None
                        if request:
                            return request.build_absolute_uri(url)
                        # Otherwise, build from settings
                        domain = getattr(settings, 'SITE_DOMAIN', 'http://localhost:8000')
                        return f"{domain}{url}"
                    return url
                except Exception:
                    pass
        return ''
    
    def get_years_experience(self, obj):
        """Get years of experience (placeholder from expertise areas count)"""
        if hasattr(obj, 'profile') and obj.profile:
            profile = obj.profile
            expertise = getattr(profile, 'expertise_areas', []) or []
            return len(expertise) if expertise else 0
        return 0
    
    def get_social_links(self, obj):
        """Get social links (placeholder for now)"""
        return {
            'linkedin': '',
            'twitter': ''
        }


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d']
        # Don't expose correct_option to students


class LessonSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'description', 'lesson_type', 'order',
            'video_url', 'duration_minutes', 'article_content',
            'quiz_title', 'questions_count', 'passing_score', 'questions',
            'assignment_title', 'due_date', 'estimated_hours'
        ]


class CourseModuleSerializer(serializers.ModelSerializer):
    # Make content optional for partial updates - lessons are managed separately
    content = serializers.CharField(required=False, allow_blank=True)
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = '__all__'
        # Make course field optional on updates - it's set on creation and shouldn't change
        extra_kwargs = {
            'course': {'required': False},
        }

    def get_lessons(self, obj):
        """Return all lessons for this module"""
        lessons = obj.lessons.all().order_by('order')
        return LessonSerializer(lessons, many=True).data

    def create(self, validated_data):
        # Ensure content is a valid JSON string
        content = validated_data.get('content', '{}')
        if isinstance(content, dict):
            validated_data['content'] = json.dumps(content)
        elif not content:
            validated_data['content'] = '{}'
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Ensure content is a valid JSON string if provided
        if 'content' in validated_data:
            content = validated_data['content']
            if isinstance(content, dict):
                validated_data['content'] = json.dumps(content)
            elif not content:
                validated_data['content'] = '{}'
        else:
            # If content is not provided on update, keep the existing value
            validated_data['content'] = instance.content
        return super().update(instance, validated_data)

class CourseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReview
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    course_thumbnail = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    facilitator_name = serializers.CharField(source='course.facilitator.get_full_name', read_only=True)
    facilitator_id = serializers.IntegerField(source='course.facilitator.id', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'course', 'progress', 'enrolled_at',
            'course_title', 'course_slug', 'course_thumbnail',
            'user_name', 'user_email',
            'facilitator_name', 'facilitator_id'
        ]
        read_only_fields = ['id', 'enrolled_at']
    
    def get_course_thumbnail(self, obj):
        """Return absolute course thumbnail URL"""
        if obj.course.thumbnail:
            return obj.course.thumbnail.url
        return obj.course.thumbnail_url or ''

class CourseSerializer(serializers.ModelSerializer):
    modules = CourseModuleSerializer(many=True, read_only=True)
    reviews = CourseReviewSerializer(many=True, read_only=True)
    # Return thumbnail as URL (prefer uploaded file over URL field)
    thumbnail_url_display = serializers.SerializerMethodField()
    preview_video_url_display = serializers.SerializerMethodField()
    enrollments_count = serializers.SerializerMethodField()
    # Use custom FacilitatorSerializer for facilitator field
    facilitator = FacilitatorSerializer(read_only=True)
    
    class Meta:
        model = Course
        # Expose all fields but treat facilitator as read-only (set on server)
        fields = '__all__'
        read_only_fields = ('facilitator', 'thumbnail', 'preview_video')
    
    def get_enrollments_count(self, obj):
        """Return the count of enrollments for this course"""
        return obj.enrollments.count()
    
    def get_thumbnail_url_display(self, obj):
        """Return the thumbnail URL, preferring the uploaded file over the URL field"""
        if obj.thumbnail:
            return obj.thumbnail.url
        return obj.thumbnail_url or ''
    
    def get_preview_video_url_display(self, obj):
        """Return the preview video URL, preferring the uploaded file over the URL field"""
        if obj.preview_video:
            return obj.preview_video.url
        return obj.preview_video_url or ''


class QuizQuestionFullSerializer(serializers.ModelSerializer):
    """Full serializer with correct answer for instructor/grading"""
    class Meta:
        model = QuizQuestion
        fields = '__all__'


class QuizSubmissionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user_name = serializers.CharField(source='enrollment.user.get_full_name', read_only=True)
    
    class Meta:
        model = QuizSubmission
        fields = ['id', 'enrollment', 'lesson', 'lesson_title', 'submitted_at', 'score', 'answers', 'graded', 'user_name']
        read_only_fields = ['id', 'submitted_at', 'score', 'graded']


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user_name = serializers.CharField(source='enrollment.user.get_full_name', read_only=True)
    
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'enrollment', 'lesson', 'lesson_title', 'submitted_at', 'content', 'score', 'graded', 'auto_graded', 'user_name']
        read_only_fields = ['id', 'submitted_at', 'graded']
