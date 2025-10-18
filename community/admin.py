from django.contrib import admin
from .models import (
	Organizer,
	FeaturedSpeaker,
	Partner,
	PastEdition,
	ChatRoom,
	Message,
	Course,
	Enrollment,
	Group,
	GroupMembership,
	Post,
	PostAttachment,
	PostBookmark,
	Comment,
	PostReaction,
	CommentReaction,
	Notification,
	Plan,
	Subscription,
	Payment,
	CorporateVerification,
)


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
	list_display = ("name", "title", "link")


@admin.register(FeaturedSpeaker)
class FeaturedSpeakerAdmin(admin.ModelAdmin):
	list_display = ("name", "title", "link")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
	list_display = ("id", "logo")


@admin.register(PastEdition)
class PastEditionAdmin(admin.ModelAdmin):
	list_display = ("year", "location", "theme")
	readonly_fields = ()


@admin.action(description="Set subscription status to active")
def set_subscription_active(modeladmin, request, queryset):
	updated = queryset.update(status='active')
	modeladmin.message_user(request, f"Marked {updated} subscriptions active")


@admin.action(description="Set subscription status to cancelled")
def set_subscription_cancelled(modeladmin, request, queryset):
	updated = queryset.update(status='cancelled')
	modeladmin.message_user(request, f"Marked {updated} subscriptions cancelled")



@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'created_by', 'created_at')
	filter_horizontal = ('members',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'room', 'sender', 'created_at')
	list_filter = ('room', 'sender')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'facilitator', 'status', 'price', 'created_at')
	search_fields = ('title', 'facilitator__email')
	list_filter = ('status',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
	list_display = ('user', 'course', 'progress', 'enrolled_at')
	search_fields = ('user__email', 'course__title')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'is_corporate_group', 'created_by', 'created_at')
	search_fields = ('name', 'category')


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
	list_display = ('user', 'group', 'joined_at')
	search_fields = ('user__email', 'group__name')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ('id', 'author', 'group', 'feed_visibility', 'created_at')
	search_fields = ('author__email', 'content')
	list_filter = ('feed_visibility', 'created_at')


@admin.register(PostAttachment)
class PostAttachmentAdmin(admin.ModelAdmin):
	list_display = ('id', 'post', 'file', 'uploaded_at')
	search_fields = ('post__id',)


@admin.register(PostBookmark)
class PostBookmarkAdmin(admin.ModelAdmin):
	list_display = ('post', 'user', 'created_at')
	search_fields = ('user__email',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ('id', 'post', 'author', 'is_private_reply', 'created_at')
	search_fields = ('author__email', 'content')


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
	list_display = ('post', 'user', 'reaction_type', 'created_at')
	search_fields = ('user__email',)


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
	list_display = ('comment', 'user', 'created_at')
	search_fields = ('user__email',)


@admin.register(Notification)
class CommunityNotificationAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'category', 'title', 'read', 'created_at')
	list_filter = ('category', 'read')
	search_fields = ('title', 'message', 'user__email')


@admin.register(Plan)
class CommunityPlanAdmin(admin.ModelAdmin):
	list_display = ('name', 'price', 'interval')
	search_fields = ('name',)


@admin.register(Subscription)
class CommunitySubscriptionAdmin(admin.ModelAdmin):
	list_display = ('user', 'plan', 'status', 'start_date', 'end_date')
	search_fields = ('user__email', 'plan__name')


@admin.register(Payment)
class CommunityPaymentAdmin(admin.ModelAdmin):
	list_display = ('user', 'amount', 'provider', 'status', 'created_at')
	search_fields = ('user__email', 'provider')


@admin.register(CorporateVerification)
class CorporateVerificationAdmin(admin.ModelAdmin):
	list_display = ('user', 'company_name', 'status', 'submitted_at', 'reviewed_at')
	list_filter = ('status',)
	search_fields = ('company_name', 'user__email')
