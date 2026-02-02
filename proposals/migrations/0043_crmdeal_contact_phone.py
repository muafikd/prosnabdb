# Generated migration: add contact_phone to CrmDeal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0042_crmdeal_and_deal_on_proposal'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmdeal',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Телефон контактного лица'),
        ),
    ]
