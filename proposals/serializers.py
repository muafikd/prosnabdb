from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Client, Category, Manufacturer, EquipmentTypes, EquipmentDetails,
    EquipmentSpecification, EquipmentTechProcess, Equipment, PurchasePrice,
    Logistics, EquipmentDocument, EquipmentLine, EquipmentLineItem, AdditionalPrices,
    EquipmentList, EquipmentListLineItem, EquipmentListItem, PaymentLog, CommercialProposal,
    ExchangeRate, CostCalculation
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
        }
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.',
                'password_confirm': 'Passwords do not match.'
            })
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
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


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
    
    class Meta:
        model = Equipment
        fields = [
            'equipment_id', 'equipment_name', 'equipment_articule', 'equipment_uom',
            'equipment_short_description', 'equipment_warranty', 'is_published',
            'categories', 'manufacturers', 'equipment_types',
            'details', 'specifications', 'tech_processes',
            'equipment_imagelinks', 'equipment_videolinks',
            'equipment_manufacture_price', 'equipment_madein_country',
            'equipment_price_currency_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['equipment_id', 'created_at', 'updated_at']
    
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
            'equipment_list', 'equipment', 'equipment_name', 'quantity', 'created_at'
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
        return [
            {
                'equipment_list': item.equipment_list_id,
                'equipment': item.equipment_id,
                'equipment_name': item.equipment.equipment_name,
                'quantity': item.quantity,
                'created_at': item.created_at
            }
            for item in equipment_items
        ]


class PaymentLogSerializer(serializers.ModelSerializer):
    """Serializer for PaymentLog model."""
    
    class Meta:
        model = PaymentLog
        fields = [
            'payment_id', 'payment_name', 'payment_value', 'payment_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['payment_id', 'created_at', 'updated_at']


class CommercialProposalSerializer(serializers.ModelSerializer):
    """Serializer for CommercialProposal model with nested relationships."""
    
    # Nested serializers for read operations
    client = ClientSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    parent_proposal = serializers.SerializerMethodField()
    payment_logs = PaymentLogSerializer(many=True, read_only=True)
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
    
    class Meta:
        model = CommercialProposal
        fields = [
            'proposal_id', 'proposal_name', 'outcoming_number',
            'client', 'client_id', 'user', 'user_id',
            'currency_ticket', 'exchange_rate', 'exchange_rate_date',
            'total_price', 'cost_price', 'margin_percentage',
            'proposal_date', 'valid_until', 'delivery_time', 'warranty',
            'proposal_status', 'proposal_version',
            'parent_proposal', 'parent_proposal_id',
            'comments', 'bitrix_lead_link',
            'payment_logs', 'payment_log_ids',
            'equipment_lists', 'equipment_items', 'equipment_list',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['proposal_id', 'created_at', 'updated_at']
    
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
    
    def create(self, validated_data):
        """Create CommercialProposal with ManyToMany relationships and equipment lists."""
        from django.db import transaction
        from .models import EquipmentList, EquipmentListItem, AdditionalPrices
        
        payment_logs = validated_data.pop('payment_log_ids', [])
        equipment_items_data = validated_data.pop('equipment_items', [])  # Данные об оборудовании
        equipment_list_data = validated_data.pop('equipment_list', {})  # Данные для EquipmentList (налоги, доставка и т.д.)
        
        with transaction.atomic():
            # Создаем КП
            proposal = CommercialProposal.objects.create(**validated_data)
            
            # Связываем платежи
            if payment_logs:
                proposal.payment_logs.set(payment_logs)
            
            # Создаем EquipmentList если есть оборудование
            if equipment_items_data:
                additional_price_ids = equipment_list_data.get('additional_price_ids', [])
                # Поддержка старого формата для обратной совместимости
                if not additional_price_ids and equipment_list_data.get('additional_price_id'):
                    additional_price_ids = [equipment_list_data.get('additional_price_id')]
                
                equipment_list = EquipmentList.objects.create(
                    proposal=proposal,
                    tax_percentage=equipment_list_data.get('tax_percentage'),
                    tax_price=equipment_list_data.get('tax_price'),
                    delivery_percentage=equipment_list_data.get('delivery_percentage'),
                    delivery_price=equipment_list_data.get('delivery_price'),
                )
                
                # Связываем дополнительные расходы
                if additional_price_ids:
                    equipment_list.additional_prices.set(additional_price_ids)
                
                # Создаем EquipmentListItem для каждого оборудования
                for item_data in equipment_items_data:
                    EquipmentListItem.objects.create(
                        equipment_list=equipment_list,
                        equipment_id=item_data['equipment_id'],
                        quantity=item_data.get('quantity', 1)
                    )
        
        return proposal
    
    def update(self, instance, validated_data):
        """Update CommercialProposal with ManyToMany relationships and equipment lists."""
        from django.db import transaction
        from .models import EquipmentList, EquipmentListItem
        
        payment_logs = validated_data.pop('payment_log_ids', None)
        equipment_items_data = validated_data.pop('equipment_items', None)
        equipment_list_data = validated_data.pop('equipment_list', None)
        
        with transaction.atomic():
            # Update all fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update ManyToMany if provided
            if payment_logs is not None:
                instance.payment_logs.set(payment_logs)
            
            # Update equipment lists if provided
            if equipment_items_data is not None:
                # Удаляем старые EquipmentList
                instance.equipment_lists.all().delete()
                
                # Создаем новый EquipmentList
                if equipment_items_data:
                    additional_price_ids = equipment_list_data.get('additional_price_ids', []) if equipment_list_data else []
                    # Поддержка старого формата для обратной совместимости
                    if not additional_price_ids and equipment_list_data and equipment_list_data.get('additional_price_id'):
                        additional_price_ids = [equipment_list_data.get('additional_price_id')]
                    
                    equipment_list = EquipmentList.objects.create(
                        proposal=instance,
                        tax_percentage=equipment_list_data.get('tax_percentage') if equipment_list_data else None,
                        tax_price=equipment_list_data.get('tax_price') if equipment_list_data else None,
                        delivery_percentage=equipment_list_data.get('delivery_percentage') if equipment_list_data else None,
                        delivery_price=equipment_list_data.get('delivery_price') if equipment_list_data else None,
                    )
                    
                    # Связываем дополнительные расходы
                    if additional_price_ids:
                        equipment_list.additional_prices.set(additional_price_ids)
                    
                    # Создаем EquipmentListItem для каждого оборудования
                    for item_data in equipment_items_data:
                        EquipmentListItem.objects.create(
                            equipment_list=equipment_list,
                            equipment_id=item_data['equipment_id'],
                            quantity=item_data.get('quantity', 1)
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

