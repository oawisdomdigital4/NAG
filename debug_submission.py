import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission, Enrollment
from accounts.models import User

# Check submission 6 directly
sub = AssignmentSubmission.objects.get(id=6)
print(f"Submission 6:")
print(f"  Attachments raw: {sub.attachments}")
print(f"  Type: {type(sub.attachments)}")
print(f"  Is list: {isinstance(sub.attachments, list)}")
print(f"  Length: {len(sub.attachments) if sub.attachments else 0}")

# Check if student is found
try:
    student = User.objects.get(email='otiwisdom80@gmail.com')
    print(f"\nStudent found: {student.id} - {student.email}")
    
    # Check enrollment
    enrollment = Enrollment.objects.get(user=student, course=sub.lesson.module.course)
    print(f"Enrollment found: {enrollment.id}")
    
    # Check which submissions match this enrollment
    matching = AssignmentSubmission.objects.filter(
        enrollment=enrollment,
        lesson=sub.lesson
    )
    print(f"Submissions for this enrollment/lesson: {matching.count()}")
    for m in matching:
        print(f"  ID: {m.id}, Attachments: {m.attachments}")
        
except Exception as e:
    print(f"Error: {e}")
