

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, CourseModule, CourseReview
from .serializers import CourseSerializer, CourseModuleSerializer, CourseReviewSerializer
from .permissions import IsFacilitator

class CourseViewSet(viewsets.ModelViewSet):
	lookup_field = "slug"
	serializer_class = CourseSerializer
	# Default: allow read-only to everyone, require auth for unsafe methods
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
	filterset_fields = ["is_featured", "category", "level", "format"]
	ordering_fields = ["created_at", "price", "enrollments_count"]
	search_fields = ["title", "short_description", "full_description"]

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
		serializer.save(facilitator=self.request.user)

	def get_permissions(self):
		# For create action, require the user to be a facilitator
		if self.action == 'create':
			return [IsFacilitator()]
		# For update/destroy, ensure the user owns the course
		if self.action in ('update', 'partial_update', 'destroy'):
			from .permissions import IsCourseOwner
			return [permissions.IsAuthenticated(), IsCourseOwner()]
		return [perm() for perm in self.permission_classes]

	@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
	def mine(self, request):
		"""Return courses owned by the authenticated user (facilitator)."""
		qs = self.get_queryset().filter(facilitator=request.user)
		page = self.paginate_queryset(qs)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = self.get_serializer(qs, many=True)
		return Response(serializer.data)

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
