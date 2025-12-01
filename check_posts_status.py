#!/usr/bin/env python
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
django.setup()

from django.contrib.auth import get_user_model
from community.models import Post, Group
from django.db.models import Q

User = get_user_model()

print("\n=== POST AND GROUP STATUS ===")
print(f"Total posts: {Post.objects.count()}")
print(f"Total groups: {Group.objects.count()}")

# Show all posts with groups
posts_with_groups = Post.objects.filter(group__isnull=False).values('id', 'title', 'group_id', 'feed_visibility', 'is_approved')[:10]
print(f"\nPosts with groups ({posts_with_groups.count() if hasattr(posts_with_groups, 'count') else len(list(posts_with_groups))}):")
for p in posts_with_groups:
    print(f"  Post {p['id']}: group={p['group_id']}, visibility={p['feed_visibility']}, approved={p['is_approved']}")

# Check visibility per group
print("\n=== GROUP POST COUNTS ===")
for group in Group.objects.all()[:5]:
    post_count = group.posts.count()
    approved_count = group.posts.filter(is_approved=True).count()
    group_only_count = group.posts.filter(feed_visibility='group_only', is_approved=True).count()
    print(f"Group {group.id} ({group.name}): total={post_count}, approved={approved_count}, group_only={group_only_count}")
