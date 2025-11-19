#!/usr/bin/env python
"""
Test script for export report and start campaign features
"""
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
# Token auth not used in this test script; we'll use session auth via force_login
from promotions.models import SponsorCampaign

User = get_user_model()

def test_start_campaign():
    """Test starting a new campaign"""
    print("\n🧪 Testing START CAMPAIGN endpoint...")
    
    # Create test user
    user, _ = User.objects.get_or_create(
        username='campaign_tester',
        defaults={'email': 'campaign_test@example.com'}
    )
    
    client = Client()
    # Force login the user for session authentication in tests
    client.force_login(user)
    
    # Prepare campaign data
    now = timezone.now()
    end_date = now + timedelta(days=7)
    
    payload = {
        'title': 'Test Campaign - Export Feature',
        'description': 'Testing the start campaign endpoint',
        'start_date': now.isoformat(),
        'end_date': end_date.isoformat(),
        'budget': 5000.00,
        'cost_per_view': 0.50,
        'priority_level': 2,
        'target_audience': {
            'regions': ['US', 'UK'],
            'interests': ['Technology', 'Education']
        }
    }
    
    # Test POST /api/promotions/sponsor-campaigns/start_campaign/
    response = client.post(
        '/api/promotions/sponsor-campaigns/start_campaign/',
        data=payload,
        content_type='application/json',
        HTTP_HOST='localhost'
    )
    
    print(f"POST /api/promotions/sponsor-campaigns/start_campaign/")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        campaign_id = data['campaign']['id']
        print(f"✅ Campaign created successfully! ID: {campaign_id}")
        print(f"Campaign Status: {data['campaign']['status']}")
        print(f"Budget: ${data['campaign']['budget']}")
        return campaign_id
    else:
        print(f"❌ Failed to start campaign: {response.content}")
        return None

def test_activate_campaign(campaign_id):
    """Test activating a draft campaign"""
    print(f"\n🧪 Testing ACTIVATE CAMPAIGN endpoint...")
    
    user = User.objects.get(username='campaign_tester')
    client = Client()
    client.force_login(user)
    
    # Test POST /api/promotions/sponsor-campaigns/{id}/activate/
    response = client.post(
        f'/api/promotions/sponsor-campaigns/{campaign_id}/activate/',
        data={},
        content_type='application/json',
        HTTP_HOST='localhost'
    )
    
    print(f"POST /api/promotions/sponsor-campaigns/{campaign_id}/activate/")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Campaign activated successfully!")
        print(f"Campaign Status: {data['campaign']['status']}")
        return True
    else:
        print(f"❌ Failed to activate campaign: {response.content}")
        return False

def test_export_report():
    """Test exporting campaigns report"""
    print(f"\n🧪 Testing EXPORT REPORT endpoint...")
    
    user = User.objects.get(username='campaign_tester')
    client = Client()
    client.force_login(user)
    
    # Test GET /api/promotions/sponsor-campaigns/export_report/
    response = client.get(
        '/api/promotions/sponsor-campaigns/export_report/',
        HTTP_HOST='localhost'
    )
    
    print(f"GET /api/promotions/sponsor-campaigns/export_report/")
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        print(f"✅ Report exported successfully!")
        print(f"CSV Header: {lines[0][:60]}...")
        print(f"Total rows (including header): {len(lines)}")
        if len(lines) > 1:
            print(f"Sample data row: {lines[1][:60]}...")
        return True
    else:
        print(f"❌ Failed to export report: {response.content}")
        return False

def test_analytics_summary():
    """Test getting analytics summary"""
    print(f"\n🧪 Testing ANALYTICS SUMMARY endpoint...")
    
    user = User.objects.get(username='campaign_tester')
    client = Client()
    client.force_login(user)
    
    # Test GET /api/promotions/sponsor-campaigns/analytics_summary/
    response = client.get(
        '/api/promotions/sponsor-campaigns/analytics_summary/?days=30',
        HTTP_HOST='localhost'
    )
    
    print(f"GET /api/promotions/sponsor-campaigns/analytics_summary/?days=30")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Analytics summary retrieved successfully!")
        print(f"Total Campaigns: {data['total_campaigns']}")
        print(f"Active Campaigns: {data['active_campaigns']}")
        print(f"Total Impressions: {data['total_impressions']}")
        print(f"Total Clicks: {data['total_clicks']}")
        print(f"Average Engagement Rate: {data['average_engagement_rate']}%")
        print(f"Total Budget: ${data['total_budget']}")
        return True
    else:
        print(f"❌ Failed to get analytics summary: {response.content}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 EXPORT REPORT & START CAMPAIGN TEST SUITE")
    print("=" * 60)
    
    # Test 1: Start a campaign
    campaign_id = test_start_campaign()
    
    if not campaign_id:
        print("\n❌ Cannot proceed - campaign creation failed")
        return
    
    # Test 2: Activate the campaign
    test_activate_campaign(campaign_id)
    
    # Test 3: Export report
    test_export_report()
    
    # Test 4: Get analytics summary
    test_analytics_summary()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == '__main__':
    main()
