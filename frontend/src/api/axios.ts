import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import Cookies from 'js-cookie'
import router from '@/router'

// Базовый URL API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Создаем экземпляр axios
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - добавляем токен к каждому запросу
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = Cookies.get('access_token')

    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - обрабатываем ошибки и обновляем токены
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Если получили 401 и это не был запрос на обновление токена
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = Cookies.get('refresh_token')

        if (!refreshToken) {
          // Нет refresh токена - перенаправляем на логин
          throw new Error('No refresh token')
        }

        // Пытаемся обновить токен
        const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        })

        const { access } = response.data

        // Сохраняем новый access токен
        Cookies.set('access_token', access, { expires: 1 }) // 1 день

        // Обновляем заголовок и повторяем запрос
        originalRequest.headers.Authorization = `Bearer ${access}`

        return apiClient(originalRequest)
      } catch (refreshError) {
        // Не удалось обновить токен - очищаем cookies и перенаправляем на логин
        Cookies.remove('access_token')
        Cookies.remove('refresh_token')

        // Перенаправляем на страницу логина
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }

        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

