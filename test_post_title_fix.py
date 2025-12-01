import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test client
client = Client()

# Get a user to test with
user = User.objects.first()
if user:
    print(f"Testing with user: {user.username}")
    
    # Make API request
    response = client.get(f'/api/community/activities/?user={user.id}&limit=10')
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ API Response Status: {response.status_code}")
        print(f"Activities Count: {data['count']}\n")
        
        print("Recent Activities:")
        for activity in data['results'][:5]:
            if activity.get('post'):
                print(f"  Activity {activity['id']}: {activity['activity_type']}")
                print(f"    Post Title/Content: {activity['post']['title'][:60]}...")
                print()
    else:
        print(f"❌ API Error: {response.status_code}")
else:
    print("No users found in database")
