import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from courses.models import Lesson, Course, CourseModule
from courses.views import LessonViewSet

User = get_user_model()

# Find the facilitator for lesson 35
lesson = Lesson.objects.get(id=35)
print(f"Lesson: {lesson.title}")
print(f"Course: {lesson.module.course.title}")
print(f"Facilitator: {lesson.module.course.facilitator.username}")
print()

# Test the assignment_submissions endpoint as the facilitator
factory = RequestFactory()
facilitator = lesson.module.course.facilitator

# Create a mock request
request = factory.get(f'/api/courses/lessons/35/assignment-submissions/')
request.user = facilitator

# Call the viewset
view = LessonViewSet.as_view({'get': 'assignment_submissions'})
response = view(request, pk=35)

print(f"Status: {response.status_code}")

if hasattr(response, 'data'):
    data = response.data
    print(f"Response keys: {data.keys()}")
    if 'submissions' in data:
        print(f"Number of submissions: {len(data['submissions'])}")
        for sub in data['submissions']:
            print(f"\nSubmission {sub['id']}:")
            print(f"  Student: {sub['student_name']}")
            print(f"  Attachments: {len(sub['attachments'])} files")
            for att in sub['attachments']:
                print(f"    - {att['name']}: {att['url']}")
