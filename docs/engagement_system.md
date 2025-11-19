# Engagement System API Documentation

## Overview

The NAG Community Engagement System automatically logs all user interactions (likes, comments, mentions) and provides comprehensive analytics, reputation scoring, and role-specific insights for facilitators and corporate users.

## Architecture

### Models

#### CommunityEngagementLog
Comprehensive engagement logging for all community interactions.

**Fields:**
- `user` - User performing the action
- `action_type` - Type of engagement (like_post, comment_post, mention_user, etc.)
- `post` - Post being engaged with (nullable)
- `comment` - Comment being engaged with (nullable)
- `group` - Group being engaged with (nullable)
- `mentioned_user` - User being mentioned (nullable)
- `metadata` - Additional context as JSON
- `created_at` - Timestamp of action
- `updated_at` - Last modification timestamp

**Action Types:**
- `like_post` - User liked a post
- `unlike_post` - User unliked a post
- `like_comment` - User liked a comment
- `unlike_comment` - User unliked a comment
- `comment_post` - User commented on a post
- `reply_comment` - User replied to a comment
- `mention_user` - User mentioned someone
- `join_group` - User joined a group
- `leave_group` - User left a group
- `view_post` - User viewed a post
- `share_post` - User shared a post
- `bookmark_post` - User bookmarked a post
- `unbookmark_post` - User removed bookmark

#### UserReputation
User reputation scoring and activity level tracking.

**Fields:**
- `user` - User account
- `reputation_score` - Overall reputation points (0-1000+)
- `total_engagements` - Count of all engagement actions
- `activity_level` - Level (inactive, novice, active, power_user, community_leader)
- `badges` - Array of earned badges
- `created_at` - When reputation was created
- `last_updated` - When reputation was last calculated

**Activity Levels:**
- `inactive` - 0 engagements in 30 days (😴)
- `novice` - 1-10 engagements (🌱)
- `active` - 11-50 engagements (⚡)
- `power_user` - 51-200 engagements (🔥)
- `community_leader` - 200+ engagements (👑)

**Badge System:**
- `first_comment` - Commented for the first time
- `first_like` - Liked something for the first time
- `ten_likes` - Earned 10 likes on posts/comments
- `commenter` - Made 10+ comments
- `mentioned` - Was mentioned 5+ times
- `group_starter` - Created or started a group
- `helpful_contributor` - High engagement quality
- `top_engager` - Top 10% most engaged user
- `community_voice` - Recognized contributor
- `influencer` - Has significant reach

#### MentionLog
Tracks @mentions of users.

**Fields:**
- `mentioned_user` - User being mentioned
- `mentioned_by` - User doing the mentioning
- `post` - Post containing mention (nullable)
- `comment` - Comment containing mention (nullable)
- `mention_context` - The text containing the mention
- `created_at` - When mention occurred
- `notification_sent` - Whether notification was sent

#### EngagementNotification
Tracks notification delivery status.

**Fields:**
- `user` - Notification recipient
- `triggered_by` - User who triggered the notification
- `engagement_log` - Related engagement action
- `notification_type` - Type of notification
- `message` - Notification message
- `read` - Whether user read the notification
- `email_sent` - Whether email was sent
- `email_delivered` - Whether email was delivered
- `in_app_sent` - Whether in-app notification was sent
- `created_at` - When notification was created

**Notification Types:**
- `post_liked` - Post received a like
- `post_commented` - Post received a comment
- `comment_liked` - Comment received a like
- `comment_replied` - Comment received a reply
- `post_mentioned` - User mentioned in post
- `comment_mentioned` - User mentioned in comment
- `group_update` - New activity in user's groups

## API Endpoints

### User Engagement Metrics

**GET** `/api/engagement/analytics/user_metrics/`

Get engagement metrics for a user over a specified period.

**Query Parameters:**
- `days` (integer, default: 30) - Number of days to look back
- `action_type` (string, optional) - Filter by specific action type

**Response:**
```json
{
  "user_id": 1,
  "username": "john_doe",
  "metrics": {
    "total_engagements": 42,
    "likes": 15,
    "comments": 8,
    "mentions": 2,
    "group_joins": 3,
    "comment_likes": 10,
    "comment_replies": 4,
    "period": "30 days",
    "average_per_day": 1.4
  }
}
```

### Post Engagement Metrics

**GET** `/api/engagement/analytics/post_metrics/`

Get engagement metrics for a specific post.

**Query Parameters:**
- `post_id` (integer, required) - ID of the post

**Response:**
```json
{
  "post_id": 5,
  "post_title": "How to Learn Django",
  "metrics": {
    "total_likes": 24,
    "total_comments": 8,
    "total_shares": 3,
    "engagement_rate": 0.35,
    "reach": 150
  }
}
```

**Permissions:** Post author or admin only

### Trending Posts

**GET** `/api/engagement/analytics/trending/`

Get trending posts leaderboard.

**Query Parameters:**
- `days` (integer, default: 7) - Time period for trending
- `limit` (integer, default: 10) - Number of results

**Response:**
```json
{
  "trending_posts": [
    {
      "post_id": 1,
      "post_title": "Introduction to REST APIs",
      "author": {
        "id": 3,
        "username": "jane_smith",
        "email": "jane@example.com"
      },
      "total_engagements": 89,
      "likes": 45,
      "comments": 28,
      "engagement_score": 0.95,
      "created_at": "2025-11-10T14:30:00Z",
      "period": "7 days"
    }
  ]
}
```

### Active Users

**GET** `/api/engagement/analytics/active_users/`

Get leaderboard of most active users.

**Query Parameters:**
- `days` (integer, default: 7) - Time period
- `limit` (integer, default: 20) - Number of results

**Response:**
```json
{
  "active_users": [
    {
      "user_id": 1,
      "username": "power_user",
      "total_engagements": 156,
      "reputation_score": 450,
      "activity_level": "power_user",
      "avatar_url": "https://example.com/avatar.jpg",
      "period": "7 days"
    }
  ]
}
```

### User Reputation

**GET** `/api/engagement/analytics/my_reputation/`

Get authenticated user's reputation and badges.

**Response:**
```json
{
  "id": 1,
  "user_id": 15,
  "reputation_score": 245,
  "total_engagements": 67,
  "activity_level": "active",
  "activity_level_display": "Active",
  "badges": ["first_comment", "commenter", "helpful_contributor"],
  "badges_display": [
    {
      "name": "first_comment",
      "awarded_at": "2025-10-15T10:00:00Z"
    }
  ],
  "last_updated": "2025-11-15T18:30:00Z"
}
```

### Course Popularity (Facilitator Only)

**GET** `/api/engagement/analytics/course_popularity/`

Get course engagement insights (facilitator access only).

**Response:**
```json
{
  "courses": [
    {
      "course_id": 1,
      "course_name": "Django Masterclass",
      "total_engagements": 234,
      "likes": 120,
      "comments": 89,
      "active_participants": 45,
      "engagement_rate": 0.68,
      "trend": "up"
    }
  ]
}
```

**Permissions:** Facilitator role only

### Campaign Performance (Corporate Only)

**GET** `/api/engagement/analytics/campaign_performance/`

Get campaign engagement metrics (corporate access only).

**Response:**
```json
{
  "campaigns": [
    {
      "campaign_id": 1,
      "campaign_name": "Black Friday Sale",
      "total_engagements": 512,
      "likes": 234,
      "comments": 156,
      "mentions": 89,
      "engagement_rate": 0.85,
      "impressions": 600,
      "ctr": 0.45,
      "conversion_rate": 0.12,
      "trend": "up"
    }
  ]
}
```

**Permissions:** Corporate user role only

### Community Statistics

**GET** `/api/engagement/analytics/community_stats/`

Get public community-wide statistics.

**Response:**
```json
{
  "total_users": 5432,
  "active_users": 1200,
  "total_posts": 8945,
  "total_comments": 23456,
  "total_engagements": 98765,
  "total_mentions": 1234,
  "total_groups": 345,
  "total_group_members": 4567,
  "avg_engagement_per_post": 11.0,
  "avg_engagement_per_user": 18.2,
  "community_health_score": 0.78,
  "top_contributors": [...],
  "trending_posts": [...]
}
```

**Permissions:** Public (AllowAny)

### User Mentions

**GET** `/api/engagement/analytics/my_mentions/`

Get recent mentions of authenticated user.

**Query Parameters:**
- `limit` (integer, default: 20) - Number of results

**Response:**
```json
{
  "mentions": [
    {
      "id": 1,
      "mentioned_by": {
        "id": 3,
        "username": "jane_smith"
      },
      "post": {
        "id": 5,
        "title": "Best practices",
        "content": "@john_doe what do you think?"
      },
      "comment": null,
      "mention_context": "what do you think?",
      "created_at": "2025-11-15T14:30:00Z",
      "notification_sent": true
    }
  ]
}
```

### Engagement Notifications

**GET** `/api/engagement/analytics/my_notifications/`

Get engagement notifications for authenticated user.

**Query Parameters:**
- `limit` (integer, default: 20) - Number of results
- `read` (boolean, optional) - Filter by read status

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "user_id": 1,
      "triggered_by": {
        "id": 2,
        "username": "jane_smith"
      },
      "notification_type": "post_liked",
      "notification_type_display": "Post Liked",
      "message": "jane_smith liked your post",
      "read": false,
      "email_sent": true,
      "email_delivered": true,
      "in_app_sent": true,
      "created_at": "2025-11-15T18:00:00Z"
    }
  ]
}
```

### Mark Notifications as Read

**POST** `/api/engagement/analytics/mark_notifications_read/`

Mark notifications as read.

**Request Body:**
```json
{
  "notification_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "marked_read": 3,
  "status": "success"
}
```

## Signal Handlers

### Automatic Engagement Logging

The system automatically logs engagement when:

1. **Post Reactions (Likes)**
   - Triggers: `log_post_like` on PostReaction creation
   - Logs: 'like_post' action
   - Updates: Post ranking, sends notification to author

2. **Comments**
   - Triggers: `log_comment_post` on Comment creation
   - Logs: 'comment_post' or 'reply_comment'
   - Extracts: @mentions and sends notifications
   - Notifies: Post author and parent commenter

3. **Comment Reactions**
   - Triggers: `log_comment_like` on CommentReaction creation
   - Logs: 'like_comment' action
   - Notifies: Comment author

4. **Group Membership**
   - Triggers: `log_group_join` and `log_group_leave`
   - Logs: 'join_group' or 'leave_group'

5. **User Creation**
   - Triggers: `create_user_reputation`
   - Auto-creates: UserReputation record for new users

6. **Reputation Updates**
   - Triggers: `update_user_reputation`
   - Recalculates: Reputation score and activity level every 10 engagements

## Notification Service

The NotificationService handles multi-channel notifications with role-based customization.

**Features:**
- Email and in-app notification sending
- Template rendering with Django templates
- Role-specific messaging (corporate, facilitator, individual)
- Notification delivery tracking
- Digest email support
- Bulk notification sending

**Email Templates:**
- `post_liked.html` - Post received a like
- `post_commented.html` - Post received a comment
- `comment_liked.html` - Comment received a like
- `comment_replied.html` - Comment received a reply
- `post_mentioned.html` - User mentioned in post
- `comment_mentioned.html` - User mentioned in comment
- `group_update.html` - New group activity

## Frontend Components

### ReputationBadge Component

Displays user reputation, activity level, and badges.

**Props:**
- `userId` (number) - User ID to fetch reputation for
- `inline` (boolean) - Compact inline display
- `showScore` (boolean) - Show reputation score
- `showBadges` (boolean) - Show earned badges
- `size` ('sm' | 'md' | 'lg') - Component size
- `className` (string) - Custom CSS classes

**Example:**
```tsx
<ReputationBadge userId={user.id} inline={true} size="md" />
```

### EngagementMetrics Component

Displays user engagement statistics over time.

**Props:**
- `userId` (number) - User ID
- `days` (number) - Time period (default: 30)
- `className` (string) - Custom CSS
- `compact` (boolean) - Compact layout

**Example:**
```tsx
<EngagementMetrics userId={user.id} days={30} compact={false} />
```

### EngagementNotifications Component

Displays recent engagement notifications with polling.

**Props:**
- `onNotificationRead` (function) - Callback when notification read
- `maxItems` (number) - Maximum items to show
- `className` (string) - Custom CSS

**Example:**
```tsx
<EngagementNotifications maxItems={5} />
```

## Caching Strategy

- **Post Engagement Metrics:** Cached for 1 hour per post
- **User Activity:** Cached for 30 minutes per user
- **Reputation Scores:** Cached for 1 hour per user

Cache is automatically invalidated when:
- New engagement is logged
- Comment is created
- Post is updated
- User activity changes

## Security & Permissions

### Permission Checks
- **Public Endpoints:** `community_stats` (AllowAny)
- **Authenticated Endpoints:** Most endpoints (IsAuthenticated)
- **Facilitator Only:** `course_popularity`
- **Corporate Only:** `campaign_performance`
- **User Only:** `my_reputation`, `my_mentions`, `my_notifications`

### Data Privacy
- Users can only see their own metrics and notifications
- Post metrics only viewable by post author or admin
- Campaign metrics only visible to campaign owner
- Course metrics only visible to course facilitator

## Integration Points

### Community Feed
- Display engagement counts on posts
- Show trending posts section
- Display user reputation badges

### User Profiles
- Show user reputation and badges
- Display engagement statistics
- Show recent activity

### Dashboard
- Individual: Personal engagement metrics
- Facilitator: Course popularity analytics
- Corporate: Campaign performance metrics
- Admin: Community-wide statistics

## Best Practices

1. **Use Signal Handlers:** Don't log engagement manually in views
2. **Cache Strategically:** Use provided caching for metrics queries
3. **Batch Notifications:** Use `bulk_notify()` for mass notifications
4. **Monitor Reputation:** Check reputation calculations monthly
5. **Clean Old Logs:** Archive engagement logs older than 90 days

## Performance Considerations

- Indexes on frequently queried fields (user, created_at, action_type)
- Caching for expensive metric calculations
- Lazy loading of related objects in serializers
- Pagination for list endpoints (default 20 items)
- Async email sending (configure Celery for production)

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK` - Successful request
- `400 Bad Request` - Missing/invalid parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Future Enhancements

1. Real-time notifications via WebSockets
2. Custom badge creation by admins
3. Engagement gamification (leaderboards)
4. Recommendation engine based on engagement
5. Engagement timeline/history
6. Advanced analytics dashboard
7. Export engagement data to CSV/PDF
8. Engagement prediction ML model
