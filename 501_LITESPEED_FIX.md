# 501 Not Implemented Error on PUT /api/community/groups/2/

## Issue Summary
Frontend PUT request to update a group returns **501 Not Implemented** on production (thenewafricagroup.com) but works on local development.

## Request Details
- **URL:** https://thenewafricagroup.com/api/community/groups/2/
- **Method:** PUT
- **Status Code:** 501 Not Implemented
- **Server:** LiteSpeed
- **Content-Type:** multipart/form-data (file upload)
- **Auth:** Bearer token (valid)

## Root Cause Analysis

The 501 error is coming from the **LiteSpeed web server**, not Django. The response headers show:
```
server: LiteSpeed
content-type: text/html (not JSON)
```

This indicates LiteSpeed is intercepting the request before it reaches the Django application.

### Possible Causes:

1. **LiteSpeed HTTP Method Not Allowed**
   - LiteSpeed may not be configured to pass PUT requests to the Django backend
   - Default LiteSpeed security settings may block PUT/DELETE methods

2. **Reverse Proxy Configuration**
   - If Nginx/Apache is between LiteSpeed and the client, it may be blocking PUT
   - Proxy headers might not be properly configured

3. **Static File Matching**
   - LiteSpeed may be treating `/api/` paths as static files
   - Context configuration in LiteSpeed may be incorrect

## Django Code Status

✅ **All Django REST Framework methods are implemented:**
- `GET /api/community/groups/` - List (works)
- `POST /api/community/groups/` - Create (implemented)
- `GET /api/community/groups/2/` - Retrieve (implemented)
- `PUT /api/community/groups/2/` - Update (implemented with permission checks)
- `PATCH /api/community/groups/2/` - Partial Update (implemented)
- `DELETE /api/community/groups/2/` - Destroy (implemented with permission checks)

## Solution

### For LiteSpeed Configuration:

1. **Enable HTTP Methods for Dynamic Context**
   ```
   Edit /usr/local/lsws/conf/httpd_config.conf
   
   Or via LiteSpeed Web Console:
   - Navigate to: Console > Server > General
   - Find: "Allowed HTTP Methods"
   - Ensure PUT and DELETE are checked
   - Or set: PUT,DELETE,POST,GET,HEAD,OPTIONS,TRACE
   ```

2. **Configure Context for API Routes**
   ```
   Navigate to: Server > Context
   
   Add context for /api/:
   - URI: /api/
   - Location: /home/user/project/
   - Allowable Methods: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
   - Enable Expires: No
   - Static Enabled: No (important!)
   ```

3. **Verify Proxy Headers**
   ```
   If using a reverse proxy, ensure these headers are passed:
   - X-Forwarded-For
   - X-Forwarded-Proto
   - X-Real-IP
   ```

4. **Restart LiteSpeed**
   ```bash
   systemctl restart lsws
   # or
   /usr/local/lsws/bin/lswsctrl restart
   ```

### Alternative: Use JSON Instead of Multipart

If LiteSpeed has strict security on multipart uploads, try:
```javascript
// Instead of FormData
const data = {
  name: "New Name",
  description: "New description",
  category: "Updated",
};

fetch('/api/community/groups/2/', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer token...'
  },
  body: JSON.stringify(data)
});
```

Note: Profile picture and banner would need to be uploaded separately or via POST to a dedicated upload endpoint.

## Testing

### Local Development (Should Work)
```bash
python manage.py runserver

curl -X PUT http://localhost:8000/api/community/groups/2/ \
  -H "Authorization: Bearer token" \
  -F "name=Updated Name"
```

### Production (Should Be Tested After Fix)
```bash
curl -X PUT https://thenewafricagroup.com/api/community/groups/2/ \
  -H "Authorization: Bearer token" \
  -F "name=Updated Name"
```

## Related Issues

- Status 501 errors often indicate server-side HTTP method restrictions
- Can also occur if:
  - FastCGI/WSGI is not properly configured
  - API routing is incorrect
  - HTTP method is not in server's allowed list

## Action Items

- [ ] SSH to production server
- [ ] Check LiteSpeed configuration
- [ ] Enable PUT/PATCH/DELETE methods for /api/ context
- [ ] Restart LiteSpeed service
- [ ] Test with curl
- [ ] Verify from frontend
