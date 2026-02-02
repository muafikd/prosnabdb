import apiClient from './axios'
import type { AxiosResponse } from 'axios'

export interface SystemSettingsResponse {
  bitrix_webhook_url: string
}

export interface BitrixCheckResponse {
  ok: boolean
  result?: unknown
  error?: string
}

export interface BitrixSearchResponse {
  results: BitrixCompanyItem[]
  error?: string
}

export interface BitrixCompanyItem {
  ID: string | number
  TITLE?: string
  PHONE?: unknown
  EMAIL?: unknown
  ADDRESS?: unknown
  ADDRESS_LEGAL?: unknown
  UF_CRM_LEGALENTITY_INN?: string
  UF_CRM_1657870237252?: string
  COMPANY_TITLE?: string
}

export interface BitrixImportResponse {
  client_id: number
  error?: string
}

export interface BitrixSelectDealResponse {
  deal_id: number
  client_id: number | null
  deal_title: string
  error?: string
}

export const bitrixAPI = {
  async getSystemSettings(): Promise<SystemSettingsResponse> {
    const response: AxiosResponse<SystemSettingsResponse> = await apiClient.get('/system-settings/')
    return response.data
  },

  async updateSystemSettings(data: { bitrix_webhook_url: string }): Promise<SystemSettingsResponse> {
    const response: AxiosResponse<SystemSettingsResponse> = await apiClient.patch('/system-settings/', data)
    return response.data
  },

  async checkConnection(bitrix_webhook_url?: string): Promise<BitrixCheckResponse> {
    const response: AxiosResponse<BitrixCheckResponse> = await apiClient.post('/bitrix/check/', {
      bitrix_webhook_url: bitrix_webhook_url || undefined,
    })
    return response.data
  },

  async search(type: 'name' | 'contact' | 'requisite' | 'deal', q: string): Promise<BitrixSearchResponse> {
    const response: AxiosResponse<BitrixSearchResponse> = await apiClient.get('/bitrix/search/', {
      params: { type, q },
    })
    return response.data
  },

  async importClient(bitrix_id: number): Promise<BitrixImportResponse> {
    const response: AxiosResponse<BitrixImportResponse> = await apiClient.post('/bitrix/import-client/', {
      bitrix_id,
    })
    return response.data
  },

  /** Импорт клиента из компании сделки (по bitrix_deal_id). */
  async importClientFromDeal(bitrix_deal_id: number): Promise<BitrixImportResponse> {
    const response: AxiosResponse<BitrixImportResponse> = await apiClient.post('/bitrix/import-client/', {
      bitrix_deal_id,
    })
    return response.data
  },

  /** Выбор сделки: сохранить/обновить CrmDeal, при наличии компании — импорт в clients. Возвращает deal_id, client_id (или null), deal_title. */
  async selectDeal(bitrix_deal_id: number): Promise<BitrixSelectDealResponse> {
    const response: AxiosResponse<BitrixSelectDealResponse> = await apiClient.post('/bitrix/select-deal/', {
      bitrix_deal_id,
    })
    return response.data
  },
}
