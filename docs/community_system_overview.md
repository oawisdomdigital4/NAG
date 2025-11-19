# Community System — Functional Overview & Purpose

Date: 2025-11-05

## Introduction

The Community is the social and collaborative heart of the New Africa Group platform. It connects learners, facilitators, and corporate organizations in a unified digital ecosystem designed to promote collaboration, knowledge sharing, mentorship, and real opportunities. The platform aims to move beyond a static e-learning experience into a dynamic knowledge economy where users can engage, grow visibility, and build professional relationships across Africa and beyond.

## 1. Core Purpose
The Community exists to:

- Connect people — link individuals, facilitators, and corporates across discussions, groups, and professional spaces.
- Enable collaboration — support cross-sector interactions, partnerships, and group-based initiatives.
- Promote learning engagement — complement courses, mentorship, and professional development.
- Encourage visibility and influence — provide channels for reputation-building (posts, sponsored content, thought leadership).
- Support economic opportunities — integrate job listings, projects, and sponsored campaigns.

## 2. Structure and Key Features

### A. Global Feed (Public / Subscribed View)

- Universal community space visible to subscribed members.
- Post types supported: text updates, photos, videos, links (with preview), mentions (@username).
- Feed algorithm prioritizes posts by:
  1. Promotion Level (sponsored and paid boosts).
  2. Relevance and tags.
  3. Recency (temporary boosts for new posts).
  4. Engagement weight (likes, comments, mentions).
  5. Role type (content from facilitators/corporates has higher weight).

Feed behavior notes:
- Sponsored posts should receive a deterministic promotion weight and defined campaign duration.
- Engagement decay over time should be implemented to surface fresh content.

### B. Groups
Groups are topic-focused, private or public spaces for concentrated discussion.

Types of groups:
- Facilitator Groups: created by facilitators; used to support their courses, pin lessons, share resources, and track analytics per-course.
- Corporate Groups: created by corporate accounts; used for job announcements, campaigns, and professional collaboration.

Moderation & Roles:
- Moderators are chosen from group members (cannot remove admins or edit settings).
- Admins (group creators) manage membership, pins, and moderation.

Access rules:
- Group posts visible only to members. Non-members see a preview and must join to interact.
- Optional private groups with invite-only entry or verification.

### C. User Roles and Their Community Functions

1. Individual Users
- Engage, comment, join groups, follow facilitators/corporates, and apply to opportunities.
- Build a professional identity and participate after subscribing.

2. Facilitators
- Create course-tied groups, post content, sponsor posts, and access engagement analytics.

3. Corporates
- Create brand or sector groups, post opportunities, sponsor campaigns, and access analytics.

## 3. Sponsored Posts System

Sponsored posts allow paid visibility boosts across the Community, Magazine, and Home.

How it works:
- Campaigns provide a promotion weight and budget/duration settings.
- Ranking uses Promotion Level, Engagement Rate, Relevance Score, and Recency.

Ranking pseudo-formula (example):

ReachScore = w_p * PromotionLevel + w_e * EngagementRate + w_r * Relevance + w_t * RecencyBoost

(Weights tuned in production based on A/B tests and platform goals.)

## 4. Engagement System

Every action (likes, comments, mentions, group joins) is logged for analytics:

- Likes: quick appreciation metric.
- Comments: deeper engagement and conversation.
- Mentions: trigger in-app and email notifications.
- Notifications: sent per engagement type with role-based templates.

Engagement drives:
- Facilitator analytics (course popularity, retention indicators).
- Corporate insights (campaign performance).
- Individual reputation (activity rank; candidate for badges/leaderboards).

## 5. Collaboration & Opportunities

- Facilitators can partner with corporates for sponsored learning or events.
- Corporates list jobs, internships, and events; subscribed individuals can apply in-app.
- Collaboration requests and partner onboarding managed via the Partner Directory and Messaging system.

## 6. Personal Branding & Growth

- Facilitators and corporates use the platform to build authority and visibility.
- Individuals increase visibility through consistent, high-quality participation.
- Future expansions: badges, leaderboards, reputation scoring.

## 7. Data & Analytics Integration

Analytics per role:
- Facilitators: post reach, course engagement, group activity.
- Corporates: campaign reach, impressions, partner collaborations.
- Individuals: engagement rate, course-based community participation, opportunity applications.

Admin dashboards:
- Platform-wide engagement trends, retention metrics, and trending topics.

Data model / instrumentation notes:
- Log every interaction with user_id, target_id (post/comment/group), action_type, timestamp, metadata.
- Store aggregates for fast queries (daily/hourly materialized counters) and retain event logs for deeper analysis.

## 8. Access Control & Monetization

Access rules:
- Only subscribed users can post or comment; non-subscribed users see previews only.
- Subscription pricing (example):
  - Individual: $1/month
  - Facilitator: $5/month
  - Corporate: $500/year
- Sponsored Post Boosts: price per campaign or budget-driven bidding.

## 9. Implementation Considerations (Contract & Edge Cases)

Contract (2–3 bullets):
- Inputs: authenticated user actions (post, comment, like, join group, sponsor post) and content payloads (text, media, link metadata).
- Outputs: persisted events, notification triggers, feed placements, analytics counters, and API responses.
- Error modes: malformed content, unauthorized actions, media upload failures, and payment failures for sponsored campaigns.

Edge cases:
- Anonymous or deleted users: retain events but mark as anonymized.
- High-volume posts: rate limit posting and engagement actions.
- Media moderation: flagging and soft-removal until review.
- Sponsored campaign expiration: graceful decay and reporting.

## 10. Next Steps & Roadmap (Suggested)

MVP (short-term):
- Global feed (text, link preview, images) with basic ranking (recency + engagement).
- Core group functionality (create/join/post/privacy settings).
- Roles & access gating by subscription status.
- Basic notifications and simple analytics (per-post counters).

Phase 2:
- Sponsored posts and payments integration (campaign management, budgets, billing hooks).
- Advanced ranking & relevance signals.
- Moderation tools and content reporting.
- Per-facilitator course analytics and group insights.

Phase 3:
- Real-time features (live sessions, chat rooms), rich profile badges, leaderboards, and partner dashboards.
- Deep analytics platform integration (data warehouse / BI dashboards).

## 11. Appendix: Quick Data Model Sketch

- User (id, role, subscription_status, profile)
- Group (id, name, type, privacy, creator_id)
- Membership (user_id, group_id, role, joined_at)
- Post (id, author_id, group_id|null, content, media[], link_preview, is_sponsored:boolean, sponsor_campaign_id|null, created_at)
- Reaction (id, user_id, target_type(post/comment), target_id, kind, created_at)
- Comment (id, post_id, author_id, content, parent_comment_id|null, created_at)
- SponsorCampaign (id, owner_id, budget, start_at, end_at, promotion_level, status)
- EngagementLog (id, user_id, action, target_type, target_id, metadata, created_at)

---

For convenience I've added this document to `docs/community_system_overview.md`. If you'd like, I can also:

- Link it from the main `README.md` or from a docs index.
- Break this into implementation epics and generate tracker issues (GitHub issues or a project board).
- Produce a one-page product brief or slide deck summary for stakeholders.

Which follow-up should I do next?