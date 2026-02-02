import apiClient from './axios'
import type { AxiosResponse } from 'axios'

export interface CrmDeal {
  id: number
  bitrix_deal_id: string
  title: string
  stage_id: string
  stage_title: string | null
  bitrix_company_id: string | null
  bitrix_contact_id: string | null
  contact_name: string | null
  contact_phone: string | null
  client: {
    client_id: number
    client_name: string
    client_company_name?: string
  } | null
  commercial_proposal_ids: number[]
  bitrix_deal_url: string | null
  created_at: string
  updated_at: string
}

export interface DealsListResponse {
  count?: number
  next?: string | null
  previous?: string | null
  results: CrmDeal[]
}

export const dealsAPI = {
  async getList(): Promise<CrmDeal[]> {
    const response: AxiosResponse<CrmDeal[] | DealsListResponse> = await apiClient.get('deals/')
    const data = response.data
    if (Array.isArray(data)) return data
    if (data && typeof data === 'object' && 'results' in data) return (data as DealsListResponse).results
    return []
  },

  async getById(id: number): Promise<CrmDeal> {
    const response: AxiosResponse<CrmDeal> = await apiClient.get(`deals/${id}/`)
    return response.data
  },
}
