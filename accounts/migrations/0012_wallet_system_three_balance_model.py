# Generated migration for facilitator wallet system
# Implements the three-balance model: earning_balance, pending_balance, available_balance
# Replaces the old balance and total_earnings fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Remove old balance fields
        migrations.RemoveField(
            model_name='userprofile',
            name='balance',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='total_earnings',
        ),
        
        # Add new three-balance fields
        migrations.AddField(
            model_name='userprofile',
            name='earning_balance',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Total earned from course sales', max_digits=12),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='pending_balance',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Earned but not yet cleared (processing period)', max_digits=12),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='available_balance',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Usable balance for withdrawals/campaigns/promotions', max_digits=12),
        ),
    ]
