#!/usr/bin/env python
"""
Final verification that all community admin models are registered and displaying.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib import admin
from django.apps import apps

print("\n" + "="*80)
print("FINAL ADMIN REGISTRATION VERIFICATION - ALL MODELS")
print("="*80 + "\n")

# Get all registered models
registered_models = admin.site._registry

# Group models by app
models_by_app = {}
for model, admin_instance in registered_models.items():
    app_label = model._meta.app_label
    if app_label not in models_by_app:
        models_by_app[app_label] = []
    models_by_app[app_label].append(model.__name__)

# Display community models specifically
print("✓ COMMUNITY APP MODELS (Registered in admin/__init__.py):\n")
community_models = [
    'CommunitySection', 'CTABanner', 'Group', 'GroupMembership', 'GroupInvite',
    'CorporateConnection', 'CorporateVerification',
    'UserEngagementScore', 'SubscriptionTier', 'SponsoredPost', 'TrendingTopic',
    'CorporateOpportunity', 'OpportunityApplication', 'CollaborationRequest',
    'PlatformAnalytics',
    'CommunityEngagementLog', 'MentionLog', 'UserReputation', 'EngagementNotification'
]

community_registered = models_by_app.get('community', [])
print(f"Total Community Models in Admin: {len(community_registered)}\n")

for model_name in community_models:
    status = "✓" if model_name in community_registered else "✗"
    print(f"  {status} {model_name}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

all_found = all(model in community_registered for model in community_models)
if all_found:
    print("\n✓ SUCCESS! All community system models are registered and displaying!")
    print(f"\nTotal: {len(community_registered)} models from community app")
    print("\nModels are now fully manageable in Django admin panel:")
    print("  • Site-wide content (CommunitySection, CTABanner)")
    print("  • Group management (Group, GroupMembership, GroupInvite)")
    print("  • Corporate system (CorporateConnection, CorporateVerification)")
    print("  • Monetization (SubscriptionTier, SponsoredPost)")
    print("  • Opportunities (CorporateOpportunity, OpportunityApplication)")
    print("  • Community features (Trending, Collaboration)")
    print("  • Analytics (UserEngagementScore, PlatformAnalytics)")
    print("  • Engagement tracking (Logs, Mentions, Reputation, Notifications)")
else:
    print("\n✗ INCOMPLETE - Missing models:")
    missing = [m for m in community_models if m not in community_registered]
    for m in missing:
        print(f"  ✗ {m}")

print("\n" + "="*80 + "\n")
