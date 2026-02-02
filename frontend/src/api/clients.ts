import apiClient from './axios'
import type { AxiosResponse } from 'axios'

// Типы для клиентов
export interface Client {
  client_id: number
  client_name: string
  client_phone?: string
  client_email?: string
  client_company_name?: string
  client_type?: string
  client_bin_iin?: string
  client_address?: string
  client_bik?: string
  client_iik?: string
  client_bankname?: string
  bitrix_id?: number | null
  created_at: string
  updated_at: string
}

export interface ClientCreateData {
  client_name: string
  client_phone?: string
  client_email?: string
  client_company_name?: string
  client_type?: string
  client_bin_iin?: string
  client_address?: string
  client_bik?: string
  client_iik?: string
  client_bankname?: string
}

export interface ClientUpdateData extends Partial<ClientCreateData> {}

export interface ClientsListResponse {
  count?: number
  next?: string | null
  previous?: string | null
  results?: Client[]
}

// API может возвращать либо пагинированный ответ, либо массив
export type ClientsResponse = ClientsListResponse | Client[]

// API функции для работы с клиентами
export const clientsAPI = {
  // Получить список клиентов
  async getClients(params?: { search?: string; page?: number }): Promise<ClientsResponse> {
    const response: AxiosResponse<ClientsResponse> = await apiClient.get('/clients/', { params })
    return response.data
  },

  // Получить клиента по ID
  async getClient(clientId: number): Promise<Client> {
    const response: AxiosResponse<Client> = await apiClient.get(`/clients/${clientId}/`)
    return response.data
  },

  // Создать клиента
  async createClient(data: ClientCreateData): Promise<Client> {
    const response: AxiosResponse<Client> = await apiClient.post('/clients/', data)
    return response.data
  },

  // Обновить клиента
  async updateClient(clientId: number, data: ClientUpdateData): Promise<Client> {
    const response: AxiosResponse<Client> = await apiClient.patch(`/clients/${clientId}/`, data)
    return response.data
  },

  // Удалить клиента
  async deleteClient(clientId: number): Promise<void> {
    await apiClient.delete(`/clients/${clientId}/`)
  },
}

