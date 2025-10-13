from rest_framework import serializers
from .models import Course, CourseModule, CourseReview

class CourseModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = '__all__'

class CourseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReview
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    modules = CourseModuleSerializer(many=True, read_only=True)
    reviews = CourseReviewSerializer(many=True, read_only=True)
    class Meta:
        model = Course
        # Expose all fields but treat facilitator as read-only (set on server)
        fields = '__all__'
        read_only_fields = ('facilitator',)
