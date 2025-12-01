#!/usr/bin/env python
"""
Verify that Group and GroupMembership are properly registered in Django admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib import admin
from community.models import Group, GroupMembership, GroupInvite

print("\n" + "="*80)
print("DJANGO ADMIN REGISTRATION VERIFICATION")
print("="*80)

# Check if models are registered
registry = admin.site._registry

models_to_check = [
    (Group, 'Group'),
    (GroupMembership, 'GroupMembership'),
    (GroupInvite, 'GroupInvite'),
]

print("\nRegistered Models:")
all_registered = True
for model, name in models_to_check:
    is_registered = model in registry
    status = "✓" if is_registered else "✗"
    print(f"  {status} {name}: {is_registered}")
    if not is_registered:
        all_registered = False

if all_registered:
    print("\n✓ SUCCESS! All group-related models are registered in Django admin!")
    print("\nAvailable Admin Features:")
    print("  • Group Admin:")
    print("    - View, create, edit, delete groups")
    print("    - Filter by category, corporate status, privacy")
    print("    - Search by name, description, creator")
    print("    - Manage banner and profile picture images")
    print("    - Manage moderators and linked courses")
    print("    - View members count and posts count")
    print("\n  • GroupMembership Admin:")
    print("    - View and manage group memberships")
    print("    - Filter by group and join date")
    print("    - Search by user and group name")
    print("\n  • GroupInvite Admin:")
    print("    - View and manage group invitations")
    print("    - Filter by status")
    print("    - Track invite tokens and expiration")
else:
    print("\n✗ FAILED! Some models are not registered!")
    exit(1)

print("\n" + "="*80 + "\n")
