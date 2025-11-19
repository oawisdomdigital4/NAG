from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from promotions.models import WithdrawalRequest
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Test withdrawal approval and balance deduction'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID of facilitator')
        parser.add_argument('--withdrawal-id', type=int, help='Withdrawal request ID')

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        withdrawal_id = options.get('withdrawal_id')

        if not withdrawal_id:
            self.stdout.write(self.style.ERROR('Please provide --withdrawal-id'))
            return

        try:
            withdrawal = WithdrawalRequest.objects.get(id=withdrawal_id)
            self.stdout.write(f"Found withdrawal: {withdrawal}")
            self.stdout.write(f"Current status: {withdrawal.status}")
            self.stdout.write(f"Amount: {withdrawal.amount}")

            profile = getattr(withdrawal.facilitator, 'profile', None)
            if profile:
                self.stdout.write(f"Current balance before: {profile.balance}")
                self.stdout.write(f"Current total_earnings: {profile.total_earnings}")
                self.stdout.write(f"Available balance: {profile.balance + profile.total_earnings}")
            else:
                self.stdout.write(self.style.ERROR("No profile found"))
                return

            # Get admin user
            admin = User.objects.filter(is_superuser=True).first()
            if not admin:
                self.stdout.write(self.style.ERROR("No admin user found"))
                return

            self.stdout.write(self.style.SUCCESS(f"\nProcessing withdrawal with admin: {admin}"))
            
            # Process the withdrawal
            withdrawal.process('approved', admin, 'Test approval')
            
            # Refresh the profile to see changes
            profile.refresh_from_db()
            self.stdout.write(f"\nAfter approval:")
            self.stdout.write(f"Current balance after: {profile.balance}")
            self.stdout.write(f"Current total_earnings: {profile.total_earnings}")
            self.stdout.write(f"Available balance: {profile.balance + profile.total_earnings}")

            # Refresh the withdrawal
            withdrawal.refresh_from_db()
            self.stdout.write(f"Withdrawal status: {withdrawal.status}")
            self.stdout.write(self.style.SUCCESS("✓ Withdrawal processed successfully"))

        except WithdrawalRequest.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Withdrawal with ID {withdrawal_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            traceback.print_exc()
