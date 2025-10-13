from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0007_post_media_and_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='parent_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='replies', to='community.comment'),
        ),
        migrations.AddField(
            model_name='comment',
            name='is_private_reply',
            field=models.BooleanField(default=False),
        ),
    ]
