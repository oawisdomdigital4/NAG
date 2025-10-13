
from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication
from accounts.authentication import DatabaseTokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ModelViewSet):
	queryset = Notification.objects.all()
	serializer_class = NotificationSerializer
	# Allow unauthenticated GET requests (safe methods) so callers that pass
	# a user_id query parameter can fetch notifications without session auth.
	# Other methods (POST/PUT/DELETE) still require authentication.
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]

	def list(self, request, *args, **kwargs):
		"""Support filtering the notification list by user_id, category and limit.

		Query params handled:
		- user_id: optional int, counts/returns notifications for that user id
		- category: optional string to filter by category
		- limit: optional int to limit number of results (ordered by created_at desc)
		"""
		queryset = self.get_queryset()

		user_id = request.query_params.get("user_id")
		if user_id:
			try:
				user_id_int = int(user_id)
			except (TypeError, ValueError):
				return Response({"detail": "Invalid user_id"}, status=400)
			queryset = queryset.filter(user_id=user_id_int)
		else:
			# If caller is authenticated and did not pass user_id, scope to their notifications
			if request.user and request.user.is_authenticated:
				queryset = queryset.filter(user=request.user)
			else:
				# Unauthenticated callers without user_id get an empty list
				queryset = queryset.none()

		category = request.query_params.get("category")
		if category:
			queryset = queryset.filter(category=category)

		limit = request.query_params.get("limit")
		if limit:
			try:
				limit_int = int(limit)
			except (TypeError, ValueError):
				limit_int = None
			if limit_int:
				queryset = queryset.order_by("-created_at")[:limit_int]

		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	@action(detail=False, methods=["get"], url_path="unread_count")
	def unread_count(self, request):
		"""Return the number of unread (and not archived) notifications for a user.

		Query params:
		- user_id: optional, integer. If provided, counts unread notifications for that user id.
				   If not provided, uses the authenticated user.
		"""
		user_id = request.query_params.get("user_id")
		qs = self.get_queryset()

		if user_id:
			try:
				user_id_int = int(user_id)
			except (TypeError, ValueError):
				return Response({"detail": "Invalid user_id"}, status=400)
			qs = qs.filter(user_id=user_id_int)
		else:
			if request.user and request.user.is_authenticated:
				qs = qs.filter(user=request.user)
			else:
				return Response({"detail": "Authentication credentials were not provided."}, status=401)

		count = qs.filter(read=False, archived=False).count()
		# Return a `count` key to match frontend expectation
		return Response({"count": count})

	@action(detail=True, methods=["post"], url_path="mark_read")
	def mark_read(self, request, pk=None):
		"""Mark a single notification as read."""
		notif = self.get_object()
		if not notif.read:
			notif.read = True
			notif.read_at = timezone.now()
			notif.save(update_fields=["read", "read_at"])
		return Response({"status": "ok", "id": notif.id})

	@action(detail=False, methods=["post"], url_path="mark_all_read")
	def mark_all_read(self, request):
		"""Mark all matching notifications as read for a user (or authenticated user).

		Accepts optional `user_id` query param; otherwise uses the authenticated user.
		Returns the number of notifications marked as read.
		"""
		qs = self.get_queryset()
		user_id = request.query_params.get("user_id")
		if user_id:
			try:
				user_id_int = int(user_id)
			except (TypeError, ValueError):
				return Response({"detail": "Invalid user_id"}, status=400)
			qs = qs.filter(user_id=user_id_int)
		else:
			if request.user and request.user.is_authenticated:
				qs = qs.filter(user=request.user)
			else:
				return Response({"detail": "Authentication credentials were not provided."}, status=401)

		updated = qs.filter(read=False).update(read=True, read_at=timezone.now())
		return Response({"marked": updated})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
	queryset = NotificationPreference.objects.all()
	serializer_class = NotificationPreferenceSerializer
	authentication_classes = [DatabaseTokenAuthentication, SessionAuthentication]
	permission_classes = [permissions.IsAuthenticated]
