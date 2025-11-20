"""
Management command to display admin dashboard statistics
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from accounts.models import User, UserProfile
from community.models import Post, Comment, Group
from courses.models import Course, Enrollment
from payments.models import Payment


class Command(BaseCommand):
    help = 'Display admin dashboard statistics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('ADMIN DASHBOARD STATISTICS'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # USER STATS
        self.stdout.write(self.style.HTTP_INFO('👥 USER STATISTICS'))
        self.stdout.write('-' * 60)
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        facilitators = User.objects.filter(role='facilitator').count()
        corporate = User.objects.filter(role='corporate').count()
        individuals = User.objects.filter(role='individual').count()
        
        self.stdout.write(f'  Total Users: {self.style.SUCCESS(str(total_users))}')
        self.stdout.write(f'  Active Users: {self.style.SUCCESS(str(active_users))}')
        self.stdout.write(f'  Facilitators: {self.style.HTTP_INFO(str(facilitators))}')
        self.stdout.write(f'  Corporate Users: {self.style.WARNING(str(corporate))}')
        self.stdout.write(f'  Individuals: {self.style.HTTP_INFO(str(individuals))}')

        # COMMUNITY STATS
        self.stdout.write(self.style.HTTP_INFO('\n💬 COMMUNITY STATISTICS'))
        self.stdout.write('-' * 60)
        total_posts = Post.objects.count()
        total_comments = Comment.objects.count()
        total_groups = Group.objects.count()
        
        self.stdout.write(f'  Total Posts: {self.style.SUCCESS(str(total_posts))}')
        self.stdout.write(f'  Total Comments: {self.style.SUCCESS(str(total_comments))}')
        self.stdout.write(f'  Total Groups: {self.style.SUCCESS(str(total_groups))}')

        # COURSE STATS
        self.stdout.write(self.style.HTTP_INFO('\n📚 COURSE STATISTICS'))
        self.stdout.write('-' * 60)
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(is_published=True).count()
        total_enrollments = Enrollment.objects.count()
        
        self.stdout.write(f'  Total Courses: {self.style.SUCCESS(str(total_courses))}')
        self.stdout.write(f'  Published: {self.style.SUCCESS(str(published_courses))}')
        self.stdout.write(f'  Total Enrollments: {self.style.SUCCESS(str(total_enrollments))}')

        # PAYMENT STATS
        self.stdout.write(self.style.HTTP_INFO('\n💳 PAYMENT STATISTICS'))
        self.stdout.write('-' * 60)
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(status='completed').count()
        total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        self.stdout.write(f'  Total Payments: {self.style.SUCCESS(str(total_payments))}')
        self.stdout.write(f'  Successful: {self.style.SUCCESS(str(successful_payments))}')
        self.stdout.write(f'  Total Revenue: {self.style.SUCCESS(f"${total_revenue:,.2f}")}')

        # PROFILE STATS
        self.stdout.write(self.style.HTTP_INFO('\n🎯 PROFILE STATISTICS'))
        self.stdout.write('-' * 60)
        verified_profiles = UserProfile.objects.filter(community_approved=True).count()
        profiles_with_avatar = UserProfile.objects.filter(avatar__isnull=False).exclude(avatar='').count()
        
        self.stdout.write(f'  Verified Profiles: {self.style.SUCCESS(str(verified_profiles))}')
        self.stdout.write(f'  With Avatar: {self.style.SUCCESS(str(profiles_with_avatar))}')

        self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))
