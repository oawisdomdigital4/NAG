"""
OTP Views for User Signup and Verification
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from accounts.models import OTPVerification
from accounts.email_tasks import send_otp_email
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def send_otp_async(otp_id):
    """Send OTP email - handles both Celery and sync execution"""
    try:
        # Check if send_otp_email is a Celery task
        if hasattr(send_otp_email, 'delay'):
            # Use Celery async
            send_otp_email.delay(otp_id)
        else:
            # Call directly (sync)
            send_otp_email(otp_id)
    except Exception as e:
        logger.error(f'Error sending OTP email: {str(e)}')


class OTPViewSet(viewsets.ViewSet):
    """
    ViewSet for OTP operations:
    - Generate and send OTP during signup
    - Verify OTP
    - Resend OTP
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        """
        Send OTP to email address
        
        POST /api/otp/send_otp/
        {
            "email": "user@example.com"
        }
        """
        email = request.data.get('email', '').lower().strip()
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        user_exists = User.objects.filter(email=email).exists()
        
        try:
            # Create OTP
            otp = OTPVerification.create_otp(
                email=email,
                otp_type='signup'
            )
            
            # Send OTP via email (handles both Celery and sync)
            send_otp_async(otp.id)
            
            return Response({
                'message': f'OTP sent to {email}',
                'user_exists': user_exists,
                'otp_id': otp.id,
                'expires_in_minutes': 10
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Error sending OTP: {str(e)}')
            return Response(
                {'error': 'Failed to send OTP'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """
        Verify OTP code
        
        POST /api/otp/verify_otp/
        {
            "email": "user@example.com",
            "otp_code": "123456"
        }
        """
        email = request.data.get('email', '').lower().strip()
        otp_code = request.data.get('otp_code', '').strip()
        
        if not email or not otp_code:
            return Response(
                {'error': 'Email and OTP code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the latest OTP for this email
            otp = OTPVerification.objects.filter(
                email=email,
                otp_type='signup'
            ).latest('created_at')
            
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'No OTP found for this email. Please request a new one.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify OTP
        is_valid, message = otp.verify_otp(otp_code)
        
        if is_valid:
            return Response({
                'message': 'OTP verified successfully',
                'verified': True,
                'email': email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': message,
                'verified': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def resend_otp(self, request):
        """
        Resend OTP to email address
        
        POST /api/otp/resend_otp/
        {
            "email": "user@example.com"
        }
        """
        email = request.data.get('email', '').lower().strip()
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the latest OTP for this email
            otp = OTPVerification.objects.filter(
                email=email,
                otp_type='signup'
            ).latest('created_at')
            
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'No OTP found for this email. Please request a new one.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Resend OTP
            otp.resend_otp()
            send_otp_async(otp.id)
            
            return Response({
                'message': f'OTP resent to {email}',
                'expires_in_minutes': 10
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Error resending OTP: {str(e)}')
            return Response(
                {'error': 'Failed to resend OTP'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
