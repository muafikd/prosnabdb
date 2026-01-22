# Анализ проблемы с calculated_data в EquipmentListItem

## Проблема
Сохраненные цифры при следующем редактировании показывают неправильные значения.

## Текущий поток данных

### 1. Сохранение КП (модальная форма "Расчет КП")

**Фронтенд (ProposalsView.vue, handleSubmit):**
- Отправляет только: `equipment_id`, `quantity`, `row_expenses`
- НЕ отправляет расчетные данные (calculated_data)

**Бэкенд (views.py, perform_update):**
1. Сохраняет КП через serializer
2. Вызывает `DataAggregatorService.get_full_data_package()`
3. Это пересчитывает все данные заново на основе ТЕКУЩИХ цен оборудования
4. Вызывает `_save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])`

**Функция _save_prices_to_equipment_list_items (serializers.py:1161-1205):**
Сохраняет в `calculated_data`:
- `base_cost_kzt` - из `item.get('base_cost_kzt')`
- `allocated_overhead_per_unit` - из `item.get('allocated_overhead_per_unit')`
- `margin_kzt` - из `item.get('margin_kzt')`
- `margin_percentage` - из `item.get('margin_percentage')`
- `purchase_price_kzt` - из `item.get('purchase_price_kzt')`

**Источник данных (services.py, _calculate_and_build_equipment_list):**
- `base_cost_kzt` = `base_unit_cost_kzt` (purchase price + row expenses)
- `allocated_overhead_per_unit` = распределенные общие расходы
- `margin_kzt` = `margin_kzt_per_unit` = `sale_price_kzt - (base_unit_cost_kzt + allocated_overhead_per_unit)`
- `margin_percentage` = `(margin_kzt_per_unit / base_unit_cost_kzt) * 100`
- `purchase_price_kzt` = цена закупки ДО row expenses

**Важно:** Все расчеты основаны на ТЕКУЩИХ значениях:
- `sale_price_kzt` из Equipment (может измениться!)
- `purchase_price` из Equipment (может измениться!)
- `row_expenses` из EquipmentListItem (может измениться!)
- Общие расходы из EquipmentList (может измениться!)

### 2. Загрузка КП для редактирования

**Фронтенд (ProposalsView.vue, handleEdit):**
1. Загружает КП через API
2. Получает `equipment_items_data` из `equipment_lists[0].equipment_items_data`
3. Каждый item содержит `calculated_data` из EquipmentListItem
4. Использует сохраненные значения:
   ```javascript
   const savedCalculatedData = item.calculated_data || {}
   purchase_price_kzt: savedCalculatedData.purchase_price_kzt || fallbackData.purchase_price_kzt
   base_cost_kzt: savedCalculatedData.base_cost_kzt || fallbackData.base_cost_kzt
   allocated_overhead_per_unit: savedCalculatedData.allocated_overhead_per_unit || fallbackData.allocated_overhead_per_unit
   margin_kzt: savedCalculatedData.margin_kzt || fallbackData.margin_kzt
   margin_percentage: savedCalculatedData.margin_percentage || fallbackData.margin_percentage
   sale_price_kzt: savedPricePerUnit || fallbackData.price_per_unit
   ```

## Проблема

При сохранении КП происходит **пересчет всех данных заново** на основе текущих цен оборудования. Если:
- Цена оборудования (`sale_price_kzt`) изменилась
- Цена закупки изменилась
- Общие расходы изменились
- Row expenses изменились

То сохраненные значения в `calculated_data` будут **другими**, чем те, что были при предыдущем сохранении.

## Возможные причины несоответствия

1. **Цены оборудования изменились** - при сохранении пересчитываются на основе новых цен
2. **Общие расходы изменились** - `allocated_overhead_per_unit` пересчитывается
3. **Row expenses изменились** - `base_cost_kzt` пересчитывается
4. **Курсы валют изменились** - если используются внутренние курсы КП
5. **Данные не сохраняются правильно** - нужно проверить логику сохранения
6. **Данные не загружаются правильно** - нужно проверить логику загрузки

## Рекомендации для проверки

1. Проверить, что именно сохраняется в `calculated_data` при сохранении КП
2. Проверить, что именно загружается из `calculated_data` при редактировании КП
3. Сравнить сохраненные значения с теми, что показываются в форме
4. Проверить, не изменяются ли цены оборудования между сохранениями
5. Проверить, не изменяются ли общие расходы между сохранениями

## Выводы

### Что сохраняется в calculated_data:
- `base_cost_kzt` - себестоимость единицы (цена закупки + расходы на строку)
- `allocated_overhead_per_unit` - распределенные общие расходы на единицу
- `margin_kzt` - маржа в тенге на единицу
- `margin_percentage` - маржа в процентах
- `purchase_price_kzt` - цена закупки в тенге (ДО добавления расходов на строку)

### Откуда загружаются данные:
- Из `equipment_items_data[].calculated_data` (EquipmentListItem)
- Fallback на `data_package.equipment_list[]` если calculated_data пусто

### Потенциальная проблема:
При сохранении КП всегда происходит **пересчет** всех данных на основе текущих цен оборудования. Если между сохранениями изменились:
- Цены оборудования (sale_price_kzt)
- Цены закупки
- Общие расходы
- Курсы валют

То сохраненные значения будут **другими**, чем при предыдущем сохранении.
