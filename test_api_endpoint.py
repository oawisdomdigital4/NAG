"""
Simulate the actual API call to verify file attachment display
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission, Lesson
from courses.views import LessonViewSet
from accounts.models import User  # Use custom User model
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

print("=" * 80)
print("API ENDPOINT SIMULATION TEST")
print("=" * 80)

# Get the lesson
lesson = Lesson.objects.get(id=35)  # The test assignment lesson
print(f"\nLesson: {lesson.title} (ID: {lesson.id})")

# Get the student and submission
student = User.objects.get(email='otiwisdom80@gmail.com')
submission = AssignmentSubmission.objects.get(id=6)

print(f"Student: {student.email}")
print(f"Submission ID: {submission.id}")

# Simulate API request
factory = APIRequestFactory()
request = factory.get(f'/api/courses/lessons/{lesson.id}/assignment-status/')
request.user = student

# Create viewset instance and call the method
viewset = LessonViewSet()
viewset.action = 'assignment_status'
viewset.basename = 'lesson'
viewset.request = request
viewset.kwargs = {'pk': lesson.id}
viewset.format_kwarg = None

# Mock get_object
def mock_get_object():
    return lesson
viewset.get_object = mock_get_object

# Call the endpoint
response = viewset.assignment_status(request, pk=lesson.id)

print("\n" + "-" * 80)
print("API RESPONSE")
print("-" * 80)

response_data = json.loads(json.dumps(response.data, default=str))
print(json.dumps(response_data, indent=2))

print("\n" + "-" * 80)
print("VERIFICATION")
print("-" * 80)

if response_data.get('_ok'):
    print("✅ Response is valid")
    status = response_data.get('status', {})
    attachments = status.get('attachments', [])
    
    if attachments:
        print(f"✅ Found {len(attachments)} attachment(s)")
        for att in attachments:
            url = att.get('url', '')
            has_encoding = '%20' in url or '%' not in url
            print(f"\n  File: {att['name']}")
            print(f"  URL: {url}")
            print(f"  Size: {att['size']} bytes")
            print(f"  Has URL encoding: {'✅ YES' if '%20' in url else '✓ No special chars'}")
            print(f"  Ready for HTTP: {'✅ YES' if has_encoding else '❌ NO'}")
    else:
        print("❌ No attachments returned")
else:
    print("❌ Invalid response")

print("\n" + "=" * 80)
print("✅ API ENDPOINT TEST COMPLETE")
print("=" * 80)
