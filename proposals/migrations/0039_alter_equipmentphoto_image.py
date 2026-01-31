# Generated manually: sync EquipmentPhoto.image upload_to with model (callable)

import uuid
from django.db import migrations, models


def equipment_photo_upload_to(instance, filename):
    return f"photos/{uuid.uuid4().hex}.jpg"


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0038_equipment_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipmentphoto',
            name='image',
            field=models.ImageField(
                max_length=255,
                upload_to=equipment_photo_upload_to,
                verbose_name='Фото',
            ),
        ),
    ]
