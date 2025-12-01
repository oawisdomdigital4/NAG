# 501 Not Implemented Error - Production LiteSpeed Fix

## Issue Summary
Frontend PUT request to update a group returns **501 Not Implemented** on production (thenewafricagroup.com) but works on local development.

**Request Details:**
- URL: https://thenewafricagroup.com/api/community/groups/2/
- Method: PUT
- Status Code: 501 Not Implemented
- Server: LiteSpeed
- Content-Type: multipart/form-data (file upload)
- Auth: Bearer token (valid)

## Root Cause
The 501 error is from **LiteSpeed web server**, not Django. Response shows:
- server: LiteSpeed
- content-type: text/html (not JSON)

**LiteSpeed is intercepting the request before Django can process it.**

## Django Status
✅ All methods are implemented and tested on localhost:
- GET /api/community/groups/ - Works
- POST /api/community/groups/ - Works
- GET /api/community/groups/2/ - Works
- PUT /api/community/groups/2/ - Works locally
- PATCH /api/community/groups/2/ - Works locally
- DELETE /api/community/groups/2/ - Works locally

**Problem is 100% server configuration, not Django code.**

## IMMEDIATE WORKAROUND (Use Now)

### Option 1: Use PATCH Instead of PUT (Recommended)

LiteSpeed is more likely to allow PATCH. Update your frontend:

```javascript
// Change from PUT to PATCH
const response = await fetch('/api/community/groups/2/', {
  method: 'PATCH',  // ← Changed from PUT
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData  // multipart still works
});
```

### Option 2: Send JSON Without Files

For updates without file uploads:

```javascript
const data = {
  name: "New Name",
  description: "New description",
  category: "Updated"
};

const response = await fetch('/api/community/groups/2/', {
  method: 'PATCH',  // Try PATCH first, then PUT
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(data)
});
```

### Option 3: Two-Step Update

Step 1 - Update text fields with PATCH/JSON:
```javascript
await fetch('/api/community/groups/2/', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name, description })
});
```

Step 2 - Upload images separately with POST:
```javascript
const formData = new FormData();
formData.append('banner', bannerFile);
formData.append('profile_picture', profileFile);

await fetch('/api/community/groups/2/upload/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

**Test these workarounds immediately in production to confirm they work.**

## LiteSpeed Server Configuration (If Workaround Fails)

If workarounds don't work, the server admin must fix LiteSpeed:

### Via SSH to Server:

1. Connect to server:
```bash
ssh user@thenewafricagroup.com
```

2. Edit LiteSpeed config:
```bash
sudo nano /usr/local/lsws/conf/httpd_config.conf
```

3. Find the /api/ context and add/verify these settings:
```
context /api/ {
  location                /home/user/project/
  allowedMethods          GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
  enableExpires           0
  staticEnabled           0
  scriptHandler           WSGI
}
```

4. Or increase global HTTP methods:
```
httpServer {
  allowedMethods          GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE
}
```

5. Increase upload size limits if needed:
```
httpServer {
  maxBodySize             10M
  maxRequestBodySize      10M
}
```

6. Restart LiteSpeed:
```bash
sudo systemctl restart lsws
# Or:
sudo /usr/local/lsws/bin/lswsctrl restart
```

### Via LiteSpeed Web Console:

1. Go to: https://superadmin.thenewafricagroup.com:7080/
2. Navigate to: Server > General
3. Find "Allowed HTTP Methods"
4. Add: PUT, PATCH, DELETE
5. Click "Apply" and "Graceful Restart"

## Testing Commands

### Test PATCH (Should work after workaround):
```bash
curl -X PATCH https://thenewafricagroup.com/api/community/groups/2/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

### Test PATCH with Multipart:
```bash
curl -X PATCH https://thenewafricagroup.com/api/community/groups/2/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Updated Name" \
  -F "banner=@image.jpg"
```

### Test PUT (May still fail):
```bash
curl -X PUT https://thenewafricagroup.com/api/community/groups/2/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Updated Name"
```

## Action Items

**Do First (Workaround):**
- [ ] Update frontend to use PATCH instead of PUT
- [ ] Test PATCH with JSON from production
- [ ] If working, deploy to production
- [ ] Test group updates from frontend

**Do If Workaround Doesn't Work:**
- [ ] SSH to production server
- [ ] Check LiteSpeed configuration file
- [ ] Verify /api/ context allows PUT/PATCH/DELETE
- [ ] Add missing methods if needed
- [ ] Increase body size limits if needed
- [ ] Restart LiteSpeed service
- [ ] Test with curl commands
- [ ] Verify from frontend

## Related Info

**Why 501 errors occur:**
- Server explicitly rejects HTTP method (PUT/PATCH/DELETE)
- Reverse proxy doesn't pass method to backend
- WSGI/FastCGI not configured for dynamic methods
- Static file handler catching dynamic routes

**Why localhost works:**
- Django runserver allows all HTTP methods by default
- No LiteSpeed server involved
- No reverse proxy restrictions

**Why PATCH is safer than PUT:**
- PATCH is less commonly restricted by legacy servers
- Some security policies block PUT/DELETE but allow PATCH
- Better for partial updates anyway

## Status

🟡 **PARTIALLY BLOCKED - Workaround Available**
- ✅ Django endpoints: fully implemented and tested
- ❌ Production server: blocking PUT (need workaround or config fix)
- 🟡 Workaround: use PATCH instead of PUT
- 📋 Long-term: configure LiteSpeed or switch web server

Next: **Try PATCH workaround immediately in production.**
