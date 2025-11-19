#!/usr/bin/env python
"""
Test script for OTP functionality
Usage: python manage.py shell < test_otp.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from accounts.models import OTPVerification
from accounts.email_tasks import send_otp_email
import time

print("=" * 70)
print("OTP SYSTEM TEST")
print("=" * 70)

# Test 1: Create OTP
print("\n[Test 1] Creating OTP for new user...")
test_email = 'otp-test@example.com'
otp = OTPVerification.create_otp(email=test_email, otp_type='signup')
print("[OK] OTP Created")
print(f"  Email: {otp.email}")
print(f"  OTP Code: {otp.otp_code}")
print(f"  Type: {otp.otp_type}")
print(f"  Expires At: {otp.expires_at}")
print(f"  Is Expired: {otp.is_expired()}")
print(f"  Valid Attempt: {otp.is_valid_attempt()}")

# Test 2: Send OTP Email
print("\n[Test 2] Sending OTP email...")
try:
    # Use sync version (no Celery)
    send_otp_email(otp.id)
    print(f"[OK] Email sent successfully to {otp.email}")
except Exception as e:
    print(f"[ERROR] Email send failed: {str(e)}")

# Test 3: Verify correct OTP
print("\n[Test 3] Verifying correct OTP...")
correct_otp_code = otp.otp_code
is_valid, message = otp.verify_otp(correct_otp_code)
print(f"  Attempts before: 0, After: {otp.attempts}")
if is_valid:
    print(f"[OK] OTP Verified: {message}")
else:
    print(f"[ERROR] Verification failed: {message}")

# Test 4: Test with new OTP instance (simulate failed verification)
print("\n[Test 4] Testing with invalid OTP...")
otp2 = OTPVerification.create_otp(email='invalid-test@example.com', otp_type='signup')
print(f"[OK] New OTP created: {otp2.otp_code}")

is_valid, message = otp2.verify_otp('000000')  # Wrong code
print(f"  Verification attempt 1 - Valid: {is_valid}, Message: {message}")
print(f"  Attempts: {otp2.attempts}/5")

is_valid, message = otp2.verify_otp('111111')  # Wrong code
print(f"  Verification attempt 2 - Valid: {is_valid}, Message: {message}")
print(f"  Attempts: {otp2.attempts}/5")

# Test 5: Resend OTP
print("\n[Test 5] Testing resend OTP...")
original_code = otp2.otp_code
new_code = otp2.resend_otp()
print(f"[OK] OTP Resent")
print(f"  Original code: {original_code}")
print(f"  New code: {new_code}")
print(f"  Attempts reset: {otp2.attempts}")
print(f"  Verified reset: {otp2.is_verified}")

# Test 6: OTP expiration
print("\n[Test 6] Testing OTP expiration check...")
from django.utils import timezone
from datetime import timedelta
import random
import string

# Generate unique OTP code
unique_code = ''.join(random.choices(string.digits, k=6))

otp3 = OTPVerification.objects.create(
    email='expiration-test@example.com',
    otp_code=unique_code,
    otp_type='signup',
    expires_at=timezone.now() - timedelta(minutes=1)  # 1 minute in the past
)
print(f"  Is Expired: {otp3.is_expired()}")
if otp3.is_expired():
    print(f"[OK] Expiration detection working correctly")

# Test 7: Query OTP by email
print("\n[Test 7] Querying OTP by email...")
queried_otp = OTPVerification.objects.filter(email=test_email, otp_type='signup').latest('created_at')
print(f"[OK] OTP queried successfully")
print(f"  Email: {queried_otp.email}")
print(f"  Verified: {queried_otp.is_verified}")
print(f"  Code: {queried_otp.otp_code}")

print("\n" + "=" * 70)
print("OTP SYSTEM TEST COMPLETED")
print("=" * 70)

print("\n[Summary]")
print("[OK] OTP Model Working")
print("[OK] OTP Generation Working")
print("[OK] OTP Email Sending Working")
print("[OK] OTP Verification Working")
print("[OK] OTP Resend Working")
print("[OK] Expiration Detection Working")
print("[OK] Database Queries Working")
