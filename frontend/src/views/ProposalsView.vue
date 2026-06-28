<template>
  <div class="proposals-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>Коммерческие предложения</h2>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            Создать КП
          </el-button>
        </div>
      </template>

      <!-- Фильтры -->
      <div class="filters">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchQuery"
              placeholder="Поиск по названию, номеру КП, клиенту или компании..."
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filters.client_id"
              placeholder="Клиент"
              clearable
              filterable
              @change="handleFilterChange"
            >
              <el-option
                v-for="client in clients"
                :key="client.client_id"
                :label="client.client_name"
                :value="client.client_id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filters.proposal_status"
              placeholder="Статус"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="Черновик" value="draft" />
              <el-option label="Отправлено" value="sent" />
              <el-option label="Принято" value="accepted" />
              <el-option label="Отклонено" value="rejected" />
              <el-option label="В переговорах" value="negotiating" />
              <el-option label="Завершено" value="completed" />
            </el-select>
          </el-col>

          <el-col :span="4" style="display: flex; align-items: center;">
             <el-checkbox v-model="includeInactive" label="Показать удаленные" @change="handleFilterChange" />
          </el-col>
        </el-row>
      </div>

      <!-- Таблица КП -->
      <el-table
        v-loading="loading"
        :data="proposalsList"
        stripe
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'proposal_date', order: 'descending' }"
      >
        <el-table-column prop="proposal_id" label="ID" width="80" sortable />
        <el-table-column prop="outcoming_number" label="Номер КП" width="150" sortable />
        <el-table-column prop="proposal_name" label="Название КП" sortable min-width="200" />
        <el-table-column label="Клиент" width="200">
          <template #default="{ row }">
            {{ row.client?.client_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="Автор (обновил)" width="150" sortable>
          <template #default="{ row }">
             {{ row.updated_by?.user_name || row.user?.user_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="proposal_date" label="Дата КП" width="120" sortable>
          <template #default="{ row }">
            {{ formatDate(row.proposal_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_price" label="Итоговая цена" width="150" sortable>
          <template #default="{ row }">
            {{ formatPrice(row.total_price, row.currency_ticket) }}
          </template>
        </el-table-column>
        <el-table-column prop="proposal_status" label="Статус" width="130" sortable>
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.proposal_status)">
              {{ getStatusLabel(row.proposal_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Дата создания" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="Компания" width="200">
          <template #default="{ row }">
            {{ row.client?.client_company_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="Обновлено" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Действия" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="DocumentCopy"
              @click="handleCopy(row)"
              circle
              title="Создать копию"
            />
            <el-button
              v-if="canEdit(row)"
              type="warning"
              size="small"
              :icon="DataBoard"
              @click="handleLayout(row)"
              circle
              title="Конструктор (верстка)"
            />
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
              circle
              :title="canEdit(row) ? 'Редактировать' : 'Просмотр'"
            />
            <el-button
              v-if="canDelete(row)"
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              circle
              :title="row.is_active === false ? 'Удалено' : 'Архивировать'"
              :disabled="row.is_active === false"
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


    <ProposalFormModal
      v-model:visible="dialogVisible"
      :proposal-id="editingProposalId"
      @saved="loadData"
    />
  </div>
</template>


<script setup lang="ts">
import ProposalFormModal from '@/components/proposals/ProposalFormModal.vue'
import { ref, reactive, computed, onMounted, nextTick, inject, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import axios from 'axios'
import Cookies from 'js-cookie'
import { Plus, Edit, Delete, Search, Coin, Setting, DocumentCopy, DataBoard, ArrowUp, ArrowDown, Refresh, View, Loading, Picture, Download, Rank } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'
import {
  proposalsAPI,
  type CommercialProposal,
  additionalPricesAPI,
  type CommercialProposalCreateData,
  type EquipmentList,
  type AdditionalPrice,
} from '@/api/proposals'
import { exchangeRatesAPI } from '@/api/exchangeRates'
import { equipmentListItemsAPI } from '@/api/proposals'
import { clientsAPI, type Client } from '@/api/clients'
import { dealsAPI, type CrmDeal } from '@/api/deals'
import { equipmentAPI, type Equipment, manufacturersAPI, type Manufacturer } from '@/api/equipment'
import BitrixSearchModal from '@/components/BitrixSearchModal.vue'
import { formatPrice } from '@/utils/formatters'
import { getImageSrc } from '@/utils/imageProxy'
import { format } from 'date-fns'
import { useAuthStore } from '@/stores/auth' // Import auth store

// --- Interfaces ---
interface InternalExchangeRate {
  currency: string
  // Display only
  current_nb_rate?: number 
  // Stored
  creation_nb_rate?: number
  internal_rate: number
  rate_date?: string
  // Legacy support
  nb_rate?: number
}

interface RowExpense {
  name: string
  value: number
  formattedValue?: string
}

interface ProposalAdjustment {
  id?: number
  adjustment_type: 'markup' | 'discount'
  value_percentage: number
  comments: string
  author_name?: string
  created_at?: string
}

interface EquipmentRow {
  equipment_id: number
  equipment_name: string
  equipment_manufacture_price: number // Base price from DB
  equipment_price_currency_type: string // Currency from DB
  sale_price_kzt?: number // Sale price in KZT from equipment card
  
  // For calculation
  quantity: number
  production_price: number // Same as manufacture_price
  currency: string // Same as price_currency_type
  
  row_expenses: RowExpense[]
  
  // Calculated fields (from data_package if available)
  purchase_price_original?: number // Purchase price in original currency
  purchase_price_currency?: string // Original currency of purchase price
  purchase_price_kzt?: number // Purchase price converted to KZT
  base_cost_kzt?: number // Base cost (purchase + row expenses) in KZT
  allocated_overhead_per_unit?: number // Distributed overhead per unit
  margin_kzt?: number // Margin per unit in KZT
  margin_percentage?: number // Margin percentage
}

interface PaymentLogItem {
  payment_id?: number
  payment_name: string
  payment_value: number
  payment_date: string
  comments: string
  user_name: string
  user?: number
}

interface AdditionalService {
  name: string
  price: number
  description: string
}

// --- State ---
const loading = ref(false)
const proposalsList = ref<CommercialProposal[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filters = reactive({ client_id: null, proposal_status: null })
const includeInactive = ref(false)

const clients = ref<Client[]>([])
const manufacturers = ref<Manufacturer[]>([])
const deals = ref<CrmDeal[]>([])
const additionalPrices = ref<AdditionalPrice[]>([])
const liveRates = ref<any[]>([]) // Store live rates from API
const equipmentList = ref<Equipment[]>([]) // All available equipment
const internalExchangeRates = ref<InternalExchangeRate[]>([])

const dialogVisible = ref(false)
const editingProposalId = ref<number | null>(null)
const isEditMode = ref(false)
const activeTab = ref('basic')
const submitting = ref(false)
const bitrixSearchVisible = ref(false)

const equipmentTableRef = ref()
let sortableInstance: Sortable | null = null

const initSortable = () => {
    if (!equipmentTableRef.value) return
    const el = equipmentTableRef.value.$el.querySelector('.el-table__body-wrapper tbody')
    if (!el) return
    
    if (sortableInstance) {
        sortableInstance.destroy()
    }
    
    sortableInstance = Sortable.create(el, {
        handle: '.drag-handle',
        animation: 150,
        onEnd: (evt: any) => {
            const oldIndex = evt.oldIndex
            const newIndex = evt.newIndex
            if (oldIndex !== undefined && newIndex !== undefined) {
                const item = selectedEquipment.value.splice(oldIndex, 1)[0]
                selectedEquipment.value.splice(newIndex, 0, item)
            }
        }
    })
}

watch([dialogVisible, activeTab], ([newDialogVisible, newActiveTab]) => {
    if (newDialogVisible && newActiveTab === 'equipment') {
        nextTick(() => {
            initSortable()
        })
    }
})

// Equipment card dialog state
const equipmentCardDialogVisible = ref(false)
const currentEquipmentCard = ref<Equipment | null>(null)
const loadingEquipmentCard = ref(false)
const currentProposal = ref<any>(null)
const authStore = useAuthStore()

const canEdit = (proposal: any) => {
  if (authStore.isAdmin || authStore.isManager) return true
  if (authStore.isJuniorManager) {
    return proposal.user?.user_id === authStore.user?.user_id
  }
  return false
}

const canDelete = (proposal: any) => {
  if (authStore.isAdmin || authStore.isManager) return true
  if (authStore.isJuniorManager) {
    return proposal.user?.user_id === authStore.user?.user_id
  }
  return false
}
const router = useRouter()
const route = useRoute()

const handleLayout = async (row: CommercialProposal) => {
  const token = Cookies.get('access_token')
  try {
    // First refresh data package from proposal
    await axios.post(`/api/commercial-proposals/${row.proposal_id}/refresh-data-package/`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    ElMessage.success('Данные обновлены')
  } catch (e) {
    console.error(e)
    ElMessage.warning('Не удалось обновить данные, открываю конструктор с текущими данными')
  }
  // Then open constructor
  router.push({ name: 'proposal-constructor', query: { proposal_id: row.proposal_id } })
}
const tempPayments = ref<PaymentLogItem[]>([]) // State for payments

// Form Data
const formRef = ref<FormInstance>()
const formData = reactive<CommercialProposalCreateData>({
  proposal_name: '',
  outcoming_number: '',
  deal_id: null,
  client_id: null,
  currency_ticket: 'KZT',
  exchange_rate: '1',
  total_price: '0',
  proposal_date: new Date().toISOString().split('T')[0] || '',
  proposal_status: 'draft',
  proposal_version: 1,
  additional_price_ids: [],
  additional_services: [],
  comments: '',
  // ... other fields set defaults
})

const bitrixDefaultTab = ref<'name' | 'contact' | 'requisite' | 'deal'>('deal')

// Rules
const formRules: FormRules = {
  proposal_name: [{ required: true, message: 'Обязательное поле', trigger: 'blur' }],
  outcoming_number: [{ required: true, message: 'Обязательное поле', trigger: 'blur' }],
  deal_id: [{ required: true, message: 'Выберите сделку в Bitrix24', trigger: 'change' }],
}

// Bitrix24 search — для выбора сделки (в начале формы)
const openBitrixSearchForDeal = () => {
  bitrixDefaultTab.value = 'deal'
  bitrixSearchVisible.value = true
}

// Bitrix24 search — для выбора клиента (компании)
const openBitrixSearch = () => {
  bitrixDefaultTab.value = 'name'
  bitrixSearchVisible.value = true
}

const onBitrixDealSelected = async (payload: { deal_id: number; client_id: number | null; deal_title: string }) => {
  formData.deal_id = payload.deal_id
  formData.client_id = payload.client_id ?? null
  try {
    // Обновляем списки из локальной БД (как для клиентов) — сделка уже сохранена бэкендом
    const [dealsRes, clientRes] = await Promise.all([
      dealsAPI.getList(),
      clientsAPI.getClients(),
    ])
    deals.value = dealsRes
    if ('results' in clientRes && clientRes.results) {
      clients.value = clientRes.results
    } else if (Array.isArray(clientRes)) {
      clients.value = clientRes
    }
  } catch (e) {
    console.error('Failed to refresh deals/clients:', e)
  }
  ElMessage.success('Сделка выгружена в локальную БД' + (payload.client_id ? ', компания подтянута' : ''))
}

const onBitrixClientSelected = async (clientId: number) => {
  formData.client_id = clientId
  try {
    const clientRes = await clientsAPI.getClients()
    if ('results' in clientRes && clientRes.results) {
      clients.value = clientRes.results
    } else if (Array.isArray(clientRes)) {
      clients.value = clientRes
    }
  } catch (e) {
    console.error('Failed to refresh clients:', e)
  }
  ElMessage.success('Клиент выбран из Bitrix24')
}

// Exchange Rates State

const showAddCurrencyDialog = ref(false)
const newCurrency = ref('USD')

// Equipment State
const selectedEquipment = ref<EquipmentRow[]>([])
const showAddEquipmentDialog = ref(false)
const equipmentSearchQuery = ref('')

const showPhotoCarouselDialog = ref(false)
const selectedEquipmentForPhotos = ref<Equipment | null>(null)

const openPhotoCarousel = (row: Equipment) => {
    selectedEquipmentForPhotos.value = row
    showPhotoCarouselDialog.value = true
}

// Server-side equipment search state (for "Добавить оборудование")
const equipmentSearchResults = ref<Equipment[]>([])
const equipmentSearchLoading = ref(false)
const equipmentSearchPage = ref(1)
const equipmentSearchTotal = ref(0)
const equipmentSearchPageSize = ref(20)
let equipmentSearchTimeout: ReturnType<typeof setTimeout> | null = null

const getManufacturerName = computed(() => (id: number) => {
    const man = manufacturers.value.find(m => m.manufacturer_id === id)
    return man?.manufacturer_name || `ID: ${id}`
})

const fetchEquipmentSearch = async (page: number = 1) => {
    equipmentSearchLoading.value = true
    try {
        const q = (equipmentSearchQuery.value || '').trim()
        const resp = await equipmentAPI.getEquipment({ search: q || undefined, page })

        if (resp && typeof resp === 'object' && 'results' in resp && Array.isArray((resp as any).results)) {
            const paged = resp as any
            equipmentSearchResults.value = paged.results || []
            equipmentSearchTotal.value = typeof paged.count === 'number' ? paged.count : (paged.results?.length || 0)
            equipmentSearchPage.value = page
            // If backend doesn't expose page_size, use received length (but keep stable fallback)
            equipmentSearchPageSize.value = paged.results?.length ? paged.results.length : equipmentSearchPageSize.value
            return
        }

        if (Array.isArray(resp)) {
            // Non-paginated backend response (fallback)
            equipmentSearchResults.value = resp
            equipmentSearchTotal.value = resp.length
            equipmentSearchPage.value = 1
            equipmentSearchPageSize.value = resp.length || equipmentSearchPageSize.value
            return
        }

        equipmentSearchResults.value = []
        equipmentSearchTotal.value = 0
        equipmentSearchPage.value = 1
    } catch (e) {
        console.error('Equipment search failed:', e)
        equipmentSearchResults.value = []
        equipmentSearchTotal.value = 0
        equipmentSearchPage.value = 1
    } finally {
        equipmentSearchLoading.value = false
    }
}

const handleEquipmentSearchPageChange = (page: number) => {
    fetchEquipmentSearch(page)
}

// Row Expenses State
const showRowExpenseDialog = ref(false)
const currentRowRow = ref<EquipmentRow | null>(null)
const currentRowExpense = reactive({ name: '', value: 0 })

// Payments Methods
const addPayment = () => {
    const userName: string = authStore.userName || ''
    const paymentDate: string = new Date().toISOString().split('T')[0] || ''
    tempPayments.value.push({
        payment_name: '',
        payment_value: 0,
        payment_date: paymentDate,
        comments: '',
        user_name: userName, // Set current user as author
        user: authStore.user?.user_id
    })
}

const removePayment = (index: number) => {
    tempPayments.value.splice(index, 1)
}

const totalPaid = computed(() => {
    return tempPayments.value.reduce((sum, item) => sum + Number(item.payment_value || 0), 0)
})

const remainingBalance = computed(() => {
    const total = Number(formData.total_price || 0)
    return total - totalPaid.value
})

// Markups/Discounts State
const showAdjustmentDialog = ref(false)
const adjustmentForm = reactive({
    adjustment_type: 'markup',
    value_percentage: 0,
    comments: ''
})

const openAdjustmentDialog = () => {
    adjustmentForm.adjustment_type = 'markup'
    adjustmentForm.value_percentage = 0
    adjustmentForm.comments = ''
    showAdjustmentDialog.value = true
}

const addAdjustment = () => {
    if (adjustmentForm.value_percentage <= 0) {
        ElMessage.warning('Размер должен быть больше 0')
        return
    }
    
    if (!formData.adjustments) formData.adjustments = []
    
    formData.adjustments.push({
        adjustment_type: adjustmentForm.adjustment_type as any,
        value_percentage: adjustmentForm.value_percentage,
        comments: adjustmentForm.comments,
        created_at: new Date().toISOString()
    })
    
    showAdjustmentDialog.value = false
}

const removeAdjustment = (index: number) => {
    formData.adjustments?.splice(index, 1)
}

const netAdjustmentPercentage = computed(() => {
    if (!formData.adjustments || formData.adjustments.length === 0) return 0
    return formData.adjustments.reduce((sum, adj) => {
        const val = Number(adj.value_percentage || 0)
        return adj.adjustment_type === 'markup' ? sum + val : sum - val
    }, 0)
})

// Global Expenses Management
const showAdditionalPriceDialog = ref(false)
const loadingAdditionalPrices = ref(false)
const showAdditionalPriceFormDialog = ref(false)
const refreshingPrices = ref(false)
const exportingProposalEquipment = ref(false)
const additionalPriceForm = reactive({
    price_parameter_name: '',
    value_type: 'fixed',
    price_parameter_value: 0
}) // simplified

// Additional Services State
const showAdditionalServicesDialog = ref(false)
const currentAdditionalService = reactive<AdditionalService>({ name: '', price: 0, description: '' })


// Calculation State
// marginType и marginValue больше не используются - маржа рассчитывается автоматически

// --- Methods ---

const loadData = async () => {
    loading.value = true
    try {
        const params: any = { page: currentPage.value, search: searchQuery.value }
        if (includeInactive.value) params.include_inactive = true
        
        const propRes = await proposalsAPI.getProposals(params)
        if ('results' in propRes && Array.isArray(propRes.results)) {
            proposalsList.value = propRes.results
            total.value = propRes.count
        } else if (Array.isArray(propRes)) {
            proposalsList.value = propRes
            total.value = propRes.length
        }

        const clientRes = await clientsAPI.getClients()
        if ('results' in clientRes && clientRes.results) {
            clients.value = clientRes.results
        } else if (Array.isArray(clientRes)) {
            clients.value = clientRes
        }

        try {
            deals.value = await dealsAPI.getList()
        } catch (e) {
            console.error('Failed to load deals:', e)
            deals.value = []
        }

        // IMPORTANT: не грузим весь список оборудования здесь.
        // Для добавления используем server-side поиск, а для точечных операций — запрос по ID.
        equipmentList.value = []
        
        const addPriceRes = await additionalPricesAPI.getAdditionalPrices()
        additionalPrices.value = addPriceRes

        try {
            manufacturers.value = await manufacturersAPI.getManufacturers()
        } catch (e) {
            console.error('Failed to load manufacturers:', e)
            manufacturers.value = []
        }
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const handleFilterChange = () => {
    currentPage.value = 1
    loadData()
}

const handleDialogClose = () => {
    dialogVisible.value = false
}

// Handle tab change - automatically refresh equipment prices when switching to equipment tab
const handleTabChange = async (tabName: string) => {
    // Если переключились на вкладку "Оборудование" и есть оборудование в списке
    if (tabName === 'equipment' && selectedEquipment.value.length > 0 && dialogVisible.value) {
        try {
            // Автоматически обновить цены из карточек оборудования при переключении на вкладку
            // Это обеспечит отображение актуальных данных в таблице
            await refreshEquipmentPricesSilently()
        } catch (e) {
            // Игнорируем ошибки при автоматическом обновлении, чтобы не мешать пользователю
            console.warn('Не удалось автоматически обновить цены из карточек:', e)
        }
    }
}

const handleCreate = () => {
    editingProposalId.value = null
    dialogVisible.value = true
}



const handleSearch = () => { currentPage.value = 1; loadData() }
const handlePageChange = () => loadData()

// --- Exchange Rate Logic ---
const hasCurrency = (curr: string) => internalExchangeRates.value.some(r => r.currency === curr)

// Computed: Unique currencies used in equipment (excluding KZT)
const activeCurrencies = computed(() => {
    const currencies = new Set<string>()
    selectedEquipment.value.forEach(row => {
        if (row.currency && row.currency !== 'KZT') {
            currencies.add(row.currency)
        }
    })
    return Array.from(currencies)
})

// Computed: Filtered internal rates based on active currencies
const displayedExchangeRates = computed(() => {
    return internalExchangeRates.value
})

const handleCurrencyTicketChange = (val: string) => {
    if (val !== 'KZT' && !hasCurrency(val)) {
        const rate = getLiveRate(val)
        internalExchangeRates.value.push({
            currency: val,
            current_nb_rate: rate,
            creation_nb_rate: rate,
            internal_rate: rate,
            rate_date: new Date().toISOString().split('T')[0]
        })
    }
    // Update formData.exchange_rate
    if (val === 'KZT') {
        formData.exchange_rate = '1'
        formData.exchange_rate_date = undefined
    } else {
        formData.exchange_rate = getRate(val).toString()
    }
}

// Helper to get live rate
const getLiveRate = (currency: string) => {
   const rateObj = liveRates.value.find(r => r.currency_from === currency && r.currency_to === 'KZT')
   return rateObj ? parseFloat(rateObj.rate_value) : 1
}

// Watcher: Auto-add missing currencies
watch(activeCurrencies, (newCurrencies) => {
    newCurrencies.forEach(currency => {
        if (!hasCurrency(currency)) {
             const rate = getLiveRate(currency)
             internalExchangeRates.value.push({
                currency: currency,
                current_nb_rate: rate, // Live rate for display
                creation_nb_rate: rate, // Snapshot rate at creation
                internal_rate: rate, // Edtiable internal rate
                rate_date: new Date().toISOString().split('T')[0]
            })
        }
    })
}, { deep: true, immediate: true })

const addCurrency = () => {
    if(!hasCurrency(newCurrency.value)) {
        const rate = getLiveRate(newCurrency.value)
        internalExchangeRates.value.push({
            currency: newCurrency.value,
            current_nb_rate: rate, 
            creation_nb_rate: rate,
            internal_rate: rate,
            rate_date: new Date().toISOString().split('T')[0]
        })
    }
    showAddCurrencyDialog.value = false
}
const removeCurrency = (idx: number) => {
    internalExchangeRates.value.splice(idx, 1)
}
const getRate = (curr: string) => {
    if (curr === 'KZT') return 1
    const r = internalExchangeRates.value.find(x => x.currency === curr)
    return r ? r.internal_rate : 1 // fallback
}

// --- Equipment Logic ---
// Поиск оборудования переведён на server-side: fetchEquipmentSearch()

// Флаг для предотвращения двойного вызова
let isSelectingEquipment = false

const selectEquipment = (equip: Equipment) => {
    // Защита от двойного вызова
    if (isSelectingEquipment) {
        return
    }
    isSelectingEquipment = true
    
    try {
        // Проверяем, не добавлено ли уже это оборудование
        const alreadyExists = selectedEquipment.value.some(
            item => item.equipment_id === equip.equipment_id
        )
        
        if (alreadyExists) {
            ElMessage.warning('Это оборудование уже добавлено в список')
            return
        }
        
        selectedEquipment.value.push({
            equipment_id: equip.equipment_id,
            equipment_name: equip.equipment_name,
            equipment_manufacture_price: Number(equip.equipment_manufacture_price) || 0,
            equipment_price_currency_type: equip.equipment_price_currency_type || 'KZT',
            sale_price_kzt: equip.sale_price_kzt ? Number(equip.sale_price_kzt) : undefined,
            production_price: Number(equip.equipment_manufacture_price) || 0,
            currency: equip.equipment_price_currency_type || 'KZT',
            quantity: 1,
            row_expenses: [],
            // Set purchase price fields for correct calculation with internal rate
            purchase_price_original: Number(equip.equipment_manufacture_price) || 0,
            purchase_price_currency: equip.equipment_price_currency_type || 'KZT'
        })
        ElMessage.success('Оборудование добавлено')
    } finally {
        // Сбрасываем флаг через небольшую задержку
        setTimeout(() => {
            isSelectingEquipment = false
        }, 300)
    }
}

const removeEquipment = (idx: number) => {
    selectedEquipment.value.splice(idx, 1)
}

// Internal function to update equipment prices (without messages)
const updateEquipmentPricesFromCards = async (showMessages: boolean = true) => {
    if (selectedEquipment.value.length === 0) {
        if (showMessages) {
            ElMessage.warning('Нет оборудования для обновления')
        }
        return
    }
    
    refreshingPrices.value = true
    try {
        // Load all equipment data from API
        const equipmentIds = selectedEquipment.value.map(row => row.equipment_id)
        const equipmentPromises = equipmentIds.map(id => equipmentAPI.getEquipmentById(id))
        const equipmentDataList = await Promise.all(equipmentPromises)
        
        // Create a map for quick lookup
        const equipmentMap = new Map(equipmentDataList.map(eq => [eq.equipment_id, eq]))
        
        // Update each row with fresh data from equipment cards
        selectedEquipment.value.forEach(row => {
            const equipmentData = equipmentMap.get(row.equipment_id)
            if (equipmentData) {
                // Update sale_price_kzt (priority: from equipment card)
                if (equipmentData.sale_price_kzt) {
                    row.sale_price_kzt = parseFloat(equipmentData.sale_price_kzt as unknown as string)
                } else {
                    row.sale_price_kzt = undefined
                }
                
                // Update manufacture price and currency
                const newManufacturePrice = parseFloat(equipmentData.equipment_manufacture_price as unknown as string) || 0
                const newCurrency = equipmentData.equipment_price_currency_type || 'KZT'
                
                row.equipment_manufacture_price = newManufacturePrice
                row.equipment_price_currency_type = newCurrency
                row.production_price = newManufacturePrice
                row.currency = newCurrency
                
                // Update purchase price fields
                row.purchase_price_original = newManufacturePrice
                row.purchase_price_currency = newCurrency
                
                // IMPORTANT: Clear calculated fields from saved calculated_data to force recalculation
                // This ensures that values are recalculated based on fresh equipment data
                row.purchase_price_kzt = undefined
                row.base_cost_kzt = undefined
                row.margin_kzt = undefined
                row.margin_percentage = undefined
                row.allocated_overhead_per_unit = undefined
            }
        })
        
        if (showMessages) {
            ElMessage.success(`Цены обновлены для ${equipmentDataList.length} единиц оборудования`)
        }
    } catch (error: any) {
        console.error('Failed to refresh equipment prices:', error)
        if (showMessages) {
            ElMessage.error('Ошибка при обновлении цен из карточек оборудования')
        }
    } finally {
        refreshingPrices.value = false
    }
}

// Refresh equipment prices from equipment cards (with messages)
const refreshEquipmentPrices = async () => {
    await updateEquipmentPricesFromCards(true)
}

// Refresh equipment prices silently (without messages) - for automatic updates
const refreshEquipmentPricesSilently = async () => {
    await updateEquipmentPricesFromCards(false)
}

const handleExportProposalEquipment = async () => {
    if (selectedEquipment.value.length === 0) {
        ElMessage.warning('Список оборудования пуст')
        return
    }
    
    try {
        exportingProposalEquipment.value = true
        
        // Prepare items with all calculated values matching the CP settings
        const itemsToExport = selectedEquipment.value.map(row => {
            const purchasePriceOriginal = row.purchase_price_original !== undefined 
                ? row.purchase_price_original 
                : row.production_price
                
            return {
                equipment_name: row.equipment_name,
                purchase_price_original: purchasePriceOriginal,
                purchase_price_currency: row.purchase_price_currency || row.currency,
                purchase_price_kzt: calculatePurchasePriceKZT(row),
                sale_price_kzt: row.sale_price_kzt,
                quantity: row.quantity,
                margin_percentage: calculateMarginPercentage(row),
                margin_kzt: calculateMarginKZT(row),
                total_expenses_kzt: calculateTotalExpensesKZT(row),
                row_expenses: row.row_expenses
            }
        })
        
        const data = await equipmentAPI.exportProposalEquipmentToExcel(
            itemsToExport, 
            netAdjustmentPercentage.value
        )
        
        const url = window.URL.createObjectURL(new Blob([data]))
        const link = document.createElement('a')
        link.href = url
        
        const cpNumber = formData.outcoming_number ? `_${formData.outcoming_number}` : ''
        link.setAttribute('download', `оборудование_КП${cpNumber}.xlsx`)
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        ElMessage.success('Данные оборудования КП успешно экспортированы в Excel')
    } catch (error: any) {
        ElMessage.error(error.response?.data?.message || 'Ошибка экспорта оборудования в Excel')
        console.error('Export CP equipment error:', error)
    } finally {
        exportingProposalEquipment.value = false
    }
}

// Перемещение оборудования вверх/вниз
const moveEquipmentUp = (index: number) => {
    if (index > 0) {
        const item = selectedEquipment.value[index]
        if (item) {
            selectedEquipment.value.splice(index, 1)
            selectedEquipment.value.splice(index - 1, 0, item)
        }
    }
}

const moveEquipmentDown = (index: number) => {
    if (index < selectedEquipment.value.length - 1) {
        const item = selectedEquipment.value[index]
        if (item) {
            selectedEquipment.value.splice(index, 1)
            selectedEquipment.value.splice(index + 1, 0, item)
        }
    }
}

// Row Expenses
const openRowExpenseDialog = (row: EquipmentRow) => {
    currentRowRow.value = row
    currentRowExpense.name = ''
    currentRowExpense.value = 0
    showRowExpenseDialog.value = true
}
const addRowExpense = () => {
    if(currentRowRow.value) {
        currentRowRow.value.row_expenses.push({ ...currentRowExpense })
        showRowExpenseDialog.value = false
    }
}

const removeRowExpense = (row: EquipmentRow, index: number) => {
    if (row.row_expenses && row.row_expenses.length > index) {
        row.row_expenses.splice(index, 1)
    }
}

// Per Row Calculation
const calculateRowExpensesSum = (row: EquipmentRow) => {
    return row.row_expenses.reduce((sum, exp) => sum + exp.value, 0)
}

// Calculate purchase price in KZT
// Calculate purchase price in KZT using internal rate from "Курс валют" tab
// Always calculates dynamically using current internal_rate from internalExchangeRates
const calculatePurchasePriceKZT = (row: EquipmentRow): number => {
    // Get purchase price in original currency
    // Use purchase_price_original if available, otherwise use production_price
    const purchasePriceOriginal = row.purchase_price_original !== undefined 
        ? row.purchase_price_original 
        : row.production_price
    
    // Get currency (purchase_price_currency or fallback to currency)
    const currency = row.purchase_price_currency || row.currency
    
    // If currency is KZT, no conversion needed
    if (currency === 'KZT') {
        return purchasePriceOriginal
    }
    
    // Get internal rate from internalExchangeRates (editable rate from "Курс валют" tab)
    // This rate is set by user in the "Курс валют" tab and stored in internalExchangeRates
    // Always use current internal_rate, not saved purchase_price_kzt
    const internalRate = getRate(currency) // This uses internal_rate from internalExchangeRates
    
    // Convert to KZT: purchase_price_original * internal_rate
    return purchasePriceOriginal * internalRate
}

// Calculate base cost (purchase price + row expenses) in KZT
// This is used for margin percentage calculation (denominator)
// Note: allocated_overhead is NOT included in base_cost for percentage calculation
const calculateBaseCostKZT = (row: EquipmentRow): number => {
    // If we have base_cost_kzt from data_package, use it (already calculated with correct rate)
    if (row.base_cost_kzt !== undefined) {
        return row.base_cost_kzt
    }
    
    // Otherwise, calculate: purchase price (converted to KZT using internal rate) + row expenses per unit
    const purchasePriceKZT = calculatePurchasePriceKZT(row)
    const rowExpensesPerUnit = row.quantity > 0 ? calculateRowExpensesSum(row) / row.quantity : 0
    return purchasePriceKZT + rowExpensesPerUnit
}

// --- Final Calculation Computed Properties ---

// 1. Raw Equipment Price KZT (sum of (rounded sale_price_kzt) * quantity)
const totalRawEquipmentPriceKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => {
        if (row.sale_price_kzt !== undefined && row.sale_price_kzt !== null) {
            const roundedUnitPrice = Math.round(row.sale_price_kzt)
            return sum + (roundedUnitPrice * row.quantity)
        }
        return sum
    }, 0)
})

// 2. Adjusted Equipment Price KZT (sum of (rounded adjusted_unit_price) * quantity)
const totalAdjustedEquipmentPriceKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => {
        if (row.sale_price_kzt !== undefined && row.sale_price_kzt !== null) {
            const adjustedUnitPriceKZT = Math.round(row.sale_price_kzt * (1 + netAdjustmentPercentage.value / 100))
            return sum + (adjustedUnitPriceKZT * row.quantity)
        }
        return sum
    }, 0)
})

// 3. Adjustment Amount KZT (The difference)
const totalAdjustmentAmountKZT = computed(() => {
    return totalAdjustedEquipmentPriceKZT.value - totalRawEquipmentPriceKZT.value
})

// 4. Additional Services KZT
const totalAdditionalServicesKZT = computed(() => {
    if (!formData.additional_services) return 0
    return formData.additional_services.reduce((sum, svc) => sum + Math.round(Number(svc.price || 0)), 0)
})

// 5. Final Grand Total KZT
const calculatedTotalPriceKZT = computed(() => {
    return totalAdjustedEquipmentPriceKZT.value + totalAdditionalServicesKZT.value
})

// --- Target Currency Values (calculated per-item to ensure sum of parts matches total) ---
const targetRate = computed(() => getRate(formData.currency_ticket))

const totalRawEquipmentPriceTarget = computed(() => {
    if (formData.currency_ticket === 'KZT') return totalRawEquipmentPriceKZT.value
    if (targetRate.value <= 0) return 0
    
    return selectedEquipment.value.reduce((sum, row) => {
        if (row.sale_price_kzt !== undefined && row.sale_price_kzt !== null) {
            // Round the UNIT PRICE in target currency first
            const unitPriceTarget = Math.round(row.sale_price_kzt / targetRate.value)
            return sum + (unitPriceTarget * row.quantity)
        }
        return sum
    }, 0)
})

const totalAdjustedEquipmentPriceTarget = computed(() => {
    if (formData.currency_ticket === 'KZT') return totalAdjustedEquipmentPriceKZT.value
    if (targetRate.value <= 0) return 0
    
    return selectedEquipment.value.reduce((sum, row) => {
        if (row.sale_price_kzt !== undefined && row.sale_price_kzt !== null) {
            // Round the ADJUSTED UNIT PRICE in target currency first
            const adjustedUnitPriceKZT = Math.round(row.sale_price_kzt * (1 + netAdjustmentPercentage.value / 100))
            const adjustedUnitPriceTarget = Math.round(adjustedUnitPriceKZT / targetRate.value)
            return sum + (adjustedUnitPriceTarget * row.quantity)
        }
        return sum
    }, 0)
})

const totalAdjustmentAmountTarget = computed(() => {
    return totalAdjustedEquipmentPriceTarget.value - totalRawEquipmentPriceTarget.value
})

const totalAdditionalServicesTarget = computed(() => {
    if (formData.currency_ticket === 'KZT') return totalAdditionalServicesKZT.value
    if (targetRate.value <= 0 || !formData.additional_services) return 0
    return formData.additional_services.reduce((sum, svc) => {
        return sum + Math.round(Number(svc.price || 0) / targetRate.value)
    }, 0)
})

const calculatedTotalPrice = computed(() => {
    return totalAdjustedEquipmentPriceTarget.value + totalAdditionalServicesTarget.value
})

// Legacy support if used elsewhere
const totalSalePriceKZT = totalAdjustedEquipmentPriceKZT
const totalAdjustmentValueKZT = totalAdjustmentAmountKZT

// Calculate allocated overhead per unit for this row
// Overhead is distributed proportionally to base costs
const calculateAllocatedOverheadPerUnit = (row: EquipmentRow): number => {
    // Calculate total base cost for all equipment (for distribution weight)
    const totalBaseCost = selectedEquipment.value.reduce((sum, r) => {
        const baseCost = calculateBaseCostKZT(r)
        return sum + (baseCost * r.quantity)
    }, 0)
    
    if (totalBaseCost <= 0) return 0
    
    // Calculate this row's base cost
    const rowBaseCost = calculateBaseCostKZT(row)
    const rowBaseTotal = rowBaseCost * row.quantity
    
    // Calculate weight (proportion of this row's base cost to total)
    const weight = rowBaseTotal / totalBaseCost
    
    // Get total global overhead (from additional_price_ids)
    const globalOverhead = totalGlobalExpensesKZT.value
    
    // Allocate overhead proportionally
    const allocatedOverheadTotal = globalOverhead * weight
    const allocatedOverheadPerUnit = row.quantity > 0 ? allocatedOverheadTotal / row.quantity : 0
    
    return allocatedOverheadPerUnit
}

// Calculate total expenses per unit (row expenses + allocated overhead) in KZT
const calculateTotalExpensesKZT = (row: EquipmentRow): number => {
    // Row expenses per unit
    const rowExpensesPerUnit = row.quantity > 0 ? calculateRowExpensesSum(row) / row.quantity : 0
    
    // Calculate allocated overhead dynamically based on current global expenses
    // This ensures margin recalculates when global expenses change
    const allocatedOverhead = calculateAllocatedOverheadPerUnit(row)
    
    return rowExpensesPerUnit + allocatedOverhead
}

// Calculate margin in KZT
// Formula: Margin = Sale Price - (Purchase Price + Total Expenses)
// Where Total Expenses = Row Expenses + Allocated Overhead
// Note: Always recalculates to reflect current global expenses
const calculateMarginKZT = (row: EquipmentRow): number => {
    // Always recalculate to ensure margin updates when global expenses change
    // Don't use saved margin_kzt as it may be outdated
    if (!row.sale_price_kzt) return 0
    
    const purchasePriceKZT = calculatePurchasePriceKZT(row)
    const totalExpensesKZT = calculateTotalExpensesKZT(row)
    
    const adjustedSalePrice = Math.round(row.sale_price_kzt * (1 + netAdjustmentPercentage.value / 100))
    return adjustedSalePrice - purchasePriceKZT - totalExpensesKZT
}

// Calculate margin percentage
// Formula: Margin % = (Margin KZT / Base Cost KZT) * 100
// Where Base Cost KZT = Purchase Price KZT + Row Expenses per unit (WITHOUT allocated_overhead)
// This matches backend formula: margin_percentage = (margin_kzt_per_unit / base_unit_cost_kzt) * 100
const calculateMarginPercentage = (row: EquipmentRow): number => {
    // If we have margin_percentage from data_package, use it (already calculated correctly)
    if (row.margin_percentage !== undefined) {
        return row.margin_percentage
    }
    
    // Otherwise, calculate from margin and base cost
    // Base cost should NOT include allocated_overhead for percentage calculation
    const baseCostKZT = calculateBaseCostKZT(row)
    if (baseCostKZT <= 0) return 0
    
    const marginKZT = calculateMarginKZT(row)
    // Formula: (margin_kzt / base_cost_kzt) * 100
    // This matches backend calculation
    return (marginKZT / baseCostKZT) * 100
}

const calculateRowTotal = (row: EquipmentRow) => {
    const rate = getRate(row.currency)
    const baseCostKZT = row.production_price * rate * row.quantity
    const expensesKZT = calculateRowExpensesSum(row) 
    return baseCostKZT + expensesKZT
}

// Overall Calculation
const totalEquipmentCostKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => sum + calculateRowTotal(row), 0)
})

const totalGlobalExpensesKZT = computed(() => {
    if (!formData.additional_price_ids) return 0
    
    let sum = 0
    formData.additional_price_ids.forEach(id => {
        const ap = additionalPrices.value.find(p => p.price_id === id)
        if (ap) {
            const val = Number(ap.price_parameter_value)
            if (ap.value_type === 'percentage') {
                sum += (totalEquipmentCostKZT.value * val / 100)
            } else {
                sum += val
            }
        }
    })
    return sum
})

const netCostKZT = computed(() => totalEquipmentCostKZT.value + totalGlobalExpensesKZT.value)

// Calculate total margin KZT (sum of all equipment margins)
const totalMarginKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => {
        const marginPerUnit = calculateMarginKZT(row)
        return sum + (marginPerUnit * row.quantity)
    }, 0)
})

// Calculate total margin percentage
// Formula: Total Margin % = (Total Margin KZT / Total Sale Price KZT) * 100
// Маржа рассчитывается только от оборудования, без учета дополнительных услуг
const totalMarginPercentage = computed(() => {
    const totalSalePrice = totalSalePriceKZT.value
    
    if (totalSalePrice <= 0) return 0
    return (totalMarginKZT.value / totalSalePrice) * 100
})



const handleEdit = (row: CommercialProposal) => {
    editingProposalId.value = row.proposal_id
    dialogVisible.value = true
}

// Маржа теперь рассчитывается автоматически на бэкенде
// calculateFinalProposalPrice и marginKZT больше не нужны

// Submit
const handleSubmit = async () => {
    if(!formRef.value) return
    await formRef.value.validate(async (valid, fields) => {
        if(valid) {
            submitting.value = true
            try {
                // Итоговая цена и маржа рассчитываются автоматически на бэкенде
                // на основе sale_price_kzt оборудования
                // Если total_price не указан, бэкенд рассчитает его автоматически

                // Prepare full payload
                const payload = { ...formData }
                
                // Remove margin fields - они теперь рассчитываются автоматически на бэкенде
                delete payload.margin_value
                delete payload.margin_percentage
                
                // Set calculated total price (sum of sale prices + additional services)
                // Ensure it's a valid number
                const totalPrice = calculatedTotalPrice.value
                if (isNaN(totalPrice) || !isFinite(totalPrice) || totalPrice < 0) {
                    ElMessage.error('Некорректная итоговая цена. Проверьте цены оборудования.')
                    submitting.value = false
                    return
                }
                payload.total_price = totalPrice.toFixed(2) // Format to 2 decimal places
                
                // Auto-increment version if editing
                if (isEditMode.value) {
                    payload.proposal_version = (payload.proposal_version || 1) + 1
                }

                // Update exchange_rate to the latest from the selected currency
                payload.exchange_rate = getRate(formData.currency_ticket).toString()

                // Add internal exchange rates snapshot
                payload.internal_exchange_rates = internalExchangeRates.value

                // Add equipment items with calculated_data
                if (selectedEquipment.value.length > 0) {
                    payload.equipment_items = selectedEquipment.value.map(item => {
                        // Calculate values robustly
                        const pPriceKZT = calculatePurchasePriceKZT(item)
                        const bCostKZT = calculateBaseCostKZT(item)
                        const margKZT = calculateMarginKZT(item)
                        const margPercentage = calculateMarginPercentage(item)
                        
                        // Helper to ensure we don't send NaN or Infinity
                        const safeNum = (val: any) => {
                            const n = Number(val)
                            return (isNaN(n) || !isFinite(n)) ? null : n
                        }

                        return {
                            equipment_id: item.equipment_id,
                            quantity: item.quantity,
                            row_expenses: item.row_expenses || [],
                            calculated_data: {
                                purchase_price_kzt: safeNum(pPriceKZT),
                                base_cost_kzt: safeNum(bCostKZT),
                                allocated_overhead_per_unit: safeNum(item.allocated_overhead_per_unit) || 0,
                                margin_kzt: safeNum(margKZT),
                                margin_percentage: safeNum(margPercentage)
                            }
                        }
                    })
                }

                // Add payments with string values
                if (tempPayments.value.length > 0) {
                    (payload as any).payment_logs = tempPayments.value.map(p => ({
                        payment_name: p.payment_name,
                        payment_value: p.payment_value.toString(),
                        payment_date: p.payment_date,
                        comments: p.comments
                    }))
                }

                // Clean up adjustments to prevent "multiple values for keyword argument 'proposal'"
                if (payload.adjustments && payload.adjustments.length > 0) {
                    payload.adjustments = payload.adjustments.map(adj => {
                        const { id, proposal, created_at, author_name, ...rest } = adj as any
                        // Only send ID if it exists (for updates), otherwise let backend create it
                        const cleaned: any = { ...rest }
                        if (id) cleaned.id = id
                        return cleaned
                    })
                }

                if (isEditMode.value && formData.proposal_id) { 
                     await proposalsAPI.updateProposal(formData.proposal_id, payload)
                     ElMessage.success('КП успешно обновлено')
                } else {
                     await proposalsAPI.createProposal(payload)
                     ElMessage.success('КП успешно создано')
                }

                dialogVisible.value = false
                loadData()
            } catch(e: any) {
                console.error(e)
                let msg = e.message
                if (e.response?.data) {
                    const formatError = (errorData: any): string => {
                        if (typeof errorData === 'string') {
                            return errorData
                        }
                        if (Array.isArray(errorData)) {
                            return errorData.map(item => typeof item === 'object' ? formatError(item) : item).join(', ')
                        }
                        if (typeof errorData === 'object' && errorData !== null) {
                            return Object.entries(errorData)
                                .map(([key, val]) => {
                                    const formattedVal = typeof val === 'object' ? formatError(val) : val
                                    return `${key}: ${formattedVal}`
                                })
                                .join('; ')
                        }
                        return String(errorData)
                    }
                    
                    if (typeof e.response.data === 'object') {
                        msg = formatError(e.response.data)
                    } else {
                        msg = JSON.stringify(e.response.data)
                    }
                }
                ElMessage.error(`Ошибка при сохранении КП: ${msg}`)
            } finally {
                submitting.value = false
            }
        } else {
            console.warn('Validation failed:', fields)
            ElMessage.warning('Пожалуйста, заполните все обязательные поля корректно')
            
            // Switch to basic tab if main fields have errors
            if (fields && (fields.proposal_name || fields.outcoming_number || fields.deal_id || fields.client_id)) {
                activeTab.value = 'basic'
            }
        }
    })
}

// --- Utils ---
const formatDate = (d: string) => d ? format(new Date(d), 'dd.MM.yyyy') : ''
const getStatusTagType = (status: string) => {
    const map: Record<string, string> = { draft: 'info', sent: 'warning', accepted: 'success', completed: 'success', rejected: 'danger' }
    return map[status] || 'info'
}
const getStatusLabel = (s: string) => s 

// Additional Prices
const loadAdditionalPrices = async () => {
    loadingAdditionalPrices.value = true
    try {
        const res = await additionalPricesAPI.getAdditionalPrices()
        additionalPrices.value = res
    } finally {
        loadingAdditionalPrices.value = false
    }
}
const handleCreateAdditionalPrice = () => {
    // simplified
    showAdditionalPriceFormDialog.value = true
}
const handleSubmitAdditionalPrice = async () => {
    // simplified
    try {
        await additionalPricesAPI.createAdditionalPrice({
            price_parameter_name: additionalPriceForm.price_parameter_name,
            expense_type: 'other', // default
            value_type: additionalPriceForm.value_type as any,
            price_parameter_value: String(additionalPriceForm.price_parameter_value)
        })
        showAdditionalPriceFormDialog.value = false
        loadAdditionalPrices()
    } catch (e) { console.error(e) }
}
const handleDeleteAdditionalPrice = async (row: AdditionalPrice) => {
    await additionalPricesAPI.deleteAdditionalPrice(row.price_id)
    loadAdditionalPrices()
}
const handleCopy = async (row: CommercialProposal) => {
    try {

        await ElMessageBox.confirm(
            `Вы уверены, что хотите создать копию КП "${row.outcoming_number}"?`,
            'Подтверждение копирования',
            {
                confirmButtonText: 'Да',
                cancelButtonText: 'Нет',
                type: 'info',
            }
        )

        await proposalsAPI.copyProposal(row.proposal_id)
        ElMessage.success('Копия коммерческого предложения успешно создана')
        loadData()
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Failed to copy proposal:', error)
            ElMessage.error('Не удалось создать копию коммерческого предложения')
        }
    }
}

// Additional Services Methods
const openAdditionalServicesDialog = () => {
    currentAdditionalService.name = ''
    currentAdditionalService.price = 0
    currentAdditionalService.description = ''
    showAdditionalServicesDialog.value = true
}

const addAdditionalService = () => {
    if (!currentAdditionalService.name) {
        ElMessage.warning('Введите название услуги')
        return
    }
    if (!formData.additional_services) {
        formData.additional_services = []
    }
    // We push a copy
    formData.additional_services.push({ ...currentAdditionalService })
    showAdditionalServicesDialog.value = false
    
    // Auto-update total price if needed (per requirement: real-time update)
    // We can call calculateFinalProposalPrice or a lighter version
    updateTotalPriceWithServices()
}

const removeAdditionalService = (index: number) => {
    if (formData.additional_services) {
        formData.additional_services.splice(index, 1)
        updateTotalPriceWithServices()
    }
}

const updateTotalPriceWithServices = () => {
    // Only update if we already have a valid calculation
    // Base calculation: NetCost + Margin
    // Итоговая цена теперь рассчитывается автоматически на бэкенде
    // на основе sale_price_kzt оборудования
    // Если total_price не указан, бэкенд рассчитает его автоматически
}

const handleDelete = async (row: CommercialProposal) => {
    try {
        await ElMessageBox.confirm(
            'Вы уверены, что хотите архивировать это КП? Оно перестанет отображаться в общем списке.',
            'Подтверждение архивации',
            {
                confirmButtonText: 'Архивировать',
                cancelButtonText: 'Отмена',
                type: 'warning',
            }
        )
        await proposalsAPI.deleteProposal(row.proposal_id)
        ElMessage.success('КП успешно архивировано')
        loadData()
    } catch (e) {
        // cancel
    }
}

// Open equipment card dialog
const openEquipmentCardDialog = async (equipmentId: number) => {
    equipmentCardDialogVisible.value = true
    loadingEquipmentCard.value = true
    currentEquipmentCard.value = null
    
    try {
        const equipment = await equipmentAPI.getEquipmentById(equipmentId)
        currentEquipmentCard.value = equipment
    } catch (error: any) {
        console.error('Failed to load equipment card:', error)
        ElMessage.error('Не удалось загрузить данные оборудования')
        currentEquipmentCard.value = null
    } finally {
        loadingEquipmentCard.value = false
    }
}

// Close equipment card dialog
const closeEquipmentCardDialog = () => {
    equipmentCardDialogVisible.value = false
    currentEquipmentCard.value = null
}

// Get image preview list for el-image component (use proxy for Drive/Yandex to avoid 403)
const getImagePreviewList = (): string[] => {
    if (!currentEquipmentCard.value?.equipment_imagelinks) return []
    return currentEquipmentCard.value.equipment_imagelinks.map((img: any) => 
        getImageSrc(typeof img === 'string' ? img : img.url)
    ).filter(Boolean)
}

onMounted(async () => {
    await loadData()
    
    // Check if we need to open edit modal from query parameter
    const editId = route.query.edit
    if (editId) {
        const proposalId = parseInt(editId as string)
        if (!isNaN(proposalId)) {
            // Find the proposal in the list
            const proposal = proposalsList.value.find(p => p.proposal_id === proposalId)
            if (proposal) {
                // Wait a bit for the component to be fully mounted
                await nextTick()
                handleEdit(proposal)
                // Remove query parameter from URL
                router.replace({ query: {} })
            }
        }
    }
})

// Equipment search: load first page when dialog opens
watch(showAddEquipmentDialog, (isOpen) => {
    if (isOpen) {
        equipmentSearchPage.value = 1
        fetchEquipmentSearch(1)
    } else {
        equipmentSearchQuery.value = ''
        equipmentSearchResults.value = []
        equipmentSearchTotal.value = 0
        equipmentSearchPage.value = 1
    }
})

// Equipment search: debounce input (server-side)
watch(equipmentSearchQuery, () => {
    if (!showAddEquipmentDialog.value) return
    if (equipmentSearchTimeout) clearTimeout(equipmentSearchTimeout)
    equipmentSearchTimeout = setTimeout(() => {
        fetchEquipmentSearch(1)
    }, 300)
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters { margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.text-gray-400 { color: #9ca3af; }
.expense-tag-container { display: flex; align-items: center; margin-bottom: 4px; }
.expense-tag { font-size: 0.85em; background: #f3f4f6; padding: 2px 6px; border-radius: 4px; flex: 1; }
.calculation-summary-container { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
.summary-card { flex: 1; min-width: 450px; max-width: 600px; }
.summary-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
.margin-block { width: 100%; }
.w-100 { width: 100%; }
.mr-2 { margin-right: 8px; }
.final-price-display { margin-top: 20px; font-size: 1.2em; border-top: 1px solid #eba4a4; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; color: #F56C6C; }
.client-select-row { display: flex; align-items: center; gap: 8px; width: 100%; }
.client-select-row .el-select { flex: 1; min-width: 0; }
.bitrix-search-btn { flex-shrink: 0; }
.option-meta { color: #909399; font-size: 12px; }

/* Styles for Adjustments */
.adjustment-row .label { font-weight: 500; }
.adjustment-row .value { font-weight: bold; }
.price-value { color: #409EFF; }
.main-total { color: #F56C6C; font-size: 1.3em; }
.target-total { color: #67C23A; font-size: 1.1em; font-weight: bold; }
</style>
