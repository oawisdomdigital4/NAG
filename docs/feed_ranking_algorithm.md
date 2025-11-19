# Feed Ranking Algorithm Documentation

## Overview

The NAG platform uses an intelligent feed ranking algorithm that determines the visibility and priority of posts across the Community, Magazine, and Homepage sections. This ensures:

- **Fair visibility** for all content creators (facilitators, corporates, individuals)
- **Engagement-driven feed** that rewards quality content
- **Sponsored content support** for promotional visibility
- **Dynamic recency** that prevents old content from dominating
- **Personalized relevance** based on user interests and activity

---

## Ranking Factors

### 1. **Promotion Level** (Sponsored Posts)
**Weight: Primary Multiplier**

Sponsored posts receive a priority boost based on their campaign configuration:

```
sponsored_boost = 1.0 + (priority_level * 0.5)
```

**Priority Levels:**
- Level 1 (Standard): 1.5x boost
- Level 2 (High): 2.0x boost  
- Level 3 (Premium): 2.5x boost

**Conditions:**
- Campaign status must be "active"
- Campaign dates must be current (start_date ≤ now < end_date)
- Non-sponsored posts get 1.0x (no boost)

---

### 2. **Engagement Rate**
**Weight: Core Scoring Factor**

Measures how actively users interact with the post:

```
engagement_score = (reactions * 1.0) + (comments * 2.0) + (bookmarks * 3.0)
```

**Weighting Rationale:**
- Reactions (likes, hearts, etc.): 1 point
- Comments (discussions): 2 points (higher effort = more meaningful)
- Bookmarks (saved for later): 3 points (indicates strong intent)

**Example:**
- Post with 10 reactions, 5 comments, 2 bookmarks = 10 + 10 + 6 = 26 points

---

### 3. **Relevance Score**
**Weight: Personalization Multiplier**

Determines how relevant a post is to a specific user:

```
relevance_score = 1.0 + (tag_matches * 0.2) + (group_bonus * 0.5) + (follow_bonus * 0.3)
```

**Scoring Breakdown:**
- **Base**: 1.0 (all posts start here)
- **Tag Matches**: +0.2 per matching industry tag
  - Compares post tags with user's interests
  - Example: User interested in "AI" + post tagged "AI" = +0.2
- **Group Membership**: +0.5 if user is member of post's group
- **Author Follow**: +0.3 if user follows the post author

**Example Calculation:**
- User interests: ["AI", "Tech", "Startups"]
- Post tags: ["AI", "Machine Learning"]
- Post in user's group: Yes
- User follows author: No
- Relevance = 1.0 + (1 match × 0.2) + 0.5 + 0 = 1.7

---

### 4. **Recency (Time Decay)**
**Weight: Exponential Decay Function**

Recent posts get a temporary boost that gradually decreases over time:

```
time_decay = 10.0 × 0.5^(age_in_seconds / half_life_seconds)
```

**Half-Life: 2 Days**
- A post's score halves every 2 days
- After 2 days: 50% of original score
- After 4 days: 25% of original score
- After 7 days: ~8% of original score

**Timeline Example:**
```
Publication    | Time Decay | Impact
Now (0h)       | 10.0       | 100%
12 hours       | 7.07       | 71%
1 day          | 7.07       | 71%
2 days         | 5.0        | 50%
3 days         | 3.54       | 35%
7 days         | 0.78       | 8%
14 days        | 0.15       | 1.5%
```

---

### 5. **Author Role Boost**
**Weight: Role Multiplier**

Different user roles get visibility boosts:

```
role_boost = 1.0 (Individual)
           | 1.5 (Facilitator/Admin)
           | 2.0 (Corporate)
```

**Rationale:**
- Corporates: Professional content, wider reach
- Facilitators: Community leaders, trusted voices
- Individuals: Base boost (no penalty)

---

## Final Ranking Score

The final ranking score combines all factors:

```
ranking_score = engagement_score × time_decay × role_boost × sponsored_boost × relevance_score
```

**Example Calculation:**

```
Post: "Tech Summit 2025"
- Engagement Score: 26 points
- Time Decay: 7.07 (1 day old)
- Role Boost: 2.0 (Corporate author)
- Sponsored Boost: 2.0 (Level 2 campaign)
- Relevance Score: 1.7 (personalized)

Final Score = 26 × 7.07 × 2.0 × 2.0 × 1.7 = 1,569.68
```

---

## Feed Visibility Levels

Posts appear in feed based on visibility settings:

| Visibility | Who Sees | Ranking Applied |
|-----------|----------|-----------------|
| `public_global` | All users | Yes, across entire platform |
| `group_only` | Group members | Yes, within group feed |
| `private` | Author only | No, never ranked |

---

## Implementation Details

### Cache Strategy

Posts' ranking scores are cached for 1 hour to reduce database queries:

```python
# Post ranking cached as:
post_rankings = {
    'post:123': 1569.68,
    'post:456': 892.34,
    # ...
}

# TTL: 3600 seconds (1 hour)
```

### Database Indexes

Optimized queries use indexes on:
- `-ranking_score` (for feed ordering)
- `sponsor_campaign__status` (for sponsorship checks)
- `created_at` (for time decay)
- `author__role` (for role boost)

### Recalculation Triggers

Post ranking scores are recalculated when:
- New reaction added/removed
- Comment created/deleted
- Post bookmarked/unbookmarked
- Campaign status changes
- Post view recorded

---

## API Usage

### Get User's Personalized Feed

```python
from community.feed import FeedRanker

# In your view:
feed = FeedRanker.get_feed_for_user(request.user)
paginated_feed = feed[:20]  # First 20 ranked posts
```

### Manually Rank Queryset

```python
from community.models import Post
from community.feed import FeedRanker

posts = Post.objects.filter(group__id=5)
ranked = FeedRanker.rank_queryset(posts, user=request.user)
```

### Update Post Ranking

```python
post.update_ranking()  # Recalculate and save ranking score
```

---

## Performance Considerations

### Time Complexity
- Engagement calculation: O(1) with database aggregation
- Time decay: O(1) mathematical function
- Role boost: O(1) lookup
- Sponsored boost: O(1) lookup
- Final ranking: O(n log n) for sorting

### Optimization Tips
1. **Use pagination** - Load 20-50 posts per page, not all
2. **Cache aggressively** - Ranking scores cached for 1 hour
3. **Index wisely** - Already optimized for common queries
4. **Batch updates** - Update multiple post rankings together

---

## Testing & Monitoring

### Sample Test Cases

**Test 1: Engagement Boost**
```
Post A: 5 reactions, 2 comments = 9 points
Post B: 0 reactions, 0 comments = 0 points
Result: Post A should rank higher
```

**Test 2: Recency Decay**
```
Post (just published): score = engagement × 10.0 × boosts
Post (2 days old): score = engagement × 5.0 × boosts (50% of above)
Result: New post with lower engagement can outrank old viral post
```

**Test 3: Sponsorship Priority**
```
Organic post score: 100
Sponsored post (level 2): 100 × 2.0 = 200
Result: Sponsored gets 2x boost
```

**Test 4: Role-Based Boost**
```
Individual score: 100
Corporate score: 100 × 2.0 = 200
Result: Corporate post gets 2x visibility
```

---

## Future Enhancements

- [ ] Machine learning model for personalized weights
- [ ] A/B testing framework for algorithm tuning
- [ ] User preference controls (filter by type, source)
- [ ] Trending hashtag/topic boost
- [ ] Community feedback on ranking quality
- [ ] Diversity penalty (prevent single sources from dominating)

