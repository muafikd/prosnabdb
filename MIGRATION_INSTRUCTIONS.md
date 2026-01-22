# Инструкция по применению миграции и тестированию функционала

## Шаг 1: Выполнение миграции

Выполните миграцию для добавления полей `price_per_unit` и `total_price` в таблицу `equipment_list_item`:

```bash
python manage.py migrate proposals
```

Или если используете виртуальное окружение:

```bash
source venv/bin/activate  # или ваш путь к venv
python manage.py migrate proposals
```

## Шаг 2: Проверка миграции

После выполнения миграции проверьте, что поля добавлены:

```bash
python manage.py showmigrations proposals
```

Должна быть отмечена миграция `0035_add_price_fields_to_equipment_list_item`.

## Шаг 3: Тестирование функционала

### Вариант 1: Через скрипт проверки

```bash
python test_price_saving.py
```

### Вариант 2: Через Django shell

```bash
python manage.py shell
```

Затем выполните:

```python
from proposals.models import EquipmentListItem

# Проверка наличия полей
fields = [f.name for f in EquipmentListItem._meta.get_fields()]
print('price_per_unit' in fields)  # Должно быть True
print('total_price' in fields)     # Должно быть True

# Проверка данных (после сохранения шаблона)
items = EquipmentListItem.objects.filter(price_per_unit__isnull=False)
print(f"Записей с ценами: {items.count()}")
```

## Шаг 4: Тестирование в интерфейсе

1. Откройте конструктор предложений в браузере
2. Выберите существующее КП или создайте новое
3. Убедитесь, что в конструкторе отображается таблица цен
4. Сохраните шаблон (кнопка "Сохранить")
5. Проверьте в базе данных, что цены сохранились:

```sql
SELECT 
    eli.equipment_id,
    e.equipment_name,
    eli.quantity,
    eli.price_per_unit,
    eli.total_price
FROM equipment_list_item eli
JOIN equipment e ON eli.equipment_id = e.equipment_id
WHERE eli.price_per_unit IS NOT NULL;
```

## Что было реализовано

1. ✅ Добавлены поля `price_per_unit` и `total_price` в модель `EquipmentListItem`
2. ✅ Создана миграция `0035_add_price_fields_to_equipment_list_item.py`
3. ✅ Реализована функция `_save_prices_to_equipment_list_items()` для сохранения цен
4. ✅ Обновлена логика сохранения в:
   - `ProposalTemplateSerializer.update()` - при сохранении шаблона
   - `ProposalTemplateSerializer.create()` - при создании шаблона
   - `refresh_data_package()` - при обновлении данных из КП

## Как это работает

1. При расчете цен в конструкторе `DataAggregatorService` вычисляет итоговые цены с распределением общих расходов
2. Цены сохраняются в `data_package.equipment_list` как `price_per_unit` и `total_price`
3. При сохранении шаблона автоматически вызывается `_save_prices_to_equipment_list_items()`
4. Функция находит соответствующие записи `EquipmentListItem` и обновляет их поля `price_per_unit` и `total_price`

## Проверка работы

После сохранения шаблона в конструкторе проверьте:

1. В базе данных должны быть заполнены поля `price_per_unit` и `total_price` в таблице `equipment_list_item`
2. Значения должны соответствовать ценам из `data_package.equipment_list`
3. При обновлении данных через кнопку "Обновить данные из КП" цены должны пересчитываться и сохраняться заново
