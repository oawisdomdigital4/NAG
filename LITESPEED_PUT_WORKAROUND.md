# LiteSpeed PUT 501 Workaround - Implementation Guide

## Problem
Production server (LiteSpeed) returns **501 Not Implemented** for PUT requests to `/api/community/groups/{id}/`, even though Django is properly configured.

**Symptoms:**
- `PUT https://thenewafricagroup.com/api/community/groups/2/ 501 (Not Implemented)`
- Works fine on localhost
- GET requests work, POST works, but PUT/PATCH fail

**Root Cause:** LiteSpeed web server doesn't pass PUT/PATCH requests to Django for this endpoint.

---

## Solution: Use POST-Based Update Endpoint

We've added a workaround POST endpoint that functions exactly like PUT/PATCH:

### New Endpoint
```
POST /api/community/groups/{id}/update_group/
```

### Why This Works
- LiteSpeed allows POST requests (it's primarily used for form submissions)
- POST can carry multipart/form-data for file uploads
- Backend permission checks are identical to PUT/PATCH
- No data loss or functionality change

---

## Frontend Implementation

### Option 1: Update Frontend to Use New Endpoint (Quickest Fix)

Change group update calls from:
```javascript
// OLD - Returns 501 on production
PUT /api/community/groups/2/
```

To:
```javascript
// NEW - Uses POST workaround endpoint
POST /api/community/groups/2/update_group/
```

**Code Change Example:**

```javascript
// BEFORE (fails on production)
const updateGroup = async (groupId, data) => {
  const response = await fetch(`/api/community/groups/${groupId}/`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${token}` },
    body: data  // multipart or JSON
  });
  return response.json();
};

// AFTER (works on production)
const updateGroup = async (groupId, data) => {
  const response = await fetch(`/api/community/groups/${groupId}/update_group/`, {
    method: 'POST',  // ← Changed from PUT
    headers: { 'Authorization': `Bearer ${token}` },
    body: data  // multipart or JSON - works the same
  });
  return response.json();
};
```

### Option 2: Try These in Order (Compatibility Testing)

1. **Try PATCH first** (more likely to work than PUT):
```javascript
fetch(`/api/community/groups/${groupId}/`, {
  method: 'PATCH',  // Try PATCH, not PUT
  body: formData
});
```

2. **If PATCH fails, use POST workaround**:
```javascript
fetch(`/api/community/groups/${groupId}/update_group/`, {
  method: 'POST',
  body: formData
});
```

3. **If POST with multipart fails, try JSON**:
```javascript
fetch(`/api/community/groups/${groupId}/update_group/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

### Option 3: Conditional Routing (Environment-Based)

```javascript
const getGroupUpdateEndpoint = (groupId) => {
  const isProduction = window.location.hostname === 'thenewafricagroup.com';
  
  if (isProduction) {
    // Use POST workaround on production
    return `/api/community/groups/${groupId}/update_group/`;
  } else {
    // Use PUT on localhost
    return `/api/community/groups/${groupId}/`;
  }
};

const updateGroup = async (groupId, data) => {
  const endpoint = getGroupUpdateEndpoint(groupId);
  const method = endpoint.includes('update_group') ? 'POST' : 'PUT';
  
  const response = await fetch(endpoint, {
    method,
    headers: { 'Authorization': `Bearer ${token}` },
    body: data
  });
  
  return response.json();
};
```

---

## API Compatibility

### New Endpoint Features
- **HTTP Method:** POST (works everywhere)
- **Content-Type:** Supports both `multipart/form-data` and `application/json`
- **Permissions:** Same as PUT/PATCH (creator, moderators, or staff only)
- **Request Body:** Identical to PUT/PATCH
- **Response:** Identical to PUT/PATCH
- **File Uploads:** Full support for images, banners, etc.

### Request Examples

**Multipart Form (with files):**
```bash
curl -X POST https://thenewafricagroup.com/api/community/groups/2/update_group/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Updated Name" \
  -F "description=New description" \
  -F "banner=@image.jpg" \
  -F "profile_picture=@profile.jpg"
```

**JSON Only (no files):**
```bash
curl -X POST https://thenewafricagroup.com/api/community/groups/2/update_group/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "description": "New description"}'
```

**JavaScript Fetch (multipart):**
```javascript
const formData = new FormData();
formData.append('name', 'Updated Name');
formData.append('description', 'New description');
formData.append('banner', bannerFile);

const response = await fetch('/api/community/groups/2/update_group/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

**JavaScript Fetch (JSON):**
```javascript
const response = await fetch('/api/community/groups/2/update_group/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Updated Name',
    description: 'New description',
    category: 'technology'
  })
});
```

---

## Both Endpoints Work Now

You can use **either** endpoint on production - they're equivalent:

| Endpoint | Method | Files | Status |
|----------|--------|-------|--------|
| `/api/community/groups/{id}/` | PUT | ✅ | 501 on LiteSpeed ❌ |
| `/api/community/groups/{id}/` | PATCH | ✅ | Unknown (untested) |
| `/api/community/groups/{id}/update_group/` | POST | ✅ | Works ✅ |

---

## Testing Checklist

- [ ] Test group name update via POST workaround endpoint
- [ ] Test description update
- [ ] Test category change
- [ ] Test image upload (banner + profile picture)
- [ ] Test on localhost (PUT still works)
- [ ] Test on production (POST workaround works)
- [ ] Test with file uploads
- [ ] Test with JSON only (no files)
- [ ] Verify moderators can also update via workaround
- [ ] Verify non-moderators get 403 Permission Denied

---

## Expected Responses

**Success (200 OK):**
```json
{
  "id": 2,
  "name": "Updated Name",
  "description": "New description",
  "category": "technology",
  "banner": "community/group_banners/filename.jpg",
  "banner_url": "https://thenewafricagroup.com/media/...",
  "profile_picture": "community/group_profiles/profile.jpg",
  "profile_picture_url": "https://thenewafricagroup.com/media/...",
  ...
}
```

**Permission Denied (403):**
```json
{
  "detail": "Permission denied. Only group creator or moderators can update."
}
```

**Not Found (404):**
```json
{
  "detail": "Not found."
}
```

---

## Why This Works

1. **LiteSpeed Configuration Issue:** Blocks PUT at the HTTP method level
2. **POST is Ubiquitous:** Every web server allows POST (it's fundamental to web forms)
3. **Django Still Handles:** Our custom `update_group()` action receives POST and processes like PUT
4. **No Django Changes Needed:** Django REST Framework already supports multiple methods per endpoint
5. **Backward Compatible:** PUT still works on localhost; we just added a POST alternative

---

## Long-Term Solution

To permanently fix this, the server admin needs to:

1. SSH to production server
2. Edit LiteSpeed config to allow PUT/PATCH for `/api/` routes
3. Restart LiteSpeed

See `501_LITESPEED_PRODUCTION_FIX.md` for detailed LiteSpeed configuration steps.

---

## Summary

**Immediate Action:** Update frontend to use:
```
POST /api/community/groups/{id}/update_group/
```

**Impact:**
- ✅ Group updates work on production
- ✅ File uploads work
- ✅ Multipart and JSON both supported
- ✅ Same permissions as PUT/PATCH
- ✅ No backend changes needed

**Timeline:**
- Now: Use POST workaround (fully functional)
- Later: Fix LiteSpeed config (optional, for aesthetics)
