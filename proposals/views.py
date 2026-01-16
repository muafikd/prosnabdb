from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.db.models import Q
try:
    from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
    from drf_spectacular.types import OpenApiTypes
except ImportError:
    # Fallback if drf-spectacular is not installed
    def extend_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def extend_schema_view(**kwargs):
        def decorator(cls):
            return cls
        return decorator
    OpenApiParameter = None
    OpenApiExample = None
    OpenApiTypes = None
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import (
    User, Client, Category, Manufacturer, EquipmentTypes, EquipmentDetails,
    EquipmentSpecification, EquipmentTechProcess, Equipment, PurchasePrice,
    Logistics, EquipmentDocument, EquipmentLine, EquipmentLineItem, AdditionalPrices,
    EquipmentList, EquipmentListLineItem, EquipmentListItem, PaymentLog, CommercialProposal,
    ExchangeRate, CostCalculation
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    ClientSerializer, CategorySerializer, ManufacturerSerializer,
    EquipmentTypesSerializer, EquipmentDetailsSerializer,
    EquipmentSpecificationSerializer, EquipmentTechProcessSerializer,
    EquipmentSerializer, PurchasePriceSerializer, LogisticsSerializer,
    EquipmentDocumentSerializer, EquipmentLineSerializer, EquipmentLineItemSerializer,
    AdditionalPricesSerializer, EquipmentListSerializer, EquipmentListLineItemSerializer,
    EquipmentListItemSerializer, PaymentLogSerializer, CommercialProposalSerializer,
    ExchangeRateSerializer, CostCalculationSerializer, CostCalculationRequestSerializer
)
from .services import CostCalculationService
from .permissions import IsManagerOrAdmin


class UserRegistrationView(generics.CreateAPIView):
    """
    Endpoint for user registration.
    
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Endpoint for user login.
    
    POST /api/auth/login/
    Body: {"user_login": "username", "password": "password"}
    """
    serializer = UserLoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Endpoint for user logout.
    
    POST /api/auth/logout/
    Headers: Authorization: Bearer <access_token>
    Body (optional): {"refresh_token": "token"} - to blacklist refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'message': 'Logout successful. Refresh token has been blacklisted.'
            }, status=status.HTTP_200_OK)
        else:
            # Just logout (session-based)
            logout(request)
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Invalid refresh token or logout failed.',
            'detail': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint to get and update current user profile.
    
    GET /api/auth/profile/ - Get current user profile
    PATCH /api/auth/profile/ - Update current user profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ClientListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all clients and creating new clients.
    
    GET /api/clients/ - List all clients
    POST /api/clients/ - Create a new client
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all clients, optionally filtered by search."""
        queryset = Client.objects.all()
        
        # Optional search by client name or company name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                client_name__icontains=search
            ) | queryset.filter(
                client_company_name__icontains=search
            )
        
        return queryset.order_by('-created_at')


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific client.
    
    GET /api/clients/{id}/ - Get client details
    PUT /api/clients/{id}/ - Update client (full update)
    PATCH /api/clients/{id}/ - Update client (partial update)
    DELETE /api/clients/{id}/ - Delete client
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'client_id'


class CategoryListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all categories and creating new categories.
    
    GET /api/categories/ - List all categories
    POST /api/categories/ - Create a new category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all categories, optionally filtered by search or parent."""
        queryset = Category.objects.all()
        
        # Optional search by category name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(category_name__icontains=search)
        
        # Optional filter by parent category
        parent_id = self.request.query_params.get('parent_id', None)
        if parent_id:
            queryset = queryset.filter(parent_category_id=parent_id)
        
        # Optional filter for root categories (no parent)
        root_only = self.request.query_params.get('root_only', None)
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent_category__isnull=True)
        
        return queryset.order_by('category_name')


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific category.
    
    GET /api/categories/{id}/ - Get category details
    PUT /api/categories/{id}/ - Update category (full update)
    PATCH /api/categories/{id}/ - Update category (partial update)
    DELETE /api/categories/{id}/ - Delete category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'category_id'


class ManufacturerListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all manufacturers and creating new manufacturers.
    
    GET /api/manufacturers/ - List all manufacturers
    POST /api/manufacturers/ - Create a new manufacturer
    """
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all manufacturers, optionally filtered by search."""
        queryset = Manufacturer.objects.all()
        
        # Optional search by manufacturer name or country
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                manufacturer_name__icontains=search
            ) | queryset.filter(
                manufacturer_country__icontains=search
            )
        
        return queryset.order_by('manufacturer_name')


class ManufacturerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific manufacturer.
    
    GET /api/manufacturers/{id}/ - Get manufacturer details
    PUT /api/manufacturers/{id}/ - Update manufacturer (full update)
    PATCH /api/manufacturers/{id}/ - Update manufacturer (partial update)
    DELETE /api/manufacturers/{id}/ - Delete manufacturer
    """
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'manufacturer_id'


class EquipmentTypesListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment types and creating new equipment types.
    
    GET /api/equipment-types/ - List all equipment types
    POST /api/equipment-types/ - Create a new equipment type
    """
    queryset = EquipmentTypes.objects.all()
    serializer_class = EquipmentTypesSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment types, optionally filtered by search."""
        queryset = EquipmentTypes.objects.all()
        
        # Optional search by type name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(type_name__icontains=search)
        
        return queryset.order_by('type_name')


class EquipmentTypesDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment type.
    
    GET /api/equipment-types/{id}/ - Get equipment type details
    PUT /api/equipment-types/{id}/ - Update equipment type (full update)
    PATCH /api/equipment-types/{id}/ - Update equipment type (partial update)
    DELETE /api/equipment-types/{id}/ - Delete equipment type
    """
    queryset = EquipmentTypes.objects.all()
    serializer_class = EquipmentTypesSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'type_id'


class EquipmentDetailsListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment details and creating new equipment details.
    
    GET /api/equipment-details/ - List all equipment details
    POST /api/equipment-details/ - Create a new equipment detail
    """
    queryset = EquipmentDetails.objects.all()
    serializer_class = EquipmentDetailsSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment details, optionally filtered by search."""
        queryset = EquipmentDetails.objects.all()
        
        # Optional search by parameter name or value
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                detail_parameter_name__icontains=search
            ) | queryset.filter(
                detail_parameter_value__icontains=search
            )
        
        return queryset.order_by('detail_parameter_name')


class EquipmentDetailsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment detail.
    
    GET /api/equipment-details/{id}/ - Get equipment detail details
    PUT /api/equipment-details/{id}/ - Update equipment detail (full update)
    PATCH /api/equipment-details/{id}/ - Update equipment detail (partial update)
    DELETE /api/equipment-details/{id}/ - Delete equipment detail
    """
    queryset = EquipmentDetails.objects.all()
    serializer_class = EquipmentDetailsSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'detail_id'


class EquipmentSpecificationListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment specifications and creating new equipment specifications.
    
    GET /api/equipment-specifications/ - List all equipment specifications
    POST /api/equipment-specifications/ - Create a new equipment specification
    """
    queryset = EquipmentSpecification.objects.all()
    serializer_class = EquipmentSpecificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment specifications, optionally filtered by search."""
        queryset = EquipmentSpecification.objects.all()
        
        # Optional search by parameter name or value
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                spec_parameter_name__icontains=search
            ) | queryset.filter(
                spec_parameter_value__icontains=search
            )
        
        return queryset.order_by('spec_parameter_name')


class EquipmentSpecificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment specification.
    
    GET /api/equipment-specifications/{id}/ - Get equipment specification details
    PUT /api/equipment-specifications/{id}/ - Update equipment specification (full update)
    PATCH /api/equipment-specifications/{id}/ - Update equipment specification (partial update)
    DELETE /api/equipment-specifications/{id}/ - Delete equipment specification
    """
    queryset = EquipmentSpecification.objects.all()
    serializer_class = EquipmentSpecificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'spec_id'


class EquipmentTechProcessListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment tech processes and creating new equipment tech processes.
    
    GET /api/equipment-tech-processes/ - List all equipment tech processes
    POST /api/equipment-tech-processes/ - Create a new equipment tech process
    """
    queryset = EquipmentTechProcess.objects.all()
    serializer_class = EquipmentTechProcessSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment tech processes, optionally filtered by search."""
        queryset = EquipmentTechProcess.objects.all()
        
        # Optional search by tech name, value, or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                tech_name__icontains=search
            ) | queryset.filter(
                tech_value__icontains=search
            ) | queryset.filter(
                tech_desc__icontains=search
            )
        
        return queryset.order_by('tech_name')


class EquipmentTechProcessDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment tech process.
    
    GET /api/equipment-tech-processes/{id}/ - Get equipment tech process details
    PUT /api/equipment-tech-processes/{id}/ - Update equipment tech process (full update)
    PATCH /api/equipment-tech-processes/{id}/ - Update equipment tech process (partial update)
    DELETE /api/equipment-tech-processes/{id}/ - Delete equipment tech process
    """
    queryset = EquipmentTechProcess.objects.all()
    serializer_class = EquipmentTechProcessSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'tech_id'


class EquipmentListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment and creating new equipment.
    
    GET /api/equipment/ - List all equipment
    POST /api/equipment/ - Create a new equipment
    """
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def create(self, request, *args, **kwargs):
        """Override create to add logging and ensure equipment is saved."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Creating equipment. Request data: {request.data}")
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            logger.info(f"Serializer is valid. Validated data: {serializer.validated_data}")
            
            # Создаем оборудование
            equipment = serializer.save()
            logger.info(f"Equipment saved with ID: {equipment.equipment_id}, Name: {equipment.equipment_name}")
            
            # Проверяем в БД
            equipment_check = Equipment.objects.filter(equipment_id=equipment.equipment_id).first()
            if not equipment_check:
                logger.error(f"Equipment {equipment.equipment_id} was created but not found in DB!")
                raise Exception(f"Equipment {equipment.equipment_id} was created but not found in DB!")
            
            logger.info(f"Equipment {equipment.equipment_id} verified in DB")
            
            # Возвращаем сериализованный ответ
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error in EquipmentListView.create: {e}", exc_info=True)
            raise
    
    def get_queryset(self):
        """Return all equipment, optionally filtered by search or filters."""
        queryset = Equipment.objects.prefetch_related(
            'categories', 'manufacturers', 'equipment_types',
            'details', 'specifications', 'tech_processes'
        ).all()
        
        # Optional search by equipment name or articule
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                equipment_name__icontains=search
            ) | queryset.filter(
                equipment_articule__icontains=search
            )
        
        # Optional filter by category (many-to-many)
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(categories__category_id=category_id).distinct()
        
        # Optional filter by manufacturer (many-to-many)
        manufacturer_id = self.request.query_params.get('manufacturer_id', None)
        if manufacturer_id:
            queryset = queryset.filter(manufacturers__manufacturer_id=manufacturer_id).distinct()
        
        # Optional filter by equipment type (many-to-many)
        equipment_type_id = self.request.query_params.get('equipment_type_id', None)
        if equipment_type_id:
            queryset = queryset.filter(equipment_types__type_id=equipment_type_id).distinct()
        
        # Optional filter by published status
        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            is_published_bool = is_published.lower() == 'true'
            queryset = queryset.filter(is_published=is_published_bool)
        
        return queryset.order_by('-created_at')


class EquipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment.
    
    GET /api/equipment/{id}/ - Get equipment details
    PUT /api/equipment/{id}/ - Update equipment (full update)
    PATCH /api/equipment/{id}/ - Update equipment (partial update)
    DELETE /api/equipment/{id}/ - Delete equipment
    """
    queryset = Equipment.objects.prefetch_related(
        'categories', 'manufacturers', 'equipment_types',
        'details', 'specifications', 'tech_processes'
    ).all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'equipment_id'


class PurchasePriceListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all purchase prices and creating new purchase prices.
    
    GET /api/purchase-prices/ - List all purchase prices
    POST /api/purchase-prices/ - Create a new purchase price
    """
    queryset = PurchasePrice.objects.select_related('equipment').all()
    serializer_class = PurchasePriceSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all purchase prices, optionally filtered by search or filters."""
        queryset = PurchasePrice.objects.select_related('equipment').all()
        
        # Optional filter by equipment
        equipment_id = self.request.query_params.get('equipment_id', None)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        # Optional filter by source type
        source_type = self.request.query_params.get('source_type', None)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # Optional filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Optional filter by currency
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency=currency)
        
        return queryset.order_by('-created_at')


class PurchasePriceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific purchase price.
    
    GET /api/purchase-prices/{id}/ - Get purchase price details
    PUT /api/purchase-prices/{id}/ - Update purchase price (full update)
    PATCH /api/purchase-prices/{id}/ - Update purchase price (partial update)
    DELETE /api/purchase-prices/{id}/ - Delete purchase price
    """
    queryset = PurchasePrice.objects.select_related('equipment').all()
    serializer_class = PurchasePriceSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'price_id'


class LogisticsListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all logistics and creating new logistics.
    
    GET /api/logistics/ - List all logistics
    POST /api/logistics/ - Create a new logistics
    """
    queryset = Logistics.objects.select_related('equipment').all()
    serializer_class = LogisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all logistics, optionally filtered by search or filters."""
        queryset = Logistics.objects.select_related('equipment').all()
        
        # Optional filter by equipment
        equipment_id = self.request.query_params.get('equipment_id', None)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        # Optional filter by route type
        route_type = self.request.query_params.get('route_type', None)
        if route_type:
            queryset = queryset.filter(route_type=route_type)
        
        # Optional filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Optional filter by currency
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency=currency)
        
        return queryset.order_by('-created_at')


class LogisticsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific logistics.
    
    GET /api/logistics/{id}/ - Get logistics details
    PUT /api/logistics/{id}/ - Update logistics (full update)
    PATCH /api/logistics/{id}/ - Update logistics (partial update)
    DELETE /api/logistics/{id}/ - Delete logistics
    """
    queryset = Logistics.objects.select_related('equipment').all()
    serializer_class = LogisticsSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'logistics_id'


class EquipmentDocumentListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment documents and creating new equipment documents.
    
    GET /api/equipment-documents/ - List all equipment documents
    POST /api/equipment-documents/ - Create a new equipment document (supports file upload)
    """
    queryset = EquipmentDocument.objects.select_related('equipment').all()
    serializer_class = EquipmentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment documents, optionally filtered by search or filters."""
        queryset = EquipmentDocument.objects.select_related('equipment').all()
        
        # Optional filter by equipment
        equipment_id = self.request.query_params.get('equipment_id', None)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        # Optional filter by document type
        document_type = self.request.query_params.get('document_type', None)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        # Optional filter by is_for_client
        is_for_client = self.request.query_params.get('is_for_client', None)
        if is_for_client is not None:
            is_for_client_bool = is_for_client.lower() == 'true'
            queryset = queryset.filter(is_for_client=is_for_client_bool)
        
        # Optional filter by is_internal
        is_internal = self.request.query_params.get('is_internal', None)
        if is_internal is not None:
            is_internal_bool = is_internal.lower() == 'true'
            queryset = queryset.filter(is_internal=is_internal_bool)
        
        # Optional search by document name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(document_name__icontains=search)
        
        return queryset.order_by('-created_at')


class EquipmentDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment document.
    
    GET /api/equipment-documents/{id}/ - Get equipment document details
    PUT /api/equipment-documents/{id}/ - Update equipment document (full update)
    PATCH /api/equipment-documents/{id}/ - Update equipment document (partial update)
    DELETE /api/equipment-documents/{id}/ - Delete equipment document
    """
    queryset = EquipmentDocument.objects.select_related('equipment').all()
    serializer_class = EquipmentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'document_id'


class EquipmentLineListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment lines and creating new equipment lines.
    
    GET /api/equipment-lines/ - List all equipment lines
    POST /api/equipment-lines/ - Create a new equipment line
    """
    queryset = EquipmentLine.objects.prefetch_related('line_items__equipment').all()
    serializer_class = EquipmentLineSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment lines, optionally filtered by search."""
        queryset = EquipmentLine.objects.prefetch_related('line_items__equipment').all()
        
        # Optional search by equipment line name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(equipment_line_name__icontains=search)
        
        return queryset.order_by('equipment_line_name')


class EquipmentLineDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment line.
    
    GET /api/equipment-lines/{id}/ - Get equipment line details
    PUT /api/equipment-lines/{id}/ - Update equipment line (full update)
    PATCH /api/equipment-lines/{id}/ - Update equipment line (partial update)
    DELETE /api/equipment-lines/{id}/ - Delete equipment line
    """
    queryset = EquipmentLine.objects.prefetch_related('line_items__equipment').all()
    serializer_class = EquipmentLineSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'equipment_line_id'


class EquipmentLineItemListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment line items and creating new equipment line items.
    
    GET /api/equipment-line-items/ - List all equipment line items
    POST /api/equipment-line-items/ - Create a new equipment line item
    """
    queryset = EquipmentLineItem.objects.select_related('equipment_line', 'equipment').all()
    serializer_class = EquipmentLineItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment line items, optionally filtered."""
        queryset = EquipmentLineItem.objects.select_related('equipment_line', 'equipment').all()
        
        # Optional filter by equipment line
        equipment_line_id = self.request.query_params.get('equipment_line_id', None)
        if equipment_line_id:
            queryset = queryset.filter(equipment_line_id=equipment_line_id)
        
        # Optional filter by equipment
        equipment_id = self.request.query_params.get('equipment_id', None)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        return queryset.order_by('equipment_line_id', 'order')


class EquipmentLineItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment line item.
    
    GET /api/equipment-line-items/{equipment_line_id}/{equipment_id}/ - Get equipment line item details
    PUT /api/equipment-line-items/{equipment_line_id}/{equipment_id}/ - Update equipment line item (full update)
    PATCH /api/equipment-line-items/{equipment_line_id}/{equipment_id}/ - Update equipment line item (partial update)
    DELETE /api/equipment-line-items/{equipment_line_id}/{equipment_id}/ - Delete equipment line item
    
    Note: This view uses a composite lookup (equipment_line_id + equipment_id) based on unique_together constraint.
    """
    queryset = EquipmentLineItem.objects.select_related('equipment_line', 'equipment').all()
    serializer_class = EquipmentLineItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_object(self):
        """Get object using composite key (equipment_line_id + equipment_id)."""
        equipment_line_id = self.kwargs.get('equipment_line_id')
        equipment_id = self.kwargs.get('equipment_id')
        
        try:
            return EquipmentLineItem.objects.get(
                equipment_line_id=equipment_line_id,
                equipment_id=equipment_id
            )
        except EquipmentLineItem.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Equipment line item not found.')


class AdditionalPricesListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all additional prices and creating new additional prices.
    
    GET /api/additional-prices/ - List all additional prices
    POST /api/additional-prices/ - Create a new additional price
    """
    queryset = AdditionalPrices.objects.all()
    serializer_class = AdditionalPricesSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all additional prices, optionally filtered by search or filters."""
        queryset = AdditionalPrices.objects.all()
        
        # Optional search by parameter name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(price_parameter_name__icontains=search)
        
        # Optional filter by expense type
        expense_type = self.request.query_params.get('expense_type', None)
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)
        
        # Optional filter by value type
        value_type = self.request.query_params.get('value_type', None)
        if value_type:
            queryset = queryset.filter(value_type=value_type)
        
        return queryset.order_by('price_parameter_name')


class AdditionalPricesDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific additional price.
    
    GET /api/additional-prices/{id}/ - Get additional price details
    PUT /api/additional-prices/{id}/ - Update additional price (full update)
    PATCH /api/additional-prices/{id}/ - Update additional price (partial update)
    DELETE /api/additional-prices/{id}/ - Delete additional price
    """
    queryset = AdditionalPrices.objects.all()
    serializer_class = AdditionalPricesSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'price_id'


class EquipmentListListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all equipment lists and creating new equipment lists.
    
    GET /api/equipment-lists/ - List all equipment lists
    POST /api/equipment-lists/ - Create a new equipment list
    """
    queryset = EquipmentList.objects.prefetch_related(
        'line_items__equipment_line', 'equipment_items_relation__equipment', 'additional_price'
    ).all()
    serializer_class = EquipmentListSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment lists, optionally filtered."""
        queryset = EquipmentList.objects.prefetch_related(
            'line_items__equipment_line', 'equipment_items_relation__equipment', 'additional_price'
        ).all()
        
        # Optional filter by proposal_id
        proposal_id = self.request.query_params.get('proposal_id', None)
        if proposal_id:
            queryset = queryset.filter(proposal_id=proposal_id)
        
        # Optional filter by equipment_line (through line_items)
        equipment_line_id = self.request.query_params.get('equipment_line_id', None)
        if equipment_line_id:
            queryset = queryset.filter(line_items__equipment_line_id=equipment_line_id).distinct()
        
        # Optional filter by equipment (through equipment_items_relation)
        equipment_id = self.request.query_params.get('equipment_id', None)
        if equipment_id:
            queryset = queryset.filter(equipment_items_relation__equipment_id=equipment_id).distinct()
        
        return queryset.order_by('-created_at')


class EquipmentListDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment list.
    
    GET /api/equipment-lists/{id}/ - Get equipment list details
    PUT /api/equipment-lists/{id}/ - Update equipment list (full update)
    PATCH /api/equipment-lists/{id}/ - Update equipment list (partial update)
    DELETE /api/equipment-lists/{id}/ - Delete equipment list
    """
    queryset = EquipmentList.objects.prefetch_related(
        'line_items__equipment_line', 'equipment_items_relation__equipment', 'additional_price'
    ).all()
    serializer_class = EquipmentListSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'list_id'


class EquipmentListLineItemListView(generics.ListCreateAPIView):
    """
    Endpoint for listing and creating equipment list line items.
    
    GET /api/equipment-list-line-items/ - List all equipment list line items
    POST /api/equipment-list-line-items/ - Add an equipment line to an equipment list
    """
    queryset = EquipmentListLineItem.objects.select_related('equipment_list', 'equipment_line').all()
    serializer_class = EquipmentListLineItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment list line items, optionally filtered."""
        queryset = EquipmentListLineItem.objects.select_related('equipment_list', 'equipment_line').all()
        
        # Optional filter by equipment_list
        list_id = self.request.query_params.get('list_id', None)
        if list_id:
            queryset = queryset.filter(equipment_list_id=list_id)
        
        return queryset.order_by('equipment_list_id', 'equipment_line_id')


class EquipmentListLineItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment list line item.
    
    GET /api/equipment-list-line-items/{list_id}/{equipment_line_id}/ - Get line item details
    PUT /api/equipment-list-line-items/{list_id}/{equipment_line_id}/ - Update line item
    PATCH /api/equipment-list-line-items/{list_id}/{equipment_line_id}/ - Update line item
    DELETE /api/equipment-list-line-items/{list_id}/{equipment_line_id}/ - Delete line item
    """
    queryset = EquipmentListLineItem.objects.select_related('equipment_list', 'equipment_line').all()
    serializer_class = EquipmentListLineItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_object(self):
        """Get object using composite key (list_id + equipment_line_id)."""
        list_id = self.kwargs.get('list_id')
        equipment_line_id = self.kwargs.get('equipment_line_id')
        
        try:
            return EquipmentListLineItem.objects.get(
                equipment_list_id=list_id,
                equipment_line_id=equipment_line_id
            )
        except EquipmentListLineItem.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Equipment list line item not found.')


class EquipmentListItemListView(generics.ListCreateAPIView):
    """
    Endpoint for listing and creating equipment list items.
    
    GET /api/equipment-list-items/ - List all equipment list items
    POST /api/equipment-list-items/ - Add an equipment to an equipment list
    """
    queryset = EquipmentListItem.objects.select_related('equipment_list', 'equipment').all()
    serializer_class = EquipmentListItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all equipment list items, optionally filtered."""
        queryset = EquipmentListItem.objects.select_related('equipment_list', 'equipment').all()
        
        # Optional filter by equipment_list
        list_id = self.request.query_params.get('list_id', None)
        if list_id:
            queryset = queryset.filter(equipment_list_id=list_id)
        
        return queryset.order_by('equipment_list_id', 'equipment_id')


class EquipmentListItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific equipment list item.
    
    GET /api/equipment-list-items/{list_id}/{equipment_id}/ - Get item details
    PUT /api/equipment-list-items/{list_id}/{equipment_id}/ - Update item
    PATCH /api/equipment-list-items/{list_id}/{equipment_id}/ - Update item
    DELETE /api/equipment-list-items/{list_id}/{equipment_id}/ - Delete item
    """
    queryset = EquipmentListItem.objects.select_related('equipment_list', 'equipment').all()
    serializer_class = EquipmentListItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_object(self):
        """Get object using composite key (list_id + equipment_id)."""
        list_id = self.kwargs.get('list_id')
        equipment_id = self.kwargs.get('equipment_id')
        
        try:
            return EquipmentListItem.objects.get(
                equipment_list_id=list_id,
                equipment_id=equipment_id
            )
        except EquipmentListItem.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Equipment list item not found.')


class PaymentLogListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all payment logs and creating new payment logs.
    
    GET /api/payment-logs/ - List all payment logs
    POST /api/payment-logs/ - Create a new payment log
    """
    queryset = PaymentLog.objects.all()
    serializer_class = PaymentLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all payment logs, optionally filtered by search or filters."""
        queryset = PaymentLog.objects.all()
        
        # Optional search by payment name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(payment_name__icontains=search)
        
        # Optional filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)
        
        # Optional filter by payment date
        payment_date = self.request.query_params.get('payment_date', None)
        if payment_date:
            queryset = queryset.filter(payment_date=payment_date)
        
        return queryset.order_by('-payment_date', '-created_at')


class PaymentLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific payment log.
    
    GET /api/payment-logs/{id}/ - Get payment log details
    PUT /api/payment-logs/{id}/ - Update payment log (full update)
    PATCH /api/payment-logs/{id}/ - Update payment log (partial update)
    DELETE /api/payment-logs/{id}/ - Delete payment log
    """
    queryset = PaymentLog.objects.all()
    serializer_class = PaymentLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'payment_id'


class CommercialProposalListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all commercial proposals and creating new proposals.
    
    GET /api/commercial-proposals/ - List all commercial proposals
    POST /api/commercial-proposals/ - Create a new commercial proposal
    """
    queryset = CommercialProposal.objects.select_related(
        'client', 'user', 'parent_proposal'
    ).prefetch_related(
        'payment_logs', 'equipment_lists'
    ).all()
    serializer_class = CommercialProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def perform_create(self, serializer):
        """Create proposal and automatically calculate cost_price and total_price."""
        proposal = serializer.save()
        
        # Автоматически рассчитываем себестоимость и итоговую цену
        try:
            cost_price = CostCalculationService.calculate_proposal_cost_price(proposal)
            proposal.cost_price = cost_price
            
            # Рассчитываем итоговую цену на основе маржи
            if proposal.margin_percentage:
                proposal.total_price = CostCalculationService.calculate_proposal_total_price(
                    cost_price, proposal.margin_percentage
                )
            else:
                # Если маржа не указана, итоговая цена = себестоимость
                proposal.total_price = cost_price
            
            proposal.save()
        except Exception as e:
            # Если не удалось рассчитать, оставляем значения как есть
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to auto-calculate prices for proposal {proposal.proposal_id}: {str(e)}')
    
    def get_queryset(self):
        """Return all commercial proposals, optionally filtered by search or filters."""
        queryset = CommercialProposal.objects.select_related(
            'client', 'user', 'parent_proposal'
        ).prefetch_related(
            'payment_logs', 'equipment_lists'
        ).all()
        
        # Optional search by proposal name or outcoming number
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(proposal_name__icontains=search) |
                Q(outcoming_number__icontains=search)
            )
        
        # Optional filter by client
        client_id = self.request.query_params.get('client_id', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Optional filter by user (creator)
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Optional filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(proposal_status=status)
        
        # Optional filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(proposal_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(proposal_date__lte=date_to)
        
        # Optional filter by proposal date
        proposal_date = self.request.query_params.get('proposal_date', None)
        if proposal_date:
            queryset = queryset.filter(proposal_date=proposal_date)
        
        # Optional filter by parent proposal
        parent_proposal_id = self.request.query_params.get('parent_proposal_id', None)
        if parent_proposal_id:
            queryset = queryset.filter(parent_proposal_id=parent_proposal_id)
        
        # Optional filter by currency
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency_ticket=currency)
        
        return queryset.order_by('-proposal_date', '-created_at')


class CommercialProposalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific commercial proposal.
    
    GET /api/commercial-proposals/{id}/ - Get commercial proposal details
    PUT /api/commercial-proposals/{id}/ - Update commercial proposal (full update)
    PATCH /api/commercial-proposals/{id}/ - Update commercial proposal (partial update)
    DELETE /api/commercial-proposals/{id}/ - Delete commercial proposal
    """
    queryset = CommercialProposal.objects.select_related(
        'client', 'user', 'parent_proposal'
    ).prefetch_related(
        'payment_logs', 'equipment_lists'
    ).all()
    serializer_class = CommercialProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'proposal_id'
    
    def perform_update(self, serializer):
        """Update proposal and automatically recalculate cost_price and total_price if equipment changed."""
        proposal = serializer.save()
        
        # Автоматически пересчитываем себестоимость и итоговую цену
        # только если изменилось оборудование или маржа
        try:
            cost_price = CostCalculationService.calculate_proposal_cost_price(proposal)
            proposal.cost_price = cost_price
            
            # Рассчитываем итоговую цену на основе маржи
            if proposal.margin_percentage:
                proposal.total_price = CostCalculationService.calculate_proposal_total_price(
                    cost_price, proposal.margin_percentage
                )
            else:
                # Если маржа не указана, итоговая цена = себестоимость
                proposal.total_price = cost_price
            
            proposal.save()
        except Exception as e:
            # Если не удалось рассчитать, оставляем значения как есть
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to auto-calculate prices for proposal {proposal.proposal_id}: {str(e)}')


class CommercialProposalPDFView(generics.RetrieveAPIView):
    """
    Endpoint for generating and downloading PDF of a commercial proposal.
    
    GET /api/commercial-proposals/{id}/pdf/ - Download PDF
    """
    queryset = CommercialProposal.objects.select_related(
        'client', 'user', 'parent_proposal'
    ).prefetch_related(
        'payment_logs', 'equipment_lists__equipment_items_relation__equipment',
        'equipment_lists__line_items__equipment_line'
    ).all()
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'proposal_id'
    
    def retrieve(self, request, *args, **kwargs):
        """Generate and return PDF file."""
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from django.http import HttpResponse
        from decimal import Decimal
        import os
        
        proposal = self.get_object()
        
        # Регистрируем шрифты с поддержкой кириллицы
        # Пытаемся найти и зарегистрировать шрифт с поддержкой кириллицы
        font_name = 'Times-Roman'
        font_bold = 'Times-Bold'
        
        # Пытаемся зарегистрировать системные шрифты с поддержкой кириллицы
        try:
            # Windows шрифты
            import platform
            system = platform.system()
            
            if system == 'Windows':
                # Пытаемся использовать Arial (обычно есть в Windows)
                arial_paths = [
                    'C:/Windows/Fonts/arial.ttf',
                    'C:/Windows/Fonts/ARIAL.TTF',
                ]
                for path in arial_paths:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont('CyrillicFont', path))
                        pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', path.replace('arial.ttf', 'arialbd.ttf').replace('ARIAL.TTF', 'ARIALBD.TTF')))
                        font_name = 'CyrillicFont'
                        font_bold = 'CyrillicFont-Bold'
                        break
            elif system == 'Linux':
                # Linux шрифты
                linux_font_paths = [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    '/usr/share/fonts/TTF/DejaVuSans.ttf',
                ]
                for path in linux_font_paths:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont('CyrillicFont', path))
                        bold_path = path.replace('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf').replace('LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf')
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', bold_path))
                        font_name = 'CyrillicFont'
                        font_bold = 'CyrillicFont-Bold'
                        break
        except Exception as e:
            # Если не удалось зарегистрировать, используем стандартные шрифты
            # Times-Roman обычно лучше поддерживает кириллицу, чем Helvetica
            pass
        
        # Создаем буфер для PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=20*mm, leftMargin=20*mm,
                               topMargin=20*mm, bottomMargin=20*mm)
        
        # Контейнер для элементов PDF
        story = []
        styles = getSampleStyleSheet()
        
        # Функция для экранирования HTML и поддержки кириллицы
        def escape_html(text):
            """Экранирует HTML символы и обеспечивает правильную кодировку."""
            if text is None:
                return ""
            # Убеждаемся, что текст в Unicode
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            else:
                text = str(text)
            # Экранируем специальные символы HTML (но сохраняем кириллицу)
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            return text
        
        # Стили с использованием шрифтов, поддерживающих кириллицу
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName=font_bold
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            spaceBefore=12,
            fontName=font_bold
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName=font_name
        )
        
        # Заголовок
        story.append(Paragraph(escape_html(proposal.proposal_name), title_style))
        story.append(Spacer(1, 5*mm))
        
        # Номер КП и дата
        header_data = [
            [f"<b>Номер КП:</b> {escape_html(proposal.outcoming_number)}", 
             f"<b>Дата:</b> {proposal.proposal_date.strftime('%d.%m.%Y')}"],
        ]
        header_table = Table(header_data, colWidths=[100*mm, 70*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 5*mm))
        
        # Информация о клиенте
        story.append(Paragraph("<b>Клиент:</b>", heading_style))
        client_info = []
        if proposal.client.client_company_name:
            client_info.append(f"Компания: {escape_html(proposal.client.client_company_name)}")
        client_info.append(f"Контактное лицо: {escape_html(proposal.client.client_name)}")
        if proposal.client.client_address:
            client_info.append(f"Адрес: {escape_html(proposal.client.client_address)}")
        if proposal.client.client_phone:
            client_info.append(f"Телефон: {escape_html(proposal.client.client_phone)}")
        if proposal.client.client_email:
            client_info.append(f"Email: {escape_html(proposal.client.client_email)}")
        if proposal.client.client_bin_iin:
            client_info.append(f"БИН/ИИН: {escape_html(proposal.client.client_bin_iin)}")
        
        for info in client_info:
            story.append(Paragraph(info, normal_style))
        story.append(Spacer(1, 5*mm))
        
        # Таблица оборудования
        story.append(Paragraph("<b>Оборудование:</b>", heading_style))
        
        # Собираем все оборудование из списков
        equipment_data = [[Paragraph("№", normal_style), 
                          Paragraph("Наименование", normal_style), 
                          Paragraph("Кол-во", normal_style), 
                          Paragraph("Цена за ед.", normal_style), 
                          Paragraph("Стоимость", normal_style)]]
        equipment_num = 1
        total_equipment_cost = Decimal('0')
        
        for equipment_list in proposal.equipment_lists.all():
            # Оборудование из списка
            for item in equipment_list.equipment_items_relation.all():
                equipment = item.equipment
                quantity = item.quantity
                
                # Получаем цену закупки (активную)
                price_obj = equipment.purchase_prices.filter(is_active=True).order_by('-created_at').first()
                unit_price = Decimal('0')
                if price_obj:
                    unit_price = price_obj.price
                    # Конвертируем в валюту КП, если нужно
                    if price_obj.currency != proposal.currency_ticket:
                        # Упрощенная конвертация через курс из КП
                        if proposal.exchange_rate:
                            if price_obj.currency == 'RUB' and proposal.currency_ticket == 'KZT':
                                unit_price = unit_price * proposal.exchange_rate
                            elif price_obj.currency == 'KZT' and proposal.currency_ticket == 'RUB':
                                unit_price = unit_price / proposal.exchange_rate
                
                total_price = unit_price * quantity
                total_equipment_cost += total_price
                
                # Форматируем числа для отображения
                unit_price_str = f"{float(unit_price):,.2f}".replace(',', ' ').replace('.', ',')
                total_price_str = f"{float(total_price):,.2f}".replace(',', ' ').replace('.', ',')
                
                equipment_data.append([
                    Paragraph(str(equipment_num), normal_style),
                    Paragraph(escape_html(equipment.equipment_name), normal_style),
                    Paragraph(str(quantity), normal_style),
                    Paragraph(f"{unit_price_str} {proposal.currency_ticket}", normal_style),
                    Paragraph(f"{total_price_str} {proposal.currency_ticket}", normal_style)
                ])
                equipment_num += 1
        
        # Создаем таблицу оборудования
        equipment_table = Table(equipment_data, colWidths=[15*mm, 80*mm, 20*mm, 30*mm, 35*mm])
        equipment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Наименование выравниваем по левому краю
        ]))
        story.append(equipment_table)
        story.append(Spacer(1, 5*mm))
        
        # Итоговая стоимость
        summary_data = []
        subtotal = total_equipment_cost
        
        # Налоги и доставка из EquipmentList
        for equipment_list in proposal.equipment_lists.all():
            if equipment_list.tax_percentage:
                tax_amount = subtotal * (equipment_list.tax_percentage / Decimal('100'))
                tax_str = f"{float(tax_amount):,.2f}".replace(',', ' ').replace('.', ',')
                summary_data.append([
                    Paragraph("Налог", normal_style), 
                    Paragraph(f"{equipment_list.tax_percentage}%", normal_style), 
                    Paragraph(f"{tax_str} {proposal.currency_ticket}", normal_style)
                ])
                subtotal += tax_amount
            
            if equipment_list.delivery_percentage:
                delivery_amount = total_equipment_cost * (equipment_list.delivery_percentage / Decimal('100'))
                delivery_str = f"{float(delivery_amount):,.2f}".replace(',', ' ').replace('.', ',')
                summary_data.append([
                    Paragraph("Доставка", normal_style), 
                    Paragraph(f"{equipment_list.delivery_percentage}%", normal_style), 
                    Paragraph(f"{delivery_str} {proposal.currency_ticket}", normal_style)
                ])
                subtotal += delivery_amount
        
        # Форматируем итоговую цену
        total_price_str = f"{float(proposal.total_price):,.2f}".replace(',', ' ').replace('.', ',')
        summary_data.append([
            Paragraph("<b>Итого:</b>", heading_style), 
            Paragraph("", normal_style), 
            Paragraph(f"<b>{total_price_str} {proposal.currency_ticket}</b>", heading_style)
        ])
        
        summary_table = Table(summary_data, colWidths=[60*mm, 40*mm, 80*mm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), font_name),
            ('FONTNAME', (0, -1), (-1, -1), font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10*mm))
        
        # Условия
        story.append(Paragraph("<b>Условия:</b>", heading_style))
        
        conditions = []
        if proposal.delivery_time:
            conditions.append(f"<b>Срок доставки:</b> {escape_html(proposal.delivery_time)}")
        if proposal.warranty:
            conditions.append(f"<b>Гарантия:</b> {escape_html(proposal.warranty)}")
        if proposal.valid_until:
            conditions.append(f"<b>Срок действия КП:</b> до {proposal.valid_until.strftime('%d.%m.%Y')}")
        
        # Условия оплаты
        if proposal.payment_logs.exists():
            conditions.append("<b>Условия оплаты:</b>")
            for payment in proposal.payment_logs.all():
                payment_str = f"{float(payment.payment_value):,.2f}".replace(',', ' ').replace('.', ',')
                conditions.append(f"  • {escape_html(payment.payment_name)}: {payment_str} {proposal.currency_ticket} ({payment.payment_date.strftime('%d.%m.%Y')})")
        
        for condition in conditions:
            story.append(Paragraph(condition, normal_style))
        
        if proposal.comments:
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("<b>Примечания:</b>", heading_style))
            story.append(Paragraph(escape_html(proposal.comments), normal_style))
        
        # Генерируем PDF
        doc.build(story)
        
        # Получаем PDF из буфера
        pdf = buffer.getvalue()
        buffer.close()
        
        # Создаем HTTP ответ
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"КП_{proposal.outcoming_number.replace(' ', '_').replace('/', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class ExchangeRateListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all exchange rates and creating new exchange rates.
    
    GET /api/exchange-rates/ - List all exchange rates
    POST /api/exchange-rates/ - Create a new exchange rate
    """
    queryset = ExchangeRate.objects.select_related(
        'proposal', 'created_by'
    ).all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all exchange rates, optionally filtered by search or filters."""
        queryset = ExchangeRate.objects.select_related(
            'proposal', 'created_by'
        ).all()
        
        # Optional filter by currency_from
        currency_from = self.request.query_params.get('currency_from', None)
        if currency_from:
            queryset = queryset.filter(currency_from=currency_from)
        
        # Optional filter by currency_to
        currency_to = self.request.query_params.get('currency_to', None)
        if currency_to:
            queryset = queryset.filter(currency_to=currency_to)
        
        # Optional filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(rate_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(rate_date__lte=date_to)
        
        # Optional filter by exact date
        rate_date = self.request.query_params.get('rate_date', None)
        if rate_date:
            queryset = queryset.filter(rate_date=rate_date)
        
        # Optional filter by source
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source=source)
        
        # Optional filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Optional filter by official status
        is_official = self.request.query_params.get('is_official', None)
        if is_official is not None:
            is_official_bool = is_official.lower() == 'true'
            queryset = queryset.filter(is_official=is_official_bool)
        
        # Optional filter by proposal (custom rates for specific proposal)
        proposal_id = self.request.query_params.get('proposal_id', None)
        if proposal_id:
            queryset = queryset.filter(proposal_id=proposal_id)
        
        # Optional filter: only official rates (exclude custom proposal adjustments)
        official_only = self.request.query_params.get('official_only', None)
        if official_only and official_only.lower() == 'true':
            queryset = queryset.filter(proposal__isnull=True, is_official=True)
        
        # Optional: get latest rate for currency pair
        latest = self.request.query_params.get('latest', None)
        if latest and latest.lower() == 'true':
            if currency_from and currency_to:
                # Get the latest active rate for this currency pair
                latest_rate = ExchangeRate.objects.filter(
                    currency_from=currency_from,
                    currency_to=currency_to,
                    is_active=True,
                    proposal__isnull=True,
                    is_official=True
                ).order_by('-rate_date', '-created_at').first()
                
                if latest_rate:
                    queryset = queryset.filter(rate_id=latest_rate.rate_id)
                else:
                    queryset = queryset.none()
        
        return queryset.order_by('-rate_date', '-created_at')
    
    def perform_create(self, serializer):
        """Set created_by to current user if not provided."""
        if not serializer.validated_data.get('created_by'):
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()


class ExchangeRateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint for retrieving, updating, and deleting a specific exchange rate.
    
    GET /api/exchange-rates/{id}/ - Get exchange rate details
    PUT /api/exchange-rates/{id}/ - Update exchange rate (full update)
    PATCH /api/exchange-rates/{id}/ - Update exchange rate (partial update)
    DELETE /api/exchange-rates/{id}/ - Delete exchange rate
    """
    queryset = ExchangeRate.objects.select_related(
        'proposal', 'created_by'
    ).all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'rate_id'


class ExchangeRateGetLatestView(generics.RetrieveAPIView):
    """
    Endpoint for getting the latest exchange rate for a currency pair.
    
    GET /api/exchange-rates/latest/?currency_from=USD&currency_to=KZT&date=2026-01-09&proposal_id=1
    """
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get the latest exchange rate for the specified parameters."""
        currency_from = self.request.query_params.get('currency_from')
        currency_to = self.request.query_params.get('currency_to', 'KZT')
        date_str = self.request.query_params.get('date', None)
        proposal_id = self.request.query_params.get('proposal_id', None)
        
        if not currency_from:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'currency_from': 'This parameter is required.'})
        
        # Parse date if provided
        date = None
        if date_str:
            from datetime import datetime
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'date': 'Invalid date format. Use YYYY-MM-DD.'})
        
        # Get proposal if proposal_id provided
        proposal = None
        if proposal_id:
            try:
                proposal = CommercialProposal.objects.get(proposal_id=proposal_id)
            except CommercialProposal.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound('Commercial proposal not found.')
        
        # Use the model method to get latest rate
        rate = ExchangeRate.get_latest_rate(
            currency_from=currency_from,
            currency_to=currency_to,
            date=date,
            proposal=proposal
        )
        
        if not rate:
            from rest_framework.exceptions import NotFound
            raise NotFound(
                f'Exchange rate not found for {currency_from}/{currency_to}'
                + (f' on {date}' if date else '')
                + (f' for proposal #{proposal_id}' if proposal_id else '')
            )
        
        return rate


class CostCalculationCalculateView(generics.CreateAPIView):
    """
    Endpoint for calculating equipment cost.
    
    POST /api/cost-calculations/calculate/ - Calculate equipment cost
    """
    serializer_class = CostCalculationRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def create(self, request, *args, **kwargs):
        """Calculate equipment cost and optionally save it."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        equipment_id = data['equipment_id']
        
        # Get equipment
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Equipment not found.')
        
        # Get proposal if provided
        proposal = None
        if data.get('proposal_id'):
            try:
                proposal = CommercialProposal.objects.get(proposal_id=data['proposal_id'])
            except CommercialProposal.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound('Commercial proposal not found.')
        
        # Prepare manual overrides
        manual_overrides = data.get('manual_overrides', {})
        # Convert string values to appropriate types
        for key in ['purchase_price', 'logistics_cost', 'warehouse_cost', 'production_cost', 'additional_costs', 'exchange_rate_value']:
            if key in manual_overrides:
                try:
                    manual_overrides[key] = float(manual_overrides[key])
                except (ValueError, TypeError):
                    pass
        
        # Если proposal есть и в нем указан курс, добавляем его в manual_overrides
        # Это позволит использовать курс из КП даже если его нет в ExchangeRate
        if proposal and proposal.exchange_rate and 'exchange_rate_value' not in manual_overrides:
            # Определяем валютную пару из proposal
            # Предполагаем, что курс в КП - это курс из currency_ticket в KZT
            # Но нужно проверить, какая валюта у оборудования
            manual_overrides['exchange_rate_value'] = float(proposal.exchange_rate)
        
        # Calculate cost
        try:
            calculation_result = CostCalculationService.calculate_equipment_cost(
                equipment=equipment,
                purchase_price_id=data.get('purchase_price_id'),
                logistics_id=data.get('logistics_id'),
                additional_prices_id=data.get('additional_prices_id'),
                exchange_rate_date=data.get('exchange_rate_date'),
                proposal=proposal,
                target_currency=data.get('target_currency', 'KZT'),
                manual_overrides=manual_overrides
            )
        except ValueError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': str(e)})
        except Exception as e:
            from rest_framework.exceptions import APIException
            raise APIException(f'Calculation error: {str(e)}')
        
        # Save calculation if requested
        saved_calculation = None
        if data.get('save_calculation', False):
            try:
                saved_calculation = CostCalculationService.save_calculation(
                    equipment=equipment,
                    calculation_result=calculation_result,
                    proposal=proposal,
                    created_by=request.user,
                    is_manual_adjustment=bool(manual_overrides),
                    notes=data.get('notes')
                )
                calculation_result['calculation_id'] = saved_calculation.calculation_id
                calculation_result['calculation_version'] = saved_calculation.calculation_version
            except Exception as e:
                from rest_framework.exceptions import APIException
                raise APIException(f'Error saving calculation: {str(e)}')
        
        return Response(calculation_result, status=status.HTTP_200_OK)


class CostCalculationListView(generics.ListAPIView):
    """
    Endpoint for listing all cost calculations.
    
    GET /api/cost-calculations/ - List all cost calculations
    """
    queryset = CostCalculation.objects.select_related(
        'equipment', 'proposal', 'created_by'
    ).all()
    serializer_class = CostCalculationSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return all cost calculations, optionally filtered."""
        queryset = CostCalculation.objects.select_related(
            'equipment', 'proposal', 'created_by'
        ).all()
        
        # Filter by equipment
        equipment_id = self.request.query_params.get('equipment_id', None)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        # Filter by proposal
        proposal_id = self.request.query_params.get('proposal_id', None)
        if proposal_id:
            queryset = queryset.filter(proposal_id=proposal_id)
        
        # Filter by manual adjustments
        is_manual = self.request.query_params.get('is_manual', None)
        if is_manual is not None:
            is_manual_bool = is_manual.lower() == 'true'
            queryset = queryset.filter(is_manual_adjustment=is_manual_bool)
        
        # Get latest version only
        latest_only = self.request.query_params.get('latest_only', None)
        if latest_only and latest_only.lower() == 'true':
            # Get latest calculation for each equipment (and proposal if specified)
            if equipment_id and proposal_id:
                latest = queryset.filter(
                    equipment_id=equipment_id,
                    proposal_id=proposal_id
                ).order_by('-calculation_version').first()
                if latest:
                    queryset = queryset.filter(calculation_id=latest.calculation_id)
                else:
                    queryset = queryset.none()
            elif equipment_id:
                latest = queryset.filter(equipment_id=equipment_id).order_by('-calculation_version').first()
                if latest:
                    queryset = queryset.filter(calculation_id=latest.calculation_id)
                else:
                    queryset = queryset.none()
        
        return queryset.order_by('-created_at')


class CostCalculationDetailView(generics.RetrieveDestroyAPIView):
    """
    Endpoint for retrieving and deleting a specific cost calculation.
    
    GET /api/cost-calculations/{id}/ - Get cost calculation details
    DELETE /api/cost-calculations/{id}/ - Delete cost calculation
    """
    queryset = CostCalculation.objects.select_related(
        'equipment', 'proposal', 'created_by'
    ).all()
    serializer_class = CostCalculationSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'calculation_id'


class CostCalculationEquipmentHistoryView(generics.ListAPIView):
    """
    Endpoint for getting cost calculation history for specific equipment.
    
    GET /api/cost-calculations/equipment/{equipment_id}/history/ - Get calculation history for equipment
    """
    serializer_class = CostCalculationSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        """Return calculation history for specific equipment."""
        equipment_id = self.kwargs['equipment_id']
        proposal_id = self.request.query_params.get('proposal_id', None)
        
        queryset = CostCalculation.objects.select_related(
            'equipment', 'proposal', 'created_by'
        ).filter(equipment_id=equipment_id)
        
        if proposal_id:
            queryset = queryset.filter(proposal_id=proposal_id)
        else:
            queryset = queryset.filter(proposal__isnull=True)
        
        return queryset.order_by('-calculation_version', '-created_at')
