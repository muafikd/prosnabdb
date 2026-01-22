<template>
  <div class="manufacturer-list-view">
    <div class="header-actions">
      <h2>Справочник производителей</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        Добавить производителя
      </el-button>
    </div>

    <!-- Filters -->
    <div class="filters">
      <el-input
        v-model="searchQuery"
        placeholder="Поиск по названию или стране..."
        prefix-icon="Search"
        clearable
        @input="handleSearch"
        style="max-width: 300px"
      />
    </div>

    <!-- Table -->
    <el-table
      v-loading="loading"
      :data="manufacturers"
      style="width: 100%; margin-top: 20px"
      border
      stripe
    >
      <el-table-column prop="manufacturer_name" label="Название" sortable min-width="150" />
      
      <el-table-column prop="manufacturer_country" label="Страна" sortable min-width="120">
        <template #default="scope">
          {{ scope.row.manufacturer_country || '-' }}
        </template>
      </el-table-column>
      
      <el-table-column prop="manufacturer_website" label="Сайт" min-width="150">
        <template #default="scope">
          <a 
            v-if="scope.row.manufacturer_website" 
            :href="scope.row.manufacturer_website" 
            target="_blank" 
            class="website-link"
          >
            {{ scope.row.manufacturer_website }}
            <el-icon><TopRight /></el-icon>
          </a>
          <span v-else>-</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="updated_at" label="Дата обновления" width="160">
        <template #default="scope">
          {{ formatDate(scope.row.updated_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="Действия" width="150" align="center">
        <template #default="scope">
          <el-button-group>
            <el-button 
              size="small" 
              type="primary" 
              icon="Edit" 
              @click="openEditDialog(scope.row)" 
            />
            <el-button 
              size="small" 
              type="danger" 
              icon="Delete" 
              @click="handleDelete(scope.row)" 
            />
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? 'Редактировать производителя' : 'Новый производитель'"
      width="500px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        status-icon
      >
        <el-form-item label="Название" prop="manufacturer_name">
          <el-input v-model="form.manufacturer_name" placeholder="Введите название" />
        </el-form-item>

        <el-form-item label="Страна" prop="manufacturer_country">
          <el-input v-model="form.manufacturer_country" placeholder="Введите страну" />
        </el-form-item>

        <el-form-item label="Сайт" prop="manufacturer_website">
          <el-input v-model="form.manufacturer_website" placeholder="https://example.com" />
        </el-form-item>

        <el-form-item label="Описание" prop="manufacturer_description">
          <el-input 
            v-model="form.manufacturer_description" 
            type="textarea" 
            :rows="3" 
            placeholder="Описание производителя" 
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Отмена</el-button>
          <el-button type="primary" :loading="saving" @click="saveManufacturer">
            Сохранить
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Edit, Delete, TopRight } from '@element-plus/icons-vue'
import { manufacturersAPI, type Manufacturer } from '@/api/manufacturers'
import { format } from 'date-fns'
import debounce from 'lodash/debounce' // Assume lodash is available or implement debounce

// State
const manufacturers = ref<Manufacturer[]>([])
const loading = ref(false)
const searchQuery = ref('')
const dialogVisible = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const currentId = ref<number | null>(null)

// Form
const form = reactive({
  manufacturer_name: '',
  manufacturer_country: '',
  manufacturer_website: '',
  manufacturer_description: '',
})

const rules = reactive<FormRules>({
  manufacturer_name: [
    { required: true, message: 'Введите название производителя', trigger: 'blur' },
    { min: 2, message: 'Название должно быть не короче 2 символов', trigger: 'blur' },
  ],
  manufacturer_website: [
    { type: 'url', message: 'Введите корректный URL (https://...)', trigger: 'blur' },
  ],
})

// Methods
const fetchManufacturers = async () => {
  loading.value = true
  try {
    const response = await manufacturersAPI.getManufacturers({ search: searchQuery.value })
    // Handle both paginated and flat list responses
    if (Array.isArray(response)) {
      manufacturers.value = response
    } else if (response.results) {
      manufacturers.value = response.results
    } else {
      manufacturers.value = []
    }
  } catch (error) {
    console.error('Error fetching manufacturers:', error)
    ElMessage.error('Не удалось загрузить список производителей')
  } finally {
    loading.value = false
  }
}

// Debounced search
let searchTimeout: ReturnType<typeof setTimeout>
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchManufacturers()
  }, 300)
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return format(new Date(dateString), 'dd.MM.yyyy')
}

const openCreateDialog = () => {
  isEditing.value = false
  currentId.value = null
  dialogVisible.value = true
}

const openEditDialog = (item: Manufacturer) => {
  isEditing.value = true
  currentId.value = item.manufacturer_id
  
  form.manufacturer_name = item.manufacturer_name
  form.manufacturer_country = item.manufacturer_country || ''
  form.manufacturer_website = item.manufacturer_website || ''
  form.manufacturer_description = item.manufacturer_description || ''
  
  dialogVisible.value = true
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.manufacturer_name = ''
  form.manufacturer_country = ''
  form.manufacturer_website = ''
  form.manufacturer_description = ''
}

const saveManufacturer = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        if (isEditing.value && currentId.value) {
          await manufacturersAPI.updateManufacturer(currentId.value, form)
          ElMessage.success('Производитель обновлен')
        } else {
          await manufacturersAPI.createManufacturer(form)
          ElMessage.success('Производитель создан')
        }
        dialogVisible.value = false
        fetchManufacturers()
      } catch (error: any) {
        console.error('Error saving manufacturer:', error)
        const errorMsg = error.response?.data?.manufacturer_name?.[0] || 'Ошибка при сохранении'
        ElMessage.error(errorMsg)
      } finally {
        saving.value = false
      }
    }
  })
}

const handleDelete = (item: Manufacturer) => {
  ElMessageBox.confirm(
    `Вы уверены, что хотите удалить производителя "${item.manufacturer_name}"?`,
    'Подтверждение удаления',
    {
      confirmButtonText: 'Удалить',
      cancelButtonText: 'Отмена',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await manufacturersAPI.deleteManufacturer(item.manufacturer_id)
      ElMessage.success('Производитель удален')
      fetchManufacturers()
    } catch (error: any) {
      console.error('Error deleting manufacturer:', error)
      // Check for specific backend error about linked equipment
      const errorDetail = error.response?.data?.detail || error.response?.data?.error || 'Не удалось удалить производителя'
      ElMessage.error(errorDetail)
    }
  })
}

onMounted(() => {
  fetchManufacturers()
})
</script>

<style scoped>
.manufacturer-list-view {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions h2 {
  margin: 0;
  color: #303133;
}

.filters {
  margin-bottom: 20px;
}

.website-link {
  color: #409eff;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.website-link:hover {
  text-decoration: underline;
}
</style>
