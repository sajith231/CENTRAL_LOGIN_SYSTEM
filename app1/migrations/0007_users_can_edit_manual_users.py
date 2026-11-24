from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0006_users_allowed_app_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='can_edit_manual_users',
            field=models.BooleanField(default=False),
        ),
    ]
