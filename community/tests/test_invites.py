from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ..models import Group, GroupInvite, GroupMembership


class GroupInviteTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='pass')
        self.invited = User.objects.create_user(username='inv', email='inv@example.com', password='pass')
        self.other = User.objects.create_user(username='other', email='other@example.com', password='pass')

        self.group = Group.objects.create(name='Test Group', description='desc', category='general', created_by=self.owner, is_private=True)

        self.client = Client()

    def test_create_invite_and_accept(self):
        # Owner logs in and creates an invite for invited user
        self.client.login(username='owner', password='pass')
        url = f'/api/community/groups/{self.group.id}/create_invite/'
        resp = self.client.post(url, {'invitee_id': self.invited.id})
        self.assertEqual(resp.status_code, 201, msg=resp.content)
        data = resp.json()
        token = data.get('token') or data.get('token')
        self.assertTrue(token)

        # Invited user accepts the invite
        self.client.logout()
        self.client.login(username='inv', password='pass')
        accept_url = f'/api/community/groups/{self.group.id}/accept_invite/'
        resp2 = self.client.post(accept_url, {'token': token})
        self.assertIn(resp2.status_code, (200, 201), msg=resp2.content)

        # Ensure membership exists
        membership_exists = GroupMembership.objects.filter(user=self.invited, group=self.group).exists()
        self.assertTrue(membership_exists)

    def test_join_with_token_endpoint(self):
        # Create an invite via model directly
        invite = GroupInvite.objects.create(group=self.group, invited_by=self.owner, invited_user=self.invited)

        # Invited user posts to join with token
        self.client.login(username='inv', password='pass')
        join_url = f'/api/community/groups/{self.group.id}/join/'
        resp = self.client.post(join_url, {'invite_token': invite.token})
        self.assertIn(resp.status_code, (200, 201), msg=resp.content)

        self.assertTrue(GroupMembership.objects.filter(user=self.invited, group=self.group).exists())
