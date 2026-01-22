import apiClient from './axios'
import type { AxiosResponse } from 'axios'

// Типы для коммерческих предложений
export interface CommercialProposal {
  proposal_id: number
  proposal_name: string
  outcoming_number: string
  client: {
    client_id: number
    client_name: string
    client_company_name?: string
  }
  user?: {
    user_id: number
    user_name: string
  }
  updated_by?: {
    user_id: number
    user_name: string
  }
  currency_ticket: string
  exchange_rate: string
  exchange_rate_date?: string
  total_price: string
  cost_price?: string
  margin_percentage?: string
  margin_value?: string
  proposal_date: string
  valid_until?: string
  delivery_time?: string
  warranty?: string
  proposal_status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'negotiating' | 'completed'
  proposal_version: number
  parent_proposal?: {
    proposal_id: number
    proposal_name: string
    outcoming_number: string
    proposal_status: string
  }
  comments?: string
  bitrix_lead_link?: string
  payment_logs?: PaymentLog[]
  additional_services?: {
    name: string;
    price: number;
    description: string;
  }[]
  equipment_lists?: EquipmentList[]
  created_at: string
  updated_at: string
}

export interface CommercialProposalCreateData {
  proposal_id?: number
  proposal_name: string
  outcoming_number: string
  client_id: number
  user_id?: number
  currency_ticket: string
  exchange_rate: string
  exchange_rate_date?: string
  total_price: string
  cost_price?: string
  margin_percentage?: string
  margin_value?: string
  proposal_date: string
  valid_until?: string
  delivery_time?: string
  warranty?: string
  proposal_status?: 'draft' | 'sent' | 'accepted' | 'rejected' | 'negotiating' | 'completed'
  proposal_version: number
  parent_proposal_id?: number
  comments?: string
  bitrix_lead_link?: string
  internal_exchange_rates?: any[] // Should define specific type ideally
  payment_log_ids?: number[]
  additional_price_ids?: number[]
  additional_services?: {
    name: string;
    price: number;
    description: string;
  }[]
  equipment_items?: {
    equipment_id: number;
    quantity: number;
    row_expenses?: any[]; // Using any[] for now or define stricter type if needed
  }[]
  equipment_list?: {
    tax_percentage?: number;
    tax_price?: number;
    delivery_percentage?: number;
    delivery_price?: number;
  }
}

export interface CommercialProposalUpdateData extends Partial<CommercialProposalCreateData> { }

export interface PaymentLog {
  payment_id: number
  payment_name: string
  payment_value: string
  payment_date: string
  comments?: string
  user?: {
    user_id: number
    user_name: string
  }
  user_name?: string
  created_at: string
  updated_at: string
}

export interface PaymentLogCreateData {
  payment_name: string
  payment_value: string
  payment_date: string
}

export interface EquipmentList {
  list_id: number
  proposal?: number
  line_items?: any[]
  equipment_items_data?: EquipmentListItem[]
  tax_percentage?: string
  tax_price?: string
  delivery_percentage?: string
  delivery_price?: string
  additional_price?: number
  additional_prices?: number[] | AdditionalPrice[]
  created_at: string
  updated_at: string
}

export interface EquipmentListItem {
  equipment_list: number
  equipment: number
  equipment_name: string
  quantity: number
  row_expenses?: any[]
  created_at: string
}

export interface CostCalculation {
  calculation_id: number
  equipment: number
  equipment_name?: string
  proposal?: number
  proposal_name?: string
  version: number
  is_manual_override: boolean
  total_cost_kzt: string
  total_cost_base_currency?: string
  calculation_details?: any
  created_at: string
  updated_at: string
}

export interface CostCalculationRequest {
  equipment_id: number
  purchase_price_id?: number
  logistics_id?: number
  additional_prices_id?: number
  exchange_rate_date?: string
  proposal_id?: number
  target_currency?: string
  save_calculation?: boolean
  manual_overrides?: Record<string, any>
}

export type CommercialProposalResponse = CommercialProposal[] | {
  count: number
  next: string | null
  previous: string | null
  results: CommercialProposal[]
}

// API функции для коммерческих предложений
export const proposalsAPI = {
  // Получить список КП
  async getProposals(params?: {
    search?: string
    client_id?: number
    user_id?: number
    proposal_status?: string
    page?: number
  }): Promise<CommercialProposalResponse> {
    const response: AxiosResponse<CommercialProposalResponse> = await apiClient.get('/commercial-proposals/', { params })
    return response.data
  },

  // Получить КП по ID
  async getProposalById(proposalId: number): Promise<CommercialProposal> {
    const response: AxiosResponse<CommercialProposal> = await apiClient.get(`/commercial-proposals/${proposalId}/`)
    return response.data
  },

  // Создать КП
  async createProposal(data: CommercialProposalCreateData): Promise<CommercialProposal> {
    const response: AxiosResponse<CommercialProposal> = await apiClient.post('/commercial-proposals/', data)
    return response.data
  },

  // Обновить КП
  async updateProposal(proposalId: number, data: CommercialProposalUpdateData): Promise<CommercialProposal> {
    const response: AxiosResponse<CommercialProposal> = await apiClient.patch(`/commercial-proposals/${proposalId}/`, data)
    return response.data
  },

  // Удалить КП
  async deleteProposal(proposalId: number): Promise<void> {
    await apiClient.delete(`/commercial-proposals/${proposalId}/`)
  },

  // Initiate PDF Generation
  async initiatePDFGeneration(proposalId: number): Promise<{ task_id: string }> {
    const response = await apiClient.get(`/commercial-proposals/${proposalId}/pdf/`)
    return response.data
  },

  // Check PDF Status
  async checkPDFStatus(taskId: string): Promise<{ status: string; url?: string; error?: string }> {
    const response = await apiClient.get(`/commercial-proposals/pdf-status/${taskId}/`)
    return response.data
  },

  // Legacy Download (now initiates async, might break if not handled)
  // async downloadPDF(proposalId: number): Promise<Blob> { ... }


  // Копировать КП
  async copyProposal(proposalId: number): Promise<CommercialProposal> {
    const response: AxiosResponse<CommercialProposal> = await apiClient.post(`/commercial-proposals/${proposalId}/copy/`)
    return response.data
  },
}

// API функции для платежей
export const paymentLogsAPI = {
  async getPaymentLogs(params?: { search?: string; date_from?: string; date_to?: string }): Promise<PaymentLog[]> {
    const response: AxiosResponse<PaymentLog[]> = await apiClient.get('/payment-logs/', { params })
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },

  async createPaymentLog(data: PaymentLogCreateData): Promise<PaymentLog> {
    const response: AxiosResponse<PaymentLog> = await apiClient.post('/payment-logs/', data)
    return response.data
  },

  async updatePaymentLog(paymentId: number, data: Partial<PaymentLogCreateData>): Promise<PaymentLog> {
    const response: AxiosResponse<PaymentLog> = await apiClient.patch(`/payment-logs/${paymentId}/`, data)
    return response.data
  },

  async deletePaymentLog(paymentId: number): Promise<void> {
    await apiClient.delete(`/payment-logs/${paymentId}/`)
  },
}

// API функции для расчета себестоимости
export const costCalculationAPI = {
  async calculateCost(data: CostCalculationRequest): Promise<CostCalculation | any> {
    // Удаляем undefined значения перед отправкой
    const cleanData: any = {}
    for (const [key, value] of Object.entries(data)) {
      if (value !== undefined && value !== null) {
        cleanData[key] = value
      }
    }
    const response: AxiosResponse = await apiClient.post('/cost-calculations/calculate/', cleanData)
    return response.data
  },

  async getCalculations(params?: { equipment?: number; proposal?: number }): Promise<CostCalculation[]> {
    const response: AxiosResponse<CostCalculation[]> = await apiClient.get('/cost-calculations/', { params })
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },

  async getEquipmentHistory(equipmentId: number): Promise<CostCalculation[]> {
    const response: AxiosResponse<CostCalculation[]> = await apiClient.get(`/cost-calculations/equipment/${equipmentId}/history/`)
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },
}

// API функции для списков оборудования в КП
export const equipmentListsAPI = {
  async getEquipmentLists(params?: { proposal_id?: number }): Promise<EquipmentList[]> {
    const response: AxiosResponse<EquipmentList[]> = await apiClient.get('/equipment-lists/', { params })
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },

  async createEquipmentList(data: Partial<EquipmentList>): Promise<EquipmentList> {
    const response: AxiosResponse<EquipmentList> = await apiClient.post('/equipment-lists/', data)
    return response.data
  },

  async updateEquipmentList(listId: number, data: Partial<EquipmentList>): Promise<EquipmentList> {
    const response: AxiosResponse<EquipmentList> = await apiClient.patch(`/equipment-lists/${listId}/`, data)
    return response.data
  },

  async deleteEquipmentList(listId: number): Promise<void> {
    await apiClient.delete(`/equipment-lists/${listId}/`)
  },
}

// API функции для элементов списка оборудования
export const equipmentListItemsAPI = {
  async addEquipmentToList(listId: number, equipmentId: number, quantity: number, row_expenses: any[] = []): Promise<EquipmentListItem> {
    const response: AxiosResponse<EquipmentListItem> = await apiClient.post('/equipment-list-items/', {
      equipment_list: listId,
      equipment: equipmentId,
      quantity,
      row_expenses,
    })
    return response.data
  },

  async updateEquipmentListItem(listId: number, equipmentId: number, quantity: number, row_expenses?: any[]): Promise<EquipmentListItem> {
    const data: any = { quantity }
    if (row_expenses) {
      data.row_expenses = row_expenses
    }
    const response: AxiosResponse<EquipmentListItem> = await apiClient.patch(
      `/equipment-list-items/${listId}/${equipmentId}/`,
      data
    )
    return response.data
  },

  async removeEquipmentFromList(listId: number, equipmentId: number): Promise<void> {
    await apiClient.delete(`/equipment-list-items/${listId}/${equipmentId}/`)
  },
}

// Типы для AdditionalPrices
export interface AdditionalPrice {
  price_id: number
  price_parameter_name: string
  expense_type: 'packaging' | 'labor' | 'depreciation' | 'service' | 'warehouse' | 'other'
  value_type: 'percentage' | 'fixed' | 'coefficient'
  price_parameter_value: string
  created_at: string
  updated_at: string
}

// API функции для AdditionalPrices
export const additionalPricesAPI = {
  async getAdditionalPrices(params?: {
    search?: string
    expense_type?: string
    value_type?: string
  }): Promise<AdditionalPrice[]> {
    const response: AxiosResponse<AdditionalPrice[] | { results: AdditionalPrice[] }> = await apiClient.get('/additional-prices/', { params })
    // Обрабатываем как массив или объект с results
    if (Array.isArray(response.data)) {
      return response.data
    } else if (response.data && typeof response.data === 'object' && 'results' in response.data) {
      return (response.data as { results: AdditionalPrice[] }).results
    }
    return []
  },

  async getAdditionalPrice(priceId: number): Promise<AdditionalPrice> {
    const response: AxiosResponse<AdditionalPrice> = await apiClient.get(`/additional-prices/${priceId}/`)
    return response.data
  },

  async createAdditionalPrice(data: {
    price_parameter_name: string
    expense_type: string
    value_type: string
    price_parameter_value: string
  }): Promise<AdditionalPrice> {
    const response: AxiosResponse<AdditionalPrice> = await apiClient.post('/additional-prices/', data)
    return response.data
  },

  async updateAdditionalPrice(priceId: number, data: Partial<AdditionalPrice>): Promise<AdditionalPrice> {
    const response: AxiosResponse<AdditionalPrice> = await apiClient.patch(`/additional-prices/${priceId}/`, data)
    return response.data
  },

  async deleteAdditionalPrice(priceId: number): Promise<void> {
    await apiClient.delete(`/additional-prices/${priceId}/`)
  },
}

