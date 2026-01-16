# Схема базы данных

## Таблицы и поля

### 1. users
**Таблица:** users  
**Модель:** User

**Поля:**
- `user_id` (PK, AutoField) - ID пользователя
- `user_name` (CharField, 255) - Имя пользователя
- `user_phone` (CharField, 20, nullable) - Телефон
- `user_email` (EmailField, unique) - Email
- `user_login` (CharField, 150, unique) - Логин
- `user_role` (CharField, 50) - Роль: Администратор, Менеджер, Просмотр
- `is_active` (BooleanField) - Активен
- `is_staff` (BooleanField) - Персонал
- `is_superuser` (BooleanField) - Суперпользователь
- `date_joined` (DateTimeField) - Дата регистрации
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления
- `password` (CharField) - Пароль (из AbstractBaseUser)

**Связи:**
- `CommercialProposal.user_id` → User (FK)

---

### 2. clients
**Таблица:** clients  
**Модель:** Client

**Поля:**
- `client_id` (PK, AutoField) - ID клиента
- `client_name` (CharField, 255) - Имя клиента
- `client_phone` (CharField, 20, nullable) - Телефон клиента
- `client_email` (EmailField, nullable) - Email клиента
- `client_company_name` (CharField, 255, nullable) - Название компании
- `client_type` (CharField, 50, nullable) - Тип клиента
- `client_bin_iin` (CharField, 20, nullable) - БИН/ИИН
- `client_address` (TextField, nullable) - Адрес клиента
- `client_bik` (TextField, nullable) - БИК
- `client_iik` (TextField, nullable) - ИИК
- `client_bankname` (CharField, 255, nullable) - Название банка
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `CommercialProposal.client_id` → Client (FK)

---

### 3. category
**Таблица:** category  
**Модель:** Category

**Поля:**
- `category_id` (PK, AutoField) - ID категории
- `category_name` (CharField, 255, unique) - Название категории
- `category_description` (TextField, nullable) - Описание категории
- `parent_category_id` (FK, nullable) - Родительская категория (self-reference)
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Category.parent_category` → Category (FK, self-reference)
- `Equipment.category_id` → Category (FK)

---

### 4. manufacturer
**Таблица:** manufacturer  
**Модель:** Manufacturer

**Поля:**
- `manufacturer_id` (PK, AutoField) - ID производителя
- `manufacturer_name` (CharField, 255, unique) - Название производителя
- `manufacturer_country` (CharField, 100, nullable) - Страна производителя
- `manufacturer_website` (URLField, nullable) - Сайт производителя
- `manufacturer_description` (TextField, nullable) - Описание
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Equipment.manufacturer_id` → Manufacturer (FK)

---

### 5. equipment_types
**Таблица:** equipment_types  
**Модель:** EquipmentTypes

**Поля:**
- `type_id` (PK, AutoField) - ID типа
- `type_name` (CharField, 255, unique) - Название типа
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Equipment.equipment_type_id` → EquipmentTypes (FK)

---

### 6. equipment_details
**Таблица:** equipment_details  
**Модель:** EquipmentDetails

**Поля:**
- `detail_id` (PK, AutoField) - ID детали
- `detail_parameter_name` (CharField, 255) - Название параметра
- `detail_parameter_value` (TextField, nullable) - Значение параметра
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Equipment.detail_id` → EquipmentDetails (FK)

---

### 7. equipment_specification
**Таблица:** equipment_specification  
**Модель:** EquipmentSpecification

**Поля:**
- `spec_id` (PK, AutoField) - ID спецификации
- `spec_parameter_name` (CharField, 255) - Название параметра
- `spec_parameter_value` (TextField, nullable) - Значение параметра
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

---

### 8. equipment_tech_proccess
**Таблица:** equipment_tech_proccess  
**Модель:** EquipmentTechProcess

**Поля:**
- `tech_id` (PK, AutoField) - ID процесса
- `tech_name` (CharField, 255) - Название процесса
- `tech_value` (CharField, 255, nullable) - Значение
- `tech_desc` (TextField, nullable) - Описание
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Equipment.equipment_tech_process_id` → EquipmentTechProcess (FK)

---

### 9. equipment
**Таблица:** equipment  
**Модель:** Equipment

**Поля:**
- `equipment_id` (PK, AutoField) - ID оборудования
- `equipment_name` (CharField, 255) - Название оборудования
- `equipment_articule` (CharField, 100, nullable) - Артикул
- `equipment_uom` (CharField, 50, nullable) - Единица измерения
- `equipment_short_description` (TextField, nullable) - Краткое описание
- `equipment_warranty` (CharField, 100, nullable) - Гарантия
- `is_published` (BooleanField) - Опубликовано на сайте
- `category_id` (FK, nullable) - Категория
- `manufacturer_id` (FK, nullable) - Производитель
- `detail_id` (FK, nullable) - Детали оборудования
- `spec_id` (FK, nullable) - Спецификация оборудования
- `equipment_type_id` (FK, nullable) - Тип оборудования
- `equipment_tech_process_id` (FK, nullable) - Технологический процесс
- `equipment_imagelinks` (TextField, nullable) - Ссылки на изображения
- `equipment_videolinks` (TextField, nullable) - Ссылки на видео
- `equipment_manufacture_price` (DecimalField, nullable) - Цена производства
- `equipment_madein_country` (CharField, 100, nullable) - Страна производства
- `equipment_price_currency_type` (CharField, 10, nullable) - Тип валюты
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Equipment.category_id` → Category (FK)
- `Equipment.manufacturer_id` → Manufacturer (FK)
- `Equipment.detail_id` → EquipmentDetails (FK)
- `Equipment.spec_id` → EquipmentSpecification (FK)
- `Equipment.equipment_type_id` → EquipmentTypes (FK)
- `Equipment.equipment_tech_process_id` → EquipmentTechProcess (FK)
- `PurchasePrice.equipment` → Equipment (FK)
- `Logistics.equipment` → Equipment (FK)
- `EquipmentDocument.equipment` → Equipment (FK)
- `EquipmentLineItem.equipment` → Equipment (FK)
- `EquipmentList.equipment_id` → Equipment (FK)

---

### 10. purchase_price
**Таблица:** purchase_price  
**Модель:** PurchasePrice

**Поля:**
- `price_id` (PK, AutoField) - ID цены
- `equipment_id` (FK) - Оборудование
- `source_type` (CharField, 20) - Источник: russia, china, own_production, other
- `price` (DecimalField, 15, 2) - Цена закупки
- `currency` (CharField, 10) - Валюта
- `is_active` (BooleanField) - Активен
- `notes` (TextField, nullable) - Примечания
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `PurchasePrice.equipment` → Equipment (FK)

---

### 11. logistics
**Таблица:** logistics  
**Модель:** Logistics

**Поля:**
- `logistics_id` (PK, AutoField) - ID логистики
- `equipment_id` (FK) - Оборудование
- `route_type` (CharField, 20) - Маршрут: china_kz, russia_kz, kz_warehouse, other
- `cost` (DecimalField, 15, 2) - Стоимость доставки
- `currency` (CharField, 10) - Валюта
- `estimated_days` (PositiveIntegerField, nullable) - Срок доставки (дней)
- `is_active` (BooleanField) - Активен
- `notes` (TextField, nullable) - Примечания
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `Logistics.equipment` → Equipment (FK)

---

### 12. equipment_document
**Таблица:** equipment_document  
**Модель:** EquipmentDocument

**Поля:**
- `document_id` (PK, AutoField) - ID документа
- `equipment_id` (FK) - Оборудование
- `document_type` (CharField, 20) - Тип: passport, certificate, declaration, estimate, manual, other
- `document_name` (CharField, 255) - Название документа
- `file` (FileField, nullable) - Файл
- `file_url` (URLField, nullable) - Ссылка на файл
- `file_size` (PositiveIntegerField, nullable) - Размер файла (байт)
- `is_for_client` (BooleanField) - Для клиента
- `is_internal` (BooleanField) - Внутренний документ
- `created_at` (DateTimeField) - Дата загрузки
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `EquipmentDocument.equipment` → Equipment (FK)

---

### 13. equipment_line
**Таблица:** equipment_line  
**Модель:** EquipmentLine

**Поля:**
- `equipment_line_id` (PK, AutoField) - ID линии оборудования
- `equipment_line_name` (CharField, 255) - Название линии оборудования
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `EquipmentLine.equipment` → Equipment (ManyToMany через EquipmentLineItem)
- `EquipmentList.equipment_line_id` → EquipmentLine (FK)

---

### 14. equipment_line_item
**Таблица:** equipment_line_item  
**Модель:** EquipmentLineItem

**Поля:**
- `equipment_line_id` (FK) - Линия оборудования
- `equipment_id` (FK) - Оборудование
- `quantity` (PositiveIntegerField) - Количество
- `order` (PositiveIntegerField) - Порядок
- `created_at` (DateTimeField) - Дата создания

**Связи:**
- `EquipmentLineItem.equipment_line` → EquipmentLine (FK)
- `EquipmentLineItem.equipment` → Equipment (FK)

**Ограничения:**
- unique_together: [equipment_line, equipment]

---

### 15. additional_prices
**Таблица:** additional_prices  
**Модель:** AdditionalPrices

**Поля:**
- `price_id` (PK, AutoField) - ID расхода
- `price_parameter_name` (CharField, 255) - Название параметра расхода
- `expense_type` (CharField, 20) - Тип: packaging, labor, depreciation, service, warehouse, other
- `value_type` (CharField, 20) - Тип значения: percentage, fixed, coefficient
- `price_parameter_value` (DecimalField, 15, 2) - Значение расхода
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `EquipmentList.additional_price_id` → AdditionalPrices (FK)

---

### 16. equipment_list
**Таблица:** equipment_list  
**Модель:** EquipmentList

**Поля:**
- `list_id` (PK, AutoField) - ID записи списка
- `proposal_id` (FK, nullable) - Коммерческое предложение
- `equipment_line_id` (FK, nullable) - Линия оборудования (взаимоисключающее с equipment_id)
- `equipment_line_quantity` (PositiveIntegerField, nullable) - Количество линий
- `equipment_id` (FK, nullable) - Единица оборудования (взаимоисключающее с equipment_line_id)
- `equipment_quantity` (PositiveIntegerField, nullable) - Количество единиц
- `tax_percentage` (DecimalField, 5, 2) - Процент налога
- `tax_price` (DecimalField, 15, 2) - Сумма налога
- `delivery_percentage` (DecimalField, 5, 2) - Процент доставки
- `delivery_price` (DecimalField, 15, 2) - Стоимость доставки
- `additional_price_id` (FK, nullable) - Дополнительный расход
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Связи:**
- `EquipmentList.proposal_id` → CommercialProposal (FK)
- `EquipmentList.equipment_line_id` → EquipmentLine (FK)
- `EquipmentList.equipment_id` → Equipment (FK)
- `EquipmentList.additional_price_id` → AdditionalPrices (FK)

**Ограничения:**
- Должна быть выбрана либо equipment_line_id, либо equipment_id (не оба одновременно)

---

### 17. exchange_rate
**Таблица:** exchange_rate  
**Модель:** ExchangeRate

**Поля:**
- `rate_id` (PK, AutoField) - ID курса
- `currency_code` (CharField, 10) - Валюта: USD, EUR, RUB, CNY, KZT
- `rate_value` (DecimalField, 15, 6) - Курс валюты
- `base_currency` (CharField, 10) - Базовая валюта
- `rate_date` (DateField) - Дата курса
- `source` (CharField, 20) - Источник: api_cbr, api_nb_rk, api_other, manual
- `is_active` (BooleanField) - Активен
- `is_manual_override` (BooleanField) - Ручная корректировка
- `created_at` (DateTimeField) - Дата создания
- `updated_at` (DateTimeField) - Дата обновления

**Ограничения:**
- unique_together: [currency_code, rate_date, base_currency]

---

### 18. payment_log
**Таблица:** payment_log  
**Модель:** PaymentLog

**Поля:**
- `payment_id` (PK, AutoField) - ID платежа
- `payment_name` (CharField, 255) - Название платежа
- `payment_value` (DecimalField, 15, 2) - Сумма платежа
- `payment_date` (DateField) - Дата платежа
- `created_at` (DateTimeField) - Дата создания записи
- `updated_at` (DateTimeField) - Дата обновления записи

**Связи:**
- `CommercialProposal.payment_logs` → PaymentLog (ManyToMany)

---

### 19. commercial_proposal
**Таблица:** commercial_proposal  
**Модель:** CommercialProposal

**Поля:**
- `proposal_id` (PK, AutoField) - ID коммерческого предложения
- `proposal_name` (CharField, 255) - Название КП
- `outcoming_number` (CharField, 100, unique) - Номер КП
- `client_id` (FK) - Клиент
- `user_id` (FK, nullable) - Создал КП
- `currency_ticket` (CharField, 10) - Валюта
- `exchange_rate` (DecimalField, 15, 6) - Курс валюты
- `exchange_rate_date` (DateField, nullable) - Дата курса валюты
- `total_price` (DecimalField, 15, 2) - Итоговая цена
- `cost_price` (DecimalField, 15, 2, nullable) - Себестоимость
- `margin_percentage` (DecimalField, 5, 2, nullable) - Процент маржи
- `proposal_date` (DateField) - Дата КП
- `valid_until` (DateField, nullable) - Срок действия КП
- `delivery_time` (CharField, 255, nullable) - Время доставки
- `warranty` (CharField, 100, nullable) - Гарантия
- `proposal_status` (CharField, 20) - Статус: draft, sent, accepted, rejected, negotiating, completed
- `proposal_version` (PositiveIntegerField) - Версия КП
- `parent_proposal_id` (FK, nullable) - Родительское КП (self-reference)
- `comments` (TextField, nullable) - Комментарии
- `bitrix_lead_link` (URLField, nullable) - Ссылка на Битрикс
- `created_at` (DateTimeField) - Дата создания записи
- `updated_at` (DateTimeField) - Дата обновления записи

**Связи:**
- `CommercialProposal.client_id` → Client (FK)
- `CommercialProposal.user_id` → User (FK)
- `CommercialProposal.parent_proposal` → CommercialProposal (FK, self-reference)
- `CommercialProposal.payment_logs` → PaymentLog (ManyToMany)
- `EquipmentList.proposal_id` → CommercialProposal (FK)

---

## Сводная таблица связей

| Таблица | Связь | Связанная таблица | Тип связи |
|---------|-------|-------------------|-----------|
| users | user_id | commercial_proposal.user_id | FK |
| clients | client_id | commercial_proposal.client_id | FK |
| category | category_id | equipment.category_id | FK |
| category | parent_category_id | category.category_id | FK (self) |
| manufacturer | manufacturer_id | equipment.manufacturer_id | FK |
| equipment_types | type_id | equipment.equipment_type_id | FK |
| equipment_details | detail_id | equipment.detail_id | FK |
| equipment_specification | spec_id | equipment.spec_id | FK |
| equipment_tech_proccess | tech_id | equipment.equipment_tech_process_id | FK |
| equipment | equipment_id | purchase_price.equipment_id | FK |
| equipment | equipment_id | logistics.equipment_id | FK |
| equipment | equipment_id | equipment_document.equipment_id | FK |
| equipment | equipment_id | equipment_line_item.equipment_id | FK |
| equipment | equipment_id | equipment_list.equipment_id | FK |
| equipment_line | equipment_line_id | equipment_list.equipment_line_id | FK |
| equipment_line_item | equipment_line_id | equipment_line.equipment_line_id | FK |
| equipment_line_item | equipment_id | equipment.equipment_id | FK |
| equipment_line | equipment_line_id | equipment (через equipment_line_item) | M2M |
| additional_prices | price_id | equipment_list.additional_price_id | FK |
| equipment_list | proposal_id | commercial_proposal.proposal_id | FK |
| commercial_proposal | proposal_id | equipment_list.proposal_id | FK |
| commercial_proposal | parent_proposal_id | commercial_proposal.proposal_id | FK (self) |
| commercial_proposal | payment_logs | payment_log.payment_id | M2M |

