from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0009_postbookmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='link_previews',
            field=models.JSONField(default=list, blank=True),
        ),
    ]
