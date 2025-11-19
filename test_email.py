#!/usr/bin/env python
"""Test email sending via Mailjet"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from utils.mailjet_service import send_email
from utils.email_templates import welcome_email_template

test_email = 'otialid040@gmail.com'
user_name = 'Test User'
activation_url = 'https://thenewafricagroup.com/verify/test'

print('='*70)
print('MAILJET EMAIL TEST')
print('='*70)
print(f'Sending test email to: {test_email}')
print()

html_content = welcome_email_template(user_name, activation_url)

print('Attempting to send email...')
success = send_email(
    to_email=test_email,
    to_name=user_name,
    subject='Welcome to The New Africa Group - Test Email',
    html_content=html_content,
    text_content=f'Welcome {user_name}! Verify your account at: {activation_url}'
)

print()
if success:
    print('✓ EMAIL SENT SUCCESSFULLY!')
    print(f'  Recipient: {test_email}')
    print(f'  Subject: Welcome to The New Africa Group - Test Email')
else:
    print('✗ EMAIL FAILED TO SEND')
    print('  Check Mailjet API credentials in settings.py')

print('='*70)
