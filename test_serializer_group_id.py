#!/usr/bin/env python
"""
Test to verify group_id parameter is correctly handled by serializer.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from community.models import Group, Post
from community.serializers import PostSerializer

User = get_user_model()

print("\n" + "="*80)
print("TEST: Serializer handling of group_id parameter")
print("="*80)

# Create test user and group
user, _ = User.objects.get_or_create(
    username='serializer_test_user',
    defaults={'email': 'sertest@test.com'}
)
print(f"\n1. Test user: {user.username} (ID={user.id})")

group, _ = Group.objects.get_or_create(
    name='Serializer Test Group',
    defaults={'description': 'Test', 'category': 'test'}
)
print(f"2. Test group: {group.name} (ID={group.id})")

# Test 1: Send data with 'group_id' (what frontend sends)
print("\n3. Testing serializer with group_id parameter (frontend format):")
data_with_group_id = {
    'content': 'Test post with group_id param',
    'group_id': group.id,  # This is what frontend sends
    'feed_visibility': 'group_only',
}
print(f"   Input data: {data_with_group_id}")

serializer = PostSerializer(data=data_with_group_id)
if serializer.is_valid():
    print(f"   [PASS] Serializer is valid!")
    print(f"   Validated data keys: {list(serializer.validated_data.keys())}")
    print(f"   Validated data group: {serializer.validated_data.get('group')}")
    
    # Save the post
    post1 = serializer.save(author=user)
    print(f"   [PASS] Post created with ID={post1.id}")
    print(f"   Post.group_id: {post1.group_id}")
    
    if post1.group_id == group.id:
        print(f"   [PASS] group_id correctly set to {group.id}!")
    else:
        print(f"   [FAIL] group_id not set correctly. Expected {group.id}, got {post1.group_id}")
else:
    print(f"   [FAIL] Serializer validation failed!")
    print(f"   Errors: {serializer.errors}")

# Test 2: Send data with 'group' (for backward compatibility)
print("\n4. Testing serializer with group parameter (backward compat):")
data_with_group = {
    'content': 'Test post with group param',
    'group': group.id,  # Old format
    'feed_visibility': 'group_only',
}
print(f"   Input data: {data_with_group}")

serializer2 = PostSerializer(data=data_with_group)
if serializer2.is_valid():
    print(f"   [PASS] Serializer is valid!")
    post2 = serializer2.save(author=user)
    print(f"   [PASS] Post created with ID={post2.id}, group_id={post2.group_id}")
else:
    print(f"   [FAIL] Serializer validation failed!")
    print(f"   Errors: {serializer2.errors}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Verify both posts are in database
post1_exists = Post.objects.filter(id=post1.id, group_id=group.id).exists()
post2_exists = Post.objects.filter(id=post2.id, group_id=group.id).exists()

print(f"Post 1 in DB with group_id set: {post1_exists}")
print(f"Post 2 in DB with group_id set: {post2_exists}")

if post1_exists and post2_exists:
    print("\n[PASS] Both posts created successfully with group_id!")
    print("The fix works! Frontend can now send group_id and posts will be created correctly.")
else:
    print("\n[FAIL] Posts not created properly with group_id!")

print("="*80 + "\n")
