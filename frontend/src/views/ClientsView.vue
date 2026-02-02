<template>
  <div class="clients-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>Клиенты</h2>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            Добавить клиента
          </el-button>
        </div>
      </template>

      <!-- Поиск и фильтры -->
      <div class="filters">
        <el-input
          v-model="searchQuery"
          placeholder="Поиск по имени или компании..."
          clearable
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- Таблица клиентов -->
      <el-table
        v-loading="loading"
        :data="clients"
        stripe
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="client_id" label="ID" width="80" sortable />
        <el-table-column prop="client_name" label="Имя клиента" sortable />
        <el-table-column prop="client_company_name" label="Компания" sortable />
        <el-table-column prop="client_phone" label="Телефон" />
        <el-table-column prop="client_email" label="Email" />
        <el-table-column prop="client_type" label="Тип" width="120" />
        <el-table-column prop="client_bin_iin" label="БИН/ИИН" width="120" />
        <el-table-column label="Bitrix24" width="120" align="center">
          <template #default="{ row }">
            <el-link
              v-if="row.bitrix_id && bitrixCompanyUrl(row.bitrix_id)"
              :href="bitrixCompanyUrl(row.bitrix_id)!"
              target="_blank"
              type="primary"
              :underline="false"
            >
              <el-icon><Link /></el-icon>
              Открыть
            </el-link>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Дата создания" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Действия" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
              circle
            />
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              circle
            />
          </template>
        </el-table-column>
      </el-table>

      <!-- Пагинация -->
      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Модальное окно создания/редактирования -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? 'Редактировать клиента' : 'Создать клиента'"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="150px"
        label-position="left"
      >
        <el-form-item label="Имя клиента *" prop="client_name">
          <el-input v-model="formData.client_name" placeholder="Введите имя клиента" />
        </el-form-item>

        <el-form-item label="Телефон" prop="client_phone">
          <el-input v-model="formData.client_phone" placeholder="+7 (XXX) XXX-XX-XX" />
        </el-form-item>

        <el-form-item label="Email" prop="client_email">
          <el-input v-model="formData.client_email" type="email" placeholder="email@example.com" />
        </el-form-item>

        <el-form-item label="Название компании" prop="client_company_name">
          <el-input v-model="formData.client_company_name" placeholder="Введите название компании" />
        </el-form-item>

        <el-form-item label="Тип клиента" prop="client_type">
          <el-select v-model="formData.client_type" placeholder="Выберите тип" clearable>
            <el-option label="Физическое лицо" value="Физическое лицо" />
            <el-option label="Юридическое лицо" value="Юридическое лицо" />
            <el-option label="ИП" value="ИП" />
          </el-select>
        </el-form-item>

        <el-form-item label="БИН/ИИН" prop="client_bin_iin">
          <el-input v-model="formData.client_bin_iin" placeholder="Введите БИН/ИИН" />
        </el-form-item>

        <el-form-item label="Адрес" prop="client_address">
          <el-input
            v-model="formData.client_address"
            type="textarea"
            :rows="2"
            placeholder="Введите адрес"
          />
        </el-form-item>

        <el-divider>Банковские реквизиты</el-divider>

        <el-form-item label="БИК" prop="client_bik">
          <el-input v-model="formData.client_bik" placeholder="Введите БИК" />
        </el-form-item>

        <el-form-item label="ИИК" prop="client_iik">
          <el-input v-model="formData.client_iik" placeholder="Введите ИИК" />
        </el-form-item>

        <el-form-item label="Название банка" prop="client_bankname">
          <el-input v-model="formData.client_bankname" placeholder="Введите название банка" />
        </el-form-item>

        <el-form-item v-if="isEditMode && currentClientBitrixId" label="Bitrix24">
          <el-link
            :href="bitrixCompanyUrl(currentClientBitrixId)!"
            target="_blank"
            type="primary"
          >
            <el-icon><Link /></el-icon>
            Открыть компанию в Bitrix24
          </el-link>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Отмена</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEditMode ? 'Сохранить' : 'Создать' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete, Search, Link } from '@element-plus/icons-vue'
import { clientsAPI, type Client, type ClientCreateData } from '@/api/clients'
import { bitrixAPI } from '@/api/bitrix'
import { format } from 'date-fns'

// State
const loading = ref(false)
const submitting = ref(false)
const clients = ref<Client[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEditMode = ref(false)
const currentClientId = ref<number | null>(null)
const currentClientBitrixId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const bitrixBaseUrl = ref('')

function bitrixCompanyUrl(bitrixId: number | null | undefined): string | null {
  if (!bitrixId || !bitrixBaseUrl.value) return null
  return `${bitrixBaseUrl.value}/crm/company/details/${bitrixId}/`
}

// Form data
const formData = reactive<ClientCreateData>({
  client_name: '',
  client_phone: '',
  client_email: '',
  client_company_name: '',
  client_type: '',
  client_bin_iin: '',
  client_address: '',
  client_bik: '',
  client_iik: '',
  client_bankname: '',
})

// Form validation rules
const formRules: FormRules = {
  client_name: [
    { required: true, message: 'Пожалуйста, введите имя клиента', trigger: 'blur' },
    { min: 2, message: 'Имя должно содержать минимум 2 символа', trigger: 'blur' },
  ],
  client_email: [
    { type: 'email', message: 'Введите корректный email', trigger: 'blur' },
  ],
}

// Methods
const loadClients = async () => {
  try {
    loading.value = true
    const params: any = {
      page: currentPage.value,
    }
    
    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = await clientsAPI.getClients(params)
    // Обрабатываем как пагинированный ответ, так и обычный массив
    if (Array.isArray(response)) {
      clients.value = response
      total.value = response.length
    } else {
      clients.value = response.results || []
      total.value = response.count || 0
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка загрузки клиентов')
    console.error('Load clients error:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadClients()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadClients()
}

const handleCreate = () => {
  isEditMode.value = false
  currentClientId.value = null
  currentClientBitrixId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = async (client: Client) => {
  try {
    loading.value = true
    const clientData = await clientsAPI.getClient(client.client_id)
    
    isEditMode.value = true
    currentClientId.value = client.client_id
    
    // Заполняем форму данными клиента
    Object.assign(formData, {
      client_name: clientData.client_name,
      client_phone: clientData.client_phone || '',
      client_email: clientData.client_email || '',
      client_company_name: clientData.client_company_name || '',
      client_type: clientData.client_type || '',
      client_bin_iin: clientData.client_bin_iin || '',
      client_address: clientData.client_address || '',
      client_bik: clientData.client_bik || '',
      client_iik: clientData.client_iik || '',
      client_bankname: clientData.client_bankname || '',
    })
    currentClientBitrixId.value = clientData.bitrix_id ?? null
    dialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка загрузки данных клиента')
    console.error('Load client error:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (client: Client) => {
  try {
    await ElMessageBox.confirm(
      `Вы уверены, что хотите удалить клиента "${client.client_name}"?`,
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )

    await clientsAPI.deleteClient(client.client_id)
    ElMessage.success('Клиент успешно удален')
    loadClients()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления клиента')
      console.error('Delete client error:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        submitting.value = true

        if (isEditMode.value && currentClientId.value) {
          await clientsAPI.updateClient(currentClientId.value, formData)
          ElMessage.success('Клиент успешно обновлен')
        } else {
          await clientsAPI.createClient(formData)
          ElMessage.success('Клиент успешно создан')
        }

        dialogVisible.value = false
        loadClients()
      } catch (error: any) {
        const errorMessage = error.response?.data?.message || 
                           (error.response?.data ? JSON.stringify(error.response.data) : '') ||
                           'Ошибка сохранения клиента'
        ElMessage.error(errorMessage)
        console.error('Submit error:', error)
      } finally {
        submitting.value = false
      }
    } else {
      ElMessage.warning('Пожалуйста, заполните все обязательные поля')
    }
  })
}

const handleDialogClose = () => {
  resetForm()
  formRef.value?.clearValidate()
}

const resetForm = () => {
  Object.assign(formData, {
    client_name: '',
    client_phone: '',
    client_email: '',
    client_company_name: '',
    client_type: '',
    client_bin_iin: '',
    client_address: '',
    client_bik: '',
    client_iik: '',
    client_bankname: '',
  })
}

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy HH:mm')
  } catch {
    return dateString
  }
}

// Загружаем базовый URL Bitrix24 для ссылок на компанию (из webhook: https://portal.bitrix24.kz/rest/... → https://portal.bitrix24.kz)
const loadBitrixBaseUrl = async () => {
  try {
    const settings = await bitrixAPI.getSystemSettings()
    const url = (settings.bitrix_webhook_url || '').trim()
    if (url) {
      const u = new URL(url)
      bitrixBaseUrl.value = u.origin
    }
  } catch {
    bitrixBaseUrl.value = ''
  }
}

onMounted(() => {
  loadClients()
  loadBitrixBaseUrl()
})
</script>

<style scoped>
.clients-view {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.filters {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.text-muted {
  color: #909399;
  font-size: 12px;
}
</style>
