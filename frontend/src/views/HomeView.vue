<template>
  <div class="home-view">
    <el-card>
      <div class="home-content">
        <h2>Добро пожаловать в систему управления коммерческими предложениями!</h2>
        <div class="user-info-section">
          <div class="user-info-left">
            <p><strong>Пользователь:</strong> {{ authStore.userName }}</p>
            <p><strong>Роль:</strong> {{ authStore.userRole || 'Не указана' }}</p>
          </div>
          <div class="user-info-right">
            <el-button type="primary" @click="logoDialogOpen = true">
              <el-icon><Picture /></el-icon>
              Настройка лого
            </el-button>
          </div>
        </div>

        <!-- Интеграция Bitrix24 (для суперпользователя или роли Администратор) -->
        <div v-if="canManageBitrix" class="bitrix-section">
          <el-divider />
          <h3>Интеграция Bitrix24</h3>
          <div class="bitrix-widget">
            <el-input
              v-model="bitrixWebhookUrl"
              placeholder="URL вебхука Bitrix24 (например: https://ваш-портал.bitrix24.com/rest/1/код/)"
              clearable
              style="max-width: 500px; margin-right: 12px;"
            />
            <el-button type="primary" :loading="bitrixChecking" @click="saveBitrixUrlAndCheck">
              Проверить связь
            </el-button>
          </div>
          <p v-if="bitrixCheckMessage" class="bitrix-message" :class="bitrixCheckSuccess ? 'success' : 'error'">
            {{ bitrixCheckMessage }}
          </p>
        </div>
        
        <el-divider />
        
        <div class="quick-links">
          <h3>Быстрые ссылки:</h3>
          <el-row :gutter="20">
            <el-col :span="8" v-if="authStore.isManager">
              <el-card shadow="hover" class="link-card" @click="router.push('/equipment')">
                <el-icon :size="40"><Box /></el-icon>
                <h4>Оборудование</h4>
                <p>Управление каталогом оборудования</p>
              </el-card>
            </el-col>
            <el-col :span="8" v-if="authStore.isManager">
              <el-card shadow="hover" class="link-card" @click="router.push('/proposals')">
                <el-icon :size="40"><Document /></el-icon>
                <h4>Коммерческие предложения</h4>
                <p>Создание и управление КП</p>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover" class="link-card" @click="router.push('/dashboard')">
                <el-icon :size="40"><DataBoard /></el-icon>
                <h4>Dashboard</h4>
                <p>Аналитика и статистика</p>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- Logo Settings Dialog -->
    <el-dialog
      v-model="logoDialogOpen"
      title="Настройка логотипа компании"
      width="500px"
      align-center
    >
      <div class="logo-dialog-content">
        <div class="logo-preview-section">
          <p class="section-label">Текущий логотип (используется в КП и PDF):</p>
          <div class="logo-container">
            <img v-if="logoUrl" :src="logoUrl" alt="Company Logo" class="preview-img" />
            <el-empty v-else description="Логотип не загружен" />
          </div>
        </div>

        <el-divider />

        <div class="upload-section">
          <p class="section-label">Загрузить новый логотип:</p>
          <el-upload
            class="logo-uploader"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleLogoChange"
          >
            <el-button type="primary">Выбрать файл</el-button>
            <template #tip>
              <div class="el-upload__tip">
                Поддерживаются форматы PNG, JPG. Рекомендуется прозрачный фон.
              </div>
            </template>
          </el-upload>
        </div>
      </div>
      <template #footer>
        <el-button @click="logoDialogOpen = false">Закрыть</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { Box, Document, DataBoard, Picture } from '@element-plus/icons-vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import { ElMessage } from 'element-plus'
import { bitrixAPI } from '@/api/bitrix'

const authStore = useAuthStore()
const router = useRouter()
const logoDialogOpen = ref(false)
const logoUrl = ref('')

// Виджет Bitrix24: суперпользователь или роль «Администратор»
const canManageBitrix = computed(() => {
  const u = authStore.user
  if (!u) return false
  return !!(u.is_superuser || u.user_role === 'Администратор')
})

const bitrixWebhookUrl = ref('')
const bitrixChecking = ref(false)
const bitrixCheckMessage = ref('')
const bitrixCheckSuccess = ref(false)

const fetchLogo = async () => {
  try {
    const token = Cookies.get('access_token')
    const response = await axios.get('/api/system-settings/logo/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    logoUrl.value = response.data.url + '?t=' + Date.now()
  } catch (e) {
    console.error('Failed to fetch logo', e)
  }
}

const handleLogoChange = async (file: any) => {
  const formData = new FormData()
  formData.append('file', file.raw)
  
  try {
    const token = Cookies.get('access_token')
    await axios.post('/api/system-settings/logo/', formData, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    ElMessage.success('Логотип успешно обновлен')
    await fetchLogo()
  } catch (e) {
    ElMessage.error('Ошибка при загрузке логотипа')
  }
}

const loadBitrixSettings = async () => {
  if (!canManageBitrix.value) return
  try {
    const data = await bitrixAPI.getSystemSettings()
    bitrixWebhookUrl.value = data.bitrix_webhook_url || ''
  } catch (e) {
    console.error('Failed to load Bitrix settings:', e)
  }
}

const saveBitrixUrlAndCheck = async () => {
  if (!canManageBitrix.value) return
  bitrixChecking.value = true
  bitrixCheckMessage.value = ''
  try {
    await bitrixAPI.updateSystemSettings({ bitrix_webhook_url: bitrixWebhookUrl.value })
    const res = await bitrixAPI.checkConnection(bitrixWebhookUrl.value || undefined)
    if (res.ok) {
      bitrixCheckSuccess.value = true
      bitrixCheckMessage.value = 'Связь с Bitrix24 успешна.'
    } else {
      bitrixCheckSuccess.value = false
      bitrixCheckMessage.value = res.error || 'Ошибка проверки связи'
    }
  } catch (e: any) {
    bitrixCheckSuccess.value = false
    bitrixCheckMessage.value = e.response?.data?.error || e.message || 'Ошибка при проверке связи'
  } finally {
    bitrixChecking.value = false
  }
}

onMounted(async () => {
  await fetchLogo()
  await loadBitrixSettings()
})
</script>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
}

.home-content {
  padding: 20px 0;
}

.home-content h2 {
  margin-bottom: 20px;
  color: #303133;
}

.user-info-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.user-info-left {
  flex: 1;
}

.user-info-right {
  display: flex;
  align-items: center;
}

.quick-links {
  margin-top: 30px;
}

.quick-links h3 {
  margin-bottom: 20px;
  color: #606266;
}

.link-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
  padding: 20px;
}

.link-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.link-card .el-icon {
  color: #409eff;
  margin-bottom: 10px;
}

.link-card h4 {
  margin: 10px 0;
  color: #303133;
}

.link-card p {
  color: #909399;
  font-size: 14px;
}

.logo-dialog-content {
  padding: 10px 0;
}

.logo-preview-section {
  margin-bottom: 20px;
}

.section-label {
  margin-bottom: 10px;
  font-weight: 500;
  color: #606266;
}

.logo-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 150px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 20px;
  background-color: #fafafa;
}

.preview-img {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.upload-section {
  margin-top: 20px;
}

.logo-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.el-upload__tip {
  margin-top: 10px;
  color: #909399;
  font-size: 12px;
}

.bitrix-section {
  margin: 20px 0;
}

.bitrix-section h3 {
  margin-bottom: 12px;
  color: #303133;
}

.bitrix-widget {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.bitrix-message {
  margin-top: 12px;
  font-size: 14px;
}

.bitrix-message.success {
  color: #67c23a;
}

.bitrix-message.error {
  color: #f56c6c;
}
</style>
