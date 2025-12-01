import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission

submissions = AssignmentSubmission.objects.all()
for s in submissions:
    print(f"Submission {s.id}:")
    print(f"  Attachments field: {s.attachments}")
    print(f"  Type: {type(s.attachments)}")
    print(f"  Is empty: {not s.attachments}")
    print()
