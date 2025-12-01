import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from courses.models import Lesson, AssignmentSubmission
from courses.views import LessonViewSet

User = get_user_model()

# Get lesson and submissions
lesson = Lesson.objects.get(id=35)
facilitator = lesson.module.course.facilitator

# Test Submission 6 detail
submission_id = 6

factory = RequestFactory()
request = factory.get(f'/api/courses/lessons/35/assignment-submissions/{submission_id}/')
request.user = facilitator

view = LessonViewSet.as_view({'get': 'assignment_submission_detail'})
response = view(request, pk=35, submission_id=submission_id)

print(f"Testing Submission {submission_id} Detail Endpoint")
print(f"Status: {response.status_code}")

if hasattr(response, 'data'):
    data = response.data
    if 'submission' in data:
        sub = data['submission']
        print(f"Student: {sub['student_name']}")
        print(f"Content length: {len(sub['content'])} chars")
        print(f"Attachments: {len(sub['attachments'])} files")
        for att in sub['attachments']:
            print(f"  - Name: {att['name']}")
            print(f"    URL: {att['url']}")
            print(f"    Size: {att['size']} bytes")
