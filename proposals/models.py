import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


def equipment_photo_upload_to(instance, filename):
    """Store equipment photos as photos/<uuid>.jpg for predictable paths and no collisions."""
    ext = 'jpg'
    return f"photos/{uuid.uuid4().hex}.{ext}"


class UserManager(BaseUserManager):
    """Custom user manager for User model."""
    
    def create_user(self, user_login, user_email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not user_login:
            raise ValueError('The user_login must be set')
        if not user_email:
            raise ValueError('The user_email must be set')
        
        user_email = self.normalize_email(user_email)
        user = self.model(user_login=user_login, user_email=user_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, user_login, user_email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_role', 'Администратор')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(user_login, user_email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    User model based on AbstractBaseUser and PermissionsMixin.
    
    This model extends Django's AbstractBaseUser to provide password handling
    and PermissionsMixin to provide permission and group functionality.
    """
    user_id = models.AutoField(primary_key=True, verbose_name='ID пользователя')
    user_name = models.CharField(max_length=255, verbose_name='Имя пользователя')
    user_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Телефон')
    user_email = models.EmailField(unique=True, verbose_name='Email')
    user_login = models.CharField(max_length=150, unique=True, verbose_name='Логин')
    user_role = models.CharField(max_length=50, verbose_name='Роль', 
                                 choices=[
                                     ('Администратор', 'Администратор'),
                                     ('Менеджер', 'Менеджер'),
                                     ('Просмотр', 'Просмотр'),
                                 ])
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')
    is_superuser = models.BooleanField(default=False, verbose_name='Суперпользователь')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Дата регистрации')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'user_login'
    REQUIRED_FIELDS = ['user_email', 'user_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.user_name} ({self.user_login})"


class Client(models.Model):
    """Client model for storing client information."""
    client_id = models.AutoField(primary_key=True, verbose_name='ID клиента')
    client_name = models.CharField(max_length=255, verbose_name='Имя клиента')
    client_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Телефон клиента')
    client_email = models.EmailField(null=True, blank=True, verbose_name='Email клиента')
    client_company_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Название компании')
    client_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='Тип клиента')
    client_bin_iin = models.CharField(max_length=20, null=True, blank=True, verbose_name='БИН/ИИН')
    client_address = models.TextField(null=True, blank=True, verbose_name='Адрес клиента')
    client_bik = models.TextField(null=True, blank=True, verbose_name='БИК')
    client_iik = models.TextField(null=True, blank=True, verbose_name='ИИК')
    client_bankname = models.CharField(max_length=255, null=True, blank=True, verbose_name='Название банка')
    bitrix_id = models.IntegerField(null=True, blank=True, unique=True, verbose_name='ID компании в Bitrix24')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'clients'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
    
    def __str__(self):
        return self.client_name or f"Client {self.client_id}"


class Category(models.Model):
    """Category model with self-referential parent category."""
    category_id = models.AutoField(primary_key=True, verbose_name='ID категории')
    category_name = models.CharField(max_length=255, unique=True, verbose_name='Название категории')
    category_description = models.TextField(null=True, blank=True, verbose_name='Описание категории')
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        db_column='parent_category_id',
        verbose_name='Родительская категория'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.category_name


class Manufacturer(models.Model):
    """Manufacturer model for storing manufacturer information."""
    manufacturer_id = models.AutoField(primary_key=True, verbose_name='ID производителя')
    manufacturer_name = models.CharField(max_length=255, unique=True, verbose_name='Название производителя')
    manufacturer_country = models.CharField(max_length=100, null=True, blank=True, verbose_name='Страна производителя')
    manufacturer_website = models.URLField(null=True, blank=True, verbose_name='Сайт производителя')
    manufacturer_description = models.TextField(null=True, blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'manufacturer'
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'
    
    def __str__(self):
        return self.manufacturer_name


class EquipmentTypes(models.Model):
    """EquipmentTypes model for storing equipment type information."""
    type_id = models.AutoField(primary_key=True, verbose_name='ID типа')
    type_name = models.CharField(max_length=255, unique=True, verbose_name='Название типа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment_types'
        verbose_name = 'Тип оборудования'
        verbose_name_plural = 'Типы оборудования'
    
    def __str__(self):
        return self.type_name


class EquipmentDetails(models.Model):
    """EquipmentDetails model for storing equipment detail parameters."""
    detail_id = models.AutoField(primary_key=True, verbose_name='ID детали')
    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='details',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    detail_parameter_name = models.CharField(max_length=255, verbose_name='Название параметра')
    detail_parameter_value = models.TextField(null=True, blank=True, verbose_name='Значение параметра')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment_details'
        verbose_name = 'Деталь оборудования'
        verbose_name_plural = 'Детали оборудования'
    
    def __str__(self):
        return f"{self.detail_parameter_name}: {self.detail_parameter_value or 'N/A'}"


class EquipmentSpecification(models.Model):
    """EquipmentSpecification model for storing equipment specification parameters."""
    spec_id = models.AutoField(primary_key=True, verbose_name='ID спецификации')
    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='specifications',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    spec_parameter_name = models.CharField(max_length=255, verbose_name='Название параметра')
    spec_parameter_value = models.TextField(null=True, blank=True, verbose_name='Значение параметра')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment_specification'
        verbose_name = 'Спецификация оборудования'
        verbose_name_plural = 'Спецификации оборудования'
    
    def __str__(self):
        return f"{self.spec_parameter_name}: {self.spec_parameter_value or 'N/A'}"


class EquipmentTechProcess(models.Model):
    """EquipmentTechProcess model for storing equipment technical process information."""
    tech_id = models.AutoField(primary_key=True, verbose_name='ID процесса')
    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tech_processes',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    tech_name = models.CharField(max_length=255, verbose_name='Название процесса')
    tech_value = models.CharField(max_length=255, null=True, blank=True, verbose_name='Значение')
    tech_desc = models.TextField(null=True, blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment_tech_proccess'
        verbose_name = 'Технологический процесс оборудования'
        verbose_name_plural = 'Технологические процессы оборудования'
    
    def __str__(self):
        return self.tech_name or f"Tech Process {self.tech_id}"


class Equipment(models.Model):
    """Equipment model - main equipment catalog model with multiple relationships."""
    equipment_id = models.AutoField(primary_key=True, verbose_name='ID оборудования')
    equipment_name = models.CharField(max_length=255, verbose_name='Название оборудования')
    equipment_articule = models.CharField(max_length=100, null=True, blank=True, verbose_name='Артикул')
    equipment_uom = models.CharField(max_length=50, null=True, blank=True, verbose_name='Единица измерения')
    equipment_short_description = models.TextField(null=True, blank=True, verbose_name='Краткое описание')
    equipment_warranty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Гарантия')
    is_published = models.BooleanField(default=False, verbose_name='Опубликовано на сайте')
    
    # Many-to-Many relationships
    categories = models.ManyToManyField(
        Category,
        related_name='equipment',
        blank=True,
        verbose_name='Категории'
    )
    manufacturers = models.ManyToManyField(
        Manufacturer,
        related_name='equipment',
        blank=True,
        verbose_name='Производители'
    )
    equipment_types = models.ManyToManyField(
        EquipmentTypes,
        related_name='equipment',
        blank=True,
        verbose_name='Типы оборудования'
    )
    
    # Additional fields
    equipment_imagelinks = models.JSONField(default=list, blank=True, verbose_name='Ссылки на изображения')
    equipment_videolinks = models.TextField(null=True, blank=True, verbose_name='Ссылки на видео')
    equipment_manufacture_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Цена производства'
    )
    sale_price_kzt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Цена продажи (KZT)'
    )
    equipment_madein_country = models.CharField(max_length=100, null=True, blank=True, verbose_name='Страна производства')
    equipment_price_currency_type = models.CharField(max_length=10, null=True, blank=True, verbose_name='Тип валюты')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment'
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'
    
    def __str__(self):
        return self.equipment_name or f"Equipment {self.equipment_id}"


class EquipmentPhoto(models.Model):
    """Locally stored photo for equipment (downloaded from cloud links and optimized)."""
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='photos',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    image = models.ImageField(
        upload_to=equipment_photo_upload_to,
        verbose_name='Фото',
        max_length=255
    )
    name = models.CharField(max_length=255, blank=True, verbose_name='Подпись')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        db_table = 'equipment_photo'
        verbose_name = 'Фото оборудования'
        verbose_name_plural = 'Фото оборудования'
        ordering = ['sort_order', 'pk']

    def __str__(self):
        return f"Photo {self.pk} for {self.equipment_id}"


class PurchasePrice(models.Model):
    """PurchasePrice model for storing equipment purchase prices from different sources."""
    price_id = models.AutoField(primary_key=True, verbose_name='ID цены')
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='purchase_prices',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    source_type = models.CharField(
        max_length=20,
        verbose_name='Источник',
        choices=[
            ('russia', 'Russia'),
            ('china', 'China'),
            ('own_production', 'Own Production'),
            ('other', 'Other'),
        ]
    )
    price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Цена закупки')
    currency = models.CharField(max_length=10, verbose_name='Валюта')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    notes = models.TextField(null=True, blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'purchase_price'
        verbose_name = 'Цена закупки'
        verbose_name_plural = 'Цены закупки'
    
    def __str__(self):
        return f"{self.equipment.equipment_name} - {self.price} {self.currency} ({self.source_type})"


class Logistics(models.Model):
    """Logistics model for storing equipment logistics and delivery information."""
    logistics_id = models.AutoField(primary_key=True, verbose_name='ID логистики')
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='logistics',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    route_type = models.CharField(
        max_length=20,
        verbose_name='Маршрут',
        choices=[
            ('china_kz', 'China to KZ'),
            ('russia_kz', 'Russia to KZ'),
            ('kz_warehouse', 'KZ Warehouse'),
            ('other', 'Other'),
        ]
    )
    cost = models.DecimalField(max_digits=25, decimal_places=2, verbose_name='Стоимость доставки')
    currency = models.CharField(max_length=10, verbose_name='Валюта')
    estimated_days = models.PositiveIntegerField(null=True, blank=True, verbose_name='Срок доставки (дней)')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    notes = models.TextField(null=True, blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'logistics'
        verbose_name = 'Логистика'
        verbose_name_plural = 'Логистика'
    
    def __str__(self):
        return f"{self.equipment.equipment_name} - {self.route_type} ({self.cost} {self.currency})"


class EquipmentDocument(models.Model):
    """EquipmentDocument model for storing equipment-related documents."""
    document_id = models.AutoField(primary_key=True, verbose_name='ID документа')
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='documents',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    document_type = models.CharField(
        max_length=20,
        verbose_name='Тип документа',
        choices=[
            ('passport', 'Passport'),
            ('certificate', 'Certificate'),
            ('declaration', 'Declaration'),
            ('estimate', 'Estimate'),
            ('manual', 'Manual'),
            ('other', 'Other'),
        ]
    )
    document_name = models.CharField(max_length=255, verbose_name='Название документа')
    file = models.FileField(upload_to='equipment_documents/', null=True, blank=True, verbose_name='Файл')
    file_url = models.URLField(null=True, blank=True, verbose_name='Ссылка на файл')
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='Размер файла (байт)')
    is_for_client = models.BooleanField(default=False, verbose_name='Для клиента')
    is_internal = models.BooleanField(default=False, verbose_name='Внутренний документ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment_document'
        verbose_name = 'Документ оборудования'
        verbose_name_plural = 'Документы оборудования'
    
    def __str__(self):
        return f"{self.document_name} ({self.document_type})"


class EquipmentLine(models.Model):
    """EquipmentLine model for grouping equipment into lines."""
    equipment_line_id = models.AutoField(primary_key=True, verbose_name='ID линии оборудования')
    equipment_line_name = models.CharField(max_length=255, verbose_name='Название линии оборудования')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    # Many-to-Many relationship with Equipment through EquipmentLineItem
    equipment = models.ManyToManyField(
        Equipment,
        through='EquipmentLineItem',
        related_name='equipment_lines',
        verbose_name='Оборудование'
    )
    
    class Meta:
        db_table = 'equipment_line'
        verbose_name = 'Линия оборудования'
        verbose_name_plural = 'Линии оборудования'
    
    def __str__(self):
        return self.equipment_line_name


class EquipmentLineItem(models.Model):
    """EquipmentLineItem model - intermediate model for EquipmentLine and Equipment ManyToMany relationship."""
    equipment_line = models.ForeignKey(
        EquipmentLine,
        on_delete=models.CASCADE,
        related_name='line_items',
        db_column='equipment_line_id',
        verbose_name='Линия оборудования'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='line_items',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    order = models.PositiveIntegerField(verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'equipment_line_item'
        verbose_name = 'Элемент линии оборудования'
        verbose_name_plural = 'Элементы линии оборудования'
        unique_together = [['equipment_line', 'equipment']]
        ordering = ['order']
    
    def __str__(self):
        return f"{self.equipment_line.equipment_line_name} - {self.equipment.equipment_name} (x{self.quantity})"


class AdditionalPrices(models.Model):
    """AdditionalPrices model for storing additional expense parameters."""
    price_id = models.AutoField(primary_key=True, verbose_name='ID расхода')
    price_parameter_name = models.CharField(max_length=255, verbose_name='Название параметра расхода')
    expense_type = models.CharField(
        max_length=20,
        verbose_name='Тип расхода',
        choices=[
            ('packaging', 'Packaging'),
            ('labor', 'Labor'),
            ('depreciation', 'Depreciation'),
            ('service', 'Service'),
            ('warehouse', 'Warehouse'),
            ('other', 'Other'),
        ]
    )
    value_type = models.CharField(
        max_length=20,
        verbose_name='Тип значения',
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed'),
            ('coefficient', 'Coefficient'),
        ]
    )
    price_parameter_value = models.DecimalField(max_digits=25, decimal_places=2, verbose_name='Значение расхода')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'additional_prices'
        verbose_name = 'Дополнительный расход'
        verbose_name_plural = 'Дополнительные расходы'
    
    def __str__(self):
        return f"{self.price_parameter_name} ({self.expense_type}) - {self.price_parameter_value}"


class EquipmentList(models.Model):
    """EquipmentList model for storing equipment items in commercial proposals."""
    list_id = models.AutoField(primary_key=True, verbose_name='ID записи списка')
    
    # ForeignKey to CommercialProposal
    proposal = models.ForeignKey(
        'CommercialProposal',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='equipment_lists',
        db_column='proposal_id',
        verbose_name='Коммерческое предложение'
    )
    
    # Many-to-Many relationships through intermediate models
    equipment_lines = models.ManyToManyField(
        EquipmentLine,
        through='EquipmentListLineItem',
        related_name='equipment_lists',
        blank=True,
        verbose_name='Линии оборудования'
    )
    equipment_items = models.ManyToManyField(
        Equipment,
        through='EquipmentListItem',
        related_name='equipment_lists',
        blank=True,
        verbose_name='Единицы оборудования'
    )
    
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=0, verbose_name='Процент налога')
    tax_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0, verbose_name='Сумма налога')
    delivery_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=0, verbose_name='Процент доставки')
    delivery_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0, verbose_name='Стоимость доставки')
    
    # Many-to-Many для поддержки нескольких дополнительных расходов
    additional_prices = models.ManyToManyField(
        AdditionalPrices,
        related_name='equipment_lists',
        blank=True,
        verbose_name='Дополнительные расходы'
    )
    
    # Оставляем старое поле для обратной совместимости (deprecated)
    additional_price = models.ForeignKey(
        AdditionalPrices,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment_lists_old',
        db_column='additional_price_id',
        verbose_name='Дополнительный расход (устаревшее)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'equipment_list'
        verbose_name = 'Список оборудования'
        verbose_name_plural = 'Списки оборудования'
    
    def __str__(self):
        return f"EquipmentList {self.list_id}"


class EquipmentListLineItem(models.Model):
    """Intermediate model for EquipmentList and EquipmentLine ManyToMany relationship."""
    equipment_list = models.ForeignKey(
        EquipmentList,
        on_delete=models.CASCADE,
        related_name='line_items',
        db_column='list_id',
        verbose_name='Список оборудования'
    )
    equipment_line = models.ForeignKey(
        EquipmentLine,
        on_delete=models.CASCADE,
        related_name='list_items',
        db_column='equipment_line_id',
        verbose_name='Линия оборудования'
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество линий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'equipment_list_line_item'
        verbose_name = 'Элемент списка (линия)'
        verbose_name_plural = 'Элементы списка (линии)'
        unique_together = [['equipment_list', 'equipment_line']]
    
    def __str__(self):
        return f"{self.equipment_list.list_id} - {self.equipment_line.equipment_line_name} (x{self.quantity})"


class EquipmentListItem(models.Model):
    """Intermediate model for EquipmentList and Equipment ManyToMany relationship."""
    equipment_list = models.ForeignKey(
        EquipmentList,
        on_delete=models.CASCADE,
        related_name='equipment_items_relation',
        db_column='list_id',
        verbose_name='Список оборудования'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='list_items',
        db_column='equipment_id',
        verbose_name='Единица оборудования'
    )
    row_expenses = models.JSONField(default=list, blank=True, verbose_name='Расходы на строку')
    quantity = models.PositiveIntegerField(verbose_name='Количество единиц')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    # Итоговые цены после распределения общих расходов
    price_per_unit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='Цена за единицу (итоговая)'
    )
    total_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='Общая стоимость (итоговая)'
    )
    # Расчетные значения для отображения в форме редактирования
    calculated_data = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='Расчетные данные (маржа, расходы и т.д.)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'equipment_list_item'
        verbose_name = 'Элемент списка (оборудование)'
        verbose_name_plural = 'Элементы списка (оборудование)'
        unique_together = [['equipment_list', 'equipment']]
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.equipment_list.list_id} - {self.equipment.equipment_name} (x{self.quantity})"


class PaymentLog(models.Model):
    """PaymentLog model for storing payment records."""
    payment_id = models.AutoField(primary_key=True, verbose_name='ID платежа')
    payment_name = models.CharField(max_length=255, verbose_name='Название платежа')
    payment_value = models.DecimalField(max_digits=25, decimal_places=2, verbose_name='Сумма платежа')
    payment_date = models.DateField(verbose_name='Дата платежа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления записи')
    
    comments = models.TextField(null=True, blank=True, verbose_name='Комментарии')
    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_logs',
        db_column='user_id',
        verbose_name='Кто внес'
    )

    class Meta:
        db_table = 'payment_log'
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
    
    def __str__(self):
        return f"{self.payment_name} - {self.payment_value} ({self.payment_date})"


class CommercialProposal(models.Model):
    """CommercialProposal model for storing commercial proposals."""
    
    # Status choices
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('sent', 'Отправлено'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
        ('negotiating', 'В переговорах'),
        ('completed', 'Завершено'),
    ]
    
    proposal_id = models.AutoField(primary_key=True, verbose_name='ID коммерческого предложения')
    proposal_name = models.CharField(max_length=255, verbose_name='Название КП')
    outcoming_number = models.CharField(max_length=100, unique=True, verbose_name='Номер КП')
    
    # Foreign Keys
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='commercial_proposals',
        db_column='client_id',
        verbose_name='Клиент'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commercial_proposals',
        db_column='user_id',
        verbose_name='Создал КП'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_proposals',
        db_column='updated_by_id',
        verbose_name='Последний раз обновил'
    )
    
    # Currency and pricing fields
    currency_ticket = models.CharField(max_length=10, verbose_name='Валюта')
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, verbose_name='Курс валюты')
    exchange_rate_date = models.DateField(null=True, blank=True, verbose_name='Дата курса валюты')
    total_price = models.DecimalField(max_digits=25, decimal_places=2, verbose_name='Итоговая цена')
    cost_price = models.DecimalField(max_digits=25, decimal_places=2, null=True, blank=True, verbose_name='Себестоимость')
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Процент маржи')
    margin_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Сумма маржи')
    internal_exchange_rates = models.JSONField(default=list, blank=True, verbose_name='Внутренние курсы валют (snapshot)')
    additional_services = models.JSONField(default=list, blank=True, verbose_name='Дополнительные услуги')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    # Proposal details
    proposal_date = models.DateField(verbose_name='Дата КП')
    valid_until = models.DateField(null=True, blank=True, verbose_name='Срок действия КП')
    delivery_time = models.CharField(max_length=255, null=True, blank=True, verbose_name='Время доставки')
    warranty = models.CharField(max_length=100, null=True, blank=True, verbose_name='Гарантия')
    proposal_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус'
    )
    proposal_version = models.PositiveIntegerField(verbose_name='Версия КП')
    
    # Self-referential ForeignKey for parent proposal
    parent_proposal = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_proposals',
        db_column='parent_proposal_id',
        verbose_name='Родительское КП'
    )
    
    # Additional fields
    comments = models.TextField(null=True, blank=True, verbose_name='Комментарии')
    bitrix_lead_link = models.URLField(null=True, blank=True, verbose_name='Ссылка на Битрикс')
    data_package = models.JSONField(default=dict, blank=True, null=True, verbose_name='Пакет данных для конструктора')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления записи')
    
    # Many-to-Many relationship with PaymentLog
    payment_logs = models.ManyToManyField(
        PaymentLog,
        related_name='commercial_proposals',
        blank=True,
        verbose_name='Платежи'
    )
    
    class Meta:
        db_table = 'commercial_proposal'
        verbose_name = 'Коммерческое предложение'
        verbose_name_plural = 'Коммерческие предложения'
        ordering = ['-proposal_date', '-created_at']
    
    def __str__(self):
        return f"{self.outcoming_number} - {self.proposal_name}"


class ExchangeRate(models.Model):
    """ExchangeRate model for storing currency exchange rates with history."""
    
    # Currency choices
    CURRENCY_CHOICES = [
        ('RUB', 'Российский рубль (RUB)'),
        ('CNY', 'Китайский юань (CNY)'),
        ('USD', 'Доллар США (USD)'),
        ('KZT', 'Казахстанский тенге (KZT)'),
        ('EUR', 'Евро (EUR)'),
    ]
    
    # Source choices
    SOURCE_CHOICES = [
        ('api_cbr', 'API Центрального банка России'),
        ('api_nbrk', 'API Национального банка РК'),
        ('api_other', 'Другое API'),
        ('manual', 'Ручной ввод'),
        ('custom', 'Корректировка для КП'),
    ]
    
    rate_id = models.AutoField(primary_key=True, verbose_name='ID курса')
    currency_from = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        verbose_name='Валюта (из)'
    )
    currency_to = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='KZT',
        verbose_name='Валюта (в)'
    )
    rate_value = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        verbose_name='Значение курса'
    )
    rate_date = models.DateField(verbose_name='Дата курса')
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual',
        verbose_name='Источник'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_official = models.BooleanField(default=True, verbose_name='Официальный курс')
    
    # Связь с CommercialProposal для корректировки курса в конкретном КП
    # Если proposal не null, то это корректировка курса для конкретного КП
    proposal = models.ForeignKey(
        'CommercialProposal',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='exchange_rate_adjustments',
        db_column='proposal_id',
        verbose_name='КП (для корректировки)'
    )
    
    # Комментарий или примечание
    notes = models.TextField(null=True, blank=True, verbose_name='Примечания')
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_exchange_rates',
        db_column='created_by_user_id',
        verbose_name='Создал'
    )
    
    class Meta:
        db_table = 'exchange_rate'
        verbose_name = 'Курс валюты'
        verbose_name_plural = 'Курсы валют'
        ordering = ['-rate_date', '-created_at']
        # Индекс для быстрого поиска актуальных курсов
        indexes = [
            models.Index(fields=['currency_from', 'currency_to', 'rate_date', 'is_active']),
            models.Index(fields=['rate_date', 'is_active']),
        ]
        # Уникальность: один курс для валютной пары на дату (если не корректировка для КП)
        # Для корректировок КП может быть несколько курсов
        constraints = [
            models.UniqueConstraint(
                fields=['currency_from', 'currency_to', 'rate_date', 'proposal'],
                condition=models.Q(proposal__isnull=True),
                name='unique_official_rate_per_date'
            ),
        ]
    
    def __str__(self):
        proposal_info = f" (КП #{self.proposal.proposal_id})" if self.proposal else ""
        source_info = f" [{self.get_source_display()}]" if self.source != 'manual' else ""
        return f"{self.currency_from}/{self.currency_to}: {self.rate_value} на {self.rate_date}{proposal_info}{source_info}"
    
    @classmethod
    def get_latest_rate(cls, currency_from, currency_to='KZT', date=None, proposal=None):
        """
        Получить актуальный курс валюты на указанную дату.
        
        Args:
            currency_from: Валюта (из)
            currency_to: Валюта (в), по умолчанию KZT
            date: Дата курса (если None, используется сегодня)
            proposal: Если указан, ищется корректировка для этого КП
        
        Returns:
            ExchangeRate объект или None
        """
        from django.utils import timezone
        
        if date is None:
            date = timezone.now().date()
        
        # Сначала ищем корректировку для конкретного КП (если указан)
        if proposal:
            custom_rate = cls.objects.filter(
                currency_from=currency_from,
                currency_to=currency_to,
                rate_date__lte=date,
                proposal=proposal,
                is_active=True
            ).order_by('-rate_date', '-created_at').first()
            
            if custom_rate:
                return custom_rate
        
        # Ищем официальный курс
        official_rate = cls.objects.filter(
            currency_from=currency_from,
            currency_to=currency_to,
            rate_date__lte=date,
            proposal__isnull=True,
            is_active=True,
            is_official=True
        ).order_by('-rate_date', '-created_at').first()
        
        return official_rate


class CostCalculation(models.Model):
    """CostCalculation model for storing cost calculation versions and history."""
    
    calculation_id = models.AutoField(primary_key=True, verbose_name='ID расчёта')
    
    # Связь с оборудованием
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='cost_calculations',
        db_column='equipment_id',
        verbose_name='Оборудование'
    )
    
    # Связь с КП (опционально, если расчет для конкретного КП)
    proposal = models.ForeignKey(
        CommercialProposal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cost_calculations',
        db_column='proposal_id',
        verbose_name='Коммерческое предложение'
    )
    
    # Версия расчета
    calculation_version = models.PositiveIntegerField(default=1, verbose_name='Версия расчёта')
    
    # Исходные данные для расчета
    purchase_price_id = models.IntegerField(null=True, blank=True, verbose_name='ID цены закупки')
    purchase_price_value = models.DecimalField(max_digits=25, decimal_places=2, verbose_name='Цена закупки')
    purchase_price_currency = models.CharField(max_length=10, verbose_name='Валюта закупки')
    purchase_price_source = models.CharField(max_length=20, null=True, blank=True, verbose_name='Источник закупки')
    
    logistics_id = models.IntegerField(null=True, blank=True, verbose_name='ID логистики')
    logistics_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Стоимость логистики')
    logistics_currency = models.CharField(max_length=10, null=True, blank=True, verbose_name='Валюта логистики')
    logistics_route = models.CharField(max_length=20, null=True, blank=True, verbose_name='Маршрут логистики')
    
    warehouse_cost = models.DecimalField(max_digits=25, decimal_places=2, default=0, verbose_name='Стоимость склада')
    warehouse_currency = models.CharField(max_length=10, null=True, blank=True, verbose_name='Валюта склада')
    
    production_cost = models.DecimalField(max_digits=25, decimal_places=2, default=0, verbose_name='Производственные расходы')
    production_currency = models.CharField(max_length=10, null=True, blank=True, verbose_name='Валюта производства')
    
    additional_costs = models.DecimalField(max_digits=25, decimal_places=2, default=0, verbose_name='Дополнительные расходы')
    additional_costs_currency = models.CharField(max_length=10, null=True, blank=True, verbose_name='Валюта доп. расходов')
    
    # Курс валюты для конвертации
    exchange_rate_id = models.IntegerField(null=True, blank=True, verbose_name='ID курса валюты')
    exchange_rate_value = models.DecimalField(max_digits=15, decimal_places=6, verbose_name='Курс валюты')
    exchange_rate_from = models.CharField(max_length=10, verbose_name='Валюта (из)')
    exchange_rate_to = models.CharField(max_length=10, default='KZT', verbose_name='Валюта (в)')
    exchange_rate_date = models.DateField(null=True, blank=True, verbose_name='Дата курса')
    
    # Результаты расчета
    total_cost_base_currency = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name='Итоговая себестоимость (базовая валюта)'
    )
    total_cost_kzt = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name='Итоговая себестоимость (KZT)'
    )
    
    # Детализация расчета (JSON для хранения подробностей)
    calculation_details = models.JSONField(null=True, blank=True, verbose_name='Детали расчёта')
    
    # Метаданные
    is_manual_adjustment = models.BooleanField(default=False, verbose_name='Ручная корректировка')
    notes = models.TextField(null=True, blank=True, verbose_name='Примечания')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cost_calculations',
        db_column='created_by_user_id',
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'cost_calculation'
        verbose_name = 'Расчёт себестоимости'
        verbose_name_plural = 'Расчёты себестоимости'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['equipment', 'proposal', 'calculation_version']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        proposal_info = f" (КП #{self.proposal.proposal_id})" if self.proposal else ""
        return f"Расчёт #{self.calculation_id} для {self.equipment.equipment_name} v{self.calculation_version}{proposal_info}"

class ProposalTemplate(models.Model):
    """
    Model for storing custom layout/structure of a Commercial Proposal.
    """
    template_id = models.AutoField(primary_key=True, verbose_name='ID шаблона')
    proposal = models.OneToOneField(
        CommercialProposal, 
        on_delete=models.CASCADE, 
        related_name='template',
        verbose_name='КП'
    )
    layout_data = models.JSONField(default=list, verbose_name='Структура контента')
    header_data = models.JSONField(default=dict, blank=True, null=True, verbose_name='Данные заголовка')
    is_final = models.BooleanField(default=False, verbose_name='Зафиксировано')
    last_edited_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='edited_templates',
        verbose_name='Последний редактор'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        db_table = 'proposal_template'
        verbose_name = 'Шаблон КП'
        verbose_name_plural = 'Шаблоны КП'

    def __str__(self):
        return f"Template for {self.proposal.outcoming_number}"
class SectionTemplate(models.Model):
    """
    Model for storing reusable text sections for commercial proposals.
    Used in the proposal constructor.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name='Техническое название')
    title = models.CharField(max_length=255, verbose_name='Заголовок раздела')
    text = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        db_table = 'section_templates'
        verbose_name = 'Шаблон раздела'
        verbose_name_plural = 'Шаблоны разделов'

    def __str__(self):
        return f"{self.title} ({self.name})"

class SystemSettings(models.Model):
    """
    Singleton model for system-wide settings (branding, logo, etc.)
    """
    company_logo = models.ImageField(upload_to='company/', null=True, blank=True, verbose_name='Логотип компании')
    bitrix_webhook_url = models.URLField(max_length=512, null=True, blank=True, verbose_name='URL вебхука Bitrix24')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'Системные настройки'
        verbose_name_plural = 'Системные настройки'

    def save(self, *args, **kwargs):
        if not self.pk and SystemSettings.objects.exists():
            # In case of multiple instance creation attempts, just return the existing one
            return
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
