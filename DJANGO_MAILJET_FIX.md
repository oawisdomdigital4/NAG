# Django Mailjet Import Error - FIXED

## Issue
When trying to delete groups, the following error appeared:
```
ModuleNotFoundError: No module named 'django_mailjet'
```

## Root Cause
The legacy `community/admin.py` file was being executed at import time through a dynamic import mechanism in `community/admin/__init__.py`. This legacy file, although no longer the primary admin configuration, was still present and was trying to be loaded. However, the dynamic import mechanism would silently fail, and the error would surface when the server processed a request.

## Solution
**Backed up and disabled** the legacy `community/admin.py` file since:
1. All admin registrations have been consolidated into `community/admin/__init__.py`
2. The legacy file was causing import issues without providing value
3. The legacy file was not being executed by the Django admin system properly (it was a workaround that is no longer needed)

**Action Taken:**
```bash
mv community/admin.py community/admin.py.bak
```

## Verification
✓ All 19 community models still registered and displaying in admin
✓ Django system check passes with no errors
✓ Group deletion now works without django_mailjet errors
✓ No impact on functionality

## Files Changed
- ✓ Backed up: `community/admin.py` → `community/admin.py.bak`
- ✓ Primary config: `community/admin/__init__.py` (contains all 19 model registrations)

## Models Still Registered (19 total)
- CommunitySection, CTABanner
- Group, GroupMembership, GroupInvite
- CorporateConnection, CorporateVerification
- UserEngagementScore, SubscriptionTier, SponsoredPost, TrendingTopic
- CorporateOpportunity, OpportunityApplication
- CollaborationRequest, PlatformAnalytics
- CommunityEngagementLog, MentionLog, UserReputation, EngagementNotification

## Email Backend
- EMAIL_BACKEND: `django.core.mail.backends.smtp.EmailBackend` (Django built-in SMTP)
- Mailjet configuration still in place (in-v3.mailjet.com:587)
- No dependency on django_mailjet package needed

## Status
✓ RESOLVED - Group deletion and all admin operations work without errors
