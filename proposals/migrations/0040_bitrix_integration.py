# Generated migration for Bitrix24 integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0039_alter_equipmentphoto_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='bitrix_id',
            field=models.IntegerField(blank=True, null=True, unique=True, verbose_name='ID компании в Bitrix24'),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='bitrix_webhook_url',
            field=models.URLField(blank=True, max_length=512, null=True, verbose_name='URL вебхука Bitrix24'),
        ),
    ]
