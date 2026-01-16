<template>
  <div class="dashboard">
    <el-card>
      <template #header>
        <h2>Dashboard</h2>
      </template>
      <div class="dashboard-content">
        <p><strong>Добро пожаловать, {{ authStore.userName }}!</strong></p>
        <p>Ваша роль: <strong>{{ authStore.userRole || 'Не указана' }}</strong></p>
        
        <el-divider />
        
        <div class="user-info" v-if="authStore.user">
          <h3>Информация о пользователе:</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="ID">{{ authStore.user.user_id }}</el-descriptions-item>
            <el-descriptions-item label="Логин">{{ authStore.user.user_login }}</el-descriptions-item>
            <el-descriptions-item label="Имя">{{ authStore.user.user_name }}</el-descriptions-item>
            <el-descriptions-item label="Email">{{ authStore.user.user_email }}</el-descriptions-item>
            <el-descriptions-item label="Роль">{{ authStore.user.user_role }}</el-descriptions-item>
            <el-descriptions-item label="Телефон">{{ authStore.user.user_phone || 'Не указан' }}</el-descriptions-item>
            <el-descriptions-item label="Активен">
              <el-tag :type="authStore.user.is_active ? 'success' : 'danger'">
                {{ authStore.user.is_active ? 'Да' : 'Нет' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-content {
  padding: 20px 0;
}

.user-info {
  margin-top: 20px;
}

.user-info h3 {
  margin-bottom: 15px;
}
</style>

