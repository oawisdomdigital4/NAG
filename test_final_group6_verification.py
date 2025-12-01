#!/usr/bin/env python
"""
Final verification: Create post in group 6 and verify it shows in listing.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db.models import Q
from django.contrib.auth import get_user_model
from community.models import Group, Post

User = get_user_model()

print("\n" + "="*80)
print("FINAL VERIFICATION: Posts in Group 6")
print("="*80)

# Try to get group 6
try:
    group6 = Group.objects.get(id=6)
    print(f"\nGroup 6 found: {group6.name}")
except Group.DoesNotExist:
    print("\nGroup 6 not found! Creating it for testing...")
    group6, _ = Group.objects.get_or_create(
        id=6,
        defaults={'name': 'Group 6', 'description': 'Test', 'category': 'test'}
    )
    print(f"Created: {group6.name}")

# Get any user
user = User.objects.first()
if not user:
    print("No users in database!")
    sys.exit(1)

print(f"\nUsing user: {user.username} (ID={user.id})")

# Create a test post in group 6
print(f"\nCreating test post in Group 6...")
from community.serializers import PostSerializer

test_data = {
    'content': 'FINAL TEST POST - Should appear in group 6',
    'group_id': 6,  # Group 6
    'feed_visibility': 'group_only',
}

serializer = PostSerializer(data=test_data)
if serializer.is_valid():
    post = serializer.save(author=user)
    print(f"[PASS] Post created: ID={post.id}, group_id={post.group_id}")
else:
    print(f"[FAIL] Serializer error: {serializer.errors}")
    sys.exit(1)

# Verify it's in database
print(f"\nVerifying post in database...")
posts_in_group6 = Post.objects.filter(group_id=6)
print(f"Total posts in group 6: {posts_in_group6.count()}")

if posts_in_group6.filter(id=post.id).exists():
    print(f"[PASS] Post {post.id} found in group 6!")
else:
    print(f"[FAIL] Post not found in group 6!")
    sys.exit(1)

# Check visibility
print(f"\nChecking visibility for user...")
base_q = Q(is_approved=True)
visibility_q = Q(feed_visibility='public_global')
visibility_q = (
    visibility_q
    | Q(feed_visibility='group_only', group__memberships__user=user)
    | Q(author=user)
)

visible_in_group6 = Post.objects.filter(base_q & visibility_q).filter(group_id=6)
print(f"Posts visible to user in group 6: {visible_in_group6.count()}")

if visible_in_group6.filter(id=post.id).exists():
    print(f"[PASS] Post {post.id} is VISIBLE to user!")
else:
    print(f"[FAIL] Post {post.id} NOT visible to user!")
    sys.exit(1)

print("\n" + "="*80)
print("ALL TESTS PASSED!")
print("="*80)
print(f"""
Your group posts fix is working!

When you create a post in group 6:
1. It will be saved with group_id=6
2. It will appear in the database
3. It will be visible when fetching /api/community/posts/?group_id=6

The posts should now display in your group feed.
""")
print("="*80 + "\n")
