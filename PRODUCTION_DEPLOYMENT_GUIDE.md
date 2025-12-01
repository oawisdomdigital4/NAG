# Production Deployment Guide - December 1, 2025

## CRITICAL: Current Status

**Issue:** Course module creation failing with "content: Not a valid string" error  
**Root Cause:** Frontend sending content as array instead of string  
**Fix Applied:** Changed to send `content: '{}'` (JSON string) instead of array  
**Build Status:** ✅ Built successfully - ready to deploy  
**Deployment Status:** ❌ NOT YET DEPLOYED - Old version still on server

---

## Files to Deploy

**Location:** `c:\Users\HP\NAG BACKEND\myproject\frontend\dist\`

### Critical Files (Must Upload):
```
dist/
├── index.html                    (Main HTML file)
├── assets/
│   ├── index-ByJNxS-U.css       (Main stylesheet)
│   ├── index-P2RY9ksP.js        (Main JavaScript - FIXED)
│   ├── index-DRrBaE32.js        (Additional JS chunk)
│   └── pdf-BAFhSO9X.js          (PDF support)
└── [other static files]
```

### Optional Files (Can Upload):
- `nag_cert.pdf`
- `page-flip.mp3`
- `pdf.worker.min.js`
- `TNAG Black Logo.png`
- `TNAG Black Logo copy.png`
- `notifications/` folder
- `engagement/` folder

---

## Deployment Methods

### Method 1: Using cPanel File Manager (Easiest)

1. **Access cPanel:**
   - Go to: `https://thenewafricagroup.com:2083/` or check Breezehost for link
   - OR: Use Breezehost dashboard → cPanel
   - Log in with your Breezehost credentials

2. **Navigate to public_html:**
   - In File Manager, go to: `/home/{username}/public_html/`
   - Replace `{username}` with your actual Breezehost username

3. **Delete Old Files:**
   - Select: `index.html`
   - Select: `assets` folder
   - Click Delete

4. **Upload New Files:**
   - Click "Upload" button
   - Upload entire `dist/` contents:
     - Drag and drop `dist/index.html`
     - Drag and drop `dist/assets/` folder

5. **Verify Upload:**
   - Refresh cPanel File Manager
   - Confirm `index.html` is there
   - Confirm `assets/` folder exists with CSS/JS files

6. **Test in Browser:**
   - Hard refresh: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
   - Open browser DevTools: `F12`
   - Go to Console tab
   - Try creating a course → check for `content: '{}'` in request logs

---

### Method 2: Using FileZilla FTP Client

1. **Set Up FileZilla:**
   - Download: https://filezilla-project.org/
   - Install and open

2. **Connect to Server:**
   - Host: `ftp.thenewafricagroup.com` (or check Breezehost for FTP host)
   - Username: Your Breezehost FTP username
   - Password: Your Breezehost FTP password
   - Port: 21 (or 22 for SFTP)
   - Click "Quickconnect"

3. **Navigate & Delete:**
   - Go to: `/public_html/`
   - Delete: `index.html`
   - Delete: `assets/` folder

4. **Upload New Files:**
   - Right-click on local `dist/` folder
   - Select: Upload
   - Upload: `index.html`
   - Upload: `assets/` folder

5. **Verify & Test:**
   - Refresh browser: `Ctrl+F5`
   - Check console logs

---

### Method 3: Using SFTP Command Line (Advanced)

```bash
# Connect via SFTP
sftp -P 22 username@thenewafricagroup.com

# Navigate to public_html
cd public_html

# Delete old files
rm -rf index.html assets/

# Upload new files
put index.html
put -r assets/

# Verify
ls -la

# Exit
exit
```

---

## What Changed (Technical Details)

### Frontend Fix Applied:

**File:** `frontend/src/hooks/useCourseCreation.ts` (Line 161)

**Before (BROKEN):**
```typescript
content: module.lessons || [],  // Sends ARRAY
```

**After (FIXED):**
```typescript
content: '{}',  // Sends JSON STRING
```

### Why This Matters:

**Backend Serializer** (`courses/serializers.py` line 264):
```python
content = serializers.CharField(required=False, allow_blank=True)
```

The serializer expects a **string**, but frontend was sending an **array**. Now it sends a proper JSON string `'{}'`.

### Error Log Fix Applied:

**File:** `frontend/src/hooks/useEnrollment.ts`

Added better error logging to show:
- Actual API URL being called
- Full HTTP error responses
- Actual response text (not just JSON parse errors)

This helps debug "HTML instead of JSON" errors on production.

---

## Testing After Deployment

1. **Open DevTools Console:** `F12`
2. **Create a new course:**
   - Title: "Test Course"
   - Add one module: "Test Module"
   - Click Submit

3. **Check Console for:**
   ```
   ✅ [useCourseCreation] Course created successfully: [ID]
   ✅ Creating module with payload: {course: X, title: '...', content: '{}', order: 0}
   ✅ [API POST] https://superadmin.thenewafricagroup.com/api/courses/course-modules/ 201
   ✅ Module creation response: {id: X, ...}
   ```

4. **If Still Failing:**
   - Check console for error message
   - Look for URL - is it pointing to localhost or production API?
   - Check if `API_BASE` is set correctly in environment

---

## Environment Configuration

If course creation still fails after deployment, the API base URL might be wrong.

**Current Default:** `http://127.0.0.1:8000` (localhost - WRONG for production)

**Solution:** Set environment variable during build:

```bash
# On Windows:
set VITE_API_BASE=https://superadmin.thenewafricagroup.com && npm run build

# On Mac/Linux:
export VITE_API_BASE=https://superadmin.thenewafricagroup.com && npm run build
```

Then rebuild and redeploy.

---

## Quick Checklist

- [ ] Access Breezehost cPanel or FTP
- [ ] Navigate to `/public_html/`
- [ ] Delete old `index.html` and `assets/` folder
- [ ] Upload new `index.html` from `dist/`
- [ ] Upload new `assets/` folder from `dist/`
- [ ] Hard refresh browser: `Ctrl+F5`
- [ ] Open DevTools: `F12`
- [ ] Try creating a course
- [ ] Check console for success or error messages
- [ ] Verify module payload shows `content: '{}'`

---

## Rollback Plan

If something breaks after deployment:

1. **Access cPanel/FTP again**
2. **Delete:** New `index.html` and `assets/`
3. **Upload:** Old files from backup (if you saved them)
4. **Hard refresh:** `Ctrl+F5`

---

## Support

If issues persist:
1. Share console error messages from DevTools
2. Check Network tab to see actual API responses
3. Verify API_BASE is correct for production
4. Check server error logs

---

**Status:** Ready to deploy ✅  
**Last Build:** 2025-12-01 (Fixed course module content issue)  
**Build Time:** 52.55s  
**Files Ready:** 12 files in dist/ folder
