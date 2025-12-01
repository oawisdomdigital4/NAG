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


class QuizQuestionFullSerializer(serializers.ModelSerializer):
    """Full serializer with correct answer for instructor/grading"""
    class Meta:
        model = QuizQuestion
        fields = ['id', 'lesson', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        extra_kwargs = {
            'lesson': {'required': True},
            'question_text': {'required': True},
            'option_a': {'required': True},
            'option_b': {'required': True},
            'option_c': {'required': True},
            'option_d': {'required': True},
            'correct_option': {'required': True},
        }
    
    def validate_lesson(self, value):
        """Validate that lesson exists"""
        if not value:
            raise serializers.ValidationError("Lesson is required")
        if not isinstance(value, Lesson):
            raise serializers.ValidationError(f"Invalid lesson ID: {value}")
        return value
    
    def validate_correct_option(self, value):
        """Validate correct option is a, b, c, or d"""
        if value.lower() not in ['a', 'b', 'c', 'd']:
            raise serializers.ValidationError(f"correct_option must be 'a', 'b', 'c', or 'd', got '{value}'")
        return value.lower()


class LessonSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    video_file_url = serializers.SerializerMethodField()
    video_file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'description', 'lesson_type', 'order',
            'video_url', 'video_file', 'video_file_url', 'video_file_name', 'duration_minutes', 'article_content',
            'quiz_title', 'questions_count', 'passing_score', 'questions',
            'assignment_title', 'due_date', 'estimated_hours', 'instructions', 'rubric', 
            'points_total', 'auto_grade_on_submit', 'late_submission_allowed', 'late_submission_days',
            'attachments_required', 'file_types_allowed', 'min_word_count', 'max_word_count',
            'availability_date'
        ]
        extra_kwargs = {
            'video_file': {'required': False},
            'assignment_title': {'required': False},
            'instructions': {'required': False},
            'rubric': {'required': False},
            'points_total': {'required': False},
            'auto_grade_on_submit': {'required': False},
            'late_submission_allowed': {'required': False},
            'late_submission_days': {'required': False},
            'attachments_required': {'required': False},
            'file_types_allowed': {'required': False},
            'min_word_count': {'required': False},
            'max_word_count': {'required': False},
        }
    
    def get_video_file_url(self, obj):
        """Return the absolute URL of the uploaded video file"""
        if obj.video_file:
            return obj.video_file.url
        return None
    
    def get_video_file_name(self, obj):
        """Return the name of the uploaded video file"""
        if obj.video_file:
            return obj.video_file.name
        return None
    
    def update(self, instance, validated_data):
        """Handle video file deletion when video_file is empty"""
        # Check if video_file is being explicitly cleared
        if 'video_file' in self.initial_data:
            video_file_value = self.initial_data.get('video_file')
            # If the field is empty or "null", delete the existing file
            if video_file_value == '' or video_file_value == 'null' or video_file_value is None:
                if instance.video_file:
                    try:
                        instance.video_file.delete(save=False)
                    except Exception as e:
                        print(f"Warning: Failed to delete video file in serializer: {str(e)}")
                # Set video_file to None in validated_data to update the DB
                validated_data['video_file'] = None
        
        # Clear video_url if it's empty
        if 'video_url' in self.initial_data:
            video_url_value = self.initial_data.get('video_url')
            if video_url_value == '' or video_url_value == 'null':
                validated_data['video_url'] = ''
        
        return super().update(instance, validated_data)
        return super().update(instance, validated_data)


class LessonInstructorSerializer(serializers.ModelSerializer):
    """Serializer for instructors - includes correct_option in questions"""
    questions = QuizQuestionFullSerializer(many=True, read_only=True)
    video_file_url = serializers.SerializerMethodField()
    video_file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'description', 'lesson_type', 'order',
            'video_url', 'video_file', 'video_file_url', 'video_file_name', 'duration_minutes', 'article_content',
            'quiz_title', 'questions_count', 'passing_score', 'questions',
            'assignment_title', 'due_date', 'estimated_hours', 'instructions', 'rubric', 
            'points_total', 'auto_grade_on_submit', 'late_submission_allowed', 'late_submission_days',
            'attachments_required', 'file_types_allowed', 'min_word_count', 'max_word_count',
            'availability_date'
        ]
        extra_kwargs = {
            'video_file': {'required': False},
            'assignment_title': {'required': False},
            'instructions': {'required': False},
            'rubric': {'required': False},
            'points_total': {'required': False},
            'auto_grade_on_submit': {'required': False},
            'late_submission_allowed': {'required': False},
            'late_submission_days': {'required': False},
            'attachments_required': {'required': False},
            'file_types_allowed': {'required': False},
            'min_word_count': {'required': False},
            'max_word_count': {'required': False},
        }
    
    def get_video_file_url(self, obj):
        """Return the absolute URL of the uploaded video file"""
        if obj.video_file:
            return obj.video_file.url
        return None
    
    def get_video_file_name(self, obj):
        """Return the name of the uploaded video file"""
        if obj.video_file:
            return obj.video_file.name
        return None
    
    def update(self, instance, validated_data):
        """Handle video file deletion when video_file is empty"""
        # Check if video_file is being explicitly cleared
        if 'video_file' in self.initial_data:
            video_file_value = self.initial_data.get('video_file')
            # If the field is empty or "null", delete the existing file
            if video_file_value == '' or video_file_value == 'null' or video_file_value is None:
                if instance.video_file:
                    try:
                        instance.video_file.delete(save=False)
                    except Exception as e:
                        print(f"Warning: Failed to delete video file in serializer: {str(e)}")
                # Set video_file to None in validated_data to update the DB
                validated_data['video_file'] = None
        
        # Clear video_url if it's empty
        if 'video_url' in self.initial_data:
            video_url_value = self.initial_data.get('video_url')
            if video_url_value == '' or video_url_value == 'null':
                validated_data['video_url'] = ''
        
        return super().update(instance, validated_data)


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

class CourseModuleInstructorSerializer(serializers.ModelSerializer):
    """Serializer for instructors - includes correct_option in questions"""
    content = serializers.CharField(required=False, allow_blank=True)
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = '__all__'
        extra_kwargs = {
            'course': {'required': False},
        }

    def get_lessons(self, obj):
        """Return all lessons with correct_option for instructors"""
        lessons = obj.lessons.all().order_by('order')
        return LessonInstructorSerializer(lessons, many=True).data

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
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = CourseReview
        fields = ['id', 'course', 'user', 'user_id', 'user_name', 'user_email', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_id', 'user_name', 'user_email', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate(self, attrs):
        """Ensure user is enrolled in the course"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            course = attrs.get('course')
            if course and not Enrollment.objects.filter(user=request.user, course=course).exists():
                raise serializers.ValidationError("You must be enrolled in this course to write a review")
        return attrs

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
            'id', 'user', 'course', 'progress', 'completed_lessons', 'enrolled_at',
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
        read_only_fields = ('facilitator',)
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
            'short_description': {'required': False, 'allow_blank': True},
            'full_description': {'required': False, 'allow_blank': True},
            'thumbnail': {'required': False},
            'thumbnail_url': {'required': False},
            'preview_video': {'required': False},
            'preview_video_url': {'required': False},
        }
    
    def validate_slug(self, value):
        """Allow slug to remain unchanged on updates"""
        # If we're updating (instance exists) and slug is the same, allow it
        if self.instance and self.instance.slug == value:
            return value
        # Otherwise, check uniqueness normally
        if Course.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A course with this slug already exists.")
        return value
    
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


class CourseInstructorSerializer(serializers.ModelSerializer):
    """Serializer for instructors - includes correct_option in quiz questions"""
    modules = CourseModuleInstructorSerializer(many=True, read_only=True)
    reviews = CourseReviewSerializer(many=True, read_only=True)
    thumbnail_url_display = serializers.SerializerMethodField()
    preview_video_url_display = serializers.SerializerMethodField()
    enrollments_count = serializers.SerializerMethodField()
    facilitator = FacilitatorSerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('facilitator',)
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True},
            'short_description': {'required': False, 'allow_blank': True},
            'full_description': {'required': False, 'allow_blank': True},
            'thumbnail': {'required': False},
            'thumbnail_url': {'required': False},
            'preview_video': {'required': False},
            'preview_video_url': {'required': False},
        }
    
    def validate_slug(self, value):
        """Allow slug to remain unchanged on updates"""
        if self.instance and self.instance.slug == value:
            return value
        if Course.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A course with this slug already exists.")
        return value
    
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
