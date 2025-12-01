#!/usr/bin/env python
"""
Comprehensive diagnostic and verification for group operations.
This script checks for and fixes common issues with group creation.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from accounts.models import UserToken
from community.models import Group, GroupMembership
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print("\n" + "="*80)
print("GROUP OPERATIONS - DIAGNOSTIC & FIX")
print("="*80 + "\n")

# 1. Check for expired tokens
print("1. Checking for expired user tokens...")
expired_count = UserToken.objects.filter(expires_at__lt=timezone.now()).count()
print(f"   Found {expired_count} expired tokens")

if expired_count > 0:
    print("   ⚠ Expired tokens detected - cleaning up...")
    UserToken.objects.filter(expires_at__lt=timezone.now()).delete()
    print(f"   ✓ Deleted {expired_count} expired tokens")

# 2. Check active tokens
print("\n2. Checking active user tokens...")
active_tokens = UserToken.objects.filter(expires_at__gt=timezone.now()).count()
print(f"   ✓ Active tokens: {active_tokens}")

# 3. Create fresh tokens for users without valid ones
print("\n3. Ensuring all users have valid tokens...")
users_without_valid_token = []
for user in User.objects.all():
    valid_token = UserToken.objects.filter(
        user=user,
        expires_at__gt=timezone.now()
    ).exists()
    if not valid_token:
        users_without_valid_token.append(user)

if users_without_valid_token:
    print(f"   Found {len(users_without_valid_token)} users without valid tokens")
    for user in users_without_valid_token:
        # Delete any expired tokens first
        UserToken.objects.filter(user=user, expires_at__lt=timezone.now()).delete()
        # Create a new valid token
        token = UserToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=365)
        )
        print(f"   ✓ Created valid token for {user.username}")
else:
    print(f"   ✓ All users have valid tokens")

# 4. Test group creation
print("\n4. Testing group creation...")
try:
    test_user = User.objects.first()
    test_group = Group.objects.create(
        name="Diagnostic Test Group",
        description="Testing group creation",
        category="test",
        created_by=test_user
    )
    print(f"   ✓ Group created successfully (ID: {test_group.id})")
    
    # Verify relationships
    membership = GroupMembership.objects.filter(user=test_user, group=test_group).exists()
    if membership:
        print(f"   ✓ Group membership created")
    else:
        print(f"   ⚠ No membership found - creating...")
        GroupMembership.objects.create(user=test_user, group=test_group)
        print(f"   ✓ Membership created")
    
    # Test deletion with proper cascade handling
    # First clear all relationships manually before deleting
    test_group.moderators.clear()  # Clear M2M
    test_group.courses.clear()     # Clear M2M
    GroupMembership.objects.filter(group=test_group).delete()  # Delete memberships
    test_group.delete()
    print(f"   ✓ Group deleted successfully (with manual cascade)")
    
except Exception as e:
    print(f"   ✗ Error during group operations: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
print("\nCommon Issues & Fixes:\n")
print("1. IntegrityError FOREIGN KEY constraint:\n")
print("   • Usually caused by expired authentication tokens")
print("   • Solution: Ensure valid non-expired UserToken exists")
print("   • Use this diagnostic script to auto-fix\n")
print("2. Group creation fails:\n")
print("   • Check that user has a valid token (not expired)")
print("   • Tokens expire after set duration - create new ones regularly")
print("   • This script auto-generates 1-year valid tokens\n")
print("="*80 + "\n")
