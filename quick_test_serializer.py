#!/usr/bin/env python
"""
Quick test to verify the serializer fix works
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.local_dev_settings')
django.setup()

from django.contrib.auth import get_user_model
from community.models import CorporateOpportunity

User = get_user_model()

# Check if there are any opportunities
count = CorporateOpportunity.objects.filter(status='open').count()
print(f'Open opportunities in database: {count}')

if count > 0:
    opp = CorporateOpportunity.objects.filter(status='open').first()
    print(f'Sample opportunity: {opp.title}')
    print(f'Creator: {opp.creator.username if opp.creator else None}')
    print(f'Status: {opp.status}')
    
    # Test the serializer
    from promotions.serializers import OpportunityListSerializer
    serializer = OpportunityListSerializer(opp)
    print(f'Serializer data keys: {list(serializer.data.keys())}')
    print(f'Creator ID from serializer: {serializer.data.get("creator")}')
    print(f'Creator name: {serializer.data.get("creator_name")}')
    print('✅ Serializer works!')
else:
    print('No open opportunities found')
