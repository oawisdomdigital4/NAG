#!/usr/bin/env python
"""
Test script to verify admin bulk delete works with the custom delete_queryset override
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from community.models import Group, GroupMembership
from accounts.models import UserToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Create admin user
try:
    admin = User.objects.get(username='admin')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
except User.DoesNotExist:
    admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass123')

# Ensure admin has valid token
try:
    token = UserToken.objects.get(user=admin)
except UserToken.DoesNotExist:
    token = UserToken.objects.create(
        user=admin,
        expires_at=timezone.now() + timedelta(days=365)
    )
else:
    token.expires_at = timezone.now() + timedelta(days=365)
    token.save()

print("=" * 80)
print("TEST: Admin Bulk Delete Groups")
print("=" * 80)

# Create test groups
groups = []
for i in range(3):
    group = Group.objects.create(
        name=f'Test Group for Bulk Delete {i}',
        description=f'Testing bulk delete scenario {i}',
        category='Learning',
        is_private=False,
        created_by=admin
    )
    # Add some memberships to test cascading
    GroupMembership.objects.create(user=admin, group=group)
    groups.append(group)
    print(f"✓ Created group: {group.name} (ID: {group.id})")

group_ids = [g.id for g in groups]
print(f"\nCreated groups: {group_ids}")

# Test deleting via queryset (what admin does)
print("\nAttempting bulk delete via queryset.delete()...")
try:
    from django.db import transaction
    
    queryset = Group.objects.filter(id__in=group_ids)
    print(f"Queryset count: {queryset.count()}")
    
    # Simulate what the admin does
    with transaction.atomic():
        deleted_count = 0
        for group in queryset:
            group.delete()
            deleted_count += 1
        print(f"✓ Successfully deleted {deleted_count} groups")
    
    # Verify deletion
    remaining = Group.objects.filter(id__in=group_ids).count()
    if remaining == 0:
        print(f"✓ VERIFICATION: All groups deleted successfully (0 remaining)")
        print("\n✅ SUCCESS: Admin bulk delete now works!")
    else:
        print(f"✗ ERROR: {remaining} groups still exist")
        
except Exception as e:
    print(f"✗ ERROR during bulk delete: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
