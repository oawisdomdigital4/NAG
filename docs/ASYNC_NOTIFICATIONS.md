# Asynchronous Notification System

## Overview
The engagement notification system now runs asynchronously using Python threading. This ensures that:

1. **Frontend gets instant feedback** - API responses return immediately after the action (like/bookmark/comment)
2. **Notifications are sent in background** - In-app and email notifications are processed without blocking the request
3. **No external dependencies** - Uses Python's built-in `threading` module

## How It Works

### Request Flow
```
User Action (like/bookmark/comment)
    ↓
API View processes action
    ↓
Signal fires (e.g., post_save on PostReaction)
    ↓
EngagementNotification.create_and_notify() called
    ↓
NotificationService.send_engagement_notification() creates background thread
    ↓
API Response returned immediately (✓ Instant frontend feedback)
    ↓
Background thread processes notifications asynchronously
```

### Implementation Details

#### NotificationService Changes
- `send_engagement_notification()` now spawns a daemon thread instead of blocking
- Thread calls `_send_notifications_async()` which handles:
  - Checking user notification preferences
  - Sending in-app notifications to Notification model
  - Sending email notifications
  - All without blocking the main request

#### Key Files
- `community/notification_service.py` - Async notification sending
- `community/engagement_signals.py` - Signal handlers (unchanged, works with async service)
- `community/engagement.py` - Notification model and create_and_notify method
- `community/tasks.py` - Task utilities for future Celery migration

## Features

### Thread Safety
- Django ORM queries are thread-safe
- Each notification thread has its own database connection
- Daemon threads allow graceful app shutdown

### Error Handling
- Try-except blocks prevent notification errors from affecting main request
- Errors are logged but don't crash the app or user action

### Scalability
- **Current:** Threading (suitable for small-medium traffic)
- **Future:** Can upgrade to Celery + Redis without changing signal logic
  - Create Celery tasks in `community/tasks.py`
  - Replace threading calls with Celery `.delay()` calls
  - No frontend/API changes needed

## User Experience

### Actions that Send Async Notifications
- ❤️ Liking a post
- 💬 Commenting on a post
- 🔗 Replying to a comment
- 🔖 Bookmarking a post
- 👥 Joining a group

### Timeline
```
t=0ms   User clicks like button
t=5ms   API receives request
t=10ms  PostReaction object created
t=15ms  Signal fires, background thread spawned
t=20ms  API response sent with {liked: true, likes_count: N}
        ↓ Frontend updates UI instantly
t=50ms  Background thread: In-app notification created
t=100ms Background thread: Email sent (if enabled)
        ↓ User sees notification in-app/email
```

The user experiences instant UI feedback (at t=20ms) while notifications arrive in background.

## Configuration

### Enable/Disable Notifications
Notifications respect user preferences via `NotificationPreference`:
```python
# Check user's preferences
try:
    pref = NotificationPreference.objects.get(
        user=user,
        notification_type='community'
    )
except NotificationPreference.DoesNotExist:
    pref = NotificationPreference(
        user=user,
        notification_type='community',
        in_app_enabled=True,
        email_enabled=True
    )
```

### Future: Migrate to Celery
When ready to add Celery:

1. Install Celery and Redis
2. Create `myproject/celery.py`
3. Update `myproject/settings.py` with Celery config
4. In `community/notification_service.py`, replace:
   ```python
   # FROM:
   thread = threading.Thread(target=cls._send_notifications_async, ...)
   
   # TO:
   from .tasks import send_notifications_async_task
   send_notifications_async_task.delay(engagement_notification.id)
   ```
5. Add async tasks to `community/tasks.py` using `@shared_task` decorator

## Testing

Test async notifications:
```python
# Create a post and like it
post = Post.objects.create(author=user1, content="Test")
PostReaction.objects.create(post=post, user=user2, reaction_type='like')

# Check that:
# 1. API response is immediate (< 100ms)
# 2. In-app notification created (in Notification model)
# 3. Email sent (if enabled)
# 4. No request timeout or errors
```

## Troubleshooting

### Notifications not appearing
1. Check user's `NotificationPreference` settings
2. Verify `Notification` model records are created
3. Check email server configuration if email not sending
4. Review Django logs for thread errors

### Performance Issues
- Threading works fine for < 1000 concurrent users
- For higher traffic, migrate to Celery + Redis
- Add monitoring to track background thread execution times

## Future Improvements

1. **Celery Integration** - Move to proper task queue
2. **Retry Logic** - Automatic retry for failed notifications
3. **Rate Limiting** - Prevent notification spam
4. **WebSocket Support** - Real-time in-app notifications
5. **Notification Digest** - Hourly/daily digest emails instead of real-time
