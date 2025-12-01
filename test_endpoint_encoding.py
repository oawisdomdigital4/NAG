import os
import django
from urllib.parse import quote

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission, Enrollment, Lesson
from rest_framework.test import APIRequestFactory
from courses.views import LessonViewSet
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the submission with attachments
submission = AssignmentSubmission.objects.get(id=6)
print(f"Testing with Submission ID: {submission.id}")
print(f"Enrollment: {submission.enrollment.id}")
print(f"Lesson: {submission.lesson.id}")
print(f"Raw attachments: {submission.attachments}")
print()

# Create a test request
factory = APIRequestFactory()
view = LessonViewSet()

# Test the _encode_attachment_urls method
print("=== Testing _encode_attachment_urls method ===")
if submission.attachments:
    encoded = view._encode_attachment_urls(submission.attachments)
    print(f"Encoded attachments:")
    for att in encoded:
        print(f"  Name: {att['name']}")
        print(f"  URL:  {att['url']}")
        print(f"  Size: {att['size']}")
        print()
else:
    print("No attachments found")
