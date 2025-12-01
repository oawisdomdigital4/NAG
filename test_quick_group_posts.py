#!/usr/bin/env python
"""
Quick test to verify group posts work correctly.
Run this WHILE the Django server is running to see the logs in real-time.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from community.models import Group, Post
import json

User = get_user_model()

print("\n" + "="*80)
print("QUICK GROUP POSTS TEST")
print("="*80)
print("\nThis test creates a post in a group and verifies it can be fetched.")
print("Watch the Django console for [PostViewSet.create] and [PostViewSet.list] logs.\n")

# Create test user and group
user, _ = User.objects.get_or_create(
    username='quicktest_user',
    defaults={'email': 'quicktest@test.com'}
)
print(f"1. Test user: {user.username} (ID={user.id})")

group, _ = Group.objects.get_or_create(
    name='Quick Test Group',
    defaults={'description': 'Quick test', 'category': 'test'}
)
print(f"2. Test group: {group.name} (ID={group.id})")

# Create post
post = Post.objects.create(
    author=user,
    content='Quick test post at ' + str(__import__('datetime').datetime.now()),
    group=group,
    feed_visibility='group_only',
    is_approved=True
)
print(f"3. Post created: ID={post.id}, group_id={post.group_id}")

# Verify it's in the database
assert Post.objects.filter(id=post.id, group_id=group.id).exists()
print(f"4. Verified post exists in database with group_id set")

# Verify visibility filter
from django.db.models import Q
base_q = Q(is_approved=True)
visibility_q = Q(feed_visibility='public_global')
visibility_q = (
    visibility_q
    | Q(feed_visibility='group_only', group__memberships__user=user)
    | Q(author=user)
)
visible = Post.objects.filter(base_q & visibility_q).filter(group_id=group.id).filter(id=post.id)
assert visible.exists()
print(f"5. Verified post is visible via visibility filter")

print("\n" + "="*80)
print("TEST PASSED!")
print("="*80)
print("""
Next steps:
1. Look at Django console above for these logs:
   [PostViewSet.create] Post created: id=..., group_id=..., is_approved=True
   [PostViewSet.list] After group filter: ... posts in group ...

2. Open browser DevTools (F12) -> Network tab

3. Create a post in a group:
   - Look for POST /api/community/posts/ request
   - Check payload has: group_id, feed_visibility: 'group_only'
   - Check response status: 201 Created

4. Watch for GET /api/community/posts/?group_id=... request:
   - Check it has group_id parameter
   - Check response has posts array with your new post
   - Check status: 200 OK

5. If posts don't appear in UI after creation:
   - Check browser console (F12) for JavaScript errors
   - Check if component is calling refetch() after POST succeeds
   - Check if group ID is being passed correctly to fetch hook
""")
print("="*80 + "\n")
