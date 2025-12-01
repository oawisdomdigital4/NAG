#!/usr/bin/env python
"""
Test group banner and profile image functionality end-to-end
"""
import os
import sys
import django
from io import BytesIO
from PIL import Image

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from community.models import Group, GroupMembership
from community.serializers import GroupSerializer
from accounts.models import User

print("=" * 80)
print("GROUP BANNER AND PROFILE IMAGE TEST")
print("=" * 80)

# Create a test user
user, created = User.objects.get_or_create(username='image_test_user', defaults={'email': 'imagetest@test.com'})
print(f"\n1. Test user: {user.username} (ID: {user.id})")

# Create or get a test group
group, created = Group.objects.get_or_create(
    name='Image Test Group',
    defaults={
        'description': 'Test group for image functionality',
        'category': 'Testing',
        'created_by': user,
    }
)
print(f"2. Test group: {group.name} (ID: {group.id})")

# Create a test membership
membership, created = GroupMembership.objects.get_or_create(
    group=group,
    user=user,
)
print(f"3. User membership created: {membership.id}")

# Create test images
def create_test_image(name, size=(200, 200)):
    """Create a simple test image"""
    img = Image.new('RGB', size, color='red' if 'banner' in name else 'blue')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile(
        name=f"{name}.jpg",
        content=img_io.getvalue(),
        content_type="image/jpeg"
    )

banner_image = create_test_image('test_banner', (800, 200))
profile_image = create_test_image('test_profile', (200, 200))

print(f"\n4. Created test images:")
print(f"   - Banner: {banner_image.name} ({banner_image.size} bytes)")
print(f"   - Profile: {profile_image.name} ({profile_image.size} bytes)")

# Update group with images
group.banner = banner_image
group.profile_picture = profile_image
group.save()
print(f"\n5. Updated group with images")
print(f"   - group.banner: {group.banner}")
print(f"   - group.profile_picture: {group.profile_picture}")

# Refresh from database to ensure changes are persisted
group.refresh_from_db()
print(f"\n6. Refreshed group from database:")
print(f"   - group.banner: {group.banner}")
print(f"   - group.profile_picture: {group.profile_picture}")

# Test serializer output
print(f"\n7. Testing serializer output:")
factory = RequestFactory()
request = factory.get('/api/community/groups/')
serializer = GroupSerializer(group, context={'request': request})
data = serializer.data

print(f"   - banner_url: {data.get('banner_url')}")
print(f"   - banner_absolute_url: {data.get('banner_absolute_url')}")
print(f"   - logo_url: {data.get('logo_url')}")
print(f"   - profile_picture_absolute_url: {data.get('profile_picture_absolute_url')}")

# Verify the URLs are returned
banner_url = data.get('banner_url')
logo_url = data.get('logo_url')

print(f"\n8. Verification:")
if banner_url:
    print(f"   ✓ Banner URL is present: {banner_url}")
else:
    print(f"   ✗ Banner URL is missing!")

if logo_url:
    print(f"   ✓ Logo URL is present: {logo_url}")
else:
    print(f"   ✗ Logo URL is missing!")

if banner_url and logo_url:
    print(f"\n✓ SUCCESS: Group images are fully functional!")
    print(f"\nFrontend can now use:")
    print(f"  - group.banner_url for the banner image")
    print(f"  - group.logo_url for the profile picture")
else:
    print(f"\n✗ FAILED: Some image URLs are missing!")

# Cleanup
print(f"\n9. Cleaning up...")
group.banner.delete()
group.profile_picture.delete()
print(f"   - Images deleted")

print("\n" + "=" * 80)
