#!/usr/bin/env python
"""
Test script to send an email via Mailjet
Usage: python manage.py shell < test_mailjet_email.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, '/Users/HP/NAG BACKEND/myproject')
django.setup()

from utils.mailjet_service import send_email
from utils.email_templates import welcome_email_template

# Test email configuration
test_email = 'otialid040@gmail.com'
user_name = 'Test User'
activation_url = 'https://thenewafricagroup.com/verify/test'

print("=" * 70)
print("MAILJET EMAIL TEST")
print("=" * 70)
print(f"Sending email to: {test_email}")
print(f"User name: {user_name}")
print()

# Generate email template
html_content = welcome_email_template(user_name, activation_url)

print("Sending email...")
success = send_email(
    to_email=test_email,
    to_name=user_name,
    subject='Welcome to The New Africa Group - Test Email',
    html_content=html_content,
    text_content=f'Welcome {user_name}! Verify your account at: {activation_url}'
)

print()
if success:
    print("✓ EMAIL SENT SUCCESSFULLY!")
    print(f"  To: {test_email}")
    print(f"  Subject: Welcome to The New Africa Group - Test Email")
else:
    print("✗ EMAIL FAILED TO SEND")
    print("  Check Mailjet API credentials in settings.py")
    print("  Ensure MAILJET_API_KEY and MAILJET_SECRET_KEY are set correctly")

print("=" * 70)
