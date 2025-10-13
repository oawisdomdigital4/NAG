from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0005_chatroom_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='posts', to='community.group'),
        ),
    ]
