<template>
  <div id="app">
    <el-container v-if="authStore.isAuthenticated" class="app-container">
      <!-- Sidebar Navigation -->
      <el-aside 
        class="app-aside" 
        :width="isCollapse ? '64px' : '250px'"
        :class="{ 'is-collapse': isCollapse }"
      >
        <div class="logo">
          <h2 v-if="!isCollapse">Система КП</h2>
          <h2 v-else>КП</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="vertical"
          router
          class="sidebar-menu"
          :collapse="isCollapse"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <template #title>
              <span>Главная</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/dashboard" v-if="authStore.isAuthenticated">
            <el-icon><DataBoard /></el-icon>
            <template #title>
              <span>Dashboard</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/equipment" v-if="authStore.isManager">
            <el-icon><Box /></el-icon>
            <template #title>
              <span>Оборудование</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/clients" v-if="authStore.isManager">
            <el-icon><User /></el-icon>
            <template #title>
              <span>Клиенты</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/manufacturers" v-if="authStore.isManager">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>
              <span>Производители</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/proposals" v-if="authStore.isManager">
            <el-icon><Document /></el-icon>
            <template #title>
              <span>КП</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/deals" v-if="authStore.isManager">
            <el-icon><Document /></el-icon>
            <template #title>
              <span>Сделки Bitrix</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/proposal-constructor" v-if="authStore.isAuthenticated">
            <el-icon><Edit /></el-icon>
            <template #title>
              <span>Конструктор КП</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/users" v-if="authStore.isAdmin">
            <el-icon><User /></el-icon>
            <template #title>
              <span>Пользователи</span>
            </template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- Main Container -->
      <el-container class="main-container">
        <!-- Header -->
        <el-header class="app-header">
          <div class="header-content">
            <div class="header-left">
              <el-button
                :icon="isCollapse ? Expand : Fold"
                circle
                @click="toggleCollapse"
                class="collapse-btn"
              />
              <div class="header-title">
                <h3>{{ pageTitle }}</h3>
              </div>
            </div>
            <div class="user-menu">
              <ExchangeRateWidget />
              <el-dropdown @command="handleCommand">
                <span class="user-info">
                  <el-icon><User /></el-icon>
                  {{ authStore.userName }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">
                      <el-icon><User /></el-icon>
                      Профиль
                    </el-dropdown-item>
                    <el-dropdown-item divided command="logout">
                      <el-icon><SwitchButton /></el-icon>
                      Выход
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>

        <!-- Main Content -->
        <el-main class="app-main">
          <RouterView />
        </el-main>
      </el-container>
    </el-container>

    <!-- Для страниц логина/регистрации без навигации -->
    <div v-else class="auth-pages-wrapper">
      <RouterView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ExchangeRateWidget from '@/components/ExchangeRateWidget.vue'
import {
  HomeFilled,
  DataBoard,
  Box,
  User,
  Document,
  SwitchButton,
  ArrowDown,
  Fold,
  Expand,
  OfficeBuilding,
  Edit,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': 'Главная',
    '/dashboard': 'Dashboard',
    '/equipment': 'Оборудование',
    '/clients': 'Клиенты',
    '/manufacturers': 'Производители',
    '/proposals': 'Коммерческие предложения',
    '/deals': 'Сделки Bitrix',
  }
  return titles[route.path] || 'Система КП'
})

const handleCommand = async (command: string) => {
  if (command === 'logout') {
    try {
      await authStore.logout()
      ElMessage.success('Вы успешно вышли из системы')
    } catch (error) {
      console.error('Logout error:', error)
    }
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

onMounted(async () => {
  // Проверяем аутентификацию при загрузке приложения
  if (!authStore.isAuthenticated) {
    await authStore.checkAuth()
  }
})
</script>

<style scoped>
#app {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

.app-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
}

.app-aside {
  background-color: #304156;
  min-height: 100vh;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1);
  transition: width 0.3s;
  overflow: hidden;
}

.app-aside.is-collapse {
  width: 64px !important;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
  white-space: nowrap;
  overflow: hidden;
}

.logo h2 {
  margin: 0;
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  transition: all 0.3s;
}

.app-aside.is-collapse .logo {
  padding: 20px 10px;
}

.app-aside.is-collapse .logo h2 {
  font-size: 16px;
}

.sidebar-menu {
  border-right: none;
  background-color: #304156;
  width: 100%;
}

.sidebar-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.7);
  border-left: 3px solid transparent;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #409eff;
  color: #fff;
  border-left-color: #66b1ff;
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  color: inherit;
  margin-right: 8px;
}

.sidebar-menu :deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0;
  height: 60px;
  line-height: 60px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.collapse-btn {
  border: none;
  background-color: transparent;
  color: #606266;
}

.collapse-btn:hover {
  background-color: #f5f7fa;
  color: #409eff;
}

.header-title h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 500;
}

.user-menu {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.user-info:hover {
  color: #409eff;
  background-color: #f5f7fa;
}

.app-main {
  background-color: #f5f5f5;
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.auth-pages-wrapper {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}
</style>
