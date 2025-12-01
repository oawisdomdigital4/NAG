import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from community.models import Post
from community.engagement import CommunityEngagementLog
from django.contrib.auth import get_user_model

User = get_user_model()

# Check some recent posts
posts = Post.objects.all().order_by('-created_at')[:10]
print('Recent Posts:')
for post in posts:
    print(f'  Post ID {post.id}: title="{post.title}" content_start="{post.content[:30]}..."')

# Check some recent activities with posts
print('\nRecent Activities with Posts:')
activities = CommunityEngagementLog.objects.select_related('post').filter(post__isnull=False).order_by('-created_at')[:10]
for activity in activities:
    if activity.post:
        print(f'  Activity {activity.id}: post_id={activity.post.id} post_title="{activity.post.title}" action={activity.action_type}')
