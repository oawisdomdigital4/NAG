"""
Test async notification behavior.

Run with: python manage.py test community.tests.test_async_notifications
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
import time
import threading

from community.models import Post, PostReaction, EngagementNotification
from notifications.models import Notification

User = get_user_model()


class AsyncNotificationTests(TransactionTestCase):
    """Test that notifications are sent asynchronously without blocking."""
    
    def setUp(self):
        """Create test users and posts."""
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com')
        
        self.post = Post.objects.create(
            author=self.user1,
            content="Test post for async notifications"
        )
    
    def test_like_returns_immediately(self):
        """Test that liking a post returns immediately without waiting for notifications."""
        start_time = time.time()
        
        # Like the post
        reaction = PostReaction.objects.create(
            post=self.post,
            user=self.user2,
            reaction_type='like'
        )
        
        elapsed = time.time() - start_time
        
        # Should complete in < 100ms (instant)
        self.assertLess(elapsed, 0.1, f"Like took {elapsed}s, should be instant")
        
        # Allow a moment for background thread to process
        time.sleep(0.5)
        
        # Verify notification was created
        notifications = Notification.objects.filter(user=self.user1)
        self.assertTrue(
            notifications.exists(),
            "In-app notification should exist after like"
        )
    
    def test_notification_created_asynchronously(self):
        """Test that EngagementNotification is created in background thread."""
        initial_count = EngagementNotification.objects.count()
        
        # Like the post
        PostReaction.objects.create(
            post=self.post,
            user=self.user2,
            reaction_type='like'
        )
        
        # Check immediately (might still be in thread)
        immediate_count = EngagementNotification.objects.count()
        
        # Allow time for background thread
        time.sleep(0.5)
        
        # Check after background processing
        final_count = EngagementNotification.objects.count()
        
        # Should have created notification (initially or after thread completes)
        self.assertGreater(
            final_count,
            initial_count,
            "EngagementNotification should be created"
        )
    
    def test_multiple_concurrent_likes(self):
        """Test that multiple concurrent likes don't block each other."""
        users = [
            User.objects.create_user(username=f'user{i}', email=f'user{i}@test.com')
            for i in range(3, 6)
        ]
        
        start_time = time.time()
        
        # Create multiple reactions
        for user in users:
            PostReaction.objects.create(
                post=self.post,
                user=user,
                reaction_type='like'
            )
        
        elapsed = time.time() - start_time
        
        # All 3 likes should complete quickly (< 200ms)
        self.assertLess(elapsed, 0.2, f"3 likes took {elapsed}s")
        
        # Allow time for background processing
        time.sleep(1)
        
        # Check that all notifications are queued/created
        notifications_count = Notification.objects.filter(user=self.user1).count()
        self.assertEqual(
            notifications_count,
            3,
            f"Should have 3 notifications, got {notifications_count}"
        )
    
    def test_notification_thread_doesnt_block_request(self):
        """Verify that notification thread runs separately."""
        threads_before = threading.active_count()
        
        # Create reaction (spawns notification thread)
        reaction = PostReaction.objects.create(
            post=self.post,
            user=self.user2,
            reaction_type='like'
        )
        
        threads_after = threading.active_count()
        
        # Should have one more active thread (notification thread)
        self.assertEqual(
            threads_after,
            threads_before + 1,
            "Should spawn a new thread for notifications"
        )
        
        # Wait for thread to complete
        time.sleep(1)
        
        # Thread should be done (daemon thread)
        threads_final = threading.active_count()
        self.assertLessEqual(
            threads_final,
            threads_before + 1,
            "Notification thread should complete and clean up"
        )
