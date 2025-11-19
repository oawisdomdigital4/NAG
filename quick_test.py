#!/usr/bin/env python
"""
Quick verification that export endpoint works
"""
import requests

API_BASE = "http://localhost:8000"

# Login
login_resp = requests.post(
    f"{API_BASE}/api/accounts/login/",
    json={"email": "test.facilitator@example.com", "password": "testpass123"}
)

if login_resp.status_code == 200:
    token = login_resp.json().get("token")
    headers = {"Authorization": f"Token {token}"}
    
    # Test export
    export_resp = requests.get(
        f"{API_BASE}/api/promotions/sponsor-campaigns/export_report/",
        headers=headers
    )
    
    print(f"Export Status: {export_resp.status_code}")
    print(f"Content-Type: {export_resp.headers.get('Content-Type')}")
    
    if export_resp.status_code == 200:
        print("SUCCESS - Export endpoint working!")
    else:
        print(f"FAILED - Status: {export_resp.status_code}")
        print(f"Response: {export_resp.text[:200]}")
else:
    print(f"Login failed: {login_resp.status_code}")
