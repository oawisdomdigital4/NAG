#!/usr/bin/env python
"""
Simple test to check group deletion
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from community.models import Group, GroupMembership
from django.contrib.auth import get_user_model

User = get_user_model()

print("\nTesting group deletion with manual cascade...")

try:
    user = User.objects.first()
    
    # Create group
    test_group = Group.objects.create(
        name="Delete Test Group",
        description="Testing deletion",
        category="test",
        created_by=user
    )
    print(f"Created group ID {test_group.id}")
    
    # Clear relationships
    test_group.moderators.clear()
    test_group.courses.clear()
    GroupMembership.objects.filter(group=test_group).delete()
    print("Cleared all relationships")
    
    # Delete
    test_group.delete()
    print("SUCCESS: Group deleted!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
