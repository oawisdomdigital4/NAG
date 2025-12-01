#!/usr/bin/env python
import os
import sys
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from community.models import Group
from community.serializers import GroupSerializer
from django.test import RequestFactory

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/community/groups/')

# Get the first group
groups = Group.objects.all()[:1]

if groups:
    g = groups[0]
    print(f"Testing group: {g.name} (ID: {g.id})")
    print(f"Group has banner: {bool(g.banner)}")
    print(f"Group has profile_picture: {bool(g.profile_picture)}")
    print(f"Group banner_url: {g.banner_url}")
    print(f"Group profile_picture_url: {g.profile_picture_url}")
    print()
    
    s = GroupSerializer(g, context={'request': request})
    data = s.data
    
    print("Serializer output fields related to images:")
    image_fields = ['banner', 'banner_url', 'banner_absolute_url', 
                    'profile_picture', 'profile_picture_url', 'profile_picture_absolute_url',
                    'logo_url']
    
    for field in image_fields:
        value = data.get(field)
        if value is not None:
            print(f"  {field}: {value}")
    
    print("\nAll returned fields:")
    for key in sorted(data.keys()):
        print(f"  - {key}")
else:
    print("No groups found in database")
