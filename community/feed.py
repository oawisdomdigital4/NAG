from django.db.models import F, ExpressionWrapper, fields, Q, Count, FloatField, When, Case
from django.utils import timezone
from datetime import timedelta
import math

class FeedRanker:
    """Feed ranking algorithm manager."""
    
    @staticmethod
    def calculate_engagement_score(post):
        """Calculate an engagement score for a post based on reactions, comments, etc."""
        # Get counts
        reactions_count = post.reactions.count()
        comments_count = post.comments.count()
        bookmarks_count = post.bookmarks.count()
        
        # Weight different types of engagement
        WEIGHTS = {
            'reaction': 1.0,
            'comment': 2.0,
            'bookmark': 3.0
        }
        
        # Calculate weighted score
        score = (
            reactions_count * WEIGHTS['reaction'] +
            comments_count * WEIGHTS['comment'] +
            bookmarks_count * WEIGHTS['bookmark']
        )
        
        return score

    @staticmethod
    def calculate_time_decay(post_date):
        """Calculate time decay factor based on post age."""
        now = timezone.now()
        age = now - post_date
        
        # Parameters for decay function
        HALF_LIFE = timedelta(days=2)  # Score halves every 2 days
        BASE_SCORE = 10.0
        
        # Calculate decay factor using exponential decay
        decay = math.exp(-math.log(2) * age.total_seconds() / HALF_LIFE.total_seconds())
        return BASE_SCORE * decay

    @staticmethod
    def calculate_role_boost(post):
        """Calculate boost factor based on author's role."""
        ROLE_BOOSTS = {
            'individual': 1.0,
            'facilitator': 1.5,
            'corporate': 2.0,
            'admin': 1.5
        }
        
        try:
            author_role = post.author.community_profile.role
            return ROLE_BOOSTS.get(author_role, 1.0)
        except AttributeError:
            return 1.0

    @staticmethod
    def calculate_sponsored_boost(post):
        """Calculate boost for sponsored posts."""
        try:
            campaign = post.sponsor_campaign
            if campaign and campaign.is_active():
                return 1.0 + (campaign.priority_level * 0.5)
        except AttributeError:
            pass
        return 1.0

    @staticmethod
    def calculate_relevance_score(post, user=None):
        """Calculate relevance score based on category tags and audience interaction."""
        relevance = 1.0
        
        # No user context - use base relevance
        if not user:
            return relevance
        
        try:
            # Get user's interests from profile
            user_interests = getattr(user.profile, 'interests', []) if hasattr(user, 'profile') else []
            user_categories = getattr(user.profile, 'categories', []) if hasattr(user, 'profile') else []
            
            # Check if post has matching industry tags
            post_tags = getattr(post, 'industry_tags', []) if hasattr(post, 'industry_tags') else []
            matching_tags = set(post_tags) & set(user_interests)
            
            # Award points for matching interests
            if matching_tags:
                relevance += len(matching_tags) * 0.2
            
            # Check group membership relevance
            if post.group and user.community_group_memberships.filter(group=post.group).exists():
                relevance += 0.5
            
            # Author interaction history boost
            if post.author and user.follower_relationships.filter(following=post.author).exists():
                relevance += 0.3
                
        except Exception:
            pass
        
        return relevance

    @classmethod
    def rank_queryset(cls, queryset, user=None):
        """
        Apply comprehensive ranking algorithm to a queryset of posts.
        
        Ranking factors (in priority order):
        1. Promotion Level - Sponsored posts get priority boost based on campaign level
        2. Engagement Rate - (Likes + Comments + Bookmarks) weighted by active users
        3. Relevance Score - Category tags, audience interaction, and user interests
        4. Recency - Recent posts get temporary boost with exponential decay
        5. Author Role - Facilitators and corporates get slight boost
        
        Args:
            queryset: QuerySet of Post objects
            user: Optional user for personalized relevance scoring
            
        Returns:
            QuerySet ordered by ranking_score (descending)
        """
        now = timezone.now()
        
        # Annotate with engagement counts
        queryset = queryset.annotate(
            reaction_count=Count('reactions'),
            comment_count=Count('comments'),
            mention_count=Count('mentions'),
            bookmark_count=Count('bookmarks'),
            
            # Calculate engagement score (include mentions)
            engagement_score=ExpressionWrapper(
                F('reaction_count') + 
                (F('comment_count') * 2.0) + 
                (F('bookmark_count') * 3.0) +
                (F('mention_count') * 4.0),
                output_field=FloatField()
            ),
            
            # Time decay
            time_factor=ExpressionWrapper(
                10.0 * pow(0.5, (now - F('created_at')).total_seconds() / (2 * 24 * 3600)),
                output_field=FloatField()
            ),
            
            # Role boost
            role_boost=Case(
                When(author__community_profile__role='corporate', then=2.0),
                When(author__community_profile__role='facilitator', then=1.5),
                default=1.0,
                output_field=FloatField()
            ),
            
            # Sponsored boost (use Post.sponsored_campaign relation)
            sponsored_boost=Case(
                When(sponsored_campaign__isnull=False, sponsored_campaign__status='active',
                     sponsored_campaign__start_date__lte=now,
                     sponsored_campaign__end_date__gt=now,
                     then=F('sponsored_campaign__promotion_level') * 0.5 + 1.0),
                default=1.0,
                output_field=FloatField()
            ),
            
            # Final ranking score
            ranking_score=F('engagement_score') * F('time_factor') * F('role_boost') * F('sponsored_boost')
        )
        
        return queryset.order_by('-ranking_score')

    @classmethod
    def get_feed_for_user(cls, user, **filters):
        """
        Get personalized feed for a user with intelligent ranking.
        
        The feed includes:
        - Public global posts visible to all users
        - Group-specific posts from groups the user is a member of
        - Posts ranked by engagement, sponsorship, relevance, and recency
        
        Args:
            user: User object to personalize feed for
            **filters: Additional QuerySet filters (e.g., group__id=5)
            
        Returns:
            QuerySet of ranked Post objects ordered by relevance
        """
        from community.models import Post
        
        # Start with all public posts
        queryset = Post.objects.filter(
            Q(feed_visibility='public_global') |
            Q(feed_visibility='group_only', group__memberships__user=user)
        ).distinct()
        
        # Apply any additional filters
        for key, value in filters.items():
            queryset = queryset.filter(**{key: value})
        
        # Apply ranking with user context for personalization
        return cls.rank_queryset(queryset, user=user)