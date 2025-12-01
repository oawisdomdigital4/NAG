"""
Course Enrollment Payment Service
Handles wallet-based payments for course enrollments
"""

from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from accounts.models import User, UserProfile
from payments.models import Payment
from courses.models import Enrollment, Course


class CoursePaymentService:
    """Handle course enrollment payments and wallet transactions"""
    
    @staticmethod
    def can_afford_course(user: User, course: Course) -> dict:
        """Check if user has sufficient wallet balance for course"""
        try:
            if user.is_anonymous:
                return {
                    'can_afford': False,
                    'error': 'User not authenticated',
                    'message': 'You must be logged in to enroll in paid courses'
                }
            
            user_profile = user.profile
            course_price = Decimal(str(course.price))
            # Use available_balance from three-balance system
            user_balance = Decimal(str(user_profile.available_balance))
            
            can_afford = user_balance >= course_price
            
            return {
                'can_afford': can_afford,
                'user_balance': float(user_balance),
                'course_price': float(course_price),
                'difference': float(user_balance - course_price),
                'message': 'Sufficient balance' if can_afford else f'Insufficient balance. Need ${course_price - user_balance:.2f} more'
            }
        except Exception as e:
            return {
                'can_afford': False,
                'error': str(e),
                'message': 'Error checking balance'
            }
    
    @staticmethod
    def process_enrollment_payment(user: User, course: Course) -> dict:
        """
        Process payment for course enrollment.
        Deducts from student wallet (available_balance) and adds to instructor's pending balance.
        Instructor funds will move from pending to available after 2-5 day processing period.
        """
        try:
            # Check if user can afford
            affordability = CoursePaymentService.can_afford_course(user, course)
            if not affordability['can_afford']:
                return {
                    'success': False,
                    'reason': affordability.get('message', 'Cannot afford course'),
                    'error': affordability.get('error')
                }
            
            # Use atomic transaction for data consistency
            with transaction.atomic():
                user_profile = user.profile
                facilitator_profile = course.facilitator.profile
                
                course_price = Decimal(str(course.price))
                
                # Deduct from student wallet (available_balance)
                user_profile.available_balance -= course_price
                user_profile.save(update_fields=['available_balance'])
                
                # Add to instructor's pending balance (will move to available after 2-5 days)
                facilitator_profile.pending_balance += course_price
                # Also track in earning_balance for record keeping
                facilitator_profile.earning_balance += course_price
                facilitator_profile.save(update_fields=['pending_balance', 'earning_balance'])
                
                # Create payment record for student
                payment = Payment.objects.create(
                    user=user,
                    amount=course_price,
                    provider='wallet',
                    status='completed',
                    transaction_type='course_enrollment',
                    currency='USD',
                    metadata={
                        'course_id': course.id,
                        'course_title': course.title,
                        'facilitator_id': course.facilitator.id,
                        'facilitator_name': course.facilitator.get_full_name()
                    }
                )
                
                # Create payment record for instructor
                instructor_payment = Payment.objects.create(
                    user=course.facilitator,
                    amount=course_price,
                    provider='wallet',
                    status='pending',
                    transaction_type='course_revenue',
                    currency='USD',
                    metadata={
                        'course_id': course.id,
                        'course_title': course.title,
                        'student_id': user.id,
                        'student_name': user.get_full_name(),
                        'processing_until': (timezone.now() + timezone.timedelta(days=2)).isoformat()
                    }
                )
                
                return {
                    'success': True,
                    'reason': 'Payment processed successfully',
                    'payment_id': payment.id,
                    'amount_charged': float(course_price),
                    'student_new_balance': float(user_profile.available_balance),
                    'instructor_pending_balance': float(facilitator_profile.pending_balance),
                    'processing_note': 'Instructor funds will be available in 2-5 business days'
                }
        
        except Exception as e:
            return {
                'success': False,
                'reason': 'Payment processing failed',
                'error': str(e)
            }
    
    @staticmethod
    def refund_enrollment(enrollment: Enrollment) -> dict:
        """
        Refund course payment and remove enrollment.
        Used when student unenrolls.
        Refunds go back to student's available_balance.
        Deducts from instructor's pending or available balance depending on status.
        """
        try:
            with transaction.atomic():
                user = enrollment.user
                course = enrollment.course
                
                user_profile = user.profile
                facilitator_profile = course.facilitator.profile
                
                course_price = Decimal(str(course.price))
                
                # Refund to student wallet (available_balance)
                user_profile.available_balance += course_price
                user_profile.save(update_fields=['available_balance'])
                
                # Deduct from instructor wallet
                # If funds are still pending, deduct from pending_balance
                if facilitator_profile.pending_balance >= course_price:
                    facilitator_profile.pending_balance -= course_price
                else:
                    # Otherwise deduct from available_balance
                    facilitator_profile.available_balance -= course_price
                
                facilitator_profile.save(update_fields=['pending_balance', 'available_balance'])
                
                # Create refund payment records
                Payment.objects.create(
                    user=user,
                    amount=course_price,
                    provider='wallet',
                    status='refunded',
                    transaction_type='course_refund',
                    currency='USD',
                    metadata={
                        'course_id': course.id,
                        'course_title': course.title,
                        'original_enrollment_id': enrollment.id
                    }
                )
                
                return {
                    'success': True,
                    'reason': 'Refund processed successfully',
                    'amount_refunded': float(course_price),
                    'new_balance': float(user_profile.available_balance)
                }
        
        except Exception as e:
            return {
                'success': False,
                'reason': 'Refund processing failed',
                'error': str(e)
            }
    
    @staticmethod
    def get_payment_history(user: User, course: Course = None) -> dict:
        """Get payment history for a user"""
        payments = Payment.objects.filter(
            user=user,
            transaction_type__in=['course_enrollment', 'course_refund']
        ).order_by('-created_at')
        
        if course:
            payments = payments.filter(metadata__course_id=course.id)
        
        return {
            'total_payments': payments.count(),
            'payments': [
                {
                    'id': p.id,
                    'amount': float(p.amount),
                    'status': p.status,
                    'type': p.transaction_type,
                    'course': p.metadata.get('course_title', 'Unknown'),
                    'date': p.created_at.isoformat()
                }
                for p in payments[:20]
            ]
        }
    
    @staticmethod
    def validate_enrollment_request(user: User, course: Course) -> dict:
        """
        Validate if enrollment request is valid.
        Checks: free vs paid, already enrolled, course exists, etc.
        """
        errors = []
        warnings = []
        
        # If user is anonymous, add error
        if user.is_anonymous:
            errors.append('User must be authenticated to enroll')
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=user, course=course).exists():
            errors.append('Already enrolled in this course')
        
        # Check if course is available
        if not course.is_published:
            errors.append('Course is not available for enrollment')
        
        # Check if facilitator is active
        if not course.facilitator.is_active:
            errors.append('Course instructor is not available')
        
        # For paid courses, check wallet balance
        if float(course.price) > 0:
            affordability = CoursePaymentService.can_afford_course(user, course)
            if not affordability['can_afford']:
                errors.append(f"Insufficient wallet balance. Need ${float(course.price):.2f}")
            else:
                warnings.append(f"You will be charged ${float(course.price):.2f}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'is_free_course': float(course.price) == 0
        }
