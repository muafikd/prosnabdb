# Generated migration: add stage_title to CrmDeal (readable stage name)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0043_crmdeal_contact_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmdeal',
            name='stage_title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Название стадии сделки'),
        ),
    ]
