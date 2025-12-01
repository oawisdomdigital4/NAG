import os
import django
from urllib.parse import quote

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission

submission = AssignmentSubmission.objects.get(id=6)
print(f"Original attachments: {submission.attachments}")
print()

# Test URL encoding
if submission.attachments:
    for att in submission.attachments:
        url = att.get('url', '')
        print(f"Original URL: {url}")
        
        if url.startswith('/media/'):
            # Encode everything after /media/
            encoded_path = quote(url[7:], safe='/')
            encoded_url = f'/media/{encoded_path}'
            print(f"Encoded URL:  {encoded_url}")
