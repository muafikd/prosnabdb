import apiClient from './axios'
import type { AxiosResponse } from 'axios'

export interface ProposalStat {
  status: string
  label: string
  count: number
}

export interface ActiveRate {
  currency_from: string
  rate_value: string
  updated_at: string
}

export interface DashboardStats {
  equipment_total: number
  proposals_stats: ProposalStat[]
  active_rates: ActiveRate[]
}

export interface ActiveProposal {
  proposal_id: number
  outcoming_number: string
  proposal_name: string
  client: {
    client_id: number
    client_name: string
    client_company_name: string
  }
  proposal_status: string
  proposal_status_label: string
  total_sum: string
  paid_amount: string
  payment_percentage: number
  created_at: string | null
}

export const dashboardAPI = {
  async getStats(): Promise<DashboardStats> {
    const response: AxiosResponse<DashboardStats> = await apiClient.get('/dashboard/stats/')
    return response.data
  },
  async getActiveProposals(dateFrom?: string, dateTo?: string): Promise<ActiveProposal[]> {
    const params: Record<string, string> = {}
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    const response: AxiosResponse<ActiveProposal[]> = await apiClient.get('/dashboard/active-proposals/', { params })
    return response.data
  },
}
