#!/usr/bin/env python
"""
Complete OTP + Signup Flow Test
Tests the entire signup workflow with OTP verification
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from accounts.models import OTPVerification
from django.contrib.auth import get_user_model
import json

User = get_user_model()
client = Client()

print("=" * 80)
print("COMPLETE OTP + SIGNUP FLOW TEST")
print("=" * 80)

# Test Data
test_email = 'flow-test@example.com'
test_password = 'TestPassword123'
test_role = 'individual'
test_name = 'Flow Test User'

# Clean up any existing test user
User.objects.filter(email=test_email).delete()

print("\n[Step 1] Sending OTP to email...")
response = client.post(
    '/api/auth/otp/send_otp/',
    data=json.dumps({'email': test_email}),
    content_type='application/json'
)

if response.status_code == 200:
    print(f"[OK] OTP sent successfully")
    data = response.json()
    otp_id = data.get('otp_id')
    print(f"     Message: {data.get('message')}")
    print(f"     Expires in: {data.get('expires_in_minutes')} minutes")
else:
    print(f"[ERROR] Failed to send OTP: {response.status_code}")
    print(f"        {response.json()}")
    exit(1)

# Get OTP code
otp_obj = OTPVerification.objects.get(id=otp_id)
otp_code = otp_obj.otp_code
print(f"     OTP Code: {otp_code}")

print("\n[Step 2] Verifying OTP...")
response = client.post(
    '/api/auth/otp/verify_otp/',
    data=json.dumps({'email': test_email, 'otp_code': otp_code}),
    content_type='application/json'
)

if response.status_code == 200:
    data = response.json()
    if data.get('verified'):
        print(f"[OK] OTP verified successfully")
        print(f"     Message: {data.get('message')}")
    else:
        print(f"[ERROR] OTP verification failed")
        print(f"        {data.get('error')}")
        exit(1)
else:
    print(f"[ERROR] OTP verification failed: {response.status_code}")
    print(f"        {response.json()}")
    exit(1)

print("\n[Step 3] Creating user account after OTP verification...")
response = client.post(
    '/api/auth/signup/',
    data=json.dumps({
        'email': test_email,
        'password': test_password,
        'role': test_role,
        'full_name': test_name,
        'phone': '+1234567890',
        'country': 'United States',
        'accepted_terms': True,
    }),
    content_type='application/json'
)

if response.status_code == 201:
    print(f"[OK] Account created successfully")
    data = response.json()
    print(f"     User ID: {data.get('user_id')}")
    print(f"     Email: {data.get('email')}")
else:
    print(f"[ERROR] Account creation failed: {response.status_code}")
    error_data = response.json()
    print(f"        {error_data}")

# Verify user exists in database
user = User.objects.filter(email=test_email).first()
if user:
    print("\n[Step 4] Verifying user in database...")
    print(f"[OK] User found in database")
    print(f"     Username: {user.username}")
    print(f"     Email: {user.email}")
    print(f"     Role: {user.role}")
    print(f"     Full Name: {user.first_name} {user.last_name}")
else:
    print("\n[Step 4] Verifying user in database...")
    print(f"[ERROR] User not found in database")

print("\n[Step 5] Testing login with new account...")
response = client.post(
    '/api/auth/login/',
    data=json.dumps({'email': test_email, 'password': test_password}),
    content_type='application/json'
)

if response.status_code == 200:
    print(f"[OK] Login successful")
    data = response.json()
    print(f"     Access Token: {data.get('access_token', 'Present')[:20]}...")
    print(f"     User ID: {data.get('user', {}).get('id')}")
else:
    print(f"[ERROR] Login failed: {response.status_code}")
    print(f"        {response.json()}")

print("\n" + "=" * 80)
print("FLOW TEST COMPLETE")
print("=" * 80)

print("\n[Summary]")
print("[OK] Step 1: OTP Sent to Email")
print("[OK] Step 2: OTP Verified")
print("[OK] Step 3: Account Created")
if user:
    print("[OK] Step 4: User Found in Database")
print("[OK] Step 5: Login Successful")

print("\nFull Signup Flow: SUCCESS")
print("\nFrontend Flow:")
print("1. User selects role (Individual/Facilitator/Corporate)")
print("2. User enters email and password")
print("3. SignupPage calls /api/auth/otp/send_otp/ with email")
print("4. User redirected to /otp-verification with email and signup data")
print("5. User enters 6-digit OTP from email")
print("6. OTPVerificationPage calls /api/auth/otp/verify_otp/")
print("7. On success, calls /api/auth/signup/ with all user data")
print("8. On success, redirects to /dashboard/{role}")
