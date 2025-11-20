# PythonAnywhere Production Deployment - Complete Fix Guide

## Current Issues on Production

```
❌ CORS blocked on multiple endpoints
❌ 500 errors returning HTML instead of JSON
❌ Endpoints affected:
   - /api/promotions/analytics/facilitator/
   - /api/courses/my_students/
   - /api/courses/mine/
   - /api/promotions/sponsor-campaigns/
   - /api/utils/about-hero/
   - /api/summit/partner-section/
   - /api/summit/partners/
   - /api/utils/footer/
   - /api/auth/otp/send_otp/
```

## Root Cause

The backend is returning **500 Internal Server Error** with HTML error pages, which:
1. Blocks CORS headers from being added
2. Causes browsers to reject requests with CORS policy errors
3. Returns invalid JSON (HTML doctype)

## Quick Fix (5 Steps)

### Step 1: SSH into PythonAnywhere

```bash
ssh mrokaimoses@ssh.pythonanywhere.com
cd ~/myproject
```

### Step 2: Apply All Database Migrations

```bash
python manage.py migrate
```

**Expected output:**
```
Running migrations:
  Applying accounts.0007_otpverification... OK
  Applying utils.0006_footercontent... OK
  Applying utils.0007_abouthero... OK
  Applying summit.0001_initial... OK
  ... (more migrations)
```

If you see errors, note them and proceed to Step 3.

### Step 3: Verify Django System Health

```bash
python manage.py check --deploy
```

**Should show:**
```
System check identified no issues (0 silenced).
```

If it shows errors, fix them before proceeding.

### Step 4: Test Endpoints Locally on Server

```bash
python manage.py shell
>>> from rest_framework.test import APIRequestFactory
>>> from courses.views import MyCoursesViewSet
>>> print("✓ Courses import OK")
>>> from promotions.views import AnalyticsViewSet  
>>> print("✓ Promotions import OK")
>>> from accounts.otp_views import OTPViewSet
>>> print("✓ OTP import OK")
>>> exit()
```

### Step 5: Reload Web App in PythonAnywhere

1. Go to: https://www.pythonanywhere.com/user/mrokaimoses/webapps/
2. Find your web app (should be `superadmin.thenewafricagroup.com`)
3. Click the **"Reload"** button
4. Wait for status to change from "Reloading..." to "running" (usually 10-30 seconds)

---

## Detailed Troubleshooting

### Issue: Migrations Show Errors

If `python manage.py migrate` fails:

```bash
# Check which migrations have issues
python manage.py showmigrations

# Try migrating specific app
python manage.py migrate accounts
python manage.py migrate courses
python manage.py migrate promotions
python manage.py migrate utils
python manage.py migrate summit

# If still failing, check the database
python manage.py dbshell
SELECT * FROM django_migrations WHERE app = 'accounts' ORDER BY name DESC;
exit
```

### Issue: Still Getting 500 Errors After Reload

Check Django error logs:

```bash
# View recent error log
tail -100 /var/log/django.log

# Or view PythonAnywhere error log via web dashboard:
# Go to Web app → Error log
```

Look for error patterns like:
- `ImportError: No module named...` - Missing dependency
- `IntegrityError` - Database constraint issue
- `OperationalError: no such table` - Migration not applied
- `AttributeError` - Code error in views/models

### Issue: CORS Headers Still Missing

After fixing 500 errors, verify CORS is working:

```bash
# Test from production server
curl -i -X OPTIONS https://superadmin.thenewafricagroup.com/api/courses/mine/ \
  -H "Origin: https://thenewafricagroup.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type"
```

Should show headers like:
```
Access-Control-Allow-Origin: https://thenewafricagroup.com
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
```

If not present, check `/etc/pythonanywhere/wsgi.py` to ensure CORS middleware is configured.

---

## Full Database Migration Verification

Run this complete check:

```bash
python manage.py shell <<EOF
import django
from django.conf import settings
from django.core.management import call_command
from django.db import connection

print("=" * 60)
print("DATABASE MIGRATION VERIFICATION")
print("=" * 60)

# Check database connection
print(f"\n✓ Database: {settings.DATABASES['default']['NAME']}")
print(f"✓ Host: {settings.DATABASES['default']['HOST']}")

# Show all tables
with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print(f"\n✓ Tables in database: {len(tables)}")
    print("  Required tables:")
    required = [
        'accounts_otpverification',
        'courses_course',
        'promotions_analytics',
        'utils_footercontent',
        'utils_abouthero',
        'summit_summithero',
    ]
    for table in required:
        exists = any(table in str(t) for t in tables)
        status = "✓" if exists else "✗"
        print(f"    {status} {table}")

# Check migrations
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, ignore_no_migrations=True)
print(f"\n✓ Loaded migrations: {len(loader.disk_migrations)}")
print("  Apps with migrations:")
for app, migration_list in loader.disk_migrations.items():
    print(f"    • {app}: {len(migration_list)} migrations")

exit(0)
EOF
```

---

## Common Errors and Fixes

| Error | Solution |
|-------|----------|
| `OperationalError: no such table` | Run `python manage.py migrate` |
| `ImportError: No module named...` | Install: `pip install -r requirements.txt` |
| `SyntaxError in views.py` | Check Python syntax: `python -m py_compile accounts/views.py` |
| `CORS errors still appearing` | Reload web app again + clear browser cache |
| `500 error with <!doctype` | Check error log: `tail -50 /var/log/django.log` |

---

## Testing Each Endpoint After Fix

Once deployment is complete, test each endpoint:

```bash
# Test OTP endpoint
curl -X POST https://superadmin.thenewafricagroup.com/api/auth/otp/send_otp/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
# Should return: {"message": "OTP sent successfully", "otp_id": 1}

# Test courses endpoint (requires auth)
curl -X GET https://superadmin.thenewafricagroup.com/api/courses/mine/ \
  -H "Authorization: Bearer YOUR_TOKEN"
# Should return: [{id, title, description, ...}]

# Test promotions analytics (requires auth)
curl -X GET "https://superadmin.thenewafricagroup.com/api/promotions/analytics/facilitator/?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
# Should return: {analytics data}

# Test footer (public endpoint)
curl -X GET https://superadmin.thenewafricagroup.com/api/utils/footer/
# Should return: {} or {id, content, ...}
```

All should return **JSON** (not HTML) with proper CORS headers.

---

## Prevention: Proper Deployment Process

For future deployments, follow this process:

```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Run system checks
python manage.py check --deploy

# 6. Reload web app (in PythonAnywhere dashboard)
# Click "Reload" button

# 7. Test endpoints
curl -i https://superadmin.thenewafricagroup.com/api/health/
```

---

## Files That Need to Be on Production

Verify these files exist on production server:

```bash
# Check app files
ls -la ~/myproject/accounts/otp_views.py
ls -la ~/myproject/promotions/views.py
ls -la ~/myproject/courses/views.py
ls -la ~/myproject/utils/views.py
ls -la ~/myproject/summit/views.py

# Check migrations
ls -la ~/myproject/accounts/migrations/0007_otpverification.py
ls -la ~/myproject/utils/migrations/0006_footercontent.py
ls -la ~/myproject/utils/migrations/0007_abouthero.py
ls -la ~/myproject/summit/migrations/0001_initial.py

# Check settings
ls -la ~/myproject/myproject/settings.py
```

If any are missing, upload/sync them first.

---

## After Fix Verification

Once deployed, the frontend should:

✅ Not show CORS errors in console  
✅ Load promotions analytics without errors  
✅ Load courses (my_students, mine endpoints)  
✅ Load footer and about-hero sections  
✅ Load OTP endpoints  
✅ Load summit endpoints  
✅ All API responses should be valid JSON  

---

## Emergency Rollback

If something goes wrong after reload:

```bash
# Check app status
python manage.py check

# Rollback code to previous commit
git reset --hard HEAD~1

# Reload web app again
# (Click Reload button in PythonAnywhere dashboard)
```

---

**Last Updated:** November 19, 2025  
**Status:** Production Debugging Guide  
**Priority:** HIGH - All API endpoints failing  
**Expected Fix Time:** 5-10 minutes
