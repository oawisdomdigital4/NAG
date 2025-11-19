# Community API

This document describes the main Community System API endpoints.

Base: /api/community/ (router prefix depends on project routing)

Authentication: JWT via `accounts.authentication.DatabaseTokenAuthentication` or session auth.

Endpoints

- GET /posts/ - List feed posts. Query params: feed_type=global|following|trending, page, page_size, author_id, group_id
- POST /posts/ - Create post (authenticated, subscription required)
- GET /posts/:id/ - Retrieve a single post
- POST /posts/:id/toggle_reaction/ - Toggle reaction (body: { reaction_type })
- POST /posts/:id/toggle_bookmark/ - Toggle bookmark
- GET /posts/:id/comments/ - List top-level comments

Groups

- GET /groups/ - List groups
- POST /groups/ - Create group
- POST /groups/:id/join/ - Join group
- POST /groups/:id/leave/ - Leave group

Sponsors

- GET /sponsors/ - List active sponsor campaigns
- POST /sponsors/ - Create sponsor campaign (corporate/facilitator)
- POST /sponsors/:id/record_impression/ - Record impression
- POST /sponsors/:id/record_click/ - Record click

Analytics

- GET /analytics/community/?days=30 - Community-wide analytics (requires authentication). Returns trending topics, user growth, content performance.
- GET /analytics/user/?days=30 - Analytics for current user
- GET /analytics/user/:user_id/?days=30 - Analytics for a specific user (staff only or self)
- GET /sponsor-analytics/?campaign_id=ID - Sponsor-specific aggregated analytics (sponsor or staff only)

Notes

- Subscription checks: Only subscribed users may create posts/comments. Enforcement should be done in the view permissions.
- Caching: Feed ranking uses Redis; configure `REDIS_URL` and install `django-redis` and `redis`.
- Pagination: DRF pagination applies for list endpoints; `page` and `page_size` query params are supported.

Examples

Fetch feed:

GET /api/community/posts/?feed_type=global&page=1&page_size=20

Fetch community analytics:

GET /api/community/analytics/community/?days=30

Sponsor impression tracking (client should call when impression visible):

POST /api/community/sponsors/123/record_impression/  (Authenticated)

Sponsor click tracking (client call on click-through):

POST /api/community/sponsors/123/record_click/  (Authenticated)

