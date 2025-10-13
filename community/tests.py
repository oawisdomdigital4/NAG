from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, UserToken
from .models import Group, GroupMembership


class CommunityTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='test@example.com', password='pass1234', role='individual')
		self.group = Group.objects.create(name='Test Group', description='desc', category='Test', is_corporate_group=False, created_by=self.user)
		# Create token
		token = UserToken.objects.create(user=self.user, expires_at=timezone.now()+timedelta(days=1))
		self.token_value = str(token.token)
		self.client = APIClient()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_value}')

	def test_join_and_leave_group(self):
		join_url = f'/api/community/groups/{self.group.id}/join/'
		leave_url = f'/api/community/groups/{self.group.id}/leave/'

		# Join
		resp = self.client.post(join_url)
		self.assertIn(resp.status_code, (200,201))
		self.assertTrue(GroupMembership.objects.filter(user=self.user, group=self.group).exists())

		# Leave
		resp = self.client.post(leave_url)
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(GroupMembership.objects.filter(user=self.user, group=self.group).exists())

	def test_create_post_with_link_and_file(self):
		# create a sample post via multipart upload
		url = '/api/community/posts/'
		with open(__file__, 'rb') as f:
			resp = self.client.post(url, {'content': 'hello', 'group_id': self.group.id, 'feed_visibility': 'group_only', 'post_category': 'standard', 'media_urls': '["https://example.com/page"]'}, format='multipart')
			# allow 201 or 200 depending on serializer
			self.assertIn(resp.status_code, (200,201))

	def test_create_comment_with_parent(self):
		from .models import Post
		post = Post.objects.create(author=self.user, content='p', group=self.group)
		url = '/api/community/comments/'
		resp = self.client.post(url, {'post_id': post.id, 'content': 'c1'}, format='json')
		self.assertEqual(resp.status_code, 201)
		c1 = resp.json()
		resp2 = self.client.post(url, {'post_id': post.id, 'content': 'reply', 'parent_comment_id': c1['id']}, format='json')
		self.assertEqual(resp2.status_code, 201)

	def test_toggle_bookmark(self):
		from .models import Post
		post = Post.objects.create(author=self.user, content='p', group=self.group)
		url = f'/api/community/posts/{post.id}/toggle_bookmark/'
		resp = self.client.post(url)
		self.assertIn(resp.status_code, (200,201))
		resp2 = self.client.post(url)
		self.assertEqual(resp2.status_code, 200)

