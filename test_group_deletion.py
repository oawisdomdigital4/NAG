#!/usr/bin/env python
"""
Test that group deletion works without django_mailjet import errors.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from community.models import Group, GroupMembership
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*80)
print("GROUP DELETION TEST - Verify no django_mailjet errors")
print("="*80 + "\n")

try:
    # Create a test group
    user = User.objects.first()
    if not user:
        print("✗ No users found in database")
        sys.exit(1)
    
    test_group = Group.objects.create(
        name="Test Group for Deletion",
        description="Testing group deletion without django_mailjet errors",
        created_by=user
    )
    print(f"✓ Created test group: {test_group.name} (ID: {test_group.id})")
    
    # Add a member
    membership = GroupMembership.objects.create(
        user=user,
        group=test_group
    )
    print(f"✓ Added membership: {user.username} -> {test_group.name}")
    
    # Delete the membership first (cascade)
    membership.delete()
    print(f"✓ Deleted membership before group deletion")
    
    # Delete the group
    group_id = test_group.id
    test_group.delete()
    print(f"✓ Successfully deleted group ID {group_id}")
    
    # Verify it's deleted
    exists = Group.objects.filter(id=group_id).exists()
    if not exists:
        print(f"✓ Verification: Group ID {group_id} no longer exists in database")
    
    print("\n" + "="*80)
    print("✓ SUCCESS! Group deletion works without django_mailjet errors!")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
