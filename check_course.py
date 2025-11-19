#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import Course

c = Course.objects.filter(slug='sfg').first()
if c:
    print(f'Course: {c.title}')
    print(f'Published: {c.is_published}')
    print(f'Price: {c.price}')
    print(f'Facilitator: {c.facilitator.username}')
    print(f'Facilitator active: {c.facilitator.is_active}')
else:
    print('Course not found')
