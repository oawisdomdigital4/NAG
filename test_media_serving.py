import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from urllib.parse import quote

client = Client()

# Test URL with encoded spaces
encoded_path = "assignments/14/35/6/20-11-2025%20PROJECT%20UPDATES%20REPORT.docx"
url = f"/media/{encoded_path}"

print(f"Testing URL: {url}")
print()

response = client.get(url)
print(f"Status Code: {response.status_code}")
print(f"Content Type: {response.get('Content-Type')}")
print(f"Content Length: {response.get('Content-Length')}")

if response.status_code == 200:
    print("✓ File served successfully!")
    print(f"File size in response: {len(response.content)} bytes")
else:
    print(f"✗ Error: {response.content.decode()}")
