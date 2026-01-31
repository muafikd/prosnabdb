import requests
import xmltodict
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from proposals.models import ExchangeRate
from datetime import timedelta

class ExchangeRateService:
    RSS_URL = "https://www.nationalbank.kz/rss/get_rates.cfm"

    @classmethod
    def fetch_and_sync_rates(cls, date_obj=None):
        """
        Fetches exchange rates from National Bank of Kazakhstan RSS and syncs them to DB.
        
        Args:
            date_obj (date, optional): Date to fetch rates for. Defaults to today.
            
        Returns:
            dict: Statistics about created/updated rates.
        """
        if date_obj is None:
            date_obj = timezone.now().date()
            
        formatted_date = date_obj.strftime("%d.%m.%Y")
        url = f"{cls.RSS_URL}?fdate={formatted_date}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = xmltodict.parse(response.content)
            
            # Try different XML structures (rss/channel/item or rates/item)
            items = []
            if 'rss' in data and 'channel' in data['rss']:
                 items = data['rss']['channel'].get('item', [])
            elif 'rates' in data:
                 items = data['rates'].get('item', [])
            
            stats = {
                'created': 0,
                'updated': 0,
                'skipped_manual': 0,
                'errors': 0
            }
            
            if not isinstance(items, list):
                items = [items]
                
            valid_currencies = ['USD', 'EUR', 'RUB', 'CNY'] # We only care about these for now based on model choices
            
            for item in items:
                currency_code = item.get('title', '').strip()
                
                # Check if we support this currency in our model
                if currency_code not in valid_currencies:
                    continue
                    
                description = item.get('description', '').strip()
                # Parse rate value (handle comma/dot)
                # Note: NB RK often returns quantity + code, e.g. depending on format, but description is usually just number
                # Let's verify format. Usually description is just the rate.
                
                try:
                    # NB RK description usually implies amount for 'quant' units, but for major currencies it is for 1 unit usually? 
                    # Wait, NB RK RSS: <quant>1</quant> <index>USD</index> <description>450.00</description>
                    # Actually valid XML usually has <description>450.00</description>
                    
                    rate_value_str = description.replace(',', '.')
                    rate_value = Decimal(rate_value_str)
                    
                    # Check for manual override
                    # If there's already a manual entry for this date/currency, skip
                    existing_manual = ExchangeRate.objects.filter(
                        rate_date=date_obj,
                        currency_from=currency_code,
                        currency_to='KZT',
                        source='manual'
                    ).exists()
                    
                    if existing_manual:
                        stats['skipped_manual'] += 1
                        continue
                        
                    # Update or Create
                    obj, created = ExchangeRate.objects.update_or_create(
                        rate_date=date_obj,
                        currency_from=currency_code,
                        currency_to='KZT',
                        defaults={
                            'rate_value': rate_value,
                            'source': 'api_nbrk',
                            'is_active': True,
                            'is_official': True
                        }
                    )
                    
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                        
                except Exception as e:
                    print(f"Error processing {currency_code}: {e}")
                    stats['errors'] += 1
                    
            return stats
            
        except Exception as e:
            print(f"Sync error: {e}")
            raise

    @classmethod
    def prune_old_rates(cls, days: int = 31):
        """Удаляем курсы старше заданного количества дней (по дате курса)."""
        cutoff = timezone.now().date() - timedelta(days=days)
        qs = ExchangeRate.objects.filter(rate_date__lt=cutoff)
        deleted_count, _ = qs.delete()
        return deleted_count
