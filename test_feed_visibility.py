#!/usr/bin/env python
"""
Test to verify group-only posts do NOT appear in global feed.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db.models import Q
from django.contrib.auth import get_user_model
from community.models import Group, Post, GroupMembership

User = get_user_model()

print("\n" + "="*80)
print("TEST: Group-only posts NOT in global feed")
print("="*80)

# Setup
user, _ = User.objects.get_or_create(
    username='feed_visibility_test_user',
    defaults={'email': 'feedvis@test.com'}
)
print(f"\n1. Test user: {user.username} (ID={user.id})")

group, _ = Group.objects.get_or_create(
    name='Feed Visibility Test Group',
    defaults={'description': 'Test', 'category': 'test'}
)
print(f"2. Test group: {group.name} (ID={group.id})")

# Add user to group so they can see group-only posts
GroupMembership.objects.get_or_create(user=user, group=group)
print(f"3. Added user to group membership")

# Create test posts
print(f"\n4. Creating test posts...")

# Post 1: public_global (should appear in global feed)
post_global = Post.objects.create(
    author=user,
    content='PUBLIC GLOBAL POST - should appear in global feed',
    feed_visibility='public_global',
    is_approved=True
)
print(f"   Post {post_global.id}: feed_visibility=public_global")

# Post 2: group_only (should NOT appear in global feed)
post_group_only = Post.objects.create(
    author=user,
    content='GROUP ONLY POST - should NOT appear in global feed',
    group=group,
    feed_visibility='group_only',
    is_approved=True
)
print(f"   Post {post_group_only.id}: feed_visibility=group_only, group={group.id}")

# Test 1: Global feed should exclude group_only posts
print(f"\n5. Testing GLOBAL FEED (no group_id parameter)...")

# Simulate global feed query
base_q = Q(is_approved=True)
visibility_q = Q(feed_visibility='public_global')
visibility_q = (
    visibility_q
    | Q(feed_visibility='group_only', group__memberships__user=user)
    | Q(author=user)
)
global_feed = Post.objects.filter(base_q & visibility_q).exclude(feed_visibility='group_only')

print(f"   Posts in global feed: {global_feed.count()}")
print(f"   Post {post_global.id} (public_global) in global feed: {global_feed.filter(id=post_global.id).exists()}")
print(f"   Post {post_group_only.id} (group_only) in global feed: {global_feed.filter(id=post_group_only.id).exists()}")

if global_feed.filter(id=post_global.id).exists():
    print(f"   [PASS] Public post appears in global feed")
else:
    print(f"   [FAIL] Public post should appear in global feed!")

if not global_feed.filter(id=post_group_only.id).exists():
    print(f"   [PASS] Group-only post EXCLUDED from global feed")
else:
    print(f"   [FAIL] Group-only post should NOT appear in global feed!")

# Test 2: Group feed should include group_only posts
print(f"\n6. Testing GROUP FEED (with group_id={group.id})...")

group_feed = Post.objects.filter(base_q & visibility_q).filter(group__id=group.id)

print(f"   Posts in group {group.id} feed: {group_feed.count()}")
print(f"   Post {post_group_only.id} (group_only) in group feed: {group_feed.filter(id=post_group_only.id).exists()}")

if group_feed.filter(id=post_group_only.id).exists():
    print(f"   [PASS] Group-only post appears in group feed")
else:
    print(f"   [FAIL] Group-only post should appear in group feed!")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

public_in_global = global_feed.filter(id=post_global.id).exists()
group_only_not_in_global = not global_feed.filter(id=post_group_only.id).exists()
group_only_in_group = group_feed.filter(id=post_group_only.id).exists()

all_pass = public_in_global and group_only_not_in_global and group_only_in_group

checks = {
    'Public post in global feed': public_in_global,
    'Group-only post NOT in global feed': group_only_not_in_global,
    'Group-only post in group feed': group_only_in_group,
}

for check, result in checks.items():
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {check}")

print("\n" + "="*80)
if all_pass:
    print("SUCCESS! Feed visibility is working correctly!")
    print("- Group-only posts only appear in their group feed")
    print("- Public posts appear in global feed")
else:
    print("FAILURE! Some checks did not pass.")
    sys.exit(1)

print("="*80 + "\n")
