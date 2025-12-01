#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from accounts.models import User, UserProfile
from courses.models import Course

# Get the course
course = Course.objects.filter(slug='sfg').first()
if not course:
    print("Course not found")
    exit()

# Get an active user
user = User.objects.filter(is_active=True).first()
if not user:
    print("No active user found")
    exit()

# Check user profile and balance
try:
    profile = user.profile
    print(f'User: {user.username}')
    print(f'Earning Balance: {profile.earning_balance}')
    print(f'Pending Balance: {profile.pending_balance}')
    print(f'Available Balance: {profile.available_balance}')
    print(f'Course price: {course.price}')
    print(f'Can afford: {profile.available_balance >= float(course.price)}')
except UserProfile.DoesNotExist:
    print(f"User {user.username} has no profile")
