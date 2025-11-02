"""Make user-related foreign keys nullable to allow user deletion.

This migration explicitly alters the user fields to ensure the database
column allows NULL. It is safe to run on development databases and will
correct the NOT NULL constraint that is currently preventing user deletion.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usertoken",
            name="user",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="user",
            field=models.OneToOneField(
                to=settings.AUTH_USER_MODEL,
                related_name="profile",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
        migrations.AlterField(
            model_name="follow",
            name="follower",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                related_name="following_set",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
        migrations.AlterField(
            model_name="follow",
            name="followed",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                related_name="followers_set",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
            ),
        ),
    ]
