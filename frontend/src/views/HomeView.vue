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
            <el-button type="primary" @click="headerListDialogOpen = true">
              <el-icon><Picture /></el-icon>
              Шапки КП
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

        <!-- Интеграция Satu.kz (для суперпользователя или роли Администратор) -->
        <div v-if="canManageBitrix" class="bitrix-section">
          <el-divider />
          <h3>Интеграция Satu.kz</h3>
          <div class="bitrix-widget">
            <el-input
              v-model="satuApiToken"
              placeholder="API Токен Satu.kz (Bearer ключ)"
              clearable
              style="max-width: 500px; margin-right: 12px;"
            />
            <el-button type="primary" :loading="satuChecking" @click="saveSatuTokenAndCheck">
              Сохранить токен
            </el-button>
          </div>
          <p v-if="satuCheckMessage" class="bitrix-message" :class="satuCheckSuccess ? 'success' : 'error'">
            {{ satuCheckMessage }}
          </p>
        </div>
        
        <el-divider />
        
        <div class="quick-links">
          <h3>Быстрые ссылки:</h3>
          <el-row :gutter="20">
            <el-col :span="8" v-if="authStore.isAtLeastJuniorManager">
              <el-card shadow="hover" class="link-card" @click="router.push('/equipment')">
                <el-icon :size="40"><Box /></el-icon>
                <h4>Оборудование</h4>
                <p>Управление каталогом оборудования</p>
              </el-card>
            </el-col>
            <el-col :span="8" v-if="authStore.isAtLeastJuniorManager">
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

    <!-- Headers List Dialog -->
    <el-dialog
      v-model="headerListDialogOpen"
      title="Шапки КП (Логотип и реквизиты)"
      width="800px"
      align-center
    >
      <div style="margin-bottom: 20px;">
        <el-button v-if="authStore.isManager" type="primary" @click="openCreateHeader">Создать шапку КП</el-button>
      </div>

      <el-table :data="headersList" style="width: 100%" v-loading="loadingHeaders">
        <el-table-column label="Логотип" width="100">
          <template #default="scope">
            <img v-if="scope.row.logo_url" :src="scope.row.logo_url" alt="logo" style="max-height: 40px; max-width: 80px; object-fit: contain;" />
            <span v-else>Нет</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="Название" />
        <el-table-column prop="created_by_name" label="Создатель" />
        <el-table-column label="Статус">
          <template #default="scope">
            <el-tag v-if="scope.row.is_default" type="success">По умолчанию</el-tag>
            <el-button v-else size="small" @click="setDefaultHeader(scope.row.id)">Установить</el-button>
          </template>
        </el-table-column>
        <el-table-column label="Действия" width="150" align="right">
          <template #default="scope">
            <template v-if="authStore.isManager">
              <el-button size="small" type="primary" circle @click="openEditHeader(scope.row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" circle @click="deleteHeader(scope.row.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Header Form Dialog -->
    <el-dialog
      v-model="headerFormDialogOpen"
      :title="editingHeaderId ? 'Редактирование шапки' : 'Создание шапки КП'"
      width="600px"
      align-center
    >
      <div class="logo-dialog-content">
        <el-form label-position="top">
          <el-form-item label="Название шапки" required>
            <el-input v-model="headerForm.name" placeholder="Введите название..." />
          </el-form-item>

          <el-form-item label="Логотип">
            <div v-if="headerForm.logoPreviewUrl" class="logo-preview-section" style="margin-bottom: 10px;">
              <img :src="headerForm.logoPreviewUrl" alt="Logo preview" style="max-height: 100px; max-width: 200px; object-fit: contain;" />
            </div>
            <el-upload
              class="logo-uploader"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleLogoFileChange"
            >
              <el-button type="primary">Выбрать файл</el-button>
              <template #tip>
                <div class="el-upload__tip">
                  Поддерживаются форматы PNG, JPG. Рекомендуется прозрачный фон.
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="Реквизиты компании для шапки (Казахский):">
            <el-input
              v-model="headerForm.header_kz_info"
              type="textarea"
              :rows="4"
              placeholder="Введите адрес, БИН, ИИК на казахском..."
            />
          </el-form-item>

          <el-form-item label="Реквизиты компании для шапки (Русский):">
            <el-input
              v-model="headerForm.header_ru_info"
              type="textarea"
              :rows="4"
              placeholder="Введите адрес, БИН, ИИК на русском..."
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="headerFormDialogOpen = false">Отмена</el-button>
        <el-button type="primary" :loading="savingHeader" @click="saveHeaderData">Сохранить</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { Box, Document, DataBoard, Picture, Edit, Delete } from '@element-plus/icons-vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import { ElMessage } from 'element-plus'
import { bitrixAPI } from '@/api/bitrix'
import { satuAPI } from '@/api/satu'

import { proposalHeadersAPI, type ProposalHeaderTemplate } from '@/api/proposalHeaders'
import { ElMessageBox } from 'element-plus'
const authStore = useAuthStore()
const router = useRouter()
const headerListDialogOpen = ref(false)
const headerFormDialogOpen = ref(false)


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

const satuApiToken = ref('')
const satuChecking = ref(false)
const satuCheckMessage = ref('')
const satuCheckSuccess = ref(false)


const headersList = ref<ProposalHeaderTemplate[]>([])
const loadingHeaders = ref(false)

const headerForm = ref({
  name: '',
  header_kz_info: '',
  header_ru_info: '',
  logoPreviewUrl: '',
  file: null as any
})
const editingHeaderId = ref<number | null>(null)
const savingHeader = ref(false)

const loadHeaders = async () => {
  loadingHeaders.value = true
  try {
    headersList.value = await proposalHeadersAPI.list()
  } catch (e) {
    ElMessage.error('Ошибка загрузки списка шапок')
  } finally {
    loadingHeaders.value = false
  }
}

const openCreateHeader = () => {
  editingHeaderId.value = null
  headerForm.value = {
    name: '',
    header_kz_info: '',
    header_ru_info: '',
    logoPreviewUrl: '',
    file: null
  }
  headerFormDialogOpen.value = true
}

const openEditHeader = (header: ProposalHeaderTemplate) => {
  editingHeaderId.value = header.id
  headerForm.value = {
    name: header.name,
    header_kz_info: header.header_kz_info || '',
    header_ru_info: header.header_ru_info || '',
    logoPreviewUrl: header.logo_url || '',
    file: null
  }
  headerFormDialogOpen.value = true
}

const handleLogoFileChange = (file: any) => {
  headerForm.value.file = file.raw
  headerForm.value.logoPreviewUrl = URL.createObjectURL(file.raw)
}

const saveHeaderData = async () => {
  if (!headerForm.value.name) {
    ElMessage.warning('Введите название шапки')
    return
  }
  
  savingHeader.value = true
  const formData = new FormData()
  formData.append('name', headerForm.value.name)
  formData.append('header_kz_info', headerForm.value.header_kz_info)
  formData.append('header_ru_info', headerForm.value.header_ru_info)
  if (headerForm.value.file) {
    formData.append('logo', headerForm.value.file)
  }

  try {
    if (editingHeaderId.value) {
      await proposalHeadersAPI.update(editingHeaderId.value, formData)
      ElMessage.success('Шапка успешно обновлена')
    } else {
      await proposalHeadersAPI.create(formData)
      ElMessage.success('Шапка успешно создана')
    }
    headerFormDialogOpen.value = false
    await loadHeaders()
  } catch (e) {
    ElMessage.error('Ошибка при сохранении шапки')
  } finally {
    savingHeader.value = false
  }
}

const deleteHeader = async (id: number) => {
  try {
    await ElMessageBox.confirm('Вы уверены, что хотите удалить эту шапку?', 'Удаление', { type: 'warning' })
    await proposalHeadersAPI.delete(id)
    ElMessage.success('Шапка удалена')
    await loadHeaders()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('Ошибка при удалении шапки')
    }
  }
}

const setDefaultHeader = async (id: number) => {
  try {
    await proposalHeadersAPI.setDefault(id)
    ElMessage.success('Шапка установлена по умолчанию')
    await loadHeaders()
  } catch (e) {
    ElMessage.error('Ошибка при установке шапки по умолчанию')
  }
}
const loadSystemSettings = async () => {
  if (!canManageBitrix.value) return
  try {
    const data = await bitrixAPI.getSystemSettings()
    bitrixWebhookUrl.value = data.bitrix_webhook_url || ''
    satuApiToken.value = data.satu_api_token || ''
    headerKzInfo.value = data.header_kz_info || ''
    headerRuInfo.value = data.header_ru_info || ''
  } catch (e) {
    console.error('Failed to load system settings:', e)
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

const saveSatuTokenAndCheck = async () => {
  if (!canManageBitrix.value) return
  satuChecking.value = true
  satuCheckMessage.value = ''
  try {
    await bitrixAPI.updateSystemSettings({ satu_api_token: satuApiToken.value })
    const res = await satuAPI.checkConnection(satuApiToken.value || undefined)
    if (res.ok) {
      satuCheckSuccess.value = true
      satuCheckMessage.value = 'Связь с Satu.kz успешна.'
    } else {
      satuCheckSuccess.value = false
      satuCheckMessage.value = res.error || 'Ошибка проверки связи'
    }
  } catch (e: any) {
    satuCheckSuccess.value = false
    satuCheckMessage.value = e.response?.data?.error || e.message || 'Ошибка при сохранении токена'
  } finally {
    satuChecking.value = false
  }
}

const saveHeaderInfo = async () => {
  savingHeader.value = true
  try {
    await bitrixAPI.updateSystemSettings({
      header_kz_info: headerKzInfo.value,
      header_ru_info: headerRuInfo.value
    })
    ElMessage.success('Реквизиты успешно сохранены')
  } catch (e) {
    ElMessage.error('Ошибка при сохранении реквизитов')
  } finally {
    savingHeader.value = false
  }
}

onMounted(async () => {
  await loadHeaders()
  await loadSystemSettings()
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
