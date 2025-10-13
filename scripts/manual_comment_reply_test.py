import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()
from django.conf import settings
# Allow testclient host used by Django tests
settings.ALLOWED_HOSTS = list(getattr(settings, 'ALLOWED_HOSTS', [])) + ['testserver']

from django.contrib.auth import get_user_model
from community.models import Post, Comment
from rest_framework.test import APIClient

User = get_user_model()

# Create or get users
u1, _ = User.objects.get_or_create(email='tester1@example.com', defaults={'username':'tester1', 'role':'individual'})
if not u1.password:
    u1.set_password('testpass')
    u1.save()

u2, _ = User.objects.get_or_create(email='tester2@example.com', defaults={'username':'tester2', 'role':'individual'})
if not u2.password:
    u2.set_password('testpass')
    u2.save()

# Ensure community profiles exist if the app expects them
try:
    # Create community_profile if model exists
    cp = getattr(u1, 'community_profile', None)
    if cp is None:
        from community.models import UserProfile
        UserProfile.objects.get_or_create(user=u1)
    cp2 = getattr(u2, 'community_profile', None)
    if cp2 is None:
        from community.models import UserProfile
        UserProfile.objects.get_or_create(user=u2)
except Exception:
    pass

# Ensure accounts.profile (accounts.UserProfile) exists and is approved so permissions allow access
try:
    from accounts.models import UserProfile as AccountsUserProfile
    prof1, _ = AccountsUserProfile.objects.get_or_create(user=u1)
    prof2, _ = AccountsUserProfile.objects.get_or_create(user=u2)
    # set full names and mark approved
    if not getattr(prof1, 'full_name', ''):
        prof1.full_name = 'Tester One'
        prof1.save()
    if not getattr(prof2, 'full_name', ''):
        prof2.full_name = 'Tester Two'
    prof2.community_approved = True
    prof2.save()
except Exception:
    pass

# Set full names on profiles so serializer will return full name
try:
    if hasattr(u1, 'community_profile'):
        p = u1.community_profile
        if not getattr(p, 'full_name', ''):
            p.full_name = 'Tester One'
            p.save()
    if hasattr(u2, 'community_profile'):
        p2 = u2.community_profile
        if not getattr(p2, 'full_name', ''):
            p2.full_name = 'Tester Two'
            p2.save()
except Exception:
    # try alternate profile name
    try:
        if hasattr(u1, 'profile'):
            p = u1.profile
            if not getattr(p, 'full_name', ''):
                p.full_name = 'Tester One'
                p.save()
        if hasattr(u2, 'profile'):
            p2 = u2.profile
            if not getattr(p2, 'full_name', ''):
                p2.full_name = 'Tester Two'
                p2.save()
            # mark community_approved so permission allows access
            p2.community_approved = True
            p2.save()
    except Exception:
        pass

# Ensure u2 is allowed to access community endpoints
try:
    if hasattr(u2, 'community_profile'):
        p = u2.community_profile
        p.community_approved = True
        p.save()
    elif hasattr(u2, 'profile'):
        p = u2.profile
        p.community_approved = True
        p.save()
except Exception:
    pass

# Create a post by u1
post = Post.objects.create(author=u1, content='Test post for replies')

# Create a parent comment by u1
parent = Comment.objects.create(post=post, author=u1, content='Parent comment')

# Now use test client as u2 to post a reply
client = APIClient()
client.force_authenticate(user=u2)

payload = {
    'post_id': post.id,
    'content': 'This is a reply to the parent comment',
    'parent_comment_id': parent.id
}

resp = client.post('/api/community/comments/', data=json.dumps(payload), content_type='application/json')
print('STATUS:', resp.status_code)

try:
    print(json.dumps(resp.json(), indent=2))
except Exception:
    print('Response text:', resp.content)

# Also fetch comments for the post to see list
resp2 = client.get(f'/api/community/posts/{post.id}/comments/')
print('\nComments list status:', resp2.status_code)
try:
    print(json.dumps(resp2.json(), indent=2))
except Exception:
    print('Response text:', resp2.content)
