import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prosnabdb.settings')
django.setup()

from proposals.models import Equipment
from django.db import connection

# Check model field type
print(f"Model field type: {Equipment._meta.get_field('equipment_imagelinks').get_internal_type()}")

# Check DB column type (PostgreSQL)
with connection.cursor() as cursor:
    cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'equipment' AND column_name = 'equipment_imagelinks'")
    row = cursor.fetchone()
    print(f"DB column type: {row[0] if row else 'Not found'}")

# Check sample data
sample = Equipment.objects.first()
if sample:
    print(f"Sample images (raw): {sample.equipment_imagelinks}")
    print(f"Sample images type: {type(sample.equipment_imagelinks)}")
else:
    print("No equipment found")
