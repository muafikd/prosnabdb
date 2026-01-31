from rest_framework import status, generics, permissions, serializers, viewsets
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError
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
    ExchangeRate, CostCalculation, ProposalTemplate, SectionTemplate, SystemSettings
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer, UserAdminUpdateSerializer,
    ClientSerializer, CategorySerializer, ManufacturerSerializer,
    EquipmentTypesSerializer, EquipmentDetailsSerializer,
    EquipmentSpecificationSerializer, EquipmentTechProcessSerializer,
    EquipmentSerializer, PurchasePriceSerializer, LogisticsSerializer,
    EquipmentDocumentSerializer, EquipmentLineSerializer, EquipmentLineItemSerializer,
    AdditionalPricesSerializer, EquipmentListSerializer, EquipmentListLineItemSerializer,
    EquipmentListItemSerializer, PaymentLogSerializer, CommercialProposalSerializer,
    EquipmentListItemSerializer, PaymentLogSerializer, CommercialProposalSerializer,
    ExchangeRateSerializer, CostCalculationSerializer, CostCalculationRequestSerializer, ProposalTemplateSerializer,
    SectionTemplateSerializer
)
from .services import CostCalculationService, DataAggregatorService
from core.services.exchange_rate_service import ExchangeRateService
from .permissions import IsManagerOrAdmin, IsAdmin
from .tasks import generate_pdf_task
from celery.result import AsyncResult
import requests
from urllib.parse import urlparse


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
        
        return Response({
            'message': 'Регистрация прошла успешно. Ваша учетная запись скоро активируется вашим руководителем.',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class UserListView(generics.ListAPIView):
    """
    Admin-only endpoint to list all users.
    GET /api/users/
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        qs = User.objects.all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user_name__icontains=search) |
                Q(user_login__icontains=search) |
                Q(user_email__icontains=search)
            )
        is_active = self.request.query_params.get('is_active')
        if is_active is not None and is_active != '':
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs.order_by('-created_at')


class UserAdminUpdateView(generics.RetrieveUpdateAPIView):
    """
    Admin-only endpoint to update user's role and activation status.
    GET/PATCH /api/users/{user_id}/
    """
    queryset = User.objects.all()
    serializer_class = UserAdminUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    lookup_field = 'user_id'

    def perform_update(self, serializer):
        # Prevent admin from deactivating themselves
        instance = self.get_object()
        new_is_active = serializer.validated_data.get('is_active', instance.is_active)
        if instance.user_id == self.request.user.user_id and new_is_active is False:
            raise ValidationError({'is_active': 'Нельзя деактивировать собственного пользователя.'})
        serializer.save()


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    print("LOGIN HEADERS:", request.headers)
    print("LOGIN META:", {k: v for k, v in request.META.items() if k.startswith('HTTP_') or k.startswith('CSRF')})
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if manufacturer is used in any equipment
        if instance.equipment.exists():
            return Response(
                {"detail": "Нельзя удалить производителя, так как к нему привязано оборудование"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return super().destroy(request, *args, **kwargs)


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
            'details', 'specifications', 'tech_processes', 'photos'
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
        'details', 'specifications', 'tech_processes', 'photos'
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
    queryset = PaymentLog.objects.select_related('user').all()
    serializer_class = PaymentLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating a payment log."""
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        """Return all payment logs, optionally filtered by search or filters."""
        queryset = PaymentLog.objects.select_related('user').all()
        
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
    queryset = PaymentLog.objects.select_related('user').all()
    serializer_class = PaymentLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'payment_id'
    
    def perform_update(self, serializer):
        """Update the user to the current user when updating a payment log."""
        serializer.save(user=self.request.user)


class CommercialProposalListView(generics.ListCreateAPIView):
    """
    Endpoint for listing all commercial proposals and creating new proposals.
    
    GET /api/commercial-proposals/ - List all commercial proposals
    POST /api/commercial-proposals/ - Create a new commercial proposal
    """
    queryset = CommercialProposal.objects.select_related(
        'client', 'user', 'updated_by', 'parent_proposal'
    ).prefetch_related(
        'payment_logs', 'equipment_lists'
    ).all()
    serializer_class = CommercialProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def perform_create(self, serializer):
        """Create proposal and automatically calculate cost_price, total_price, and margin."""
        proposal = serializer.save(user=self.request.user, updated_by=self.request.user)
        
        # Автоматически рассчитываем себестоимость, итоговую цену и маржу
        try:
            cost_price = CostCalculationService.calculate_proposal_cost_price(proposal)
            proposal.cost_price = cost_price
            
            # Рассчитываем итоговую цену и маржу через DataAggregatorService
            # (использует sale_price_kzt для расчета)
            from .services import DataAggregatorService
            from .serializers import _save_prices_to_equipment_list_items
            
            service = DataAggregatorService(proposal)
            data_pkg = service.get_full_data_package()
            
            # total_price и margin_value/margin_percentage уже обновлены в get_full_data_package
            proposal.refresh_from_db()
            
            # Сохранить итоговые цены в EquipmentListItem
            if 'equipment_list' in data_pkg:
                _save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])
        except Exception as e:
            # Если не удалось рассчитать, оставляем значения как есть
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to auto-calculate prices for proposal {proposal.proposal_id}: {str(e)}')
    
    def get_queryset(self):
        """Return all commercial proposals, optionally filtered by search or filters."""
        queryset = CommercialProposal.objects.select_related(
            'client', 'user', 'updated_by', 'parent_proposal'
        ).prefetch_related(
            'payment_logs', 'equipment_lists'
        ).all()
        
        # Soft delete filtering
        include_inactive = self.request.query_params.get('include_inactive', None)
        if include_inactive and include_inactive.lower() == 'true':
            pass  # Do not filter, show all
        else:
            queryset = queryset.filter(is_active=True)
        
        # Optional search by proposal name, outcoming number, client name, or company name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(proposal_name__icontains=search) |
                Q(outcoming_number__icontains=search) |
                Q(client__client_name__icontains=search) |
                Q(client__client_company_name__icontains=search)
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
        'client', 'user', 'updated_by', 'parent_proposal'
    ).prefetch_related(
        'payment_logs', 'equipment_lists'
    ).all()
    serializer_class = CommercialProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'proposal_id'
    
    def perform_update(self, serializer):
        """Update proposal and automatically recalculate cost_price and total_price if equipment changed."""
        proposal = serializer.save(updated_by=self.request.user)
        
        # Автоматически пересчитываем себестоимость, итоговую цену и маржу
        try:
            cost_price = CostCalculationService.calculate_proposal_cost_price(proposal)
            proposal.cost_price = cost_price
            
            # Рассчитываем итоговую цену и маржу через DataAggregatorService
            # (использует sale_price_kzt для расчета)
            from .services import DataAggregatorService
            from .serializers import _save_prices_to_equipment_list_items
            
            service = DataAggregatorService(proposal)
            data_pkg = service.get_full_data_package()
            
            # total_price и margin_value/margin_percentage уже обновлены в get_full_data_package
            proposal.refresh_from_db()
            
            # Сохранить итоговые цены в EquipmentListItem
            if 'equipment_list' in data_pkg:
                _save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to auto-calculate prices for proposal {proposal.proposal_id}: {str(e)}')

    def perform_destroy(self, instance):
        """Soft delete the proposal."""
        instance.is_active = False
        instance.save()

class CommercialProposalRefreshDataPackageView(APIView):
    """
    Endpoint for refreshing data_package from proposal data.
    
    POST /api/commercial-proposals/{id}/refresh-data-package/
    """
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def _fix_json_serialization(self, obj):
        """Recursively fix JSON serialization issues in data structures."""
        from datetime import date, datetime
        from decimal import Decimal
        
        if isinstance(obj, dict):
            return {k: self._fix_json_serialization(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._fix_json_serialization(item) for item in obj]
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            # Handle model instances
            return str(obj)
        else:
            return obj
    
    def post(self, request, proposal_id):
        """Refresh data_package from proposal data and save it to proposal."""
        try:
            proposal = CommercialProposal.objects.get(proposal_id=proposal_id)
        except CommercialProposal.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            from .services import DataAggregatorService
            import json
            import traceback
            
            service = DataAggregatorService(proposal)
            data_pkg = service.get_full_data_package()
            
            # Try to serialize to JSON to catch any serialization errors early
            try:
                json.dumps(data_pkg, default=str)  # Test serialization
            except (TypeError, ValueError) as ser_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"JSON serialization error for proposal {proposal.proposal_id}: {ser_error}")
                # Try to fix common issues
                data_pkg = self._fix_json_serialization(data_pkg)
            
            # Save to proposal
            proposal.data_package = data_pkg
            proposal.save(update_fields=['data_package'])
            
            # Сохранить итоговые цены в EquipmentListItem
            if 'equipment_list' in data_pkg:
                from .serializers import _save_prices_to_equipment_list_items
                _save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])
            
            return Response({
                'message': 'Data package refreshed successfully',
                'data_package': data_pkg
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error refreshing data_package for proposal {proposal.proposal_id}: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc() if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommercialProposalCopyView(generics.CreateAPIView):
    """
    Endpoint for copying a commercial proposal.
    
    POST /api/commercial-proposals/{id}/copy/
    """
    queryset = CommercialProposal.objects.all()
    serializer_class = CommercialProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    lookup_field = 'proposal_id'
    
    def post(self, request, *args, **kwargs):
        from django.db import transaction
        
        try:
            original_proposal = self.get_object()
            
            with transaction.atomic():
                # 1. Create copy of proposal
                new_proposal = CommercialProposal.objects.get(pk=original_proposal.pk)
                new_proposal.pk = None
                new_proposal.proposal_id = None
                
                # Update fields
                new_proposal.proposal_status = 'draft'
                new_proposal.outcoming_number = f"{original_proposal.outcoming_number} (copy)"
                # Ensure uniqueness of outcoming_number
                counter = 1
                while CommercialProposal.objects.filter(outcoming_number=new_proposal.outcoming_number).exists():
                    new_proposal.outcoming_number = f"{original_proposal.outcoming_number} (copy {counter})"
                    counter += 1
                
                new_proposal.proposal_name = f"{original_proposal.proposal_name} (Копия)"
                new_proposal.created_at = None
                new_proposal.updated_at = None
                new_proposal.user = request.user
                new_proposal.updated_by = request.user
                new_proposal.save()
                
                # 2. Copy PaymentLogs
                for payment in original_proposal.payment_logs.all():
                    new_payment = PaymentLog.objects.get(pk=payment.pk)
                    new_payment.pk = None
                    new_payment.payment_id = None
                    new_payment.created_at = None
                    new_payment.updated_at = None
                    new_payment.save()
                    new_proposal.payment_logs.add(new_payment)
                
                # 3. Copy EquipmentLists and items
                for eq_list in original_proposal.equipment_lists.all():
                    new_eq_list = EquipmentList.objects.get(pk=eq_list.pk)
                    new_eq_list.pk = None
                    new_eq_list.list_id = None
                    new_eq_list.proposal = new_proposal
                    new_eq_list.created_at = None
                    new_eq_list.updated_at = None
                    new_eq_list.save()
                    
                    # Copy many-to-many additional_prices
                    new_eq_list.additional_prices.set(eq_list.additional_prices.all())
                    
                    # Copy EquipmentListLineItems
                    for item in eq_list.line_items.all():
                        new_item = EquipmentListLineItem.objects.get(pk=item.pk)
                        new_item.pk = None
                        new_item.id = None  # Django auto id
                        new_item.equipment_list = new_eq_list
                        new_item.created_at = None
                        new_item.save()

                    # Copy EquipmentListItems
                    for item in eq_list.equipment_items_relation.all():
                        new_item = EquipmentListItem.objects.get(pk=item.pk)
                        new_item.pk = None
                        new_item.id = None # Django auto id
                        new_item.equipment_list = new_eq_list
                        new_item.created_at = None
                        new_item.save()
                
                return Response(
                    CommercialProposalSerializer(new_proposal).data,
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# Removed CommercialProposalPDFView_Old
    
    def retrieve(self, request, *args, **kwargs):
        """Generate and return PDF file."""
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from django.http import HttpResponse
        from django.conf import settings
        from decimal import Decimal
        import os
        
        proposal = self.get_object()
        
        # --- fonts setup ---
        font_name = 'Arial'
        font_path = os.path.join(settings.BASE_DIR, 'proposals', 'static', 'proposals', 'fonts', 'Arial.ttf')
        
        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                # For bold, we ideally need a bold font file. If not, use standard or same.
                # Attempt to find Arial Bold if strictly needed, or just register same as Bold (hacky but works for characters)
                # Ideally:
                # pdfmetrics.registerFont(TTFont('Arial-Bold', font_path_bold))
                # Fallback: use same font for 'Arial-Bold' alias if bold not available, or standard Helvetica if ascii
                pdfmetrics.registerFont(TTFont('Arial-Bold', font_path)) # Using same font, ReportLab might simulate bold or just print normal
            else:
                # Fallback to system fonts logic or standard
                font_name = 'Helvetica' 
        except Exception as e:
            # Fallback
            font_name = 'Helvetica'

        # --- buffer setup ---
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=15*mm, 
            leftMargin=15*mm,
            topMargin=15*mm, 
            bottomMargin=15*mm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Helper: escape html
        def escape_html(text):
            if text is None: return ""
            if isinstance(text, bytes): text = text.decode('utf-8')
            else: text = str(text)
            return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Helper: format money
        def fmt_money(val, currency=''):
            s = f"{float(val):,.2f}".replace(',', ' ').replace('.', ',')
            return f"{s} {currency}".strip()

        # Styles
        style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontName=font_name, fontSize=18, alignment=TA_LEFT, spaceAfter=20, textColor=colors.HexColor('#2c3e50'))
        style_heading = ParagraphStyle('Heading', parent=styles['Heading2'], fontName=font_name, fontSize=12, textColor=colors.HexColor('#34495e'), spaceBefore=10, spaceAfter=5)
        style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=font_name, fontSize=9, leading=12)
        style_normal_right = ParagraphStyle('NormalRight', parent=style_normal, alignment=TA_RIGHT)
        style_bold = ParagraphStyle('Bold', parent=style_normal, fontName='Arial-Bold' if font_name == 'Arial' else 'Helvetica-Bold')
        style_bold_right = ParagraphStyle('BoldRight', parent=style_bold, alignment=TA_RIGHT)

        # --- Header (Logo + Info) ---
        logo_path = os.path.join(settings.BASE_DIR, 'proposals', 'static', 'proposals', 'images', 'logo.png')
        if os.path.exists(logo_path):
            # Logo on the left, Company info on the right
            im = Image(logo_path, width=50*mm, height=15*mm)
            im.hAlign = 'LEFT'
            story.append(im)
            story.append(Spacer(1, 5*mm))

        # Title Row
        story.append(Paragraph(f"Коммерческое предложение № {escape_html(proposal.outcoming_number)}", style_title))
        story.append(Paragraph(f"Дата: {proposal.proposal_date.strftime('%d.%m.%Y')}", style_normal))
        if proposal.valid_until:
             story.append(Paragraph(f"Действительно до: {proposal.valid_until.strftime('%d.%m.%Y')}", style_normal))
        
        story.append(Spacer(1, 5*mm))

        # --- Client Info ---
        story.append(Paragraph("Заказчик:", style_heading))
        client_data = []
        if proposal.client.client_company_name: client_data.append(f"Компания: {proposal.client.client_company_name}")
        client_data.append(f"Контактное лицо: {proposal.client.client_name}")
        if proposal.client.client_phone: client_data.append(f"Тел: {proposal.client.client_phone}")
        if proposal.client.client_email: client_data.append(f"Email: {proposal.client.client_email}")
        
        for line in client_data:
            story.append(Paragraph(escape_html(line), style_normal))
            
        story.append(Spacer(1, 5*mm))

        # --- Equipment Table ---
        story.append(Paragraph("Спецификация оборудования:", style_heading))
        
        # Headers
        table_data = [[
            Paragraph("№", style_bold),
            Paragraph("Наименование / Описание", style_bold),
            Paragraph("Кол-во", style_bold),
            Paragraph("Цена ед.", style_bold),
            Paragraph("Сумма", style_bold),
        ]]
        
        col_widths = [10*mm, 90*mm, 15*mm, 30*mm, 35*mm]
        
        total_equipment = Decimal('0')
        row_counter = 1
        
        # Iterate equipment
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                qty = item.quantity
                
                # Base Price
                price_obj = equipment.purchase_prices.filter(is_active=True).order_by('-created_at').first()
                unit_price = Decimal('0')
                if price_obj:
                    unit_price = price_obj.price
                    # Convert to Proposal Currency
                    if price_obj.currency != proposal.currency_ticket and proposal.exchange_rate:
                        if proposal.currency_ticket == 'KZT' and price_obj.currency != 'KZT':
                             # Assuming exchange_rate is KZT per 1 unit of Foreign Currency
                             unit_price = unit_price * proposal.exchange_rate
                        elif proposal.currency_ticket != 'KZT' and price_obj.currency == 'KZT':
                             unit_price = unit_price / proposal.exchange_rate
                        # Note: Cross-currency (e.g. RUB to USD) logic deferred, assume KZT pivot
                
                # Row Expenses (stored in JSON field `row_expenses`)
                row_expenses_sum = Decimal('0')
                expenses_desc = []
                if item.row_expenses:
                    for exp in item.row_expenses:
                        try:
                            val = Decimal(str(exp.get('value', 0)))
                            # Assume expense value is in KZT. If proposal is not KZT, convert.
                            if proposal.currency_ticket != 'KZT' and proposal.exchange_rate:
                                val = val / proposal.exchange_rate
                            row_expenses_sum += val
                            expenses_desc.append(f"{exp.get('name', 'Расход')}: {fmt_money(val, proposal.currency_ticket)}")
                        except: pass
                
                # Total for this item (Unit Price + Expenses per unit? Or Expenses are total?)
                # Usually row expenses are "per item" or "for the line". 
                # Frontend logic `calculateRowTotal`: (production_price * rate * quantity) + expenses. Matches "expenses for the line".
                
                # Base sum for line
                line_base_sum = unit_price * qty
                line_total_sum = line_base_sum + row_expenses_sum
                
                # Unit price for display (effective unit price?) -> Let's show base unit price, and separate expenses
                
                # Main Row
                table_data.append([
                    Paragraph(str(row_counter), style_normal),
                    Paragraph(escape_html(equipment.equipment_name), style_normal),
                    Paragraph(str(qty), style_normal),
                    Paragraph(fmt_money(unit_price, proposal.currency_ticket), style_normal_right),
                    Paragraph(fmt_money(line_total_sum, proposal.currency_ticket), style_normal_right),
                ])
                
                # If expenses exist, show detailed note
                if expenses_desc:
                    desc_text = "Включено: " + "; ".join(expenses_desc)
                    table_data.append([
                        "",
                        Paragraph(desc_text, ParagraphStyle('SmallNote', parent=style_normal, fontSize=8, textColor=colors.gray)),
                        "", "", ""
                    ])
                
                total_equipment += line_total_sum
                row_counter += 1

        # Table Styling
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'), # Qty, Price, Sum aligned right
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 5*mm))
        
        # --- Totals & Global Expenses ---
        summary_data = []
        
        # Subtotal
        summary_data.append([
            Paragraph("Итого оборудование:", style_bold),
            Paragraph(fmt_money(total_equipment, proposal.currency_ticket), style_bold_right)
        ])
        
        # Global Expenses (from EquipmentList.additional_prices)
        current_sum = total_equipment
        
        # Additional Services
        if proposal.additional_services:
             for svc in proposal.additional_services:
                 price = Decimal(str(svc.get('price', 0)))
                 summary_data.append([
                     Paragraph(f"{svc.get('name')}:", style_normal),
                     Paragraph(f"+ {fmt_money(price, proposal.currency_ticket)}", style_normal_right)
                 ])
                 current_sum += price
        
        seen_expenses = set() # Avoid dupes if multiple lists share same expense (though usually one list per proposal)
        
        for eq_list in proposal.equipment_lists.all():
            for ap in eq_list.additional_prices.all():
                if ap.price_id in seen_expenses: continue
                seen_expenses.add(ap.price_id)
                
                amount = Decimal('0')
                if ap.value_type == 'percentage':
                    # Percentage of current equipment sum
                    amount = total_equipment * (ap.price_parameter_value / Decimal('100'))
                elif ap.value_type == 'fixed':
                    amount = ap.price_parameter_value
                    # Convert if needed
                    if proposal.currency_ticket != 'KZT' and proposal.exchange_rate:
                         amount = amount / proposal.exchange_rate
                
                current_sum += amount
                summary_data.append([
                    Paragraph(f"{ap.price_parameter_name} ({ap.expense_type}):", style_normal),
                    Paragraph(f"+ {fmt_money(amount, proposal.currency_ticket)}", style_normal_right)
                ])

            # Tax & Delivery
            if eq_list.tax_percentage:
                 tax = current_sum * (eq_list.tax_percentage / Decimal('100'))
                 current_sum += tax
                 summary_data.append([
                     Paragraph(f"Налог ({eq_list.tax_percentage}%):", style_normal),
                     Paragraph(f"+ {fmt_money(tax, proposal.currency_ticket)}", style_normal_right)
                 ])
            
            if eq_list.delivery_percentage:
                 delivery = total_equipment * (eq_list.delivery_percentage / Decimal('100'))
                 current_sum += delivery
                 summary_data.append([
                     Paragraph(f"Доставка ({eq_list.delivery_percentage}%):", style_normal),
                     Paragraph(f"+ {fmt_money(delivery, proposal.currency_ticket)}", style_normal_right)
                 ])

        # Final Total
        summary_data.append([
            Paragraph("ИТОГО:", ParagraphStyle('TotalLabel', parent=style_title, fontSize=12)),
            Paragraph(fmt_money(proposal.total_price, proposal.currency_ticket), ParagraphStyle('TotalVal', parent=style_title, fontSize=12, alignment=TA_RIGHT))
        ])
        
        # Summary Table
        st = Table(summary_data, colWidths=[120*mm, 60*mm])
        st.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,-1), (-1,-1), 10),
        ]))
        story.append(st)
        
        story.append(Spacer(1, 10*mm))
        
        # --- Footer / Terms ---
        if proposal.delivery_time:
             story.append(Paragraph(f"<b>Срок поставки:</b> {escape_html(proposal.delivery_time)}", style_normal))
        if proposal.warranty:
             story.append(Paragraph(f"<b>Гарантия:</b> {escape_html(proposal.warranty)}", style_normal))
        if proposal.comments:
             story.append(Paragraph(f"<b>Примечание:</b> {escape_html(proposal.comments)}", style_normal))
             
        story.append(Spacer(1, 15*mm))
        
        # Signatures
        sig_data = [
            [Paragraph("__________________________<br/>Подпись", style_normal), 
             Paragraph("__________________________<br/>Дата", style_normal)]
        ]
        sig_table = Table(sig_data, colWidths=[90*mm, 90*mm])
        story.append(sig_table)
        
        doc.build(story)
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Proposal_{proposal.outcoming_number}.pdf"
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
            base_qs = ExchangeRate.objects.filter(
                is_active=True,
                proposal__isnull=True,
                is_official=True
            ).order_by('-rate_date', '-updated_at', '-created_at')

            if currency_from and currency_to:
                latest_rate = base_qs.filter(
                    currency_from=currency_from,
                    currency_to=currency_to
                ).first()
                if latest_rate:
                    queryset = queryset.filter(rate_id=latest_rate.rate_id)
                else:
                    queryset = queryset.none()
            else:
                seen = set()
                ids = []
                for r in base_qs:
                    key = (r.currency_from, r.currency_to)
                    if key in seen:
                        continue
                    seen.add(key)
                    ids.append(r.rate_id)
                queryset = queryset.filter(rate_id__in=ids)

        return queryset.order_by('-rate_date', '-updated_at', '-created_at')


class ExchangeRateSyncView(generics.GenericAPIView):
    """
    Endpoint to manually trigger exchange rate synchronization.
    
    POST /api/exchange-rates/sync/
    """
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    serializer_class = serializers.Serializer # Generic placeholder
    
    def post(self, request, *args, **kwargs):
        try:
            stats = ExchangeRateService.fetch_and_sync_rates()
            return Response({
                'message': 'Synchronization completed successfully.',
                'stats': stats
            })
        except Exception as e:
            return Response({
                'error': f'Synchronization failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExchangeRateAddView(generics.GenericAPIView):
    """
    Endpoint to add a new currency ticker.
    Checks availability in NB RK API and saves it.
    
    POST /api/exchange-rates/add/
    Body: {"currency_code": "GBP"}
    """
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    serializer_class = serializers.Serializer # Placeholder
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='currency_code', description='Currency code (e.g. GBP)', required=True, type=OpenApiTypes.STR),
        ]
    )
    def post(self, request, *args, **kwargs):
        currency_code = request.data.get('currency_code') or request.query_params.get('currency_code')
        
        if not currency_code:
            return Response({'error': 'currency_code is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        currency_code = currency_code.upper()
        
        try:
            # 1. Fetch current rates
            # We import here to avoid circular dependencies if any, though top-level should be fine
            # Re-using logic or calling service properly
            # Actually, let's just use the service but we need to fetch all, finding specific one
            
            # Using raw requests here to avoid changing service logic which filters strict list
            import requests
            import xmltodict
            from decimal import Decimal
            from django.utils import timezone
            
            date_obj = timezone.now().date()
            formatted_date = date_obj.strftime("%d.%m.%Y")
            url = f"{ExchangeRateService.RSS_URL}?fdate={formatted_date}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = xmltodict.parse(response.content)
            
            # Support both XML formats
            items = []
            if 'rss' in data and 'channel' in data['rss']:
                 items = data['rss']['channel'].get('item', [])
            elif 'rates' in data:
                 items = data['rates'].get('item', [])
            
            if not isinstance(items, list):
                items = [items]
                
            # 2. Find requested currency
            found_item = None
            for item in items:
                if item.get('title', '').strip() == currency_code:
                    found_item = item
                    break
            
            if not found_item:
                return Response({
                    'error': f'Currency {currency_code} not found in National Bank RK API for today.'
                }, status=status.HTTP_404_NOT_FOUND)
                
            # 3. Create ExchangeRate
            existing_manual = ExchangeRate.objects.filter(
                rate_date=date_obj,
                currency_from=currency_code,
                currency_to='KZT',
                source='manual'
            ).exists()
            
            if existing_manual:
                return Response({
                    'message': f'Manual rate for {currency_code} already exists for today.',
                    'status': 'skipped'
                })
            
            rate_value = Decimal(found_item.get('description', '').replace(',', '.'))
            
            obj, created = ExchangeRate.objects.update_or_create(
                rate_date=date_obj,
                currency_from=currency_code,
                currency_to='KZT',
                defaults={
                    'rate_value': rate_value,
                    'source': 'api_nb_rk',
                    'is_active': True,
                    'is_official': True
                }
            )
            
            return Response({
                'message': f'Currency {currency_code} added/updated successfully.',
                'rate': ExchangeRateSerializer(obj).data,
                'created': created
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to add currency: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
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

from rest_framework import viewsets
from rest_framework.decorators import action
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

class ProposalTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProposalTemplate.
    """
    queryset = ProposalTemplate.objects.all()
    serializer_class = ProposalTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['proposal']

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Generate PDF synchronously or asynchronously based on query param."""
        template = self.get_object()
        
        # Check if sync parameter is explicitly set (default to async for better performance)
        sync_mode = request.query_params.get('sync', 'false').lower() == 'true'
        async_mode = request.query_params.get('async', 'true').lower() == 'true'
        
        # Use async by default for better performance, sync only if explicitly requested
        if not sync_mode and async_mode:
            # Asynchronous generation (default)
            from .tasks import generate_pdf_task
            task = generate_pdf_task.delay(template.template_id)
            return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
        else:
            # Synchronous generation - return PDF directly (only if explicitly requested)
            try:
                from .services import ExportService
                from weasyprint import HTML
                from django.http import HttpResponse
                from django.conf import settings
                import io
                
                service = ExportService(template)
                html_content = service.generate_pdf_html()
                
                # Generate PDF in memory with optimizations
                pdf_buffer = io.BytesIO()
                HTML(
                    string=html_content, 
                    base_url=str(settings.BASE_DIR)
                ).write_pdf(
                    pdf_buffer,
                    optimize_images=True  # Optimize images for faster generation
                )
                pdf_buffer.seek(0)
                
                # Return PDF as response
                response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
                safe_number = str(template.proposal.outcoming_number).replace('/', '_').replace(' ', '_')
                filename = f"proposal_{safe_number}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
            except Exception as e:
                import logging
                import traceback
                logger = logging.getLogger(__name__)
                logger.error(f"PDF generation failed for template {template.template_id}: {e}")
                logger.error(traceback.format_exc())
                return Response({
                    'error': str(e),
                    'traceback': traceback.format_exc() if settings.DEBUG else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='refresh-data-package')
    def refresh_data_package(self, request, pk=None):
        """Refresh data_package from proposal data and save it to proposal."""
        template = self.get_object()
        proposal = template.proposal
        
        try:
            from .services import DataAggregatorService
            import json
            import traceback
            
            service = DataAggregatorService(proposal)
            data_pkg = service.get_full_data_package()
            
            # Try to serialize to JSON to catch any serialization errors early
            try:
                json.dumps(data_pkg, default=str)  # Test serialization
            except (TypeError, ValueError) as ser_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"JSON serialization error for proposal {proposal.proposal_id}: {ser_error}")
                # Try to fix common issues
                data_pkg = self._fix_json_serialization(data_pkg)
            
            # Save to proposal
            proposal.data_package = data_pkg
            proposal.save(update_fields=['data_package'])
            
            # Сохранить итоговые цены в EquipmentListItem
            if 'equipment_list' in data_pkg:
                from .serializers import _save_prices_to_equipment_list_items
                _save_prices_to_equipment_list_items(proposal, data_pkg['equipment_list'])
            
            return Response({
                'message': 'Data package refreshed successfully',
                'data_package': data_pkg
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error refreshing data_package for proposal {proposal.proposal_id}: {e}")
            logger.error(traceback.format_exc())
            return Response({
                'error': str(e),
                'traceback': traceback.format_exc() if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _fix_json_serialization(self, obj):
        """Recursively fix JSON serialization issues in data structures."""
        from datetime import date, datetime
        from decimal import Decimal
        
        if isinstance(obj, dict):
            return {k: self._fix_json_serialization(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._fix_json_serialization(item) for item in obj]
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            # Handle model instances
            return str(obj)
        else:
            return obj

    def _generate_equipment_details_html(self, proposal):
        """Generate HTML for equipment details parameter list."""
        html = '<div class="equipment-details">'
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                details = equipment.details.all()
                if details:
                    html += f"<h3>{equipment.equipment_name}</h3><ul>"
                    for detail in details:
                        html += f"<li><strong>{detail.detail_parameter_name}:</strong> {detail.detail_parameter_value}</li>"
                    html += "</ul>"
        html += '</div>'
        return html

    def _generate_equipment_spec_html(self, proposal):
        """Generate HTML for equipment specifications with Image Grid."""
        html = '<div class="equipment-specs">'
        service = DataAggregatorService(proposal)
        specs_data = service._get_equipment_specifications()
        
        # We need the equipment list to iterate in order and get names/images
        data_pkg = service.get_full_data_package()
        eq_list = data_pkg['equipment_list']
        
        for item in eq_list:
            eq_id = item['equipment_id']
            name = item['name']
            images = item['images']
            
            # Specs for this item
            specs = specs_data.get(eq_id, [])
            
            html += f'<div class="specs-container" style="page-break-inside: avoid;"><h3>{name}</h3>'
            
            # Tech Specs Table
            if specs:
                html += '<table><tr><th>Параметр</th><th>Значение</th></tr>'
                for spec in specs:
                    html += f"<tr><td>{spec['name']}</td><td>{spec['value']}</td></tr>"
                html += '</table>'
            
            # Images (Auto-insert after table)
            if images:
                 html += '<div class="image-grid">'
                 for img_url in images:
                     # For PDF export handled by WeasyPrint, absolute URLs or file paths are best.
                     # img_url is essentially a string from the DB (e.g. http... or just path)
                     html += f'<div class="image-item"><img src="{img_url}" style="width: 150px; height: auto;"></div>'
                 html += '</div>'
            
            html += '</div>'
            
        html += '</div>'
        return html

    def _generate_tech_process_html(self, proposal):
        """Generate HTML for tech processes."""
        html = '<div class="tech-processes">'
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                processes = equipment.tech_processes.all()
                if processes:
                    html += f"<h3>{equipment.equipment_name} - Технологический процесс</h3>"
                    for proc in processes:
                        html += f'<div class="tech-process"><h4>{proc.tech_name}</h4>'
                        if proc.tech_value:
                            html += f'<p><strong>Значение:</strong> {proc.tech_value}</p>'
                        if proc.tech_desc:
                            html += f'<p>{proc.tech_desc}</p>'
                        html += '</div>'
        html += '</div>'
        return html

    def _generate_photo_grid_html(self, proposal):
        """Generate HTML for equipment photo grid with 70mm cells."""
        from .services import DataAggregatorService
        html = '<div class="photo-grids-container">'
        service = DataAggregatorService(proposal)
        data_pkg = service.get_full_data_package()
        eq_list = data_pkg.get('equipment_list', [])
        
        for item in eq_list:
            images = item.get('images', [])
            if not images:
                continue
            
            name = item.get('name', 'Оборудование')
            html += f'''
            <table class="photo-grid-table">
                <thead>
                    <tr>
                        <th colspan="2" class="equipment-title-cell">{name}</th>
                    </tr>
                </thead>
                <tbody>
            '''
            
            # Chunk images into pairs
            for i in range(0, len(images), 2):
                row_images = images[i:i+2]
                html += '<tr>'
                for img_data in row_images:
                    img_url = img_data.get('url', '')
                    img_name = img_data.get('name', '')
                    html += f'''
                        <td class="photo-cell">
                            <div class="photo-wrapper">
                                <img src="{img_url}" class="equipment-photo">
                                {f'<div class="photo-caption">{img_name}</div>' if img_name else ''}
                            </div>
                        </td>
                    '''
                # Fill empty cell
                if len(row_images) == 1:
                    html += '<td class="photo-cell"></td>'
                html += '</tr>'
            
            html += '</tbody></table>'
        
        html += '</div>'
        return html

    def _generate_equipment_table_html(self, proposal):
        rows = ""
        
        # Use DataAggregatorService to get correct data with margin logic
        service = DataAggregatorService(proposal)
        data = service.get_full_data_package()
        equipment_list = data['equipment_list']
        
        counter = 1
        for item in equipment_list:
            unit_price = item['price_per_unit'] # calculated selling price
            line_sum = item['total_price']
            
            rows += f"""
            <tr>
                <td>{counter}</td>
                <td>{item['name']}</td>
                <td>{item['quantity']}</td>
                <td class='text-right'>{unit_price:,.2f} {proposal.currency_ticket}</td>
                <td class='text-right'>{line_sum:,.2f} {proposal.currency_ticket}</td>
            </tr>
            """
            counter += 1
            
        return f"""
        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">№</th>
                    <th>Наименование</th>
                    <th style="width: 50px;">Кол-во</th>
                    <th class='text-right'>Цена</th>
                    <th class='text-right'>Сумма</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_additional_services_html(self, proposal):
        """Generate HTML for additional services table (2 columns)."""
        rows = ""
        services = proposal.additional_services or []
        for service in services:
            price = service.get('price', 0)
            rows += f"""
            <tr>
                <td>{service.get('description', service.get('name', ''))}</td>
                <td class='text-right'>{float(price):,.2f} {proposal.currency_ticket}</td>
            </tr>
            """
        
        if not rows:
            return ""
            
        return f"""
        <table class="services-table">
            <thead>
                <tr>
                    <th>Описание</th>
                    <th class='text-right' style="width: 120px;">Стоимость</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _generate_total_price_html(self, proposal):
        return f"""
        <div class="total-section">
            <h3>Итого: {float(proposal.total_price):,.2f} {proposal.currency_ticket}</h3>
        </div>
        """

    @action(detail=True, methods=['get'], url_path='export-docx')
    def export_docx(self, request, pk=None):
        """Generate DOCX synchronously (fast) or asynchronously based on query param."""
        template = self.get_object()
        
        # Check if async parameter is set (default to sync for DOCX as it's fast)
        async_mode = request.query_params.get('async', 'false').lower() == 'true'
        
        if async_mode:
            # Asynchronous generation
            from .tasks import generate_docx_task
            task = generate_docx_task.delay(template.template_id)
            return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
        else:
            # Synchronous generation - return DOCX directly (default, fast)
            try:
                from .services import ExportService
                from django.http import HttpResponse
                from django.conf import settings
                
                service = ExportService(template)
                docx_stream = service.generate_docx()
                
                # Return DOCX as response
                response = HttpResponse(docx_stream.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                safe_number = str(template.proposal.outcoming_number).replace('/', '_').replace(' ', '_')
                filename = f"proposal_{safe_number}.docx"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
            except Exception as e:
                import logging
                import traceback
                logger = logging.getLogger(__name__)
                logger.error(f"DOCX generation failed for template {template.template_id}: {e}")
                logger.error(traceback.format_exc())
                return Response({
                    'error': str(e),
                    'traceback': traceback.format_exc() if settings.DEBUG else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _old_export_docx_logic_placeholder(self, request, pk=None):
        pass
        
        # Load base template
        template_path = os.path.join(settings.BASE_DIR, 'proposals', 'templates', 'base_proposal.docx')
        
        # If template doesn't exist, we can't proceed easily with docxtpl
        if not os.path.exists(template_path):
             return HttpResponse("Base template not found", status=404)

        doc = DocxTemplate(template_path)
        
        # Helper to process content blocks
        blocks_data = []
        if template_obj.layout_data:
            for block in template_obj.layout_data:
                title = block.get('title', '')
                content = block.get('content', '')
                
                block_context = {'title': title, 'body': content, 'type': 'text'}
                
                if '{equipment_list}' in content:
                    block_context['type'] = 'equipment_list'
                    block_context['equipment_list'] = self._get_equipment_list_data(proposal)
                
                elif '{total_price_table}' in content:
                    block_context['type'] = 'total_price'
                    block_context['total_price_data'] = self._get_total_price_data(proposal)
                    
                elif '{equipment_details}' in content:
                    block_context['type'] = 'equipment_details'
                    block_context['details'] = self._get_equipment_details_data(proposal)

                elif '{equipment_specs}' in content:
                    block_context['type'] = 'equipment_spec'
                    block_context['specs'] = self._get_equipment_spec_data(proposal, doc) 

                elif '{equipment_tech_process}' in content:
                    block_context['type'] = 'tech_process'
                    block_context['processes'] = self._get_tech_process_data(proposal)
                
                blocks_data.append(block_context)
        
        context = {
            'outcoming_number': proposal.outcoming_number,
            'client_name': proposal.client.client_name if proposal.client else '',
            'blocks': blocks_data
        }
        
        doc.render(context)
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="proposal_{proposal.outcoming_number}.docx"'
        return response

    # --- Data Helpers for DOCX ---
    def _get_equipment_list_data(self, proposal):
        items = []
        counter = 1
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                
                # Use simplified price logic matching PDF generator for consistency
                # In real world, revisit this to use shared service logic
                price_obj = equipment.purchase_prices.filter(is_active=True).order_by('-created_at').first()
                from decimal import Decimal
                unit_price = Decimal('0')
                if price_obj:
                    unit_price = price_obj.price
                    if price_obj.currency != proposal.currency_ticket and proposal.exchange_rate:
                         if proposal.currency_ticket == 'KZT' and price_obj.currency != 'KZT':
                              unit_price = unit_price * proposal.exchange_rate
                         elif proposal.currency_ticket != 'KZT' and price_obj.currency == 'KZT':
                              unit_price = unit_price / proposal.exchange_rate

                line_sum = unit_price * item.quantity
                
                items.append({
                    'index': counter,
                    'name': equipment.equipment_name,
                    'qty': item.quantity,
                    'unit': equipment.equipment_uom or 'шт',
                    'price': f"{float(unit_price):,.2f}".replace(',', ' '),
                    'total': f"{float(line_sum):,.2f}".replace(',', ' ')
                })
                counter += 1
        return items

    def _get_total_price_data(self, proposal):
        return {
            'total_price': f"{float(proposal.total_price):,.2f}".replace(',', ' '),
            'currency': proposal.currency_ticket
        }

    def _get_equipment_details_data(self, proposal):
        data = []
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                details = equipment.details.all()
                if details:
                   data.append({
                       'name': equipment.equipment_name,
                       'params': [{'name': d.detail_parameter_name, 'value': d.detail_parameter_value} for d in details]
                   })
        return data

    def _get_equipment_spec_data(self, proposal, doc_template):
        import os
        from docxtpl import InlineImage
        from docx.shared import Mm
        import requests
        import io
        from django.conf import settings

        data = []
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                specs = equipment.specifications.all()
                images = []
                # Local photos (EquipmentPhoto) first
                for photo in equipment.photos.all().order_by('sort_order', 'pk'):
                    if photo.image:
                        try:
                            path = getattr(photo.image, 'path', None) or os.path.join(settings.MEDIA_ROOT, photo.image.name)
                            with open(path, 'rb') as f:
                                img = InlineImage(doc_template, io.BytesIO(f.read()), width=Mm(50))
                                images.append(img)
                        except Exception as e:
                            print(f"Error loading local image {photo.image.name}: {e}")
                # Legacy equipment_imagelinks (list or comma string)
                imagelinks = equipment.equipment_imagelinks
                if imagelinks:
                    links = []
                    if isinstance(imagelinks, list):
                        for x in imagelinks:
                            links.append(x.get('url', x) if isinstance(x, dict) else x)
                    elif isinstance(imagelinks, str):
                        links = [link.strip() for link in imagelinks.split(',') if link.strip()]
                    for link in links:
                        if not link:
                            continue
                        try:
                            if link.startswith('http'):
                                response = requests.get(link, timeout=5)
                                if response.status_code == 200:
                                    image_stream = io.BytesIO(response.content)
                                    img = InlineImage(doc_template, image_stream, width=Mm(50))
                                    images.append(img)
                        except Exception as e:
                            print(f"Error loading image {link}: {e}")
                data.append({
                    'name': equipment.equipment_name,
                    'params': [{'name': s.spec_parameter_name, 'value': s.spec_parameter_value} for s in specs],
                    'images': images
                })
        return data

    def _get_tech_process_data(self, proposal):
        data = []
        for eq_list in proposal.equipment_lists.all():
            for item in eq_list.equipment_items_relation.all():
                equipment = item.equipment
                procs = equipment.tech_processes.all()
                if procs:
                    data.append({
                        'name': equipment.equipment_name,
                        'items': [{'title': p.tech_name, 'value': p.tech_value, 'desc': p.tech_desc} for p in procs]
                    })
        return data

class SectionTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SectionTemplate.
    """
    queryset = SectionTemplate.objects.all()
    serializer_class = SectionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

class CeleryTaskStatusView(APIView):
    """
    Generic endpoint to check Celery task status.
    GET /api/celery-task-status/{task_id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        response_data = {
            'task_id': task_id,
            'status': result.status,
        }
        if result.ready():
            response_data['result'] = result.result
        
        return Response(response_data, status=status.HTTP_200_OK)

# Removed CommercialProposalPDFView (now handled by ProposalTemplateViewSet or constructor)

class SystemSettingsLogoView(APIView):
    """
    Endpoint for getting and uploading the company logo.
    GET /api/system-settings/logo/
    POST /api/system-settings/logo/
    """
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    
    def get(self, request, *args, **kwargs):
        settings = SystemSettings.get_settings()
        logo_url = settings.company_logo.url if settings.company_logo else "/static/assets/prosnab_logo.png"
        return Response({'url': logo_url}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        logo_file = request.FILES['file']
        settings = SystemSettings.get_settings()
        
        # Standardize name as requested: media/company/logo.png
        # Note: ImageField will handle the save, but we can enforce the name if we want.
        # However, ImageField usually appends random strings if name exists.
        # The user specifically asked for media/company/logo.png
        
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        ext = os.path.splitext(logo_file.name)[1]
        filename = f"logo{ext}"
        filepath = os.path.join('company', filename)
        
        # Delete old if exists to ensure "replacement"
        if default_storage.exists(filepath):
            default_storage.delete(filepath)
            
        path = default_storage.save(filepath, ContentFile(logo_file.read()))
        settings.company_logo = path
        settings.save()
        
        return Response({'url': settings.company_logo.url}, status=status.HTTP_200_OK)


# Allowed hosts for image proxy (Google Drive, Yandex Disk) to avoid 403 when embedding
IMAGE_PROXY_ALLOWED_NETLOCS = frozenset([
    'drive.google.com',
    'www.drive.google.com',
    'lh3.googleusercontent.com',
    'lh4.googleusercontent.com',
    'lh5.googleusercontent.com',
    'lh6.googleusercontent.com',
    'disk.yandex.ru',
    'disk.yandex.com',
    'yadi.sk',
])


class ImageProxyView(APIView):
    """
    Proxy for external images (Google Drive, Yandex Disk) to avoid 403 when
    loading in <img> from our frontend (Google blocks by Referer).
    GET /api/proxy-image/?url=ENCODED_IMAGE_URL
    AllowAny so <img src> works without sending JWT (allowlist restricts hosts).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        url = request.query_params.get('url')
        if not url:
            return Response({'error': 'Missing url parameter'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return Response({'error': 'Invalid url'}, status=status.HTTP_400_BAD_REQUEST)
            if parsed.netloc.lower() not in IMAGE_PROXY_ALLOWED_NETLOCS:
                return Response({'error': 'URL host not allowed for proxy'}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({'error': 'Invalid url'}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Referer': 'https://drive.google.com/',
        }
        try:
            r = requests.get(url, headers=headers, timeout=25, stream=True)
            r.raise_for_status()
            content_type = r.headers.get('Content-Type', 'application/octet-stream')
            # Only allow image types
            if 'image/' not in content_type and content_type not in ('application/octet-stream',):
                return Response({'error': 'Not an image'}, status=status.HTTP_400_BAD_REQUEST)
            return HttpResponse(r.content, content_type=content_type)
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class DashboardStatsView(APIView):
    """
    Endpoint to get dashboard statistics.
    
    GET /api/dashboard/stats/
    Returns:
    {
        "equipment_total": int,
        "proposals_stats": [
            {"status": "draft", "label": "Черновик", "count": int},
            ...
        ],
        "active_rates": [
            {
                "currency_from": "USD",
                "rate_value": "450.00",
                "updated_at": "2026-01-21T10:30:00Z"
            },
            ...
        ]
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # 1. Equipment total count (all equipment, not just published)
        equipment_total = Equipment.objects.count()
        
        # 2. Proposals stats by status (only active proposals)
        proposals_stats = (
            CommercialProposal.objects
            .filter(is_active=True)
            .values('proposal_status')
            .annotate(count=Count('proposal_id'))
            .order_by('proposal_status')
        )
        
        # Map status codes to labels
        status_labels = {
            'draft': 'Черновик',
            'sent': 'Отправлено',
            'accepted': 'Принято',
            'rejected': 'Отклонено',
            'negotiating': 'В переговорах',
            'completed': 'Завершено',
        }
        
        proposals_stats_list = [
            {
                'status': item['proposal_status'],
                'label': status_labels.get(item['proposal_status'], item['proposal_status']),
                'count': item['count']
            }
            for item in proposals_stats
        ]
        
        # 3. Active exchange rates (latest unique rates from widget)
        # Get unique currency pairs with latest rates
        active_rates_qs = ExchangeRate.objects.filter(
            is_active=True,
            is_official=True,
            proposal__isnull=True,
            currency_to='KZT'
        ).order_by('currency_from', '-rate_date', '-updated_at', '-created_at')
        
        # Deduplicate by currency_from (keep only latest for each currency)
        seen_currencies = set()
        active_rates_list = []
        for rate in active_rates_qs:
            if rate.currency_from not in seen_currencies:
                seen_currencies.add(rate.currency_from)
                active_rates_list.append({
                    'currency_from': rate.currency_from,
                    'rate_value': str(rate.rate_value),
                    'updated_at': rate.updated_at.isoformat() if rate.updated_at else rate.created_at.isoformat()
                })
        
        return Response({
            'equipment_total': equipment_total,
            'proposals_stats': proposals_stats_list,
            'active_rates': active_rates_list
        }, status=status.HTTP_200_OK)


class DashboardActiveProposalsView(APIView):
    """
    Endpoint to get active commercial proposals with payment details for dashboard.
    
    GET /api/dashboard/active-proposals/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
    Returns:
    [
        {
            "proposal_id": int,
            "outcoming_number": str,
            "proposal_name": str,
            "client": {
                "client_id": int,
                "client_name": str,
                "client_company_name": str
            },
            "proposal_status": str,
            "total_sum": str,  # Total price in KZT
            "paid_amount": str,  # Sum of all payments in KZT
            "payment_percentage": float,  # Percentage of paid amount (0-100)
            "created_at": str
        },
        ...
    ]
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        from decimal import Decimal
        
        # Get date range from query params (default to current month)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        # If no dates provided, default to current month
        if not date_from or not date_to:
            now = timezone.now()
            # First day of current month
            date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of current month
            if now.month == 12:
                date_to = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                date_to = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Parse provided dates
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
                # Make timezone-aware
                if timezone.is_naive(date_from):
                    date_from = timezone.make_aware(date_from)
                if timezone.is_naive(date_to):
                    date_to = timezone.make_aware(date_to)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get active proposals filtered by created_at date range
        # Exclude closed/archived proposals (is_active=False or status='completed')
        queryset = CommercialProposal.objects.filter(
            is_active=True
        ).exclude(
            proposal_status='completed'
        ).filter(
            created_at__gte=date_from,
            created_at__lte=date_to
        ).select_related(
            'client'
        ).prefetch_related(
            'payment_logs'
        ).order_by('-created_at')
        
        # Status labels mapping
        status_labels = {
            'draft': 'Черновик',
            'sent': 'Отправлено',
            'accepted': 'Принято',
            'rejected': 'Отклонено',
            'negotiating': 'В переговорах',
            'completed': 'Завершено',
        }
        
        proposals_list = []
        for proposal in queryset:
            # Calculate total sum in KZT
            # If currency is not KZT, convert using exchange_rate
            total_price = Decimal(str(proposal.total_price))
            if proposal.currency_ticket != 'KZT':
                exchange_rate = Decimal(str(proposal.exchange_rate))
                total_sum_kzt = total_price * exchange_rate
            else:
                total_sum_kzt = total_price
            
            # Calculate paid amount from payment logs
            # For ManyToMany with prefetch_related, we can iterate directly
            paid_amount = Decimal('0')
            # prefetch_related loads the related objects, so we can iterate without additional query
            for payment in proposal.payment_logs.all():
                paid_amount += Decimal(str(payment.payment_value))
            
            # Calculate payment percentage
            if total_sum_kzt > 0:
                payment_percentage = float((paid_amount / total_sum_kzt) * 100)
                # Cap at 100%
                payment_percentage = min(payment_percentage, 100.0)
            else:
                payment_percentage = 0.0
            
            proposals_list.append({
                'proposal_id': proposal.proposal_id,
                'outcoming_number': proposal.outcoming_number,
                'proposal_name': proposal.proposal_name,
                'client': {
                    'client_id': proposal.client.client_id,
                    'client_name': proposal.client.client_name,
                    'client_company_name': proposal.client.client_company_name or '',
                },
                'proposal_status': proposal.proposal_status,
                'proposal_status_label': status_labels.get(proposal.proposal_status, proposal.proposal_status),
                'total_sum': str(total_sum_kzt),
                'paid_amount': str(paid_amount),
                'payment_percentage': round(payment_percentage, 2),
                'created_at': proposal.created_at.isoformat() if proposal.created_at else None,
            })
        
        return Response(proposals_list, status=status.HTTP_200_OK)
