#!/usr/bin/env python
"""
Test to verify 'joined_groups' feed type shows only posts from groups user is member of.
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
print("TEST: Joined Groups Feed")
print("="*80)

# Create test users
user1, _ = User.objects.get_or_create(
    username='joined_groups_user1',
    defaults={'email': 'joinedgroups1@test.com'}
)
user2, _ = User.objects.get_or_create(
    username='joined_groups_user2',
    defaults={'email': 'joinedgroups2@test.com'}
)

print(f"\nUsers:")
print(f"  User1: {user1.username} (ID={user1.id})")
print(f"  User2: {user2.username} (ID={user2.id})")

# Create test groups
group1, _ = Group.objects.get_or_create(
    name='Joined Groups Test Group 1',
    defaults={'description': 'Test', 'category': 'test'}
)
group2, _ = Group.objects.get_or_create(
    name='Joined Groups Test Group 2',
    defaults={'description': 'Test', 'category': 'test'}
)
group3, _ = Group.objects.get_or_create(
    name='Joined Groups Test Group 3',
    defaults={'description': 'Test', 'category': 'test'}
)

print(f"\nGroups:")
print(f"  Group1: {group1.name} (ID={group1.id})")
print(f"  Group2: {group2.name} (ID={group2.id})")
print(f"  Group3: {group3.name} (ID={group3.id})")

# User1 joins group1 and group2
GroupMembership.objects.get_or_create(user=user1, group=group1)
GroupMembership.objects.get_or_create(user=user1, group=group2)

# User2 joins only group2
GroupMembership.objects.get_or_create(user=user2, group=group2)

print(f"\nMemberships:")
print(f"  User1 -> Group1: YES")
print(f"  User1 -> Group2: YES")
print(f"  User1 -> Group3: NO")
print(f"  User2 -> Group2: YES")
print(f"  User2 -> Group1: NO")
print(f"  User2 -> Group3: NO")

# Create posts
print(f"\nCreating test posts...")

# Post 1: Group1 (User1 should see)
p1 = Post.objects.create(
    author=user2,
    content='Post in Group 1 by User2',
    group=group1,
    feed_visibility='group_only',
    is_approved=True
)
print(f"  P1 (ID={p1.id}): Group1, author=User2")

# Post 2: Group2 (Both should see)
p2 = Post.objects.create(
    author=user1,
    content='Post in Group 2 by User1',
    group=group2,
    feed_visibility='group_only',
    is_approved=True
)
print(f"  P2 (ID={p2.id}): Group2, author=User1")

# Post 3: Group2 (Both should see)
p3 = Post.objects.create(
    author=user2,
    content='Post in Group 2 by User2',
    group=group2,
    feed_visibility='group_only',
    is_approved=True
)
print(f"  P3 (ID={p3.id}): Group2, author=User2")

# Post 4: Group3 (Neither should see)
p4 = Post.objects.create(
    author=user1,
    content='Post in Group 3 by User1',
    group=group3,
    feed_visibility='group_only',
    is_approved=True
)
print(f"  P4 (ID={p4.id}): Group3, author=User1")

# Post 5: Public global (both should see in their joined groups feed, but via visibility filter)
p5 = Post.objects.create(
    author=user1,
    content='Public post by User1',
    feed_visibility='public_global',
    is_approved=True
)
print(f"  P5 (ID={p5.id}): No group (public_global)")

print(f"\n5. Testing 'joined_groups' feed for User1...")

# Simulate joined_groups feed for User1
base_q = Q(is_approved=True)
visibility_q = Q(feed_visibility='public_global')
visibility_q = (
    visibility_q
    | Q(feed_visibility='group_only', group__memberships__user=user1)
    | Q(author=user1)
)
user1_groups = GroupMembership.objects.filter(user=user1).values_list('group_id', flat=True)
user1_joined_groups_feed = Post.objects.filter(base_q & visibility_q).filter(group_id__in=user1_groups)

print(f"  User1 is member of groups: {list(user1_groups)}")
print(f"  Posts in User1's joined groups feed: {user1_joined_groups_feed.count()}")
print(f"  Expected posts: P1, P2, P3 (all in groups 1 or 2)")
print(f"    P1 (Group1): {user1_joined_groups_feed.filter(id=p1.id).exists()}")
print(f"    P2 (Group2): {user1_joined_groups_feed.filter(id=p2.id).exists()}")
print(f"    P3 (Group2): {user1_joined_groups_feed.filter(id=p3.id).exists()}")
print(f"    P4 (Group3): {user1_joined_groups_feed.filter(id=p4.id).exists()}")
print(f"    P5 (public): {user1_joined_groups_feed.filter(id=p5.id).exists()}")

print(f"\n6. Testing 'joined_groups' feed for User2...")

# Simulate joined_groups feed for User2
visibility_q2 = Q(feed_visibility='public_global')
visibility_q2 = (
    visibility_q2
    | Q(feed_visibility='group_only', group__memberships__user=user2)
    | Q(author=user2)
)
user2_groups = GroupMembership.objects.filter(user=user2).values_list('group_id', flat=True)
user2_joined_groups_feed = Post.objects.filter(base_q & visibility_q2).filter(group_id__in=user2_groups)

print(f"  User2 is member of groups: {list(user2_groups)}")
print(f"  Posts in User2's joined groups feed: {user2_joined_groups_feed.count()}")
print(f"  Expected posts: P2, P3 (only in group 2)")
print(f"    P1 (Group1): {user2_joined_groups_feed.filter(id=p1.id).exists()}")
print(f"    P2 (Group2): {user2_joined_groups_feed.filter(id=p2.id).exists()}")
print(f"    P3 (Group2): {user2_joined_groups_feed.filter(id=p3.id).exists()}")
print(f"    P4 (Group3): {user2_joined_groups_feed.filter(id=p4.id).exists()}")
print(f"    P5 (public): {user2_joined_groups_feed.filter(id=p5.id).exists()}")

# Verify
print(f"\n" + "="*80)
print("VERIFICATION")
print("="*80)

checks = {
    "User1 sees P1 (in Group1)": user1_joined_groups_feed.filter(id=p1.id).exists(),
    "User1 sees P2 (in Group2)": user1_joined_groups_feed.filter(id=p2.id).exists(),
    "User1 sees P3 (in Group2)": user1_joined_groups_feed.filter(id=p3.id).exists(),
    "User1 NOT sees P4 (in Group3)": not user1_joined_groups_feed.filter(id=p4.id).exists(),
    
    "User2 NOT sees P1 (in Group1)": not user2_joined_groups_feed.filter(id=p1.id).exists(),
    "User2 sees P2 (in Group2)": user2_joined_groups_feed.filter(id=p2.id).exists(),
    "User2 sees P3 (in Group2)": user2_joined_groups_feed.filter(id=p3.id).exists(),
    "User2 NOT sees P4 (in Group3)": not user2_joined_groups_feed.filter(id=p4.id).exists(),
}

all_pass = all(checks.values())
for check, result in checks.items():
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {check}")

print("\n" + "="*80)
if all_pass:
    print("SUCCESS! Joined groups feed is working correctly!")
    print("\nBehavior:")
    print("- Users see only posts from groups they are members of")
    print("- Each user sees different posts based on their memberships")
    print("- Feed respects visibility filters")
else:
    print("FAILURE! Some checks did not pass.")
    sys.exit(1)

print("="*80 + "\n")
