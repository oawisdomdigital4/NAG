

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Course, CourseModule, CourseReview, Enrollment,
    Lesson, QuizQuestion, QuizSubmission, AssignmentSubmission
)
from .serializers import (
    CourseSerializer, CourseModuleSerializer, CourseReviewSerializer, EnrollmentSerializer,
    LessonSerializer, QuizQuestionSerializer, QuizQuestionFullSerializer,
    QuizSubmissionSerializer, AssignmentSubmissionSerializer
)
from .permissions import IsFacilitator
from .grading import QuizAutoGrader, AssignmentAutoGrader, ProgressTracker
import os
from django.conf import settings

class CourseViewSet(viewsets.ModelViewSet):
	lookup_field = "slug"
	serializer_class = CourseSerializer
	# Default: allow read-only to everyone, require auth for unsafe methods
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
	filterset_fields = ["is_featured", "category", "level", "format"]
	ordering_fields = ["created_at", "price", "enrollments_count"]
	search_fields = ["title", "short_description", "full_description"]

	def get_parsers(self):
		"""Override to support both JSON and multipart form data"""
		if self.request.method in ['POST', 'PUT', 'PATCH']:
			# Support both multipart (for files) and JSON
			return [MultiPartParser(), FormParser(), JSONParser()]
		return [JSONParser()]

	def get_queryset(self):
		from django.db.models import Count
		qs = Course.objects.all().annotate(enrollments_count=Count('enrollments'))
		ordering = self.request.query_params.get('ordering')
		if ordering:
			# Support ordering by enrollments_count
			if 'enrollments_count' in ordering:
				qs = qs.order_by(ordering)

		# Accept both 'format' and 'course_format' query params. Some clients
		# (or intermediate tools) may reserve the 'format' query param for
		# content-negotiation which can lead to unexpected routing issues. To be
		# robust, support 'course_format' as an alias and also apply the normal
		# 'format' filter if present.
		course_format = self.request.query_params.get('course_format') or self.request.query_params.get('format')
		if course_format:
			qs = qs.filter(format=course_format)

		return qs

	def perform_create(self, serializer):
		# Set the facilitator to the authenticated user when creating a course
		instance = serializer.save(facilitator=self.request.user)
		
		# Attach files if provided
		thumbnail_file = self.request.FILES.get('thumbnail')
		preview_video_file = self.request.FILES.get('preview_video')
		
		if thumbnail_file or preview_video_file:
			if thumbnail_file:
				instance.thumbnail = thumbnail_file
			if preview_video_file:
				instance.preview_video = preview_video_file
			instance.save()

	def perform_update(self, serializer):
		# Save the instance with updated fields
		instance = serializer.save()

		# Attach files if provided, or accept URL fields and remove uploaded files
		thumbnail_file = self.request.FILES.get('thumbnail')
		preview_video_file = self.request.FILES.get('preview_video')
		# DRF's request.data supports .get()
		thumbnail_url = self.request.data.get('thumbnail_url') if hasattr(self.request, 'data') else None
		preview_video_url = self.request.data.get('preview_video_url') if hasattr(self.request, 'data') else None

		# Handle thumbnail: prefer file upload. If a URL is provided (even when a file exists),
		# use the URL and remove the uploaded file so the URL replaces the file.
		if thumbnail_file:
			# new file uploaded -> use it and clear any thumbnail_url
			instance.thumbnail = thumbnail_file
			instance.thumbnail_url = ''
		elif thumbnail_url is not None:
			# URL provided (could be empty string to clear)
			if thumbnail_url == '':
				# clear both file and url
				if instance.thumbnail:
					try:
						instance.thumbnail.delete(save=False)
					except Exception:
						pass
					instance.thumbnail = None
				instance.thumbnail_url = ''
			else:
				# remove existing uploaded file (if any) and store URL
				if instance.thumbnail:
					try:
						instance.thumbnail.delete(save=False)
					except Exception:
						pass
					instance.thumbnail = None
				instance.thumbnail_url = thumbnail_url

		# Handle preview video similarly
		if preview_video_file:
			instance.preview_video = preview_video_file
			instance.preview_video_url = ''
		elif preview_video_url is not None:
			if preview_video_url == '':
				if instance.preview_video:
					try:
						instance.preview_video.delete(save=False)
					except Exception:
						pass
					instance.preview_video = None
				instance.preview_video_url = ''
			else:
				if instance.preview_video:
					try:
						instance.preview_video.delete(save=False)
					except Exception:
						pass
					instance.preview_video = None
				instance.preview_video_url = preview_video_url

		# Save any changes made above
		instance.save()

	def create(self, request, *args, **kwargs):
		"""Override create to handle file uploads - parent calls perform_create"""
		return super().create(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		"""Override update to handle file uploads - parent calls perform_update"""
		return super().update(request, *args, **kwargs)

	def get_permissions(self):
		# For create action, require the user to be a facilitator
		if self.action == 'create':
			return [IsFacilitator()]
		# For update/destroy, ensure the user owns the course
		if self.action in ('update', 'partial_update', 'destroy'):
			from .permissions import IsCourseOwner
			return [permissions.IsAuthenticated(), IsCourseOwner()]
		# For enrollment-related actions, require authentication
		if self.action in ('enroll', 'my_enrollments', 'my_students', 'update_progress', 'unenroll'):
			return [permissions.IsAuthenticated()]
		return [perm() for perm in self.permission_classes]

	@action(detail=False, methods=['get'])
	def mine(self, request):
		"""Return courses owned by the authenticated user (facilitator)."""
		qs = self.get_queryset().filter(facilitator=request.user)
		page = self.paginate_queryset(qs)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = self.get_serializer(qs, many=True)
		return Response(serializer.data)
	
	@action(detail=True, methods=['get'])
	def validate_enrollment(self, request, slug=None):
		"""Validate if user can enroll in course and get payment info"""
		try:
			from .payment_service import CoursePaymentService
			
			course = self.get_object()
			
			# Validate enrollment
			validation = CoursePaymentService.validate_enrollment_request(request.user, course)
			
			# Get user balance if authenticated
			user_balance = 0
			if request.user.is_authenticated:
				try:
					user_balance = float(request.user.userprofile.balance)
				except:
					user_balance = 0
			
			return Response({
				'course_id': course.id,
				'course_title': course.title,
				'course_price': float(course.price),
				'is_free': float(course.price) == 0,
				'user_balance': user_balance,
				'validation': validation,
				'can_enroll': validation['valid']
			})
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=['post'])
	def enroll(self, request, slug=None):
		"""Enroll the authenticated user in the course with payment processing."""
		try:
			from .payment_service import CoursePaymentService
			
			course = self.get_object()
			
			# Validate enrollment request
			validation = CoursePaymentService.validate_enrollment_request(request.user, course)
			if not validation['valid']:
				return Response(
					{
						'success': False,
						'error': 'Enrollment validation failed',
						'details': validation['errors'],
						'warnings': validation['warnings']
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# Process payment if course is paid
			if float(course.price) > 0:
				payment_result = CoursePaymentService.process_enrollment_payment(request.user, course)
				if not payment_result['success']:
					return Response(
						{
							'success': False,
							'error': payment_result['reason'],
							'details': payment_result.get('error')
						},
						status=status.HTTP_400_BAD_REQUEST
					)
			
			# Create enrollment
			enrollment = Enrollment.objects.create(user=request.user, course=course)
			
			# Send notification to facilitator
			try:
				from notifications.models import Notification
				message = f'{request.user.get_full_name() or request.user.username} enrolled in your course "{course.title}"'
				if float(course.price) > 0:
					message += f' and paid ${float(course.price):.2f}'
				
				Notification.objects.create(
					user=course.facilitator,
					type='enrollment',
					category='course',
					title=f'New enrollment in {course.title}',
					message=message,
					action_url=f'/dashboard/facilitator/courses/{course.id}',
					metadata={
						'student_id': request.user.id,
						'student_name': request.user.get_full_name() or request.user.username,
						'course_id': course.id,
						'course_title': course.title
					}
				)
			except Exception as e:
				print(f"Failed to send notification: {str(e)}")
			
			serializer = EnrollmentSerializer(enrollment)
			response_data = serializer.data
			response_data['success'] = True
			
			# Include payment info if applicable
			if float(course.price) > 0:
				response_data['payment'] = {
					'amount_charged': payment_result.get('amount_charged'),
					'student_balance': payment_result.get('student_new_balance'),
					'payment_id': payment_result.get('payment_id')
				}
			
			return Response(response_data, status=status.HTTP_201_CREATED)
		except Exception as e:
			return Response(
				{
					'success': False,
					'error': str(e)
				},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

	@action(detail=False, methods=['get'])
	def my_enrollments(self, request):
		"""Return all courses the authenticated user is enrolled in."""
		enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__facilitator')
		
		page = self.paginate_queryset(enrollments)
		if page is not None:
			serializer = EnrollmentSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		
		serializer = EnrollmentSerializer(enrollments, many=True)
		return Response(serializer.data)
	
	@action(detail=True, methods=['post'])
	def unenroll(self, request, slug=None):
		"""Unenroll user from course and process refund if applicable."""
		try:
			from .payment_service import CoursePaymentService
			
			course = self.get_object()
			
			# Get enrollment
			try:
				enrollment = Enrollment.objects.get(user=request.user, course=course)
			except Enrollment.DoesNotExist:
				return Response(
					{'error': 'You are not enrolled in this course'},
					status=status.HTTP_404_NOT_FOUND
				)
			
			# Process refund if course is paid
			if float(course.price) > 0:
				refund_result = CoursePaymentService.refund_enrollment(enrollment)
				if not refund_result['success']:
					return Response(
						{
							'error': refund_result['reason'],
							'details': refund_result.get('error')
						},
						status=status.HTTP_400_BAD_REQUEST
					)
			
			# Delete enrollment
			enrollment.delete()
			
			return Response(
				{
					'success': True,
					'message': 'Successfully unenrolled from course',
					'refund': refund_result if float(course.price) > 0 else None
				},
				status=status.HTTP_200_OK
			)
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=['get'])
	def my_students(self, request):
		"""Return all students enrolled in the facilitator's courses."""
		if not hasattr(request.user, 'profile') or request.user.role != 'facilitator':
			return Response(
				{'error': 'Only facilitators can view their students'},
				status=status.HTTP_403_FORBIDDEN
			)
		
		# Get all enrollments in courses owned by this facilitator
		# Use values_list to get unique users, then fetch their enrollments
		from django.db.models import OuterRef, Exists
		
		enrollments = Enrollment.objects.filter(
			course__facilitator=request.user
		).select_related('user', 'course')
		
		page = self.paginate_queryset(enrollments)
		if page is not None:
			serializer = EnrollmentSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		
		serializer = EnrollmentSerializer(enrollments, many=True)
		return Response(serializer.data)

	@action(detail=False, methods=['post'])
	def update_progress(self, request):
		"""Update enrollment progress."""
		try:
			course_id = request.data.get('course_id')
			progress = request.data.get('progress', 0)
			
			enrollment = Enrollment.objects.get(user=request.user, course_id=course_id)
			enrollment.progress = min(max(progress, 0), 100)  # Clamp between 0-100
			enrollment.save()
			
			serializer = EnrollmentSerializer(enrollment)
			return Response(serializer.data)
		except Enrollment.DoesNotExist:
			return Response(
				{'error': 'Enrollment not found'},
				status=status.HTTP_404_NOT_FOUND
			)
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=['post'])
	def unenroll(self, request):
		"""Unenroll the user from a course."""
		try:
			course_id = request.data.get('course_id')
			enrollment = Enrollment.objects.get(user=request.user, course_id=course_id)
			enrollment.delete()
			return Response({'success': 'Unenrolled successfully'})
		except Enrollment.DoesNotExist:
			return Response(
				{'error': 'Enrollment not found'},
				status=status.HTTP_404_NOT_FOUND
			)
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=['post'], parser_classes=(MultiPartParser, FormParser))
	def upload_media(self, request):
		"""Upload media files (thumbnail, video) and return their URLs."""
		file = request.FILES.get('file')
		file_type = request.data.get('type')  # 'thumbnail' or 'preview_video'
		course_id = request.data.get('course_id')  # Optional: to attach to a course
		
		if not file:
			return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
		
		if not file_type or file_type not in ['thumbnail', 'preview_video']:
			return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Validate file size (5MB for images, 100MB for videos)
		max_size = 5 * 1024 * 1024 if file_type == 'thumbnail' else 100 * 1024 * 1024
		if file.size > max_size:
			return Response({'error': f'File too large. Max size: {max_size // (1024*1024)}MB'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Validate file type
		if file_type == 'thumbnail':
			if not file.content_type.startswith('image/'):
				return Response({'error': 'File must be an image'}, status=status.HTTP_400_BAD_REQUEST)
		else:  # preview_video
			if not file.content_type.startswith('video/'):
				return Response({'error': 'File must be a video'}, status=status.HTTP_400_BAD_REQUEST)
		
		try:
			# If course_id provided, attach file to course
			if course_id:
				try:
					course = Course.objects.get(id=course_id)
					if file_type == 'thumbnail':
						course.thumbnail = file
						course.save()
						file_url = course.thumbnail.url
					else:  # preview_video
						course.preview_video = file
						course.save()
						file_url = course.preview_video.url
				except Course.DoesNotExist:
					return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
			else:
				# Just return the file path for later use
				directory = 'course_thumbnails' if file_type == 'thumbnail' else 'course_previews'
				import uuid
				ext = os.path.splitext(file.name)[1]
				filename = f"{uuid.uuid4()}{ext}"
				file_path = os.path.join(directory, filename)
				
				# Create directory if it doesn't exist
				upload_dir = os.path.join(settings.MEDIA_ROOT, directory)
				os.makedirs(upload_dir, exist_ok=True)
				
				# Save file
				full_path = os.path.join(settings.MEDIA_ROOT, file_path)
				with open(full_path, 'wb+') as destination:
					for chunk in file.chunks():
						destination.write(chunk)
				
				file_url = f"{settings.MEDIA_URL}{file_path}"
			
			return Response({
				'url': file_url,
				'file_type': file_type,
				'filename': file.name
			}, status=status.HTTP_201_CREATED)
		except Exception as e:
			return Response({'error': f'File upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CourseModuleViewSet(viewsets.ModelViewSet):
	queryset = CourseModule.objects.all()
	serializer_class = CourseModuleSerializer
	permission_classes = [permissions.AllowAny]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ["course"]

class CourseReviewViewSet(viewsets.ModelViewSet):
	queryset = CourseReview.objects.all()
	serializer_class = CourseReviewSerializer
	permission_classes = [permissions.AllowAny]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ["course"]


class LessonViewSet(viewsets.ModelViewSet):
	"""API endpoints for course lessons"""
	queryset = Lesson.objects.all()
	serializer_class = LessonSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
	filterset_fields = ["module", "lesson_type"]
	ordering_fields = ["order", "created_at"]
	ordering = ["order"]
	
	def get_permissions(self):
		"""Allow read-only for everyone, require facilitator for create/update"""
		if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated(), IsFacilitator()]
	
	def perform_create(self, serializer):
		"""Ensure facilitator owns the course"""
		lesson = serializer.save()
		module = lesson.module
		if module.course.facilitator != self.request.user:
			lesson.delete()
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
	
	@action(detail=True, methods=['post'])
	def add_question(self, request, pk=None):
		"""Add a quiz question to this lesson"""
		lesson = self.get_object()
		if lesson.lesson_type != 'quiz':
			return Response({'error': 'Can only add questions to quiz lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		question_data = request.data
		question = QuizQuestion.objects.create(
			lesson=lesson,
			question_text=question_data.get('question_text'),
			option_a=question_data.get('option_a'),
			option_b=question_data.get('option_b'),
			option_c=question_data.get('option_c'),
			option_d=question_data.get('option_d'),
			correct_option=question_data.get('correct_option').lower()
		)
		return Response(QuizQuestionFullSerializer(question).data, status=status.HTTP_201_CREATED)
	
	@action(detail=True, methods=['get'])
	def questions(self, request, pk=None):
		"""Get all questions for a quiz lesson"""
		lesson = self.get_object()
		if lesson.lesson_type != 'quiz':
			return Response({'error': 'Can only get questions from quiz lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Check if user is the facilitator (show full answers) or student (hide answers)
		is_instructor = lesson.module.course.facilitator == request.user
		
		questions = lesson.questions.all()
		if is_instructor:
			serializer = QuizQuestionFullSerializer(questions, many=True)
		else:
			serializer = QuizQuestionSerializer(questions, many=True)
		
		return Response(serializer.data)


class QuizSubmissionViewSet(viewsets.ModelViewSet):
	"""API endpoints for quiz submissions"""
	queryset = QuizSubmission.objects.all()
	serializer_class = QuizSubmissionSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
	filterset_fields = ["enrollment", "lesson"]
	ordering = ["-submitted_at"]
	
	def get_queryset(self):
		"""Only return submissions for current user or if user is facilitator"""
		user = self.request.user
		qs = QuizSubmission.objects.all()
		
		if not user.is_staff:
			# Students can only see their own submissions
			qs = qs.filter(enrollment__user=user)
		
		return qs
	
	@action(detail=False, methods=['post'])
	def submit(self, request):
		"""Submit a quiz attempt"""
		enrollment_id = request.data.get('enrollment_id')
		lesson_id = request.data.get('lesson_id')
		answers = request.data.get('answers', {})
		
		try:
			enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
			lesson = Lesson.objects.get(id=lesson_id, lesson_type='quiz')
		except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
			return Response({'error': 'Invalid enrollment or lesson'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Create submission
		submission = QuizSubmission.objects.create(
			enrollment=enrollment,
			lesson=lesson,
			answers=answers
		)
		
		# Auto-grade
		score = QuizAutoGrader.grade_quiz(submission)
		passed = QuizAutoGrader.passes_quiz(submission)
		
		return Response({
			'id': submission.id,
			'score': score,
			'passed': passed,
			'passing_score': lesson.passing_score or 70
		}, status=status.HTTP_201_CREATED)
	
	@action(detail=True, methods=['get'])
	def grade(self, request, pk=None):
		"""Get grading details for a submission (instructor only)"""
		submission = self.get_object()
		
		# Check authorization
		if submission.lesson.module.course.facilitator != request.user and not request.user.is_staff:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		questions = submission.lesson.questions.all()
		grading_details = []
		
		for question in questions:
			student_answer = submission.answers.get(str(question.id))
			is_correct = student_answer and student_answer.lower() == question.correct_option.lower()
			
			grading_details.append({
				'question_id': question.id,
				'question_text': question.question_text,
				'student_answer': student_answer,
				'correct_answer': question.correct_option,
				'is_correct': is_correct,
				'options': {
					'a': question.option_a,
					'b': question.option_b,
					'c': question.option_c,
					'd': question.option_d
				}
			})
		
		return Response({
			'submission_id': submission.id,
			'score': submission.score,
			'passed': submission.score >= (submission.lesson.passing_score or 70),
			'grading_details': grading_details
		})
	
	@action(detail=False, methods=['get'])
	def retry_status(self, request):
		"""Check if student can retry a quiz"""
		from .quiz_retry import QuizRetryManager
		
		enrollment_id = request.query_params.get('enrollment_id')
		lesson_id = request.query_params.get('lesson_id')
		
		try:
			enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
			lesson = Lesson.objects.get(id=lesson_id, lesson_type='quiz')
		except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
			return Response({'error': 'Invalid enrollment or lesson'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Check retry eligibility
		retry_info = QuizRetryManager.can_retake(enrollment, lesson)
		history = QuizRetryManager.get_quiz_history(enrollment, lesson)
		recommendations = QuizRetryManager.get_retry_recommendations(enrollment, lesson)
		
		return Response({
			'can_retake': retry_info['can_retake'],
			'reason': retry_info['reason'],
			'attempt_count': retry_info.get('attempt_count', 0),
			'max_attempts': retry_info.get('max_attempts', 3),
			'history': history,
			'recommendations': recommendations['recommendations']
		})
	
	@action(detail=False, methods=['get'])
	def history(self, request):
		"""Get complete quiz attempt history for a lesson"""
		from .quiz_retry import QuizRetryManager
		
		enrollment_id = request.query_params.get('enrollment_id')
		lesson_id = request.query_params.get('lesson_id')
		
		try:
			enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
			lesson = Lesson.objects.get(id=lesson_id, lesson_type='quiz')
		except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
			return Response({'error': 'Invalid enrollment or lesson'}, status=status.HTTP_400_BAD_REQUEST)
		
		history = QuizRetryManager.get_quiz_history(enrollment, lesson)
		best_attempt = QuizRetryManager.get_best_attempt(enrollment, lesson)
		
		return Response({
			'history': history,
			'best_attempt': best_attempt
		})
	
	@action(detail=False, methods=['get'])
	def stats(self, request):
		"""Get quiz statistics for a student across all lessons"""
		from .quiz_retry import QuizRetryManager
		
		enrollment_id = request.query_params.get('enrollment_id')
		
		try:
			enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
		except Enrollment.DoesNotExist:
			return Response({'error': 'Invalid enrollment'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Get all quiz submissions
		submissions = QuizSubmission.objects.filter(
			enrollment=enrollment,
			graded=True
		)
		
		if not submissions.exists():
			return Response({
				'total_attempts': 0,
				'average_score': 0,
				'best_score': 0,
				'lessons_passed': 0
			})
		
		scores = [s.score for s in submissions]
		
		return Response({
			'total_attempts': len(scores),
			'average_score': round(sum(scores) / len(scores), 2),
			'best_score': max(scores),
			'worst_score': min(scores),
			'lessons_passed': sum(1 for s in submissions if s.score >= (s.lesson.passing_score or 70)),
			'total_lessons': submissions.values('lesson').distinct().count()
		})


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
	"""API endpoints for assignment submissions"""
	queryset = AssignmentSubmission.objects.all()
	serializer_class = AssignmentSubmissionSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
	filterset_fields = ["enrollment", "lesson"]
	ordering = ["-submitted_at"]
	
	def get_queryset(self):
		"""Only return submissions for current user or if user is facilitator"""
		user = self.request.user
		qs = AssignmentSubmission.objects.all()
		
		if not user.is_staff:
			# Students can only see their own submissions
			qs = qs.filter(enrollment__user=user)
		
		return qs
	
	@action(detail=False, methods=['post'])
	def submit(self, request):
		"""Submit an assignment"""
		enrollment_id = request.data.get('enrollment_id')
		lesson_id = request.data.get('lesson_id')
		content = request.data.get('content', '')
		
		try:
			enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
			lesson = Lesson.objects.get(id=lesson_id, lesson_type='assignment')
		except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
			return Response({'error': 'Invalid enrollment or lesson'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Create submission
		submission = AssignmentSubmission.objects.create(
			enrollment=enrollment,
			lesson=lesson,
			content=content
		)
		
		# Auto-grade
		score = AssignmentAutoGrader.grade_assignment(submission)
		
		return Response({
			'id': submission.id,
			'score': score,
			'graded': True
		}, status=status.HTTP_201_CREATED)
	
	@action(detail=True, methods=['post'])
	def grade_manual(self, request, pk=None):
		"""Manually grade an assignment (instructor only)"""
		submission = self.get_object()
		
		# Check authorization
		if submission.lesson.module.course.facilitator != request.user and not request.user.is_staff:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		score = request.data.get('score')
		if score is None or not isinstance(score, (int, float)):
			return Response({'error': 'Invalid score'}, status=status.HTTP_400_BAD_REQUEST)
		
		AssignmentAutoGrader.manual_grade_assignment(submission, int(score))
		
		return Response({
			'id': submission.id,
			'score': submission.score,
			'graded': True,
			'auto_graded': submission.auto_graded
		})


class ProgressReportViewSet(viewsets.ReadOnlyModelViewSet):
	"""API endpoints for student progress and reports"""
	queryset = Enrollment.objects.all()
	serializer_class = EnrollmentSerializer
	permission_classes = [permissions.IsAuthenticated]
	
	def get_queryset(self):
		"""Only return enrollments for current user or if user is facilitator"""
		user = self.request.user
		qs = Enrollment.objects.all()
		
		if not user.is_staff:
			qs = qs.filter(user=user)
		
		return qs
	
	@action(detail=True, methods=['get'])
	def progress(self, request, pk=None):
		"""Get detailed progress report for an enrollment"""
		enrollment = self.get_object()
		
		# Check authorization
		if enrollment.user != request.user and enrollment.course.facilitator != request.user and not request.user.is_staff:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		report = ProgressTracker.get_student_report(enrollment)
		return Response(report)
	
	@action(detail=True, methods=['get'])
	def summary(self, request, pk=None):
		"""Get quick progress summary"""
		enrollment = self.get_object()
		
		# Check authorization
		if enrollment.user != request.user and enrollment.course.facilitator != request.user and not request.user.is_staff:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		progress = ProgressTracker.calculate_lesson_progress(enrollment)
		return Response(progress)
