"""Add message field to CorporateConnection

This migration adds the `message` TextField to the existing
`CorporateConnection` model. Use a default empty string so existing
rows are populated safely.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0029_post_is_sponsored_post_sponsored_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='corporateconnection',
            name='message',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
