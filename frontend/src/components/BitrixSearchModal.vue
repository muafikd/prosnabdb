<template>
  <el-dialog
    v-model="visible"
    title="Поиск в Bitrix24"
    width="640px"
    destroy-on-close
    @close="handleClose"
  >
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="По названию" name="name">
        <el-input
          v-model="queryName"
          placeholder="Введите название компании (от 3 символов)"
          clearable
          @input="debouncedSearch('name')"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-tab-pane>
      <el-tab-pane label="По представителю" name="contact">
        <el-input
          v-model="queryContact"
          placeholder="Введите имя или телефон контакта (от 3 символов)"
          clearable
          @input="debouncedSearch('contact')"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-tab-pane>
      <el-tab-pane label="По ИИН / БИН" name="requisite">
        <el-input
          v-model="queryRequisite"
          placeholder="Введите ИИН или БИН (от 3 символов)"
          clearable
          @input="debouncedSearch('requisite')"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-tab-pane>
      <el-tab-pane label="По сделке" name="deal">
        <el-input
          v-model="queryDeal"
          placeholder="Введите название сделки (от 3 символов)"
          clearable
          @input="debouncedSearch('deal')"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-tab-pane>
    </el-tabs>

    <div class="search-results">
      <div v-if="loading" class="loading-wrap">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>Поиск...</span>
      </div>
      <div v-else-if="error" class="error-wrap">
        {{ error }}
      </div>
      <div v-else-if="results.length === 0 && hasSearched" class="empty-wrap">
        Ничего не найдено. Введите от 3 символов для поиска.
      </div>
      <ul v-else class="results-list">
        <li
          v-for="item in results"
          :key="item.ID"
          class="result-item"
          tabindex="0"
          @click="selectItem(item)"
          @keydown.enter="selectItem(item)"
        >
          <div class="result-title">{{ item.TITLE || item.COMPANY_TITLE || `#${item.ID}` }}</div>
          <div v-if="activeTab === 'deal' && item.COMPANY_TITLE" class="result-meta">
            Компания: {{ item.COMPANY_TITLE }}
          </div>
          <div v-else-if="item.UF_CRM_LEGALENTITY_INN || item.UF_CRM_1657870237252" class="result-meta">
            БИН/ИИН: {{ item.UF_CRM_LEGALENTITY_INN || item.UF_CRM_1657870237252 }}
          </div>
        </li>
      </ul>
    </div>

    <template #footer>
      <el-button @click="handleClose">Закрыть</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Search, Loading } from '@element-plus/icons-vue'
import { bitrixAPI, type BitrixCompanyItem } from '@/api/bitrix'
import { useDebounceFn } from '@vueuse/core'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    defaultTab?: 'name' | 'contact' | 'requisite' | 'deal'
  }>(),
  { defaultTab: 'name' }
)

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'select', clientId: number): void
  (e: 'selectDeal', payload: { deal_id: number; client_id: number | null; deal_title: string }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const activeTab = ref<'name' | 'contact' | 'requisite' | 'deal'>(props.defaultTab || 'name')
const queryName = ref('')
const queryContact = ref('')
const queryRequisite = ref('')
const queryDeal = ref('')
const results = ref<BitrixCompanyItem[]>([])
const loading = ref(false)
const error = ref('')
const hasSearched = ref(false)

const minChars = 3
const debounceMs = 500

function getQuery(): string {
  if (activeTab.value === 'name') return queryName.value.trim()
  if (activeTab.value === 'contact') return queryContact.value.trim()
  if (activeTab.value === 'deal') return queryDeal.value.trim()
  return queryRequisite.value.trim()
}

async function doSearch() {
  const q = getQuery()
  if (q.length < minChars) {
    results.value = []
    hasSearched.value = true
    return
  }
  loading.value = true
  error.value = ''
  hasSearched.value = true
  try {
    const res = await bitrixAPI.search(activeTab.value, q)
    if (res.error) {
      error.value = res.error
      results.value = []
    } else {
      results.value = res.results || []
    }
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message || 'Ошибка поиска'
    results.value = []
  } finally {
    loading.value = false
  }
}

const debouncedSearch = useDebounceFn(() => doSearch(), debounceMs)

function debouncedSearchByTab(_tab: string) {
  debouncedSearch()
}

watch(activeTab, () => {
  debouncedSearchByTab(activeTab.value)
})

watch(() => [props.modelValue, props.defaultTab], ([visible, tab]) => {
  if (visible && tab) {
    activeTab.value = tab as 'name' | 'contact' | 'requisite' | 'deal'
  }
}, { immediate: true })

async function selectItem(item: BitrixCompanyItem) {
  const id = typeof item.ID === 'string' ? parseInt(item.ID, 10) : item.ID
  if (Number.isNaN(id)) return
  loading.value = true
  error.value = ''
  try {
    const isDeal = activeTab.value === 'deal'
    if (isDeal) {
      const res = await bitrixAPI.selectDeal(id)
      if (res.deal_id != null) {
        emit('selectDeal', {
          deal_id: res.deal_id,
          client_id: res.client_id ?? null,
          deal_title: res.deal_title || (item.TITLE as string) || '',
        })
        visible.value = false
      } else {
        error.value = (res as any).error || 'Ошибка выбора сделки'
      }
    } else {
      const res = await bitrixAPI.importClient(id)
      if (res.client_id) {
        emit('select', res.client_id)
        visible.value = false
      } else {
        error.value = (res as any).error || 'Ошибка импорта'
      }
    }
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message || (activeTab.value === 'deal' ? 'Ошибка выбора сделки' : 'Ошибка импорта клиента')
  } finally {
    loading.value = false
  }
}

function handleClose() {
  visible.value = false
  queryName.value = ''
  queryContact.value = ''
  queryRequisite.value = ''
  queryDeal.value = ''
  results.value = []
  error.value = ''
  hasSearched.value = false
}
</script>

<style scoped>
.search-results {
  min-height: 200px;
  margin-top: 16px;
}

.loading-wrap,
.error-wrap,
.empty-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: #909399;
}

.error-wrap {
  color: #f56c6c;
}

.results-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.result-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover,
.result-item:focus {
  background: #ecf5ff;
  outline: none;
}

.result-title {
  font-weight: 500;
  color: #303133;
}

.result-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
