"""
Diagnostic script to test group post creation and filtering.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from community.models import Post, Group, GroupMembership
from django.db.models import Q

User = get_user_model()

def run_diagnostics():
    print("\n" + "="*60)
    print("GROUP POSTS DIAGNOSTIC")
    print("="*60)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='test_diagnostic_user',
        defaults={'email': 'test@diagnostic.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    print(f"\n✓ Test user: {user.username} (id={user.id})")
    
    # Get or create test groups
    group1, created1 = Group.objects.get_or_create(
        name='Test Group 1',
        defaults={'description': 'First test group', 'created_by': user}
    )
    print(f"✓ Test Group 1: id={group1.id}")
    
    group2, created2 = Group.objects.get_or_create(
        name='Test Group 2',
        defaults={'description': 'Second test group', 'created_by': user}
    )
    print(f"✓ Test Group 2: id={group2.id}")
    
    # Add user to both groups
    GroupMembership.objects.get_or_create(
        group=group1,
        user=user,
        defaults={'role': 'member'}
    )
    GroupMembership.objects.get_or_create(
        group=group2,
        user=user,
        defaults={'role': 'member'}
    )
    print(f"\n✓ User is member of both groups")
    
    # Create test posts
    post1, _ = Post.objects.get_or_create(
        title='Post in Group 1',
        content='This post is in group 1',
        group=group1,
        author=user,
        feed_visibility='group_only',
        is_approved=True,
        defaults={'post_category': 'general'}
    )
    print(f"\n✓ Created Post 1 in Group 1: id={post1.id}")
    
    post2, _ = Post.objects.get_or_create(
        title='Post in Group 2',
        content='This post is in group 2',
        group=group2,
        author=user,
        feed_visibility='group_only',
        is_approved=True,
        defaults={'post_category': 'general'}
    )
    print(f"✓ Created Post 2 in Group 2: id={post2.id}")
    
    # Test visibility filtering
    print("\n" + "="*60)
    print("VISIBILITY FILTER TEST")
    print("="*60)
    
    # Simulate the backend get_queryset logic
    qs = Post.objects.all()
    
    # Apply visibility filters (from PostViewSet.get_queryset)
    base_q = Q(is_approved=True)
    visibility_q = Q(feed_visibility='public_global')
    visibility_q = (
        visibility_q
        | Q(feed_visibility='group_only', group__memberships__user=user)
        | Q(author=user)
    )
    filtered_qs = qs.filter(base_q & visibility_q).distinct()
    
    print(f"\nTotal posts after visibility filter: {filtered_qs.count()}")
    for p in filtered_qs:
        print(f"  - Post {p.id}: group={p.group_id}, visibility={p.feed_visibility}")
    
    # Test group-specific filtering
    print("\n" + "="*60)
    print("GROUP-SPECIFIC FILTER TEST")
    print("="*60)
    
    # Test filtering for group 1
    print(f"\nFiltering for Group {group1.id}:")
    group1_posts = filtered_qs.filter(group__id=group1.id)
    print(f"  Posts count: {group1_posts.count()}")
    for p in group1_posts:
        print(f"  - Post {p.id}: title={p.title}")
    
    # Test filtering for group 2
    print(f"\nFiltering for Group {group2.id}:")
    group2_posts = filtered_qs.filter(group__id=group2.id)
    print(f"  Posts count: {group2_posts.count()}")
    for p in group2_posts:
        print(f"  - Post {p.id}: title={p.title}")
    
    # Test edge case: public_global posts
    print("\n" + "="*60)
    print("PUBLIC GLOBAL POSTS TEST")
    print("="*60)
    
    global_post, _ = Post.objects.get_or_create(
        title='Global Post',
        content='This is a global post',
        group=None,
        author=user,
        feed_visibility='public_global',
        is_approved=True,
        defaults={'post_category': 'general'}
    )
    print(f"\n✓ Created global post: id={global_post.id}")
    
    # Check if global posts appear in group filters
    print(f"\nGlobal posts in Group 1 filter:")
    global_in_group1 = filtered_qs.filter(group__id=group1.id, feed_visibility='public_global')
    print(f"  Count: {global_in_group1.count()}")
    
    print("\n" + "="*60)
    print("✓ DIAGNOSTIC COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    run_diagnostics()
