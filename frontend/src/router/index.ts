import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false, requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { requiresAuth: false, requiresGuest: true },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    // Защищенные маршруты для менеджеров и администраторов
    {
      path: '/equipment',
      name: 'equipment',
      component: () => import('../views/EquipmentView.vue'),
      meta: { requiresAuth: true, requiresManager: true },
    },
    {
      path: '/clients',
      name: 'clients',
      component: () => import('../views/ClientsView.vue'),
      meta: { requiresAuth: true, requiresManager: true },
    },
    {
      path: '/proposals',
      name: 'proposals',
      component: () => import('../views/ProposalsView.vue'),
      meta: { requiresAuth: true, requiresManager: true },
    },
    {
      path: '/deals',
      name: 'deals',
      component: () => import('../views/DealsView.vue'),
      meta: { requiresAuth: true, requiresManager: true },
    },
    {
      path: '/manufacturers',
      name: 'manufacturers',
      component: () => import('../views/ManufacturerListView.vue'),
      meta: { requiresAuth: true, requiresManager: true },
    },
    {
      path: '/proposal-constructor',
      name: 'proposal-constructor',
      component: () => import('../views/ProposalConstructorView.vue'),
      meta: { requiresAuth: true, requiresManager: true },
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UsersView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    // 404 страница
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue'),
    },
  ],
})

// Navigation guards
router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next) => {
  const authStore = useAuthStore()

  // Проверяем аутентификацию при первом заходе
  if (!authStore.isAuthenticated) {
    const hasAuth = await authStore.checkAuth()
    if (!hasAuth && to.meta.requiresAuth) {
      next({ name: 'login', query: { redirect: to.fullPath } })
      return
    }
  }

  // Если пользователь уже авторизован и пытается зайти на страницы логина/регистрации
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'home' })
    return
  }

  // Проверка прав доступа для менеджеров/администраторов
  if (to.meta.requiresManager && !authStore.isManager) {
    next({ name: 'home' })
    return
  }

  // Проверка прав доступа только для администраторов
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'home' })
    return
  }

  next()
})

export default router
