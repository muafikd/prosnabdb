import apiClient from './axios'

export interface ProposalHeaderTemplate {
  id: number
  name: string
  logo: string | null
  logo_url: string | null
  header_kz_info: string
  header_ru_info: string
  created_by: number | null
  created_by_name: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export const proposalHeadersAPI = {
  async list(): Promise<ProposalHeaderTemplate[]> {
    const res = await apiClient.get('/proposal-headers/')
    return res.data
  },

  async create(formData: FormData): Promise<ProposalHeaderTemplate> {
    const res = await apiClient.post('/proposal-headers/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  async update(id: number, formData: FormData): Promise<ProposalHeaderTemplate> {
    const res = await apiClient.put(`/proposal-headers/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/proposal-headers/${id}/`)
  },

  async setDefault(id: number): Promise<void> {
    await apiClient.post(`/proposal-headers/${id}/set-default/`)
  },

  async getMyDefault(): Promise<ProposalHeaderTemplate | null> {
    const res = await apiClient.get('/proposal-headers/my-default/')
    return res.data
  }
}
