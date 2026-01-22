import apiClient from './axios'
import type { AxiosResponse } from 'axios'

export type UserRole = 'Администратор' | 'Менеджер' | 'Просмотр'

export interface User {
  user_id: number
  user_name: string
  user_phone?: string | null
  user_email: string
  user_login: string
  user_role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserUpdateData {
  user_role?: UserRole
  is_active?: boolean
  user_name?: string
  user_phone?: string | null
}

export const usersAPI = {
  async list(params?: { search?: string; is_active?: boolean }): Promise<User[]> {
    const response: AxiosResponse<User[]> = await apiClient.get('/users/', { params })
    return Array.isArray(response.data) ? response.data : (response.data as any).results || []
  },

  async update(userId: number, data: UserUpdateData): Promise<User> {
    const response: AxiosResponse<User> = await apiClient.patch(`/users/${userId}/`, data)
    return response.data
  },
}

