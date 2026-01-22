from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Client, Category, Manufacturer, EquipmentTypes, EquipmentDetails,
    EquipmentSpecification, EquipmentTechProcess, Equipment, PurchasePrice,
    Logistics, EquipmentDocument, EquipmentLine, EquipmentLineItem, AdditionalPrices,
    EquipmentList, EquipmentListLineItem, EquipmentListItem, PaymentLog, CommercialProposal,
    ExchangeRate, CostCalculation, ProposalTemplate, SectionTemplate
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'user_name', 'user_phone', 'user_email', 
            'user_login', 'user_role', 'password', 'password_confirm',
            'date_joined', 'created_at'
        ]
        read_only_fields = ['user_id', 'date_joined', 'created_at']
        extra_kwargs = {
            'user_name': {'required': True},
            'user_email': {'required': True},
            'user_login': {'required': True},
            'user_role': {'required': False, 'allow_null': True},
        }
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.',
                'password_confirm': 'Passwords do not match.'
            })
        # Ensure default role if not provided
        if not attrs.get('user_role'):
            attrs['user_role'] = 'Просмотр'
        return attrs
    
    def validate_user_email(self, value):
        """Validate that email is unique."""
        if User.objects.filter(user_email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value
    
    def validate_user_login(self, value):
        """Validate that login is unique."""
        if User.objects.filter(user_login=value).exists():
            raise serializers.ValidationError('A user with this login already exists.')
        return value
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Set default role if not provided
        if 'user_role' not in validated_data:
            validated_data['user_role'] = 'Просмотр'

        # New users must be inactive until approved by an admin
        validated_data['is_active'] = False
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to update user's role and activation status.
    """
    class Meta:
        model = User
        fields = [
            'user_id', 'user_name', 'user_phone', 'user_email', 'user_login',
            'user_role', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user_id', 'user_email', 'user_login', 'created_at', 'updated_at'
        ]


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    user_login = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Validate user credentials."""
        user_login = attrs.get('user_login')
        password = attrs.get('password')
        
        if user_login and password:
            user = authenticate(request=self.context.get('request'), 
                              username=user_login, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid login credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include "user_login" and "password".')
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details (read-only for authenticated users)."""
    
    class Meta:
        model = User
        fields = [
            'user_id', 'user_name', 'user_phone', 'user_email',
            'user_login', 'user_role', 'is_active', 'is_staff',
            'is_superuser', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user_id', 'user_email', 'user_login', 'is_staff',
            'is_superuser', 'date_joined', 'created_at', 'updated_at'
        ]


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model."""
    
    class Meta:
        model = Client
        fields = [
            'client_id', 'client_name', 'client_phone', 'client_email',
            'client_company_name', 'client_type', 'client_bin_iin',
            'client_address', 'client_bik', 'client_iik', 'client_bankname',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['client_id', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = [
            'category_id', 'category_name', 'category_description',
            'parent_category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['category_id', 'created_at', 'updated_at']


class ManufacturerSerializer(serializers.ModelSerializer):
    """Serializer for Manufacturer model."""
    
    class Meta:
        model = Manufacturer
        fields = [
            'manufacturer_id', 'manufacturer_name', 'manufacturer_country',
            'manufacturer_website', 'manufacturer_description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['manufacturer_id', 'created_at', 'updated_at']


class EquipmentTypesSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentTypes model."""
    
    class Meta:
        model = EquipmentTypes
        fields = [
            'type_id', 'type_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['type_id', 'created_at', 'updated_at']


class EquipmentDetailsSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentDetails model."""
    
    class Meta:
        model = EquipmentDetails
        fields = [
            'detail_id', 'equipment', 'detail_parameter_name', 'detail_parameter_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['detail_id', 'created_at', 'updated_at']


class EquipmentSpecificationSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentSpecification model."""
    
    class Meta:
        model = EquipmentSpecification
        fields = [
            'spec_id', 'equipment', 'spec_parameter_name', 'spec_parameter_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['spec_id', 'created_at', 'updated_at']


class EquipmentTechProcessSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentTechProcess model."""
    
    class Meta:
        model = EquipmentTechProcess
        fields = [
            'tech_id', 'equipment', 'tech_name', 'tech_value', 'tech_desc',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tech_id', 'created_at', 'updated_at']


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer for Equipment model with all relationships."""
    # Many-to-many relationships
    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=Category.objects.all(), required=False)
    manufacturers = serializers.PrimaryKeyRelatedField(many=True, queryset=Manufacturer.objects.all(), required=False)
    equipment_types = serializers.PrimaryKeyRelatedField(many=True, queryset=EquipmentTypes.objects.all(), required=False)
    
    # One-to-many relationships (nested serializers for details)
    details = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    tech_processes = serializers.SerializerMethodField()
    
    # Актуальная цена из последнего сохраненного EquipmentListItem
    actual_price = serializers.SerializerMethodField()
    
    # Explicitly define JSON field to avoid auto-mapping issues
    equipment_imagelinks = serializers.JSONField(required=False)
    
    class Meta:
        model = Equipment
        fields = [
            'equipment_id', 'equipment_name', 'equipment_articule', 'equipment_uom',
            'equipment_short_description', 'equipment_warranty', 'is_published',
            'categories', 'manufacturers', 'equipment_types',
            'details', 'specifications', 'tech_processes',
            'equipment_imagelinks', 'equipment_videolinks',
            'equipment_manufacture_price', 'sale_price_kzt', 'equipment_madein_country',
            'equipment_price_currency_type', 'actual_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['equipment_id', 'created_at', 'updated_at', 'actual_price']
    
    def get_details(self, obj):
        """Get all details for this equipment."""
        details = obj.details.all()
        return [
            {
                'detail_id': detail.detail_id,
                'detail_parameter_name': detail.detail_parameter_name,
                'detail_parameter_value': detail.detail_parameter_value
            }
            for detail in details
        ]
    
    def get_specifications(self, obj):
        """Get all specifications for this equipment."""
        specs = obj.specifications.all()
        return [
            {
                'spec_id': spec.spec_id,
                'spec_parameter_name': spec.spec_parameter_name,
                'spec_parameter_value': spec.spec_parameter_value
            }
            for spec in specs
        ]
    
    def get_tech_processes(self, obj):
        """Get all tech processes for this equipment."""
        tech_processes = obj.tech_processes.all()
        return [
            {
                'tech_id': tp.tech_id,
                'tech_name': tp.tech_name,
                'tech_value': tp.tech_value,
                'tech_desc': tp.tech_desc
            }
            for tp in tech_processes
        ]
    
    def get_actual_price(self, obj):
        """
        Get the actual price: sale_price_kzt if set, otherwise latest price from EquipmentListItem.
        """
        # Priority 1: Use sale_price_kzt if available
        if obj.sale_price_kzt is not None:
            return float(obj.sale_price_kzt)
        
        # Priority 2: Fallback to latest EquipmentListItem price
        from .models import EquipmentListItem
        from decimal import Decimal
        
        # Get the latest EquipmentListItem with saved price for this equipment
        latest_item = EquipmentListItem.objects.filter(
            equipment=obj,
            price_per_unit__isnull=False
        ).order_by('-created_at').first()
        
        if latest_item and latest_item.price_per_unit is not None:
            # Return price in KZT (assuming prices are saved in proposal currency, which is usually KZT)
            return float(latest_item.price_per_unit)
        
        return None
    
    def create(self, validated_data):
        """Create equipment with Many-to-Many relationships."""
        from django.db import transaction
        import logging
        logger = logging.getLogger(__name__)
        
        # Извлекаем Many-to-Many данные
        categories = validated_data.pop('categories', [])
        manufacturers = validated_data.pop('manufacturers', [])
        equipment_types = validated_data.pop('equipment_types', [])
        
        logger.info(f"Creating equipment with data: {validated_data}")
        logger.info(f"Categories: {categories}, Manufacturers: {manufacturers}, Types: {equipment_types}")
        
        # Создаем оборудование в транзакции
        try:
            with transaction.atomic():
                equipment = Equipment.objects.create(**validated_data)
                logger.info(f"Equipment created with ID: {equipment.equipment_id}")
                
                # Устанавливаем Many-to-Many связи
                if categories:
                    equipment.categories.set(categories)
                    logger.info(f"Categories set: {equipment.categories.all()}")
                if manufacturers:
                    equipment.manufacturers.set(manufacturers)
                    logger.info(f"Manufacturers set: {equipment.manufacturers.all()}")
                if equipment_types:
                    equipment.equipment_types.set(equipment_types)
                    logger.info(f"Equipment types set: {equipment.equipment_types.all()}")
                
                # Принудительно обновляем из БД, чтобы получить актуальный ID
                equipment.refresh_from_db()
                
                # Проверяем, что оборудование действительно в БД
                equipment_check = Equipment.objects.filter(equipment_id=equipment.equipment_id).first()
                if not equipment_check:
                    logger.error(f"Equipment {equipment.equipment_id} was created but not found in DB!")
                    raise Exception(f"Equipment {equipment.equipment_id} was created but not found in DB!")
                
                logger.info(f"Equipment {equipment.equipment_id} successfully created and verified in DB")
                return equipment
        except Exception as e:
            # Логируем ошибку для отладки
            logger.error(f"Error creating equipment: {e}", exc_info=True)
            logger.error(f"Validated data: {validated_data}")
            raise
    
    def update(self, instance, validated_data):
        """Update equipment with Many-to-Many relationships."""
        # Извлекаем Many-to-Many данные
        categories = validated_data.pop('categories', None)
        manufacturers = validated_data.pop('manufacturers', None)
        equipment_types = validated_data.pop('equipment_types', None)
        
        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем Many-to-Many связи, если они переданы
        if categories is not None:
            instance.categories.set(categories)
        if manufacturers is not None:
            instance.manufacturers.set(manufacturers)
        if equipment_types is not None:
            instance.equipment_types.set(equipment_types)
        
        return instance


class PurchasePriceSerializer(serializers.ModelSerializer):
    """Serializer for PurchasePrice model."""
    
    class Meta:
        model = PurchasePrice
        fields = [
            'price_id', 'equipment', 'source_type', 'price', 'currency',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price_id', 'created_at', 'updated_at']


class LogisticsSerializer(serializers.ModelSerializer):
    """Serializer for Logistics model."""
    
    class Meta:
        model = Logistics
        fields = [
            'logistics_id', 'equipment', 'route_type', 'cost', 'currency',
            'estimated_days', 'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['logistics_id', 'created_at', 'updated_at']


class EquipmentDocumentSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentDocument model."""
    
    class Meta:
        model = EquipmentDocument
        fields = [
            'document_id', 'equipment', 'document_type', 'document_name',
            'file', 'file_url', 'file_size', 'is_for_client', 'is_internal',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['document_id', 'created_at', 'updated_at']


class EquipmentLineItemSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentLineItem model."""
    
    class Meta:
        model = EquipmentLineItem
        fields = [
            'equipment_line', 'equipment', 'quantity', 'order', 'created_at'
        ]
        read_only_fields = ['created_at']


class EquipmentLineSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentLine model."""
    line_items = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipmentLine
        fields = [
            'equipment_line_id', 'equipment_line_name',
            'line_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['equipment_line_id', 'created_at', 'updated_at']
    
    def get_line_items(self, obj):
        """Get all line items for this equipment line."""
        line_items = obj.line_items.select_related('equipment').all()
        return [
            {
                'equipment_line': item.equipment_line_id,
                'equipment': item.equipment_id,
                'equipment_name': item.equipment.equipment_name,
                'quantity': item.quantity,
                'order': item.order,
                'created_at': item.created_at
            }
            for item in line_items
        ]


class AdditionalPricesSerializer(serializers.ModelSerializer):
    """Serializer for AdditionalPrices model."""
    
    class Meta:
        model = AdditionalPrices
        fields = [
            'price_id', 'price_parameter_name', 'expense_type', 'value_type',
            'price_parameter_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price_id', 'created_at', 'updated_at']


class EquipmentListLineItemSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentListLineItem model."""
    
    class Meta:
        model = EquipmentListLineItem
        fields = [
            'equipment_list', 'equipment_line', 'quantity', 'created_at'
        ]
        read_only_fields = ['created_at']


class EquipmentListItemSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentListItem model."""
    
    class Meta:
        model = EquipmentListItem
        fields = [
            'equipment_list', 'equipment', 'quantity', 'created_at'
        ]
        read_only_fields = ['created_at']


class EquipmentListLineItemSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentListLineItem model."""
    equipment_line_name = serializers.CharField(source='equipment_line.equipment_line_name', read_only=True)
    
    class Meta:
        model = EquipmentListLineItem
        fields = [
            'equipment_list', 'equipment_line', 'equipment_line_name', 'quantity', 'created_at'
        ]
        read_only_fields = ['created_at']


class EquipmentListItemSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentListItem model."""
    equipment_name = serializers.CharField(source='equipment.equipment_name', read_only=True)
    
    class Meta:
        model = EquipmentListItem
        fields = [
            'equipment_list', 'equipment', 'equipment_name', 'quantity', 'row_expenses', 
            'price_per_unit', 'total_price', 'calculated_data', 'created_at'
        ]
        read_only_fields = ['created_at']


class EquipmentListSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentList model."""
    # Nested data for line items and equipment items
    line_items = serializers.SerializerMethodField()
    equipment_items_data = serializers.SerializerMethodField()
    
    # Support both proposal (read) and proposal_id (write)
    proposal_id = serializers.PrimaryKeyRelatedField(
        queryset=CommercialProposal.objects.all(),
        source='proposal',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Поддержка множественных additional_prices
    additional_prices = serializers.PrimaryKeyRelatedField(
        queryset=AdditionalPrices.objects.all(),
        many=True,
        required=False,
        allow_null=True
    )
    additional_price_ids = serializers.PrimaryKeyRelatedField(
        queryset=AdditionalPrices.objects.all(),
        many=True,
        write_only=True,
        required=False,
        allow_null=True,
        source='additional_prices'
    )
    
    class Meta:
        model = EquipmentList
        fields = [
            'list_id', 'proposal', 'proposal_id', 'line_items', 'equipment_items_data',
            'tax_percentage', 'tax_price', 'delivery_percentage', 'delivery_price',
            'additional_price', 'additional_prices', 'additional_price_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['list_id', 'proposal', 'created_at', 'updated_at']
        extra_kwargs = {
            'tax_percentage': {'required': False, 'allow_null': True},
            'tax_price': {'required': False, 'allow_null': True},
            'delivery_percentage': {'required': False, 'allow_null': True},
            'delivery_price': {'required': False, 'allow_null': True},
        }
    
    def get_line_items(self, obj):
        """Get all line items for this equipment list."""
        line_items = obj.line_items.select_related('equipment_line').all()
        return [
            {
                'equipment_list': item.equipment_list_id,
                'equipment_line': item.equipment_line_id,
                'equipment_line_name': item.equipment_line.equipment_line_name,
                'quantity': item.quantity,
                'created_at': item.created_at
            }
            for item in line_items
        ]
    
    def get_equipment_items_data(self, obj):
        """Get all equipment items for this equipment list."""
        equipment_items = obj.equipment_items_relation.select_related('equipment').all()
        return EquipmentListItemSerializer(equipment_items, many=True).data


class PaymentLogSerializer(serializers.ModelSerializer):
    """Serializer for PaymentLog model."""
    
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    
    class Meta:
        model = PaymentLog
        fields = [
            'payment_id', 'payment_name', 'payment_value', 'payment_date',
            'comments', 'user', 'user_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['payment_id', 'created_at', 'updated_at', 'user_name']


class CommercialProposalSerializer(serializers.ModelSerializer):
    """Serializer for CommercialProposal model with nested relationships."""
    
    # Nested serializers for read operations
    client = ClientSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    parent_proposal = serializers.SerializerMethodField()
    payment_logs = PaymentLogSerializer(many=True, required=False)
    equipment_lists = EquipmentListSerializer(many=True, read_only=True)
    
    # Primary key fields for write operations
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        source='client',
        write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False,
        allow_null=True
    )
    parent_proposal_id = serializers.PrimaryKeyRelatedField(
        queryset=CommercialProposal.objects.all(),
        source='parent_proposal',
        write_only=True,
        required=False,
        allow_null=True
    )
    payment_log_ids = serializers.PrimaryKeyRelatedField(
        queryset=PaymentLog.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    additional_price_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='Список ID дополнительных расходов (общие для КП)'
    )
    
    proposal_version = serializers.IntegerField(required=False, default=1)
    
    # Поля для записи оборудования при создании/обновлении
    equipment_items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text='Список оборудования с quantity и equipment_id'
    )
    equipment_list = serializers.DictField(
        write_only=True,
        required=False,
        help_text='Данные для EquipmentList (tax_percentage, delivery_percentage и т.д.)'
    )
    
    data_package = serializers.SerializerMethodField()
    
    class Meta:
        model = CommercialProposal
        fields = [
            'proposal_id', 'proposal_name', 'outcoming_number',
            'client', 'client_id', 'user', 'user_id',
            'currency_ticket', 'exchange_rate', 'exchange_rate_date',
            'total_price', 'cost_price', 'margin_percentage', 'margin_value',
            'proposal_date', 'valid_until', 'delivery_time', 'warranty',
            'proposal_status', 'proposal_version', 'is_active',

            'parent_proposal', 'parent_proposal_id',
            'comments', 'bitrix_lead_link',
            'payment_logs', 'payment_log_ids',
            'equipment_lists', 'equipment_items', 'equipment_list',
            'additional_price_ids', 'internal_exchange_rates', 'additional_services',
            'data_package', 'created_at', 'updated_at', 'updated_by', 'template_status'
        ]
        read_only_fields = ['proposal_id', 'created_at', 'updated_at', 'updated_by', 'data_package']
    
    def get_data_package(self, obj):
        """Return data_package if exists, otherwise return None (will be generated on demand)."""
        return obj.data_package if obj.data_package else None
    
    def get_parent_proposal(self, obj):
        """Return parent proposal basic info if exists."""
        if obj.parent_proposal:
            return {
                'proposal_id': obj.parent_proposal.proposal_id,
                'proposal_name': obj.parent_proposal.proposal_name,
                'outcoming_number': obj.parent_proposal.outcoming_number,
                'proposal_status': obj.parent_proposal.proposal_status
            }
        return None

    template_status = serializers.SerializerMethodField()

    def get_template_status(self, obj):
        """Return status of the proposal template."""
        if hasattr(obj, 'template'):
            return 'Ready' if obj.template.is_final else 'Draft'
        return 'Not Created'
    
    def create(self, validated_data):
        """Create CommercialProposal with ManyToMany relationships and equipment lists."""
        from django.db import transaction
        from .models import EquipmentList, EquipmentListItem, AdditionalPrices
        
        payment_logs_data = validated_data.pop('payment_logs', [])
        payment_log_ids = validated_data.pop('payment_log_ids', [])
        additional_price_ids = validated_data.pop('additional_price_ids', [])
        equipment_items_data = validated_data.pop('equipment_items', [])  # Данные об оборудовании
        equipment_list_data = validated_data.pop('equipment_list', {})  # Данные для EquipmentList (налоги, доставка и т.д.)
        
        if 'proposal_version' not in validated_data:
            validated_data['proposal_version'] = 1
            
        try:
            with transaction.atomic():
                # Создаем КП
                proposal = CommercialProposal.objects.create(**validated_data)
                
                # Связываем платежи
                # Связываем платежи (по ID)
                if payment_log_ids:
                    proposal.payment_logs.set(payment_log_ids)
                
                # Создаем и связываем новые платежи из nested data
                if payment_logs_data:
                    current_user = self.context['request'].user if 'request' in self.context else None
                    for payment_data in payment_logs_data:
                        # Если передан ID, то это существующий платеж (хотя при create обычно новые)
                        # Но для надежности проверяем
                        if 'payment_id' in payment_data:
                            payment = PaymentLog.objects.get(pk=payment_data['payment_id'])
                            # Можно обновить поля если надо
                        else:
                            # Удаляем user_id и user_name из данных, чтобы бэкенд установил user автоматически
                            payment_data.pop('user_id', None)
                            payment_data.pop('user_name', None)
                            payment_data.pop('user', None)
                            # Устанавливаем user из контекста запроса
                            if current_user:
                                payment_data['user'] = current_user
                            payment = PaymentLog.objects.create(**payment_data)
                        
                        proposal.payment_logs.add(payment)
                
                # Создаем EquipmentList (всегда создаем один основной список для КП)
                # Даже если нет оборудования, список нужен для хранения общих расходов
                prop_additional_price_ids = additional_price_ids
                # Если передали внутри equipment_list_data (старый формат), тоже учитываем
                if not prop_additional_price_ids:
                    prop_additional_price_ids = equipment_list_data.get('additional_price_ids', [])
                
                # Поддержка старого формата для обратной совместимости
                if not prop_additional_price_ids and equipment_list_data.get('additional_price_id'):
                    prop_additional_price_ids = [equipment_list_data.get('additional_price_id')]
                
                equipment_list = EquipmentList.objects.create(
                    proposal=proposal,
                    tax_percentage=equipment_list_data.get('tax_percentage'),
                    tax_price=equipment_list_data.get('tax_price'),
                    delivery_percentage=equipment_list_data.get('delivery_percentage'),
                    delivery_price=equipment_list_data.get('delivery_price'),
                )
                
                # Связываем дополнительные расходы
                if prop_additional_price_ids:
                    equipment_list.additional_prices.set(prop_additional_price_ids)
                
                # Создаем EquipmentListItem для каждого оборудования
                if equipment_items_data:
                    # Группируем оборудование по ID, чтобы избежать IntegrityError
                    # (т.к. в базе есть unique_together=['equipment_list', 'equipment'])
                    # Но сохраняем порядок из исходного массива
                    grouped_items = {}
                    order_map = {}  # Сохраняем порядок первого вхождения каждого equipment_id
                    
                    for order, item_data in enumerate(equipment_items_data, start=1):
                        eq_id = int(item_data['equipment_id'])
                        calculated_data = item_data.get('calculated_data', {})
                        if eq_id in grouped_items:
                            grouped_items[eq_id]['quantity'] += item_data.get('quantity', 1)
                            # Объединяем row_expenses если они есть
                            if 'row_expenses' in item_data and item_data['row_expenses']:
                                grouped_items[eq_id]['row_expenses'].extend(item_data['row_expenses'])
                            # Сохраняем calculated_data из последнего элемента (самый актуальный)
                            if calculated_data:
                                grouped_items[eq_id]['calculated_data'] = calculated_data
                        else:
                            grouped_items[eq_id] = {
                                'quantity': item_data.get('quantity', 1),
                                'row_expenses': item_data.get('row_expenses', []),
                                'calculated_data': calculated_data
                            }
                            order_map[eq_id] = order

                    # Сортируем по порядку из исходного массива
                    sorted_items = sorted(grouped_items.items(), key=lambda x: order_map.get(x[0], 999))
                    
                    for order, (eq_id, data) in enumerate(sorted_items, start=1):
                        EquipmentListItem.objects.create(
                            equipment_list=equipment_list,
                            equipment_id=eq_id,
                            quantity=data['quantity'],
                            row_expenses=data['row_expenses'],
                            calculated_data=data.get('calculated_data', {}),
                            order=order
                        )
            
            return proposal
        except Exception as e:
            import traceback
            with open('debug_error.log', 'a') as f:
                f.write(f"Error creating proposal: {str(e)}\n")
                f.write(traceback.format_exc())
                f.write(f"Validated data: {validated_data}\n")
            raise e
    
    def update(self, instance, validated_data):
        """Update CommercialProposal with ManyToMany relationships and equipment lists."""
        from django.db import transaction
        from .models import EquipmentList, EquipmentListItem
        
        payment_logs_data = validated_data.pop('payment_logs', None)
        payment_log_ids = validated_data.pop('payment_log_ids', None)
        additional_price_ids = validated_data.pop('additional_price_ids', None)
        equipment_items_data = validated_data.pop('equipment_items', None)
        equipment_list_data = validated_data.pop('equipment_list', None)
        
        with transaction.atomic():
            # Update all fields with proper Decimal handling
            for attr, value in validated_data.items():
                try:
                    # Get field metadata
                    field = instance._meta.get_field(attr)
                    
                    # Handle Decimal fields specially
                    from django.db import models as django_models
                    if isinstance(field, django_models.DecimalField):
                        if value is None:
                            if field.null or field.blank:
                                setattr(instance, attr, None)
                            continue
                        
                        # Convert to Decimal safely
                        from decimal import Decimal, InvalidOperation
                        try:
                            if isinstance(value, str):
                                # Skip empty strings or invalid values
                                value_str = value.strip()
                                if not value_str or value_str.lower() in ['nan', 'inf', '-inf', 'infinity', '-infinity']:
                                    continue
                                decimal_value = Decimal(value_str)
                            elif isinstance(value, (int, float)):
                                # Check for NaN or Infinity
                                if isinstance(value, float) and (value != value or not (-1e308 < value < 1e308)):
                                    continue  # Skip NaN or Infinity
                                decimal_value = Decimal(str(value))
                            else:
                                decimal_value = Decimal(str(value))
                            
                            # Quantize to field's decimal_places
                            quantize_value = Decimal('0.1') ** field.decimal_places
                            decimal_value = decimal_value.quantize(quantize_value)
                            
                            setattr(instance, attr, decimal_value)
                        except (InvalidOperation, ValueError, TypeError) as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f'Invalid Decimal value for {attr}: {value}, error: {e}')
                            continue  # Skip invalid values
                    else:
                        # For non-Decimal fields, set directly
                        setattr(instance, attr, value)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Error setting field {attr}: {e}')
                    continue
            
            instance.save()
            
            # Update ManyToMany if provided
            if payment_log_ids is not None:
                instance.payment_logs.set(payment_log_ids)
            
            # Обработка nested payment_logs
            if payment_logs_data is not None:
                # Если пришли данные, синхронизируем их
                # Стратегия: 
                # 1. Существующие в списке (с ID) - обновляем и привязываем
                # 2. Новые (без ID) - создаем и привязываем
                # 3. Те что были привязаны, но не пришли в списке - отвязываем (или удаляем?)
                # Поскольку это лог "внутри" КП, логично что список полный.
                # Но у нас есть еще payment_log_ids. 
                # Давайте сделаем добавление/обновление.
                
                current_user = self.context['request'].user if 'request' in self.context else None
                new_payment_ids = []
                
                for payment_data in payment_logs_data:
                    payment_id = payment_data.get('payment_id')
                    if payment_id:
                        # Обновляем существующий
                        payment = PaymentLog.objects.get(pk=payment_id)
                        for key, value in payment_data.items():
                             if key != 'payment_id': # Не обновляем ID
                                 setattr(payment, key, value)
                        payment.save()
                        new_payment_ids.append(payment.payment_id)
                    else:
                        # Создаем новый
                        # Удаляем user_id и user_name из данных, чтобы бэкенд установил user автоматически
                        payment_data.pop('user_id', None)
                        payment_data.pop('user_name', None)
                        payment_data.pop('user', None)
                        # Устанавливаем user из контекста запроса
                        if current_user:
                            payment_data['user'] = current_user
                        payment = PaymentLog.objects.create(**payment_data)
                        new_payment_ids.append(payment.payment_id)
                
                # Если мы хотим полную синхронизацию списка платежей (удалить те, что не пришли)
                # instance.payment_logs.set(new_payment_ids)
                # Или просто добавить новые?
                # Workflow: "Синхронизация... Данные должны отправляться на сервер".
                # "Действия: Иконка «Корзина» для удаления черновика строки или уже существующего платежа."
                # Это означает, что если пользователь удалил платеж в UI, он должен удалиться (или отвязаться).
                # Поэтому используем set() для полной замены списка привязанных платежей на тот, что пришел с фронта.
                
                # Объединяем с payment_log_ids если они были переданы
                if payment_log_ids:
                    new_payment_ids.extend([pid.payment_id if hasattr(pid, 'payment_id') else pid for pid in payment_log_ids])
                
                # Удаляем дубликаты
                new_payment_ids = list(set(new_payment_ids))
                
                instance.payment_logs.set(new_payment_ids)
            
            # Logic for EquipmentList update:
            # We assume there is only one EquipmentList per Proposal.
            # If it exists, update it. If not, create it.
            
            equipment_list = instance.equipment_lists.first()
            
            # Update EquipmentList fields if provided
            if equipment_list_data or additional_price_ids is not None:
                 if not equipment_list:
                     equipment_list = EquipmentList.objects.create(proposal=instance)
                 
                 if equipment_list_data:
                     if 'tax_percentage' in equipment_list_data:
                         equipment_list.tax_percentage = equipment_list_data['tax_percentage']
                     if 'tax_price' in equipment_list_data:
                         equipment_list.tax_price = equipment_list_data['tax_price']
                     if 'delivery_percentage' in equipment_list_data:
                         equipment_list.delivery_percentage = equipment_list_data['delivery_percentage']
                     if 'delivery_price' in equipment_list_data:
                         equipment_list.delivery_price = equipment_list_data['delivery_price']
                     equipment_list.save()

                 if additional_price_ids is not None:
                     equipment_list.additional_prices.set(additional_price_ids)

            # Update equipment items if provided
            if equipment_items_data is not None:
                if not equipment_list:
                     equipment_list = EquipmentList.objects.create(proposal=instance)
                
                # Извлекаем все существующие EquipmentListItem для обновления
                # Стратегия: удаляем старые и создаем новые (самый простой способ синхронизации Many2Many через промежуточную таблицу с доп. полями)
                equipment_list.equipment_items_relation.all().delete()
                
                # Группируем оборудование по ID, но сохраняем порядок из исходного массива
                grouped_items = {}
                order_map = {}  # Сохраняем порядок первого вхождения каждого equipment_id
                
                for order, item_data in enumerate(equipment_items_data, start=1):
                    eq_id = int(item_data['equipment_id'])
                    calculated_data = item_data.get('calculated_data', {})
                    if eq_id in grouped_items:
                        grouped_items[eq_id]['quantity'] += item_data.get('quantity', 1)
                        if 'row_expenses' in item_data and item_data['row_expenses']:
                            grouped_items[eq_id]['row_expenses'].extend(item_data['row_expenses'])
                        # Сохраняем calculated_data из последнего элемента (самый актуальный)
                        if calculated_data:
                            grouped_items[eq_id]['calculated_data'] = calculated_data
                    else:
                        grouped_items[eq_id] = {
                            'quantity': item_data.get('quantity', 1),
                            'row_expenses': item_data.get('row_expenses', []),
                            'calculated_data': calculated_data
                        }
                        order_map[eq_id] = order

                # Сортируем по порядку из исходного массива
                sorted_items = sorted(grouped_items.items(), key=lambda x: order_map.get(x[0], 999))

                for order, (eq_id, data) in enumerate(sorted_items, start=1):
                    EquipmentListItem.objects.create(
                        equipment_list=equipment_list,
                        equipment_id=eq_id,
                        quantity=data['quantity'],
                        row_expenses=data['row_expenses'],
                        calculated_data=data.get('calculated_data', {}),
                        order=order
                    )
        
        return instance


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for ExchangeRate model."""
    
    # Nested serializers for read operations
    proposal = CommercialProposalSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    # Primary key fields for write operations
    proposal_id = serializers.PrimaryKeyRelatedField(
        queryset=CommercialProposal.objects.all(),
        source='proposal',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='created_by',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Display choices in response
    currency_from_display = serializers.CharField(source='get_currency_from_display', read_only=True)
    currency_to_display = serializers.CharField(source='get_currency_to_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = ExchangeRate
        fields = [
            'rate_id', 'currency_from', 'currency_from_display',
            'currency_to', 'currency_to_display',
            'rate_value', 'rate_date', 'source', 'source_display',
            'is_active', 'is_official',
            'proposal', 'proposal_id',
            'notes', 'created_by', 'created_by_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['rate_id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate exchange rate data."""
        currency_from = data.get('currency_from')
        currency_to = data.get('currency_to')
        
        # Нельзя создать курс для одинаковых валют
        if currency_from and currency_to and currency_from == currency_to:
            raise serializers.ValidationError({
                'currency_to': 'Валюта "из" и "в" не могут быть одинаковыми.'
            })
        
        # Значение курса должно быть положительным
        rate_value = data.get('rate_value')
        if rate_value is not None and rate_value <= 0:
            raise serializers.ValidationError({
                'rate_value': 'Значение курса должно быть положительным числом.'
            })
        
        return data


class CostCalculationSerializer(serializers.ModelSerializer):
    """Serializer for CostCalculation model."""
    
    # Nested serializers for read operations
    equipment = EquipmentSerializer(read_only=True)
    proposal = CommercialProposalSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    # Primary key fields for write operations
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    proposal_id = serializers.PrimaryKeyRelatedField(
        queryset=CommercialProposal.objects.all(),
        source='proposal',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='created_by',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CostCalculation
        fields = [
            'calculation_id', 'equipment', 'equipment_id',
            'proposal', 'proposal_id',
            'calculation_version',
            'purchase_price_id', 'purchase_price_value', 'purchase_price_currency', 'purchase_price_source',
            'logistics_id', 'logistics_cost', 'logistics_currency', 'logistics_route',
            'warehouse_cost', 'warehouse_currency',
            'production_cost', 'production_currency',
            'additional_costs', 'additional_costs_currency',
            'exchange_rate_id', 'exchange_rate_value', 'exchange_rate_from', 'exchange_rate_to', 'exchange_rate_date',
            'total_cost_base_currency', 'total_cost_kzt',
            'calculation_details',
            'is_manual_adjustment', 'notes',
            'created_by', 'created_by_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'calculation_id', 'calculation_version', 'created_at', 'updated_at',
            'purchase_price_id', 'purchase_price_value', 'purchase_price_currency', 'purchase_price_source',
            'logistics_id', 'logistics_cost', 'logistics_currency', 'logistics_route',
            'warehouse_cost', 'warehouse_currency',
            'production_cost', 'production_currency',
            'additional_costs', 'additional_costs_currency',
            'exchange_rate_id', 'exchange_rate_value', 'exchange_rate_from', 'exchange_rate_to', 'exchange_rate_date',
            'total_cost_base_currency', 'total_cost_kzt',
            'calculation_details'
        ]


class CostCalculationRequestSerializer(serializers.Serializer):
    """Serializer for cost calculation request."""
    equipment_id = serializers.IntegerField(required=True)
    purchase_price_id = serializers.IntegerField(required=False, allow_null=True)
    logistics_id = serializers.IntegerField(required=False, allow_null=True)
    additional_prices_id = serializers.IntegerField(required=False, allow_null=True)
    exchange_rate_date = serializers.DateField(required=False, allow_null=True)
    proposal_id = serializers.IntegerField(required=False, allow_null=True)
    target_currency = serializers.CharField(max_length=10, default='KZT', required=False)
    save_calculation = serializers.BooleanField(default=False, required=False)
    
    # Ручные переопределения
    manual_overrides = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        allow_null=True
    )
    
    def validate_equipment_id(self, value):
        """Validate equipment exists."""
        from .models import Equipment
        try:
            Equipment.objects.get(equipment_id=value)
        except Equipment.DoesNotExist:
            raise serializers.ValidationError('Equipment not found.')
        return value
    
    def validate_proposal_id(self, value):
        """Validate proposal exists if provided."""
        if value is not None:
            from .models import CommercialProposal
            try:
                CommercialProposal.objects.get(proposal_id=value)
            except CommercialProposal.DoesNotExist:
                raise serializers.ValidationError('Commercial proposal not found.')
        return value


def _save_prices_to_equipment_list_items(proposal, equipment_list_data):
    """
    Сохраняет итоговые цены из equipment_list в EquipmentListItem.
    
    Args:
        proposal: CommercialProposal instance
        equipment_list_data: список словарей с данными оборудования, включая price_per_unit и total_price
    """
    if not equipment_list_data:
        return
    
    from decimal import Decimal
    equipment_list = proposal.equipment_lists.first()
    if not equipment_list:
        return
    
    # Создаем словарь для быстрого поиска по equipment_id
    data_map = {}
    for item in equipment_list_data:
        if 'equipment_id' not in item:
            continue
        
        eq_id = item['equipment_id']
        
        # Safely convert price_per_unit and total_price to Decimal
        try:
            price_per_unit = Decimal(str(item.get('price_per_unit', 0)))
        except (ValueError, TypeError, InvalidOperation):
            price_per_unit = Decimal('0')
        
        try:
            total_price = Decimal(str(item.get('total_price', 0)))
        except (ValueError, TypeError, InvalidOperation):
            total_price = Decimal('0')
        
        # Prepare calculated_data
        calculated_data = {}
        try:
            if item.get('base_cost_kzt') is not None:
                calculated_data['base_cost_kzt'] = float(item.get('base_cost_kzt', 0))
            if item.get('allocated_overhead_per_unit') is not None:
                calculated_data['allocated_overhead_per_unit'] = float(item.get('allocated_overhead_per_unit', 0))
            if item.get('margin_kzt') is not None:
                calculated_data['margin_kzt'] = float(item.get('margin_kzt', 0))
            if item.get('margin_percentage') is not None:
                calculated_data['margin_percentage'] = float(item.get('margin_percentage', 0))
            if item.get('purchase_price_kzt') is not None:
                calculated_data['purchase_price_kzt'] = float(item.get('purchase_price_kzt', 0))
        except (ValueError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Error preparing calculated_data for equipment {eq_id}: {e}')
            # Continue with empty calculated_data if conversion fails
        
        data_map[eq_id] = {
            'price_per_unit': price_per_unit,
            'total_price': total_price,
            'calculated_data': calculated_data
        }
    
    # Обновляем цены и calculated_data в EquipmentListItem
    for item in equipment_list.equipment_items_relation.all():
        if item.equipment.equipment_id in data_map:
            data = data_map[item.equipment.equipment_id]
            
            item.price_per_unit = data['price_per_unit']
            item.total_price = data['total_price']
            item.calculated_data = data['calculated_data']
            item.save(update_fields=['price_per_unit', 'total_price', 'calculated_data'])


class ProposalTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ProposalTemplate model."""
    data_package = serializers.SerializerMethodField()
    # Allow writing data_package to save it to proposal
    data_package_to_save = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = ProposalTemplate
        fields = [
            'template_id', 'proposal', 'layout_data', 'header_data', 'data_package',
            'data_package_to_save', 'is_final', 'last_edited_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['template_id', 'created_at', 'updated_at', 'data_package']

    def get_data_package(self, obj):
        """Get data_package from proposal if exists, otherwise generate it."""
        proposal = obj.proposal
        # First try to get from saved data_package in proposal
        if proposal.data_package:
            return proposal.data_package
        
        # Fallback: generate it
        try:
            from .services import DataAggregatorService
            service = DataAggregatorService(proposal)
            return service.get_full_data_package()
        except Exception as e:
            # Fallback or log error to avoid breaking the serializer if something goes wrong
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting data package for template {obj.template_id}: {e}")
            return None

    def create(self, validated_data):
        """Create template and save data_package to proposal."""
        from .services import DataAggregatorService
        
        proposal = validated_data.get('proposal')
        template = super().create(validated_data)
        
        # Generate and save data_package to proposal
        if proposal:
            try:
                service = DataAggregatorService(proposal)
                data_pkg = service.get_full_data_package()
                proposal.data_package = data_pkg
                proposal.save(update_fields=['data_package'])
                
                # Сохранить итоговые цены в EquipmentListItem
                if 'equipment_list' in data_pkg:
                    _save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving data_package to proposal {proposal.proposal_id}: {e}")
        
        return template

    def update(self, instance, validated_data):
        """Update template and save data_package to proposal if provided."""
        proposal = validated_data.get('proposal') or instance.proposal
        
        # Extract data_package_to_save if provided
        data_package_to_save = validated_data.pop('data_package_to_save', None)
        
        template = super().update(instance, validated_data)
        
        # Save data_package to proposal if provided
        if proposal and data_package_to_save is not None:
            try:
                # Ensure we have all required fields by merging with fresh data if needed
                from .services import DataAggregatorService
                from datetime import date, datetime
                from decimal import Decimal
                
                def _fix_json_serialization(obj):
                    """Recursively fix JSON serialization issues in data structures."""
                    if isinstance(obj, dict):
                        return {k: _fix_json_serialization(v) for k, v in obj.items()}
                    elif isinstance(obj, (list, tuple)):
                        return [_fix_json_serialization(item) for item in obj]
                    elif isinstance(obj, (date, datetime)):
                        return obj.isoformat()
                    elif isinstance(obj, Decimal):
                        return float(obj)
                    elif hasattr(obj, '__dict__'):
                        # Handle model instances
                        return str(obj)
                    else:
                        return obj
                
                # Get fresh data package to ensure completeness
                service = DataAggregatorService(proposal)
                fresh_data_package = service.get_full_data_package()
                
                # Merge: use data from constructor (layout_data changes) but ensure all equipment data is present
                # Preserve equipment_list order and any custom changes from constructor
                merged_package = fresh_data_package.copy()
                
                # Preserve equipment_list from constructor if it exists (may have custom order/changes)
                # BUT ensure prices are updated from fresh calculation to match current proposal totals
                if 'equipment_list' in data_package_to_save and data_package_to_save['equipment_list']:
                    constructor_list = data_package_to_save['equipment_list']
                    fresh_list = fresh_data_package.get('equipment_list', [])
                    
                    # Create a map of fresh data by equipment_id for price updates
                    fresh_map = {item['equipment_id']: item for item in fresh_list}
                    
                    # Use constructor list order but update prices from fresh calculation
                    merged_list = []
                    for constructor_item in constructor_list:
                        eq_id = constructor_item.get('equipment_id')
                        if eq_id in fresh_map:
                            # Update prices from fresh calculation but keep constructor order and other fields
                            merged_item = constructor_item.copy()
                            merged_item['price_per_unit'] = fresh_map[eq_id]['price_per_unit']
                            merged_item['total_price'] = fresh_map[eq_id]['total_price']
                            # Also update quantity if it changed
                            merged_item['quantity'] = fresh_map[eq_id]['quantity']
                            # Update calculated data from fresh calculation
                            if 'base_cost_kzt' in fresh_map[eq_id]:
                                merged_item['base_cost_kzt'] = fresh_map[eq_id]['base_cost_kzt']
                            if 'allocated_overhead_per_unit' in fresh_map[eq_id]:
                                merged_item['allocated_overhead_per_unit'] = fresh_map[eq_id]['allocated_overhead_per_unit']
                            if 'margin_kzt' in fresh_map[eq_id]:
                                merged_item['margin_kzt'] = fresh_map[eq_id]['margin_kzt']
                            if 'margin_percentage' in fresh_map[eq_id]:
                                merged_item['margin_percentage'] = fresh_map[eq_id]['margin_percentage']
                            if 'purchase_price_kzt' in fresh_map[eq_id]:
                                merged_item['purchase_price_kzt'] = fresh_map[eq_id]['purchase_price_kzt']
                            merged_list.append(merged_item)
                        else:
                            # If not in fresh, keep constructor item as-is
                            merged_list.append(constructor_item)
                    
                    merged_package['equipment_list'] = merged_list
                else:
                    # If no constructor list, use fresh list
                    merged_package['equipment_list'] = fresh_data_package.get('equipment_list', [])
                
                # Ensure all equipment data is present (details, specs, tech_processes)
                # Use fresh data to fill in any missing equipment
                merged_package['equipment_details'] = fresh_data_package.get('equipment_details', {})
                merged_package['equipment_specifications'] = fresh_data_package.get('equipment_specifications', {})
                merged_package['tech_processes'] = fresh_data_package.get('tech_processes', {})
                
                # Preserve other fields from constructor if they exist
                if 'additional_services' in data_package_to_save:
                    merged_package['additional_services'] = data_package_to_save['additional_services']
                if 'company_logo_url' in data_package_to_save:
                    merged_package['company_logo_url'] = data_package_to_save['company_logo_url']
                
                # Fix JSON serialization before saving
                fixed_package = _fix_json_serialization(merged_package)
                proposal.data_package = fixed_package
                proposal.save(update_fields=['data_package'])
                
                # Сохранить итоговые цены в EquipmentListItem
                if 'equipment_list' in merged_package:
                    _save_prices_to_equipment_list_items(proposal, merged_package['equipment_list'])
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving data_package to proposal {proposal.proposal_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        elif proposal and not proposal.data_package:
            # If no data_package provided and proposal doesn't have one, generate it
            try:
                from .services import DataAggregatorService
                service = DataAggregatorService(proposal)
                data_pkg = service.get_full_data_package()
                proposal.data_package = data_pkg
                proposal.save(update_fields=['data_package'])
                
                # Сохранить итоговые цены в EquipmentListItem
                if 'equipment_list' in data_pkg:
                    _save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error generating data_package for proposal {proposal.proposal_id}: {e}")
        
        return template

class SectionTemplateSerializer(serializers.ModelSerializer):
    """Serializer for SectionTemplate model."""
    
    class Meta:
        model = SectionTemplate
        fields = ['id', 'name', 'title', 'text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
