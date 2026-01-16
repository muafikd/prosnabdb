from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'proposals'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    
    # JWT token refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Client CRUD endpoints
    path('clients/', views.ClientListView.as_view(), name='client-list'),
    path('clients/<int:client_id>/', views.ClientDetailView.as_view(), name='client-detail'),
    
    # Category CRUD endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:category_id>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Manufacturer CRUD endpoints
    path('manufacturers/', views.ManufacturerListView.as_view(), name='manufacturer-list'),
    path('manufacturers/<int:manufacturer_id>/', views.ManufacturerDetailView.as_view(), name='manufacturer-detail'),
    
    # Equipment Types CRUD endpoints
    path('equipment-types/', views.EquipmentTypesListView.as_view(), name='equipment-types-list'),
    path('equipment-types/<int:type_id>/', views.EquipmentTypesDetailView.as_view(), name='equipment-types-detail'),
    
    # Equipment Details CRUD endpoints
    path('equipment-details/', views.EquipmentDetailsListView.as_view(), name='equipment-details-list'),
    path('equipment-details/<int:detail_id>/', views.EquipmentDetailsDetailView.as_view(), name='equipment-details-detail'),
    
    # Equipment Specification CRUD endpoints
    path('equipment-specifications/', views.EquipmentSpecificationListView.as_view(), name='equipment-specification-list'),
    path('equipment-specifications/<int:spec_id>/', views.EquipmentSpecificationDetailView.as_view(), name='equipment-specification-detail'),
    
    # Equipment Tech Process CRUD endpoints
    path('equipment-tech-processes/', views.EquipmentTechProcessListView.as_view(), name='equipment-tech-process-list'),
    path('equipment-tech-processes/<int:tech_id>/', views.EquipmentTechProcessDetailView.as_view(), name='equipment-tech-process-detail'),
    
    # Equipment CRUD endpoints
    path('equipment/', views.EquipmentListView.as_view(), name='equipment-list'),
    path('equipment/<int:equipment_id>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),
    
    # Purchase Price CRUD endpoints
    path('purchase-prices/', views.PurchasePriceListView.as_view(), name='purchase-price-list'),
    path('purchase-prices/<int:price_id>/', views.PurchasePriceDetailView.as_view(), name='purchase-price-detail'),
    
    # Logistics CRUD endpoints
    path('logistics/', views.LogisticsListView.as_view(), name='logistics-list'),
    path('logistics/<int:logistics_id>/', views.LogisticsDetailView.as_view(), name='logistics-detail'),
    
    # Equipment Document CRUD endpoints
    path('equipment-documents/', views.EquipmentDocumentListView.as_view(), name='equipment-document-list'),
    path('equipment-documents/<int:document_id>/', views.EquipmentDocumentDetailView.as_view(), name='equipment-document-detail'),
    
    # Equipment Line CRUD endpoints
    path('equipment-lines/', views.EquipmentLineListView.as_view(), name='equipment-line-list'),
    path('equipment-lines/<int:equipment_line_id>/', views.EquipmentLineDetailView.as_view(), name='equipment-line-detail'),
    
    # Equipment Line Item CRUD endpoints
    path('equipment-line-items/', views.EquipmentLineItemListView.as_view(), name='equipment-line-item-list'),
    path('equipment-line-items/<int:equipment_line_id>/<int:equipment_id>/', views.EquipmentLineItemDetailView.as_view(), name='equipment-line-item-detail'),
    
    # Additional Prices CRUD endpoints
    path('additional-prices/', views.AdditionalPricesListView.as_view(), name='additional-prices-list'),
    path('additional-prices/<int:price_id>/', views.AdditionalPricesDetailView.as_view(), name='additional-prices-detail'),
    
    # Equipment List CRUD endpoints
    path('equipment-lists/', views.EquipmentListListView.as_view(), name='equipment-list-list'),
    path('equipment-lists/<int:list_id>/', views.EquipmentListDetailView.as_view(), name='equipment-list-detail'),
    
    # Equipment List Line Item endpoints (for adding equipment lines to lists)
    path('equipment-list-line-items/', views.EquipmentListLineItemListView.as_view(), name='equipment-list-line-item-list'),
    path('equipment-list-line-items/<int:list_id>/<int:equipment_line_id>/', views.EquipmentListLineItemDetailView.as_view(), name='equipment-list-line-item-detail'),
    
    # Equipment List Item endpoints (for adding equipment to lists)
    path('equipment-list-items/', views.EquipmentListItemListView.as_view(), name='equipment-list-item-list'),
    path('equipment-list-items/<int:list_id>/<int:equipment_id>/', views.EquipmentListItemDetailView.as_view(), name='equipment-list-item-detail'),
    
    # Payment Log CRUD endpoints
    path('payment-logs/', views.PaymentLogListView.as_view(), name='payment-log-list'),
    path('payment-logs/<int:payment_id>/', views.PaymentLogDetailView.as_view(), name='payment-log-detail'),
    
    # Commercial Proposal CRUD endpoints
    path('commercial-proposals/', views.CommercialProposalListView.as_view(), name='commercial-proposal-list'),
    path('commercial-proposals/<int:proposal_id>/', views.CommercialProposalDetailView.as_view(), name='commercial-proposal-detail'),
    path('commercial-proposals/<int:proposal_id>/pdf/', views.CommercialProposalPDFView.as_view(), name='commercial-proposal-pdf'),
    
    # Exchange Rate CRUD endpoints
    path('exchange-rates/', views.ExchangeRateListView.as_view(), name='exchange-rate-list'),
    path('exchange-rates/latest/', views.ExchangeRateGetLatestView.as_view(), name='exchange-rate-latest'),
    path('exchange-rates/<int:rate_id>/', views.ExchangeRateDetailView.as_view(), name='exchange-rate-detail'),
    
    # Cost Calculation endpoints
    path('cost-calculations/calculate/', views.CostCalculationCalculateView.as_view(), name='cost-calculation-calculate'),
    path('cost-calculations/', views.CostCalculationListView.as_view(), name='cost-calculation-list'),
    path('cost-calculations/<int:calculation_id>/', views.CostCalculationDetailView.as_view(), name='cost-calculation-detail'),
    path('cost-calculations/equipment/<int:equipment_id>/history/', views.CostCalculationEquipmentHistoryView.as_view(), name='cost-calculation-equipment-history'),
]

