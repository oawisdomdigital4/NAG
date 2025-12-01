#!/usr/bin/env python
"""
Test script to verify group posts are created with group_id and visible in group feed.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from community.models import Group, GroupMembership, Post

User = get_user_model()

def test_group_post_creation_and_visibility():
    """Test that posts created in groups are visible to the creator."""
    
    print("\n" + "="*70)
    print("TEST: Group Post Creation and Visibility")
    print("="*70)
    
    # 1. Get or create test users
    print("\n1. Creating test users...")
    user1, created = User.objects.get_or_create(
        username='testuser1',
        defaults={'email': 'testuser1@test.com'}
    )
    print(f"   User1 (testuser1): {'Created' if created else 'Exists'}")
    
    user2, created = User.objects.get_or_create(
        username='testuser2',
        defaults={'email': 'testuser2@test.com'}
    )
    print(f"   User2 (testuser2): {'Created' if created else 'Exists'}")
    
    # 2. Create or get a test group
    print("\n2. Creating test group...")
    group, created = Group.objects.get_or_create(
        name='Test Group for Posts',
        defaults={
            'description': 'A test group for verifying post creation',
            'category': 'test'
        }
    )
    print(f"   Group (ID={group.id}): {'Created' if created else 'Exists'}")
    
    # 3. Manually add user2 to the group (to simulate existing member)
    print("\n3. Adding user2 to group...")
    membership, created = GroupMembership.objects.get_or_create(
        user=user2,
        group=group
    )
    print(f"   User2 group membership: {'Created' if created else 'Exists'}")
    
    # 4. Create a post by user1 in the group
    print("\n4. Creating post in group by user1...")
    post = Post.objects.create(
        author=user1,
        content='This is a test post in the group',
        group=group,
        feed_visibility='group_only',
        is_approved=True
    )
    print(f"   Post created (ID={post.id}):")
    print(f"      - Author: {post.author.username}")
    print(f"      - Group: {post.group.name}")
    print(f"      - Feed Visibility: {post.feed_visibility}")
    print(f"      - Is Approved: {post.is_approved}")
    
    # 5. Check if user1 was auto-added to group membership
    print("\n5. Checking group membership after post creation...")
    user1_in_group = GroupMembership.objects.filter(user=user1, group=group).exists()
    print(f"   User1 in group membership: {user1_in_group}")
    
    if user1_in_group:
        print("   ✓ FIX WORKING: User auto-added to group when creating post!")
    else:
        print("   ✗ FIX NOT WORKING: User not auto-added to group!")
    
    # 6. Verify visibility filter would include the post
    print("\n6. Checking visibility filter logic for user1...")
    from django.db.models import Q
    
    # Simulate what get_queryset does
    base_q = Q(is_approved=True)
    visibility_q = Q(feed_visibility='public_global')
    visibility_q = (
        visibility_q
        | Q(feed_visibility='group_only', group__memberships__user=user1)
        | Q(author=user1)
    )
    
    filtered_posts = Post.objects.filter(base_q & visibility_q).filter(group=group)
    print(f"   Posts visible to user1 in this group: {filtered_posts.count()}")
    
    if filtered_posts.exists():
        print("   ✓ Post is visible to user1!")
        for p in filtered_posts:
            print(f"      - Post {p.id}: {p.content[:50]}...")
    else:
        print("   ✗ Post is NOT visible to user1!")
    
    # 7. Verify visibility filter would include the post for user2
    print("\n7. Checking visibility filter logic for user2...")
    filtered_posts_u2 = Post.objects.filter(base_q & Q(
        Q(feed_visibility='public_global') |
        Q(feed_visibility='group_only', group__memberships__user=user2) |
        Q(author=user2)
    )).filter(group=group)
    print(f"   Posts visible to user2 in this group: {filtered_posts_u2.count()}")
    
    if filtered_posts_u2.exists():
        print("   ✓ Post is visible to user2!")
    else:
        print("   ✗ Post is NOT visible to user2!")
    
    # 8. Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    checks = {
        'Post created with group': post.group_id == group.id,
        'Post marked as approved': post.is_approved,
        'User auto-added to group': user1_in_group,
        'Post visible to author': filtered_posts.exists(),
        'Post visible to member': filtered_posts_u2.exists(),
    }
    
    all_pass = all(checks.values())
    
    for check, result in checks.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check}")
    
    print("\n" + "="*70)
    if all_pass:
        print("✓ ALL TESTS PASSED! Group posts should now display correctly.")
    else:
        print("✗ SOME TESTS FAILED. Group posts may not display correctly.")
    print("="*70 + "\n")
    
    return all_pass

if __name__ == '__main__':
    success = test_group_post_creation_and_visibility()
    sys.exit(0 if success else 1)
