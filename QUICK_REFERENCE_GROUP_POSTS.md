# Quick Reference: Group Posts Fix

## Changes Made

### 1. PostSerializer - Handle group_id Parameter
**File**: `community/serializers.py` (line 323)

```python
def to_internal_value(self, data):
    """Handle both 'group' and 'group_id' parameter names for backward compatibility."""
    if 'group_id' in data and 'group' not in data:
        data = dict(data)
        data['group'] = data.pop('group_id')
    return super().to_internal_value(data)
```

**Why**: Frontend sends `group_id` but serializer field is named `group`. This method converts `group_id` → `group` transparently.

---

### 2. PostViewSet.list() - Exclude group_only from Global Feed
**File**: `community/views.py` (line 612-616)

```python
else:
    # When viewing global feed (no group_id specified), exclude group-only posts
    qs = qs.exclude(feed_visibility='group_only')
    logger.info(f'[PostViewSet.list] Excluded group_only posts from global feed. Remaining: {qs.count()} posts')
```

**Why**: Group-only posts should only appear when viewing that specific group, not in the global community feed.

---

### 3. PostViewSet.create() - Enhanced Logging
**File**: `community/views.py` (lines 799-809)

```python
# Debug logging for group_id handling
logger.info(f'[PostViewSet.create] Request data keys: {list(request.data.keys())}')
logger.info(f'[PostViewSet.create] group in request.data: {"group" in request.data}')
logger.info(f'[PostViewSet.create] group_id in request.data: {"group_id" in request.data}')
if "group_id" in request.data:
    logger.info(f'[PostViewSet.create] Received group_id={request.data.get("group_id")}')
if "group" in request.data:
    logger.info(f'[PostViewSet.create] Received group={request.data.get("group")}')
```

**Why**: Track when group_id is being handled for debugging.

---

## How It Works

### Before Fix
```
Frontend: POST /api/community/posts/ {group_id: 6, ...}
  ↓
Serializer: group_id not recognized → ignored
  ↓
Post created with group_id=NULL ❌
```

### After Fix
```
Frontend: POST /api/community/posts/ {group_id: 6, ...}
  ↓
Serializer.to_internal_value(): group_id → group conversion
  ↓
Post created with group_id=6 ✓
  ↓
Global feed query: Excludes group_only posts ✓
  ↓
Group feed query: Shows group_only posts ✓
```

---

## Testing

Quick verification:
```bash
# Test serializer handles group_id
python test_serializer_group_id.py

# Test complete API flow
python test_api_flow_complete.py

# Test feed separation
python test_feed_comprehensive.py
```

All should show: `[PASS]` for all checks

---

## Behavior

| Scenario | Before | After |
|----------|--------|-------|
| Create post with group_id=6 | ❌ Ignored, created without group | ✓ Created with group_id=6 |
| View global feed | ❌ Group posts appear | ✓ Group posts excluded |
| View group 6 feed | ❌ No posts (none created) | ✓ Posts appear |
| Non-member sees group post | N/A | ✓ Cannot see |
| Member sees in group feed | N/A | ✓ Can see |
| Member sees in global feed | N/A | ✓ Cannot see |

---

## API Examples

### Create Group Post
```bash
POST /api/community/posts/
{
  "content": "Hello group!",
  "group_id": 6,
  "feed_visibility": "group_only"
}
```

### Get Global Feed
```bash
GET /api/community/posts/
# Returns: public_global posts + user's own posts
# Excludes: group_only posts
```

### Get Group 6 Posts
```bash
GET /api/community/posts/?group_id=6
# Returns: group_only posts from group 6 (if user is member)
# Excludes: posts from other groups
```

---

## Logging

Watch Django console for:

```
[PostViewSet.create] Request data keys: ['content', 'group_id', 'feed_visibility', ...]
[PostViewSet.create] group_id in request.data: True
[PostViewSet.create] Received group_id=6
[PostViewSet.create] Post created: id=123, group_id=6, feed_visibility=group_only, is_approved=True
[PostViewSet.list] Excluded group_only posts from global feed. Remaining: 42 posts
```

---

## Verification Checklist

- [x] Posts created with `group_id` are saved to DB
- [x] Posts appear in group-specific feed
- [x] Posts do NOT appear in global feed
- [x] Public posts still in global feed
- [x] Non-members cannot see group posts
- [x] Serializer accepts both `group` and `group_id`
- [x] Auto-add to group membership works
- [x] Visibility filters work correctly

