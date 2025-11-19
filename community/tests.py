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

	def test_corporate_connections_create_list_accept(self):
		"""Test creating, listing, and accepting corporate connections."""
		from .models import CorporateConnection
		
		# Create a second user for connection
		user2 = User.objects.create_user(email='test2@example.com', password='pass1234', role='corporate')
		token2 = UserToken.objects.create(user=user2, expires_at=timezone.now()+timedelta(days=1))
		
		# Test 1: Create connection (as user1, receiver=user2)
		url = '/api/community/connections/'
		payload = {'receiver': user2.id, 'message': "Let's connect!"}
		resp = self.client.post(url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		data = resp.json()
		self.assertEqual(data['status'], 'pending')
		self.assertEqual(data['message'], "Let's connect!")
		self.assertEqual(data['sender'], self.user.id)
		self.assertEqual(data['receiver'], user2.id)
		conn_id = data['id']
		
		# Test 2: List connections (as user1 - should see the connection)
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		results = resp.json() if isinstance(resp.json(), list) else resp.json().get('results', [])
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]['id'], conn_id)
		
		# Test 3: Get stats (as user1)
		stats_url = '/api/community/connections/stats/'
		resp = self.client.get(stats_url)
		self.assertEqual(resp.status_code, 200)
		stats = resp.json()
		self.assertEqual(stats['total'], 1)
		self.assertEqual(stats['pending'], 1)
		self.assertEqual(stats['accepted'], 0)
		self.assertEqual(stats['rejected'], 0)
		
		# Test 4: Accept connection (as user2 - the receiver)
		client2 = APIClient()
		client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2.token}')
		accept_url = f'/api/community/connections/{conn_id}/accept/'
		resp = client2.post(accept_url)
		self.assertEqual(resp.status_code, 200)
		
		# Verify connection is now accepted
		conn = CorporateConnection.objects.get(id=conn_id)
		self.assertEqual(conn.status, 'accepted')
		self.assertIsNotNone(conn.connected_at)
		
		# Test 5: Check stats after accept
		resp = client2.get(stats_url)
		self.assertEqual(resp.status_code, 200)
		stats = resp.json()
		self.assertEqual(stats['total'], 1)
		self.assertEqual(stats['pending'], 0)
		self.assertEqual(stats['accepted'], 1)
		self.assertEqual(stats['rejected'], 0)

	def test_corporate_connections_reject(self):
		"""Test rejecting corporate connections."""
		from .models import CorporateConnection
		
		# Create a second user for connection
		user2 = User.objects.create_user(email='test3@example.com', password='pass1234', role='corporate')
		token2 = UserToken.objects.create(user=user2, expires_at=timezone.now()+timedelta(days=1))
		
		# Create connection (as user1, receiver=user2)
		url = '/api/community/connections/'
		payload = {'receiver': user2.id, 'message': 'Connect with me'}
		resp = self.client.post(url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		conn_id = resp.json()['id']
		
		# Reject connection (as user2 - the receiver)
		client2 = APIClient()
		client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2.token}')
		reject_url = f'/api/community/connections/{conn_id}/reject/'
		resp = client2.post(reject_url)
		self.assertEqual(resp.status_code, 200)
		
		# Verify connection is now rejected
		conn = CorporateConnection.objects.get(id=conn_id)
		self.assertEqual(conn.status, 'rejected')
		self.assertIsNone(conn.connected_at)  # rejection does not set connected_at
		
		# Check stats show rejected count
		stats_url = '/api/community/connections/stats/'
		resp = client2.get(stats_url)
		self.assertEqual(resp.status_code, 200)
		stats = resp.json()
		self.assertEqual(stats['total'], 1)
		self.assertEqual(stats['pending'], 0)
		self.assertEqual(stats['accepted'], 0)
		self.assertEqual(stats['rejected'], 1)

	def test_corporate_connections_prevent_self_connection(self):
		"""Test that a user cannot create a connection to themselves."""
		url = '/api/community/connections/'
		payload = {'receiver': self.user.id, 'message': 'Self connection'}
		resp = self.client.post(url, payload, format='json')
		self.assertEqual(resp.status_code, 400)

	def test_corporate_connections_prevent_duplicate(self):
		"""Test that duplicate connections are prevented."""
		user2 = User.objects.create_user(email='test4@example.com', password='pass1234', role='corporate')
		
		# Create first connection
		url = '/api/community/connections/'
		payload = {'receiver': user2.id, 'message': 'First'}
		resp = self.client.post(url, payload, format='json')
		self.assertEqual(resp.status_code, 201)
		
		# Try to create duplicate
		resp = self.client.post(url, payload, format='json')
		self.assertEqual(resp.status_code, 400)

