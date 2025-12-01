# Group Posts Fix - Complete Implementation

## Problem
Posts created with `group_id` and `feed_visibility='group_only'` were not appearing anywhere because:
1. ❌ Frontend was sending `group_id` but serializer expected `group` field
2. ❌ Posts were appearing in global feed (should be group-only)

## Solution Implemented

### 1. **Serializer Fix** (community/serializers.py - line 323)
Added `to_internal_value()` method to PostSerializer to handle both `group` and `group_id` parameters:
```python
def to_internal_value(self, data):
    """Handle both 'group' and 'group_id' parameter names for backward compatibility."""
    if 'group_id' in data and 'group' not in data:
        data = dict(data)
        data['group'] = data.pop('group_id')
    return super().to_internal_value(data)
```

**Result**: Frontend can now send `group_id` and posts are created with group relationship.

### 2. **Feed Separation Fix** (community/views.py - line 612)
Added filter to exclude `group_only` posts from global feed:
```python
else:
    # When viewing global feed (no group_id specified), exclude group-only posts
    qs = qs.exclude(feed_visibility='group_only')
```

**Result**: Group-only posts only appear in their specific group, not in global feed.

### 3. **Enhanced Logging** (community/views.py - lines 799-809)
Added debug logging to track when group_id is being handled:
```python
logger.info(f'[PostViewSet.create] Request data keys: {list(request.data.keys())}')
logger.info(f'[PostViewSet.create] group in request.data: {"group" in request.data}')
logger.info(f'[PostViewSet.create] group_id in request.data: {"group_id" in request.data}')
```

## Behavior After Fix

### Creating Posts in Groups
- Frontend sends: `{group_id: 6, feed_visibility: 'group_only', content: '...'}`
- Backend receives and converts to: `{group: 6, feed_visibility: 'group_only'}`
- Post is created with `group_id=6` ✓

### Viewing Global Feed
- Global feed shows: All `public_global` posts + author's own posts
- Global feed excludes: All `group_only` posts (even if user is member)
- **Result**: Clean separation - group posts don't leak into global feed ✓

### Viewing Group Feed
- Group feed shows: All `group_only` posts in that group (for members)
- Group feed shows: Author's own posts (visibility filters)
- **Result**: Members see only posts in their group ✓

### Non-members
- Cannot see `group_only` posts anywhere (global or group feed)
- Can see `public_global` posts in global feed
- **Result**: Privacy maintained ✓

## Test Results

All comprehensive tests pass:
```
[PASS] Post created with group_id
[PASS] Post marked as approved
[PASS] Post visible via visibility filter
[PASS] Post visible when filtering by group_id
[PASS] Public post in global feed
[PASS] Group-only post NOT in global feed
[PASS] Group-only post in group feed
[PASS] User 1 (member) sees group post only in group feed
[PASS] User 2 (non-member) cannot see group post anywhere
```

## Flow Diagrams

### Post Creation Flow
```
User creates post in group 6
  ↓
Frontend sends: POST /api/community/posts/
  {group_id: 6, feed_visibility: 'group_only', content: '...'}
  ↓
Serializer.to_internal_value() converts group_id → group
  ↓
Post saved with group_id=6
  ↓
User auto-added to GroupMembership (if not already)
  ↓
Response: 201 Created with post data
```

### Global Feed Fetch
```
User requests: GET /api/community/posts/
  (no group_id parameter)
  ↓
Backend applies visibility filter (approval, public/group, author)
  ↓
Backend EXCLUDES group_only posts
  ↓
Returns: public_global posts + user's own posts
```

### Group Feed Fetch
```
User requests: GET /api/community/posts/?group_id=6
  ↓
Backend applies visibility filter (approval, public/group, author)
  ↓
Backend filters by group_id=6
  ↓
Returns: group_only posts from group 6 (if user is member)
```

## Files Modified

1. **community/serializers.py** (lines 323-329)
   - Added `to_internal_value()` method to handle `group_id` parameter

2. **community/views.py** (lines 612-616)
   - Added filter to exclude `group_only` posts from global feed
   - Enhanced logging in create method (lines 799-809)

## Backward Compatibility

✓ Old code sending `group` parameter still works
✓ New code sending `group_id` parameter now works
✓ Both parameters are accepted and handled correctly

## Verification Scripts

Created test scripts to verify the fix:
- `test_serializer_group_id.py` - Serializer handles both parameter names
- `test_api_flow_complete.py` - Complete API flow works
- `test_feed_visibility.py` - Group-only posts excluded from global feed
- `test_feed_comprehensive.py` - Full feed separation behavior
- `test_final_group6_verification.py` - Group 6 specifically verified

Run any test:
```bash
python test_feed_comprehensive.py
```

## Key Points

1. **Group-only posts now created correctly** with `group_id` parameter
2. **Posts appear in group feed** when accessing `/api/community/posts/?group_id=X`
3. **Posts don't leak into global feed** - proper visibility separation maintained
4. **Members see group posts only in group** - not in general community feed
5. **Non-members cannot see group posts** - privacy maintained
6. **Public posts still appear in global feed** - as expected

## Testing Checklist

- [x] Posts created with `group_id` are saved to database
- [x] Posts appear in group-specific feed
- [x] Posts do NOT appear in global feed
- [x] Public posts appear in global feed as normal
- [x] Non-members cannot see group-only posts
- [x] Serializer handles both `group` and `group_id` parameters
- [x] Auto-add to group membership works
- [x] Visibility filters still work correctly
- [x] Logging shows correct flow

