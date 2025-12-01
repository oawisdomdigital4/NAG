from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from .analytics_service import AnalyticsService
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncMonth, TruncDate

# Local models
from .models import FacilitatorEarning
try:
    # Prefer courses app models when available
    from courses.models import Course, Enrollment, CourseReview
except Exception:
    # Fallbacks if course models differ
    Course = None
    Enrollment = None
    CourseReview = None

class DashboardAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        user = request.user
        
        # Get all relevant analytics
        campaign_performance = AnalyticsService.get_campaign_performance(user, days)
        earnings_summary = AnalyticsService.get_earnings_summary(user, days)
        engagement_patterns = AnalyticsService.get_engagement_patterns(user, days)
        roi_metrics = AnalyticsService.get_roi_metrics(user, days)
        audience_insights = AnalyticsService.get_audience_insights(user, days)
        profile_metrics = AnalyticsService.get_profile_metrics(user, days)
        user_account_insights = AnalyticsService.get_user_account_insights(user, days)
        
        # Build frontend-friendly data structures
        # Performance Trends (daily): combine campaign impressions (views) with click counts
        trends = []
        try:
            # base views per day from campaign_performance.trends if available
            campaign_trends = campaign_performance.get('trends') or []
            views_map = {t.get('period'): (t.get('metrics', {}).get('views', 0) or 0) for t in campaign_trends}

            # compute clicks per day by aggregating EngagementLog and CommunityEngagementLog
            start_date = (timezone.now() - timedelta(days=days)).date()
            end_date = timezone.now().date()

            from django.db.models.functions import TruncDate
            # EngagementLog (promotions) clicks
            try:
                prom_clicks_qs = EngagementLog.objects.filter(
                    post__sponsored_campaign__sponsor=user,
                    created_at__date__range=(start_date, end_date),
                    action_type__in=['click']
                ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
            except Exception:
                prom_clicks_qs = []

            # Community clicks
            try:
                from community.engagement import CommunityEngagementLog
                comm_clicks_qs = CommunityEngagementLog.objects.filter(
                    post__sponsored_campaign__sponsor=user,
                    created_at__date__range=(start_date, end_date),
                    action_type='click_action'
                ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
            except Exception:
                comm_clicks_qs = []

            clicks_map = {}
            for row in prom_clicks_qs:
                d = row.get('date').strftime('%Y-%m-%d')
                clicks_map[d] = clicks_map.get(d, 0) + (row.get('count') or 0)
            for row in comm_clicks_qs:
                d = row.get('date').strftime('%Y-%m-%d')
                clicks_map[d] = clicks_map.get(d, 0) + (row.get('count') or 0)

            # Build combined trends iterating campaign_trends periods (fallback: generate date range)
            if campaign_trends:
                for t in campaign_trends:
                    period = t.get('period')
                    v = int(t.get('metrics', {}).get('views', 0) or 0)
                    c = int(clicks_map.get(period, 0))
                    trends.append({'period': period, 'views': v, 'clicks': c, 'metrics': {'views': v, 'clicks': c}})
            else:
                # fallback: iterate dates between start and end
                cur = start_date
                while cur <= end_date:
                    p = cur.strftime('%Y-%m-%d')
                    v = int(views_map.get(p, 0))
                    c = int(clicks_map.get(p, 0))
                    trends.append({'period': p, 'views': v, 'clicks': c, 'metrics': {'views': v, 'clicks': c}})
                    cur += timedelta(days=1)
        except Exception:
            # If anything fails, fall back to a simple placeholder based on engagement_patterns
            for item in (engagement_patterns.get('engagement_types') or [])[:7]:
                trends.append({
                    'period': item.get('action_type', 'Unknown'),
                    'views': item.get('count', 0),
                    'metrics': {'views': item.get('count', 0)}
                })
        
        # Audience Demographics (from audience_insights)
        audience_demographics = []
        for role_item in (audience_insights.get('audience_roles') or [])[:5]:
            total_engagement = sum(i.get('count', 0) for i in (audience_insights.get('audience_roles') or []))
            pct = (role_item.get('count', 0) / total_engagement * 100) if total_engagement > 0 else 0
            audience_demographics.append({
                'category': role_item.get('user__role', 'Unknown'),
                'percentage': round(pct, 1),
                'count': role_item.get('count', 0)
            })
        
        # Top Performing Content (from audience_insights.content_engagement)
        top_content = []
        for content in (audience_insights.get('content_engagement') or [])[:10]:
            top_content.append({
                'title': content.get('post__title', 'Untitled'),
                'type': 'Post',
                'views': content.get('views', 0),
                'clicks': content.get('clicks', 0),
                'likes': content.get('likes', 0),
                'comments': content.get('comments', 0),
                'shares': content.get('shares', 0),
                'date': '—'
            })
        
        return Response({
            'campaign_performance': campaign_performance,
            'earnings_summary': earnings_summary,
            'engagement_patterns': engagement_patterns,
            'roi_metrics': roi_metrics,
            'audience_insights': audience_insights,
            'profile_metrics': profile_metrics,
            'user_account_insights': user_account_insights,
            'performance_trends': trends,
            'audience_demographics': audience_demographics,
            'top_content': top_content,
            'period_days': days
        })


class FacilitatorAnalyticsView(APIView):
    """Return a normalized analytics payload for a facilitator (used by frontend).

    This view aims to provide a stable JSON shape so the frontend doesn't
    receive 404s or partial/undefined responses. It uses available
    AnalyticsService helpers when possible and falls back to sensible
    defaults.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        user = request.user

        # Use AnalyticsService where it makes sense
        earnings = AnalyticsService.get_earnings_summary(user, days)

        # audience and engagement helpers may provide useful lists
        audience = AnalyticsService.get_audience_insights(user, days)
        engagement = AnalyticsService.get_engagement_patterns(user, days)

        # Build a normalized payload matching frontend expectations
        profile = getattr(user, 'profile', None)
        profile_earning_balance = None
        profile_pending_balance = None
        profile_available_balance = None
        if profile and hasattr(profile, 'earning_balance') and profile.earning_balance is not None:
            profile_earning_balance = float(profile.earning_balance)
        if profile and hasattr(profile, 'pending_balance') and profile.pending_balance is not None:
            profile_pending_balance = float(profile.pending_balance)
        if profile and hasattr(profile, 'available_balance') and profile.available_balance is not None:
            profile_available_balance = float(profile.available_balance)
        payload = {
            # Three-balance wallet system
            'earning_balance': profile_earning_balance if profile_earning_balance is not None else float(earnings.get('total_earnings') or 0),
            'pending_balance': profile_pending_balance if profile_pending_balance is not None else 0.0,
            'available_balance': profile_available_balance if profile_available_balance is not None else 0.0,
            
            # Scalars
            'total_earnings': profile_earning_balance if profile_earning_balance is not None else float(earnings.get('total_earnings') or 0),
            'total_students': 0,
            'avg_rating': 0.0,
            'total_courses': 0,

            # Trends and lists (frontend will guard these, but provide defaults)
            'earning_trends': [],
            'enrollment_trends': [],
            'course_performance': [],
            'rating_distribution': [],
            'engagement_by_type': [],

            'period_days': days,

            # Growth stats - keep keys the frontend expects
            'growth_stats': {
                'earnings_growth': '',
                'student_growth': '',
                'rating_change': '',
                'course_growth': ''
            }
        }

        # If earnings_by_source exists, expose total_earnings already set above
        # Optionally map audience insights into course_performance simplistically
        content_engagement = audience.get('content_engagement') or []
        if content_engagement:
            # Map top content into course-like performance rows (best-effort)
            courses = []
            for c in content_engagement[:10]:
                courses.append({
                    'title': c.get('post__title') or 'Untitled',
                    'students': int(c.get('views') or 0),
                    'revenue': float(c.get('views') or 0) * 0.0,
                    'rating': 0.0,
                    'engagement': int(c.get('likes') or 0)
                })
            payload['course_performance'] = courses

        # Total earnings is already set in payload from profile_earning_balance
        # Three-balance system is already fully set above

        # Enrich payload with course/enrollment/review/earnings data when possible
        try:
            now = timezone.now()
            start_date = now - timedelta(days=days)

            if Course is not None:
                courses_qs = Course.objects.filter(facilitator=user)
                payload['total_courses'] = courses_qs.count()

                # Total students across facilitator's courses
                if Enrollment is not None:
                    total_students = Enrollment.objects.filter(course__in=courses_qs).count()
                    payload['total_students'] = total_students

                    # Enhanced Enrollment trends by month
                    enrollment_months = (
                        Enrollment.objects.filter(course__in=courses_qs, enrolled_at__range=(start_date, now))
                        .annotate(month=TruncMonth('enrolled_at'))
                        .values('month')
                        .annotate(
                            students=Count('id'),
                            unique_students=Count('student', distinct=True),
                            completed_courses=Count('id', filter=F('status') == 'completed'),
                            avg_progress=Avg('progress_percentage')
                        )
                        .order_by('month')
                    )

                    # Process enrollment data with growth metrics
                    trends = []
                    prev_month_data = None
                    
                    for e in enrollment_months:
                        growth = {
                            'total': 0,
                            'unique': 0,
                            'completion': 0
                        }
                        
                        if prev_month_data:
                            if prev_month_data['students'] > 0:
                                growth['total'] = round(((e['students'] - prev_month_data['students']) / prev_month_data['students']) * 100, 1)
                            if prev_month_data['unique_students'] > 0:
                                growth['unique'] = round(((e['unique_students'] - prev_month_data['unique_students']) / prev_month_data['unique_students']) * 100, 1)
                            if prev_month_data['completed_courses'] > 0:
                                growth['completion'] = round(((e['completed_courses'] - prev_month_data['completed_courses']) / prev_month_data['completed_courses']) * 100, 1)
                        
                        month_data = {
                            'month': e['month'].strftime('%Y-%m'),
                            'total_enrollments': e['students'],
                            'unique_students': e['unique_students'],
                            'completed_courses': e['completed_courses'],
                            'avg_progress': round(float(e['avg_progress'] or 0), 1),
                            'growth_rates': growth
                        }
                        
                        trends.append(month_data)
                        prev_month_data = e
                    
                    payload['enrollment_trends'] = trends

                # Course performance
                perf = []
                for c in courses_qs.order_by('-created_at')[:50]:
                    students = Enrollment.objects.filter(course=c).count() if Enrollment is not None else 0
                    revenue = float((getattr(c, 'price', 0) or 0) * students) if getattr(c, 'price', None) is not None else 0.0
                    avg_r = CourseReview.objects.filter(course=c).aggregate(avg=Avg('rating'))['avg'] or 0.0 if CourseReview is not None else 0.0
                    perf.append({
                        'title': c.title,
                        'students': students,
                        'revenue': revenue,
                        'rating': float(avg_r),
                        'engagement': students
                    })
                payload['course_performance'] = perf

                if CourseReview is not None:
                    overall_avg = CourseReview.objects.filter(course__in=courses_qs).aggregate(avg=Avg('rating'))['avg']
                    payload['avg_rating'] = float(overall_avg or 0.0)

                    # Enhanced Rating distribution with time-based analysis
                    ratings = (
                        CourseReview.objects.filter(course__in=courses_qs)
                        .values('rating')
                        .annotate(
                            count=Count('id'),
                            recent_count=Count(
                                'id',
                                filter=F('created_at__gte') >= (now - timedelta(days=30))
                            ),
                            avg_score=Avg('score'),
                            recent_avg_score=Avg(
                                'score',
                                filter=F('created_at__gte') >= (now - timedelta(days=30))
                            )
                        )
                        .order_by('-rating')
                    )
                    
                    total_reviews = sum(r['count'] for r in ratings) if ratings else 0
                    recent_reviews = sum(r['recent_count'] for r in ratings) if ratings else 0
                    
                    dist = []
                    for r in ratings:
                        overall_pct = (r['count'] / total_reviews * 100) if total_reviews > 0 else 0
                        recent_pct = (r['recent_count'] / recent_reviews * 100) if recent_reviews > 0 else 0
                        
                        dist.append({
                            'rating': r['rating'],
                            'count': r['count'],
                            'recent_count': r['recent_count'],
                            'percentage': round(overall_pct, 1),
                            'recent_percentage': round(recent_pct, 1),
                            'avg_score': round(float(r['avg_score'] or 0), 2),
                            'recent_avg_score': round(float(r['recent_avg_score'] or 0), 2)
                        })
                    payload['rating_distribution'] = dist

                # Enhanced Engagement by type with detailed metrics
                if Enrollment is not None:
                    fmt_qs = (
                        Enrollment.objects.filter(course__in=courses_qs)
                        .values(format=F('course__format'))
                        .annotate(
                            total_count=Count('id'),
                            active_count=Count(
                                'id',
                                filter=F('last_activity_date__gte') >= (now - timedelta(days=30))
                            ),
                            completed_count=Count(
                                'id',
                                filter=F('status') == 'completed'
                            ),
                            avg_completion=Avg('completion_percentage'),
                            avg_duration=Avg('duration_minutes')
                        )
                        .order_by('-total_count')
                    )
                    
                    total_enroll = sum(f['total_count'] for f in fmt_qs) if fmt_qs else 0
                    engagement_types = []
                    
                    for f in fmt_qs:
                        total_pct = (f['total_count'] / total_enroll * 100) if total_enroll > 0 else 0
                        completion_rate = (f['completed_count'] / f['total_count'] * 100) if f['total_count'] > 0 else 0
                        active_rate = (f['active_count'] / f['total_count'] * 100) if f['total_count'] > 0 else 0
                        
                        engagement_types.append({
                            'type': f['format'] or 'Unknown',
                            'total_students': f['total_count'],
                            'active_students': f['active_count'],
                            'completed_students': f['completed_count'],
                            'total_percentage': round(total_pct, 1),
                            'completion_rate': round(completion_rate, 1),
                            'activity_rate': round(active_rate, 1),
                            'avg_completion': round(float(f['avg_completion'] or 0), 1),
                            'avg_duration_minutes': round(float(f['avg_duration'] or 0), 1)
                        })
                    payload['engagement_by_type'] = engagement_types

            # Earnings trends by month
            earnings_qs = FacilitatorEarning.objects.filter(facilitator=user, earned_at__range=(start_date, now))
            earn_months = (
                earnings_qs
                .annotate(month=TruncMonth('earned_at'))
                .values('month')
                .annotate(total=Sum('amount'))
                .order_by('month')
            )
            payload['earning_trends'] = [
                {'month': e['month'].strftime('%Y-%m'), 'revenue': float(e['total'] or 0)} for e in earn_months
            ]

            # Simple growth heuristics
            if payload['earning_trends'] and len(payload['earning_trends']) >= 2:
                first = payload['earning_trends'][0]['revenue']
                last = payload['earning_trends'][-1]['revenue']
                if first > 0:
                    payload['growth_stats']['earnings_growth'] = f"{round((last - first) / first * 100, 1)}%"

            if payload['enrollment_trends'] and len(payload['enrollment_trends']) >= 2:
                first = payload['enrollment_trends'][0]['students']
                last = payload['enrollment_trends'][-1]['students']
                if first > 0:
                    payload['growth_stats']['student_growth'] = f"{round((last - first) / first * 100, 1)}%"

        except Exception:
            # If anything goes wrong, return the safe defaults built earlier
            pass

        # Ensure types are JSON serializable (floats instead of Decimal)
        try:
            payload['total_earnings'] = float(payload.get('total_earnings') or 0)
            payload['avg_rating'] = float(payload.get('avg_rating') or 0.0)
        except Exception:
            pass

        return Response(payload, status=status.HTTP_200_OK)