import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission

submission = AssignmentSubmission.objects.get(id=6)
print(f"Submission 6 attachments: {submission.attachments}")

if submission.attachments:
    for att in submission.attachments:
        full_path = att['url']
        print(f"\nAttachment: {att['name']}")
        print(f"URL: {full_path}")
        print(f"MEDIA_URL: {settings.MEDIA_URL}")
        print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        # Check if file exists
        # Remove MEDIA_URL prefix if it exists
        if full_path.startswith(settings.MEDIA_URL):
            file_path = full_path[len(settings.MEDIA_URL):]
        else:
            file_path = full_path
        
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
        print(f"Full file path: {full_file_path}")
        print(f"File exists: {os.path.exists(full_file_path)}")
