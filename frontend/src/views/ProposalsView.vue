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
              placeholder="Поиск по названию или номеру КП..."
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
        <el-table-column prop="proposal_date" label="Дата КП" width="120" sortable>
          <template #default="{ row }">
            {{ formatDate(row.proposal_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_price" label="Итоговая цена" width="150" sortable>
          <template #default="{ row }">
            {{ formatPrice(convertCurrency(row.total_price, 'KZT', row.currency_ticket, parseFloat(row.exchange_rate || '1')), row.currency_ticket) }}
          </template>
        </el-table-column>
        <el-table-column prop="cost_price" label="Себестоимость" width="150" sortable>
          <template #default="{ row }">
            {{ row.cost_price ? formatPrice(convertCurrency(row.cost_price, 'KZT', row.currency_ticket, parseFloat(row.exchange_rate || '1')), row.currency_ticket) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="margin_percentage" label="Маржа %" width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="getMarginTagType(row.margin_percentage)">
              {{ row.margin_percentage ? `${row.margin_percentage}%` : '-' }}
            </el-tag>
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
        <el-table-column label="Действия" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              :icon="Download"
              @click="handleDownloadPDF(row)"
              circle
              title="Скачать PDF"
            />
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
              circle
              title="Редактировать"
            />
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              circle
              title="Удалить"
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

    <!-- Модальное окно создания/редактирования КП -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? 'Редактировать КП' : 'Создать КП'"
      width="1200px"
      @close="handleDialogClose"
    >
      <el-tabs v-model="activeTab">
        <!-- Основная информация -->
        <el-tab-pane label="Основная информация" name="basic">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="200px"
            label-position="left"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Название КП *" prop="proposal_name">
                  <el-input v-model="formData.proposal_name" placeholder="Введите название КП" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Номер КП *" prop="outcoming_number">
                  <el-input v-model="formData.outcoming_number" placeholder="Например: Исх. № 123 от 01.01.2025" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Клиент *" prop="client_id">
                  <el-select
                    v-model="formData.client_id"
                    filterable
                    placeholder="Выберите клиента"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="client in clients"
                      :key="client.client_id"
                      :label="client.client_name"
                      :value="client.client_id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Дата КП *" prop="proposal_date">
                  <el-date-picker
                    v-model="formData.proposal_date"
                    type="date"
                    placeholder="Выберите дату"
                    style="width: 100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Срок действия КП" prop="valid_until">
                  <el-date-picker
                    v-model="formData.valid_until"
                    type="date"
                    placeholder="Выберите дату"
                    style="width: 100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Статус *" prop="proposal_status">
                  <el-select v-model="formData.proposal_status" placeholder="Выберите статус" style="width: 100%">
                    <el-option label="Черновик" value="draft" />
                    <el-option label="Отправлено" value="sent" />
                    <el-option label="Принято" value="accepted" />
                    <el-option label="Отклонено" value="rejected" />
                    <el-option label="В переговорах" value="negotiating" />
                    <el-option label="Завершено" value="completed" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Время доставки" prop="delivery_time">
                  <el-input v-model="formData.delivery_time" placeholder="Например: 30-45 рабочих дней" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Гарантия" prop="warranty">
                  <el-input v-model="formData.warranty" placeholder="Например: 1 год после поставки" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="Комментарии" prop="comments">
              <el-input
                v-model="formData.comments"
                type="textarea"
                :rows="4"
                placeholder="Введите комментарии"
              />
            </el-form-item>

            <el-form-item label="Ссылка на Битрикс" prop="bitrix_lead_link">
              <el-input v-model="formData.bitrix_lead_link" placeholder="https://..." />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Цены и валюта -->
        <el-tab-pane label="Цены и валюта" name="pricing">
          <el-form
            :model="formData"
            label-width="200px"
            label-position="left"
          >
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="Валюта *" prop="currency_ticket">
                  <el-select v-model="formData.currency_ticket" placeholder="Выберите валюту" style="width: 100%">
                    <el-option label="KZT" value="KZT" />
                    <el-option label="USD" value="USD" />
                    <el-option label="EUR" value="EUR" />
                    <el-option label="RUB" value="RUB" />
                    <el-option label="CNY" value="CNY" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Курс валюты *" prop="exchange_rate">
                  <el-input-number
                    v-model="formData.exchange_rate"
                    :precision="6"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Дата курса" prop="exchange_rate_date">
                  <el-date-picker
                    v-model="formData.exchange_rate_date"
                    type="date"
                    placeholder="Выберите дату"
                    style="width: 100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="Итоговая цена *" prop="total_price">
                  <el-input-number
                    v-model="formData.total_price"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Себестоимость" prop="cost_price">
                  <el-input-number
                    v-model="formData.cost_price"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                    readonly
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Маржа %" prop="margin_percentage">
                  <el-input-number
                    v-model="formData.margin_percentage"
                    :precision="2"
                    :min="-100"
                    :max="1000"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20" style="margin-top: 20px">
              <el-col :span="24">
                <el-button type="primary" @click="calculateTotalPrice" :loading="calculatingTotalPrice">
                  <el-icon><Search /></el-icon>
                  Рассчитать итоговую цену
                </el-button>
              </el-col>
            </el-row>

            <el-alert
              v-if="formData.cost_price && formData.total_price"
              :title="`Маржа: ${calculateMargin(formData.total_price, formData.cost_price)}%`"
              type="info"
              :closable="false"
              style="margin-top: 20px"
            />
          </el-form>
        </el-tab-pane>

        <!-- Оборудование -->
        <el-tab-pane label="Оборудование" name="equipment">
          <div class="equipment-section">
            <div class="section-header">
              <h3>Оборудование в КП</h3>
              <el-button type="primary" size="small" @click="showAddEquipmentDialog = true">
                <el-icon><Plus /></el-icon>
                Добавить оборудование
              </el-button>
            </div>

            <!-- Дополнительные расходы -->
            <el-form
              :model="formData"
              label-width="200px"
              label-position="left"
              style="margin-top: 20px; margin-bottom: 20px"
            >
              <el-form-item label="Дополнительные расходы">
                <div style="display: flex; gap: 10px; width: 100%">
                  <el-select
                    v-model="formData.additional_price_ids"
                    placeholder="Выберите дополнительные расходы"
                    multiple
                    clearable
                    filterable
                    style="flex: 1"
                  >
                    <el-option
                      v-for="price in additionalPrices"
                      :key="price.price_id"
                      :label="`${price.price_parameter_name} (${price.price_parameter_value} ${price.value_type === 'percentage' ? '%' : price.value_type === 'fixed' ? 'KZT' : ''})`"
                      :value="price.price_id"
                    />
                  </el-select>
                  <el-button type="primary" @click="showAdditionalPriceDialog = true">
                    <el-icon><Plus /></el-icon>
                    Управление
                  </el-button>
                </div>
              </el-form-item>
            </el-form>

            <el-table :data="selectedEquipment" border style="width: 100%; margin-top: 15px">
              <el-table-column prop="equipment_name" label="Оборудование" min-width="200" />
              <el-table-column prop="quantity" label="Количество" width="120">
                <template #default="{ row, $index }">
                  <el-input-number
                    v-model="row.quantity"
                    :min="1"
                    @change="updateEquipmentQuantity($index, row.quantity)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="Себестоимость" width="150">
                <template #default="{ row }">
                  {{ row.cost ? formatPrice(convertCurrency(row.cost, 'KZT', formData.currency_ticket || 'KZT', parseFloat(formData.exchange_rate || '1')), formData.currency_ticket || 'KZT') : '-' }}
                </template>
              </el-table-column>
              <el-table-column label="Итого" width="150">
                <template #default="{ row }">
                  {{ row.total_cost ? formatPrice(convertCurrency(row.total_cost, 'KZT', formData.currency_ticket || 'KZT', parseFloat(formData.exchange_rate || '1')), formData.currency_ticket || 'KZT') : '-' }}
                </template>
              </el-table-column>
              <el-table-column label="Действия" width="150">
                <template #default="{ row, $index }">
                  <el-button
                    type="primary"
                    size="small"
                    @click="calculateEquipmentCost(row)"
                  >
                    Рассчитать
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="removeEquipment($index)"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Отмена</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEditMode ? 'Сохранить' : 'Создать' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Диалог добавления оборудования -->
    <el-dialog
      v-model="showAddEquipmentDialog"
      title="Добавить оборудование"
      width="800px"
    >
      <el-input
        v-model="equipmentSearchQuery"
        placeholder="Поиск оборудования..."
        style="margin-bottom: 15px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-table
        :data="filteredEquipment"
        max-height="400"
        @row-click="selectEquipment"
      >
        <el-table-column prop="equipment_name" label="Название" />
        <el-table-column prop="equipment_articule" label="Артикул" width="120" />
        <el-table-column label="Действие" width="100">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="selectEquipment(row)">
              Выбрать
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showAddEquipmentDialog = false">Отмена</el-button>
      </template>
    </el-dialog>

    <!-- Диалог управления дополнительными расходами -->
    <el-dialog
      v-model="showAdditionalPriceDialog"
      title="Управление дополнительными расходами"
      width="900px"
      @opened="loadAdditionalPrices"
    >
      <div style="margin-bottom: 15px">
        <el-button type="primary" @click="handleCreateAdditionalPrice">
          <el-icon><Plus /></el-icon>
          Создать
        </el-button>
      </div>

      <el-table :data="additionalPrices" border style="width: 100%" v-loading="loadingAdditionalPrices">
        <template #empty>
          <el-empty description="Нет дополнительных расходов" />
        </template>
        <el-table-column prop="price_parameter_name" label="Название" min-width="200" />
        <el-table-column prop="expense_type" label="Тип расхода" width="150">
          <template #default="{ row }">
            {{ getExpenseTypeLabel(row.expense_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="value_type" label="Тип значения" width="150">
          <template #default="{ row }">
            {{ getValueTypeLabel(row.value_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="price_parameter_value" label="Значение" width="120" />
        <el-table-column label="Действия" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEditAdditionalPrice(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteAdditionalPrice(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showAdditionalPriceDialog = false">Закрыть</el-button>
      </template>
    </el-dialog>

    <!-- Диалог создания/редактирования дополнительного расхода -->
    <el-dialog
      v-model="showAdditionalPriceFormDialog"
      :title="isEditAdditionalPriceMode ? 'Редактировать дополнительный расход' : 'Создать дополнительный расход'"
      width="600px"
    >
      <el-form
        ref="additionalPriceFormRef"
        :model="additionalPriceForm"
        :rules="additionalPriceFormRules"
        label-width="180px"
      >
        <el-form-item label="Название параметра *" prop="price_parameter_name">
          <el-input v-model="additionalPriceForm.price_parameter_name" placeholder="Введите название" />
        </el-form-item>
        <el-form-item label="Тип расхода *" prop="expense_type">
          <el-select v-model="additionalPriceForm.expense_type" placeholder="Выберите тип" style="width: 100%">
            <el-option label="Упаковка" value="packaging" />
            <el-option label="Труд" value="labor" />
            <el-option label="Амортизация" value="depreciation" />
            <el-option label="Сервис" value="service" />
            <el-option label="Склад" value="warehouse" />
            <el-option label="Другое" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="Тип значения *" prop="value_type">
          <el-select v-model="additionalPriceForm.value_type" placeholder="Выберите тип" style="width: 100%">
            <el-option label="Процент" value="percentage" />
            <el-option label="Фиксированная сумма" value="fixed" />
            <el-option label="Коэффициент" value="coefficient" />
          </el-select>
        </el-form-item>
        <el-form-item label="Значение *" prop="price_parameter_value">
          <el-input-number
            v-model="additionalPriceForm.price_parameter_value"
            :precision="2"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAdditionalPriceFormDialog = false">Отмена</el-button>
        <el-button type="primary" :loading="submittingAdditionalPrice" @click="handleSubmitAdditionalPrice">
          {{ isEditAdditionalPriceMode ? 'Сохранить' : 'Создать' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete, Search, Download } from '@element-plus/icons-vue'
import {
  proposalsAPI,
  additionalPricesAPI,
  type CommercialProposal,
  type CommercialProposalCreateData,
  type CommercialProposalResponse,
  type AdditionalPrice,
} from '@/api/proposals'
import { clientsAPI, type Client, type ClientsResponse } from '@/api/clients'
import { equipmentAPI, type Equipment, type EquipmentResponse } from '@/api/equipment'
import { costCalculationAPI } from '@/api/proposals'
import { format } from 'date-fns'
import { useAuthStore } from '@/stores/auth'

// State
const loading = ref(false)
const submitting = ref(false)
const proposalsList = ref<CommercialProposal[]>([])
const clients = ref<Client[]>([])
const equipmentList = ref<Equipment[]>([])
const additionalPrices = ref<AdditionalPrice[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEditMode = ref(false)
const currentProposalId = ref<number | null>(null)
const activeTab = ref('basic')
const formRef = ref<FormInstance>()
const showAddEquipmentDialog = ref(false)
const equipmentSearchQuery = ref('')
const selectedEquipment = ref<Array<{
  equipment_id: number
  equipment_name: string
  quantity: number
  cost?: number
  total_cost?: number
}>>([])
const showAdditionalPriceDialog = ref(false)
const showAdditionalPriceFormDialog = ref(false)
const isEditAdditionalPriceMode = ref(false)
const currentAdditionalPriceId = ref<number | null>(null)
const submittingAdditionalPrice = ref(false)
const loadingAdditionalPrices = ref(false)
const calculatingTotalPrice = ref(false)
const additionalPriceFormRef = ref<FormInstance>()
const additionalPriceForm = reactive({
  price_parameter_name: '',
  expense_type: '' as 'packaging' | 'labor' | 'depreciation' | 'service' | 'warehouse' | 'other',
  value_type: '' as 'percentage' | 'fixed' | 'coefficient',
  price_parameter_value: 0,
})
const additionalPriceFormRules: FormRules = {
  price_parameter_name: [{ required: true, message: 'Введите название параметра', trigger: 'blur' }],
  expense_type: [{ required: true, message: 'Выберите тип расхода', trigger: 'change' }],
  value_type: [{ required: true, message: 'Выберите тип значения', trigger: 'change' }],
  price_parameter_value: [{ required: true, message: 'Введите значение', trigger: 'blur' }],
}

const filters = reactive({
  client_id: null as number | null,
  proposal_status: null as string | null,
})

// Form data
const formData = reactive<CommercialProposalCreateData>({
  proposal_name: '',
  outcoming_number: '',
  client_id: 0,
  currency_ticket: 'KZT',
  exchange_rate: '1',
  additional_price_ids: [] as number[],
  total_price: '0',
  cost_price: '',
  margin_percentage: '',
  proposal_date: new Date().toISOString().split('T')[0],
  valid_until: '',
  delivery_time: '',
  warranty: '',
  proposal_status: 'draft',
  proposal_version: 1,
  comments: '',
  bitrix_lead_link: '',
})

// Form rules
const formRules: FormRules = {
  proposal_name: [{ required: true, message: 'Введите название КП', trigger: 'blur' }],
  outcoming_number: [{ required: true, message: 'Введите номер КП', trigger: 'blur' }],
  client_id: [{ required: true, message: 'Выберите клиента', trigger: 'change' }],
  proposal_date: [{ required: true, message: 'Выберите дату КП', trigger: 'change' }],
  currency_ticket: [{ required: true, message: 'Выберите валюту', trigger: 'change' }],
  exchange_rate: [{ required: true, message: 'Введите курс валюты', trigger: 'blur' }],
  total_price: [{ required: true, message: 'Введите итоговую цену', trigger: 'blur' }],
  proposal_status: [{ required: true, message: 'Выберите статус', trigger: 'change' }],
}

// Computed
const filteredEquipment = computed(() => {
  if (!equipmentSearchQuery.value) return equipmentList.value
  const query = equipmentSearchQuery.value.toLowerCase()
  return equipmentList.value.filter(
    (eq) =>
      eq.equipment_name.toLowerCase().includes(query) ||
      eq.equipment_articule?.toLowerCase().includes(query)
  )
})

const authStore = useAuthStore()

// Methods
const loadProposals = async () => {
  try {
    loading.value = true
    const params: any = {
      page: currentPage.value,
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    if (filters.client_id) {
      params.client_id = filters.client_id
    }
    if (filters.proposal_status) {
      params.proposal_status = filters.proposal_status
    }

    const response: CommercialProposalResponse = await proposalsAPI.getProposals(params)

    if (Array.isArray(response)) {
      proposalsList.value = response
      total.value = response.length
    } else {
      proposalsList.value = response.results || []
      total.value = response.count || 0
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка загрузки КП')
    console.error('Load proposals error:', error)
  } finally {
    loading.value = false
  }
}

const loadClients = async () => {
  try {
    const response: ClientsResponse = await clientsAPI.getClients()
    if (Array.isArray(response)) {
      clients.value = response
    } else {
      clients.value = response.results || []
    }
  } catch (error) {
    console.error('Load clients error:', error)
  }
}

const loadEquipment = async () => {
  try {
    const response: EquipmentResponse = await equipmentAPI.getEquipment()
    if (Array.isArray(response)) {
      equipmentList.value = response
    } else {
      equipmentList.value = response.results || []
    }
  } catch (error) {
    console.error('Load equipment error:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadProposals()
}

const handleFilterChange = () => {
  currentPage.value = 1
  loadProposals()
}

const handlePageChange = () => {
  loadProposals()
}

const handleCreate = () => {
  isEditMode.value = false
  currentProposalId.value = null
  resetForm()
  dialogVisible.value = true
  activeTab.value = 'basic'
}

const handleEdit = async (proposal: CommercialProposal) => {
  try {
    loading.value = true
    const proposalData = await proposalsAPI.getProposalById(proposal.proposal_id)

    isEditMode.value = true
    currentProposalId.value = proposal.proposal_id
    activeTab.value = 'basic'

    Object.assign(formData, {
      proposal_name: proposalData.proposal_name || '',
      outcoming_number: proposalData.outcoming_number || '',
      client_id: proposalData.client?.client_id || 0,
      currency_ticket: proposalData.currency_ticket || 'KZT',
      exchange_rate: proposalData.exchange_rate || '1',
      total_price: proposalData.total_price || '0',
      cost_price: proposalData.cost_price || '',
      margin_percentage: proposalData.margin_percentage || '',
      proposal_date: proposalData.proposal_date || new Date().toISOString().split('T')[0],
      valid_until: proposalData.valid_until || '',
      delivery_time: proposalData.delivery_time || '',
      warranty: proposalData.warranty || '',
      proposal_status: proposalData.proposal_status || 'draft',
      proposal_version: proposalData.proposal_version || 1,
      comments: proposalData.comments || '',
      bitrix_lead_link: proposalData.bitrix_lead_link || '',
      additional_price_ids: proposalData.equipment_lists?.[0]?.additional_prices?.map((p: any) => typeof p === 'object' ? p.price_id : p) || [],
    })

    // Загружаем оборудование из КП
    if (proposalData.equipment_lists && proposalData.equipment_lists.length > 0) {
      selectedEquipment.value = []
      for (const list of proposalData.equipment_lists) {
        if (list.equipment_items_data) {
          for (const item of list.equipment_items_data) {
            selectedEquipment.value.push({
              equipment_id: item.equipment,
              equipment_name: item.equipment_name,
              quantity: item.quantity,
            })
          }
        }
      }
    }

    dialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка загрузки данных КП')
    console.error('Load proposal error:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (proposal: CommercialProposal) => {
  try {
    await ElMessageBox.confirm(
      `Вы уверены, что хотите удалить КП "${proposal.proposal_name || proposal.outcoming_number}"?`,
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )

    await proposalsAPI.deleteProposal(proposal.proposal_id)
    ElMessage.success('КП успешно удалено')
    loadProposals()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления КП')
      console.error('Delete proposal error:', error)
    }
  }
}

const handleDownloadPDF = async (proposal: CommercialProposal) => {
  try {
    loading.value = true
    const blob = await proposalsAPI.downloadPDF(proposal.proposal_id)
    
    // Создаем ссылку для скачивания
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const filename = `КП_${proposal.outcoming_number.replace(/\s+/g, '_').replace(/\//g, '_')}.pdf`
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('PDF успешно скачан')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка скачивания PDF')
    console.error('Download PDF error:', error)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        submitting.value = true

        // Рассчитываем итоговую цену на основе себестоимости и маржи
        let calculatedTotalPrice = formData.total_price
        if (formData.cost_price && formData.margin_percentage) {
          const costPrice = parseFloat(String(formData.cost_price))
          const marginPercent = parseFloat(String(formData.margin_percentage))
          calculatedTotalPrice = (costPrice * (1 + marginPercent / 100)).toFixed(2)
          formData.total_price = calculatedTotalPrice
        } else if (formData.cost_price) {
          // Если маржа не указана, итоговая цена = себестоимость
          calculatedTotalPrice = parseFloat(String(formData.cost_price)).toFixed(2)
          formData.total_price = calculatedTotalPrice
        } else {
          // Округляем существующее значение до 2 знаков
          calculatedTotalPrice = parseFloat(String(formData.total_price || '0')).toFixed(2)
          formData.total_price = calculatedTotalPrice
        }

        const submitData: any = {
          proposal_name: formData.proposal_name.trim(),
          outcoming_number: formData.outcoming_number.trim(),
          client_id: formData.client_id,
          currency_ticket: formData.currency_ticket,
          exchange_rate: String(formData.exchange_rate),
          total_price: calculatedTotalPrice,
          proposal_date: formData.proposal_date,
          proposal_status: formData.proposal_status,
          proposal_version: formData.proposal_version || 1,
        }

        if (formData.user_id) {
          submitData.user_id = formData.user_id
        } else if (authStore.user?.user_id) {
          submitData.user_id = authStore.user.user_id
        }

        if (formData.valid_until) submitData.valid_until = formData.valid_until
        if (formData.delivery_time) submitData.delivery_time = formData.delivery_time.trim()
        if (formData.warranty) submitData.warranty = formData.warranty.trim()
        if (formData.comments) submitData.comments = formData.comments.trim()
        if (formData.bitrix_lead_link) submitData.bitrix_lead_link = formData.bitrix_lead_link.trim()
        if (formData.exchange_rate_date) submitData.exchange_rate_date = formData.exchange_rate_date
        if (formData.cost_price) submitData.cost_price = String(formData.cost_price)
        if (formData.margin_percentage) submitData.margin_percentage = String(formData.margin_percentage)
        if (formData.parent_proposal_id) submitData.parent_proposal_id = formData.parent_proposal_id

        // Добавляем данные об оборудовании
        if (selectedEquipment.value.length > 0) {
          submitData.equipment_items = selectedEquipment.value.map(item => ({
            equipment_id: item.equipment_id,
            quantity: item.quantity || 1
          }))
          
          // Данные для EquipmentList (налоги, доставка и т.д.)
          // Пока оставляем пустым, можно добавить поля в форму позже
          submitData.equipment_list = {
            tax_percentage: null,
            tax_price: null,
            delivery_percentage: null,
            delivery_price: null,
            additional_price_ids: formData.additional_price_ids || []
          }
        }

        if (isEditMode.value && currentProposalId.value) {
          await proposalsAPI.updateProposal(currentProposalId.value, submitData)
          ElMessage.success('КП успешно обновлено')
        } else {
          await proposalsAPI.createProposal(submitData)
          ElMessage.success('КП успешно создано')
        }

        dialogVisible.value = false
        loadProposals()
      } catch (error: any) {
        const errorMessage = error.response?.data?.message || 
                           (error.response?.data ? JSON.stringify(error.response.data) : '') ||
                           'Ошибка сохранения КП'
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

const selectEquipment = (equipment: Equipment) => {
  const exists = selectedEquipment.value.find(eq => eq.equipment_id === equipment.equipment_id)
  if (!exists) {
    selectedEquipment.value.push({
      equipment_id: equipment.equipment_id,
      equipment_name: equipment.equipment_name,
      quantity: 1,
    })
    showAddEquipmentDialog.value = false
    equipmentSearchQuery.value = ''
  } else {
    ElMessage.warning('Это оборудование уже добавлено')
  }
}

const removeEquipment = (index: number) => {
  selectedEquipment.value.splice(index, 1)
}

const updateEquipmentQuantity = (index: number, quantity: number) => {
  const item = selectedEquipment.value[index]
  if (item.cost) {
    item.total_cost = item.cost * quantity
  }
}

const calculateEquipmentCost = async (item: { equipment_id: number; quantity: number }) => {
  try {
    // Подготавливаем данные для запроса
    const requestData: any = {
      equipment_id: item.equipment_id,
      target_currency: formData.currency_ticket || 'KZT',
      save_calculation: false,
    }

    // Добавляем proposal_id только если КП уже создано
    if (currentProposalId.value) {
      requestData.proposal_id = currentProposalId.value
    }

    // Добавляем дату курса валюты, если указана
    if (formData.exchange_rate_date) {
      requestData.exchange_rate_date = formData.exchange_rate_date
    }

    // Добавляем курс валюты из формы в manual_overrides
    // Это позволит использовать курс из КП даже если его нет в ExchangeRate
    if (formData.exchange_rate && parseFloat(formData.exchange_rate) > 0) {
      requestData.manual_overrides = {
        exchange_rate_value: parseFloat(formData.exchange_rate),
      }
    }

    console.log('Расчет себестоимости, отправляемые данные:', requestData)

    const calculation = await costCalculationAPI.calculateCost(requestData)

    console.log('Результат расчета:', calculation)

    if (calculation && calculation.total_cost_target_currency) {
      // Используем себестоимость в целевой валюте КП
      const cost = parseFloat(String(calculation.total_cost_target_currency))
      item.cost = parseFloat(cost.toFixed(2))
      item.total_cost = parseFloat((cost * item.quantity).toFixed(2))

      // Обновляем общую себестоимость КП
      const totalCost = selectedEquipment.value.reduce((sum, eq) => sum + (eq.total_cost || 0), 0)
      formData.cost_price = String(parseFloat(totalCost.toFixed(2)))

      // Автоматически пересчитываем итоговую цену на основе маржи
      if (formData.margin_percentage) {
        const marginPercent = parseFloat(String(formData.margin_percentage))
        const calculatedTotal = totalCost * (1 + marginPercent / 100)
        formData.total_price = String(parseFloat(calculatedTotal.toFixed(2)))
      } else {
        // Если маржа не указана, итоговая цена = себестоимость
        formData.total_price = String(parseFloat(String(totalCost)).toFixed(2))
      }

      ElMessage.success(`Себестоимость рассчитана: ${item.cost.toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ${formData.currency_ticket || 'KZT'}`)
    } else {
      ElMessage.warning('Не удалось получить результат расчета себестоимости')
    }
  } catch (error: any) {
    console.error('Calculate cost error:', error)
    console.error('Error response:', error.response?.data)
    
    let errorMessage = 'Ошибка расчета себестоимости'
    
    if (error.response?.data) {
      // Обрабатываем разные форматы ошибок
      if (error.response.data.error) {
        errorMessage = error.response.data.error
      } else if (error.response.data.message) {
        errorMessage = error.response.data.message
      } else if (typeof error.response.data === 'string') {
        errorMessage = error.response.data
      } else if (error.response.data.non_field_errors) {
        errorMessage = error.response.data.non_field_errors.join(', ')
      } else {
        // Пытаемся извлечь первую ошибку из объекта
        const firstError = Object.values(error.response.data)[0]
        if (Array.isArray(firstError)) {
          errorMessage = firstError[0]
        } else if (typeof firstError === 'string') {
          errorMessage = firstError
        } else {
          errorMessage = JSON.stringify(error.response.data)
        }
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  }
}

const calculateMargin = (total: string | number, cost: string | number): string => {
  const totalNum = typeof total === 'string' ? parseFloat(total) : total
  const costNum = typeof cost === 'string' ? parseFloat(cost) : cost
  if (!costNum || costNum === 0) return '0'
  const margin = ((totalNum - costNum) / costNum) * 100
  return margin.toFixed(2)
}

const calculateTotalPrice = async () => {
  try {
    calculatingTotalPrice.value = true
    
    // Сначала рассчитываем себестоимость всех оборудования
    let totalCostPrice = 0
    
    if (selectedEquipment.value.length === 0) {
      ElMessage.warning('Добавьте оборудование в КП для расчета')
      return
    }
    
    // Рассчитываем себестоимость для каждого оборудования
    for (const item of selectedEquipment.value) {
      if (!item.equipment_id) continue
      
      try {
        const requestData: any = {
          equipment_id: item.equipment_id,
          target_currency: 'KZT',
          save_calculation: false,
        }
        
        // Добавляем proposal_id только если КП уже создано
        if (currentProposalId.value) {
          requestData.proposal_id = currentProposalId.value
        }
        
        // Добавляем дату курса валюты, если указана
        if (formData.exchange_rate_date) {
          requestData.exchange_rate_date = formData.exchange_rate_date
        }
        
        // Добавляем курс валюты из формы в manual_overrides
        if (formData.exchange_rate && parseFloat(formData.exchange_rate) > 0) {
          requestData.manual_overrides = {
            exchange_rate_value: parseFloat(formData.exchange_rate),
          }
        }
        
        const calculation = await costCalculationAPI.calculateCost(requestData)
        
        if (calculation && calculation.total_cost_kzt) {
          const cost = parseFloat(String(calculation.total_cost_kzt))
          const quantity = item.quantity || 1
          totalCostPrice += cost * quantity
        }
      } catch (error: any) {
        console.error(`Error calculating cost for equipment ${item.equipment_id}:`, error)
        ElMessage.warning(`Ошибка расчета себестоимости для ${item.equipment_name || 'оборудования'}`)
      }
    }
    
    // Обновляем себестоимость
    formData.cost_price = String(totalCostPrice.toFixed(2))
    
    // Рассчитываем итоговую цену с учетом маржи
    if (formData.margin_percentage && parseFloat(formData.margin_percentage) > 0) {
      const margin = parseFloat(formData.margin_percentage) / 100
      const totalPrice = totalCostPrice * (1 + margin)
      formData.total_price = String(totalPrice.toFixed(2))
      ElMessage.success(`Итоговая цена рассчитана: ${totalPrice.toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ${formData.currency_ticket || 'KZT'}`)
    } else {
      ElMessage.warning('Укажите процент маржи для расчета итоговой цены')
    }
  } catch (error: any) {
    console.error('Calculate total price error:', error)
    ElMessage.error('Ошибка расчета итоговой цены')
  } finally {
    calculatingTotalPrice.value = false
  }
}

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy')
  } catch {
    return dateString
  }
}

const formatPrice = (price: string | number, currency: string) => {
  const priceNum = typeof price === 'string' ? parseFloat(price) : price
  return `${priceNum.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    draft: 'Черновик',
    sent: 'Отправлено',
    accepted: 'Принято',
    rejected: 'Отклонено',
    negotiating: 'В переговорах',
    completed: 'Завершено',
  }
  return labels[status] || status
}

const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    draft: 'info',
    sent: 'warning',
    accepted: 'success',
    rejected: 'danger',
    negotiating: 'warning',
    completed: 'success',
  }
  return types[status] || 'info'
}

const getMarginTagType = (margin?: string) => {
  if (!margin) return 'info'
  const marginNum = parseFloat(margin)
  if (marginNum < 0) return 'danger'
  if (marginNum < 10) return 'warning'
  return 'success'
}

const resetForm = () => {
  Object.assign(formData, {
    proposal_name: '',
    outcoming_number: '',
    client_id: 0,
    currency_ticket: 'KZT',
    exchange_rate: '1',
    additional_price_ids: [],
    total_price: '0',
    cost_price: '',
    margin_percentage: '',
    proposal_date: new Date().toISOString().split('T')[0],
    valid_until: '',
    delivery_time: '',
    warranty: '',
    proposal_status: 'draft',
    proposal_version: 1,
    comments: '',
    bitrix_lead_link: '',
  })
  selectedEquipment.value = []
}

const handleDialogClose = () => {
  resetForm()
  formRef.value?.clearValidate()
  activeTab.value = 'basic'
}

const loadAdditionalPrices = async () => {
  try {
    loadingAdditionalPrices.value = true
    console.log('Loading additional prices from API...')
    const data = await additionalPricesAPI.getAdditionalPrices()
    console.log('API response:', data)
    console.log('Data type:', typeof data, 'Is array:', Array.isArray(data))
    additionalPrices.value = Array.isArray(data) ? data : []
    console.log('Loaded additional prices:', additionalPrices.value.length, 'items')
    console.log('Additional prices data:', JSON.stringify(additionalPrices.value, null, 2))
    if (additionalPrices.value.length === 0) {
      console.warn('No additional prices found. Check database and API response.')
    }
  } catch (error: any) {
    console.error('Load additional prices error:', error)
    console.error('Error response:', error.response?.data)
    ElMessage.error(error.response?.data?.message || error.message || 'Ошибка загрузки дополнительных расходов')
    additionalPrices.value = []
  } finally {
    loadingAdditionalPrices.value = false
  }
}

// Функции для управления дополнительными расходами
const handleCreateAdditionalPrice = () => {
  isEditAdditionalPriceMode.value = false
  currentAdditionalPriceId.value = null
  Object.assign(additionalPriceForm, {
    price_parameter_name: '',
    expense_type: '' as any,
    value_type: '' as any,
    price_parameter_value: 0,
  })
  showAdditionalPriceFormDialog.value = true
}

const handleEditAdditionalPrice = (price: AdditionalPrice) => {
  isEditAdditionalPriceMode.value = true
  currentAdditionalPriceId.value = price.price_id
  Object.assign(additionalPriceForm, {
    price_parameter_name: price.price_parameter_name,
    expense_type: price.expense_type,
    value_type: price.value_type,
    price_parameter_value: parseFloat(price.price_parameter_value),
  })
  showAdditionalPriceFormDialog.value = true
}

const handleDeleteAdditionalPrice = async (price: AdditionalPrice) => {
  try {
    await ElMessageBox.confirm(
      `Вы уверены, что хотите удалить дополнительный расход "${price.price_parameter_name}"?`,
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )
    await additionalPricesAPI.deleteAdditionalPrice(price.price_id)
    ElMessage.success('Дополнительный расход успешно удален')
    await loadAdditionalPrices()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления дополнительного расхода')
    }
  }
}

const handleSubmitAdditionalPrice = async () => {
  if (!additionalPriceFormRef.value) return
  
  await additionalPriceFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        submittingAdditionalPrice.value = true
        if (isEditAdditionalPriceMode.value && currentAdditionalPriceId.value) {
          await additionalPricesAPI.updateAdditionalPrice(currentAdditionalPriceId.value, {
            price_parameter_name: additionalPriceForm.price_parameter_name,
            expense_type: additionalPriceForm.expense_type,
            value_type: additionalPriceForm.value_type,
            price_parameter_value: String(additionalPriceForm.price_parameter_value),
          })
          ElMessage.success('Дополнительный расход успешно обновлен')
        } else {
          await additionalPricesAPI.createAdditionalPrice({
            price_parameter_name: additionalPriceForm.price_parameter_name,
            expense_type: additionalPriceForm.expense_type,
            value_type: additionalPriceForm.value_type,
            price_parameter_value: String(additionalPriceForm.price_parameter_value),
          })
          ElMessage.success('Дополнительный расход успешно создан')
        }
        showAdditionalPriceFormDialog.value = false
        await loadAdditionalPrices()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || 'Ошибка сохранения дополнительного расхода')
      } finally {
        submittingAdditionalPrice.value = false
      }
    }
  })
}

const getExpenseTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    packaging: 'Упаковка',
    labor: 'Труд',
    depreciation: 'Амортизация',
    service: 'Сервис',
    warehouse: 'Склад',
    other: 'Другое',
  }
  return labels[type] || type
}

const getValueTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    percentage: 'Процент',
    fixed: 'Фиксированная сумма',
    coefficient: 'Коэффициент',
  }
  return labels[type] || type
}

// Функция конвертации валют
const convertCurrency = (amount: number | string, fromCurrency: string, toCurrency: string, exchangeRate?: number): number => {
  if (fromCurrency === toCurrency) {
    return typeof amount === 'string' ? parseFloat(amount) : amount
  }
  
  const amountNum = typeof amount === 'string' ? parseFloat(amount) : amount
  
  // Если есть курс из КП, используем его
  if (exchangeRate && exchangeRate > 0) {
    // exchangeRate - это курс из валюты КП в KZT
    // Например, если currency_ticket = RUB, exchange_rate = 5.5 (RUB/KZT)
    // То для конвертации KZT -> RUB: amount / exchangeRate
    // Для конвертации RUB -> KZT: amount * exchangeRate
    if (fromCurrency === 'KZT' && toCurrency !== 'KZT') {
      // Конвертируем из KZT в валюту КП
      return amountNum / exchangeRate
    } else if (fromCurrency !== 'KZT' && toCurrency === 'KZT') {
      // Конвертируем из валюты КП в KZT
      return amountNum * exchangeRate
    }
  }
  
  // Если курса нет, возвращаем исходное значение
  return amountNum
}

onMounted(async () => {
  await Promise.all([
    loadProposals(),
    loadClients(),
    loadEquipment(),
    loadAdditionalPrices(),
  ])
})
</script>

<style scoped>
.proposals-view {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.equipment-section {
  padding: 20px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
</style>
