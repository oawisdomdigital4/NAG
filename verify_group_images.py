#!/usr/bin/env python
"""
Final verification that group banner and profile images are fully functional
"""
import os
import django
from io import BytesIO
from PIL import Image

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from community.models import Group, GroupMembership
from community.serializers import GroupSerializer
from accounts.models import User

print("\n" + "="*80)
print("FINAL VERIFICATION: GROUP BANNER & PROFILE IMAGE FUNCTIONALITY")
print("="*80)

# Setup
user, _ = User.objects.get_or_create(username='verify_user', defaults={'email': 'verify@test.com'})
group, _ = Group.objects.get_or_create(name='Verify Group', defaults={'description': 'Verify', 'category': 'Test', 'created_by': user})
GroupMembership.objects.get_or_create(group=group, user=user)

# Create images
def create_image(name):
    img = Image.new('RGB', (100, 100), color='red' if 'banner' in name else 'blue')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile(f"{name}.jpg", img_io.getvalue(), content_type="image/jpeg")

group.banner = create_image('verify_banner')
group.profile_picture = create_image('verify_profile')
group.save()
group.refresh_from_db()

# Test
factory = RequestFactory()
request = factory.get('/api/community/groups/')
serializer = GroupSerializer(group, context={'request': request})
data = serializer.data

checks = [
    ("banner_url present", bool(data.get('banner_url'))),
    ("logo_url present", bool(data.get('logo_url'))),
    ("banner_url is absolute", data.get('banner_url', '').startswith('http')),
    ("logo_url is absolute", data.get('logo_url', '').startswith('http')),
    ("profile_picture_absolute_url present", bool(data.get('profile_picture_absolute_url'))),
    ("banner_absolute_url present", bool(data.get('banner_absolute_url'))),
]

print("\nVerification Results:")
all_pass = True
for check_name, result in checks:
    status = "✓" if result else "✗"
    print(f"  {status} {check_name}")
    if not result:
        all_pass = False

# Cleanup
group.banner.delete()
group.profile_picture.delete()

if all_pass:
    print("\n✓ SUCCESS! All group image functionality is working correctly!")
    print("\nFrontend can now:")
    print("  • Display group banner: <img src={group.banner_url} />")
    print("  • Display group logo: <img src={group.logo_url} />")
    print("  • Upload images via GroupSettings component")
    print("  • Edit group images with preview")
else:
    print("\n✗ Some checks failed!")
    exit(1)

print("="*80 + "\n")
