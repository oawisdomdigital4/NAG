from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from community.models import UserActivity
from community.engagement import CommunityEngagementLog
from datetime import timedelta

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_activity(request):
    """Update user's last activity timestamp"""
    try:
        activity, _ = UserActivity.objects.get_or_create(user=request.user)
        activity.last_active = timezone.now()
        activity.save()
        
        return Response({
            'status': 'success',
            'message': 'Activity updated',
            'lastActive': activity.last_active
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity(request, user_id):
    """Get user's activity status"""
    try:
        activity = UserActivity.objects.get(user_id=user_id)
        
        # Consider user online if active in last 5 minutes
        is_online = (timezone.now() - activity.last_active).total_seconds() < 300
        
        return Response({
            'status': 'success',
            'isOnline': is_online,
            'lastActive': activity.last_active
        })
    except UserActivity.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'No activity record found'
        }, status=404)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_activities(request):
    """
    Get recent activities for the current user or a specific user.
    
    Query Parameters:
        - user: User ID (optional, defaults to current user)
        - limit: Maximum number of activities to return (default: 5, max: 50)
        - days: Filter activities from the past N days (default: 30)
    """
    try:
        # Get user from query params or use authenticated user
        user_id = request.query_params.get('user')
        limit = min(int(request.query_params.get('limit', 5)), 50)
        days = int(request.query_params.get('days', 30))
        
        if user_id:
            target_user_id = int(user_id)
        else:
            target_user_id = request.user.id
        
        # Get recent engagement logs
        start_date = timezone.now() - timedelta(days=days)
        
        logs = CommunityEngagementLog.objects.filter(
            user_id=target_user_id,
            created_at__gte=start_date
        ).select_related('user', 'post', 'comment', 'group').order_by('-created_at')[:limit]
        
        activities = []
        for log in logs:
            activity = {
                'id': log.id,
                'activity_type': log.action_type,
                'created_at': log.created_at,
                'user': {
                    'id': log.user.id,
                    'full_name': getattr(log.user.profile, 'full_name', log.user.get_full_name()),
                },
            }
            
            # Add related data based on activity type
            if log.post:
                activity['post'] = {
                    'id': log.post.id,
                    'title': log.post.title or log.post.content[:50] + '...',
                }
            
            if log.comment:
                activity['comment'] = {
                    'id': log.comment.id,
                    'content': log.comment.content[:50] + '...' if len(log.comment.content) > 50 else log.comment.content,
                }
            
            if log.group:
                activity['group'] = {
                    'id': log.group.id,
                    'name': log.group.name,
                }
            
            if log.mentioned_user:
                activity['mentioned_user'] = {
                    'id': log.mentioned_user.id,
                    'full_name': getattr(log.mentioned_user.profile, 'full_name', log.mentioned_user.get_full_name()),
                }
            
            activities.append(activity)
        
        return Response({
            'status': 'success',
            'count': len(activities),
            'results': activities  # Changed from 'data' to 'results' to match DRF convention
        })
    
    except ValueError as e:
        return Response({
            'status': 'error',
            'message': 'Invalid query parameters'
        }, status=400)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)