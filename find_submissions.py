import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission

submissions_with_files = []
for sub in AssignmentSubmission.objects.all():
    if sub.attachments and len(sub.attachments) > 0:
        submissions_with_files.append(sub)

print(f"Found {len(submissions_with_files)} submissions with attachments")
print(f"IDs: {[s.id for s in submissions_with_files]}")

if submissions_with_files:
    s = submissions_with_files[0]
    print(f"\nFirst submission (ID {s.id}):")
    print(f"Attachments: {s.attachments}")
