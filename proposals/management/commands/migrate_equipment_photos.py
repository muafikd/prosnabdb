"""
Django management command: migrate equipment_imagelinks (JSONB) to local EquipmentPhoto.

Parses equipment.equipment_imagelinks, downloads images from Google Drive / Yandex Disk,
optimizes and saves to EquipmentPhoto. Logs errors for inactive or invalid links.
"""
import logging
from django.core.management.base import BaseCommand
from proposals.models import Equipment
from proposals.services import CloudImageImportService

logger = logging.getLogger(__name__)


def _iter_imagelinks(equipment):
    """Yield (url, name, index) from equipment.equipment_imagelinks."""
    links = equipment.equipment_imagelinks
    if not links:
        return
    if isinstance(links, list):
        for i, item in enumerate(links):
            if isinstance(item, dict):
                url = item.get('url')
                if url and str(url).strip():
                    yield (str(url).strip(), item.get('name') or '', i)
            elif isinstance(item, str) and item.strip():
                yield (item.strip(), '', i)
    elif isinstance(links, str):
        for i, link in enumerate(link.strip() for link in links.split(',') if link.strip()):
            yield (link, '', i)


class Command(BaseCommand):
    help = (
        'Migrate equipment_imagelinks (JSONB) to local EquipmentPhoto: '
        'download from Google Drive / Yandex Disk, optimize and save to /app/media/photos/.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only log what would be done, do not create EquipmentPhoto.',
        )
        parser.add_argument(
            '--equipment-id',
            type=int,
            default=None,
            help='Process only this equipment_id (optional).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        equipment_id = options.get('equipment_id')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: no files will be created.'))

        qs = Equipment.objects.all().order_by('equipment_id')
        if equipment_id is not None:
            qs = qs.filter(equipment_id=equipment_id)
            if not qs.exists():
                self.stdout.write(self.style.ERROR(f'Equipment id={equipment_id} not found.'))
                return

        total_ok = 0
        total_skip = 0
        total_fail = 0

        for equipment in qs:
            for url, name, idx in _iter_imagelinks(equipment):
                if not CloudImageImportService.detect_source(url):
                    self.stdout.write(
                        self.style.WARNING(
                            f'Equipment {equipment.equipment_id} link[{idx}]: not Google/Yandex, skip: {url[:60]}...'
                        )
                    )
                    total_skip += 1
                    continue
                if dry_run:
                    self.stdout.write(
                        f'Would import: equipment_id={equipment.equipment_id} idx={idx} url={url[:60]}...'
                    )
                    total_ok += 1
                    continue
                photo = CloudImageImportService.import_and_save(equipment, url, name=name, sort_order=idx)
                if photo:
                    total_ok += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Equipment {equipment.equipment_id} link[{idx}]: saved -> {photo.image.name}'
                        )
                    )
                else:
                    total_fail += 1
                    logger.warning(
                        'Import failed: equipment_id=%s idx=%s url=%s',
                        equipment.equipment_id, idx, url[:80],
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f'Equipment {equipment.equipment_id} link[{idx}]: failed (link inactive or download error): {url[:60]}...'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Created={total_ok} Skipped={total_skip} Failed={total_fail}'
            )
        )
