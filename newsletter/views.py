from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import NewsletterSubscriberSerializer
from .models import NewsletterSubscriber

@api_view(['POST'])
def subscribe_newsletter(request):
    serializer = NewsletterSubscriberSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Thank you for subscribing to our newsletter!'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            if 'unique constraint' in str(e).lower():
                return Response({
                    'status': 'error',
                    'message': 'You are already subscribed to our newsletter.'
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': 'error',
                'message': 'An error occurred. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        'status': 'error',
        'message': 'Please provide a valid email address.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
