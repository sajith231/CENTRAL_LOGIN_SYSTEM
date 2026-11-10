from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MobileApp', '0028_mobileproject_t_erp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobileproject',
            name='t_erp',
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text='Allow this project to be used by the T-ERP licence create API.',
            ),
        ),
    ]
