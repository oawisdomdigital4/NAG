#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from accounts.models import User
from courses.models import Course, Enrollment

# Get the course and user
course = Course.objects.filter(slug='sfg').first()
user = User.objects.filter(username='wisdom').first()

if course and user:
    enrolled = Enrollment.objects.filter(user=user, course=course).exists()
    print(f'User: {user.username}')
    print(f'Course: {course.title}')
    print(f'Already enrolled: {enrolled}')
    
    # List all enrollments for this user
    enrollments = Enrollment.objects.filter(user=user).count()
    print(f'Total enrollments: {enrollments}')
else:
    print('Course or User not found')
