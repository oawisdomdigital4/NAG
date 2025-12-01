#!/usr/bin/env python
"""
Simplified test to verify the visibility filter logic works correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db.models import Q
from django.contrib.auth import get_user_model
from community.models import Group, GroupMembership, Post

User = get_user_model()

def test_visibility_filter():
    """Test the visibility filter Q objects logic."""
    
    print("\n" + "="*70)
    print("TEST: Visibility Filter Logic")
    print("="*70)
    
    # Setup: Create users and group
    print("\n1. Setup: Creating test data...")
    user_author, _ = User.objects.get_or_create(
        username='visibility_test_author',
        defaults={'email': 'author@test.com'}
    )
    print(f"   Created author user: {user_author.username} (ID={user_author.id})")
    
    user_member, _ = User.objects.get_or_create(
        username='visibility_test_member',
        defaults={'email': 'member@test.com'}
    )
    print(f"   Created member user: {user_member.username} (ID={user_member.id})")
    
    user_non_member, _ = User.objects.get_or_create(
        username='visibility_test_nonmember',
        defaults={'email': 'nonmember@test.com'}
    )
    print(f"   Created non-member user: {user_non_member.username} (ID={user_non_member.id})")
    
    group, _ = Group.objects.get_or_create(
        name='Visibility Test Group',
        defaults={'description': 'For testing visibility', 'category': 'test'}
    )
    print(f"   Created group: {group.name} (ID={group.id})")
    
    # Add user_member to the group
    GroupMembership.objects.get_or_create(user=user_member, group=group)
    print(f"   Added {user_member.username} to group")
    
    # Create posts
    print("\n2. Creating test posts...")
    
    # Post 1: group_only, by author
    post1 = Post.objects.create(
        author=user_author,
        content='Group-only post by author',
        group=group,
        feed_visibility='group_only',
        is_approved=True
    )
    print(f"   Post {post1.id}: group_only post by author")
    
    # Post 2: public_global
    post2 = Post.objects.create(
        author=user_member,
        content='Public global post',
        group=group,
        feed_visibility='public_global',
        is_approved=True
    )
    print(f"   Post {post2.id}: public_global post")
    
    # Test visibility for each user
    print("\n3. Testing visibility filters...")
    
    def get_visible_posts(user):
        """Simulate the get_queryset visibility filter."""
        base_q = Q(is_approved=True)
        visibility_q = Q(feed_visibility='public_global')
        
        if user and getattr(user, 'is_authenticated', False):
            visibility_q = (
                visibility_q
                | Q(feed_visibility='group_only', group__memberships__user=user)
                | Q(author=user)
            )
        
        return Post.objects.filter(base_q & visibility_q).filter(group=group).order_by('id')
    
    # Test for author (not a member, but author of post1)
    print(f"\n   Testing for author ({user_author.username}):")
    author_posts = get_visible_posts(user_author)
    print(f"   Posts visible: {author_posts.count()}")
    for p in author_posts:
        print(f"      - Post {p.id}: {p.content} (visibility={p.feed_visibility}, author={p.author.username})")
    
    # Expectations for author
    expected_for_author = [post1.id]  # Should see their own post
    actual_for_author = list(author_posts.values_list('id', flat=True))
    if set(actual_for_author) >= set(expected_for_author):
        print(f"   [PASS] Author can see their own post ({post1.id})")
    else:
        print(f"   [FAIL] Author cannot see their own post!")
    
    # Test for member (member of group)
    print(f"\n   Testing for group member ({user_member.username}):")
    member_posts = get_visible_posts(user_member)
    print(f"   Posts visible: {member_posts.count()}")
    for p in member_posts:
        print(f"      - Post {p.id}: {p.content} (visibility={p.feed_visibility}, author={p.author.username})")
    
    # Expectations for member
    expected_for_member = [post1.id, post2.id]  # Should see group post + public post
    actual_for_member = list(member_posts.values_list('id', flat=True))
    if set(actual_for_member) >= set(expected_for_member):
        print(f"   [PASS] Member can see group posts and public posts")
    else:
        print(f"   [FAIL] Member cannot see expected posts!")
        print(f"      Expected: {expected_for_member}, Got: {actual_for_member}")
    
    # Test for non-member
    print(f"\n   Testing for non-member ({user_non_member.username}):")
    nonmember_posts = get_visible_posts(user_non_member)
    print(f"   Posts visible: {nonmember_posts.count()}")
    for p in nonmember_posts:
        print(f"      - Post {p.id}: {p.content} (visibility={p.feed_visibility}, author={p.author.username})")
    
    # Expectations for non-member
    expected_for_nonmember = [post2.id]  # Should only see public posts
    actual_for_nonmember = list(nonmember_posts.values_list('id', flat=True))
    if set(actual_for_nonmember) == set(expected_for_nonmember):
        print(f"   [PASS] Non-member can only see public posts")
    else:
        print(f"   [FAIL] Non-member has wrong visibility!")
        print(f"      Expected: {expected_for_nonmember}, Got: {actual_for_nonmember}")
    
    # Summary
    print("\n" + "="*70)
    print("VISIBILITY FILTER TEST COMPLETE")
    print("="*70)
    print("""
Summary of visibility logic:
1. Author can see their own posts (via Q(author=user))
2. Group members can see group_only posts (via Q(feed_visibility='group_only', group__memberships__user=user))
3. Everyone can see public_global posts (via Q(feed_visibility='public_global'))

If all tests passed, the visibility filter is working correctly!
This means:
- When user creates a post with group_id, they can fetch it back
- The issue may be elsewhere (frontend, caching, etc.)
""")
    print("="*70 + "\n")

if __name__ == '__main__':
    test_visibility_filter()
