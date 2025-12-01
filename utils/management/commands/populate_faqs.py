from django.core.management.base import BaseCommand
from utils.models import FAQ


class Command(BaseCommand):
    help = 'Populate initial FAQ data for the platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate FAQ data...'))
        
        faqs_data = [
            {
                'question': 'Can I cancel my membership anytime?',
                'answer': 'Yes, absolutely. You can cancel your membership at any time with no penalties or hidden fees. Your access will continue until the end of your current billing period, and you won\'t be charged again.',
                'category': 'Membership',
            },
            {
                'question': 'What if I only want to purchase courses without joining the community?',
                'answer': 'You can purchase individual courses from The New Africa Institute without becoming a community member. However, community members receive exclusive discounts on all courses and programs, often saving more than the membership cost itself.',
                'category': 'Courses',
            },
            {
                'question': 'Do I need to join the community to access learning resources?',
                'answer': 'While some courses and resources are available for individual purchase, community membership provides comprehensive access to exclusive content, mentorship opportunities, networking events, and discounted pricing across all platforms. It\'s designed to maximize your growth and connections within the African ecosystem.',
                'category': 'Community',
            },
            {
                'question': 'How do corporate benefits work?',
                'answer': 'Corporate memberships provide organization-wide benefits including brand visibility across all New Africa platforms, thought leadership opportunities, strategic networking access, CSR recognition, exclusive research reports, and talent pipeline connections. Custom partnership packages are available for larger organizations with specific needs.',
                'category': 'Corporate',
            },
            {
                'question': 'How do I update my profile information?',
                'answer': 'You can update your profile by logging into your account, navigating to the "Account Settings" section, and editing your personal information, preferences, and profile picture. Changes are saved immediately and reflected across all New Africa platforms.',
                'category': 'Account',
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'We accept all major credit and debit cards (Visa, Mastercard, American Express), as well as mobile money payments in selected African countries. Payment processing is secure and encrypted through our payment partners.',
                'category': 'Billing',
            },
            {
                'question': 'Can I change my membership tier?',
                'answer': 'Yes, you can upgrade or downgrade your membership tier at any time. Changes will take effect at the start of your next billing cycle. If upgrading, you may be entitled to a pro-rata adjustment. Contact our support team for assistance with tier changes.',
                'category': 'Membership',
            },
            {
                'question': 'How do I access exclusive content as a member?',
                'answer': 'As a member, you have access to exclusive content through your dashboard. This includes member-only courses, research reports, networking events, and webinars. All exclusive content is marked clearly and available in the "Premium Content" section of the platform.',
                'category': 'Community',
            },
            {
                'question': 'Is there a referral program or community rewards?',
                'answer': 'Yes! We have an active referral program where you can earn credits and rewards for inviting friends to join the New Africa Community. Details about the current program, rewards, and how to participate are available in your account dashboard.',
                'category': 'Rewards',
            },
            {
                'question': 'How do facilitators monetize their courses?',
                'answer': 'Facilitators earn revenue from course enrollments. You set your course pricing, and The New Africa Institute takes a standard commission. Detailed analytics and payment reports are available in your facilitator dashboard, with payouts processed monthly.',
                'category': 'Facilitator',
            },
            {
                'question': 'What technical support is available?',
                'answer': 'We provide 24/7 customer support through email, live chat, and our support portal. Our team is responsive and committed to resolving technical issues quickly. Premium members receive priority support with faster response times.',
                'category': 'Support',
            },
            {
                'question': 'Can organizations customize group memberships?',
                'answer': 'Yes, corporate and organizational memberships can be customized to meet specific needs. This may include team licensing, custom training programs, dedicated account management, and branded content spaces. Contact our corporate sales team for a customized proposal.',
                'category': 'Corporate',
            },
        ]

        created_count = 0
        for faq_data in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {faq_data["question"][:50]}...'))
            else:
                self.stdout.write(self.style.WARNING(f'⊘ Already exists: {faq_data["question"][:50]}...'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ FAQ data population complete! Created {created_count} new FAQs.'))
