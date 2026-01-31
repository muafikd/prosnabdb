# Generated manually for EquipmentPhoto (local storage for imported cloud images)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0037_equipmentlistitem_calculated_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipmentPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to='photos/', verbose_name='Фото')),
                ('name', models.CharField(blank=True, max_length=255, verbose_name='Подпись')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('equipment', models.ForeignKey(db_column='equipment_id', on_delete=models.CASCADE, related_name='photos', to='proposals.equipment', verbose_name='Оборудование')),
            ],
            options={
                'verbose_name': 'Фото оборудования',
                'verbose_name_plural': 'Фото оборудования',
                'db_table': 'equipment_photo',
                'ordering': ['sort_order', 'pk'],
            },
        ),
    ]
