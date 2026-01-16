import apiClient from './axios'
import type { AxiosResponse } from 'axios'

// Типы для аутентификации
export interface LoginCredentials {
  user_login: string
  password: string
}

export interface RegisterData {
  user_login: string
  password: string
  password_confirm: string
  user_name: string
  user_email: string
  user_phone?: string
  role?: string
}

export interface User {
  user_id: number
  user_login: string
  user_name: string
  user_email: string
  user_phone?: string
  user_role: string  // API возвращает user_role, а не role
  is_active: boolean
  is_staff?: boolean
  is_superuser?: boolean
  date_joined?: string
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  message: string
  user: User
  tokens: {
    access: string
    refresh: string
  }
}

export interface TokenRefreshResponse {
  access: string
}

// API функции для аутентификации
export const authAPI = {
  // Логин
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/login/', credentials)
    return response.data
  },

  // Регистрация
  async register(data: RegisterData): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/register/', data)
    return response.data
  },

  // Выход
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout/')
  },

  // Получить профиль пользователя
  async getProfile(): Promise<User> {
    const response: AxiosResponse<User> = await apiClient.get('/auth/profile/')
    return response.data
  },

  // Обновить токен
  async refreshToken(refreshToken: string): Promise<TokenRefreshResponse> {
    const response: AxiosResponse<TokenRefreshResponse> = await apiClient.post('/auth/token/refresh/', {
      refresh: refreshToken,
    })
    return response.data
  },
}

