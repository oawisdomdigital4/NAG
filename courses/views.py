

from rest_framework import viewsets, permissions, filters, status, serializers
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
    LessonSerializer, LessonInstructorSerializer, QuizQuestionSerializer, QuizQuestionFullSerializer,
    QuizSubmissionSerializer, AssignmentSubmissionSerializer, CourseInstructorSerializer,
    CourseModuleInstructorSerializer
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
	filterset_fields = ["is_featured", "category", "level", "format", "status"]
	ordering_fields = ["created_at", "price", "enrollments_count"]
	search_fields = ["title", "short_description", "full_description"]

	def get_serializer_class(self):
		"""Use CourseInstructorSerializer for instructors viewing their own course"""
		# Check if this is a retrieve action and the user is the facilitator
		if self.action == 'retrieve' and self.request.user.is_authenticated:
			try:
				course = self.get_object()
				if course.facilitator == self.request.user:
					from .serializers import CourseInstructorSerializer
					return CourseInstructorSerializer
			except Exception:
				pass
		return self.serializer_class

	def get_parsers(self):
		"""Override to support both JSON and multipart form data"""
		if self.request.method in ['POST', 'PUT', 'PATCH']:
			# Support both multipart (for files) and JSON
			return [MultiPartParser(), FormParser(), JSONParser()]
		return [JSONParser()]

	def get_queryset(self):
		from django.db.models import Count, Q
		qs = Course.objects.all().annotate(enrollments_count=Count('enrollments'))
		
		# If no explicit status filter is provided, apply default filtering:
		# - Show published courses to everyone (public listing)
		# - Show draft courses only to the facilitator who created them (private listing)
		status_param = self.request.query_params.get('status')
		if not status_param:
			# Default behavior: show published courses + user's own draft courses
			if self.request.user.is_authenticated:
				# Show published courses + this user's draft courses
				qs = qs.filter(Q(status='published') | Q(status='draft', facilitator=self.request.user))
			else:
				# Show only published courses to anonymous users
				qs = qs.filter(status='published')
		
		ordering = self.request.query_params.get('ordering')
		if ordering:
			# Support ordering by enrollments_count
			if 'enrollments_count' in ordering:
				qs = qs.order_by(ordering)

		# Accept both 'format' and 'course_format' query params. Some clients
		# (or intermediate tools) may reserve the 'format' query param for
		# content-negotiation which can lead to unexpected routing issues. To be
		# robust, support 'course_format' as an alias and also apply the normal
		# 'filter' if present.
		course_format = self.request.query_params.get('course_format') or self.request.query_params.get('format')
		if course_format:
			qs = qs.filter(format=course_format)

		return qs

	def perform_create(self, serializer):
		from django.utils.text import slugify
		import uuid
		
		# Auto-generate slug if not provided
		title = serializer.validated_data.get('title', '')
		slug = serializer.validated_data.get('slug', '')
		
		if not slug and title:
			# Generate slug from title with a unique suffix to avoid conflicts
			base_slug = slugify(title)
			slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
		elif not slug:
			# Fallback if no title either
			slug = f"course-{uuid.uuid4().hex[:6]}"
		
		# Set defaults for optional fields
		short_description = serializer.validated_data.get('short_description', '')
		if not short_description:
			short_description = title[:100] if title else 'Untitled Course'
		
		full_description = serializer.validated_data.get('full_description', '')
		if not full_description:
			full_description = short_description
		
		# Set the facilitator to the authenticated user when creating a course
		instance = serializer.save(
			facilitator=self.request.user,
			slug=slug,
			short_description=short_description,
			full_description=full_description
		)
		
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
		try:
			qs = self.get_queryset().filter(facilitator=request.user)
			page = self.paginate_queryset(qs)
			if page is not None:
				serializer = self.get_serializer(page, many=True)
				return self.get_paginated_response(serializer.data)
			serializer = self.get_serializer(qs, many=True)
			return Response(serializer.data)
		except Exception as e:
			import traceback
			error_trace = traceback.format_exc()
			print(f"[CourseViewSet.mine] ERROR: {str(e)}")
			print(error_trace)
			return Response(
				{'error': str(e), 'detail': error_trace},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
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
					user_balance = float(request.user.userprofile.available_balance)
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
		try:
			enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__facilitator')
			
			page = self.paginate_queryset(enrollments)
			if page is not None:
				serializer = EnrollmentSerializer(page, many=True)
				return self.get_paginated_response(serializer.data)
			
			serializer = EnrollmentSerializer(enrollments, many=True)
			return Response(serializer.data)
		except Exception as e:
			import traceback
			error_trace = traceback.format_exc()
			print(f"[CourseViewSet.my_enrollments] ERROR: {str(e)}")
			print(error_trace)
			return Response(
				{'error': str(e), 'detail': error_trace},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
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
		try:
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
		except Exception as e:
			import traceback
			error_trace = traceback.format_exc()
			print(f"[CourseViewSet.my_students] ERROR: {str(e)}")
			print(error_trace)
			return Response(
				{'error': str(e), 'detail': error_trace},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

	@action(detail=False, methods=['post'])
	def update_progress(self, request):
		"""Update enrollment progress and completed lessons."""
		try:
			import json
			course_id = request.data.get('course_id')
			progress = request.data.get('progress', 0)
			completed_lessons = request.data.get('completed_lessons')  # Array of lesson IDs
			
			enrollment = Enrollment.objects.get(user=request.user, course_id=course_id)
			enrollment.progress = min(max(progress, 0), 100)  # Clamp between 0-100
			
			# Update completed lessons if provided
			if completed_lessons is not None:
				enrollment.completed_lessons = json.dumps(completed_lessons)
			
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
	
	def perform_create(self, serializer):
		"""Handle course assignment - support both direct field and query param"""
		# Check if course is in validated_data
		if 'course' not in serializer.validated_data or not serializer.validated_data['course']:
			# Try to get course from query params
			course_id = self.request.query_params.get('course')
			if course_id:
				try:
					course = Course.objects.get(id=course_id)
					serializer.validated_data['course'] = course
				except Course.DoesNotExist:
					raise serializers.ValidationError({'course': 'Course not found'})
			else:
				raise serializers.ValidationError({'course': 'Course is required'})
		
		serializer.save()

class CourseReviewViewSet(viewsets.ModelViewSet):
	queryset = CourseReview.objects.all()
	serializer_class = CourseReviewSerializer
	permission_classes = [permissions.AllowAny]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ["course"]
	
	def get_permissions(self):
		"""
		Allow everyone to read reviews.
		Only authenticated, enrolled students can create/update reviews.
		Only review author or facilitator can delete reviews.
		"""
		if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
			return [permissions.AllowAny()]
		if self.request.method in ['POST', 'PUT', 'PATCH']:
			return [permissions.IsAuthenticated()]
		if self.request.method == 'DELETE':
			return [permissions.IsAuthenticated()]
		return [permissions.AllowAny()]
	
	def perform_create(self, serializer):
		"""Automatically set the user to the authenticated user"""
		serializer.save(user=self.request.user)
	
	def perform_update(self, serializer):
		"""Only allow user to update their own review"""
		review = self.get_object()
		if review.user != self.request.user:
			return Response({'error': 'You can only edit your own reviews'}, status=status.HTTP_403_FORBIDDEN)
		serializer.save()
	
	def perform_destroy(self, instance):
		"""Only allow user to delete their own review or facilitator can delete"""
		if instance.user != self.request.user and instance.course.facilitator != self.request.user:
			return Response({'error': 'You can only delete your own reviews'}, status=status.HTTP_403_FORBIDDEN)
		instance.delete()


class LessonViewSet(viewsets.ModelViewSet):
	"""API endpoints for course lessons"""
	queryset = Lesson.objects.all()
	serializer_class = LessonSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
	filterset_fields = ["module", "lesson_type"]
	ordering_fields = ["order", "created_at"]
	ordering = ["order"]
	parser_classes = [MultiPartParser, FormParser, JSONParser]
	
	def _encode_attachment_urls(self, attachments):
		"""Return attachment URLs as-is"""
		if not attachments:
			return []
		return attachments
	
	def get_permissions(self):
		"""Allow read-only for everyone, require facilitator for create/update, but allow students for quiz actions"""
		if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
			return [permissions.AllowAny()]
		# Allow students to take quizzes and assignments
		if self.action in ['get_questions', 'submit_quiz', 'assignment_status', 'submit_assignment']:
			return [permissions.IsAuthenticated()]
		# Allow facilitators to view analytics and grade assignments (check permission in method)
		if self.action in ['quiz_analytics', 'quiz_submissions', 'assignment_submissions', 'assignment_submission_detail', 'assignment_submission_grade']:
			return [permissions.IsAuthenticated()]
		# Require facilitator for create/update/delete
		return [permissions.IsAuthenticated(), IsFacilitator()]
	
	def perform_create(self, serializer):
		"""Ensure facilitator owns the course"""
		lesson = serializer.save()
		module = lesson.module
		if module.course.facilitator != self.request.user:
			lesson.delete()
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
	
	def perform_update(self, serializer):
		"""Handle video file deletion when video fields are cleared"""
		# Get the existing lesson instance
		instance = self.get_object()
		
		# Check if video_file is being explicitly set to None/empty (deletion request)
		if 'video_file' in self.request.data and not self.request.FILES.get('video_file'):
			# User is clearing the video_file field
			data_video_file = self.request.data.get('video_file')
			if data_video_file is None or data_video_file == '' or data_video_file == 'null':
				# Delete the existing video file from storage
				if instance.video_file:
					try:
						instance.video_file.delete(save=False)
					except Exception as e:
						print(f"Warning: Failed to delete video file: {str(e)}")
		
		# Check if video_url is being cleared
		if 'video_url' in self.request.data:
			data_video_url = self.request.data.get('video_url')
			if data_video_url is None or data_video_url == '':
				# Just update the field, no file to delete for URLs
				pass
		
		# Save the updated lesson
		serializer.save()
	
	def update(self, request, *args, **kwargs):
		"""Override update to provide better error logging"""
		try:
			return super().update(request, *args, **kwargs)
		except Exception as e:
			print(f'[LessonViewSet] Update error: {str(e)}')
			print(f'[LessonViewSet] Request data: {request.data}')
			print(f'[LessonViewSet] Lesson ID: {kwargs.get("pk")}')
			raise
	
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

	@action(detail=True, methods=['post'], url_path='get-questions')
	def get_questions(self, request, pk=None):
		"""Get all quiz questions for frontend (without showing answers)"""
		print(f'[get_questions] ENDPOINT CALLED!')
		print(f'[get_questions] User: {request.user}, Authenticated: {request.user.is_authenticated}')
		print(f'[get_questions] Auth: {request.auth}')
		print(f'[get_questions] Headers: Authorization={request.headers.get("Authorization")}')
		
		lesson = self.get_object()
		
		if lesson.lesson_type != 'quiz':
			return Response({'error': 'Can only get questions from quiz lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		questions = lesson.questions.all()
		serializer = QuizQuestionSerializer(questions, many=True)
		print(f'[get_questions] Returning {questions.count()} questions')
		return Response({
			'_ok': True,
			'questions': serializer.data,
			'total_questions': questions.count(),
			'passing_score': lesson.passing_score or 70,
		})

	@action(detail=True, methods=['post'], url_path='submit-quiz')
	def submit_quiz(self, request, pk=None):
		"""Submit quiz answers and get score"""
		print(f'[submit_quiz] ENDPOINT CALLED!')
		print(f'[submit_quiz] User: {request.user}, Authenticated: {request.user.is_authenticated}')
		print(f'[submit_quiz] Lesson ID: {pk}')
		print(f'[submit_quiz] Request data: {request.data}')
		
		lesson = self.get_object()
		print(f'[submit_quiz] Lesson type: {lesson.lesson_type}, Lesson title: {lesson.title}')
		
		if lesson.lesson_type != 'quiz':
			return Response({'error': 'Can only submit quiz for quiz lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Get user's enrollment
		try:
			enrollment = Enrollment.objects.get(user=request.user, course=lesson.module.course)
			print(f'[submit_quiz] Enrollment found: {enrollment.id}')
		except Enrollment.DoesNotExist:
			print(f'[submit_quiz] Enrollment not found for user {request.user.id} and course {lesson.module.course.id}')
			return Response({'error': 'Not enrolled in this course'}, status=status.HTTP_403_FORBIDDEN)
		
		# Get answers from request
		answers = request.data.get('answers', {})
		print(f'[submit_quiz] Answers received: {answers}')
		
		if not answers:
			return Response({'error': 'No answers provided'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Calculate score
		questions = lesson.questions.all()
		print(f'[submit_quiz] Total questions: {questions.count()}')
		
		correct_count = 0
		total_count = questions.count()
		
		for question in questions:
			user_answer = answers.get(str(question.id), '').lower()
			correct_answer = question.correct_option.lower()
			is_correct = user_answer == correct_answer
			if is_correct:
				correct_count += 1
			print(f'[submit_quiz] Q{question.id}: user={user_answer}, correct={correct_answer}, match={is_correct}')
		
		score = int((correct_count / total_count) * 100) if total_count > 0 else 0
		is_passing = score >= (lesson.passing_score or 70)
		
		print(f'[submit_quiz] Score calculated: {score}% (Correct: {correct_count}/{total_count}), Passing: {is_passing}')
		
		# Create quiz submission record
		submission = QuizSubmission.objects.create(
			enrollment=enrollment,
			lesson=lesson,
			score=score,
			answers=answers,
			graded=True
		)
		
		print(f'[submit_quiz] Submission saved: {submission.id}')
		
		return Response({
			'_ok': True,
			'submission_id': submission.id,
			'score': score,
			'correct_answers': correct_count,
			'total_questions': total_count,
			'is_passing': is_passing,
			'passing_score': lesson.passing_score or 70,
			'message': 'Quiz submitted successfully'
		}, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=['get'], url_path='assignment-status')
	def assignment_status(self, request, pk=None):
		"""Get student's assignment submission status"""
		lesson = self.get_object()
		
		if lesson.lesson_type != 'assignment':
			return Response({'error': 'Can only get status for assignment lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		try:
			enrollment = Enrollment.objects.get(user=request.user, course=lesson.module.course)
		except Enrollment.DoesNotExist:
			return Response({'error': 'Not enrolled in this course'}, status=status.HTTP_403_FORBIDDEN)
		
		# Check if student has submitted this assignment - get the LATEST submission
		submission = AssignmentSubmission.objects.filter(
			enrollment=enrollment,
			lesson=lesson
		).order_by('-submitted_at').first()
		
		if submission:
			return Response({
				'_ok': True,
				'status': {
					'submitted': True,
					'submittedAt': submission.submitted_at.isoformat(),
					'content': submission.content,
					'score': submission.score if submission.graded else None,
					'feedback': getattr(submission, 'feedback', None),
					'graded': submission.graded,
					'attachments': self._encode_attachment_urls(submission.attachments or []),
				}
			})
		
		return Response({
			'_ok': True,
			'status': {
				'submitted': False,
				'graded': False,
				'attachments': [],
			}
		})

	@action(detail=True, methods=['post'], url_path='submit-assignment')
	def submit_assignment(self, request, pk=None):
		"""Submit assignment with text content and file attachments"""
		lesson = self.get_object()
		
		if lesson.lesson_type != 'assignment':
			return Response({'error': 'Can only submit assignment for assignment lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Get user's enrollment
		try:
			enrollment = Enrollment.objects.get(user=request.user, course=lesson.module.course)
		except Enrollment.DoesNotExist:
			return Response({'error': 'Not enrolled in this course'}, status=status.HTTP_403_FORBIDDEN)
		
		# Get content - try both request.data and request.POST
		content = request.data.get('content', '') or request.POST.get('content', '')
		
		if not content or not content.strip():
			# Debug: log what we're receiving
			import logging
			logger = logging.getLogger(__name__)
			logger.debug(f"Content field missing. request.data keys: {request.data.keys()}")
			logger.debug(f"request.POST keys: {request.POST.keys()}")
			logger.debug(f"request.FILES keys: {request.FILES.keys()}")
			return Response({'error': 'Assignment content is required'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Validate word count if specified
		word_count = len(content.split())
		min_words = lesson.min_word_count or 0
		max_words = lesson.max_word_count or 5000
		
		if word_count < min_words:
			return Response(
				{'error': f'Assignment must be at least {min_words} words. Current: {word_count} words'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		if word_count > max_words:
			return Response(
				{'error': f'Assignment cannot exceed {max_words} words. Current: {word_count} words'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Check file attachments if required
		files = request.FILES.getlist('attachments')
		if lesson.attachments_required and not files:
			return Response(
				{'error': 'This assignment requires file attachments'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Validate file types
		if files and lesson.file_types_allowed:
			allowed_types = lesson.file_types_allowed
			for file in files:
				ext = file.name.split('.')[-1].lower()
				if ext not in allowed_types:
					return Response(
						{'error': f'File type .{ext} not allowed. Allowed types: {", ".join(allowed_types)}'},
						status=status.HTTP_400_BAD_REQUEST
					)
		
		# Create submission
		submission = AssignmentSubmission.objects.create(
			enrollment=enrollment,
			lesson=lesson,
			content=content,
			auto_graded=lesson.auto_grade_on_submit,
			graded=False
		)
		
		# Store file attachments metadata
		attachments_data = []
		if files:
			for file in files:
				# Generate a file path and URL for storage
				from django.core.files.storage import default_storage
				import os
				
				# Create unique file path - preserve original extension
				import uuid
				file_ext = os.path.splitext(file.name)[1]
				unique_filename = f"{uuid.uuid4().hex}{file_ext}"
				file_path = f"assignments/{lesson.module.course.id}/{lesson.id}/{submission.id}/{unique_filename}"
				
				# Save file to storage in binary mode to preserve file integrity
				file.seek(0)
				saved_path = default_storage.save(file_path, file)
				
				# Get the full URL using MEDIA_URL
				full_url = f"{settings.MEDIA_URL}{saved_path}"
				
				# Store metadata with original filename for display
				attachments_data.append({
					'name': file.name,  # Keep original filename for display
					'url': full_url,
					'size': file.size,
					'type': file.content_type or 'application/octet-stream'
				})
		
		# Update submission with attachments
		if attachments_data:
			submission.attachments = attachments_data
			submission.save(update_fields=['attachments'])
		
		return Response({
			'_ok': True,
			'submission_id': submission.id,
			'message': 'Assignment submitted successfully',
			'attachments': attachments_data
		}, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=['get'], url_path='quiz-analytics')
	def quiz_analytics(self, request, pk=None):
		"""Get quiz analytics for facilitators"""
		lesson = self.get_object()
		
		# Check if facilitator
		if lesson.module.course.facilitator != request.user:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		if lesson.lesson_type != 'quiz':
			return Response({'error': 'Can only get analytics for quiz lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		# Get all submissions
		submissions = QuizSubmission.objects.filter(lesson=lesson)
		questions = lesson.questions.all()
		
		if submissions.count() == 0:
			return Response({
				'_ok': True,
				'analytics': {
					'total_submissions': 0,
					'average_score': 0,
					'pass_rate': 0,
					'fail_rate': 0,
					'highest_score': 0,
					'lowest_score': 0,
					'questions_data': []
				}
			})
		
		# Calculate basic stats
		scores = list(submissions.values_list('score', flat=True))
		passing_score = lesson.passing_score or 70
		pass_count = sum(1 for s in scores if s >= passing_score)
		
		# Calculate question statistics
		questions_data = []
		for question in questions:
			correct_count = 0
			wrong_answers = {}
			
			for submission in submissions:
				user_answer = submission.answers.get(str(question.id), '').lower()
				correct_answer = question.correct_option.lower()
				
				if user_answer == correct_answer:
					correct_count += 1
				else:
					# Track wrong answers
					wrong_answers[user_answer] = wrong_answers.get(user_answer, 0) + 1
			
			correct_percentage = (correct_count / submissions.count() * 100) if submissions.count() > 0 else 0
			most_common_wrong = max(wrong_answers.items(), key=lambda x: x[1])[0] if wrong_answers else None
			
			questions_data.append({
				'question_id': question.id,
				'question_text': question.question_text,
				'correct_percentage': correct_percentage,
				'most_common_wrong_answer': most_common_wrong
			})
		
		analytics = {
			'total_submissions': submissions.count(),
			'average_score': sum(scores) / len(scores) if scores else 0,
			'pass_rate': (pass_count / submissions.count() * 100) if submissions.count() > 0 else 0,
			'fail_rate': ((submissions.count() - pass_count) / submissions.count() * 100) if submissions.count() > 0 else 0,
			'highest_score': max(scores) if scores else 0,
			'lowest_score': min(scores) if scores else 0,
			'questions_data': questions_data
		}
		
		return Response({'_ok': True, 'analytics': analytics})

	@action(detail=True, methods=['get'], url_path='quiz-submissions')
	def quiz_submissions(self, request, pk=None):
		"""Get all quiz submissions for a quiz lesson"""
		lesson = self.get_object()
		
		# Check if facilitator
		if lesson.module.course.facilitator != request.user:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		if lesson.lesson_type != 'quiz':
			return Response({'error': 'Can only get submissions for quiz lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		submissions = QuizSubmission.objects.filter(lesson=lesson).select_related('enrollment__user')
		
		submissions_data = []
		for submission in submissions:
			user = submission.enrollment.user
			submissions_data.append({
				'student_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
				'student_email': user.email,
				'submission_date': submission.submitted_at,
				'score': submission.score,
				'is_passing': submission.score >= (lesson.passing_score or 70),
				'answers': submission.answers,
				'time_taken': 5  # Placeholder - would need to track this separately
			})
		
		return Response({'_ok': True, 'submissions': submissions_data})

	@action(detail=True, methods=['get'], url_path='assignment-submissions')
	def assignment_submissions(self, request, pk=None):
		"""Get all assignment submissions for an assignment lesson"""
		lesson = self.get_object()
		
		# Check if facilitator
		if lesson.module.course.facilitator != request.user:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		if lesson.lesson_type != 'assignment':
			return Response({'error': 'Can only get submissions for assignment lessons'}, status=status.HTTP_400_BAD_REQUEST)
		
		submissions = AssignmentSubmission.objects.filter(lesson=lesson).select_related('enrollment__user')
		
		submissions_data = []
		for submission in submissions:
			user = submission.enrollment.user
			submissions_data.append({
				'id': submission.id,
				'student_id': user.id,
				'student_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
				'student_email': user.email,
				'content': submission.content[:100] + '...' if len(submission.content) > 100 else submission.content,
				'attachments': self._encode_attachment_urls(submission.attachments or []),
				'submitted_at': submission.submitted_at,
				'score': submission.score,
				'feedback': getattr(submission, 'feedback', ''),
				'graded': submission.graded,
				'word_count': len(submission.content.split()),
				'late_submission': False  # Would need to check against due date
			})
		
		return Response({'_ok': True, 'submissions': submissions_data})

	@action(detail=True, methods=['get', 'put'], url_path='assignment-submissions/(?P<submission_id>[0-9]+)/grade')
	def assignment_submission_grade(self, request, pk=None, submission_id=None):
		"""Get or grade a specific assignment submission"""
		lesson = self.get_object()
		
		# Check if facilitator
		if lesson.module.course.facilitator != request.user:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		try:
			submission = AssignmentSubmission.objects.get(id=submission_id, lesson=lesson)
		except AssignmentSubmission.DoesNotExist:
			return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
		
		if request.method == 'GET':
			user = submission.enrollment.user
			return Response({
				'_ok': True,
				'submission': {
					'id': submission.id,
					'student_id': user.id,
					'student_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
					'student_email': user.email,
					'content': submission.content,
					'attachments': self._encode_attachment_urls(submission.attachments or []),
					'submitted_at': submission.submitted_at,
					'score': submission.score,
					'feedback': getattr(submission, 'feedback', ''),
					'graded': submission.graded,
					'word_count': len(submission.content.split()),
					'late_submission': False
				}
			})
		
		elif request.method == 'PUT':
			# Grade the submission
			score = request.data.get('score')
			feedback = request.data.get('feedback', '')
			
			if score is None:
				return Response({'error': 'Score is required'}, status=status.HTTP_400_BAD_REQUEST)
			
			submission.score = score
			submission.feedback = feedback
			submission.graded = True
			submission.save()
			
			# Send in-app and email notifications to student
			self._send_grading_notifications(submission, score, feedback, lesson)
			
			return Response({'_ok': True, 'message': 'Assignment graded successfully'})

	@action(detail=True, methods=['get', 'put'], url_path='assignment-submissions/(?P<submission_id>[0-9]+)')
	def assignment_submission_detail(self, request, pk=None, submission_id=None):
		"""Get or update a specific assignment submission"""
		lesson = self.get_object()
		
		# Check if facilitator
		if lesson.module.course.facilitator != request.user:
			return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
		
		try:
			submission = AssignmentSubmission.objects.get(id=submission_id, lesson=lesson)
		except AssignmentSubmission.DoesNotExist:
			return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
		
		if request.method == 'GET':
			user = submission.enrollment.user
			return Response({
				'_ok': True,
				'submission': {
					'id': submission.id,
					'student_id': user.id,
					'student_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
					'student_email': user.email,
					'content': submission.content,
					'attachments': self._encode_attachment_urls(submission.attachments or []),
					'submitted_at': submission.submitted_at,
					'score': submission.score,
					'feedback': getattr(submission, 'feedback', ''),
					'graded': submission.graded,
					'word_count': len(submission.content.split()),
					'late_submission': False
				}
			})
		
		elif request.method == 'PUT':
			# Grade the submission
			score = request.data.get('score')
			feedback = request.data.get('feedback', '')
			
			if score is None:
				return Response({'error': 'Score is required'}, status=status.HTTP_400_BAD_REQUEST)
			
			submission.score = score
			submission.feedback = feedback
			submission.graded = True
			submission.save()
			
			# Send in-app and email notifications to student
			self._send_grading_notifications(submission, score, feedback, lesson)
			
			return Response({'_ok': True, 'message': 'Assignment graded successfully'})

	def _send_grading_notifications(self, submission, score, feedback, lesson):
		"""Send in-app and email notifications to student when assignment is graded"""
		try:
			from notifications.utils import send_notification
			from notifications.models import NotificationPreference
			from utils.mailjet_service import send_email
			
			student = submission.enrollment.user
			course = lesson.module.course
			
			# Create in-app notification
			title = f"Assignment Graded: {lesson.assignment_title or lesson.title}"
			message = f"Your assignment has been graded with a score of {score}/{lesson.points_total or 100}."
			if feedback:
				message += f" Feedback: {feedback[:100]}..." if len(feedback) > 100 else f" Feedback: {feedback}"
			
			action_url = f"/courses/{course.id}/lessons/{lesson.id}"
			
			# Send in-app notification
			send_notification(
				user=student,
				category='course',
				title=title,
				message=message,
				action_url=action_url,
				metadata={
					'lesson_id': lesson.id,
					'score': score,
					'max_points': lesson.points_total or 100
				}
			)
			
			# Send email notification if user has email enabled
			try:
				pref = NotificationPreference.objects.filter(
					user=student,
					notification_type='course'
				).first()
				
				email_enabled = pref.email_enabled if pref else True
				
				if email_enabled:
					percentage = (score / (lesson.points_total or 100)) * 100
					email_subject = f"Your Assignment Has Been Graded: {lesson.assignment_title or lesson.title}"
					
					email_body = f"""
Hello {student.first_name or 'Student'},

Your assignment has been graded!

Assignment: {lesson.assignment_title or lesson.title}
Course: {course.title}
Your Score: {score}/{lesson.points_total or 100} ({percentage:.1f}%)
"""
					
					if feedback:
						email_body += f"\nFeedback from Instructor:\n{feedback}\n"
					
					email_body += f"\n\nView your assignment: {course.id}/lessons/{lesson.id}\n"
					email_body += "\nBest regards,\nThe Learning Platform Team"
					
					send_email(
						recipient_email=student.email,
						subject=email_subject,
						text_body=email_body,
						html_body=None
					)
			except Exception as e:
				print(f"Error sending email notification: {str(e)}")
		
		except Exception as e:
			print(f"Error sending grading notifications: {str(e)}")


class QuizQuestionViewSet(viewsets.ModelViewSet):
	"""API endpoints for quiz questions"""
	queryset = QuizQuestion.objects.all()
	serializer_class = QuizQuestionFullSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
	filterset_fields = ["lesson"]
	ordering = ["id"]
	
	def get_serializer_class(self):
		"""Use full serializer for instructors, hide answers for students"""
		lesson_id = self.request.query_params.get('lesson') or self.request.data.get('lesson')
		if lesson_id:
			try:
				lesson = Lesson.objects.get(id=lesson_id)
				is_instructor = lesson.module.course.facilitator == self.request.user
				if is_instructor:
					return QuizQuestionFullSerializer
				else:
					return QuizQuestionSerializer
			except Lesson.DoesNotExist:
				return QuizQuestionFullSerializer
		return QuizQuestionFullSerializer
	
	def get_queryset(self):
		"""Filter by lesson if provided"""
		qs = QuizQuestion.objects.all()
		lesson_id = self.request.query_params.get('lesson')
		if lesson_id:
			qs = qs.filter(lesson_id=lesson_id)
		return qs
	
	def perform_create(self, serializer):
		"""Create quiz question and validate lesson ownership"""
		lesson = serializer.validated_data.get('lesson')
		# Verify user is the course facilitator
		if lesson and lesson.module.course.facilitator != self.request.user:
			raise permissions.PermissionDenied("You must be the course facilitator to add questions.")
		serializer.save()
	
	def create(self, request, *args, **kwargs):
		"""Override create to provide better error messages"""
		try:
			return super().create(request, *args, **kwargs)
		except Exception as e:
			print(f'[QuizQuestionViewSet] Create error: {str(e)}')
			print(f'[QuizQuestionViewSet] Request data: {request.data}')
			print(f'[QuizQuestionViewSet] Request user: {request.user}')
			raise


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
