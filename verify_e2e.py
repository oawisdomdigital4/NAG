import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import Course

print("=" * 80)
print("VERIFYING END-TO-END UPLOAD")
print("=" * 80)

course = Course.objects.get(slug='e2e-test-325c7f11')
print(f"\nCourse ID: {course.id}")
print(f"Title: {course.title}")
print(f"Thumbnail field value: {course.thumbnail}")
print(f"Thumbnail URL: {course.thumbnail.url if course.thumbnail else 'NONE'}")

if course.thumbnail:
    full_path = course.thumbnail.path
    print(f"Thumbnail path: {full_path}")
    
    if os.path.exists(full_path):
        file_size = os.path.getsize(full_path)
        print(f"\n✓ OK: File exists on disk!")
        print(f"  Path: {full_path}")
        print(f"  Size: {file_size} bytes")
        print(f"\n✓ OK: THUMBNAIL UPLOAD COMPLETE AND VERIFIED!")
    else:
        print(f"\n✗ ERROR: File not found on disk!")
        print(f"  Expected: {full_path}")
else:
    print("\n✗ ERROR: No thumbnail file in database!")

print("\n" + "=" * 80)
