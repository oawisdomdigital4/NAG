from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from community.models import UserActivity

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