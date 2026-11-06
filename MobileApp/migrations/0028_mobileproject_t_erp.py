from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MobileApp', '0027_mobileproject_branch_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobileproject',
            name='t_erp',
            field=models.BooleanField(
                default=False,
                help_text='Allow this project to be used by the T-ERP licence create API.',
            ),
        ),
    ]
