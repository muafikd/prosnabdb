# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0034_add_data_package_to_commercial_proposal'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentlistitem',
            name='price_per_unit',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Цена за единицу (итоговая)'),
        ),
        migrations.AddField(
            model_name='equipmentlistitem',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Общая стоимость (итоговая)'),
        ),
    ]
