from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0006_post_group_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='media_urls',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.CreateModel(
            name='PostAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='community/post_media/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='attachments', to='community.post')),
            ],
        ),
    ]
