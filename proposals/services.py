"""
Services module for business logic, including cost calculation.
"""
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
from .models import (
    Equipment, PurchasePrice, Logistics, AdditionalPrices, ExchangeRate,
    CostCalculation, CommercialProposal
)


class CostCalculationService:
    """Service for calculating equipment cost."""
    
    @staticmethod
    def convert_currency(amount, from_currency, to_currency, date=None, proposal=None, manual_rate_value=None):
        """
        Конвертировать сумму из одной валюты в другую.
        
        Args:
            amount: Сумма для конвертации
            from_currency: Валюта "из"
            to_currency: Валюта "в"
            date: Дата курса (если None, используется сегодня)
            proposal: КП для получения корректировки курса
            manual_rate_value: Ручное значение курса (если указано, используется вместо поиска в БД)
        
        Returns:
            Decimal: Конвертированная сумма
        """
        if from_currency == to_currency:
            return Decimal(str(amount))
        
        # Использовать ручной курс, если указан
        if manual_rate_value is not None:
            rate_value = Decimal(str(manual_rate_value))
        else:
            # Получить курс валюты из БД
            rate = ExchangeRate.get_latest_rate(
                currency_from=from_currency,
                currency_to=to_currency,
                date=date,
                proposal=proposal
            )
            
            if not rate:
                raise ValueError(
                    f'Exchange rate not found for {from_currency}/{to_currency}'
                    + (f' on {date}' if date else '')
                    + '. Please provide exchange rate in the proposal or create it manually.'
                )
            
            rate_value = rate.rate_value
        
        # Конвертировать
        converted_amount = Decimal(str(amount)) * rate_value
        return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_equipment_cost(
        equipment,
        purchase_price_id=None,
        logistics_id=None,
        additional_prices_id=None,
        exchange_rate_date=None,
        proposal=None,
        target_currency='KZT',
        manual_overrides=None
    ):
        """
        Рассчитать себестоимость оборудования по формуле:
        Себестоимость в KZT = (закупочная цена + логистика + склад + производственные расходы + доп.расходы)
        где все компоненты конвертируются в KZT через курс валюты из КП
        
        Args:
            equipment: Equipment объект
            purchase_price_id: ID конкретной цены закупки (если None, берется активная)
            logistics_id: ID конкретной логистики (если None, берется активная)
            additional_prices_id: ID дополнительных расходов (если None, не учитываются)
            exchange_rate_date: Дата курса валюты (если None, используется сегодня)
            proposal: CommercialProposal для получения корректировок курса
            target_currency: Целевая валюта для результата (по умолчанию KZT)
            manual_overrides: Словарь с ручными переопределениями значений
        
        Returns:
            dict: Словарь с результатами расчета
        """
        if exchange_rate_date is None:
            exchange_rate_date = timezone.now().date()
        
        manual_overrides = manual_overrides or {}
        
        # 1. Закупочная цена
        purchase_price_value = Decimal('0')
        purchase_price_currency = None
        purchase_price_source = None
        purchase_price_obj = None
        
        if purchase_price_id:
            try:
                purchase_price_obj = PurchasePrice.objects.get(
                    price_id=purchase_price_id,
                    equipment=equipment,
                    is_active=True
                )
            except PurchasePrice.DoesNotExist:
                raise ValueError(f'Purchase price with ID {purchase_price_id} not found')
        else:
            # Берем активную цену закупки
            purchase_price_obj = PurchasePrice.objects.filter(
                equipment=equipment,
                is_active=True
            ).order_by('-created_at').first()
        
        if purchase_price_obj:
            purchase_price_value = Decimal(str(purchase_price_obj.price))
            purchase_price_currency = purchase_price_obj.currency
            purchase_price_source = purchase_price_obj.source_type
        
        # Ручное переопределение
        if 'purchase_price' in manual_overrides:
            purchase_price_value = Decimal(str(manual_overrides['purchase_price']))
            if 'purchase_price_currency' in manual_overrides:
                purchase_price_currency = manual_overrides['purchase_price_currency']
        
        # 2. Логистика - суммируем все активные логистики (кроме склада kz_warehouse)
        logistics_cost = Decimal('0')
        logistics_currency = None
        logistics_route = None
        logistics_obj = None
        
        if logistics_id:
            try:
                logistics_obj = Logistics.objects.get(
                    logistics_id=logistics_id,
                    equipment=equipment,
                    is_active=True
                )
                logistics_cost = Decimal(str(logistics_obj.cost))
                logistics_currency = logistics_obj.currency
                logistics_route = logistics_obj.route_type
            except Logistics.DoesNotExist:
                raise ValueError(f'Logistics with ID {logistics_id} not found')
        else:
            # Суммируем все активные логистики (кроме склада kz_warehouse)
            active_logistics = Logistics.objects.filter(
                equipment=equipment,
                is_active=True
            ).exclude(route_type='kz_warehouse').order_by('-created_at')
            
            if active_logistics.exists():
                # Берем первую для route_type (для обратной совместимости)
                logistics_obj = active_logistics.first()
                logistics_route = logistics_obj.route_type
                logistics_currency = logistics_obj.currency
                # Суммируем логистики в основной валюте (конвертация всех в KZT будет позже)
                logistics_cost = sum(Decimal(str(l.cost)) for l in active_logistics if l.currency == logistics_currency)
        
        # Ручное переопределение
        if 'logistics_cost' in manual_overrides:
            logistics_cost = Decimal(str(manual_overrides['logistics_cost']))
            if 'logistics_currency' in manual_overrides:
                logistics_currency = manual_overrides['logistics_currency']
        
        # 3. Склад (из логистики с маршрутом kz_warehouse)
        warehouse_cost = Decimal('0')
        warehouse_currency = None
        
        warehouse_logistics = Logistics.objects.filter(
            equipment=equipment,
            route_type='kz_warehouse',
            is_active=True
        ).first()
        
        if warehouse_logistics:
            warehouse_cost = Decimal(str(warehouse_logistics.cost))
            warehouse_currency = warehouse_logistics.currency
        
        # Ручное переопределение
        if 'warehouse_cost' in manual_overrides:
            warehouse_cost = Decimal(str(manual_overrides['warehouse_cost']))
            if 'warehouse_currency' in manual_overrides:
                warehouse_currency = manual_overrides['warehouse_currency']
        
        # 4. Производственные расходы
        production_cost = Decimal('0')
        production_currency = None
        
        if equipment.equipment_manufacture_price:
            production_cost = Decimal(str(equipment.equipment_manufacture_price))
            production_currency = equipment.equipment_price_currency_type or 'KZT'
        
        # Ручное переопределение
        if 'production_cost' in manual_overrides:
            production_cost = Decimal(str(manual_overrides['production_cost']))
            if 'production_currency' in manual_overrides:
                production_currency = manual_overrides['production_currency']
        
        # 5. Дополнительные расходы (AdditionalPrices) - будут рассчитаны после базовой себестоимости
        # Сначала собираем информацию о доп.расходах
        additional_prices_list = []
        
        # Если есть proposal, проверяем EquipmentList для этого оборудования
        if proposal:
            from .models import EquipmentList, EquipmentListItem
            # Ищем EquipmentList в этом КП, который содержит это оборудование
            equipment_lists = EquipmentList.objects.filter(
                proposal=proposal
            ).prefetch_related('equipment_items_relation', 'additional_prices')
            
            for eq_list in equipment_lists:
                # Проверяем, есть ли это оборудование в списке
                if eq_list.equipment_items_relation.filter(equipment=equipment).exists():
                    # Собираем все дополнительные расходы
                    if eq_list.additional_prices.exists():
                        additional_prices_list.extend(eq_list.additional_prices.all())
                    # Поддержка старого поля для обратной совместимости
                    elif eq_list.additional_price:
                        additional_prices_list.append(eq_list.additional_price)
                    break
        
        # Если указан конкретный additional_prices_id
        if additional_prices_id:
            try:
                additional_prices_obj = AdditionalPrices.objects.get(price_id=additional_prices_id)
                additional_prices_list.append(additional_prices_obj)
            except AdditionalPrices.DoesNotExist:
                pass
        
        # Ручное переопределение - если указано, используем его вместо расчетных
        manual_additional_costs = None
        if 'additional_costs' in manual_overrides:
            manual_additional_costs = Decimal(str(manual_overrides['additional_costs']))
        
        # 6. Конвертация всех сумм в базовую валюту (KZT) через курс валюты
        service = CostCalculationService()
        
        # Получаем ручной курс валюты, если указан
        manual_rate_value = manual_overrides.get('exchange_rate_value')
        # Если курс не указан вручную, но есть proposal с курсом, используем его
        if not manual_rate_value and proposal and proposal.exchange_rate:
            manual_rate_value = proposal.exchange_rate
        
        # Определяем базовую валюту для расчета (валюта закупочной цены или KZT)
        base_currency = purchase_price_currency or 'KZT'
        
        # Конвертируем все компоненты в базовую валюту (KZT)
        # 1. Закупочная цена
        purchase_price_base = purchase_price_value
        if purchase_price_currency and purchase_price_currency != 'KZT':
            try:
                purchase_price_base = service.convert_currency(
                    purchase_price_value,
                    purchase_price_currency,
                    'KZT',
                    date=exchange_rate_date,
                    proposal=proposal,
                    manual_rate_value=manual_rate_value
                )
            except ValueError as e:
                # Если не удалось конвертировать, используем исходное значение
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to convert purchase price from {purchase_price_currency} to KZT: {e}')
                purchase_price_base = purchase_price_value
        
        # 2. Логистика - суммируем все активные логистики, конвертируя каждую в KZT
        logistics_base = Decimal('0')
        if not logistics_id:
            # Берем все активные логистики (кроме склада)
            active_logistics = Logistics.objects.filter(
                equipment=equipment,
                is_active=True
            ).exclude(route_type='kz_warehouse')
            
            for log in active_logistics:
                log_cost = Decimal(str(log.cost))
                if log.currency == 'KZT':
                    logistics_base += log_cost
                else:
                    try:
                        # Конвертируем в KZT через курс из КП
                        log_cost_kzt = service.convert_currency(
                            log_cost,
                            log.currency,
                            'KZT',
                            date=exchange_rate_date,
                            proposal=proposal,
                            manual_rate_value=manual_rate_value
                        )
                        logistics_base += log_cost_kzt
                    except ValueError as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f'Failed to convert logistics from {log.currency} to KZT: {e}')
                        # Если не удалось конвертировать, пропускаем эту логистику
        elif logistics_cost > 0:
            # Если указана конкретная логистика или есть ручное переопределение
            if logistics_currency and logistics_currency != 'KZT':
                try:
                    logistics_base = service.convert_currency(
                        logistics_cost,
                        logistics_currency,
                        'KZT',
                        date=exchange_rate_date,
                        proposal=proposal,
                        manual_rate_value=manual_rate_value
                    )
                except ValueError as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to convert logistics from {logistics_currency} to KZT: {e}')
                    logistics_base = logistics_cost
            else:
                logistics_base = logistics_cost
        
        # 3. Склад
        warehouse_base = warehouse_cost
        if warehouse_currency and warehouse_currency != 'KZT':
            try:
                warehouse_base = service.convert_currency(
                    warehouse_cost,
                    warehouse_currency,
                    'KZT',
                    date=exchange_rate_date,
                    proposal=proposal,
                    manual_rate_value=manual_rate_value
                )
            except ValueError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to convert warehouse cost from {warehouse_currency} to KZT: {e}')
                warehouse_base = warehouse_cost
        
        # 4. Производственные расходы
        production_base = production_cost
        if production_currency and production_currency != 'KZT':
            try:
                production_base = service.convert_currency(
                    production_cost,
                    production_currency,
                    'KZT',
                    date=exchange_rate_date,
                    proposal=proposal,
                    manual_rate_value=manual_rate_value
                )
            except ValueError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to convert production cost from {production_currency} to KZT: {e}')
                production_base = production_cost
        
        # 6. Рассчитываем базовую себестоимость (без доп.расходов)
        base_cost_kzt = (
            purchase_price_base +
            logistics_base +
            warehouse_base +
            production_base
        )
        
        # 7. Рассчитываем дополнительные расходы на основе базовой себестоимости
        additional_base = Decimal('0')
        
        # Если есть ручное переопределение, используем его
        if manual_additional_costs is not None:
            additional_base = manual_additional_costs
        else:
            # Рассчитываем дополнительные расходы по их типам
            for additional_price in additional_prices_list:
                value = Decimal(str(additional_price.price_parameter_value))
                
                if additional_price.value_type == 'percentage':
                    # Процент от базовой себестоимости
                    additional_base += base_cost_kzt * (value / Decimal('100'))
                elif additional_price.value_type == 'fixed':
                    # Фиксированная сумма
                    additional_base += value
                elif additional_price.value_type == 'coefficient':
                    # Коэффициент умножения базовой себестоимости
                    additional_base += base_cost_kzt * value
        
        # 8. Итоговая себестоимость в KZT (сумма всех компонентов)
        # Формула: Себестоимость = (закупочная цена + логистика + склад + производство) + доп.расходы
        total_cost_kzt = base_cost_kzt + additional_base
        
        # 8. Конвертация в целевую валюту (если не KZT)
        # Если целевая валюта не KZT, конвертируем через курс
        total_cost_target = total_cost_kzt
        if target_currency != 'KZT':
            try:
                # Для конвертации из KZT в целевую валюту
                # Если есть manual_rate_value из proposal, это курс из целевой валюты в KZT
                # Например, если proposal.currency_ticket = RUB, manual_rate_value = курс RUB/KZT
                # То для конвертации KZT -> RUB нужен обратный курс: 1 / manual_rate_value
                reverse_rate_value = None
                if manual_rate_value and proposal and proposal.currency_ticket == target_currency:
                    # Если целевая валюта совпадает с валютой КП, используем обратный курс
                    reverse_rate_value = Decimal('1') / Decimal(str(manual_rate_value))
                
                total_cost_target = service.convert_currency(
                    total_cost_kzt,
                    'KZT',
                    target_currency,
                    date=exchange_rate_date,
                    proposal=proposal,
                    manual_rate_value=reverse_rate_value
                )
            except ValueError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to convert total cost from KZT to {target_currency}: {e}')
                # Если не удалось конвертировать, оставляем в KZT
                total_cost_target = total_cost_kzt
        
        # 9. Получить курс валюты для сохранения
        exchange_rate = ExchangeRate.get_latest_rate(
            currency_from=purchase_price_currency or 'KZT',
            currency_to='KZT',
            date=exchange_rate_date,
            proposal=proposal
        )
        
        # 10. Формируем результат
        result = {
            'equipment_id': equipment.equipment_id,
            'equipment_name': equipment.equipment_name,
            'purchase_price': {
                'id': purchase_price_obj.price_id if purchase_price_obj else None,
                'value': float(purchase_price_value),
                'currency': purchase_price_currency,
                'source': purchase_price_source,
                'value_kzt': float(purchase_price_base),
            },
            'logistics': {
                'id': logistics_obj.logistics_id if logistics_obj else None,
                'cost': float(logistics_cost),
                'currency': logistics_currency,
                'route': logistics_route,
                'cost_kzt': float(logistics_base),
            },
            'warehouse': {
                'cost': float(warehouse_cost),
                'currency': warehouse_currency,
                'cost_kzt': float(warehouse_base),
            },
            'production': {
                'cost': float(production_cost),
                'currency': production_currency,
                'cost_kzt': float(production_base),
            },
            'additional_costs': {
                'id': additional_prices_id,
                'cost': float(additional_base),  # Используем рассчитанное значение в KZT
                'currency': 'KZT',  # Дополнительные расходы всегда в KZT после расчета
                'cost_kzt': float(additional_base),
            },
            'exchange_rate': {
                'id': exchange_rate.rate_id if exchange_rate else None,
                'value': float(exchange_rate.rate_value) if exchange_rate else 1.0,
                'from_currency': exchange_rate.currency_from if exchange_rate else 'KZT',
                'to_currency': exchange_rate.currency_to if exchange_rate else 'KZT',
                'date': str(exchange_rate.rate_date) if exchange_rate else str(exchange_rate_date),
            },
            'total_cost_kzt': float(total_cost_kzt),
            'total_cost_target_currency': float(total_cost_target),
            'target_currency': target_currency,
            'calculation_date': str(exchange_rate_date),
        }
        
        return result
    
    @staticmethod
    @transaction.atomic
    def save_calculation(
        equipment,
        calculation_result,
        proposal=None,
        created_by=None,
        is_manual_adjustment=False,
        notes=None
    ):
        """
        Сохранить расчет себестоимости в базу данных.
        
        Args:
            equipment: Equipment объект
            calculation_result: Результат расчета из calculate_equipment_cost
            proposal: CommercialProposal (опционально)
            created_by: User (опционально)
            is_manual_adjustment: Флаг ручной корректировки
            notes: Примечания
        
        Returns:
            CostCalculation: Созданный объект расчета
        """
        # Определить версию расчета
        if proposal:
            last_version = CostCalculation.objects.filter(
                equipment=equipment,
                proposal=proposal
            ).order_by('-calculation_version').first()
        else:
            last_version = CostCalculation.objects.filter(
                equipment=equipment,
                proposal__isnull=True
            ).order_by('-calculation_version').first()
        
        next_version = (last_version.calculation_version + 1) if last_version else 1
        
        # Создать запись расчета
        calculation = CostCalculation.objects.create(
            equipment=equipment,
            proposal=proposal,
            calculation_version=next_version,
            purchase_price_id=calculation_result['purchase_price']['id'],
            purchase_price_value=calculation_result['purchase_price']['value'],
            purchase_price_currency=calculation_result['purchase_price']['currency'],
            purchase_price_source=calculation_result['purchase_price']['source'],
            logistics_id=calculation_result['logistics']['id'],
            logistics_cost=calculation_result['logistics']['cost'],
            logistics_currency=calculation_result['logistics']['currency'],
            logistics_route=calculation_result['logistics']['route'],
            warehouse_cost=calculation_result['warehouse']['cost'],
            warehouse_currency=calculation_result['warehouse']['currency'],
            production_cost=calculation_result['production']['cost'],
            production_currency=calculation_result['production']['currency'],
            additional_costs=calculation_result['additional_costs']['cost'],
            additional_costs_currency=calculation_result['additional_costs']['currency'] or 'KZT',
            exchange_rate_id=calculation_result['exchange_rate']['id'],
            exchange_rate_value=calculation_result['exchange_rate']['value'],
            exchange_rate_from=calculation_result['exchange_rate']['from_currency'],
            exchange_rate_to=calculation_result['exchange_rate']['to_currency'],
            exchange_rate_date=calculation_result['exchange_rate']['date'],
            total_cost_base_currency=calculation_result['total_cost_kzt'],
            total_cost_kzt=calculation_result['total_cost_kzt'],
            calculation_details=calculation_result,
            is_manual_adjustment=is_manual_adjustment,
            notes=notes,
            created_by=created_by,
        )
        
        return calculation
    
    @staticmethod
    def calculate_proposal_total_price(cost_price, margin_percentage=None):
        """
        Рассчитать итоговую цену КП на основе себестоимости и маржи.
        
        Формула: total_price = cost_price * (1 + margin_percentage / 100)
        
        Args:
            cost_price: Себестоимость (сумма всех себестоимостей оборудования)
            margin_percentage: Процент маржи (если None, маржа не добавляется)
        
        Returns:
            Decimal: Итоговая цена
        """
        cost_price_decimal = Decimal(str(cost_price))
        
        if margin_percentage is None or margin_percentage == 0:
            return cost_price_decimal
        
        margin_decimal = Decimal(str(margin_percentage))
        total_price = cost_price_decimal * (Decimal('1') + margin_decimal / Decimal('100'))
        
        return total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_proposal_cost_price(proposal):
        """
        Рассчитать общую себестоимость КП на основе всех оборудования в EquipmentList.
        
        Args:
            proposal: CommercialProposal объект
        
        Returns:
            Decimal: Общая себестоимость
        """
        from .models import EquipmentListItem
        
        total_cost = Decimal('0')
        
        # Проходим по всем EquipmentList в КП
        for equipment_list in proposal.equipment_lists.all():
            # Проходим по всем EquipmentListItem
            for item in equipment_list.equipment_items_relation.all():
                equipment = item.equipment
                quantity = item.quantity
                
                # Рассчитываем себестоимость для этого оборудования
                try:
                    calculation_result = CostCalculationService.calculate_equipment_cost(
                        equipment=equipment,
                        exchange_rate_date=proposal.exchange_rate_date or None,
                        proposal=proposal,
                        target_currency=proposal.currency_ticket,
                        manual_overrides={'exchange_rate_value': proposal.exchange_rate} if proposal.exchange_rate else None
                    )
                    
                    # Себестоимость единицы оборудования в целевой валюте
                    unit_cost = Decimal(str(calculation_result['total_cost_target_currency']))
                    
                    # Учитываем количество
                    item_total_cost = unit_cost * quantity
                    total_cost += item_total_cost
                    
                except Exception as e:
                    # Если не удалось рассчитать, пропускаем это оборудование
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to calculate cost for equipment {equipment.equipment_id}: {str(e)}')
                    continue
        
        return total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

