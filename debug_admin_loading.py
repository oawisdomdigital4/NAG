#!/usr/bin/env python
"""
Debug admin loading to see what's happening with the legacy admin.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib import admin
from community.models import Group, GroupMembership, GroupInvite

print("\n" + "="*80)
print("ADMIN REGISTRATION DEBUG")
print("="*80)

registry = admin.site._registry

print("\nCurrently Registered Models:")
for model in registry.keys():
    print(f"  - {model.__name__}")

print("\n" + "="*80)
