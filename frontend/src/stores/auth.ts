import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import Cookies from 'js-cookie'
import { authAPI, type LoginCredentials, type RegisterData, type User } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAdmin = computed(() => user.value?.user_role === 'Администратор')
  const isManager = computed(() => user.value?.user_role === 'Менеджер' || isAdmin.value)
  const isViewer = computed(() => user.value?.user_role === 'Просмотр')
  const userName = computed(() => user.value?.user_name || '')
  const userRole = computed(() => user.value?.user_role || '')

  // Actions
  async function login(credentials: LoginCredentials) {
    try {
      isLoading.value = true
      error.value = null

      const response = await authAPI.login(credentials)

      // Сохраняем токены в cookies
      Cookies.set('access_token', response.tokens.access, { expires: 1 }) // 1 день
      Cookies.set('refresh_token', response.tokens.refresh, { expires: 7 }) // 7 дней

      // Сохраняем пользователя
      user.value = response.user
      isAuthenticated.value = true

      return response
    } catch (err: any) {
      error.value = err.response?.data?.message || err.message || 'Ошибка входа'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function register(data: RegisterData) {
    try {
      isLoading.value = true
      error.value = null

      const response = await authAPI.register(data)

      return response
    } catch (err: any) {
      error.value = err.response?.data?.message || err.message || 'Ошибка регистрации'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      isLoading.value = true
      
      // Вызываем API для выхода (если нужно)
      try {
        await authAPI.logout()
      } catch (err) {
        // Игнорируем ошибки при выходе
        console.error('Logout API error:', err)
      }

      // Очищаем состояние
      user.value = null
      isAuthenticated.value = false
      error.value = null

      // Удаляем токены из cookies
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')

      // Перенаправляем на страницу логина
      router.push('/login')
    } catch (err: any) {
      error.value = err.message || 'Ошибка выхода'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchProfile() {
    try {
      isLoading.value = true
      error.value = null

      const profile = await authAPI.getProfile()
      user.value = profile
      isAuthenticated.value = true

      return profile
    } catch (err: any) {
      // Если не удалось получить профиль, возможно токен истек
      if (err.response?.status === 401) {
        await logout()
      }
      error.value = err.response?.data?.message || err.message || 'Ошибка загрузки профиля'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function checkAuth() {
    const accessToken = Cookies.get('access_token')
    const refreshToken = Cookies.get('refresh_token')

    if (!accessToken || !refreshToken) {
      isAuthenticated.value = false
      user.value = null
      return false
    }

    // Если есть токены, пытаемся загрузить профиль
    try {
      await fetchProfile()
      return true
    } catch (err) {
      // Если не удалось загрузить профиль, очищаем состояние
      isAuthenticated.value = false
      user.value = null
      return false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    error,
    // Getters
    isAdmin,
    isManager,
    isViewer,
    userName,
    userRole,
    // Actions
    login,
    register,
    logout,
    fetchProfile,
    checkAuth,
    clearError,
  }
})

