#!/usr/bin/env python
"""Check what fields are actually being returned by the API"""
import os
import sys
import django

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import requests
import json

print("=" * 80)
print("CHECK API RESPONSE FIELDS FOR THUMBNAIL")
print("=" * 80)

# Get a course with a thumbnail
response = requests.get('http://127.0.0.1:8000/api/courses/api-test-thumb-413d8e/')
print(f"\nResponse Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    
    # Show all thumbnail-related fields
    print("Thumbnail-related fields in response:")
    print("-" * 80)
    for key in sorted(data.keys()):
        if 'thumbnail' in key.lower() or 'preview' in key.lower():
            value = data[key]
            if isinstance(value, str):
                print(f"{key:30} = {value[:80]}")
            else:
                print(f"{key:30} = {value}")
    
    print("\n" + "=" * 80)
    print("FIELD MAPPING:")
    print("=" * 80)
    print(f"thumbnail:             {data.get('thumbnail')}")
    print(f"thumbnail_url:         {data.get('thumbnail_url')}")
    print(f"thumbnail_url_display: {data.get('thumbnail_url_display')}")
    
    # Check which one has a value
    print(f"\n" + "=" * 80)
    print("WHICH FIELD HAS THE IMAGE URL?")
    print("=" * 80)
    
    if data.get('thumbnail'):
        print(f"[+] thumbnail has value: {data.get('thumbnail')[:60]}...")
    else:
        print(f"[-] thumbnail is empty/null")
        
    if data.get('thumbnail_url'):
        print(f"[+] thumbnail_url has value: {data.get('thumbnail_url')[:60]}...")
    else:
        print(f"[-] thumbnail_url is empty")
        
    if data.get('thumbnail_url_display'):
        print(f"[+] thumbnail_url_display has value: {data.get('thumbnail_url_display')[:60]}...")
    else:
        print(f"[-] thumbnail_url_display is empty")

print("\n" + "=" * 80)
