from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0018_add_engagement_and_sponsor_models'),
    ]

    operations = [
        # Plan, Payment, and Subscription models moved to payments app

        # Add fields to existing UserProfile model
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.CharField(default='individual', max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='community/avatars/'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='community/covers/'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='website',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='social_links',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='verification_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='last_active',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='activity_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notification_preferences',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='privacy_settings',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='total_posts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='total_likes',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='total_comments',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='engagement_rate',
            field=models.FloatField(default=0.0),
        ),

        # Add fields to Post
        migrations.AddField(
            model_name='post',
            name='title',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='post',
            name='view_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='post',
            name='engagement_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='post',
            name='ranking_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='post',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='post',
            name='moderation_status',
            field=models.CharField(default='approved', max_length=20),
        ),
        migrations.AddField(
            model_name='post',
            name='moderation_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='post',
            name='last_activity_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
