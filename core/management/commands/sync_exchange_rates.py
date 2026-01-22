from django.core.management.base import BaseCommand
from core.services.exchange_rate_service import ExchangeRateService

class Command(BaseCommand):
    help = 'Syncs exchange rates from National Bank of Kazakhstan'

    def handle(self, *args, **options):
        self.stdout.write('Starting exchange rate sync...')
        
        try:
            stats = ExchangeRateService.fetch_and_sync_rates()
            self.stdout.write(self.style.SUCCESS(f'Sync completed successfully! Stats: {stats}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Sync failed: {str(e)}'))
