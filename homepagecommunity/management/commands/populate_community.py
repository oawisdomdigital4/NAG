from django.core.management.base import BaseCommand
from homepagecommunity.models import (
    HeroSection, AboutCommunityMission, CommunityFeature,
    SubscriptionTier, SubscriptionBenefit, Testimonial,
    FinalCTA, CommunityMetrics
)


class Command(BaseCommand):
    help = 'Populate initial data for community homepage'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate community data...'))
        
        # Hero Section
        HeroSection.objects.get_or_create(
            id=1,
            defaults={
                'title_line_1': 'One Million Voices.',
                'title_line_2': 'One Africa.',
                'title_line_3': 'One Movement.',
                'subtitle': 'Join a global community of Africans, innovators, facilitators, and leaders shaping tomorrow.',
                'individual_price': 1.00,
                'individual_period': 'Month',
                'facilitator_price': 5.00,
                'facilitator_period': 'Month',
                'corporate_price': 500.00,
                'corporate_period': 'Year',
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Hero Section created'))

        # About Community
        AboutCommunityMission.objects.get_or_create(
            id=1,
            defaults={
                'mission_label': 'Our Mission',
                'mission_title': 'More Than a Forum',
                'mission_description': 'The New Africa Community is more than a forum — it\'s a continental movement uniting individuals and organizations across Africa and the diaspora into a single ecosystem of empowerment, visibility, and influence.',
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ About Community created'))

        # Community Features
        features_data = [
            {'title': 'Mentorship', 'description': 'Connect with leaders', 'feature_type': 'mentorship', 'order': 0},
            {'title': 'Education', 'description': 'Learn and grow', 'feature_type': 'education', 'order': 1},
            {'title': 'Networking', 'description': 'Build relationships', 'feature_type': 'networking', 'order': 2},
        ]
        for feature_data in features_data:
            CommunityFeature.objects.get_or_create(
                title=feature_data['title'],
                defaults=feature_data
            )
        self.stdout.write(self.style.SUCCESS('✓ Community Features created'))

        # Subscription Tiers
        tiers_data = [
            {
                'tier_type': 'individual',
                'title': 'Empowering Your Growth',
                'subtitle': 'For Individuals',
                'price': 1.00,
                'period': 'Month',
                'description': 'Access to mentorship, career development, and exclusive discounts.',
                'label_color': 'text-cool-blue',
                'bg_color': 'bg-white',
                'button_color': 'bg-brand-red',
            },
            {
                'tier_type': 'facilitator',
                'title': 'Empowering Africa\'s Educators & Mentors',
                'subtitle': 'For Facilitators',
                'price': 5.00,
                'period': 'Month',
                'description': 'Course visibility, sponsored content, and professional branding.',
                'label_color': 'text-brand-gold',
                'bg_color': 'bg-gradient-to-br from-gray-50 to-white',
                'button_color': 'bg-brand-red',
            },
            {
                'tier_type': 'corporate',
                'title': 'Build Visibility & Influence',
                'subtitle': 'For Corporates',
                'price': 500.00,
                'period': 'Year',
                'description': 'Brand visibility, thought leadership, and strategic networking.',
                'label_color': 'text-brand-gold',
                'bg_color': 'bg-gradient-to-br from-gray-50 via-white to-gray-50',
                'button_color': 'bg-brand-gold',
            },
        ]

        for tier_data in tiers_data:
            tier, created = SubscriptionTier.objects.get_or_create(
                tier_type=tier_data['tier_type'],
                defaults=tier_data
            )
            # Update price and period if already exists (to ensure correct values)
            if not created:
                tier.price = tier_data['price']
                tier.period = tier_data['period']
                tier.title = tier_data['title']
                tier.description = tier_data['description']
                tier.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ {tier.get_tier_type_display()} tier created'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ {tier.get_tier_type_display()} tier updated'))

        # Individual Benefits
        individual_benefits = [
            {'title': 'Mentorship & Leadership', 'description': 'Access to experienced mentors and leadership development programs to accelerate your personal growth.', 'icon_name': 'Users', 'order': 0},
            {'title': 'Career Development', 'description': 'Exclusive internship opportunities, job postings, and career advancement resources.', 'icon_name': 'TrendingUp', 'order': 1},
            {'title': 'Knowledge Resources', 'description': 'Free access to ebooks, research reports, and premium content from New Africa Magazine.', 'icon_name': 'BookOpen', 'order': 2},
            {'title': 'Global Networking', 'description': 'Connect with changemakers, innovators, and leaders across Africa and the diaspora.', 'icon_name': 'Network', 'order': 3},
            {'title': 'Media Visibility', 'description': 'Feature opportunities in New Africa Magazine, TV broadcasts, and digital platforms.', 'icon_name': 'Tv', 'order': 4},
            {'title': 'Exclusive Discounts', 'description': 'Special pricing on courses, events, summits, and all New Africa programs and services.', 'icon_name': 'Gift', 'order': 5},
        ]

        individual_tier = SubscriptionTier.objects.get(tier_type='individual')
        for benefit_data in individual_benefits:
            SubscriptionBenefit.objects.get_or_create(
                tier=individual_tier,
                title=benefit_data['title'],
                defaults=benefit_data
            )
        self.stdout.write(self.style.SUCCESS('✓ Individual benefits created'))

        # Facilitator Benefits
        facilitator_benefits = [
            {'title': 'Course Visibility & Monetization', 'description': 'Promote your courses across the New Africa platforms and community. Earn from every enrolment and grow your audience.', 'icon_name': 'DollarSign', 'order': 0},
            {'title': 'Sponsored Content Opportunities', 'description': 'Feature your courses or programs as sponsored posts, boosting reach to individuals and corporates seeking learning opportunities.', 'icon_name': 'TrendingUp', 'order': 1},
            {'title': 'Professional Branding', 'description': 'Build a verified educator profile showcasing your expertise, achievements, and past student feedback.', 'icon_name': 'Award', 'order': 2},
            {'title': 'Collaborative Learning Spaces', 'description': 'Host live sessions, mentorship programs, and workshops that engage learners from across Africa and the diaspora.', 'icon_name': 'Users', 'order': 3},
            {'title': 'Community Influence', 'description': 'Gain exposure through New Africa Magazine and TV features spotlighting leading facilitators and thought leaders.', 'icon_name': 'Tv', 'order': 4},
            {'title': 'Continuous Support', 'description': 'Access technical, marketing, and content support to enhance your course quality and learner engagement.', 'icon_name': 'Headphones', 'order': 5},
        ]

        facilitator_tier = SubscriptionTier.objects.get(tier_type='facilitator')
        for benefit_data in facilitator_benefits:
            SubscriptionBenefit.objects.get_or_create(
                tier=facilitator_tier,
                title=benefit_data['title'],
                defaults=benefit_data
            )
        self.stdout.write(self.style.SUCCESS('✓ Facilitator benefits created'))

        # Corporate Benefits
        corporate_benefits = [
            {'title': 'Brand Visibility', 'description': 'Premium advertising and brand placement across all New Africa platforms and media channels.', 'icon_name': 'Megaphone', 'order': 0},
            {'title': 'Thought Leadership', 'description': 'Publish articles, participate in panel discussions, and showcase your expertise through case studies.', 'icon_name': 'Lightbulb', 'order': 1},
            {'title': 'Strategic Networking', 'description': 'Connect with policymakers, investors, and key decision-makers shaping Africa\'s future.', 'icon_name': 'Handshake', 'order': 2},
            {'title': 'CSR Recognition', 'description': 'Build your corporate social responsibility profile and create a lasting legacy across the continent.', 'icon_name': 'Award', 'order': 3},
            {'title': 'Research Access', 'description': 'Exclusive access to reports, data, and insights from The New Africa Institute.', 'icon_name': 'FileText', 'order': 4},
            {'title': 'Talent Pipeline', 'description': 'Access to internship programs, mentorship opportunities, and Africa\'s brightest emerging talent.', 'icon_name': 'UserCheck', 'order': 5},
        ]

        corporate_tier = SubscriptionTier.objects.get(tier_type='corporate')
        for benefit_data in corporate_benefits:
            SubscriptionBenefit.objects.get_or_create(
                tier=corporate_tier,
                title=benefit_data['title'],
                defaults=benefit_data
            )
        self.stdout.write(self.style.SUCCESS('✓ Corporate benefits created'))

        # Testimonials
        testimonials_data = [
            {'name': 'Amara Okafor', 'title': 'Tech Entrepreneur, Nigeria', 'quote': 'Joining the New Africa Community connected me with mentors who transformed my startup journey. The networking opportunities alone are worth exponentially more than the membership fee.', 'display_order': 0},
            {'name': 'Kwame Mensah', 'title': 'Policy Advisor, Ghana', 'quote': 'This community is a game-changer for anyone serious about Africa\'s development. The knowledge resources and strategic connections have been invaluable to my work.', 'display_order': 1},
            {'name': 'Zainab Diallo', 'title': 'Social Impact Leader, Senegal', 'quote': 'I\'ve never felt more empowered and supported. The New Africa Community is where vision meets action, and where individual dreams contribute to our collective transformation.', 'display_order': 2},
            {'name': 'David Mwangi', 'title': 'Investment Manager, Kenya', 'quote': 'The caliber of professionals and innovators in this community is exceptional. Every conversation opens new doors and creates opportunities I never imagined possible.', 'display_order': 3},
        ]

        for testimonial_data in testimonials_data:
            Testimonial.objects.get_or_create(
                name=testimonial_data['name'],
                defaults=testimonial_data
            )
        self.stdout.write(self.style.SUCCESS('✓ Testimonials created'))

        # Final CTA
        FinalCTA.objects.get_or_create(
            id=1,
            defaults={
                'title_part_1': 'The future of Africa depends on those who',
                'title_teach': 'teach',
                'title_connect': 'connect',
                'title_empower': 'empower',
                'subtitle': 'Join the movement. Shape the narrative. Build the future.',
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Final CTA created'))

        # Community Metrics
        CommunityMetrics.objects.get_or_create(
            id=1,
            defaults={
                'total_members': 15000,
                'active_groups': 145,
                'total_posts': 8500,
                'total_facilitators': 450,
                'total_courses': 280,
                'total_enrollments': 32000,
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Community Metrics created'))

        self.stdout.write(self.style.SUCCESS('\n✅ All community data has been successfully populated!'))
