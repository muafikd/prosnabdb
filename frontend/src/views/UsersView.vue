<template>
  <div class="users-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>Пользователи</h2>
          <div class="header-actions">
            <el-input
              v-model="search"
              placeholder="Поиск (имя, логин, email)"
              clearable
              style="width: 320px"
              @input="loadUsers"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="users" stripe style="width: 100%">
        <el-table-column prop="user_id" label="ID" width="80" />
        <el-table-column prop="user_name" label="Имя" min-width="180" />
        <el-table-column prop="user_login" label="Логин" width="160" />
        <el-table-column prop="user_email" label="Email" min-width="220" show-overflow-tooltip />
        <el-table-column prop="user_phone" label="Телефон" width="160">
          <template #default="{ row }">
            {{ row.user_phone || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="Роль" width="180">
          <template #default="{ row }">
            <el-select
              v-model="row.user_role"
              style="width: 100%"
              :disabled="row.user_id === authStore.user?.user_id"
              @change="(val) => updateUser(row.user_id, { user_role: val })"
            >
              <el-option label="Администратор" value="Администратор" />
              <el-option label="Менеджер" value="Менеджер" />
              <el-option label="Просмотр" value="Просмотр" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="Активен" width="120" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :disabled="row.user_id === authStore.user?.user_id"
              @change="(val) => updateUser(row.user_id, { is_active: val })"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Создан" width="140">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { format } from 'date-fns'
import { usersAPI, type User, type UserUpdateData } from '@/api/users'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const users = ref<User[]>([])
const search = ref('')

const formatDate = (d: string) => (d ? format(new Date(d), 'dd.MM.yyyy') : '')

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await usersAPI.list({ search: search.value || undefined })
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e.response?.data?.detail || 'Ошибка загрузки пользователей')
  } finally {
    loading.value = false
  }
}

const updateUser = async (userId: number, data: UserUpdateData) => {
  try {
    await usersAPI.update(userId, data)
    ElMessage.success('Сохранено')
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e.response?.data?.detail || 'Ошибка обновления пользователя')
    await loadUsers() // rollback
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>

