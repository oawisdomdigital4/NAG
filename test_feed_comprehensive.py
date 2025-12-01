#!/usr/bin/env python
"""
Comprehensive test: Group posts appear ONLY in group, not in global feed.
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
print("COMPREHENSIVE TEST: Group vs Global Feed Separation")
print("="*80)

# Setup users
user1, _ = User.objects.get_or_create(
    username='comp_test_user1',
    defaults={'email': 'comptest1@test.com'}
)
user2, _ = User.objects.get_or_create(
    username='comp_test_user2',
    defaults={'email': 'comptest2@test.com'}
)

print(f"\nUsers:")
print(f"  User 1: {user1.username} (ID={user1.id})")
print(f"  User 2: {user2.username} (ID={user2.id})")

# Setup group
group_a, _ = Group.objects.get_or_create(
    name='Comprehensive Test Group A',
    defaults={'description': 'Test', 'category': 'test'}
)

print(f"\nGroup:")
print(f"  Group A: {group_a.name} (ID={group_a.id})")

# Add only user1 to group
GroupMembership.objects.get_or_create(user=user1, group=group_a)
print(f"\nMemberships:")
print(f"  User 1 -> Group A: YES (member)")
print(f"  User 2 -> Group A: NO (not member)")

# Create posts
print(f"\n5. Creating posts...")

# Post 1: Public global (visible to everyone)
p1 = Post.objects.create(
    author=user1,
    content='PUBLIC POST from User 1 - visible to all',
    feed_visibility='public_global',
    is_approved=True
)
print(f"  P1 (ID={p1.id}): author=User1, visibility=PUBLIC_GLOBAL")

# Post 2: Group-only (visible to group members only)
p2 = Post.objects.create(
    author=user1,
    content='GROUP-ONLY POST from User 1 in Group A',
    group=group_a,
    feed_visibility='group_only',
    is_approved=True
)
print(f"  P2 (ID={p2.id}): author=User1, group=A, visibility=GROUP_ONLY")

# Post 3: Another public post
p3 = Post.objects.create(
    author=user2,
    content='PUBLIC POST from User 2 - visible to all',
    feed_visibility='public_global',
    is_approved=True
)
print(f"  P3 (ID={p3.id}): author=User2, visibility=PUBLIC_GLOBAL")

# Test visibility for each user
print(f"\n6. Testing feed visibility...")

def get_global_feed(user):
    """Simulate global feed (no group_id specified)"""
    base_q = Q(is_approved=True)
    visibility_q = Q(feed_visibility='public_global')
    if user and getattr(user, 'is_authenticated', True):
        visibility_q = (
            visibility_q
            | Q(feed_visibility='group_only', group__memberships__user=user)
            | Q(author=user)
        )
    return Post.objects.filter(base_q & visibility_q).exclude(feed_visibility='group_only')

def get_group_feed(user, group):
    """Simulate group feed (with group_id specified)"""
    base_q = Q(is_approved=True)
    visibility_q = Q(feed_visibility='public_global')
    if user and getattr(user, 'is_authenticated', True):
        visibility_q = (
            visibility_q
            | Q(feed_visibility='group_only', group__memberships__user=user)
            | Q(author=user)
        )
    return Post.objects.filter(base_q & visibility_q).filter(group__id=group.id)

# Test for User 1 (group member)
print(f"\n   === USER 1 (Group member) ===")

global_feed_u1 = get_global_feed(user1)
group_feed_u1 = get_group_feed(user1, group_a)

print(f"\n   GLOBAL FEED (should have P1, P3):")
print(f"      P1 (public): {global_feed_u1.filter(id=p1.id).exists()}")
print(f"      P2 (group-only): {global_feed_u1.filter(id=p2.id).exists()}")
print(f"      P3 (public): {global_feed_u1.filter(id=p3.id).exists()}")

print(f"\n   GROUP A FEED (should have P2 + P1 because User1 authored P1):")
print(f"      P1 (author's post): {group_feed_u1.filter(id=p1.id).exists() if p1.group_id else 'N/A (no group)'}")
print(f"      P2 (group post): {group_feed_u1.filter(id=p2.id).exists()}")

# Test for User 2 (not group member)
print(f"\n   === USER 2 (NOT group member) ===")

global_feed_u2 = get_global_feed(user2)
group_feed_u2 = get_group_feed(user2, group_a)

print(f"\n   GLOBAL FEED (should have P1, P3 - NOT P2):")
print(f"      P1 (public): {global_feed_u2.filter(id=p1.id).exists()}")
print(f"      P2 (group-only): {global_feed_u2.filter(id=p2.id).exists()}")
print(f"      P3 (public): {global_feed_u2.filter(id=p3.id).exists()}")

print(f"\n   GROUP A FEED (should be empty - User2 not member):")
print(f"      P1 (author): {group_feed_u2.filter(id=p1.id).exists() if p1.group_id else 'N/A (no group)'}")
print(f"      P2 (group post): {group_feed_u2.filter(id=p2.id).exists()}")

# Final checks
print(f"\n" + "="*80)
print("VERIFICATION")
print("="*80)

checks = {
    "U1 sees P1 in global": global_feed_u1.filter(id=p1.id).exists(),
    "U1 sees P3 in global": global_feed_u1.filter(id=p3.id).exists(),
    "U1 does NOT see P2 in global": not global_feed_u1.filter(id=p2.id).exists(),
    "U1 sees P2 in group feed": group_feed_u1.filter(id=p2.id).exists(),
    
    "U2 sees P1 in global": global_feed_u2.filter(id=p1.id).exists(),
    "U2 sees P3 in global": global_feed_u2.filter(id=p3.id).exists(),
    "U2 does NOT see P2 in global": not global_feed_u2.filter(id=p2.id).exists(),
    "U2 does NOT see P2 in group feed": not group_feed_u2.filter(id=p2.id).exists(),
}

all_pass = all(checks.values())
for check, result in checks.items():
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {check}")

print("\n" + "="*80)
if all_pass:
    print("SUCCESS! All feed visibility tests passed!")
    print("\nBehavior:")
    print("- Group-only posts appear ONLY in their group feed")
    print("- Public posts appear in global feed")
    print("- Non-members cannot see group posts")
    print("- Members can see group posts in group feed, not in global feed")
else:
    print("FAILURE! Some checks did not pass.")
    sys.exit(1)

print("="*80 + "\n")
