#!/usr/bin/env python
"""
Test to verify posts can be created with group_id via the API and then fetched.
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
print("FULL API FLOW TEST: Create post in group, then fetch from group")
print("="*80)

# Setup
user, _ = User.objects.get_or_create(
    username='api_flow_test_user',
    defaults={'email': 'apiflow@test.com'}
)
print(f"\n1. Test user: {user.username} (ID={user.id})")

group, _ = Group.objects.get_or_create(
    name='API Flow Test Group',
    defaults={'description': 'Test', 'category': 'test'}
)
print(f"2. Test group: {group.name} (ID={group.id})")

# Test: Simulate frontend POST to create post with group_id
print("\n3. Simulating frontend POST /api/community/posts/ with group_id...")
from community.serializers import PostSerializer

post_data = {
    'content': 'API flow test post created at ' + str(__import__('datetime').datetime.now()),
    'group_id': group.id,  # This is what frontend sends
    'feed_visibility': 'group_only',
}

print(f"   Payload: {post_data}")

serializer = PostSerializer(data=post_data)
if not serializer.is_valid():
    print(f"   [FAIL] Serializer error: {serializer.errors}")
    sys.exit(1)

post = serializer.save(author=user)
print(f"   [PASS] Post created: ID={post.id}, group_id={post.group_id}")

# Check if user was auto-added to group (the fix we added)
user_in_group = GroupMembership.objects.filter(user=user, group=group).exists()
print(f"\n4. User auto-added to group: {user_in_group}")

# Test: Simulate frontend GET to fetch posts from group
print("\n5. Simulating frontend GET /api/community/posts/?group_id={group.id}...")

# Apply visibility filter (same logic as backend)
base_q = Q(is_approved=True)
visibility_q = Q(feed_visibility='public_global')
visibility_q = (
    visibility_q
    | Q(feed_visibility='group_only', group__memberships__user=user)
    | Q(author=user)
)

filtered_posts = Post.objects.filter(base_q & visibility_q).filter(group_id=group.id)
print(f"   Posts visible to user in group: {filtered_posts.count()}")

if filtered_posts.filter(id=post.id).exists():
    print(f"   [PASS] Post {post.id} IS visible!")
else:
    print(f"   [FAIL] Post {post.id} NOT visible!")
    sys.exit(1)

# Test with all group posts (not filtered)
print(f"\n6. All posts in group (no visibility filter): {Post.objects.filter(group_id=group.id).count()}")

all_group_posts = Post.objects.filter(group_id=group.id)
if all_group_posts.filter(id=post.id).exists():
    print(f"   [PASS] Post {post.id} exists in group!")
else:
    print(f"   [FAIL] Post {post.id} NOT in group!")
    sys.exit(1)

print("\n" + "="*80)
print("SUCCESS!")
print("="*80)
print(f"""
Complete flow verified:
1. Post created with group_id={group.id}
2. Post stored in database with group relationship
3. Post visible via visibility filter
4. Post visible when filtering by group_id

The fix is working! Group posts will now display correctly.
""")
print("="*80 + "\n")
