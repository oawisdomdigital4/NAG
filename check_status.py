#!/usr/bin/env python3
"""
QUICK TROUBLESHOOTING SCRIPT - Run this to check frontend/backend status
"""

import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.conf import settings

print("\n" + "="*80)
print("THUMBNAIL UPLOAD - STATUS CHECK")
print("="*80 + "\n")

# Check 1: MEDIA folder configuration
print("1. MEDIA CONFIGURATION")
print("-" * 40)
media_root = settings.MEDIA_ROOT
media_url = settings.MEDIA_URL
print(f"✓ MEDIA_ROOT: {media_root}")
print(f"✓ MEDIA_URL: {media_url}")

course_thumb_dir = Path(media_root) / "course_thumbnails"
if course_thumb_dir.exists():
    files = list(course_thumb_dir.glob("*"))
    print(f"✓ course_thumbnails/ directory exists")
    print(f"  Files in directory: {len(files)}")
    if files:
        recent = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        print(f"  Most recent: {recent.name}")
else:
    print(f"✗ course_thumbnails/ directory NOT found")

# Check 2: Models
print("\n2. DATABASE MODELS")
print("-" * 40)
from courses.models import Course
latest_course = Course.objects.order_by('-id').first()
if latest_course:
    has_thumb_field = hasattr(latest_course, 'thumbnail')
    has_preview_field = hasattr(latest_course, 'preview_video')
    print(f"✓ Course model has 'thumbnail' field: {has_thumb_field}")
    print(f"✓ Course model has 'preview_video' field: {has_preview_field}")
    
    # Check latest course
    print(f"\n  Latest Course:")
    print(f"    ID: {latest_course.id}")
    print(f"    Title: {latest_course.title}")
    print(f"    Thumbnail: {latest_course.thumbnail}")
    if latest_course.thumbnail:
        print(f"    ✓ HAS FILE SAVED IN DATABASE")
    else:
        print(f"    ✗ No thumbnail file")
else:
    print("✗ No courses in database yet")

# Check 3: Serializer
print("\n3. SERIALIZER CONFIGURATION")
print("-" * 40)
from courses.serializers import CourseSerializer
serializer = CourseSerializer()
fields = serializer.fields
print(f"✓ CourseSerializer has 'thumbnail_url' field: {'thumbnail_url' in fields}")
print(f"✓ CourseSerializer has 'thumbnail' field: {'thumbnail' in fields}")
print(f"✓ CourseSerializer has 'preview_video_url' field: {'preview_video_url' in fields}")

# Check 4: ViewSet Parser
print("\n4. VIEWSET PARSER CONFIGURATION")
print("-" * 40)
from courses.views import CourseViewSet
viewset = CourseViewSet()
parsers = viewset.get_parsers()
parser_names = [p.__class__.__name__ for p in parsers]
print(f"✓ Available parsers: {', '.join(parser_names)}")
has_multipart = 'MultiPartParser' in parser_names
has_form = 'FormParser' in parser_names
print(f"✓ MultiPartParser configured: {has_multipart}")
print(f"✓ FormParser configured: {has_form}")

# Check 5: Frontend build
print("\n5. FRONTEND BUILD")
print("-" * 40)
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    index_html = frontend_dist / "index.html"
    index_js = list((frontend_dist / "assets").glob("index-*.js")) if (frontend_dist / "assets").exists() else []
    print(f"✓ Frontend dist folder exists")
    print(f"✓ index.html exists: {index_html.exists()}")
    print(f"✓ JavaScript bundle exists: {len(index_js) > 0}")
else:
    print(f"✗ Frontend dist folder NOT found - need to run: npm run build")

# Check 6: Migration status
print("\n6. DATABASE MIGRATIONS")
print("-" * 40)
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
if plan:
    print(f"⚠ {len(plan)} migrations pending")
else:
    print(f"✓ All migrations applied")

# Summary
print("\n" + "="*80)
print("CHECKLIST BEFORE TESTING")
print("="*80 + "\n")

checks = [
    ("MEDIA_ROOT configured", settings.MEDIA_ROOT),
    ("course_thumbnails directory", course_thumb_dir.exists()),
    ("Course model has thumbnail field", has_thumb_field),
    ("Serializer has thumbnail_url", 'thumbnail_url' in fields),
    ("MultiPartParser enabled", has_multipart),
    ("FormParser enabled", has_form),
    ("Frontend built", frontend_dist.exists()),
    ("All migrations applied", not plan),
]

all_good = True
for check, status in checks:
    if isinstance(status, bool):
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check}")
        if not status:
            all_good = False
    else:
        print(f"✓ {check}")

print("\n" + "="*80)
if all_good:
    print("✓✓✓ EVERYTHING CONFIGURED - READY TO TEST ✓✓✓")
else:
    print("⚠ Some items need attention - check above")
print("="*80 + "\n")

print("TO TEST:")
print("1. Login to frontend")
print("2. Create a course")
print("3. Go to Media step")
print("4. SELECT A THUMBNAIL IMAGE")
print("5. Click Publish")
print("6. Check console logs (F12)")
print("\n")
